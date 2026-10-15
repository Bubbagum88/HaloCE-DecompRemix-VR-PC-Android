# Test70 checklist: release-preparation and precision polish

Private successor to Test69, **1.0.37-test70 / code82**, branch
`test39-interaction-completion`. Source: Test69's delivered tree (APKs from
`03c364ea`, record `2cf05f63`) plus this work. Local commits only; no
push, publish, install or game launch. Saved settings preserved (one
documented exception: GRAB ASSIST at the old automatic 10 cm moves to 15 cm,
once). Network 29 unchanged.

Owner's request (2026-10-15): 72 items, "REGRESS NOTHING". Evidence
reviewed: four logs (two 1.0.10 from 2026-10-06; a 1.0.31-test64 Quest 3
session 2026-10-14 08:44-13:53, left-handed, locked then physical weapons;
its 2 s launch twin), four screenshots (two "problem with the disc", two
left-hand rocket launcher with reversed lettering), the owner's Altheros and
Lumoria files. No Test69 log of Altheros or MCC was supplied.

Legend: [x] done and tested off-device; [~] partly, or done but only a
headset can confirm; [=] verified, deliberately unchanged; [ ] not done.

## Campaigns and launcher (1-4, 66)

- [x] 1 MCC: cause found. Test67's merge kept this port's
  `cache_files_windows.c`, dropping GulchCE's three MCC hooks; every MCC level
  was looked for among the Xbox maps, not found, and
  `display_error_damaged_media()` followed (the screenshots). Hooks restored.
  Labelled "Experimental — currently not working" until a headset confirms.
- [~] 1 Altheros: still labelled experimental. Its scripts were fixed in
  Test69; the next step (model conversion) holds each level's model data in
  one block: 24-57 MB for Altheros (b40 56.5 MB) against at most 20 MB for
  SPV1 (measured from the maps' headers), plus 13-26 MB of tags. Likely the
  next failure point; not changed blind (SPV1 shares the code). A Test69/70
  launch log will name the step.
- [x] 2 SPV1 labelled Supported; flow unchanged.
- [x] 3 Project Lumoria: a mod of its own levels (lumoria_a-d), imported
  straight from `Lumoria_Full_Campaign.zip` (or its folder), sizes and
  SHA-256 verified (recipe from the owner's archive), Custom Edition's
  resource maps as SPV1; its own ui.map and Windows DLLs are left out (no
  redistribution permission: the player supplies the archive). Installs beside
  the original campaign: New Game, CUSTOM SINGLEPLAYER, lumoria_a. Labelled
  Supported (the owner: it works).
- [x] 4 What's New: shown once after a version change, reopenable ("What's
  new in this version"), "View full release notes on GitHub" opens the
  device browser.
- [x] 66 status labels on every campaign button and panel, and MCC's section.

## Weapons (5-6, 14-25)

- [x] 5 Locked weapons: a grip at a holster stores the gun (hand empty:
  nothing drawn or fired, free to climb/grab), an empty hand's grip draws it.
  Where physical weapons are allowed (local, or physical multiplayer).
  Halo has no unarmed state: with one weapon the stow cannot switch away and
  the gun returns after the pending timeout, as with physical weapons.
- [=] 6 Scope: unchanged (user error confirmed; right stick click zooms).
- [x] 14 Needler with MANUAL RELOAD: four deliberate shake strokes in 1.2 s
  start the native reload (strong pulse); automatic reload waits; the reload
  button still works. The crystal-by-crystal profile is gone.
- [x] 15 Shake cooling: the detector missed brisk shakes (its 1 m/s test fell
  at the stroke's turn) and sampled only when fully overheated. Strokes are
  now counted by peak speed and length (jitter, aiming, walking and melee
  swings excluded: tested), cooling 1.5x-3x while the gun is hot, a light
  tick per stroke. SHAKE COOLING stays off by default.
- [x] 16 Rocket launcher: empty reload no longer waits for the push bar; the
  tubes are ready once seated, as the partial reload was.
- [x] 17 Full-empty audit: magazine guns (AR, pistol, sniper) and the shotgun
  still need charging/pumping when emptied (real); canister (flamethrower)
  ready when seated like the launcher; any gun owed charging ticks the gun
  hand every 1.5 s. Ammo moves only at the native commit (unchanged).
- [x] 18-19, 25, 32 Left hand: MIRROR BUTTONS (AUTO) puts the face buttons,
  so use/reload and the magazine release, on the gun hand even with standard
  sticks (the community log: left-handed, face buttons on the right
  controller). Bindings are logical and never rewritten by handedness, so
  custom maps survive; MIRROR BUTTONS OFF restores the old layout.
- [~] 20 Left-hand visuals: rocket launcher, sniper, shotgun, pistol drawn the
  right way round (mirrored back whole about the grip); AR keeps its display
  fix; Covenant guns stay mirrored. Winding per part at any size. Needs the
  headset to confirm each gun.
- [~] 21 Left-hand reload parity: shared code paths (pouches, poses
  mirrored, shake reload/cooling hand-agnostic, haptics, MIRROR BUTTONS for
  the eject). Device check.
- [=] 22 Sniper hold unchanged (quality reference).
- [~] 23-24 Pistol/AR magazine holds: measured from the reload animations,
  the AR's magazine sat ~3 cm behind the fingers and the pistol's animation
  never grips its magazine (19+ cm from the wrist in every frame). Their
  magazine centre is now placed in the closed hand of the same frame's fingers
  (`vr.reload_grip_fit`, on; off restores Test67's place). Other guns
  unchanged (shotgun shell, rocket tubes keep Test67's verified holds).

## Controls (26-34)

- [x] 26-30 Remapping never reshuffles: a row is edited in place (A or
  left/right: the choice shown with a "?", nothing written; A sets); a taken
  button asks CANCEL / SWAP / CLEAR / BOTH; NONE for every gameplay action.
  A row is about 20 letters wide (test_test25 holds every row to it), so the
  row shows the choice and the hints line says whose button it is, what A
  will do and which is the default.
- [x] 31 RESET CONTROLS (the row's width holds no more) first and last on
  BUTTONS; "Reset this binding" = choose the value the hints line calls
  (DEFAULT).
- [x] 33 Contextual ownership shown in rows: `*` off for now (Button
  Sprint, grenade on the grip, the grip with physical weapons), `+` shared,
  the hints line saying what the marks mean. See TEST70-CONTROLS-AUDIT.md.
- [x] 34 Full audit: TEST70-CONTROLS-AUDIT.md.
- [x] Side fix: the Button Sprint restore mask dropped PUSH TO TALK (bit 8).

## Movement (7-13, 50-55)

- [x] 7-10 SLIDE (off by default; LOCOMOTION page): sprint + crouch (button,
  or with CROUCH SLIDES the head) slides with the run's momentum; friction,
  slope, steering, duration, wall stop; JUMP CANCELS keeps momentum into the
  jump (wall-run chaining unchanged). Brings BUTTON SPRINT unless ARM RUN.
  Settings: SLIDE, SLIDE DISTANCE, SLIDE FRICTION, SLIDE IMPACT, CROUCH
  SLIDES, JUMP CANCELS. Offline only.
- [x] 11 Slide impacts: by speed, angle and kind (Grunts/Jackals knocked
  down, Elites staggered, Hunters barely moved and the slide stops), a share
  of a melee up to 0.5x at 1x, never a kill.
- [x] 12-13 BULLET TIME (off by default; GAMEPLAY page, key on BUTTONS):
  default the turning stick pushed up (the audit's only free input), HOLD or
  TOGGLE, TIME SCALE 25-65%. Local games only (never co-op/multiplayer), not
  seated, in menus, cutscenes or paused; eased; a script's speed preserved.
  Head and hands keep full frame rate (ticks slowed, frames not).
- [~] 50-52 Climbing: a full collision feature list (a tree's dense top)
  was a refusal; now retried at half and a quarter radius; short rays from
  the hand find a trunk the sphere missed. Same safety (static scenery,
  climbable faces, moving scenery refused). Needs a tree on device.
- [x] 53-55 Wall jump: led by the level look, the wall run along (not the
  nearest face) is the one jumped from, at least 35% away from it, stick a
  fifth, momentum up to 1.5x; logged with vectors. Wall running unchanged.

## Fist combat and grabbing (35-49)

- [x] 36 Defaults change only for fresh or untouched values (migration
  flag `vr.test70_defaults_applied`).
- [x] 37 HIT ASSIST (30 cm): an in-reach punch at the acquired enemy lands
  without the 3.5 cm sweep meeting the collision bubble. Not a reach (only
  in striking range).
- [x] 38-40 FIST COMBAT and NPC GRAB bring GRAB ASSIST 15 cm (was 10); fresh
  default 15 cm; an untouched 10 cm moves once.
- [x] 41 Maximum GRAB ASSIST: the contact mapping refused hands more than
  22 cm from a joint, undoing large assists after detection; it allows the
  assist now (tested).
- [x] 42-43 LUNGE HOP (15 cm): a ground lunge begins with a small leap.
- [=] 44-49 Airborne lunge, difficulty scaling (melee durability 0.85x-1.5x,
  parry windows), block/parry feedback, target switching, body-point latch,
  light/heavy rules: present since Test65-67; unchanged (the owner: refine,
  do not redesign).
- [x] Menu: FIST COMBAT section (8) and FIST OPTIONS (HIT HIGHLIGHTS, DEFLECT
  SHOTS, FIST REQUIRED, AIM STEADY); every IMMERSION row stays listed there
  once and on its usual page (test_vr_immersion_menu).

## Upstream, network, menus (56-65, 67-69)

- [x] 56-65 TEST70-UPSTREAM-NETWORK.md: OpenCE build-206 current; network 29
  hosting, 11-29 joining covers every listed server; no alternate OpenCE
  network modes exist; GulchCE 42 deferred (protocol project);
  HALOFREAK95 fast-decals reviewed, not taken (needs on-device profiling).
- [~] 67-69 Menu pass: fist rows grouped, slide rows on
  LOCOMOTION, bullet time on GAMEPLAY; dependencies automatic (SLIDE ->
  sprint). A wider reorganisation was not attempted (risk to settings
  players know).

## Not done / pending

- Altheros model memory (above): needs a launch log.
- Every [~] item needs headset confirmation (TEST70-DEVICE-CHECKLIST.md).
