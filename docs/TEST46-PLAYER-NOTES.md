# Test46 private candidate: 1.0.27-test46

## Changes in Test46: contact latching and allied NPCs

- **NPC GRAB** now accepts supported friendly Marines and crew as well as the
  existing enemy species and corpses. Acquisitions still require the tracked
  palm collision volume to overlap the NPC's authored collision model, followed
  by a fresh Grip press. Pointing at an NPC or holding Grip before contact does
  not acquire it. Friendly ordinary AI orders are preserved while the mod
  temporarily suppresses movement/trigger controls during the hold; forced
  immediate orders remain excluded.
- While Grip remains held, ordinary hand movement and target-to-joint distance
  no longer drop an NPC or prop. The held target follows a bounded per-step
  hand position. Large tracking discontinuities clear throw velocity and rebase
  the target instead of releasing it. Invalid tracking, lost ownership, stale
  entities, unsafe target states and explicit Grip release remain logged
  cancellation/release conditions.
- Host-authoritative co-op prop holds now rate-limit large remote target steps
  while retaining contact ownership. The host still independently checks palm
  overlap with the object's authored collision model and validates line of
  sight after contact.
- Interaction logs now distinguish a contact acquisition, a started hold
  constraint, a tracking rebase, solver strain and a release/cancellation
  reason. Logs help diagnose a session but do not prove a controller action
  succeeded.

Private Quest VR and Android test build. Public v1.0.18 remains the accepted
release; Test46 has not been published or device-tested. It carries forward all
project changes made after v1.0.18 through Test45, plus the A10 calibration,
Build167 voice, retained-magazine, vehicle-lift and rescue-eligibility updates
documented below. PC/Steam Frame remains deferred.

## Changes in Test46

- The first-run screen, main launcher and **Game files & versions** manager now
  explain that picker-selected ISO/XISO files import supported maps
  only. The original image remains in its original location; the launcher does
  not keep or delete it. Use Android Files to remove that original file. Only a
  copy placed in `game-versions/inbox` can be deleted from the launcher.
- The first-run import is installed as the protected **Existing game data**
  base set. The manager explains that its disabled **Currently selected** row
  is expected when it is the only set; use **Import ISO / XISO** or **Scan
  inbox** to add separately selectable managed sets. The base row cannot be
  deleted or replaced from the manager.
- In Halo CE's opening A10 look-calibration sequence, the directional checks
  and scripted look-at checks follow the current hand-aim reticle ray when the
  rendered ray is fresh and valid. Outside A10 and in head-aim mode, the
  existing head-based behavior remains. In hand-aim mode, invalid/stale ray
  data pauses calibration progress until a valid rendered ray is available.
- No other mission's script visibility, AI behavior, weapon aim, reticle render,
  saves, networking, Android touch input, or Safe Geometry behavior is changed.

This is source/test verified only. Calibration still requires Quest testing to
confirm the in-game tutorial's authored timing and target sequence.

## Game-data selection and storage

- The main launcher shows the selected game-data label and number of installed
  distinct sets. Tap it to open **Game files & versions** and choose the set
  used on the next launch.
- The full manager marks the active set, shows detected cache build and map
  fingerprint, and allows each imported set to be selected or renamed.
- **Delete imported copy** removes an inactive managed set, including its maps,
  configuration and local saves. Switch to another complete set first. Existing
  game data cannot be deleted through this control.
- ISO/XISO files placed inside the import inbox can be deleted there after
  import. An ISO/XISO selected directly through Android's file picker is not
  retained; the source ISO/XISO stays where you selected it. Source folders
  also remain untouched.
- Byte-identical managed map sets deduplicate to one profile; Existing game data
  is a separate protected base row. The verified USA Original,
  Rev 1 and Rev 2 XISOs contain identical bytes for their 24 maps, so importing
  them does not create three distinct selectable map sets. Other images remain
  separately selectable when their imported maps differ. Filenames do not
  verify a disc revision.

Selection uses the existing atomic `active-data.txt` marker consumed by native
and Java startup. Switching applies to the next launch. See
`GAME-DATA-LIBRARY.md` and `USA-IMAGE-COMPARISON.md` for evidence and limits.

## Retained features since v1.0.18

- **Manual reload and weapon handling:** optional physical magazine removal and
  insertion, charging where profiled, two-hand handling and cancellation use
  the native ammo/state path. Reload remains solo-only. Supported weapon
  profiles determine which actions are available. Shoulder/hip magazine pouches
  follow the gun hand; the free hand performs the reload. Diagnostic contact
  bounds are logged once per weapon/model profile.
- **Weapon scopes and mounted aiming:** per-weapon scope adjustment and
  diagnostics; configurable right/left/head/stick vehicle and turret aiming;
  vehicle view/recenter settings and scoped reticles remain available.
- **Physical world interactions:** optional hand/object contact, consent-gated
  interaction sync and NPC handling. NPC graph fallback is limited to
  recognized or validated layouts. Manual reload and parkour remain solo-only;
  networked physics requires compatible peers and host permission.
- **SHAKE COOLING:** the optional gesture cools supported overheating weapons
  in solo play. It does not alter normal firing heat rules online.
- **CUSTOM SCENERY / CUSTOM NPC RIGS / MAG DEBRIS / LIFT VEHICLES / NPC RESCUE:**
  optional custom scenery/NPC graph paths, magazine debris, bounded vehicle
  lifting and mission-NPC recovery. Magazine debris is visual and local. Up to
  32 discarded magazines remain visible through same-map checkpoint/core
  restores during the running session; map change, disabling MAG DEBRIS, or
  entering an online session clears them. When full, new visuals are skipped.
  Vehicle lift uses contact plus Grip to move and rotate a supported unoccupied
  Warthog, Ghost, Scorpion or turret with one or two hands. Translation and
  orientation are speed-capped; release lets the native vehicle solver continue
  with gravity and collision. It is solo-only, does not teleport, and excludes
  occupied, destroyed, parented, named/movie-star, boat, aircraft and networked
  vehicles. Rescue applies only to eligible live actors
  in the documented fall/recovery state. Custom scenery uses validated
  collision bounds; it does not enable arbitrary BSP geometry or script-owned
  scenery.
- **HAND CONTACT:** sets the shared palm-collider radius (2, 4, 6, or 8 cm; 4 cm default), not a target-search reach. World objects and NPCs can be grabbed only when the tracked hand volume overlaps their collision model; the co-op host repeats the NPC/object collision check. Manual reload part bounds, virtual pouch points, and optional vehicle-wheel handles use touch-then-press. Magazine insertion is a separate held-object alignment step. To climb, touch a solid vertical surface with a free hand, then squeeze Grip. Aim direction cannot select these targets. **NPC RIG SLOTS** controls 1-8
  mod interaction rigs, not Halo's native corpse count. Source review found no
  native corpse-count slider or fixed simultaneous corpse cap; per-corpse
  settling duration and general object/memory cleanup are separate.
  **HAPTICS** is the master controller-vibration control. **HOLSTER HAPTICS**
  only mutes holster entry/draw/stow buzzes and does not mute reload or other
  effects.
- **Diagnostics:** interaction logs state the local/network session and active
  interaction settings when changed; logs do not prove an action completed.
- **Android touch-layout presets:** in-game **HUD > OPTIONS** can export or
  import a versioned layout through Android's file picker. Presets include
  touch positions, sizes, visibility and touch/gyro options, not gamepad
  mappings or saved game data. Imports stay preview-only until **SAVE**; use
  **CANCEL** to discard. Select a control and turn off **Show and enable this
  touch control** to hide it from gameplay; hidden controls remain recoverable
  in the editor. Existing installs keep controls visible by default.
- **Refresh rate:** **Graphics > Display > Refresh > Auto** removes this app's
  fixed-rate preference and asks OpenXR to use the runtime's choice again.
  Choosing 72/80/90/120 Hz continues to request the highest supported rate at
  or below that value; the runtime can still decline a request.

## OpenCE Build167 voice chat (selected Test46 integration)

Test46 adds OpenCE's host-relayed Opus voice path using optional message IDs
80-82. The engine remains based on Build157/network24; this does not raise or
change the network protocol version. Voice-capable peers participate after
they advertise that they can hear voice; this is not a claim that older or
unmodified clients support voice.

- The microphone mode defaults to **Off** for privacy. Off stops transmitting
  but still allows incoming voice when **Voice Volume** is above zero. Set
  Voice Volume to **Muted** (0) to silence all incoming speakers; the available
  range is 0-200%.
- In VR, open **VR Settings > Voice Chat** to choose Off, Push to Talk or Open
  Mic and set incoming voice volume. Bind a Quest controller button under
  **VR Settings > Buttons > Push to Talk**. The binding defaults to **None** to
  avoid taking over a gameplay control. The keyboard binding remains available
  in VR too.
- On flat Android, the default keyboard PTT key is **V** and can be changed in
  **Controls Setup**. Flat Android has no dedicated hold-to-talk touch button
  or gamepad PTT binding; use a connected keyboard or Open Mic.
- Android declares the microphone permission. The SDL permission request is
  asynchronous and starts only when voice transmission is enabled and allowed
  by the host; capture opens later only if PTT/Open Mic is still active after
  permission is granted. Actual permission UI and headset microphone routing
  still need device testing.
- Hosts configure lobby voice, in-game routing, bitrate and proximity in
  **Server Setup > Teamplay Options**. Lobby speaker icons show who is speaking.
  Per-player mute controls are not exposed; set Voice Volume to zero to mute
  everyone.

Source checks verify configuration, controls, network wiring and Android audio
bridging. Quest permission prompts, capture/playback, lobby/match routing and
two-client voice have not been runtime-verified. See
[`TEST46-VOICE-CHAT.md`](TEST46-VOICE-CHAT.md) for setup and the device test
boundary.

## OpenCE, network and image compatibility

The engine base remains OpenCE Build157 / network24. Selected fixes reviewed
against official OpenCE Build167 are included; Build167 does not change the
network protocol. The launcher offers client targets 11-24 or All compatible,
while hosting stays on 24. The official Build167 teamplay settings overlay now
defines the host controls for voice routing, lobby voice, bitrate and
proximity. This menu asset alone does not establish working microphone capture,
network transport or playback. Selected voice-chat runtime is integrated as
described above, but per-player mute, votekick, the upstream co-op setup UI, and
Build165-166 renderer/camera/animation changes are not included or verified.
The Test42 audit linked in the repo is a historical snapshot and is
superseded for voice integration by the Test46 notes and voice-chat record.

The supplied USA Original, Rev 1 and Rev 2 XISOs all import successfully and
their 24 map files are byte-identical. Original remains the recommended
conservative baseline; this does not mean the tested Rev 1/Rev 2 sets are known
to be incompatible. Other regions, repacks and modified images remain
unverified.

## Campaign co-op and enhanced interaction limits

Campaign player-count options remain those supplied by OpenCE. The 128-machine
transport table is not a claim that 128-player campaign spawning, AI, vehicles,
checkpoints or transitions are stable or device-tested. Enhanced world-object
interaction can negotiate above four remote peers when the host enables it and
all participating clients support it. Articulated NPC pose synchronization is
still limited to four remote peers; above that, NPC physical handling falls
back to native behavior. Manual reload and parkour remain solo-only. Native
campaign co-op and its usual capacity are unchanged by these optional systems.

## Important limits

NPC RIG SLOTS does not raise Halo's native corpse-ragdoll count. Source review
found no native simultaneous corpse-count cap to raise: eligible bodies run a
settling solver for a bounded duration, while general object/memory pressure
may reclaim eligible off-screen garbage. Custom rig support is opt-in and
solo-only for `_actor_none` and grounded custom `_actor_engineer` tags that
pass the native head/pelvis, capsule, graph and non-flight checks. It reuses
the authored graph; it is not universal retargeting for arbitrary mods or
online custom-layout support. Dropped magazines are not serialized into save files, do not survive a
map change, create ammo, or replicate; the 32 visual props survive only same-map
state restores in the current process. Vehicle lifting supports bounded
hand-driven translation and rotation for the listed ground vehicle classes;
it does not teleport or add an extra throw impulse, and release retains only
the capped native velocity.
NPC rescue does not revive dead actors, override scripts or guarantee every
mission encounter. These interactions still need Quest testing. Automated
checks do not establish headset or live-server acceptance.

Install over the existing app without clearing data. Follow
`TEST46-DEVICE-CHECKLIST.md` before treating this candidate as accepted.
