# Halo CE Quest VR + Android 1.0.37

> ## ⚠️ LARGE RELEASE — MANY NEW FEATURES. PLEASE READ.
>
> Several VR systems need more headset testing and may be inconsistent: **fist combat, projectile deflection/parrying, sliding, parkour, physical reload, ragdolls and NPC/object interaction, and immersive vehicle controls**. Broad user-supplied mod support also remains **work in progress**. Project Lumoria and SPV1 have specific supported setup paths; this does not mean every mod works. Try optional features individually and report what works as well as what fails.
>
> The MCC map path and The Altheros Experience are experimental. MCC's damaged-disc lookup was repaired in code but still needs headset confirmation. Altheros script handling was improved, but the next level-loading stage has not yet been confirmed on a device. Automated checks are not device acceptance.

**Public release v1.0.37 · supplied Test70 APKs · Android version code 82 · OpenCE Build 206 / network 29**

This is a cumulative public update from v1.0.31. It includes the intervening private Test65–Test70 work and refinements, while retaining the previous release and tag.

## 1. Installation and updating

| Device | Download |
| --- | --- |
| Android phone/tablet — flat play | [HaloCE-Android-1.0.37.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.37/HaloCE-Android-1.0.37.apk) |
| Meta Quest — standalone VR | [HaloCE-Quest-1.0.37.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.37/HaloCE-Quest-1.0.37.apk) |

Both APKs are ARM64 and require Android 9 / API 28 or newer. Enable Developer Mode on Quest and sideload with SideQuest or ADB. On Android, open the downloaded APK and allow installation from that source if asked.

**Updating:** use the launcher's project updater or install the matching edition above over the existing app. **Do not uninstall the old app or clear its data** if you want to preserve app-held saves, settings, imported maps and profiles. Package IDs and signing certificate are unchanged. The public version is **v1.0.37**; the APK's Android identity is **1.0.37-test70 / version code 82**. Android will ask you to approve the install. `compatibility.json` accompanies the release for the updater; users do not install it themselves.

New installations need the player's own complete supported Xbox Halo CE ISO/XISO or extracted files, imported through **Game files & versions**. No Halo game data, campaign maps or mod assets are bundled.

## 2. New features and major changes

### Launcher and campaigns

- **What's New** opens after an app update, lists the named changes and can be reopened from the launcher.
- Campaign choices now show support status. **SPV1** and **Project Lumoria** have supported setup paths. **The Altheros Experience** and **Halo 1 MCC maps** remain experimental.
- **Project Lumoria** can be prepared and imported from a user-supplied ZIP or folder, checked against expected file sizes and hashes, installed beside the original campaign, then restored/switched through the campaign launcher. Use its `lumoria_a` entry to start. It needs the required Custom Edition resource maps. This guided path does not imply every mod is compatible.
- The cause of the MCC “problem with the disc” lookup was identified and the missing GulchCE cache-map hooks restored. This path still needs headset confirmation and remains labelled experimental.
- The Altheros script loader now recognizes OpenSauce calls used by the supplied campaign scripts. VISR/bloom scripting calls are accepted but their post-processing effects are not rendered by this build. The next large-model loading step remains unverified on device.

### Controls and input changes

VR SETTINGS → **BUTTONS** now edits a selected action without silently rearranging other actions:

- Press A or left/right on a row to choose an input; nothing is written until confirmation.
- If another action already uses that input, choose **CANCEL**, **SWAP**, **CLEAR** or **BOTH**. Every gameplay action can be set to **NONE**.
- **RESET CONTROLS** appears at the top and bottom. Context marks show actions that are currently unavailable (`*`) or shared (`+`), with an explanation line. Menu navigation remains separately available.
- **MIRROR BUTTONS** can place face-button actions on the gun hand in left-handed play without rewriting saved logical bindings. Stick clicks remain with their sticks.
- The Button Sprint restore-mask fix retains PUSH TO TALK when sprint temporarily owns the left-stick click.

### Weapons, reloads and hands

- **Locked weapon holsters:** grip at a holster to stow a locked weapon; grip at it again to draw. Empty hands can be used for interactions where the mode permits.
- **Needler manual reload:** with manual reload enabled, four deliberate shake strokes within about 1.2 seconds start its native reload. The regular reload input still works. Small aiming/walking motion is filtered.
- **Shake cooling** is an optional solo feature: deliberate strokes cool a hot plasma weapon faster (about 1.5×–3×); tiny movement does not. It is off by default and does not change multiplayer cooling.
- Empty **SPNKR** tubes can fire once seated instead of waiting for the bar. The flamethrower canister is ready once seated. Empty magazine weapons and the shotgun still require normal charging/pumping; a gun hand receives periodic feedback while charging remains owed. Native ammo commit behavior is retained.
- **Pistol and Assault Rifle magazine fit** positions now place the magazine in the closing hand; the accepted Sniper pose is unchanged. Left-hand lettered weapons (rocket launcher, Sniper, shotgun and pistol) are mirrored back as a whole so the markings read correctly. Left-hand reload paths share the same hand-agnostic pouch, pose and haptic behavior.
- Existing manual reload remains a physical, experimental interaction. Its grip, insertion and charging still need device feedback for comfort and fit.

### Movement, fist combat and deflection — experimental

- **SLIDE** (VR Settings → Locomotion; off by default) uses sprint plus crouch, or head-lowered crouch when CROUCH SLIDES is enabled. It carries momentum, responds to distance/friction/impact settings, stops at walls and can be cancelled into a jump. Contact effects vary by enemy type. It is solo-only; timing and impacts may need tuning.
- **BULLET TIME** (off by default) uses the remappable **right stick up** action with Hold or Toggle and a 25–65% time scale. It applies to local solo play only and is suppressed while seated, in menus, cutscenes, paused, or in multiplayer/co-op. Rendering, head tracking and hand tracking keep their frame rate; game ticks slow. Map-authored speed settings are preserved.
- Tree climbing retries contacts at smaller radii and checks short hand rays for narrow trunks. Wall jumps use the direction you look and the wall you were running along. Parkour remains experimental and may be inconsistent across surfaces.
- **HIT ASSIST** helps an in-range punch connect without requiring the hand sweep to cross a small collision bubble. **LUNGE HOP** adds a small leap to a ground lunge. The fresh GRAB ASSIST default is 15 cm (an untouched old 10 cm value is migrated once); the maximum reach mapping was corrected.
- **Fist combat and parrying/deflection** include target-aware assistance, species/difficulty behavior, hit highlights and melee/attack feedback from the preceding tests. DEFLECT SHOTS can be used with fists or a deliberately moving gun hand; a support hand on a two-handed gun is not counted as an active parry hand. Timing, projectile direction, target behavior and reactions still need headset refinement. Not every projectile or enemy action is guaranteed to be deflected or parried. These features may not yet feel as good or reliable as intended.

### Graphics, ragdolls and bodies

The build carries OpenCE-fork **Extra Effects** and Graphics options. They start off or at Classic so existing visuals are preserved until changed:

- Extra Effects includes animated overshield visuals, dynamic blood, vehicle blood, projectile effects/lights, stencil shadows and Jolt physics for dropped weapons/grenades. Stencil shadows and increased effects can cost performance, especially on Quest.
- Graphics options include corpse duration/limit and decal duration. The fork's Decals option is desktop-only. Big Multiplayer Guns changes the flat game's ground-weapon presentation, not VR weapon scale.
- **Dynamic death ragdolls use Jolt Physics.** VR settings include death-physics/ragdoll controls, force, retention and a **RAGDOLL RANGE** of 20/40/60/80 metres; 60 metres is the fresh default. NPC rig slots can be raised up to 24. Cleanup is still affected by engine/object/memory pressure; these are not guarantees of a fixed corpse count. Host rules and peer compatibility govern network behavior.
- Living NPC grabbing, heavy two-hand handling, throwing/slams, shields and ally behavior remain experimental. Results depend on contact, species, actor protection and game state.

## 3. Controls and inputs

### Quest Touch defaults

| Input | Right-handed default |
| --- | --- |
| Left stick | Move / strafe |
| Right stick | Turn; hold down to crouch |
| Gun-hand trigger | Fire |
| Off-hand trigger | Zoom |
| A | Jump / menu confirm |
| B | Use / reload |
| X | Grenade; hold to change grenade type |
| Y | Switch weapon |
| Left-stick click | Reticle; Button Sprint temporarily takes this input when enabled |
| Right-stick click | Native melee |
| Both stick clicks | Recenter |
| Gun-hand grip | Hold physical weapons; locked-weapon holster behavior depends on mode |
| Off-hand grip | Support grip / interaction, according to enabled features |
| Menu button | Pause |
| Off hand beside left temple | Flashlight gesture when enabled |
| Gun hand beside temple | HUD gesture when enabled |

Point at menu items and press the trigger; thumbstick/D-pad menu navigation is also available. Physical actions are optional and may be session-restricted. For left-handed play, use handedness and MIRROR BUTTONS settings; do not assume a saved custom binding has moved unless the menu shows it.

**Button Sprint:** when enabled, left-stick click sprints; Hold or Toggle selects how it operates. It temporarily owns the left-stick click, then restores the previous action when disabled. To put crouch on that click, disable Button Sprint and choose the crouch binding on the VR Buttons page. Remapping conflicts ask before changing bindings. **BULLET TIME** defaults to right stick up and is off by default; its action is remappable.

### Android gamepad

Common Xbox-style defaults: left stick move, right stick aim, RT fire, LT grenade, A jump/confirm, B melee/back, X reload/use, Y switch weapon, LB flashlight, RB grenade type, stick clicks crouch/zoom and Start pause. D-pad/left-stick menu navigation is supported. Use **Controller & touch settings** for button swap, dead zones, sensitivity/response, trigger thresholds and vibration where supported. Controller button labels and mappings can vary by device.

### Android touch

The circular touch HUD remains editable and supports move, swipe-to-look and firing gestures. The layout editor can export/import layouts; selected controls can be hidden and restored from the editor. Touch visibility offers Auto, Always show or Always hide. Auto can restore touch when a connected controller disconnects. Direct touch look and gyro aim are optional; gyro is off by default. See the [Android touch guide](ANDROID-TOUCH-CONTROLS.md).

## 4. VR features and settings

Standalone OpenXR, room-scale movement, tracked hands, estimated body IK, fingers, weapon alignment, scopes, wrist/head HUD, holsters, hand contact and haptics remain available. Defaults remain **Legs + Arms**, **Safe geometry**, **Third Person vehicles** and **Right Hand steering**. Untracked joints are estimated rather than optically tracked.

Vehicle settings include third/first-person view, right/left/head/stick steering and turret aiming, seat recentering, per-vehicle offsets, control placement and hide-glass/hatch controls. First-person and immersive physical steering remain WIP; third-person/right-hand control is the recommended default.

Manual reload, physical grenades, NPC/world interaction, parkour, fist combat and vehicle immersion each have their own VR menu controls. Some settings depend on supporting toggles; read the in-game hints and the [Test70 field guide](TEST70-FIELD-GUIDE.md). Some interactions are disabled or require host permission in multiplayer/co-op. Use single-player first when testing them.

## 5. Android / mobile and launcher

The flat Android edition retains its familiar gameplay touch interface and Android/SDL controller input, including hot-plug/reconnect, analog triggers, menu navigation, configurable response/dead zones and vibration where supported. Touch HUD placement and visibility remain adjustable. The optional touch-look control hides its joystick graphic while keeping touch aiming active; the interface does not switch to a different button layout. Gamepad users can choose whether touch controls hide automatically, always show or always hide.

### Android third-person camera

The flat Android build includes OpenCE's optional over-the-shoulder **Third Person** camera for campaign and co-op play. Enable it from **Settings → Video Setup → FOV and Viewmodels → Third Person**; it is off by default. A keyboard can toggle it during play with **Keypad Enter** and hold **Alt** to look around. This is the flat-game player camera, separate from VR's vehicle view options.

The launcher handles imported game data/revisions, network profiles and populations, saved invites, compatible project updates, supported campaign preparation, guides and per-launch logs. Changing network or game data takes effect after launching/restarting as indicated. The app does not include or redistribute game files/mod archives.

## 6. Multiplayer, campaign co-op and server compatibility

### Join and host

- Join public games through **Play → Multiplayer → Join Game → Server Browser**, nearby games through **LAN**, or use **Direct Link** for an invite.
- Host PvP through **Create Game → Internet or LAN → Multiplayer**.
- Host campaign co-op through **Create Game → Internet or LAN → Singleplayer**, choose mission/difficulty, configure **Server Setup**, then start the lobby and share its invite or make it public.

This build hosts OpenCE **network 29** and supports client targets **11–29**. The launcher population list and native in-game browser are separate discovery sources. Choosing an older client target changes which compatible hosts you can join; it does not downgrade a hosted game. Custom Edition sessions need matching maps and network 23 or newer. Campaign co-op normally requires network 15 or newer; legacy 12–14 need the explicit compatibility option. Game content, NAT/firewall, host settings and server state can still prevent joining. Retail Halo PC/Custom Edition, MCC and retail Xbox networking are separate protocol families.

Campaign co-op uses OpenCE's native path. The owner previously confirmed co-op working, but the full exact Test70 pair still needs paired-device regression testing. This engine exposes campaign-player limits up to 128; that is not a promise of stable gameplay, performance or synchronized AI at that scale. Start with a small group. NPC ragdoll synchronization for four remote peers is not the overall co-op player limit.

Enhanced VR actions require host permission and compatible peers. Unsupported clients and ordinary PvP retain native behavior. No new network protocol is introduced in Test70. Community extras such as armor sharing, text chat and kick/ban votes use separate message kinds; stock peers ignore messages they do not support.

### Voice chat

OpenCE host-relayed voice is included. The host controls whether voice is allowed in Server Setup. Grant Android microphone permission to transmit, then choose Push to Talk or Open Mic. PTT needs a binding on Quest; Android uses the supported keyboard/touch/controller paths. Incoming voice has a volume setting. A quiet lobby may have voice disabled by its host.

## 7. Game revision and mod compatibility

The USA Original, Rev 1 and Rev 2 images compared for this port contain identical copies of their 24 maps. The **original Xbox XISO remains the recommended baseline** for best-known compatibility. This comparison does not cover every region, repack, modified or incomplete image. A launcher's revision label alone cannot prove a remote server has matching content.

Custom Edition/campaign mods need compatible resource maps and scripts. SPV1 and Project Lumoria have specific setup instructions. Altheros script handling improved, but its level load remains experimental. MCC maps are experimental and MCC online play is not supported by this integration. **General support for arbitrary mods, modified maps, regional images, custom scripts/assets and every campaign is WIP.** A successful import does not guarantee that the content plays. Keep the original game-data set available.

## 8. Known issues and testing notes

- Fist combat, parry/deflection, SLIDE and parkour are experimental. They may miss or trigger inconsistently, or feel less smooth than intended across enemies, maps, projectiles and tracking setups.
- Manual reload, physical grenades, NPC/ally/enemy grabbing, slam damage, ragdoll behavior/retention and immersive vehicle controls remain WIP. First-person vehicles are not the recommended default.
- Project Lumoria has a guided import path; this does not guarantee general mod compatibility. Altheros script gaps were addressed, but its next model-memory step is unverified and may still fail. MCC maps remain experimental despite the damaged-disc lookup fix.
- Higher graphics effects, shadows, ragdoll range/count and large co-op lobbies can reduce performance or increase resource use. The configurable 128-player co-op maximum is not a tested target.
- This exact pair passed the registered automated suites and package/build checks, but was not installed or launched by the packaging agent and has not received full Quest/Android device verification. Automated checks do not establish headset acceptance.

**Please report successful tests and problems.** Include device/OS, app version/code, selected game-data revision, map/mission, host/client role, network type, settings, reproduction steps and the session log. For co-op, include both players' logs. Logs normally appear under **Download/HaloCE**, with app-private fallback. Remove private invites/device details before public posting.

Support: DM **@MeWhenINameMyself**, use the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx), or report in the [Flat2VR Halo CE discussion](https://discord.com/channels/747967102895390741/1555959498349215774). This release is intended to gather real-user testing and logs for refinement.

## 9. Technical details and credits

- Quest package `com.halo.decomp.vr`; Android package `com.halo.decomp`; APK version `1.0.37-test70`, version code 82; unchanged project signing certificate.
- Runtime source: Test70 commit `1cd63dc453768a3ca94bef37e8c20b3b77583bee`. Public filenames do not change APK contents.
- Upstream base: OpenCE Build 206 / network 29. No new upstream merge in Test70.
- Graphics/effects are adapted from [jcompto95-tech / HALOFREAK95's OpenCE fork](https://github.com/jcompto95-tech/OpenCE).
- Jolt Physics ragdolls use the OpenCE Build 201 integration (PR #317), adapted for the Quest/Android host bridge. Jolt is by Jorrit Rouwe and contributors. The MCC map loader is from GulchCE by chestahh and is experimental here. Steam Workshop integration uses JavaSteam and related third-party libraries; full notices are included.
- Willem Horak's glasses-FOV/resolution contribution remains included ([PR #1](https://github.com/moistman42069/HaloCE-Quest-VR/pull/1)). See [CREDITS.md](../CREDITS.md) and [THIRD-PARTY-NOTICES.txt](../THIRD-PARTY-NOTICES.txt). No external game's art/animations are bundled by this release.
- PC and Steam Frame work remains deferred. This is an unofficial community project and is not affiliated with Microsoft.
