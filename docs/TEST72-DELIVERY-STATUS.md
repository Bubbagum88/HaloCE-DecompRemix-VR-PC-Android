# Test72 delivery status

Private **1.0.39-test72 / version code 84**, branch
`test39-interaction-completion`. Test70 (published as v1.0.37) plus Test71
(never delivered on its own) plus the Test72 multi-platform work, the
owner's VR refinement pass and this round (shot deflection, OpenCE 208,
HaloFreak95's build, testers' reports, VR third person, the Android
controller and save fixes). Local commits only: no push, tag, publish or
install.

## Builds and source

Folder: `D:\HaloQuest\builds\test72-20261016-v1.0.39-test72`

Every package was built from runtime source
`0b66c841ecf61da10cfa4b06cd54fa10ab2d8d11`, the tree clean before and after.
This record follows it and changes no runtime file.

| Package | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test72.apk` (Quest, Pico, Steam Frame) | 74,848,071 | `58c24de69ce6d808bb36aa4a906f28d3a329bf97dec53a218193187d65b668f2` |
| `HaloCE-Android-test72.apk` (phones, tablets) | 72,429,772 | `2fef4dc3bb034029d88fa0ac65f831f27c748ab58477517701742e9f8bb73eb3` |
| `HaloCE-Windows-test72.zip` (flat, PC VR, launcher) | 26,073,994 | `f3583cdcff9c53e747552a48875d29510920e840ff44247d3af70be3d672aea7` |
| `HaloCE-Quest-test72-build.zip` | 62,617,350 | `3ca6d786abf4a47ea2d8c47cf91914047b8e442634f2465d901c2a5344aa2f9b` |
| `HaloCE-Quest-test72-source.zip` | 26,729,623 | `6d2e8dadcf036db94b3032925d19b0a4d4654c5d200cb61726a0d74a56293beb` |

- Quest package `com.halo.decomp.vr`, Android `com.halo.decomp`: version
  `1.0.39-test72`, code **84**, ARM64, min SDK 28; signing certificate
  SHA-256 `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
  (unchanged). Install over Test70 or Test69 without uninstalling.
- Windows zip: `halo.exe` (e0cb1636…), `halo-vr.exe` (c50f100b…), `SDL3.dll`
  (SDL 3.4.16), `openxr_loader.dll` (OpenXR 1.1.63), README, licenses and
  notices. Fonts, menus and the high-res HUD are inside the executables.
- Toolchain: Android NDK 27.2.12479018 with clang 18 (the PGO profiles need
  clang 22: built without them, as before), Gradle 9.7.1, build-tools
  36.0.0; Windows: LLVM clang for i686-pc-windows-msvc with lld.
- Gate: `tools/build-quest.sh vr` ran the whole suite (171 suites, none
  failed), the guest Opus tables check and the guest ABI lint; the flat APK
  ran the same steps but the suite (just passed on the same tree);
  `tools/package-quest.py` checked both APKs' identity, markers and
  signatures. The Windows zip was extracted outside the checkout and run
  (menus, HUD, a hosted Blood Gulch game).

## How far each platform is verified

Levels: **implemented**, **built** (compiles, links, packages),
**runtime-validated** (run here, off the headset), **hardware-tested**.

| Platform | Package | Implemented | Built | Runtime-validated | Hardware-tested |
|---|---|---|---|---|---|
| Quest 3 / 3S / Pro / 2 | VR APK | yes | yes | no (no headset here) | owner's tests pending |
| Pico 4 / Neo 3 / 4 Ultra | VR APK | yes | yes | no | no |
| Steam Frame | VR APK | yes | yes | no | no |
| Android phones and tablets | flat APK | yes | yes | no | owner's tests pending |
| Windows, flat | `halo.exe` + launcher | yes | yes | menus, campaigns and hosted games run; stereo 3D measured; holstered guns, rifle display, fast decals seen on frames; a host took three system-link bots | no |
| Windows, PC VR | `halo-vr.exe` | yes | yes | SteamVR null driver: session FOCUSED, b30 at 40-60 fps, VR THIRD PERSON engaged and seen in the eye dump | no |

## What changed

See TEST72-CHECKLIST.md (every item and its verification),
TEST72-FIELD-GUIDE.md (the player's view; the in-app guide's first
section), TEST72-HALOFREAK95.md (that review) and TEST72-DEVICE-CHECKLIST.md
(what only the hardware can confirm).

## Open

- Headsets: everything VR is runtime-validated only on PC VR's null
  driver; Quest, Pico and Steam Frame await the owner's tests.
- The left eye's garbling: the fix and EYE ORDER test await the owner.
- Shot deflection, grenades, the Shade, VR third person: feel on a headset.
- Android: the reporter's controller; the VPN join (the cause is likely,
  not proven; the log now says what happens); save import on a phone.
- Two copies of the game on one PC cannot play together (the host tells
  machines apart by address): a test limit, not a regression.
- Loading a map by the console from the main menu with the scripted bot
  input can stop on a stale menu sound (seen in testing only, with and
  without this round's changes); not a player path.
