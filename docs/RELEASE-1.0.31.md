# ⚠️ MASSIVE RELEASE — MANY NEW FEATURES. PLEASE READ.

**The main goal of this release is individual user testing and useful logs, so future releases can be refined around real device results.** Please share what worked, what failed, your preferred settings, and the log from the affected session.

**WIP / experimental:** immersive vehicles, manual physical reload, ragdolls, NPC/object grabbing and slamming, parkour, assisted fist combat, and physical grenades still need refinement. They may behave differently across maps, actors and tracking setups. Enable them individually and report your experience. These are implemented experimental systems, not a promise that every option works perfectly in every situation.

**Public release 1.0.31 · supplied Test64 APKs · Android code 76 · OpenCE network 28 hosting**

## 1. Installation and updating

| Device | Download |
| --- | --- |
| Android phone/tablet — flat play | [HaloCE-Android-1.0.31.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.31/HaloCE-Android-1.0.31.apk) |
| Meta Quest — standalone VR | [HaloCE-Quest-1.0.31.apk](https://github.com/moistman42069/HaloCE-Quest-VR/releases/download/v1.0.31/HaloCE-Quest-1.0.31.apk) |

Both editions require ARM64 and Android 9 / API 28 or newer. For Quest, enable Developer Mode and sideload with SideQuest or ADB. On Android, allow installation from the browser/file manager when asked.

**Already installed?** Use the launcher's project update check, download the offered update, and approve Android's installer. Or install the correct APK above directly over the existing app. **Do not uninstall or clear app data:** that deletes app-held saves/settings/imports. Back up important data first. The package IDs and signing certificate are unchanged; code 76 is newer than public 1.0.18's code 48. Saved settings stay, so new defaults mainly affect fresh installs or settings you have not saved.

These are the original Test64 binaries, renamed for the public updater without rebuilding or resigning. The app still displays **1.0.31-test64** internally. Someone already running Test64/code 76 has the same binaries and will correctly see “already have this published build.”

For a new installation, open **Game files & versions** and import your own complete supported Xbox Halo CE ISO/XISO or extracted game files. No Halo maps or game data are included. `compatibility.json` is required by the launcher; users do not need to install it manually. Source ZIP/tar archives are available through GitHub.

## 2. Major changes since public 1.0.18

This release collects the work across many private tests, not just Test64's final fix:

- **Physical interaction systems:** manual reloading, shoulder/hip ammo pouches, optional discarded magazines, NPC/ally/enemy and object grabbing, two-handed heavy handling, throwing/slam damage, ragdolls and body-retention controls. These remain WIP.
- **Button sprint and movement options:** optional left-stick-click sprint, Hold or Toggle operation, adjustable 1.0–1.5? offline speed, and physical arm-running with adjustable effort. See the dedicated sprint guide below for setup and binding changes.
- **Movement and combat:** optional climbing, wall running/jumping, arm-powered launches, sprint toggle, shake-to-cool, enemy-focused fist assistance and physically thrown chest grenades. Session permissions restrict gameplay-changing features online.
- **Immersive vehicles:** optional grab-based steering with vehicle-specific wheel/bar/stick models, adjustable placement and reach, highlights, feedback and a live blue calibration preview. Ordinary controller vehicle controls remain available.
- **Aiming, hands and feedback:** shared aim steadying, per-weapon scope positioning, updated scope attachment, mounted vehicle/turret shot-reticle alignment, reload grip/charging feedback, and fixes to weapon release, holsters, contact haptics and unwanted animation interactions.
- **Menus:** long VR categories have a section index with Back navigation. Test64 fixes the Test63 crash when opening VR SETTINGS. Pointer/list/category navigation refinements are included.
- **Android:** touch-layout export/import and individual control hiding, alongside the familiar editable circular HUD, gamepad support and optional direct touch/gyro looking.
- **Launcher/data:** clearer imported-set selection/deletion, original/Rev 1/Rev 2 map comparison, fitted app icons, font choice, support links, network/population selection and expanded diagnostics.
- **New voice chat, adapted from OpenCE:** host-relayed Opus voice for Quest and Android, with Push to Talk / Open Mic, incoming voice volume controls, microphone permission handling and host-controlled voice settings. Hosts must enable voice; see section 6 for setup and platform-specific controls.
- **Networking and stability:** network 28 hosting and compatible client targets 11–28; selected upstream changes through OpenCE Build 201, host-relayed Opus voice, and fixes for the Quest voice/server-join crashes investigated in private tests. This remains a customized OpenCE Build 157 base with selected later integrations, not a complete Build 201 rebase.

## 3. Controls and inputs

### Quest Touch defaults

Right-handed defaults are below. Handedness and button settings can change supported mappings. Physical hand actions require controller tracking, not optical finger tracking.

| Input | Default action |
| --- | --- |
| Left stick | Move/strafe |
| Right stick | Turn; hold down to crouch by default |
| Weapon-hand trigger | Fire |
| Off-hand trigger | Zoom with compatible weapons |
| Right A | Jump / menu confirm |
| Right B | Use / reload |
| Left Y | Switch weapon |
| Left X | Throw grenade; hold to change grenade type |
| Weapon-hand grip | Physical weapon holding/transfer; behavior depends on handling mode |
| Off-hand grip at weapon support point | Two-hand support attachment |
| Left-stick click | Reticle toggle normally; sprint while BUTTON SPRINT is enabled |
| Right-stick click | Native melee |
| Both stick clicks | Recenter |
| Left menu button | Pause/menu |
| Off hand near left temple | Flashlight gesture, when enabled |
| Gun hand beside its temple | Head HUD gesture, when enabled |

Point at menu items and press the trigger; thumbstick/D-pad navigation is also available. VR settings group controls by topic; long categories open a section list, and Back returns to that list.

**Binding changes to know:** BUTTON SPRINT owns left-stick click while enabled. **SPRINT TOGGLE** changes it from hold-to-run to click-on/click-off. A hidden reticle is restored if its toggle loses its binding. To put crouch on left-stick click, disable BUTTON SPRINT and use **Controls → Buttons / L STICK → Crouch** (older menus call this Controls, page 2). With MANUAL RELOAD on, the configured USE/RELOAD action ejects the magazine instead of performing a stock reload; an available use/vehicle/weapon interaction takes priority. With the feature off, normal reload returns. Right-stick melee is not repurposed for magazine ejection.

### Sprint button and physical running (Quest VR)

Open **VR Settings → Locomotion**:

| Option | What it does |
| --- | --- |
| **BUTTON SPRINT** | Enable to use **left-stick click** for sprint while moving. Off by default on a fresh configuration. |
| **SPRINT TOGGLE → HOLD** | Hold left-stick click to sprint; release it to stop. This is the default mode. |
| **SPRINT TOGGLE → TOGGLE** | Click once to enable sprint, then click again to stop—no need to keep the stick pressed. Selecting Toggle also enables Button Sprint. Movement still uses the movement stick; this is not auto-walk. |
| **SPRINT SPEED** | Choose **1.0X?1.5X**, in 0.1 steps; fresh default **1.5X**. At 1.0X there is no speed increase. |
| **ARM RUN / ARM EFFORT** | Optional physical running from arm pumping, with adjustable motion sensitivity. Arm Run starts off. Sprint Speed sets the maximum speed boost separately from arm effort. Deliberate stick movement takes priority. |

**Binding conflicts:** Button Sprint temporarily owns left-stick click, so its previous action (such as reticle toggle or crouch) cannot fire at the same time. Disabling Button Sprint restores the saved assignment unless you changed that action in the meantime. The Buttons menu excludes that click while sprint owns it; a reticle hidden by the displaced reticle binding is restored. Both-stick recentering remains available and cancels toggled sprint. Entering a vehicle, losing app focus or losing the active VR input state also cancels it.

**Multiplayer/co-op:** the extra movement speed applies only in local/offline play. Network sessions retain stock movement speed, including when this client hosts. These are VR locomotion options, not a new flat Android sprint binding. Existing saved settings are preserved when updating.

### Experimental interaction quick guide

| Feature | How to use it / important options |
| --- | --- |
| Manual reload | Enable MANUAL RELOAD. Eject with USE/RELOAD or contact-grab the magazine. Reach to an enabled hip/shoulder pouch, squeeze the configured Reload Input (Grip by default; Trigger selectable), align the replacement with the well, then seat it. If the gun was empty, operate its slide/charging handle/pump. Tactical reloads retain a chambered round. |
| Ammo pouches | HIP POUCH / SHOULDER POUCH enable pickup regions; MAG POUCH SIDE offers AUTO, LEFT, RIGHT or BOTH. AUTO follows the free hand. Position controls help separate pouches from holsters. |
| Physical grenades | Enable IMMERSION → GRENADES → PHYS GRENADES. Touch the left-chest frag or right-chest plasma grenade with a free hand, press Grip, then release Grip to throw. Native counts apply; the fuse starts on release. Standard grenade buttons remain available. |
| NPC/object grabbing | Enable NPC GRAB / WORLD GRAB. Touch the visible body/object with a free hand, then squeeze Grip. Release to let go/throw. GRAB ASSIST, HAND CONTACT, NPC HOLD and THROW tune reach and feel. |
| Heavy NPCs | A living Elite/Hunter normally needs one hand to restrain and a second to lift. ONE-HAND HEAVIES optionally relaxes this. Dead heavy bodies can be lifted one-handed. Allies can be grabbed too. |
| Parkour | Enable the relevant climbing/wall-run/wall-jump options. Touch a climbable surface and Grip to hold; pull your body and release to launch. Run/jump along a wall for wall running; use Jump against it to wall-jump. Tune CLIMB GRAB, CLIMB LAUNCH, WALL SPEED, WALL LEAP and WALL TIME. |
| Fist combat | Enable IMMERSION → FIST COMBAT. Look at an enemy and make a deliberate closed-fist punch. The optional approach assist closes a short gap and subsequent punches favor that target. Grabbing/climbing or pulling away ends the assist. |
| Immersive steering | Enable IMMERSIVE VEHICLE, then touch and Grip the vehicle's wheel/bar/stick. Release to disengage. See vehicle calibration below. |
| Shake cooling | SHAKE COOLING optionally speeds supported overheating-weapon cooling when shaken in solo play; disabled online. |

Enabling some features also enables their supporting settings. Fist assist requires physical fist melee and switches off conflicting native/weapon-melee behavior; grabbing/climbing also requires fist-aware melee to avoid a fast open-hand reach becoming a punch. Review the automatically changed rows. Settings are optional; automatic dependencies do not bypass session restrictions.

### Android gamepad and touch

Common Xbox-style USB/Bluetooth controllers use Android/SDL input: left stick moves, right stick aims, RT fires, LT throws grenades, A jumps/confirms, B melees/backs out, X reloads/uses, Y switches weapons, LB flashlight, RB grenade type, stick clicks crouch/zoom, Start pauses. D-pad/left-stick menu navigation is supported. Controller profiles can differ; use **Controller & touch settings** for face-button swap, dead zones and response.

The circular touch HUD supports multitouch, MOVE plus swipe-to-look, and FIRE dragging. Optional drag-anywhere look hides the look-stick graphic while keeping touch looking. In **HUD → OPTIONS**, export/import a layout through Android's file picker; imported changes are a preview until **SAVE**, and **CANCEL** discards them. Select a control and disable **Show and enable this touch control** to hide it; it remains recoverable in the editor. Presets include touch/gyro options, not gamepad mappings or saved games.

## 4. VR features and settings

### Body, weapons, scopes and feedback

- Standalone OpenXR, room-scale movement, recentering, smooth/snap turning, tracked hands and estimated full-body IK. **Legs + Arms** remains the default; Full Body, Arms + Hands and Hands Only are alternatives. Untracked elbows/torso/legs are estimates.
- Safe geometry is enabled by default on both editions. Graphics resolution and refresh are adjustable; **Refresh → Auto** returns the requested rate to the runtime's choice. Higher settings can reduce performance.
- Physical/locked weapon handling, first-grip protection, support-hand grip lock, holsters and temporary native animation handoff remain available. Per-weapon scope placement and **AIM STEADY** (Off/Light/Medium/Strong/Max) help fit sights and reduce small aiming movements. Shared aiming changes affect gun/shot/scope alignment, so start with a mild setting.
- Wrist HUD placement/size, head HUD and flashlight gestures remain configurable. **HAPTICS** scales general feedback; **HOLSTER HAPTICS** separately mutes holster entry/draw/stow cues. Immersive steering also has its own STEER HAPTICS option.

### Manual reload — WIP

Supported profiles include AR, pistol and sniper magazines; shotgun shells/pump; SPNKR tube/latch; flamethrower canister/cover; and the Needler crystal bundle. Plasma weapons keep their native battery/heat behavior. Unsupported custom guns retain native handling. Reloading uses native ammo accounting, with tactical-reload and reseating behavior, hand-aligned parts and event feedback. Hand pose, insertion and charging fit can still need adjustment. **CHARGE GRAB** helps tune charging contact; a moving gun and hand together should not count as a charging stroke. Turning manual reload off restores classic reloads. It remains solo-only.

### Physical grenade placement — WIP

**Grenades may be offset for your body/tracking setup.** Open **VR Settings → IMMERSION → GRENADES** and adjust **CHEST FWD**, **CHEST DOWN**, and **CHEST SPACING** in small steps until both slots are comfortable to reach. The slots follow a torso-facing frame that holds while looking down; they are not tied to whether a chest mesh is visible. Touch with the visible free palm before pressing Grip. **THROW POWER** adjusts throw strength (new default 1.5X); direction and momentum come from hand movement. Slot position and throw power are separate adjustments.

### Grabbing, ragdolls, impacts and parkour — WIP

- Living NPCs, allies, enemies and bodies use contact-based handling with species/weight differences. **DEATH RAGDOLLS**, **DEATH FORCE**, **RAGDOLL RANGE** (20/40/60/80 m; new default 60), **NPC RIG SLOTS** (up to 24), and **BODY RETENTION** control different aspects of physical bodies and cleanup. Engine/object pressure can still remove bodies or fall back to native deaths.
- Impact/slam handling applies native damage and eligible shield/body effects when contacts qualify. It can hurt allies as well. IMPACT SPEED and throw settings affect the result; native actor protection and effects still apply. NPC RESCUE is bounded recovery for eligible mission actors, not a guarantee every NPC can be recovered.
- CUSTOM NPC RIGS / CUSTOM SCENERY extend validated contact/rig paths, not arbitrary script-owned or unsupported geometry. LIFT VEHICLES is restricted to supported unoccupied ground vehicles/turrets in solo; occupied and protected vehicles are excluded. MAG DEBRIS keeps a bounded local visual pool, not permanent save-file objects.
- Parkour's newer defaults include CLIMB GRAB 14 cm, WALL TIME 2 s, WALL SPEED 1.5X and WALL LEAP 1.5X. Existing saved values stay. Physical movement can be uncomfortable; tune or disable individual actions.
- Fist assistance targets enemies, not allies/players, with a configurable reach (new default 2.5 m), short approach/target restraint, optional HIT HIGHLIGHTS, brief stun and stronger rear strike. It uses Halo hurt sounds/effects and a small procedural hit reaction. It is not a recreation of another game's combat engine or a scripted cinematic takedown.

### Vehicles — WIP

Ordinary vehicle defaults remain **Third Person + Right Hand steering**; left hand, head and stick are alternatives. Turret aim has right/left/head/stick options. Vehicle entry/exit recentering and per-vehicle first-person view offsets are available. **First-person view is still not recommended as the reliable default**; it needs further refinement despite reduced jitter.

IMMERSIVE VEHICLE automatically selects FIRST PERSON; returning to third person disables immersive controls. The Warthog uses a modeled wheel, Ghost a handlebar, Scorpion a drive stick and Banshee a flight bar/yoke. Vehicle-specific behavior differs from ordinary hand-ray steering; immersive tank turret aiming follows the head. TANK DRIVE and BANSH SLIDE add their respective stick/bar movement controls. CONTROL GLOW highlights reachable controls; VIRTUAL WHEEL can be hidden.

To fit controls, enter the vehicle, let the seat settle, then open VEHICLES. Adjust **CTRL REACH / LEFT / HEIGHT** and the relevant **HOG / GHOST / TANK / BANSH** rows; the live blue preview shows the grab placement. COMFORT REACH provides a reachable fallback. HOG GLASS, TANK HATCH and vehicle-specific view options are optional. Report the exact vehicle, seat, camera mode and offsets if something is misplaced.

## 5. Android / mobile and launcher

Flat Android keeps its familiar touch gameplay and common gamepad support, including reconnect/hot-plug, analog triggers, response/dead zones, vibration where supported and menu navigation. Touch visibility offers Auto, Always show and Always hide; Auto restores touch after controller disconnect. Gyro aiming is optional.

The launcher manages imports, selected game data, network populations, saved invites, project updates, font choice, help and support. Upstream information/downloads are separate; upstream executables are not blindly substituted for the integrated Quest/Android engine. VR-only gestures do not become touchscreen actions.

## 6. Multiplayer, co-op and voice

**Join:** in game, **Play → Multiplayer → Join Game → Server Browser**, or **LAN** for local hosts. Use **Direct Link** for invites. **Host PvP:** **Create Game → Internet or LAN → Multiplayer**, then Server Setup. **Host campaign co-op:** **Create Game → Internet or LAN → Singleplayer**, select mission/difficulty and Server Setup, then start and share the invite or make it public.

The app hosts on **network 28**. The launcher can show combined compatible networks and reported server/player counts, busiest first; **All compatible networks** is the new default, with targets **11–28** selectable. Close the game to change its target. This selects a client's discovery/admission behavior and does not downgrade hosted games. Counts/listings can be stale; HTTPS launcher catalogs and the in-game native discovery browser are separate sources.

Original Xbox-map PvP supports the implemented 11–28 client targets. Campaign co-op defaults to host network **15+**; **12–14** require explicit legacy opt-in. Custom Edition sessions require **23+** and matching maps/checksums. Retail PC/Custom Edition, MCC and retail Xbox networking are different protocols. Selecting a network cannot make incompatible content or protocols work. OpenCE web/browser players cannot join this app's hosts. Network27 map-sharing requests receive “not shared”; this host does not distribute maps.

Native co-op is supported; results still depend on game data, NAT/firewall, host settings, server state and player count. The selectable 128-player cap is an engine option, not a validated performance target. Start with a small group and collect both peers' logs for failures.

**Enhanced interactions online:** use Server Setup's **VR INTERACTIONS** permission and compatible peers. **HOST VR ACTIONS** is a separate opt-in for the host's fist/grenade actions; every peer must complete the capability handshake. PvP and guests keep native combat actions. Manual reload, custom-rig fallback, magazine debris and vehicle lifting retain local restrictions; parkour has local/authorized-host restrictions. NPC ragdoll pose synchronization supports up to four remote machines, which is not the ordinary co-op player limit.

**Voice chat:** the host must allow voice (Server Setup → Teamplay Options). In VR, **Voice Chat** offers Off, Push to Talk, Open Mic and Voice Volume (0–200%). Mic Off stops transmission but does not mute incoming voices; Voice Volume 0 does. Grant Android microphone permission when enabling transmission. Assign a PTT button under Buttons; it defaults to None. Flat Android uses native in-game voice settings; keyboard PTT defaults to V, or use Open Mic. There is no dedicated flat touch/gamepad PTT control. Earlier Quest voice capture/callback and join-diagnostic crashes were corrected; this exact pair still needs broad device testing. A silent server may have voice disabled.

## 7. Game revisions and game-file management

The tested USA Original, Rev 1 and Rev 2 images contain identical bytes for their 24 maps and are suitable for this port. The original Xbox XISO remains the recommended reference. This is not certification of every region, repack or modified image; content/checksums and network version matter more than the filename.

In **Game files & versions**, select/rename imported sets and choose the set used next launch. Byte-identical managed maps deduplicate, so those three images may not produce three selectable sets. **Delete imported copy** removes an inactive managed set, including its associated local configuration/saves; switch away first. The active set and protected **Existing game data** row cannot be deleted there. A grey “currently selected” row alone is not a delete button. Files chosen through Android's picker are extracted; the original ISO stays at its source location. Inbox ISOs can be removed after import. Source folders remain untouched.

SPV1/custom maps remain experimental. Map size alone does not prove compatibility; protected maps, resources, scripts and custom rig assumptions can still fail. Keep the original game-data set available.

## 8. Testing, known issues and reporting

**Individual testing and logs are this release's priority.** Please report both successful and failed tests, preferred settings and short videos where useful, especially reloads, grenade placement, ragdolls/slams, grabbing, parkour, immersive vehicles and multiplayer interaction combinations.

The supplied pair passed its recorded full automated regression suites, native builds, ABI lint and package checks. Test64 specifically fixes the settings-category out-of-bounds crash. A complete headset/phone/paired-co-op checklist for these exact binaries is not recorded; automated success is not a universal gameplay guarantee. Experimental features can remain inconsistent and should be enabled one at a time.

Logs are normally saved after launches under **Download/HaloCE**, with app-private fallback if Android denies access. Send the relevant session log, device/OS, app version, game-data set, map/mission, host/client role, selected network, relevant toggles and reproduction steps. For co-op, logs from both sides help. Remove private invites/device details before public posting.

**Support:** DM **@MeWhenINameMyself** or report in the [Halo CE Decomp Discord](https://discord.gg/S9uSCKxKx) or the [Flat2VR Halo CE discussion](https://discord.com/channels/747967102895390741/1555959498349215774). Preferences and comfort/placement feedback are welcome alongside bug reports.

## 9. Source, technical details and credits

- Public tag **v1.0.31**; APK label **1.0.31-test64**, code **76**. Runtime source: `d1a61e06` (original build identity; matching runtime code is included in this release tag). Release-tag source adds publication documentation/metadata; runtime code is unchanged.
- Package IDs: `com.halo.decomp` and `com.halo.decomp.vr`. Established signing certificate retained. Public assets are the two APKs and updater-required `compatibility.json`; GitHub supplies source archives from the matching source tag.
- OpenCE Build157 base, selected later integrations through Build201/network28, including networking, voice, gameplay fixes and earlier upstream rendering/performance fixes where applicable. This is not a full latest-upstream rebase or a promise of PGO speedups.
- Thanks to Bungie, the OpenCE/decomp contributors, the Quest/Android port contributors and testers. Willem Horak's glasses-FOV/resolution contribution ([PR #1](https://github.com/moistman42069/HaloCE-Quest-VR/pull/1)) remains included. See [credits](https://github.com/moistman42069/HaloCE-Quest-VR/blob/v1.0.31/CREDITS.md) and [third-party notices](https://github.com/moistman42069/HaloCE-Quest-VR/blob/v1.0.31/THIRD-PARTY-NOTICES.txt).
- Unofficial community project; not affiliated with Microsoft. No Halo ISO/maps are distributed. PC and Steam Frame ports remain deferred.
