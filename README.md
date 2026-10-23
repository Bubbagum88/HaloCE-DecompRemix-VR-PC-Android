<p align="center"><img src=".github/decomplogo.png" alt="Halo Combat Evolved VR — OpenCE port" width="460" /></p>

<h1 align="center">Halo CE Decomp Remix — VR, PC & Android</h1>

<p align="center">An unofficial OpenCE-based community port for Meta Quest, PICO and Steam Frame VR, Windows flat PC and PC VR, and flat Android phones and tablets.</p>

**Latest: [1.0.41 — Test73b Multi-Platform Release](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/tag/v1.0.41).** This is a large cumulative update from 1.0.37. Read the install and WIP notes before playing.

> **Experimental / WIP:** fist combat and projectile deflection, sliding, parkour, physical reload, ragdolls and body interactions, immersive vehicle controls, and broad support for user-supplied mods still need refinement and device reports. Enable experimental options one at a time. Project Lumoria and SPV1 have specific setup paths; this does not mean every mod works. MCC maps and The Altheros Experience remain experimental.

## Downloads

| Platform | Download |
| --- | --- |
| Android phone/tablet — flat | [HaloCE-Android-1.0.41.apk](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Android-1.0.41.apk) |
| Meta Quest — standalone VR | [HaloCE-Quest-1.0.41.apk](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Quest-1.0.41.apk) |
| PICO — standalone VR | [Universal VR APK](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Quest-1.0.41.apk) |
| Windows — flat PC and PC VR | [HaloCE-Windows-1.0.41.zip](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Windows-1.0.41.zip) |
| Steam Frame — installer bundle | [HaloCE-SteamFrame-1.0.41.zip](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-SteamFrame-1.0.41.zip) |

See the [complete release notes](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/docs/RELEASE-1.0.41.md) for separate install instructions. Existing Android/VR users should install over the old app; **do not uninstall or clear app data** to preserve saves, settings and imported files. APK identity is 1.0.41-test73b / code 86. The app contains no Halo game data. The original Xbox XISO remains the recommended baseline.

## Highlights and compatibility

- **VR third person:** an over-the-shoulder camera for on-foot campaign and co-op, under VR Settings → Gameplay → Third Person. Physical hand interactions suspend while active and restore on exit. PvP is excluded. This exact build still needs headset validation.
- **VR body and shadows:** the player body casts a shadow; stencil shadows were restored to the HALOFREAK95/OpenCE-fork behavior.
- **Controllers and menus:** B returns from menus on all controllers; A/B/X/Y keep their labelled actions. A CONTROLS page is in each launcher.
- **Movement:** VR Sprint Toggle is the default, Bullet Time works across supported controllers, Android touch has a Sprint button, and Windows flat uses Left Shift.
- **World Scale:** VR Settings → Comfort, adjustable from 70% to 150%.
- **Map sharing:** default upload limits are 20 MB/s for hosts and 10 MB/s for helpers; lower Server Setup → Map Sharing → Upload Limit if the host connection saturates.
- **Held bodies:** a corpse stays visible where held when used as a shield.
- **Logs:** Windows launcher LOGS page; Windows and Steam Frame retain ten runs.
- **Included platforms:** standalone VR on Quest/PICO/Steam Frame, flat Android, Windows flat PC and PC VR, plus the Steam Frame installer.
- **Networking:** OpenCE Build 256/network 34, joining compatible network versions 11–34, in-game server browser, campaign hosting/co-op, voice and map sharing. Co-op supports ordinary campaign play; very high player counts are not validated.

Fist combat/deflection, sliding, parkour, manual reload, physical grenades, ragdolls/body interaction, immersive vehicles and broad mod support remain experimental/WIP. Reports for PC graphics settings, post-Flood camera behavior, a possible Wrist HUD report and The Maw bridge countdown need session logs.

### Installation notes

- **Android:** download the flat APK, open it from Downloads, allow the chosen file manager/browser to install apps if prompted, then import your own game image.
- **Quest:** enable Developer Mode; install the VR APK through SideQuest or ADB (adb install -r), then import your game image.
- **PICO:** sideload the same universal VR APK through ADB or a compatible utility. This exact build has not been tested on PICO hardware.
- **Windows flat:** extract the Windows ZIP with its DLLs together, start halo.exe, import your ISO/XISO under GAME DATA and choose PLAY.
- **Windows PC VR:** configure an **OpenXR runtime (recommended)** such as SteamVR, Quest Link, Virtual Desktop or PICO Connect, then start halo.exe and choose PLAY IN VR.
- **Steam Frame:** in Desktop Mode download and extract its ZIP in Downloads, run Install HaloCE Quest VR.desktop, then return to Gaming Mode and launch from Steam.

The Test73b candidate passed 203/203 automated suites and its Android/Windows build checks. It was not launched in a game or headset during packaging; device/runtime testing is requested. See the [Test73b field guide](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/docs/TEST73B-FIELD-GUIDE.md), [controls](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/docs/CONTROLS-AND-OPTIONS.md), [Android touch guide](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/docs/ANDROID-TOUCH-CONTROLS.md), and [full release notes](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/docs/RELEASE-1.0.41.md).

## Support and project

Please report both failures and successful tests, especially for fist combat/deflection, sliding, ragdolls, campaigns, vehicle options, and co-op. Include device and OS, app and network version, selected game-data set, map/mission, relevant settings, steps to reproduce, and the log of the run it happened in (where each device keeps it, below). For co-op, logs from both players help. Remove private invites/device details before public posting.

| Device | Each run's log |
| --- | --- |
| Quest, PICO, Android | **Download/HaloCE**: `halo_log_<date>_<time>.txt`, the newest the last run, the last ten kept (the game's own `debug.txt` lines are in it). A copy of the last run's: `Android/data/<package>/files/halo_log.txt`. |
| Steam Frame | **Documents/HaloCEQuestVR/logs** (Desktop Mode's file manager): `halo_log_<date>_<time>.txt`, the last ten kept. Beside that folder: `launcher.log` (each start from Steam), `logcat.txt` (the last run's Android log), `install.log` (the installer's). |
| Windows | Beside the game: `halo.log` (`halo.exe`) and `halo-vr.log` (`halo-vr.exe`, PC VR), the last run's; the ten runs before each in **logs** (`halo_<date>_<time>.log`, `halo-vr_<date>_<time>.log`). The game's own `debug.txt` is in the game data folder. The PC launcher's **LOGS** page opens these folders. |

Contact **@MeWhenINameMyself** by Discord DM, use the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx), or report in the [Flat2VR Halo CE discussion](https://discord.com/channels/747967102895390741/1555959498349215774). This build is intended to collect real-device feedback for the next refinement pass.

The repository/About description now reflects the expanded platform scope. This is an unofficial community project, not affiliated with Microsoft. No Halo game files are distributed. See [credits](CREDITS.md) and [third-party notices](THIRD-PARTY-NOTICES.txt).

## Licence

From Test73 on, this project is free software under the terms of the GNU Affero General Public License, version 3 or (at your option) any later version (`AGPL-3.0-or-later`), without any warranty; the full text is in [LICENSE](LICENSE).

- **Why:** this port merges OpenCE, which moved to the AGPL 3.0 or later with its commit 4b09168e7 (between its Builds 232 and 246), as the decompilation both build on did ([punpckhdq/halo](https://github.com/punpckhdq/halo), from 17 October 2026).
- **Before the change:** the code from before it, and every release of this project up to Test72 (v1.0.37 included), were released under [CC0 1.0](LICENSES/CC0-1.0.txt) and stay that way.
- **Source:** each release's source is offered with it (the release's source zip, and its tag).
- **Hosts and servers:** if you change the game and let other people play your version over a network (as an internet game's host, for example), the AGPL asks you to offer them your version's source (section 13).
- **Other parts:** third-party code, fonts and art keep their own licences, next to them and in [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt).
- **Halo is not covered:** the licence covers this project's and its upstreams' work, and gives no rights in Halo, its maps or anything else Microsoft owns.
