# Test57 delivery record

Private owner-test candidate **1.0.24-test57 / Android version code 69**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test57-20261011-v1.0.24-test57`
- Source of both APKs: commit `221db6108cfa48e0fac23cd25be24bc58343f29d`
  (branch `test39-interaction-completion`): the Test57 changes (`5553d6f9`,
  `82d86ffe`) on the Test56 delivery, plus the bundled guide files the
  build generated from them. Later commits change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test56 (code 68) and earlier, keeping settings, saves and
  game data.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test57.apk | `9b8e6b398b64f84cfc33f4b5a29e7e460a878a70ef7594fd3ba32070ea02ccde` |
| HaloCE-Android-test57.apk | `4981237a46bf4e85d427dcaefdfd20a77a5ed9ed3e7f7ca472b86ab2a2d884d0` |
| HaloCE-Quest-test57-source.zip | `9f300b5b3cf6bf75a86f7193766174c0f1996d7e4ef502701442dfc182eed3d9` |
| HaloCE-Quest-test57-build.zip | `22a34f518164f251903a5a971387a08e91839d4522774333976c8224fa80d454` |
| manifest.json | `0845095bd358e1d8b4a6f0118083978f60ed56f084b7bd955be11d13c9aaeec3` |
| compatibility.json | `8c27059797d54fc669e3944a2552a373ecfeaafb73d6df7425a43e7e910ce171` |

Guest images: VR `e202aa70…762d`, Android `31c82542…3a00`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, including the new
  `test_test57_vehicles` and the updated `test_test38_vehicle_handles`):
  **Failed suites: []** inside each flavor's `tools/build-quest.sh` (VR and
  flat).
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee (`tools/android_guest_abi_lint.py`).
- `tools/package-quest.py --label test57`: certificate, package names, ABI,
  version 1.0.24-test57 / code 69, networking parity, ZIP integrity, launcher
  assets, bundled Test57 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.
- Stock-data checks (USA Xbox disc, read-only): the Warthog's wheel node and
  grip markers; the first-person assault rifle's "frame safety button" in
  its idle, moving, firing, ready and overlay animations.

## Boundary

Host checks and builds do not prove headset behaviour. Every Test57 change
awaits the owner's Quest and phone results:
[TEST57-DEVICE-CHECKLIST.md](TEST57-DEVICE-CHECKLIST.md). Outcomes per item:
[TEST57-CHECKLIST.md](TEST57-CHECKLIST.md).
