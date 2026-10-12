# Test58 delivery record

Private owner-test candidate **1.0.25-test58 / Android version code 70**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test58-20261011-v1.0.25-test58`
- Source of both APKs: commit `bb64af945aa671f15c0bb9765e5649962b0befb3`
  (branch `test39-interaction-completion`): the Test58 changes (`131edc83`,
  `2831e50a`, `55eb63a0`) on the Test57 delivery, plus the bundled guide
  files the build generated from them. Later commits change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test57 (code 69) and earlier, keeping settings, saves and
  game data.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test58.apk | `3a2b1b5b863152fac9a5b1ceb5f5cf9acf25b074875b5c806669e32092d03299` |
| HaloCE-Android-test58.apk | `a5586838e9cb6656a82c5e0598ef09861adcaf94f6f180b4670150d372e610b0` |
| HaloCE-Quest-test58-source.zip | `39f379de3c27d281974428ab0077c16eaea8addda9151449a559da5475dd1da9` |
| HaloCE-Quest-test58-build.zip | `9c19acbd44707cd54e04cc2f53aa921288c0baec396aafad1835dae8b7764737` |
| manifest.json | `c234570064fce04819c16a1aade32d8bc7943352d8a733bcae4085fa5687409f` |
| compatibility.json | `25eaa81f16cd11d0804bdcc1c4fd9c2c7cfb12ecb644e65e51e4c6cb1cf77fa8` |

Guest images: VR `9289da2c…6de4`, Android `cc76faa2…dfe3`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, including the new
  `test_test57b_vehicle_anchor`): **Failed suites: []** inside each flavor's
  `tools/build-quest.sh` (VR and flat). A first VR build failed three
  suites that pinned the old code (Test56's `node_matrix` line, the seat
  view's call order, a missing stub); they now pin the fix.
- `test_test57b_vehicle_anchor` replays the real control placement with
  engine-shaped markers at five places, headings and tilts; with the old
  line restored it fails (the Warthog's wheel 566 m away at Blood Gulch's
  spawn).
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee.
- `tools/package-quest.py --label test58`: certificate, package names, ABI,
  version 1.0.25-test58 / code 70, networking parity, ZIP integrity, launcher
  assets, bundled Test58 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.

## Boundary

Host checks and builds do not prove headset behaviour:
[TEST58-DEVICE-CHECKLIST.md](TEST58-DEVICE-CHECKLIST.md),
[TEST58-CHECKLIST.md](TEST58-CHECKLIST.md).
