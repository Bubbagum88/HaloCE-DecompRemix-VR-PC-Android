# Test59 delivery record

Private owner-test candidate **1.0.26-test59 / Android version code 71**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test59-20261012-v1.0.26-test59`
- Source of both APKs: commit `3d34a101e8912814b96b10bd7daaee77892d6718`
  (branch `test39-interaction-completion`): the Test59 changes (`84cc50f3`
  vehicles, `96a907f5` OpenCE network 28, `6817b021` reload and DEATH
  FORCE, `53595225` blast throws, `97797a78` identity and docs, `9615ab4b`
  launcher test) on the Test58 delivery, plus the bundled guide files the
  build generated from them. Later commits change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test58 (code 70) and earlier, keeping settings, saves and
  game data.
- Network: hosts OpenCE network 28; joins 11-28; All compatible networks
  by default (manifest `native_host_version` 28, compatibility 11..28).
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test59.apk | `d7c66235564ba98e735d396b1cab34c653bd9276d74e145edb0613f1c9f1c63c` |
| HaloCE-Android-test59.apk | `9ff6a802f804e20cc7cbd46c8bd4383d1c99508b057d69372d2122672ab63224` |
| HaloCE-Quest-test59-source.zip | `284759a80e77c2302ac700dc3eac2ef80686622461a0a5963d134614f52cb4da` |
| HaloCE-Quest-test59-build.zip | `b854039e99937d8315f0084817950b16ea8ce83a3ea8b8f1ca1586c342bcb2f9` |
| manifest.json | `6991b71712f7603c04953318be6735a9c1b50f0889f9285d65554b79877dbf10` |
| compatibility.json | `fe4d458a6ab76d5a44e15855e2b963c7a62fa052ffc5c7427edbdb48061fabe2` |

Guest images: VR `ef7c71b4…7761`, Android `b5a6b1c0…5134`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, including the new
  `test_test59_network28` and `test_test59_reload_ragdoll`): **Failed
  suites: []** inside each flavor's `tools/build-quest.sh` (VR and flat). A
  first VR build failed `test_test37_launcher`, which still treated 27 as
  unsupported; it now selects 11-28 and refuses 29. An earlier stand-alone
  run found three pins of the old version / menu layout
  (`test_vr_immersion_menu`, `test_test19_network_browser`, `test_test26`),
  fixed before the builds.
- `test_test59_network28` replays the real map-sharing responder with
  valid and forged requests; `test_test56_ragdoll` adds DEATH FORCE's
  throws (rifle burst, rocket, HUGE rocket, HUGE sniper) for all 12 stock
  skeletons: each rests within the 5 s corpse hand-back.
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee.
- `tools/package-quest.py --label test59`: certificate, package names, ABI,
  version 1.0.26-test59 / code 71, networking parity, ZIP integrity,
  launcher assets, bundled Test59 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.

## Boundary

Host checks and builds do not prove headset behaviour:
[TEST59-DEVICE-CHECKLIST.md](TEST59-DEVICE-CHECKLIST.md),
[TEST59-CHECKLIST.md](TEST59-CHECKLIST.md).
