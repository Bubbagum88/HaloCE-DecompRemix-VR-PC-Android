"""The arm64_32 -> ELF assembly converter must never alter literal data.

Test51/v1.0.19 crashed on Quest as soon as a player spoke in voice chat: the
converter ran Darwin symbol "undecoration" (dropping a leading underscore)
over .ascii data. clang emits byte tables as .ascii strings, so Opus's
cache_bits50 table lost the byte 95 ('_') that followed an escaped quote, the
rest of the table shifted by one, and the CELT encoder indexed past
CELT_PVQ_U_ROW (SIGSEGV in encode_pulses). Any C string that began with an
underscore lost it as well.

This suite checks the converter text transforms directly, then (where a clang
with the arm64_32 target is available, as in every build environment) compiles
real tables through the production pipeline and compares the assembled bytes.
When the Android third-party headers exist (after configure.py), the actual
Opus mode tables are compiled and compared with the vendored source, and a
built guest image, when present, is checked as well.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import android_asm_convert as conv  # noqa: E402

OUT = ROOT / "build" / "asm-convert-test"
OUT.mkdir(parents=True, exist_ok=True)


def convert(text):
    return conv.Converter(text.splitlines()).run()


# ---------- text transforms

# literal data is passed through byte-for-byte
for line in (
    '\t.ascii\t"(\\017\\027\\034\\037\\"$&\')*+,-./3_\\206\\252"',
    '\t.asciz\t"_leading underscore"',
    '\t.asciz\t"a\\"b_c \\\\_d Ltmp0 _main"',
    '\t.ascii\t"\\"_\\"_"',
    '\t.asciz\t"x@PAGEOFF y@GOTPAGE ;not a comment // nor this"',
):
    out = convert(line).strip()
    assert out.split(None, 1) == line.strip().split(None, 1), (line, out)

# symbols are still undecorated in code and pointer data
assert convert("\tbl\t_opus_encode_float").strip() == "bl opus_encode_float"
assert convert("\t.long\t_CELT_PVQ_U_DATA+1200").strip() == ".long CELT_PVQ_U_DATA+1200"
assert convert("\t.quad\t_foo").strip() == ".quad foo"
assert convert('_cache_bits50:').strip() == "cache_bits50:"
assert convert('\t.globl\t_cache_bits50').strip() == ".globl cache_bits50"
assert ":lo12:table" in convert("\tadd\tx8, x8, _table@PAGEOFF")
# quoted symbol names (Darwin uses them for unusual characters)
assert convert('"_odd$name":').strip() == '"odd$name":'
# a label and a string directive on one line
assert convert('Lstr: .asciz "_x\\"_y"').splitlines()[-1] == '\t.asciz "_x\\"_y"'
# relocation operators inside strings are data, not errors
convert('\t.asciz\t"user@host"')
print("PASS: converter text transforms keep .ascii/.asciz data intact and still undecorate symbols")


# ---------- the production pipeline: C -> arm64_32 Darwin assembly -> ELF object

def find_guest_cc():
    for cc in (shutil.which("clang"),):
        if not cc:
            continue
        probe = subprocess.run([cc, "--target=arm64_32-apple-watchos", "-x", "c", "-S", "-o", "-", "-"],
                               input="int x;", text=True, capture_output=True)
        if probe.returncode == 0:
            return cc
    return None


GUEST_ABI = [
    "--target=arm64_32-apple-watchos", "-U__APPLE__", "-U__MACH__", "-fno-define-target-os-macros",
    "-D__linux__=1", "-D__unix__=1", "-DHALO_ANDROID=1", "-mcpu=cortex-a53", "-nostdinc",
    "-fshort-wchar", "-fno-stack-protector", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
    "-femulated-tls", "-mllvm", "-aarch64-neon-syntax=generic", "-ffp-contract=off", "-O2",
]


def guest_object(cc, source, obj, flags=()):
    darwin = obj.with_suffix(".darwin.s")
    elf = obj.with_suffix(".s")
    subprocess.run([cc, *GUEST_ABI, *flags, "-S", str(source), "-o", str(darwin)], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools/android_asm_convert.py"), str(darwin), str(elf)], check=True)
    subprocess.run([cc, "--target=aarch64-linux-android", "-c", str(elf), "-o", str(obj)], check=True)


def tool(name):
    for candidate in (name, f"llvm-{name}"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def symbol_bytes(obj, symbol, section, size):
    nm = tool("llvm-nm") or tool("nm")
    objcopy = tool("llvm-objcopy") or tool("objcopy")
    assert nm and objcopy, "need nm and objcopy"
    table = subprocess.check_output([nm, str(obj)], text=True)
    match = re.search(r"^([0-9a-f]+) \w " + re.escape(symbol) + r"$", table, re.M)
    assert match, f"{symbol} not found in {obj}"
    blob = obj.with_suffix("." + symbol + ".bin")
    subprocess.run([objcopy, "-O", "binary", f"--only-section={section}", str(obj), str(blob)], check=True)
    data = blob.read_bytes()
    offset = int(match.group(1), 16)
    return data[offset:offset + size]


cc = find_guest_cc()
if not cc:
    print("SKIP: no clang with the arm64_32 target here; text transforms were checked")
    sys.exit(0)

# every byte value, in an order that places '"' before '_' and identifier-like
# runs inside the string, plus strings that begin with underscores
values = list(range(256))
tricky = [34, 51, 95, 134, 34, 95, 95, 120, 49, 102, 76, 116, 109, 112, 48, 92, 34, 95]
data_values = values + tricky + values[::-1]
c_source = OUT / "tables.c"
c_source.write_text(
    "const unsigned char halo_test_table[] = {" + ",".join(map(str, data_values)) + "};\n"
    'const char halo_test_string[] = "_leading \\"_quoted_\\" Ltmp0 _main \\\\_x @PAGEOFF";\n'
    "const char *const halo_test_pointer = halo_test_string;\n",
    encoding="utf-8",
)
obj = OUT / "tables.o"
guest_object(cc, c_source, obj)
got = symbol_bytes(obj, "halo_test_table", ".rodata", len(data_values))
assert got == bytes(data_values), "byte table altered by the converter"
expected = b'_leading "_quoted_" Ltmp0 _main \\_x @PAGEOFF\0'
got = symbol_bytes(obj, "halo_test_string", ".rodata", len(expected))
assert got == expected, (got, expected)
print("PASS: byte tables and strings compiled through the guest pipeline are byte-identical")

# the real Opus mode tables (voice chat), when the guest libc headers exist
musl = ROOT / "build/android/third_party/musl-1.2.5"
libc_include = ROOT / "build/android/guest/libc_include"
arch = ROOT / "port/android/guest/libc/arch/arm64_32"
opus = ROOT / "port/third_party/opus"
static_modes = (opus / "celt/static_modes_float.h").read_text(encoding="utf-8")


def source_table(name):
    match = re.search(r"\b" + name + r"\[\d*\]\s*=\s*\{(.*?)\};", static_modes, re.S)
    body = re.sub(r"/\*.*?\*/", "", match.group(1), flags=re.S)
    return [int(x, 0) for x in re.findall(r"-?\d+", body)]


tables = {"cache_bits50": ("B", 1), "cache_caps50": ("B", 1), "cache_index50": ("h", 2)}
if musl.is_dir() and libc_include.is_dir():
    opus_obj = OUT / "opus_modes.o"
    guest_object(cc, opus / "celt/modes.c", opus_obj, [
        f"-isystem{libc_include}", f"-isystem{arch}", f"-isystem{musl}/arch/generic", f"-isystem{musl}/include",
        "-std=gnu11", "-DOPUS_BUILD", "-DVAR_ARRAYS", "-DHAVE_LRINTF", "-DHAVE_LRINT",
        f"-I{opus}/include", f"-I{opus}/celt", f"-I{opus}/silk", f"-I{opus}/silk/float", "-w"])
    import struct
    for name, (fmt, width) in tables.items():
        ref = source_table(name)
        raw = symbol_bytes(opus_obj, name, ".rodata", len(ref) * width)
        assert list(struct.unpack("<%d%s" % (len(ref), fmt), raw)) == ref, f"Opus {name} differs from source"
    print("PASS: Opus CELT pulse-cache tables match the vendored source after conversion")
else:
    print("SKIP: Opus table compile (run configure.py first for the guest libc headers)")

# a built guest image, when present: its Opus tables must match the source
image = ROOT / "build/android/halo_guest.elf"
if image.is_file():
    import struct
    nm = tool("llvm-nm") or tool("nm")
    readelf = tool("llvm-readelf") or tool("readelf")
    symbols = subprocess.check_output([nm, str(image)], text=True)
    sections = subprocess.check_output([readelf, "-SW", str(image)], text=True)
    blob = image.read_bytes()

    def read(address, size):
        for line in sections.splitlines():
            m = re.match(r"\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)", line)
            if not m or m.group(2) == "NOBITS":
                continue
            start, offset, length = int(m.group(3), 16), int(m.group(4), 16), int(m.group(5), 16)
            if start and start <= address < start + length:
                return blob[offset + address - start: offset + address - start + size]
        raise AssertionError(f"address {address:#x} not in a loaded section")

    for name, (fmt, width) in tables.items():
        m = re.search(r"^([0-9a-f]+) \w " + name + r"$", symbols, re.M)
        assert m, f"{name} missing from the guest image"
        ref = source_table(name)
        raw = read(int(m.group(1), 16), len(ref) * width)
        assert list(struct.unpack("<%d%s" % (len(ref), fmt), raw)) == ref, f"guest image {name} is corrupt"
    print("PASS: the built guest image carries the exact Opus pulse-cache tables")
