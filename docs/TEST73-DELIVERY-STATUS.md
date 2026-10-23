# Test73 delivery status

Private **1.0.40-test73 / version code 85**, branch `test39-interaction-completion`. Every VR feature on
once with the update, co-op VR for every player (VR INTERACTIONS, on by default), OpenCE Build 256 with its
testing and fix-scenery-shields-network branches (network 34), stencil shadows that keep the dynamic lights,
the Steam Frame checked against Lepton 3.0.8 and the other Halo CE Frame ports, and the owner's items
(TEST73-CHECKLIST.md). Test72 (1.0.39) and Test71 (1.0.38) travel with it. Local commits only: no push, tag,
publish or install.

## Builds and source

Folder: `D:\HaloQuest\builds\test73-20261022-v1.0.40-test73`

Every package was built from runtime source `fcaa04e39b152511b2080be97131858598d9be9d`, the tree clean
after it. This record follows it in a commit of its own and changes no runtime file.

| Package | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test73.apk` (Quest, Pico, Steam Frame) | 76,039,308 | `1b90e2124b44a77d7568da9b73eb55cf21e03eba475f2d399225e574a4b9067b` |
| `HaloCE-Android-test73.apk` (phones, tablets) | 73,570,140 | `ed23553b93be57d4e8ef7df5f94f200b13cdea74e062939f04a835a2d2fae46e` |
| `HaloCE-Windows-test73.zip` (flat, PC VR, launcher) | 28,211,259 | `d5ade1a9b840945591a69d154da9c0f2e1cace1034f265f73a6b70e4a99ad190` |
| `HaloCEQuestVR-SteamFrame.zip` (the Steam Frame, installed on it, no computer) | 76,046,079 | `786ef5f35c90de24012a16a3180f15a2d49588fbffb4b745e4eb00029a870275` |
| `HaloCE-Quest-test73-build.zip`, `HaloCE-Quest-test73-source.zip` | | in `SHA256SUMS.txt` beside them (they carry this record) |

- Quest package `com.halo.decomp.vr`, Android `com.halo.decomp`: version `1.0.40-test73`, code **85**, ARM64,
  min SDK 28; signing certificate SHA-256 `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
  (unchanged; `tools/package-quest.py` checked both). Install over Test72, Test70 or Test69 without
  uninstalling.
- Windows zip: `halo.exe` (2728771c…), `halo-vr.exe` (33c70000…), `SDL3.dll` (SDL 3.4.16),
  `openxr_loader.dll` (OpenXR 1.1.63), README, the AGPL as LICENSE.txt, CC0-1.0.txt, CREDITS and notices.
- Steam Frame bundle (`tools/steam_frame/bundle.py`): the same VR APK as `HaloCEQuestVR.apk`, with
  `install.sh`, `launch.sh`, "Install HaloCE Quest VR.desktop" and a README. Unpacked in the Frame's
  Downloads (Desktop Mode), its installer adds the game to the Steam library (docs/VR_ARCHITECTURE.md).
- Toolchain: Android NDK 27.2.12479018 with clang 18 (the PGO profiles need clang 22: built without them,
  as before), Gradle, build-tools 36.0.0; Windows: LLVM clang for i686-pc-windows-msvc with lld.
- Gate: the whole suite on this tree, 196 of 196 (`tools/run-quest-checks.py`); the VR and the flat Android
  builds with no warnings, the guest Opus tables check and the guest ABI lint (799 + 923 units) passing,
  then Gradle; `windows_vr` and `windows` full rebuilds with no warnings. The VR build found one error,
  fixed before the commit: `d3d8_gl.c`'s declaration of `custom_edition_cache_tags_loaded` was seen only by
  the flat build. `tools/package-quest.py` checked both APKs' identity, markers, networking parity and
  signatures.
- **Not run**, the owner's call ("just skip the running checks and provide the builds if possible. i will
  test it all myself"): the build pass's runtime checks (the scopes per weapon, the co-op two-instance run,
  a fresh profile's levels, a PC VR smoke run, the desktop cursor, the stencil shadows' frames), and the PC
  launcher's saves import and export (the owner's).

## How far each platform is verified

Levels: **implemented**, **built** (compiles, links, packages), **runtime-validated** (run here, off the
headset), **hardware-tested**.

| Platform | Package | Implemented | Built | Runtime-validated | Hardware-tested |
|---|---|---|---|---|---|
| Quest 3 / 3S / Pro / 2 | VR APK | yes | yes | no (no headset here) | the owner's tests pending |
| Pico 4 / Neo 3 / 4 Ultra | VR APK | yes | yes | no | no |
| Steam Frame | VR APK, Steam Frame bundle | yes | yes | no | no |
| Android phones and tablets | flat APK | yes | yes | no | the owner's tests pending |
| Windows, flat | `halo.exe` + launcher | yes | yes | not this build (Test73's earlier builds: the render guard, the menus, the visibility tests) | no |
| Windows, PC VR | `halo-vr.exe` | yes | yes | not this build (Test73's earlier builds on SteamVR's null driver: the menus' world and follow modes, grenades in the hand, the played character's arms) | no |

## What changed

TEST73-CHECKLIST.md (every item and how far it is verified), TEST73-FIELD-GUIDE.md (the players' notes),
TEST73-DEVICE-CHECKLIST.md (what to try on each device) and HANDOFF-2026-10-22b.md (the state, and what the
owner should know).
