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

Conversions from floating point to an integer in a SIMD register become
the vector form, which the x86 emulator's ARM translation has: the scalar
form stopped the app with SIGILL in hud_calculate_point once a game was
drawn (OpenCE 242). Those are checked as text and, with clang, compiled.
"""
from pathlib import Path
import re
import shutil
import struct
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

# scalar conversions to an integer in a SIMD register: the vector form (OpenCE 242)
for instruction, replacement in (
    ("\tfcvtzs\ts0, s0", ["\tfmov s0, s0", "\tfcvtzs v0.2s, v0.2s"]),
    ("\tfcvtzu\ts2, s17", ["\tfmov s2, s17", "\tfcvtzu v2.2s, v2.2s"]),
    ("\tfcvtms\td31, d4", ["\tfmov d31, d4", "\tfcvtms v31.2d, v31.2d"]),
    ("\tfcvtau\td1, d1", ["\tfmov d1, d1", "\tfcvtau v1.2d, v1.2d"]),
    ("\tfcvtns\ts3, s4, #4", ["\tfmov s3, s4", "\tfcvtns v3.2s, v3.2s, #4"]),
    ("\tfcvtpu\td5, d6, #16", ["\tfmov d5, d6", "\tfcvtpu v5.2d, v5.2d, #16"]),
):
    assert convert(instruction).splitlines() == replacement, (instruction, convert(instruction))
# the other conversions are kept
for instruction in ("\tfcvtzs\tw0, s0", "\tfcvtzu\tx3, d1", "\tfcvtzs\tv0.4s, v1.4s", "\tscvtf\ts0, s0",
                    "\tucvtf\td1, d2", "\tfcvt\td0, s0", "\tfcvtzs\tw8, s0, #4"):
    op, args = instruction.strip().split("\t")
    assert convert(instruction).splitlines() == [f"\t{op} {args}"], (instruction, convert(instruction))
print("PASS: scalar float-to-integer conversions in SIMD registers become the vector form; the others are kept")


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
    for candidate in (f"llvm-{name}", *(f"llvm-{name}-{v}" for v in range(30, 13, -1)), name):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def elf_sections(blob):
    """(name, address, offset, size, type) for every section of a 64-bit
    little-endian ELF (objects and images), read without external tools:
    GNU binutils on an x86 host cannot read AArch64 objects."""
    assert blob[:4] == b"\x7fELF" and blob[4] == 2 and blob[5] == 1, "expected ELF64 LE"
    shoff = struct.unpack_from("<Q", blob, 0x28)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", blob, 0x3A)
    raw = [struct.unpack_from("<IIQQQQIIQQ", blob, shoff + i * shentsize) for i in range(shnum)]
    names = raw[shstrndx]
    strings = blob[names[4]:names[4] + names[5]]
    out = []
    for name, kind, _flags, address, offset, size, link, _info, _align, entsize in raw:
        out.append((strings[name:strings.index(b"\0", name)].decode(), address, offset, size, kind, link, entsize))
    return out


def symbol_bytes(obj, symbol, section, size):
    blob = Path(obj).read_bytes()
    sections = elf_sections(blob)
    symtab = next(s for s in sections if s[4] == 2)  # SHT_SYMTAB
    strtab = sections[symtab[5]]
    names = blob[strtab[2]:strtab[2] + strtab[3]]
    for i in range(symtab[3] // symtab[6]):
        st_name, _info, _other, shndx, value, _size = struct.unpack_from("<IBBHQQ", blob, symtab[2] + i * symtab[6])
        if names[st_name:names.index(b"\0", st_name)].decode() != symbol:
            continue
        target = sections[shndx]
        assert target[0] == section, f"{symbol} is in {target[0]}, expected {section}"
        start = target[2] + value - target[1]  # objects: address 0, value is the offset
        return blob[start:start + size]
    raise AssertionError(f"{symbol} not found in {obj}")


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

# what clang makes of a rounded short (as hud_calculate_point's point),
# through the guest's pipeline: no scalar form is left, and it assembles
SCALAR_FROM_SIMD = re.compile(r"^\s*fcvt[amnpz][su]\s+[sd]\d+\s*,", re.MULTILINE)
point_source = OUT / "point.c"
point_source.write_text(
    "struct point { short x, y; };\n"
    "void calculate_point(float x, float y, struct point *result)\n"
    "{ result->x = (short)__builtin_rintf(x); result->y = (short)__builtin_rintf(y); }\n"
    "void store_doubles(double a, double b, long long *result) { result[0] = (long long)a; result[1] = (long long)b; }\n",
    encoding="utf-8",
)
point_darwin = OUT / "point.darwin.s"
subprocess.run([cc, *GUEST_ABI, "-S", str(point_source), "-o", str(point_darwin)], check=True)
if SCALAR_FROM_SIMD.search(point_darwin.read_text()):
    point_elf = OUT / "point.s"
    subprocess.run([sys.executable, str(ROOT / "tools/android_asm_convert.py"), str(point_darwin), str(point_elf)],
                   check=True)
    text = point_elf.read_text()
    assert not SCALAR_FROM_SIMD.search(text), "a scalar conversion is left"
    assert re.search(r"fcvtzs v\d+\.2s, v\d+\.2s", text), "no vector conversion"
    subprocess.run([cc, "--target=aarch64-linux-android", "-c", str(point_elf), "-o", str(OUT / "point.o")], check=True)
    print("PASS: a compiled rounding conversion leaves no scalar SIMD form and assembles")
else:
    print("SKIP: this clang converts in general registers (no scalar SIMD form to replace)")

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
    for name, (fmt, width) in tables.items():
        ref = source_table(name)
        raw = symbol_bytes(opus_obj, name, ".rodata", len(ref) * width)
        assert list(struct.unpack("<%d%s" % (len(ref), fmt), raw)) == ref, f"Opus {name} differs from source"
    print("PASS: Opus CELT pulse-cache tables match the vendored source after conversion")
else:
    print("SKIP: Opus table compile (run configure.py first for the guest libc headers)")

# a built guest image: its Opus tables must match the source. Before a build
# (tools/build-quest.sh runs the checks first) the image on disk may be an
# older one, built by an older converter: that is reported, not failed, and
# the build script repeats this check with HALO_REQUIRE_GUEST_IMAGE=1 once the
# new image exists.
import os  # noqa: E402

image = ROOT / "build/android/halo_guest.elf"
required = os.environ.get("HALO_REQUIRE_GUEST_IMAGE") == "1"
if required and not image.is_file():
    raise AssertionError("HALO_REQUIRE_GUEST_IMAGE=1 but no build/android/halo_guest.elf was built")
if image.is_file():
    blob = image.read_bytes()
    sections = elf_sections(blob)
    symtab = next(s for s in sections if s[4] == 2)
    strtab = sections[symtab[5]]
    names = blob[strtab[2]:strtab[2] + strtab[3]]
    addresses = {}
    for i in range(symtab[3] // symtab[6]):
        st_name, _info, _other, shndx, value, _size = struct.unpack_from("<IBBHQQ", blob, symtab[2] + i * symtab[6])
        name = names[st_name:names.index(b"\0", st_name)].decode()
        if name in tables:
            addresses[name] = (shndx, value)
    for name, (fmt, width) in tables.items():
        assert name in addresses, f"{name} missing from the guest image"
        shndx, value = addresses[name]
        target = sections[shndx]
        ref = source_table(name)
        start = target[2] + value - target[1]
        raw = blob[start:start + len(ref) * width]
        if list(struct.unpack("<%d%s" % (len(ref), fmt), raw)) != ref:
            if required:
                raise AssertionError(f"guest image {name} is corrupt")
            print(f"STALE: build/android/halo_guest.elf has a corrupt {name} (built before the converter fix); "
                  "rebuild it -- tools/build-quest.sh rechecks the new image")
            break
    else:
        print("PASS: the built guest image carries the exact Opus pulse-cache tables")
