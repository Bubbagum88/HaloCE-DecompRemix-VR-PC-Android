<p align="center"><img src=".github/decomplogo.png" alt="Halo Combat Evolved VR — OpenCE port" width="460" /></p>

<h1 align="center">Halo CE Quest VR + Android</h1>

<p align="center">An unofficial OpenCE-based community port for standalone Meta Quest VR and flat Android.</p>

**Latest: [1.0.37 — Test70](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.37).** This is a large cumulative update. Read the release notes, especially the experimental-feature and compatibility sections, before enabling optional systems.

> **Experimental / WIP:** fist combat and projectile deflection, sliding, parkour, physical reload, ragdolls and body interactions, immersive vehicle controls, and broad support for user-supplied mods still need refinement and device reports. Enable experimental options one at a time. Project Lumoria and SPV1 have specific setup paths; this does not mean every mod works. MCC maps and The Altheros Experience remain experimental.

## Download and update

| Device | Download |
| --- | --- |
| Android phone/tablet — flat | [HaloCE-Android-1.0.37.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.37/HaloCE-Android-1.0.37.apk) |
| Meta Quest — standalone VR | [HaloCE-Quest-1.0.37.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.37/HaloCE-Quest-1.0.37.apk) |

Both builds require ARM64 and Android 9 / API 28 or newer. On Quest, enable Developer Mode and sideload with SideQuest or ADB. On Android, allow installation from the browser/file manager when prompted.

Existing users can use the launcher's project updater or install the matching APK over the current app. **Do not uninstall or clear app data** if you want to keep saves, settings and imported files. The public release is v1.0.37; the APK reports its exact build identity as **1.0.37-test70 / code 82**. Package IDs and signing certificate are unchanged. `compatibility.json` is required by the updater and is already handled by it; do not install it manually.

The app contains no Halo game data. Import your own complete supported Xbox Halo CE ISO/XISO or extracted game files through **Game files & versions**. The original Xbox XISO remains the recommended reference.

## What changed

- **Launcher and campaigns:** What's New appears after an update and can be reopened; campaign buttons show their support status. Project Lumoria has a guided import/install/restore flow for a player-supplied archive or folder. The MCC damaged-disc lookup was repaired, but MCC maps remain experimental pending headset confirmation. Altheros script support improved in Test69; later level loading still needs device logs.
- **Controls:** button remapping now asks before changing a binding, offers CANCEL / SWAP / CLEAR / BOTH, supports NONE, shows contextual ownership, and has RESET CONTROLS at both ends of the page. MIRROR BUTTONS puts face-button actions on the gun hand for left-handed play without rewriting saved bindings.
- **Weapons:** locked weapons can be holstered; the Needler supports deliberate shake reload when manual reload is enabled; optional shake cooling responds to deliberate strokes; empty rocket tubes and the flamethrower canister are ready when seated; charging feedback and Pistol/AR magazine fit were refined. Left-hand weapon lettering and button ownership were improved.
- **Movement and combat:** optional SLIDE, solo-only BULLET TIME, improved tree contact and look-directed wall jumps, fist HIT ASSIST and LUNGE HOP, and a larger GRAB ASSIST default. Sliding, fist combat, deflection and parkour remain experimental and can feel inconsistent.
- **Graphics and bodies:** Extra Effects includes optional overshield visuals, dynamic/vehicle blood, projectile effects, stencil shadows and Jolt-backed dropped-weapon physics. Corpse duration/limits and other visual options are configurable. Dynamic death ragdolls use Jolt; the VR ragdoll range default is increased. See the release notes for performance and multiplayer limits.
- **Android:** existing touch controls and controller support remain, including touch-layout export/import, hiding selected HUD controls, optional touch looking and controller-aware touch visibility.
- **Multiplayer:** OpenCE Build 206 / network 29 is retained. The app hosts on 29 and can target compatible hosts 11–29. Native in-game browser, PvP/campaign hosting, voice chat and launcher population lists remain. Voice transmission depends on host settings and microphone permission.

## Controls, setup and compatibility

The [complete 1.0.37 release notes](docs/RELEASE-1.0.37.md) include installation, Quest and Android inputs, all new settings, server setup, game revisions, WIP notes, testing status and credits. The [Test70 field guide](docs/TEST70-FIELD-GUIDE.md) provides the full menu and feature reference; [controls and options](docs/CONTROLS-AND-OPTIONS.md) and the [Android touch guide](docs/ANDROID-TOUCH-CONTROLS.md) give further detail.

For VR, the familiar defaults remain **Legs + Arms**, **Safe geometry**, **Third Person vehicles** and **Right Hand steering**. Experimental systems are optional and may be restricted in multiplayer/co-op unless the host and peers support and allow them. For Android gamepads, use **Controller & touch settings** to adjust mapping, dead zones, sensitivity and touch visibility.

The tested USA Original, Rev 1 and Rev 2 images contain identical copies of their 24 maps; other regions, repacks and modified images are not certified. Custom Edition and campaign co-op have additional network-version and content requirements. The release notes explain these limits.

## Support and project

Please report both failures and successful tests, especially for fist combat/deflection, sliding, ragdolls, campaigns, vehicle options, and co-op. Include device and OS, app and network version, selected game-data set, map/mission, relevant settings, steps to reproduce, and the launch log under **Download/HaloCE** when available. For co-op, logs from both players help. Remove private invites/device details before public posting.

Contact **@MeWhenINameMyself** by Discord DM, use the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx), or report in the [Flat2VR Halo CE discussion](https://discord.com/channels/747967102895390741/1555959498349215774). This build is intended to collect real-device feedback for the next refinement pass.

The About description is unchanged. This repository is an unofficial community project, not affiliated with Microsoft. No Halo game files are distributed. See [credits](CREDITS.md) and [third-party notices](THIRD-PARTY-NOTICES.txt). PC and Steam Frame ports remain deferred.
