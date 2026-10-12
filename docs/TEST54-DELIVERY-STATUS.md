# Test54 delivery record

Private owner-test candidate **1.0.21-test54 / Android version code 66**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test54-20261011-v1.0.21-test54`
- Source commit of both APKs: `938a044858fe970012845e1e71886677c818089a`
  (branch `test39-interaction-completion`; later commits change only docs)
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test53 (code 65) and v1.0.19 (code 63), keeping settings,
  saves and game data.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test54.apk | `ad022d35f89bb467d8910b9b5904e7bfd5f0b3350bf62757620fee53b646b4db` |
| HaloCE-Android-test54.apk | `e338bd0cfcb01985a7c21e38d655be56f7eeee86b64b14f97e74a6261d65232b` |
| HaloCE-Quest-test54-source.zip | `a674abbfe7917559e10232de61839d3e36a96a632b383ffbb394da3acb694f8b` |
| HaloCE-Quest-test54-build.zip | `268cc5dceaab7e1074943c37393a069d2a1bb563141fc980f6d74500195f37d7` |
| manifest.json | `509ede30ab783ce32b343e0f3311e7b159bf088eef773f9648f486f32e3b720a` |
| compatibility.json | `d8b2bf3fca56c96f7df7f4b3e02dead4b6597fba7404fa66b914ca6a8a13f592` |

Guest images: VR `1b6e1175…2657`, Android `e9a44ee2…c10d`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, now including
  `test_test54_interactions`) inside each flavor's `tools/build-quest.sh`:
  **Failed suites: []** for VR and flat.
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee (`tools/android_guest_abi_lint.py`).
- `tools/package-quest.py --label test54`: certificate, package names, ABI,
  version 1.0.21-test54 / code 66, networking parity, ZIP integrity, launcher
  assets, bundled Test54 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.

## Boundary

Host checks and builds do not prove headset behaviour. Every Test54 change
awaits the owner's Quest and phone results:
[TEST54-DEVICE-CHECKLIST.md](TEST54-DEVICE-CHECKLIST.md). Outcomes per item:
[TEST54-CHECKLIST.md](TEST54-CHECKLIST.md). Online scope:
[TEST54-NETWORK.md](TEST54-NETWORK.md).
