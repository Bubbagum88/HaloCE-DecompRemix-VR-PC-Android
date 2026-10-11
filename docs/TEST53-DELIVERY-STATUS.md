# Test53 delivery record

Private owner-test candidate **1.0.20-test53 / Android version code 65**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `D:\HaloQuest\builds\test53-20261011-v1.0.20-test53`
- Source commit of both APKs: `6a961c167029c26ea17d13de38781b98f033d8ac`
  (branch `test39-interaction-completion`; later commits change only docs)
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over v1.0.19 (code 63) keeping settings, saves and game data.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest (as v1.0.18), NDK
  27.2.12479018, build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test53.apk | `9f874e42c82fc275169956b739e50684efe912a238d66841d9613c6411e87aa3` |
| HaloCE-Android-test53.apk | `058c0ccdcf6a82deafcb4e590a437200c178da714aeea8f357e6baa82373866f` |
| HaloCE-Quest-test53-source.zip | `126f3011c8647b8b940eb79415bce5c61aa4b76bb4eec2124a36b7a353c5b7b0` |
| HaloCE-Quest-test53-build.zip | `7fecc3ccbf48700d8edf8880d55b303d6743edb97f5c2c0b9b8e6fb7d4b22a57` |
| manifest.json | `ec30ea37fe31c3e034280703347b9d3fff9ba9fd3a55de1f5e3657fe9b6791cc` |
| compatibility.json | `b941c1dd58696569fcd05b55c43733739ce2c45bc8644562dc5dc8292c25f379` |

Guest images: VR `0db52665…4989`, Android `49057fae…d584`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, 111 suites): after the
  crash fix, after the features, and inside each flavor's
  `tools/build-quest.sh` run: **Failed suites: []** for VR and flat.
- After each flavor's build: the built guest's Opus pulse-cache tables match
  the source; `tools/android_guest_abi_lint.py`: every direct guest call
  matches its callee (716 game/port/library + 924 musl units).
- `tools/package-quest.py`: certificate, package names, arm64 ABI, version
  name/code, networking parity between the APKs, ZIP integrity, launcher
  artwork/fonts, bundled guide markers, VR identity and upstream markers.
- Independent re-check of the delivered files: both guests' `cache_bits50`,
  `cache_index50`, `cache_caps50` match the Opus source (Test51's differed
  at byte 338); `apksigner` certificate; `aapt` version; `sha256sum -c`.
- `compatibility.json`: native networks 11–26.

## Boundary

Host checks, builds and the reproduction do not prove device behavior. Voice,
network 26 play and every immersion feature await the owner's Quest and phone
results: [TEST53-DEVICE-CHECKLIST.md](TEST53-DEVICE-CHECKLIST.md). Outcomes per
item: [TEST53-CHECKLIST.md](TEST53-CHECKLIST.md).
