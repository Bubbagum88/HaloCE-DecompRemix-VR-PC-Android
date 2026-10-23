#!/usr/bin/env python3
"""Builds one native port in one configuration, as the GitHub workflow does
(.github/workflows/build.yml), and collects what it built into dist/:

    python tools/ci_build.py linux debug
    python tools/ci_build.py android release

Builds are portable (any x86-64 processor), so they run on other
computers. Debug builds skip link-time and profile-guided optimisation,
which only make the build slower; release builds use both, as a local
release build does (profile-guided optimisation needs clang 22 or later,
and is skipped with an older one). CI_COMPILER_LAUNCHER (ccache, say) is
passed on as --compiler-launcher. A build of the main branch gets the run's
number (HALO_BUILD_NUMBER), which its release is named after and the
self-updater compares.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# what each port's build leaves, and what goes into dist/
OUTPUTS = {
    "linux": ["build/linux/halo"],
    "windows": ["build/windows/halo.exe", "build/windows/SDL3.dll"],
    "android": [],  # the APK, below
}
APKS = {
    "debug": "port/android/app/build/outputs/apk/debug/app-debug.apk",
    "release": "port/android/app/build/outputs/apk/release/app-release.apk",
}


def run(command, cwd=ROOT):
    print("+", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("platform", choices=sorted(OUTPUTS))
    parser.add_argument("config", choices=["debug", "release"])
    args = parser.parse_args()

    configure = [sys.executable, "configure.py", "--portable"]
    if args.config == "release":
        configure.append("--release")
    else:
        configure += ["--lto=off", "--pgo=off"]
    launcher = os.environ.get("CI_COMPILER_LAUNCHER")
    if launcher:
        configure += ["--compiler-launcher", launcher]
    # a build of main knows its number, which names its release (build-<n>),
    # for the self-updater (port/linux/src/updater.c, and the Android app);
    # other builds have none, and never look for updates
    if os.environ.get("GITHUB_REF") == "refs/heads/main" and os.environ.get("GITHUB_RUN_NUMBER", "").isdigit():
        os.environ["HALO_BUILD_NUMBER"] = os.environ["GITHUB_RUN_NUMBER"]
        print(f"build number {os.environ['HALO_BUILD_NUMBER']}", flush=True)
    run(configure)

    if args.platform == "android":
        # the native part, then the app around it (Gradle's variant of the
        # same name: release is signed with the debug key, not debuggable)
        run(["ninja", "android"])
        gradlew = "gradlew.bat" if os.name == "nt" else "./gradlew"
        run([gradlew, "--console=plain", "-q", f"assemble{args.config.capitalize()}"], cwd=ROOT / "port/android")
        outputs = [APKS[args.config]]
    else:
        run(["ninja", args.platform])
        outputs = OUTPUTS[args.platform]

    dist = ROOT / "dist" / f"halo-{args.platform}-{args.config}"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    for output in outputs:
        shutil.copy2(ROOT / output, dist)
        print(f"{output} -> {dist.relative_to(ROOT)}", flush=True)
    if args.platform == "windows":
        # the symbols of halo.exe and SDL3.dll, apart (players do not need
        # them), which turn a crash's addresses into functions and lines in a
        # debugger. (port: only those built; OpenCE's crash reporting, which
        # sends minidumps to Sentry, is not taken)
        symbols = ROOT / "dist" / f"halo-windows-{args.config}-symbols"
        if symbols.exists():
            shutil.rmtree(symbols)
        symbols.mkdir(parents=True)
        for pdb in [ROOT / "build/windows/halo.pdb", *sorted((ROOT / "build/windows/third_party").glob("SDL3-*/lib/x86/SDL3.pdb"))]:
            if not pdb.exists():
                continue
            shutil.copy2(pdb, symbols)
            print(f"{pdb.relative_to(ROOT)} -> {symbols.relative_to(ROOT)}", flush=True)
    # OpenCE's own licence, the AGPL, which asks each copy to carry its text
    # (the code before its change, CC0, is LICENSES/CC0-1.0.txt)
    shutil.copy2(ROOT / "LICENSE", dist / "LICENSE.txt")
    shutil.copy2(ROOT / "LICENSES/CC0-1.0.txt", dist / "CC0-1.0.txt")
    if args.platform == "linux":
        # the self-updater's TLS (port/third_party/mbedtls), whose Apache
        # license asks binaries to carry its notice
        shutil.copy2(ROOT / "port/third_party/mbedtls/LICENSE", dist / "mbedtls-LICENSE.txt")
    # internet play's UPnP (port/third_party/miniupnpc), in every build,
    # whose BSD license asks binaries to carry its notice
    shutil.copy2(ROOT / "port/third_party/miniupnpc/LICENSE", dist / "miniupnpc-LICENSE.txt")
    # voice chat's Opus codec, whose BSD license asks binaries to carry its notice
    shutil.copy2(ROOT / "port/third_party/opus/COPYING", dist / "opus-COPYING.txt")
    # the text's fonts (port/assets/fonts), embedded in every build, whose
    # SIL Open Font License asks each copy to carry it
    shutil.copy2(ROOT / "port/assets/fonts/Overpass-OFL.txt", dist / "Overpass-OFL.txt")
    # the menus' XML parser (port/third_party/expat), in every build, whose
    # MIT license asks copies to carry its notice
    shutil.copy2(ROOT / "port/third_party/expat/COPYING", dist / "expat-COPYING.txt")
    # voice chat's speaker icons and the Mods menu's warning icons
    # (port/assets/icons/lucide, drawn into the menus' bitmaps), whose ISC
    # license asks copies to carry its notice
    shutil.copy2(ROOT / "port/assets/icons/lucide/LICENSE", dist / "lucide-LICENSE.txt")
    # internet play's MQTT brokers, a file beside the game (network.brokers_file;
    # Android's APK has its own copy). HaloCE-Quest-VR: this port builds its
    # broker list in (p2p_signal.c), and has no such file yet
    if args.platform != "android" and (ROOT / "port/assets/network/brokers.txt").exists():
        shutil.copy2(ROOT / "port/assets/network/brokers.txt", dist / "brokers.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
