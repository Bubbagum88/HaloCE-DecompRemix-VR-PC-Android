<p align="center"><img src=".github/decomplogo.png" alt="Halo Combat Evolved VR — OpenCE port" width="460" /></p>

<h1 align="center">Halo CE Quest VR + Android</h1>

<p align="center">An unofficial OpenCE-based community port for standalone Meta Quest VR and flat Android.</p>

**MASSIVE UPDATE — MANY NEW FEATURES. [Read the full 1.0.31 release notes](docs/RELEASE-1.0.31.md).**

> This release focuses on individual user testing and logs to refine future builds. Immersive vehicles, manual reload, ragdolls, grabbing/slamming, parkour, fist assistance and physical grenades are WIP/experimental. Report bugs, placement/comfort preferences and successful tests too.

## Download and update

| Device | Download |
| --- | --- |
| Android phone/tablet — flat | [HaloCE-Android-1.0.31.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.31/HaloCE-Android-1.0.31.apk) |
| Meta Quest — VR | [HaloCE-Quest-1.0.31.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.31/HaloCE-Quest-1.0.31.apk) |

ARM64, Android 9/API28+. On Quest enable Developer Mode and sideload with SideQuest/ADB. On Android allow installation from the browser/file manager. Existing users can use the launcher's project updater or install the matching APK over the current app. **Do not uninstall or clear data.** Back up important saves first.

Public **v1.0.31** contains the exact supplied **Test64 / 1.0.31-test64 / code76** binaries. The internal test label is expected; someone already on Test64 has this build. Package IDs/signing remain unchanged. The release includes updater-required compatibility metadata; users do not install that JSON manually.

Import your own complete supported Xbox Halo CE ISO/XISO or extracted data through **Game files & versions**. No game data is included. Tested USA Original/Rev1/Rev2 map contents are identical; other regions/modifications still need validation. Original Xbox XISO remains the reference. Identical managed map sets deduplicate. The manager can select/rename sets and delete inactive managed copies; active and protected Existing game data remain protected. Source ISOs selected through Android's picker stay at their original location.

## What is included

- Standalone Quest OpenXR, room-scale movement, tracked hands, estimated body IK, holsters, two-hand weapons, scopes, gestures and wrist HUD. Legs + Arms and Safe geometry remain defaults.
- Experimental physical reload with mirrored hip/shoulder pouches and charging; physical grenades; NPC/ally/object grabbing, heavy handling, ragdolls, slams, optional debris and bounded vehicle lifting/recovery.
- Experimental parkour and fist-combat assist, toggle sprint, solo shake cooling, aim steadying and vehicle/turret reticle refinements.
- Optional immersive vehicle wheels/bars/sticks with calibration preview and per-vehicle offsets. Ordinary third-person/right-hand steering remains the default. First-person vehicles still need refinement.
- Flat Android circular touch HUD, layout import/export and individual control hiding, optional touch/gyro look and common USB/Bluetooth gamepads.
- **Voice chat, adapted from OpenCE:** host-relayed Opus voice for Quest and Android, with Push to Talk / Open Mic, incoming voice volume controls and host-controlled voice settings. Microphone permission is required for transmission; see the release guide for controls and setup.
- Native OpenCE server browsing, PvP/campaign hosting; network28 hosting and compatible client targets11–28; launcher populations, updates, imports, support and per-launch logs.
- Long VR-menu section indexes and the Test64 fix for the crash opening VR SETTINGS.

## Controls and feature setup

The [release notes](docs/RELEASE-1.0.31.md) contain the Quest, gamepad and touch mappings and a feature-by-feature quick guide. **BUTTON SPRINT takes left-stick click; SPRINT TOGGLE makes it click-on/click-off. MANUAL RELOAD changes USE/RELOAD to magazine ejection.** Optional features can enable supporting settings; check those rows when experimenting.

Physical grenade slots may be offset: **VR Settings → IMMERSION → GRENADES → CHEST FWD / CHEST DOWN / CHEST SPACING** adjusts placement. Touch the visible slot with a free palm then Grip; release Grip to throw. THROW POWER adjusts strength separately.

## Multiplayer, co-op and voice

Join from **Play → Multiplayer → Join Game → Server Browser**, LAN or Direct Link. Host from **Create Game → Internet or LAN → Multiplayer** for PvP, or **Singleplayer** for campaign; choose mission/difficulty and configure **Server Setup**, then start/share the lobby.

Hosting stays on network28. The launcher defaults to All compatible networks and offers targets11–28, taking effect next launch. Original-map PvP uses the implemented targets; co-op defaults to15+ with12–14 legacy opt-in; Custom Edition needs23+ and matching maps. Retail PC/CE, MCC and Xbox protocols are separate. NAT, content and host settings still affect joins. 128 players is an engine option, not a performance guarantee. This port does not host OpenCE web/browser clients or share maps.

Enhanced VR actions require host permission and compatible peers. Manual reload and other local-only systems remain restricted; NPC ragdoll replication supports four remote machines, not a four-player general co-op limit. See the full notes for details.

Hosts must allow voice. Mic Off still permits incoming voice; Voice Volume0 mutes it. Enable PTT/Open Mic, grant microphone permission and configure a PTT binding when needed. The notes explain Quest/flat controls and troubleshooting.

## Guides, source and support

- [Complete 1.0.31 release notes](docs/RELEASE-1.0.31.md)
- [Test64 field guide and history](docs/TEST64-FIELD-GUIDE.md) — newest sections supersede older test instructions
- [Android touch controls](docs/ANDROID-TOUCH-CONTROLS.md)
- [Release provenance](docs/RELEASE-PROVENANCE-1.0.31.md)

Logs normally appear under **Download/HaloCE**, with app-private fallback. Send device/OS, app/network version, selected data, map/mission, toggles, reproduction steps and relevant logs; collect both peers' logs for co-op. Remove private invites/device details before public posting. DM **@MeWhenINameMyself** or use the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx) or the [Flat2VR Halo CE discussion](https://discord.com/channels/747967102895390741/1555959498349215774). This release's goal is real user testing and logs for future refinements.

The source tag contains the supplied APK runtime source plus publication docs/metadata. Automated checks are recorded; a complete device checklist for this exact pair remains pending. PC/Steam Frame work remains deferred.

Built on [OpenCE](https://github.com/OpenCommunityEdition/OpenCE): Build157 base with selected integrations through Build201/network28, not a complete rebase. Thanks to the upstream, port and testing communities, including [Willem Horak's PR #1](https://github.com/moistman42069/HaloCE-Quest-VR/pull/1). See [CREDITS.md](CREDITS.md) and [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt). Unofficial; not affiliated with Microsoft.
