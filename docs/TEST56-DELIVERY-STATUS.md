# Test56 delivery record

Private owner-test candidate **1.0.23-test56 / Android version code 68**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `D:\HaloQuest\builds\test56-20261011-v1.0.23-test56`
- Source of both APKs: commit `71de2548a9e74745652bf1f2647b0bd74c74406d`
  (branch `test39-interaction-completion`): the Test56 changes
  (`46a18740`, `7221e1ac`, `edfdfc5e`, `3ad9b1b5`, `3c41de87`, `bcbba3d2`,
  `3362967a`) plus the bundled guide files the build generated from them.
  Later commits change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test55 (code 67), Test54, Test53 and v1.0.19, keeping
  settings, saves and game data.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test56.apk | `409c423ba9ff70945f91c389f64c07af8559395ba4086fef09a7a7dd94b7f672` |
| HaloCE-Android-test56.apk | `00ff37c099ba4223c0c0e62982c9ba35028e8318fef35dc4380eea9ab1bee873` |
| HaloCE-Quest-test56-source.zip | `4afa5772f192a113dd6bbe82428bef74bf715b21f007bd80e5b6cc7fe72ce595` |
| HaloCE-Quest-test56-build.zip | `643a7681dbbaa32a912d73adbc255945fcfaf6c7cb1d02ba70d447a0186897e6` |
| manifest.json | `219cfc841824ca22da5a45457f94fab3c7ad163ec98e9c2ce18e2254d6999bde` |
| compatibility.json | `f49f2f85c1367022ab38f2bbf609812fdc289b8a3ad6a06ea39000000ad9e7a1` |

Guest images: VR `958a7217…9936`, Android `669112af…28db`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, 114 suites including
  `test_test56_ragdoll` and `test_test56_polish`): **Failed suites: []**
  standalone, and inside each flavor's `tools/build-quest.sh` (VR and flat).
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee (`tools/android_guest_abi_lint.py`).
- `tools/package-quest.py --label test56`: certificate, package names, ABI,
  version 1.0.23-test56 / code 68, networking parity, ZIP integrity, launcher
  assets, bundled Test56 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.
- Ragdolls: an offline simulation of the production solver on the 12 stock
  character skeletons from the owner's USA Xbox disc (read-only), each dropped
  five ways: every body comes to rest. The Test55 solver left 56 of 78
  simulated cases unsettled.
- OpenCE: Builds 189 and 190 reviewed. Build 189 (Custom Edition map sharing)
  raises the network to 27 and is not taken; Build 190's host-only lobby
  countdown fix is. Network 26 unchanged.

## Boundary

Host checks and builds do not prove headset behaviour. Every Test56 change
awaits the owner's Quest and phone results:
[TEST56-DEVICE-CHECKLIST.md](TEST56-DEVICE-CHECKLIST.md). Outcomes per item:
[TEST56-CHECKLIST.md](TEST56-CHECKLIST.md).
