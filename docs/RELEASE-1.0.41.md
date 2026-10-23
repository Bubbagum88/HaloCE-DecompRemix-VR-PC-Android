# 🚨 MASSIVE MULTI-PLATFORM RELEASE — PLEASE READ

This is a large cumulative update from public **1.0.37**, bringing the intervening Test71–Test73b work into one release. The project now offers standalone VR, flat Android, Windows flat PC, Windows PC VR, and a Steam Frame installation bundle.

**VR third person is now included.** Choose **VR Settings → Gameplay → Third Person** for an over-the-shoulder view on foot in campaign/co-op. It is implemented in this build, but this exact release has not been headset runtime-tested by the packaging session. PvP is excluded. Physical hand interactions temporarily suspend while it is active and restore their previous state when switched off.

## 1. Installation and updating

| Platform | Download |
| --- | --- |
| Android phone/tablet — flat | [HaloCE-Android-1.0.41.apk](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Android-1.0.41.apk) |
| Meta Quest — standalone VR | [HaloCE-Quest-1.0.41.apk](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Quest-1.0.41.apk) |
| PICO headset — standalone VR | Use the same [universal VR APK](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Quest-1.0.41.apk) |
| Windows — flat PC and PC VR | [HaloCE-Windows-1.0.41.zip](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-Windows-1.0.41.zip) |
| Steam Frame — headset-side installer | [HaloCE-SteamFrame-1.0.41.zip](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/releases/download/v1.0.41/HaloCE-SteamFrame-1.0.41.zip) |

### Android phone/tablet
1. Download the Android APK on the device.
2. Open it from Downloads or your browser. If Android asks, allow that file manager/browser to install apps, then return to the APK and install.
3. Launch the app and import your own complete Halo CE game image under **Game files & versions**.

### Meta Quest
1. Enable Developer Mode and connect the headset to SideQuest, or enable USB debugging for ADB.
2. Download the Quest VR APK to a computer or the headset.
3. In SideQuest select **Install APK file from folder** and choose the APK, or run: adb install -r HaloCE-Quest-1.0.41.apk
4. Launch Halo CE Quest VR and import your game image under **Game files & versions**.

### PICO
1. Enable developer mode/USB debugging and connect with ADB or a compatible sideload utility.
2. Install the same universal VR APK with the utility, or run: adb install -r HaloCE-Quest-1.0.41.apk
3. Launch and import your own game image. The PICO build is included, but this exact release has not been run on PICO hardware.

### Windows flat PC
1. Download and extract the Windows ZIP to a writable folder. Keep the executables and DLLs together.
2. Run **halo.exe**; the launcher opens.
3. In **GAME DATA → IMPORT FROM A DISC IMAGE**, select your own Xbox Halo CE ISO/XISO and let the launcher scan it.
4. Choose **PLAY**. Flat PC and PC VR share this folder's game data, saves, profiles and configuration.

### Windows PC VR
1. Install and import game data using the Windows steps above.
2. Install/configure an OpenXR runtime. **OpenXR is the recommended PC VR path.** SteamVR, Meta Quest Link, Virtual Desktop and PICO Connect can provide an OpenXR runtime; make the runtime you intend to use the active OpenXR runtime first.
3. Run **halo.exe**, choose **PLAY IN VR**, and put on the headset. The bundle also contains halo-vr.exe.

PC VR is built, but this exact release has not had a PC-headset runtime test; results depend on headset, runtime and GPU setup.

### Steam Frame
1. In Desktop Mode, download the Steam Frame ZIP on the headset.
2. Extract it in Downloads with the file manager.
3. Run **Install HaloCE Quest VR.desktop** (or install.sh) to add the app to the Steam library. Return to Gaming Mode and launch it.
4. Import your own game image in the launcher. No computer-side installer is needed.

### Updating
For Android, Quest and PICO, install the matching APK over the existing app or use the built-in project updater when available. **Do not uninstall the app or clear its data** if you want to preserve saves, settings, profiles and imported files. Package IDs and signing certificate are unchanged. APK identity is **1.0.41-test73b / version code 86**; public release tag is **v1.0.41**.

For Windows, close the game and extract the new ZIP to a new folder or over the old program files while keeping game data, saves and configuration. On Steam Frame, rerun the installer from the new bundle. No Halo game data is included. The **original Xbox XISO** is the recommended compatibility baseline.

## 2. New features and major changes
- **VR third-person camera:** over-the-shoulder on-foot view for campaign/co-op. Head gaze aims; controller inputs handle weapon actions. Physical hand systems suspend while active and resume on exit. Not enabled in PvP; visual/device validation is still needed.
- **VR player-body shadow:** the body casts a shadow through the game's shadow path and stencil shadows.
- **Stencil-shadow correction:** restored to the behavior from the HALOFREAK95/OpenCE fork. No speculative lighting change was added.
- **Controller/menu behavior:** B returns from menus on every controller, including Steam Frame; A/B/X/Y retain their labelled actions. Each launcher now has a CONTROLS page for the current device.
- **Sprint and Bullet Time:** VR sprint defaults to Toggle on the movement-stick click; Button Sprint and left-handed mapping were refined. Bullet Time works across supported VR controllers. Android has an on-screen Sprint button with Hold/Toggle; Windows flat uses Left Shift.
- **World Scale:** VR Settings → Comfort, adjustable from 70% to 150%.
- **Map-sharing upload limits:** up to 20 MB/s for the host and 10 MB/s for helpers. Lower **Server Setup → Map Sharing → Upload Limit** if the host's upload connection saturates or gameplay lags during downloads.
- **Held corpses:** a body remains drawn at the hands while used as a shield.
- **Logging:** Windows has a launcher LOGS page; Windows and Steam Frame retain the latest ten runs.
- The release also includes the cumulative work since 1.0.37: Windows flat PC/PC VR and Steam Frame packaging; universal VR support for PICO; OpenCE in-game server browser and hosting; campaign co-op and voice chat; network and game-revision selection; Android touch/gamepad improvements; flat Android third person; VR full-body/finger work, holsters/scopes, physical reloads/grenades, NPC/world interaction, vehicle options, Jolt ragdolls and graphics/effect options.

## 3. Controls and inputs
- Use each launcher's **CONTROLS** page for controller/keyboard mappings.
- **VR Sprint:** click the movement stick to toggle sprint (default); select Hold or Toggle under VR Settings → Locomotion. Button Sprint temporarily takes this click. Crouch can be rebound at VR Settings → Controls, page 2.
- **VR Bullet Time:** right-stick up by default on supported VR controllers; off by default and remappable.
- **Android touch:** editable, movable/resizable HUD; export/import layouts and hide selected controls in the HUD editor. Touch visibility supports Auto, Always Show and Always Hide. Optional touch-look keeps screen touch aiming while hiding the joystick graphic.
- **Android gamepad:** common XInput-style controllers use Android's input APIs. Standard movement, aim, fire, grenades, melee, reload/use, weapon switching, crouch, jump, pause and menu navigation are supported. Controller options cover mapping, dead zones, sensitivity, trigger thresholds, touch visibility and vibration where supported.
- **Windows flat:** keyboard/mouse and gamepad controls are listed in the launcher; Left Shift sprints when sprint is on.

## 4. VR features and settings
OpenXR standalone VR, room-scale movement, tracked hands/fingers, estimated full-body IK, weapon alignment, scopes, body modes, HUD placement, holsters, contact and haptics are included.

- **Third Person:** VR Settings → Gameplay. Campaign/co-op on foot only. Physical hand features pause while enabled and restore their prior state on exit. This feature is included but needs headset confirmation for this release.
- **World Scale:** VR Settings → Comfort. Safe geometry is the default for VR and Android.
- Vehicle settings include first/third-person view, steering/turret aim source, recentering, per-vehicle offsets and glass/hatch visibility. Third-person vehicles and right-hand control remain recommended; first-person vehicle handling still needs refinement.
- Manual reload, physical grenades, physical NPC/world interaction, ragdolls, parkour/sliding, fist combat and projectile deflection are experimental/WIP. Some are restricted in network sessions for compatibility; test in solo first and enable one at a time.

## 5. Android / mobile and launcher
Android is the flat mobile build. Familiar touch controls remain alongside Android gamepad support, hot-plug/reconnect, analog triggers, menu navigation, customizable touch visibility and optional direct touch looking. Use **Controller & Touch Settings** and the HUD editor.

Android's optional over-the-shoulder camera is separate from VR third person: **Settings → Video Setup → FOV and Viewmodels → Third Person**, for campaign/co-op.

The launcher manages imported game revisions, network profiles/population, saved invites, project updates, supported campaign setup, guides and logs. Network/data changes take effect after restart where shown.

## 6. Multiplayer, co-op and server compatibility
- OpenCE Build 256 networking: hosts on **network 34** and joins compatible hosts on **network 11–34**.
- Join from **Play → Multiplayer → Join Game → Server Browser**; host PvP or campaign from **Create Game** and configure **Server Setup**. Launcher network/population selection and saved invites remain available.
- Campaign co-op uses OpenCE's native path and is supported. Matching content/maps, revisions, network versions, NAT/firewall and host settings still matter; individual setups may have issues.
- The engine allows co-op player limits up to 128, but 128-player campaign is not a stable or performance-tested target. Start with a small group.
- Voice chat requires the host to allow it and each device's microphone permission/input settings. A host may disable it.
- Cross-play and optional physical-feature synchronization depend on compatible versions and host settings. For co-op reports, include both players' logs when possible.

## 7. Game revision and content compatibility
The USA Original, Rev 1 and Rev 2 images compared for this port contain identical copies of the 24 stock maps. **The original Xbox XISO is recommended** for best-known compatibility. Other regions, repacks, incomplete or modified images are not all validated. Revision labels do not guarantee server compatibility; map/content and network versions also need to match.

The launcher scans/imports supported images and switches between imported sets. Custom Edition maps/campaigns need matching content and supported network versions. SPV1 and Project Lumoria have guided setup paths. Altheros Experience and MCC maps remain experimental. Import success does not guarantee every mod/map/script/mission will run.

## 8. Known issues and test status
- Test73b passed **203/203 automated suites**, Android VR/flat build/ABI checks, Gradle packaging and Windows flat/VR builds. SHA256SUMS.txt records the four platform-download hashes. GitHub also provides source-code ZIP and tar.gz archives for this tag.
- This exact build was **not launched in-game or tested on a headset** during packaging. Quest/Android, PICO, Steam Frame and PC VR runtime feedback is requested. Third-person VR and the new body shadow need visual confirmation.
- Fist combat/deflection, parkour/sliding, manual reload, physical grenades, NPC/world handling, ragdoll behavior and immersive vehicles remain WIP. First-person vehicle view is not recommended yet.
- Four reports lacked logs needed for diagnosis: Windows graphics settings, camera after the Flood introduction cutscene, a possible Wrist HUD report, and The Maw bridge countdown.
- Extra graphics/shadows, high ragdoll limits and large co-op lobbies may affect performance or memory.

Please report successful tests as well as issues. Include device/model and OS, app version, game-data set/revision, network version, map/mission, settings, reproduction steps and log. Logs: **Download/HaloCE** (Quest/PICO/Android), **Documents/HaloCEQuestVR/logs** (Steam Frame), beside the game and under **logs** on Windows (also linked from the launcher LOGS page). Remove private invites/device details before public posting.

Support: DM **@MeWhenINameMyself**, use the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx), or report in the [Flat2VR Halo CE discussion](https://discord.com/channels/747967102895390741/1555959498349215774).

## 9. Technical details and credits
- VR package **com.halo.decomp.vr**; Android flat **com.halo.decomp**; APK identity **1.0.41-test73b / code 86**, ARM64, Android 9/API 28 minimum. Signing certificate is unchanged.
- Windows bundle contains **halo.exe** (flat and launcher) and **halo-vr.exe** (PC VR), SDL3 and Khronos OpenXR loader. Configure an OpenXR runtime before PC VR.
- Runtime source commit: a29762e0480412ebf7f550e30beb6a047965e801. Package/source record: d8b8319820188ae10658258c2fbb26c983fb286b.
- Upstream: OpenCE Build 256, native network 34.
- Stencil shadows and Extra Effects are adapted from [jcompto95-tech / HALOFREAK95's OpenCE fork](https://github.com/jcompto95-tech/OpenCE). Dynamic ragdolls use OpenCE's Jolt Physics integration. See [CREDITS.md](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/CREDITS.md) and [THIRD-PARTY-NOTICES.txt](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android/blob/main/THIRD-PARTY-NOTICES.txt) for Jorrit Rouwe, OpenCE contributors and third-party library credits.
- Unofficial community project, not affiliated with Microsoft. No Halo game files are distributed. Current code is **AGPL-3.0-or-later**; project history through Test72 retains its earlier CC0 dedication.
