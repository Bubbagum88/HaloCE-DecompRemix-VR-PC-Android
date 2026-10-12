# Test42 private candidate: 1.0.23-test42

This is a private Quest VR and Android test build. The public release remains
v1.0.18 until the owner accepts a later release. The candidate carries forward
all project changes made after v1.0.18 (Tests38-41), including the existing
network selector, saved game-image revisions, touch/gamepad support, safe
geometry defaults, VR controls and the user's Halo CE Quest icon.

## What changed after v1.0.18

- **Manual reload and weapon handling:** optional physical magazine removal and
  insertion, charging where profiled, two-hand handling and cancellation use
  the native ammo/state path. Reload remains solo-only. Supported weapon
  profiles determine which actions are available. Shoulder/hip magazine pouches
  follow the gun hand; the free hand performs the reload. Diagnostic contact
  bounds are logged once per weapon/model profile to keep reload action details
  readable when transient state resets cause a profile to be reacquired.
- **Weapon scopes and mounted aiming:** per-weapon scope adjustment and
  diagnostics; configurable right/left/head/stick vehicle and turret aiming;
  vehicle view/recenter settings and scoped reticles remain available.
- **Physical world interactions:** optional hand/object contact, consent-gated
  interaction sync and NPC handling. NPC graph fallback is limited to
  recognized or validated layouts. Manual reload and parkour remain solo-only;
  networked physics requires compatible peers and host permission.
- **SHAKE COOLING:** the optional gesture cools supported
  overheating weapons in solo play. It does not alter normal firing heat rules
  online.
- **CUSTOM SCENERY / CUSTOM NPC RIGS / MAG DEBRIS / LIFT VEHICLES / NPC RESCUE:**
  optional custom scenery/NPC graph paths, magazine debris, bounded vehicle
  lifting and mission-NPC rescue. Magazine debris is visual, local and reset on
  map change. Up to 32 discarded magazines remain visible for the loaded map,
  even if the source weapon object disappears;
  when full, older drops are retained and new visuals are skipped. Vehicle lift is vertical and
  limited to supported unoccupied vehicles. Rescue only applies to eligible
  live actors in the documented fall/recovery state.
  Custom scenery is restricted to validated supported collision bounds; it
  does not enable arbitrary BSP geometry or script-owned scenery.
- **GRAB REACH:** selectable from 12 to 40 cm. **NPC RIG SLOTS** controls 1-8
  mod interaction rigs, not Halo's native corpse count. Source review found no
  native corpse-count slider or fixed simultaneous corpse cap; the engine's
  per-corpse settling duration and general object/memory cleanup are separate.
  **HAPTICS** is the
  master for controller vibration. **HOLSTER HAPTICS** only mutes holster
  entry/draw/stow buzzes and does not mute reload or other effects.
- **Diagnostics:** interaction logs state the actual local/network session and
  active interaction settings when they change. They do not prove an action
  completed; use the device checklist and include the full log in reports.
- **Android touch-layout presets:** in-game **HUD > OPTIONS** can export or
  import a versioned layout through Android's file picker. The preset carries
  touch positions, sizes, visibility and touch/gyro options, but not gamepad
  mappings or saved game data. Imports stay preview-only until **SAVE**; use
  **CANCEL** to discard. In the same editor, select any control and turn off
  **Show and enable this touch control** to hide it from gameplay; hidden
  controls remain recoverable in the editor. Existing installs keep every
  control visible by default.
- **Refresh rate:** **Graphics > Display > Refresh > Auto** removes this app's
  fixed-rate preference and asks OpenXR to use the runtime's choice again.
  Choosing 72/80/90/120 Hz continues to request the highest supported rate at
  or below that value; the runtime can still decline a request.

## OpenCE and network compatibility

The engine base remains OpenCE Build157 / network24. Selected fixes reviewed
against official OpenCE Build167 are included; Build167 does not change the
network protocol. The launcher still offers client targets 11-24 or All
compatible, while hosting stays on 24. Build167's broader renderer/animation,
voice-chat/votekick and co-op setup UI changes are not represented as integrated
or verified by this candidate. Read `TEST42-OPENCE167-INTEGRATION.md` for the
exact boundary.

The supplied USA Original, Rev 1 and Rev 2 XISOs all imported successfully and
their 24 map files were byte-identical. Original remains the recommended
conservative baseline; this does not mean the tested Rev 1/Rev 2 sets are known
to be incompatible. Other regions, repacks and modified images remain
unverified.

## Important limits

NPC RIG SLOTS does not raise Halo's native corpse ragdoll count. Source review
found no native simultaneous corpse-count cap to raise: eligible bodies run a
settling solver for a bounded duration, while general object/memory pressure
may reclaim eligible off-screen garbage. The mod's custom
rig support is bounded to known or validated humanoid graph layouts; it is not
universal retargeting for arbitrary mods. Dropped magazines do not persist in
saves, survive a map change, create ammo, or replicate. Vehicle lifting does not
carry/rotate/throw vehicles. NPC rescue does not revive dead actors, override
scripts or guarantee every mission encounter. These interactions still need
Quest testing. No headset or live-server acceptance is inferred from host tests.

Install the matching APK over the existing app without clearing data. Keep the
Test40/Test41 artifacts for comparison and follow `TEST42-DEVICE-CHECKLIST.md`.
Do not publish this candidate as a stable release until testing is complete.
