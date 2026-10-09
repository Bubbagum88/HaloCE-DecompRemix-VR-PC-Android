# Test41 implementation and validation status

## Candidate identity

Private candidate **1.0.22-test41 / Android code52**, based on OpenCE
Build157/network24. Public v1.0.18 and the delivered Test40 APKs remain
unchanged. PC/Steam Frame remains deferred. Test41 is not published.

## What the two logs establish

- `halo_log_2026-10-09_07-25-16-112_12968.txt` contains one confirmed public
  multiplayer join (network24, 12 players). The user confirms this was one
  multiplayer match; its options should not be read as solo feature attempts.
- `halo_log_2026-10-09_07-29-31-202_14750.txt` receives a P2P invite and starts
  a signalling attempt, but never records a completed network join. At
  07:29:37 it loads the saved campaign (`the saved game is taken`) and runs
  in-game VR frames. This is solo campaign evidence, as the owner clarified.
- The source's solo campaign setup assigns `_game_connection_local`
  (`source/main/main.c`, `main_setup_connection`). No solo-as-multiplayer bug is
  established. The pending invite does not itself switch the game's connection
  mode.
- Stronger direct evidence: `vr_manual_reload_model` only emits its authored
  magazine/chamber bounds after passing `game_connection() ==
  _game_connection_local`. The second log emits that line repeatedly for the
  same weapon at roughly 30 ms intervals. This proves the gameplay path saw the
  solo session as local. It also proves the reload transaction is repeatedly
  reset/reacquired; the log does not identify which later reset condition is
  responsible, so no speculative reload behavior change is included.
- The logs show settings being written. The second log shows manual reload
  reaching valid authored magazine and chamber bounds, but no reload-state
  event. It contains no parkour activation, world/NPC grab, vehicle-lift,
  magazine-spawn or rescue-success event. The prior build did not record the
  session connection beside these settings, and most of these actions were not
  instrumented. Therefore the logs do not establish that every action was
  attempted or identify a specific failure inside those action paths.

## Evidence-backed changes

1. **Solo/network diagnosis:** world-interaction diagnostics now log the actual
   game-connection enum/name, `game_in_progress`, map-loaded and VR state, co-op
   state, the relevant toggles, reach, NPC rig capacity and haptic strength.
   A line is emitted when that state changes, not every frame. This distinguishes
   a pending invite from an actual network session.
2. **Physical grab reach:** world-object and NPC contact used a hard-coded
   12 cm surface-distance limit. The VR menu now offers 12, 18, 25, 30 and
   40 cm, defaulting to 25 cm for new configurations. The same bounded setting
   is used by the broad-phase, ray start and final surface-distance checks.
   Solid-surface collision, target identity and line of sight remain required;
   this does not permit reaching through walls.
3. **NPC interaction-rig capacity:** the fixed physical NPC rig pool and menu
   now support 1-8 simultaneous rig slots, with a new-configuration default of
   eight. The setting is labelled **NPC RIG SLOTS** because it controls this
   mod's held, settling and recovery rigs, not Halo's separate native
   corpse-ragdoll cap. Existing config files keep their saved value.
4. **Climb contact coverage:** the wall-grab probe now sweeps 16 horizontal
   directions instead of only six world axes. Angled wall hits still require
   native static collision and stay within the selected reach.
5. **One haptics control:** every controller vibration already routes through
   the global `vr.haptics` scaler. The separate `WEIGHT HAPTICS` toggle is
   removed; bounded load feedback now follows that same master strength, and
   setting it to 0 disables every haptic effect.
6. **Optional holster buzz:** added `HOLSTER HAPTICS`, enabled by default, to
   mute only the weapon-hand buzz for holster entry, weapon draw and stow.
   Holster positions/actions and free-hand magazine pouches stay independent;
   reload and every other vibration remain controlled by global HAPTICS.

## Preserved behavior and evidence limits

Test41 does not change reload state-machine behavior, native AI recovery, NPC
rescue eligibility, custom-rig admission, vehicle eligibility, networking,
saves, Android touch or accepted VR defaults. It extends the configured reach
into the actual world/NPC surface checks and parkour wall-grab probe, and clears
parkour ownership when disabled. The production parkour test now includes a
diagonal wall contact exactly at the configured reach, a case the old
world-axis rays missed. A source test now compiles the production NPC
eligibility function (including player/script/animation/grenade/weapon-busy
rejections) instead of a fake permissive stub; normal Grunt admission and the
validated custom-rig path pass. It removes the separate load-haptics toggle and
applies the HAPTICS master strength to that effect. The holster-only mute wraps
four feedback sites without changing their hand/zone/action logic; reload keeps
the free hand, pouch selection and global haptics path. None of these host
checks establish that a Quest controller contact or motion completed in game.

The session/config log confirms which mode and settings are active; it does not
by itself prove a hand contacted a target or that a reload/rescue/parkour action
completed. Actual headset action checks remain on
[TEST41-DEVICE-CHECKLIST.md](TEST41-DEVICE-CHECKLIST.md). Do not claim that the
new physical interaction behaviors are device-confirmed until the owner tests
the packaged APKs.

## Validation

Focused NPC-pool, grab-reach, menu-range, world-physics, NPC rescue, parkour,
reload, debris, interaction lifecycle and haptic tests are listed in
[TEST41-DELIVERY.md](TEST41-DELIVERY.md). The final APK hashes and build/package
results are recorded there after packaging.
