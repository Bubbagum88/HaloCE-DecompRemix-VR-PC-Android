# Halo CE Quest VR + Android player guide

This guide describes the published **Halo CE Quest VR + Android v1.0.18 / OpenCE Build 157 / network 24**. For installation, controls, compatibility and release details, see [v1.0.18 release notes](RELEASE-1.0.18.md). Private-candidate additions are documented in the candidate note prepended to this guide.

## Install and update

Use the Android APK for a phone/tablet and the Quest APK for standalone VR. On Quest, enable Developer Mode and sideload with SideQuest or ADB. Install over the existing project app so imported game data, saves and settings remain. Do not uninstall or clear app data. Supply your own supported Xbox Halo CE game files; none are included.

The main launcher shows the selected game-data label and how many distinct sets are installed; tap it to switch. **Game files & versions** opens the full manager, where you can import an ISO/XISO or extracted game folder, inspect the recognized cache build and select or rename a set. You can delete an inactive imported copy there; deletion removes that set's maps, config and local saves, while the active set and existing/base game data are protected. Deleting a copied ISO/XISO from the import inbox is a separate action. Images selected through Android's file picker are imported as maps only: the launcher does not retain or delete the original ISO/XISO, which remains at its original location. Use Android Files to delete that source image. The initial setup image appears as protected **Existing game data**; use the manager's **Import ISO / XISO** or **Scan inbox** controls to add separately selectable managed sets. Exact byte-identical managed map sets share one profile, while the Existing game data base row remains separate; labels alone do not create separate runtime revisions. The **Versions & updates** page checks the project's compatible releases and provides official upstream downloads separately. Upstream files are not applied blindly to the integrated VR/network runtime.

## Browse, join and host in game

The OpenCE multiplayer flow is in the game menus. Create/select a profile if prompted.

| Goal | Menu path |
| --- | --- |
| Join a public PvP or campaign game | **Play → Multiplayer → Join Game → Server Browser**; refresh and choose a listing |
| Join a nearby LAN game | **Play → Multiplayer → Join Game → LAN** |
| Join from an invite | **Play → Multiplayer → Join Game → Direct Link** and paste/enter the invite |
| Host PvP | **Play → Multiplayer → Create Game → Internet or LAN → Multiplayer → map → game type → Server Setup** |
| Host campaign co-op | **Play → Multiplayer → Create Game → Internet or LAN → Singleplayer → mission → difficulty → Server Setup** |

In **Server Setup**, choose the server name, player limit, public/private listing and password as needed. PvP also has match rules; campaign has co-op options. Start the lobby, invite players or publish it, then start the match when ready. The campaign player selector offers limits up to 128; start with a small group because the maximum is not a performance guarantee.

The launcher also has **Browse multiplayer servers** and **Browse campaign co-op servers**. Refresh, then open **Network** to compare reported server/player populations, busiest first. Choose **All compatible networks** (11-24) or an exact version from 11 through 24. The default is 24. This sets the native client's discovery and join target on the next game launch as well as filtering the launcher list. The selection is shared across both browsers and game-data sets. Close the game before changing it; it cannot switch while a game is running.

Versions 11-22 are for original Xbox-map PvP only. Campaign co-op and Custom Edition require a version23 or version24 host. Hosting and signed listings from this app always use network24; choosing an older join target does not make a network24 host compatible with old clients. Versions below 11 and unknown future versions remain unavailable. This is backward client compatibility, not a replacement for every historical engine or compatibility with retail Halo PC/Custom Edition, MCC or retail Xbox networking.

Counts are catalog reports, may be stale, and do not include every private/LAN game. Up to four supported HTTPS catalogs can be configured; only the default community catalog has been independently verified in this pass. MQTT brokers are mirrors of discovery, not separate selectable game protocols. The native in-game browser continues to use signed MQTT and LAN discovery with the selected client target.

Compatible maps/resources and a reachable network route are still required. Public listings do not relay traffic. NAT, firewall/VPN, mobile-data restrictions, Wi-Fi isolation, passwords, full lobbies and missing or different game content can prevent joining. PvP directory joins can prompt for an installed map/game-data set; campaign joins do not automatically choose a matching revision. If joining fails, record logs from both host and client, host version, selected join target, map/revision and network type. Device cross-play testing is still required; no universal compatibility is claimed.

The launcher server directory is a fallback list; it does not replace in-game host setup, LAN discovery or signed MQTT discovery. Saved invites, game-data management, updates, controller/touch settings, guides and logs remain available.

## Controls

### Quest Touch

- Left stick moves; right stick turns and, when held down, crouches by default.
- Weapon-hand trigger fires; off-hand trigger zooms.
- Right A jumps/confirms; right B reloads/uses. Left Y switches weapons; left X throws a grenade, and holding X changes grenade type.
- Left stick click toggles the reticle (visible at startup); right stick click performs native melee; clicking both sticks recenters.
- Weapon-hand grip handles physical weapons; the off-hand grip locks to the support point when the two-hand option is enabled.
- Bring the off hand to the left side of the head to toggle the flashlight when its gesture is enabled. Adjust or disable the reach in **VR Settings → Head Gestures → Flashlight**.
- Hold the gun hand by its own temple to toggle the HUD when enabled. A cycles co-op spectate targets or votes in a skippable cutscene.
- Point at a menu row and press the trigger. Thumbstick/D-pad menu navigation is available as well. B returns/back. Left-handed mode mirrors supported actions.

To put crouch back on left-stick click, open **VR menu → Controls → Page 2 → L Stick Click → Crouch**. Reassign the reticle on **Buttons** if needed.

### Android gamepad

The default Xbox-style mapping is: left stick move, right stick aim, RT fire, LT grenade, A jump, B melee/cancel, X reload/use, Y switch weapon, LB flashlight, RB grenade type, stick clicks crouch/zoom, and Start pause. D-pad or left stick navigates menus; A confirms and B returns. Controller labels can vary; use **Controller & touch settings** for face-button swap, dead zones, response, trigger threshold and vibration.

### Android touch

Use **MOVE + swipe** to move and aim, or drag **FIRE** to move, aim and fire together. Tap **HUD** while playing to reposition or resize touch controls and adjust opacity, color and response. Gyro aiming is optional and off by default. Touch visibility can be **Auto**, **Always show** or **Always hide**; Auto restores touch when a connected controller disconnects.

## VR settings

Open the pause menu and choose **VR Settings**. Use Next Page and Back to move between settings pages. Arrow controls decrease/increase values; A/right advances or confirms. **Legs + Arms**, **Safe geometry**, **Third Person vehicles** and **Right Hand steering** are defaults. First-person vehicle view remains experimental. Changes save; restart after changing geometry compatibility.

Settings include body/hand modes, fingers, hand/gun calibration, weapon grip and support grip, controls, gestures, HUD/wrist HUD, scopes, vehicles/seats, comfort, graphics, display and controller tracking corrections. Optical finger tracking is not used; fingers follow controller sensors. See [controls and options](CONTROLS-AND-OPTIONS.md) for exact defaults and the full menu inventory.

**HAPTICS** is the single vibration control for every controller effect,
including shots, contact, reloads, movement and interaction feedback. Set it to
0% to disable all vibration, or raise it to adjust strength. Load feedback is
part of this same setting; it has no separate on/off toggle.

## Revisions, logs and support

The original Xbox Halo: Combat Evolved XISO remains the recommended baseline. The exact USA Original, Rev 1 and Rev 2 images compared for this project all import successfully and contain byte-identical copies of the same 24 maps; their other disc files differ. This does not cover other regions, repacks or modified images. The launcher detects supported cache builds and fingerprints map files, but a filename does not authenticate a disc label, and the server browser cannot determine a remote host's ISO from its listing. See [the full USA comparison](USA-IMAGE-COMPARISON.md). SPV1 is experimental and unverified; file sizes fitting the current reader limits do not establish protected-map/resource/campaign support.

Each launch writes a detailed log under **Download/HaloCE** when Android allows; app-private storage is used as fallback. For crashes, failed joins or desyncs, share logs from each peer and include device/model, OS, app/network version, game-data set, map/mission, network type and reproduction steps. Contact **@MeWhenINameMyself** or the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx). Remove private invite/device details before sharing.
