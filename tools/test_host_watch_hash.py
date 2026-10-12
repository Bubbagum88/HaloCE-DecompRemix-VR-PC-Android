"""Run C tests of Android's page-hash write tracking without Android APIs."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def compiler():
    for name in ("clang", "cc", "gcc"):
        path = shutil.which(name)
        if path:
            return path
    return None


def main():
    host_main = (ROOT / "port" / "android" / "host" / "host_main.c").read_text(encoding="utf-8")
    host = (ROOT / "port" / "android" / "host" / "host_memory.c").read_text(encoding="utf-8")
    guest = (ROOT / "port" / "android" / "guest" / "runtime" / "guest_memory_watch.c").read_text(encoding="utf-8")
    renderer = (ROOT / "port" / "linux" / "src" / "d3d8_gl.c").read_text(encoding="utf-8")
    imports = (ROOT / "port" / "android" / "host_imports.list").read_text(encoding="utf-8").splitlines()
    assert '"ro.dalvik.vm.native.bridge"' in host_main
    assert 'host_memory_watch_use_hashes();' in host_main and '"debug.memory_watch"' in host_main
    assert "watch_hash_generation(&page_hashes" in host
    assert "host_memory_watch_begin_frame();" in guest
    assert "memory_watch_begin_frame();" in renderer
    assert "host_memory_watch_begin_frame" in imports
    cc = compiler()
    if not cc:
        raise SystemExit("no C compiler")
    with tempfile.TemporaryDirectory(prefix="host-watch-hash-") as directory:
        binary = Path(directory) / ("host_watch_hash_test.exe" if os.name == "nt" else "host_watch_hash_test")
        subprocess.run(
            [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O1",
             str(ROOT / "port" / "android" / "tests" / "host_watch_hash_test.c"),
             str(ROOT / "port" / "android" / "host" / "host_watch_hash.c"),
             "-o", str(binary)],
            check=True,
        )
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        print(result.stdout.strip())


if __name__ == "__main__":
    main()
