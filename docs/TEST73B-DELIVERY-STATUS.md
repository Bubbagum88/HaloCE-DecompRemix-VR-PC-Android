# Test73b delivery status

Private **1.0.41-test73b / version code 86**, branch `test39-interaction-completion`. Fixes and additions on
the delivered Test73: STENCIL SHADOWS as HaloFreak95 made them (Test73's change undone, no lighting change),
the VR body's shadow (stencil and the game's), B back in the menus on every controller (the Steam Frame's
report), map sharing at its most by default (20 MB/s hosting, 10 MB/s helping), every launcher's log locations,
SPRINT TOGGLE on TOGGLE by default with BUTTON SPRINT's fixes and BULLET TIME on every controller, the flat
builds' sprint (a SPRINT circle on Android's touch screen, Left Shift on PC), a CONTROLS page in every launcher,
held bodies drawn where they are held, and WORLD SCALE (TEST73B-CHECKLIST.md). Test73 (1.0.40), Test72 (1.0.39)
and Test71 (1.0.38) travel with it. Local commits only: no push, tag, publish or install.

## Builds and source

Folder: `D:\HaloQuest\builds\test73b-20261023-v1.0.41-test73b`

Every package was built from runtime source `a29762e0480412ebf7f550e30beb6a047965e801`, the tree clean after
it. This record follows it in a commit of its own and changes no runtime file.

| Package | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test73b.apk` (Quest, Pico, Steam Frame) | 76,069,753 | `8f7a10ddf25d89f20598f6526782606a7fd452677ffb6bc0877e6bb329255a1f` |
| `HaloCE-Android-test73b.apk` (phones, tablets) | 73,596,981 | `b4ffaeecc32dd3d52c295ecf2c619bc3fcea6b27c723fa3a609e409e0a5d6410` |
| `HaloCE-Windows-test73b.zip` (flat, PC VR, launcher) | 28,233,873 | `2e572f09c5d3aaff0d450bbbb4771ba6b25d95be7ef87292ab3d3ffab9dea216` |
| `HaloCEQuestVR-SteamFrame.zip` (the Steam Frame, installed on it, no computer) | 76,076,834 | `2028336af5a469ac6fd31f1d03b97201f4a4d93d5c830f7ea6a6822b8381c08c` |
| `HaloCE-Quest-test73b-build.zip`, `HaloCE-Quest-test73b-source.zip` | | in `SHA256SUMS.txt` beside them (they carry this record) |

- Quest package `com.halo.decomp.vr`, Android `com.halo.decomp`: version `1.0.41-test73b`, code **86**, ARM64,
  min SDK 28; signing certificate SHA-256 `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
  (unchanged; `tools/package-quest.py` checked both). Install over Test73, Test72, Test70 or Test69 without
  uninstalling.
- Windows zip: `halo.exe` (2abb2c11…), `halo-vr.exe` (1f51aa33…), `SDL3.dll` (SDL 3.4.16),
  `openxr_loader.dll` (OpenXR 1.1.63), README (Test73b's: the CONTROLS page, the logs), the AGPL as
  LICENSE.txt, CC0-1.0.txt, CREDITS and notices.
- Steam Frame bundle (`tools/steam_frame/bundle.py`): the same VR APK as `HaloCEQuestVR.apk` (byte for byte),
  with `install.sh`, `launch.sh`, "Install HaloCE Quest VR.desktop" and a README. Unpacked in the Frame's
  Downloads (Desktop Mode), its installer adds the game to the Steam library (docs/VR_ARCHITECTURE.md).
- Toolchain: Android NDK 27.2.12479018 with clang 18 (the PGO profiles need clang 22: built without them,
  as before), Gradle, build-tools 36.0.0; Windows: LLVM clang for i686-pc-windows-msvc with lld.
- Gate: the whole suite on this tree, 203 of 203 (`tools/run-quest-checks.py`); the VR and the flat Android
  builds with no warnings, the guest Opus tables check and the guest ABI lint (799 + 923 units) passing, then
  Gradle; `windows_vr` and `windows` full rebuilds with no warnings. No build found an error. Before the commit,
  `.gitignore` was found to keep the CONTROLS text (`assets/controls/controllers.txt`) out of the repository; an
  exception like the guide's lets it in (the APKs carried it already). `tools/package-quest.py` checked both APKs'
  identity, markers, networking parity and signatures.
- **Not run**, the owner's call for Test73 ("just skip the running checks and provide the builds if possible. i
  will test it all myself"), kept for Test73b: runtime checks of this build (the shadows' frames, the menus' B on
  each controller, the sprint toggle, the touch SPRINT circle, the CONTROLS pages on a device, a body held as a
  shield, WORLD SCALE in a headset, a PC VR smoke run).

## How far each platform is verified

Levels: **implemented**, **built** (compiles, links, packages), **runtime-validated** (run here, off the
headset), **hardware-tested**.

| Platform | Package | Implemented | Built | Runtime-validated | Hardware-tested |
|---|---|---|---|---|---|
| Quest 3 / 3S / Pro / 2 | VR APK | yes | yes | no (no headset here) | Test73 by the owner (Quest 3); Test73b pending |
| Pico 4 / Neo 3 / 4 Ultra | VR APK | yes | yes | no | no |
| Steam Frame | VR APK, Steam Frame bundle | yes | yes | no | Test73 by a player (their log); Test73b pending |
| Android phones and tablets | flat APK | yes | yes | no | the owner's tests pending |
| Windows, flat | `halo.exe` + launcher | yes | yes | no (this build) | a tester's report (its build not known); Test73b pending |
| Windows, PC VR | `halo-vr.exe` | yes | yes | no (this build) | no |

Off the device, each change's code runs in its test (TEST73B-CHECKLIST.md: [x] items), with negative controls.

## Reports with no change

Four reports came without a log, and nothing in the code or the maps' scripts explains them as a defect of this
port: the PC's GRAPHICS screen, a camera after 343 Guilty Spark's Flood cutscene, a HUD on the gun (WRIST HUD fits
it), and The Maw's bridge countdown (the map's own screen, as on the Xbox). TEST73B-CHECKLIST.md says what to ask.

## What changed

TEST73B-CHECKLIST.md (every item and how far it is verified), TEST73B-FIELD-GUIDE.md (the players' notes),
TEST73B-DEVICE-CHECKLIST.md (what to try on each device) and HANDOFF-2026-10-23.md (the state, and what the
owner should know).
