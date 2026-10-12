# Test52 private candidate: 1.0.20-test52

## Test52: voice crash root cause fixed

Test51 / v1.0.19 still closed on Quest as soon as you spoke in a voice-enabled
game. The supplied logs show the crash right after the first microphone frame
was encoded, inside the Opus voice codec (`encode_pulses`). The cause was in the
build pipeline, not the voice code: the step that converts the Quest guest's
assembly from Apple to Android format was rewriting text and byte-table data.
It deleted one byte of the **Opus pulse-cache table**, so the encoder read past a
table and crashed when real speech arrived. The converter now passes all data
through untouched; a new check compares the built tables with the Opus source.
The same conversion bug had also altered a few other strings and tables (the
loading tone, a sound-effects image, settings-file number parsing and text
classification); they are corrected too.

A second, related bug class is fixed as well: **missing function prototypes**.
On the Quest/Android guest ABI, a call to an undeclared function passes
variadic and decimal arguments in the wrong place. That is why Test50/Test51
voice logs showed nonsense numbers (and why Test50 crashed in a log line). It
also gave the NPC grab/recovery clearance test a garbage radius, drew the
scoreboard at the wrong scale, and could misread multiplayer vehicle-placement
results. Every guest file now declares what it calls, and the build fails if a
future change forgets.

This candidate is built with the same compiler setup as public v1.0.18. Gameplay,
network protocol (network 24), voice protocol and settings are otherwise
unchanged from v1.0.19. Voice still needs a voice-enabled host and a nonzero
receive volume; please retest talking in a lobby and in a match, on more than
one server if possible. See [Test52 crash analysis](TEST52-CRASH-ANALYSIS.md)
and [Test52 device checks](TEST52-DEVICE-CHECKLIST.md).

---

# Test51 private candidate: 1.0.32-test51

## Test51: network-join crash and voice-config fix

The two supplied Quest crash logs show successful admission and map loading,
followed by a fault in Test50's host voice-settings diagnostic. Test51 changes
all voice diagnostics to integer-only formatting and records the host settings
before logging. **Host voice settings accepted before diagnostics.** The voice
protocol, host routing, microphone behavior and existing in-game voice controls
remain unchanged. No Android launcher voice options were added.

Voice still requires the host to enable lobby/in-game routing, a compatible
Build167 voice relay on the host and peers, a nonzero listener receive volume,
and a speaking player. If logs report no host settings, confirm host setup and
version first. The fix is source/test verified; Quest join and two-client voice
still need a device check. See [Test51 crash analysis](TEST51-CRASH-ANALYSIS.md)
and [Test51 device checks](TEST51-DEVICE-CHECKLIST.md).

---

## Test50 carried-forward features

## Test50: voice diagnostics and sprint toggle

- **Mounted reticle alignment:** driver and gunner shots (including tanks,
  Ghosts and mounted turrets) now follow the selected reticle/muzzle ray. The
  Test49 log showed native camera aim assist turning shots 2.28°/2.61° away
  from the reticle. Test50 bypasses that correction only for the local VR
  driver/gunner, avoiding target snapping. On-foot, passenger, remote-player
  and flat Android aim assist stay unchanged. Random spread can still move
  individual rounds around the center ray.

- **Sprint:** in VR Settings → Locomotion, turn **Button Sprint** on. **Sprint Toggle** defaults to **Hold**; choose **Toggle** to click left stick once to start and again to stop. Hold remains unchanged unless Toggle is selected. Recenter, losing focus, seating, or losing the VR input state cancels the toggle. Sprint remains local/offline movement only and respects existing movement limits.
- **Voice:** behavior and privacy defaults are unchanged. Test50 logs host voice settings, local mic mode and receive volume, encoded frames handed to the network path, host-accepted/relayed frames, and successful incoming Opus decoding. It never records/logs audio or player names. A host that sends no Build167 settings is called out after five seconds. Voice still requires a compatible, voice-enabled host and peers, host routing that includes the listener, nonzero receive volume, and a speaking player.
- **Evidence boundary:** the supplied Test49 log shows Wi-Fi, a 48 kHz stereo output device without reported underruns, and microphone open/close without permission/device errors. It does not establish that anyone spoke or that remote audio was received. See [Test50 voice diagnostics](TEST50-VOICE-DIAGNOSTICS.md).
- **Upstream:** the latest official release checked on 2026-10-10 is OpenCE Build177; the exact-match reticle art was already integrated. Engine base remains Build157/network24 with selected compatible changes through Build177, not a full Build177 rebase.

Device checks: [TEST50-DEVICE-CHECKLIST.md](TEST50-DEVICE-CHECKLIST.md).

---
# Test49 private candidate: 1.0.30-test49

This candidate carries forward Test48, Test47, and the cumulative
player-facing features below. It retains the signed weapon-datum fix and
restores surface-contact haptics to the v1.0.18 collision and animation
ownership gates. Weapon recoil values and routing match v1.0.18. It also logs
whether melee and weapon-switch actions were emitted separately. The APKs are
for owner testing; they are not a public release.

## Test49 corrections and Test48/Test47 changes to retest

- **Controller haptics:** palm pressure buzzes only when the tracked hand's
  actual surface collision is pressing in and VR IK owns that arm, matching
  v1.0.18. Finger contact feedback uses that same arm-ownership gate. The
  extra head-to-hand collision probe no longer renews vibration every render
  update. Weapon recoil amplitudes/durations and two-hand routing are unchanged
  from v1.0.18. The OpenXR log confirms action availability and runtime
  acceptance, but only headset testing can verify motor feel.
- **Weapon switch / melee:** the supplied log records holster weapon switches
  and resulting weapon changes, but does not record a melee action. The
  gameplay action bits and default inputs remain separate; this candidate
  reports the emitted melee/switch mask and physical swing events for any
  retest. No input binding was changed.

- **Grip release / holsters (confirmed regression fix):** OpenCE weapon datum handles are signed values; valid live handles can be negative. Only `-1` means no weapon. Test47's release latch, holster storage/pruning, and pending-release recovery incorrectly rejected every negative handle. Test48 checks the actual empty sentinel, so releasing a gripped weapon drops it, releasing inside a holster stores it, and re-gripping an occupied holster can request that exact weapon. Retest with both weapons shown in the supplied log (`-431815724` and `-431750187`).
- The matching regression tests exercise negative live unit/weapon handles through the release, hand-state recovery, holster store/draw/prune paths, and preserve cancellation when grip is re-pressed, tracking/focus is lost, recenter occurs, or an interaction owns the hand.
- **Signed weapon datum fix:** negative live weapon IDs are valid; only `-1` is the empty sentinel. Grip release, dropping, holster storage/pruning, and exact holster draw use that sentinel correctly. Test49 retains the Test48 fix.

- **Hands/arms:** the arm model now keeps the original upper-arm and forearm
  lengths. The wrist target is clamped to what the shoulder and authored bone
  lengths can reach, with a small shoulder adjustment; the solver no longer
  lengthens or compresses the arm to force the controller pose. Test normal
  reach, crossing arms, looking down at the torso, turning the body, and
  tracking/recentering transitions.
- **Manual reload:** enable **MANUAL RELOAD** in VR Controls. Use the configured
  free-hand **RELOAD INPUT** (Grip by default; Trigger is optional) only after
  the palm touches the authored magazine/handle or the enabled hip/shoulder
  pickup point. Pull the magazine clear, release, take a replacement from the
  body pouch, align it with the socket, and release it to seat. Finish with the
  authored handle/pump/latch. The configured **USE / RELOAD** action ejects a
  magazine only while the free palm contacts it; it cancels an active reload.
  Quest B is the default USE / RELOAD button. Right-stick click remains melee.
  Unsupported profiles keep native reload; physical reload remains solo-only.
- The reload log now reports changes in the mapped action, native reload bit,
  free-hand Grip/Trigger, contact with the authored magazine/pouch/chamber, and
  interaction ownership. A missing contact or conflicting owner should now be
  diagnosable from a single session log.
- **New Game > multiplayer map:** a local solo map load should spawn at a
  multiplayer scenario start inside the BSP with the multiplayer biped, instead
  of reusing a campaign continuation unit. Network matches and campaign starts
  are unchanged.
- **BODY RETENTION** (saved as `vr.ragdoll_retention`): solo campaign defaults to a higher active-garbage
  cleanup threshold (75 trigger / 45 target, scaled per 16 players). Choose
  **STOCK** for OpenCE's 50 / 30 thresholds or **100** for 100 / 60. Corpses
  share this pool with other garbage, so this retains eligible offscreen bodies
  longer but is not a fixed corpse-count guarantee. Memory/object pressure may
  still collect sooner. Network and local multiplayer always use stock values.

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
- **HAND CONTACT:** sets the shared palm-collider radius (2, 4, 6, or 8 cm; 4 cm default), not a target-search reach. World objects and NPCs can be grabbed only when the tracked hand volume overlaps their collision model; the co-op host repeats the NPC/object collision check. Manual reload part bounds, virtual pouch points, and optional vehicle-wheel handles use touch-then-press. Magazine insertion is a separate held-object alignment step. To climb, touch a solid vertical surface with a free hand, then squeeze Grip. Aim direction cannot select these targets. **NPC RIG SLOTS** controls 1, 2, 4, 8, 12 or 16 mod interaction rigs (default 8). **BODY RETENTION** separately raises solo-only engine garbage thresholds to 75/45 by default or 100/60; STOCK restores 50/30. This changes the shared pool, not a fixed corpse count. Native tag eligibility remains; memory/object pressure may clean sooner, and multiplayer always uses stock thresholds.
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

The engine base remains OpenCE Build157 / network24. This is a selective
integration through official Build177, **not** a full Build177 engine rebase;
network24 and the launcher's network selector stay unchanged. The candidate
includes the compatible Custom Edition tag guard, Android cleanup, large
co-op respawn selection, pagemap-denied ART-memory fallback and exact-match
reticle artwork. Build175's old-kernel fixed-map safeguard was already present
and is retained. Build174's high-resolution button rendering was reviewed but
not merged because its upstream renderer/asset patch conflicts with the
customized Android and VR menu paths. The exact scope and test limits are in
[the Build177 integration audit](TEST47-OPENCE177-INTEGRATION.md).

Build167 voice chat remains integrated as described above, without changing
network24. The launcher offers client targets 11-24 or All compatible, while
hosting stays on 24. Selected assets do not establish device-level voice,
server, map-revision or co-op compatibility; see the device checklist.

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

NPC RIG SLOTS changes the mod's articulated interaction pool, not native
ragdoll eligibility. Test47's BODY RETENTION adjusts the shared active-
garbage cleanup threshold only in solo VR campaign. There is no exact corpse
count guarantee: eligible bodies run the tag-gated settling solver, and memory
or object pressure may reclaim off-screen garbage. NPC interaction slots allow 1,
2, 4, 8, 12 or 16 active mod rigs; new configurations remain at 8 to limit
Quest CPU work. Custom rig support is opt-in and solo-only for otherwise-
unprofiled grounded humanoid actor variants whose native biped capsule and
authored graph checks pass. It simulates the captured graph without assuming
stock head/pelvis markers; malformed,
flying, swarm and online custom-layout rigs remain unsupported. Dropped magazines are not serialized into save files, do not survive a
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
