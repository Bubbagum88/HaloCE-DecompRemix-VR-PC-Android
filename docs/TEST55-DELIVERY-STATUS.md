# Test55 delivery record

Private owner-test candidate **1.0.22-test55 / Android version code 67**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test55-20261011-v1.0.22-test55`
- Source of both APKs: commit `dd18462bf61c8fe1e7f1b6f0fe6f60ec79381f07`
  (branch `test39-interaction-completion`): the Test55 change `64bc7e48`
  plus the bundled guide files the build generated from it. Later commits
  change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test54 (code 66), Test53 and v1.0.19, keeping settings, saves
  and game data.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test55.apk | `f84fae5e5bfe5fcc86125d51cb5bc15e867191bef36160817b8c6dc815300687` |
| HaloCE-Android-test55.apk | `ca2f94be48e63939a67c7cfcc3315f2c2b0c60ab522f7f18d85be6830e4c53f4` |
| HaloCE-Quest-test55-source.zip | `180237502f62b3a8c4ab70e5593f317d3c2f5eed5e2e62497c6b9e7fec24f6ca` |
| HaloCE-Quest-test55-build.zip | `1f27d1c0d9cf67fe69abdfdaa85754b1817e5b8fc44ee37f1a6ead7b4c53aa9e` |
| manifest.json | `eb5b9cb7769146cae20374a35f28ccc317b16b9994d0ab18ee85c5590e8ed6f8` |
| compatibility.json | `1f921a3f5bb1b2a6cd18d47d459a49ff7494cfc1e5eb81a09ed802b07b59fe44` |

Guest images: VR `de463bea…7628`, Android `bc171fc3…c9ef`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, now including
  `test_test55_polish`) inside each flavor's `tools/build-quest.sh`:
  **Failed suites: []** for VR and flat.
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee (`tools/android_guest_abi_lint.py`).
- `tools/package-quest.py --label test55`: certificate, package names, ABI,
  version 1.0.22-test55 / code 67, networking parity, ZIP integrity, launcher
  assets, bundled Test55 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.
- Stock-data research used the owner's USA Xbox XISO (maps extracted
  read-only to <workspace>\_scratch\xbox_usa\maps).

## Boundary

Host checks and builds do not prove headset behaviour. Every Test55 change
awaits the owner's Quest and phone results:
[TEST55-DEVICE-CHECKLIST.md](TEST55-DEVICE-CHECKLIST.md). Outcomes per item:
[TEST55-CHECKLIST.md](TEST55-CHECKLIST.md).
