"""Whole-program call-signature check for the Android guest image.

The guest runs the game as arm64_32 code with the Darwin calling convention:
variadic arguments go on the stack, promoted floats travel in double
registers, and a caller (not the callee) extends narrow integer arguments.
A call whose declaration disagrees with the real definition is therefore
miscompiled silently: Test50/Test51's voice logs read stack garbage through
an undeclared platform_log, and libtiff's "long lseek()" passed a 32-bit
offset where lseek takes a 64-bit off_t. The build rejects implicit
declarations; this check also catches hand-written prototypes in one unit
that do not match the definition in another, which no single-unit compiler
diagnostic can see.

Every guest unit in the configured build.ninja is compiled to LLVM bitcode
with its own flags, the units are linked (musl only as needed, as the real
link uses it as an archive), and LLVM's Lint pass reports each direct call
whose argument count, argument types or return type differ from the callee's
definition. Run after ``ninja android_apk`` (the guest's generated headers
must exist); tools/build-quest.sh does so for both flavors.

    python3 tools/android_guest_abi_lint.py [--jobs N]
"""
import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "android-abi-lint"

# Calls the check accepts, with the reason. Keep this list short and exact.
ALLOWED = {
    # guest_start.c passes the usual argc/argv; the game's main ignores them
    "main": "guest runtime entry passes argc/argv to the game's main(void)",
}


def llvm_tool(name):
    for candidate in (f"llvm-{name}", *(f"llvm-{name}-{v}" for v in range(30, 13, -1))):
        path = shutil.which(candidate)
        if path:
            return path
    for version in range(30, 13, -1):
        path = Path(f"/usr/lib/llvm-{version}/bin/{name}")
        if path.is_file():
            return str(path)
    return None


def guest_units(ninja_text):
    text = ninja_text.replace("$\n    ", "").replace("$ ", "\x00").replace("$:", ":")
    cc = re.search(r"^android_guest_cc = (.*)$", text, re.M)
    units = []
    for match in re.finditer(r"^build [^\n]*?: android_guest_cc (\S+)[^\n]*\n((?:  [^\n]*\n)*)", text, re.M):
        source = match.group(1).replace("\x00", " ")
        flags = re.search(r"^\s+cflags = (.*)$", match.group(2), re.M)
        units.append((source, flags.group(1).replace("\x00", " ") if flags else ""))
    return (cc.group(1).strip() if cc else "clang"), units


def balanced(text, start):
    """text[start] is '('; return the contents up to its matching ')'."""
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1:index]
    return text[start + 1:]


def split_top(text):
    parts, depth, current = [], 0, ""
    for char in text:
        if char in "([{<":
            depth += 1
        elif char in ")]}>":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    return parts


def parameter_shape(text):
    """(type, extension) of an IR parameter or argument; sret is marked"""
    if text == "...":
        return ("...", "")
    tokens = text.split()
    extension = "signext" if "signext" in tokens else "zeroext" if "zeroext" in tokens else ""
    return (tokens[0] + (" sret" if "sret(" in text else ""), extension)


def extension_mismatches(ir):
    """Calls passing a narrow integer with a different extension than the
    definition expects (e.g. a word NONE zero-extended into a short): Lint
    compares types only, and on this ABI the caller performs the extension."""
    definitions = {}
    for match in re.finditer(r"^define [^@\n]*@(\"?[\w.$]+\"?)\(", ir, re.M):
        definitions[match.group(1)] = [parameter_shape(p) for p in split_top(balanced(ir, match.end() - 1))]
    problems = []
    function = None
    for line in ir.splitlines():
        match = re.match(r"^define [^@]*@(\"?[\w.$]+\"?)\(", line)
        if match:
            function = match.group(1)
            continue
        match = re.search(r"\b(?:call|invoke)\b[^@]*@(\"?[\w.$]+\"?)\(", line)
        if not match or match.group(1) not in definitions or match.group(1).startswith("llvm."):
            continue
        expected = definitions[match.group(1)]
        arguments = [parameter_shape(a) for a in split_top(balanced(line, match.end() - 1))]
        for position, (argument, parameter) in enumerate(zip(arguments, expected)):
            if parameter[0] == "..." or argument[0] != parameter[0]:
                break
            if parameter[1] and argument[1] != parameter[1]:
                problems.append(f"{function} -> {match.group(1)} argument {position}: "
                                f"{argument[0]} {argument[1] or 'unextended'}, callee expects {parameter[1]}")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jobs", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    args = parser.parse_args()

    ninja = ROOT / "build.ninja"
    link, opt = llvm_tool("link"), shutil.which("opt") or llvm_tool("opt")
    if not ninja.is_file() or "android_guest_cc" not in ninja.read_text(encoding="utf-8", errors="replace"):
        print("SKIP: no configured Android build (python3 configure.py --vr|--release first)")
        return 0
    if not link or not opt:
        print("SKIP: llvm-link/opt not found")
        return 0
    cc, units = guest_units(ninja.read_text(encoding="utf-8", errors="replace"))
    OUT.mkdir(parents=True, exist_ok=True)

    def compile_unit(index_unit):
        index, (source, cflags) = index_unit
        output = OUT / f"{index:05d}_{Path(source).name}.bc"
        flags = [a for a in shlex.split(cflags.replace("$$", "$"))
                 if a != "-w" and not a.startswith("-fprofile")]
        result = subprocess.run([cc, *flags, "-Wno-everything", "-O0", "-Xclang", "-disable-O0-optnone", "-g0",
                                 "-emit-llvm", "-c", source, "-o", str(output)],
                                cwd=ROOT, capture_output=True, text=True)
        return source, output, result.returncode, result.stderr

    main_units, musl_units, failed = [], [], []
    with ThreadPoolExecutor(args.jobs) as pool:
        for source, output, code, err in pool.map(compile_unit, enumerate(units)):
            if code:
                failed.append((source, err.strip().splitlines()[:3]))
            elif "/musl-" in source and "/src/" in source:
                musl_units.append(str(output))
            else:
                main_units.append(str(output))
    if failed:
        for source, err in failed:
            print("FAIL: could not compile", source, *err, sep="\n  ")
        return 1

    game = OUT / "game.bc"
    image = OUT / "guest.bc"
    for command in ([link, *main_units, "-o", str(game)],
                    [link, str(game), "--only-needed", *musl_units, "-o", str(image)]):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            print("FAIL: llvm-link", result.stderr.strip()[:2000])
            return 1

    lint = subprocess.run([opt, "-passes=lint", "-disable-output", str(image)], capture_output=True, text=True)
    lines = lint.stderr.splitlines()
    problems = []
    for index, line in enumerate(lines):
        if not re.match(r"Undefined behavior: Call (argument count|argument type|return type) mismatches", line):
            continue
        call = lines[index + 1].strip() if index + 1 < len(lines) else ""
        callee = re.search(r"@(\"?[\w.$]+\"?)\(", call)
        name = callee.group(1).strip('"') if callee else "?"
        # a call that discards a return value it declared void is harmless
        if "return type" in line and re.search(r"\bcall void\b", call):
            continue
        if name in ALLOWED:
            continue
        problems.append(f"{line.split(': ', 1)[1]}: {call}")
    dis = subprocess.run([llvm_tool("dis") or "llvm-dis", str(game), "-o", "-"], capture_output=True, text=True)
    if dis.returncode:
        print("FAIL: llvm-dis", dis.stderr.strip()[:2000])
        return 1
    problems += extension_mismatches(dis.stdout)
    print(f"guest units: {len(main_units)} game/port/library + {len(musl_units)} musl")
    if problems:
        print("FAIL: calls whose declaration differs from the definition (miscompiled on arm64_32):")
        for problem in sorted(set(problems)):
            print("  " + problem)
        return 1
    print("PASS: every direct guest call matches its callee's definition (count, types, extensions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
