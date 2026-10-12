# Agent and contributor continuation

## Active private Test59 candidate (2026-10-12)

Continue on `test39-interaction-completion`; private `1.0.26-test59`, Android
code71 (docs/TEST59-DELIVERY-STATUS.md; docs/TEST59-CHECKLIST.md,
TEST59-DEVICE-CHECKLIST.md). Hosts OpenCE network 28 (Build 201), joins
11..28; the launcher selector lists every network (27 too) and defaults to
All compatible (`network.protocol_version` 0). Network 27's map-sharing
requests are answered "not shared" (`map_share_handle_message`,
network_distributed.c); 28's rules (hs.c BSP, game_engine.c lights,
units.c / network_objects.c second weapon) are ported. In vehicles a
driver's weapon is stowed, so the stowed weapon lends its first-person rig
(real hands) while the immersive controls steer; COMFORT REACH and TANK
DRIVE are VEHICLES rows. Manual reload: the gun's own magazine reseats
(`VR_MR_RESEAT`/`VR_MR_RECOVER`, ammo unchanged); the free hand uses the
drawn camera (`vr_render_drawn_camera`). DEATH FORCE (IMMERSION > RAGDOLLS, STRONG)
throws death ragdolls along the burst / away from blasts. NPC recovery stays
within 1 s. Owner: toggles for optional behaviour; regress nothing.

## Previous private Test58 candidate (2026-10-11)

Continue on `test39-interaction-completion`; private `1.0.25-test58`, Android
code70 (docs/TEST58-DELIVERY-STATUS.md; docs/TEST58-CHECKLIST.md,
TEST58-DEVICE-CHECKLIST.md). Test57's immersive Warthog wheel and Scorpion
stick were out of reach (owner's log: misses of ~540 m and ~2 m):
`object_marker.node_matrix` is a marker's offset from its node, never a world
place; use `nodes[marker.node_index]` or `marker.matrix`. Controls are kept in
the vehicle's frame, placed on the drawn vehicle each frame, the stick/bar in
front of the chest, anything out of reach falls back there;
tools/test_test57b_vehicle_anchor.py proves it at many places and fails on the
old line. The mounted reticle follows the head between ticks with the
immersive controls. TANK HATCH is an off-by-default option (the owner likes
the tank view). Owner: toggles for optional behaviour; regress nothing.

## Previous private Test57 candidate (2026-10-11)

Continue on `test39-interaction-completion`; private `1.0.24-test57`, Android
code69 (docs/TEST57-DELIVERY-STATUS.md). A final polish pass the owner calls
release-candidate quality: read docs/TEST57-CHECKLIST.md and
docs/TEST57-DEVICE-CHECKLIST.md. Immersive vehicles (only with IMMERSIVE
VEHICLE on) have one profile per vehicle in `vr_vehicle_handles.h`
(`vr_wheel_names`, `vr_wheel_profiles`): the Warthog a drawn virtual wheel
(the model's rim never took a hand in the owner's drive; hidden, the grab sits
on the model's wheel), the Ghost its handlebar (owner-approved), the Scorpion
and Wraith one drive stick, the Banshee a flight bar that rolls or slides.
CONTROL GLOW, STEER HAPTICS and BANSH SLIDE are VEHICLES rows. The assault
rifle's "frame safety button" is as authored (stock animations checked).
Ragdolls and holster calibration were reviewed and left alone. The owner asks
for toggles for optional behaviour, and regress nothing.

## Previous private Test56 candidate (2026-10-11)

Continue on `test39-interaction-completion`; private `1.0.23-test56`, Android
code68 (docs/TEST56-DELIVERY-STATUS.md). Read docs/TEST56-CHECKLIST.md
(evidence, each request with implemented / automated / device outcome) and
docs/TEST56-DEVICE-CHECKLIST.md. Key findings: ragdolls never rested because
joint limits authored relative to the parent bone (limp-noodle flags 0x1
ball, 0x2 hinge, 0x4 rigid) were compared in world space; the parent-relative
solver is tested offline on the 12 stock skeletons
(tools/test_test56_ragdoll.py, fixture tools/fixtures/ragdoll-skeletons.h).
Immersive vehicles steered inverted and stuttered (controls on the newest
tick while the vehicle is drawn a tick behind). NPC recovery never exceeds
1 s (owner rule). Immersive-vehicle behaviour applies only with IMMERSIVE
VEHICLE on. OpenCE Build189 (map sharing) moves to network 27 and is not
taken; Build190's host-only lobby countdown fix is. Settings that only serve
another feature turn on with it (`vr_menu_dependencies`), never as extra
toggles.

## Previous private Test55 candidate (2026-10-11)

Continue on `test39-interaction-completion`; private `1.0.22-test55`, Android
code67 (docs/TEST55-DELIVERY-STATUS.md). Read docs/TEST55-CHECKLIST.md
(evidence, each request with implemented / automated / device outcome) and
docs/TEST55-DEVICE-CHECKLIST.md. Key findings: the stock campaign script-names
most placed objects (59 of 61 Shades, most vehicles, bodies, and on some
levels nearly all weapons/equipment), so interactions now allow named objects
and exclude only cutscene (movie star) control; the Test54 frame-rate drop in
long fights is decals (OpenCE Build 188's decal batching adopted; Builds
185-188 made no network change). Zoom moves to the right stick click while
physical melee is in use. Use the stock Xbox data for tag/scenario research:
the USA XISOs in D:\Downloads (maps extracted with
tools/steam_frame/extract_maps.py), never the SPV1 mod maps (Custom Edition,
not supported) or D:\Games\Halo (Halo PC, cache version 7).

## Previous private Test54 candidate (2026-10-11)

Continue on `test39-interaction-completion`; private `1.0.21-test54`, Android
code66, built from 938a0448 (docs/TEST54-DELIVERY-STATUS.md). Read
docs/TEST54-CHECKLIST.md (owner's 2026-10-11 logs/videos, the 35-item brief
and additions, each with implemented / automated / device outcome),
docs/TEST54-NETWORK.md (what is and is not shared online) and
docs/TEST54-DEVICE-CHECKLIST.md.

Owner's Test53 report (2026-10-11): voice chat works online (log: frames
encoded and decoded); wall run and wall jump work; many interaction systems
finally run. **Do not regress them; do not touch voice code without cause.**
Test54 refines manual reload (reload button drops the magazine, body pouches
via `vr_reload_pouch_zone`, insert on contact, charge only when empty), NPC
grabs (bone capsules of the live pose), throws/holds, thrown-body root
follow, DEATH RAGDOLLS, climbing on slopes/overhangs/ledges, open hands never
strike (FIST REQUIRED is a reference-counted soft dependency in
`vr_menu_dependencies` / `vr.immersion_auto`), gun parts steady through the
first-person walking overlays, and the IMMERSION+ page. None of Test54 is
device-confirmed yet.

## Previous private Test53 candidate (2026-10-11)

Continue on `test39-interaction-completion`; private `1.0.20-test53`, Android
code65 (Test52/code64 was committed but never built or delivered; Test53
supersedes it). Read docs/TEST53-CHECKLIST.md (every change and requested
item with implemented / automated / device outcome), docs/TEST53-DELIVERY-STATUS.md,
docs/TEST52-CRASH-ANALYSIS.md and docs/TEST53-DEVICE-CHECKLIST.md.

Voice chat: v1.0.19/Test51 closed on Quest as soon as a player spoke. Cause
(re-proved in Test53): the arm64_32→ELF assembly converter corrupted Opus's
`cache_bits50`. Fixed in Test52/53 and hardened; the owner reported voice
working on Test53 (2026-10-11).

Test53 also fixes why the interaction features never worked: hand-contact
grabs used a zero-length pill sweep that cannot report a touch
(`collision_model_touch_sphere` now), and parkour/manual reload asked for the
head pose from game ticks, which `vr_head_view` refused outside the stereo
pass. It adds the IMMERSION settings page, hosts on OpenCE network 26
(Build184; clients 11–26, All compatible by default; dual-version internet
signalling, no WebRTC) and selected Build177–184 fixes.

Guest-build rules: every guest unit rejects implicit declarations;
`tools/android_guest_abi_lint.py` (run by build-quest.sh after each flavor)
fails on any cross-unit signature mismatch; the post-build image check needs
exact Opus tables. Build in WSL with clang 18 like v1.0.18 (LLVM 22 cannot
run under WSL1); same debug key 53d416f7…2aa4. Run Python that writes repo
files inside WSL (Windows Python rewrites LF as CRLF). Device acceptance of
everything above is pending.

## Current public release: v1.0.19 (2026-10-10)

The published v1.0.19 source/tag is based on the Test51 runtime, merged with
the current main landing-page/logo commit. The owner confirmed Quest server
joins no longer crash; the owner then reported that **speaking in voice chat
crashes v1.0.19** (fixed in source in Test52/Test53, unconfirmed on device).
Read docs/RELEASE-1.0.19.md, docs/RELEASE-PROVENANCE-1.0.19.md, and
docs/CURRENT-STATE.md before changing code.

Keep these status limits explicit until the owner reports device results:
parkour, wall grabs, ragdolls/body retention, NPC/enemy/ally grabs and manual
reload had real defects fixed in Test53 but are unconfirmed in the headset.
Settings that appear in the menu are not proof of a working feature.
Preserve the owner-confirmed join, reticle, sprint, weapon
release/drop/holster, haptics, Android, co-op, network, launcher, Safe
Geometry and calibration behavior. PC/Steam Frame remains deferred.

## Superseded private Test47 candidate (2026-10-09)

Continue on `test39-interaction-completion`; target private `1.0.28-test47`,
Android code58. Preserve Test46/Test45 and prior APK/source artifacts, plus
public v1.0.18. Read `docs/TEST47-DELIVERY-STATUS.md`,
`docs/TEST47-REQUIREMENT-DISPOSITION.md`, `docs/TEST47-PLAYER-NOTES.md`,
`docs/TEST47-DEVICE-CHECKLIST.md`, `docs/MANUAL-RELOAD.md`, and
`docs/VR-INTERACTION-REQUIREMENTS.md`.

The first fix preserves authored upper-arm/forearm lengths and clamps only the
reachable wrist target. Manual reload reads the configured VR USE/RELOAD action
directly as well as the engine bit; part contact and a fresh Grip/Trigger remain
required, while right-stick click remains melee. Solo multiplayer-map loads
clear a stale campaign continuation slot and select an in-BSP native/fallback
start with the multiplayer biped. Network matches and campaign spawns stay on
their existing paths.

Run focused interaction fixtures, the full regression suite and both Quest/VR
and flat Android builds, then package both APKs and matching build/source ZIPs.
Do not publish, install or launch the game. Preserve network, VR, mobile, saves,
co-op, Safe Geometry, launcher and calibration behavior. PC/Steam Frame remains
deferred. Host/source tests do not prove headset behavior; device acceptance is
pending.

## Superseded private Test42 candidate (2026-10-09)

Test42 was `1.0.23-test42` / Android code53. Its APKs and delivery records are
preserved. Read `docs/TEST42-DELIVERY-STATUS.md` and
`docs/TEST42-REQUIREMENT-DISPOSITION.md` for its cumulative scope and limits.

## Superseded private Test40 candidate (2026-10-08)

Test40's pair is preserved at
`D:\HaloQuest\builds\test40-20261008-v1.0.21-test40-delivery`; see its
delivery/status/disposition/checklist docs for the exact hashes and bounds.


## Historical public release: v1.0.18 (2026-10-08)

The owner authorized publication of Halo CE Quest VR + Android 1.0.18 as
Latest. It is based on Test37, OpenCE Build157/network24, Android code48.
Read `docs/RELEASE-1.0.18.md` for the complete user-facing feature, controls
and compatibility record and `docs/RELEASE-PROVENANCE-1.0.18.md` for exact
asset hashes and checks. The launcher offers client targets 11–24 or All
compatible; hosting stays network24. Older client targets are limited to
original Xbox-map PvP; co-op/Custom Edition require host23/24. Preserve older
releases and the existing GitHub About description.

The original Test37 private-candidate record below is historical; it records
the state before the owner authorized publication. Device/revision limitations
remain visible in the release notes. Continue from the published release and
preserve its package identity and signing certificate.

## Historical private candidate: Test37 (2026-10-08)

Continue on local branch `test37-network-browser`. Read `docs/TEST37-DELIVERY.md` for final APK hashes and checks. Await owner device results; no public release is authorized.

The private candidate is **1.0.18-test37 / code47 / OpenCE Build 157**.
Local hosting and signed advertisements remain **network24**. The launcher
now selects the client's startup join target: **24** by default, an exact
version **11 through 24**, or **All compatible networks** (11-24). This choice
controls native discovery and admission as well as the launcher list; it is
not merely a directory filter. Versions 11-22 are limited to original Xbox-map
PvP. Campaign co-op and Custom Edition require host version 23 or 24.

The target is shared across PvP, co-op and imported data sets. Close the game,
choose the target in the launcher, then launch again. It cannot change during
a running game. Hosting never impersonates an older version. Catalog-reported
players and servers are grouped by version and sorted busiest first; unsupported
versions remain visible but unavailable. MQTT brokers are discovery mirrors,
not additional protocol implementations. One public HTTPS catalog is verified;
up to four compatible custom catalogs can be configured.

Public v1.0.16/code45/network23 and the Test36 artifacts remained unchanged
while this candidate was private. Source checks and compilation do not
establish every historical server, map revision or co-op combination.
Read [TEST37-PROGRESS.md](docs/TEST37-PROGRESS.md),
[TEST37-UPSTREAM-INTEGRATION.md](docs/TEST37-UPSTREAM-INTEGRATION.md) and
[TEST37-PLAYER-NOTES.md](docs/TEST37-PLAYER-NOTES.md) record candidate-era
validation. This historical hold was superseded by the owner's later release
authorization.

Read `docs/ACTIVE-WORK-CHECKPOINT.md` and `docs/CURRENT-STATE.md` first. Preserve the accepted VR/mobile baselines and leave uncertain runtime reports unchanged until exact evidence is available.

## Historical public release: v1.0.16 (2026-10-07)

Read `docs/ACTIVE-WORK-CHECKPOINT.md`, `docs/CURRENT-STATE.md`,
`docs/RELEASE-1.0.16.md`, `docs/RELEASE-PROVENANCE-1.0.16.md`,
`docs/TEST35-PROGRESS.md`, and `docs/TEST35-UPSTREAM-INTEGRATION.md`.
At that historical checkpoint, the public latest release was Android/Quest 1.0.16/code45, OpenCE Build 148,
network23. Build148 adds particle-radius tag corrections, a point-physics
guard, and clearer native halt-screen details; it does not change the network
protocol. Preserve Test34 map/cache/BSP validation, co-op/camera safeguards,
cursor selection, scope diagnostics/alignment, and the owner-accepted Test31b
VR settings and Test31c Android touch/gameplay. The exact v1.0.16 APK pair has
no recorded device session, so distinguish release publication from device
acceptance. Keep older releases and the repository About description intact.

Test35 below is the previous released implementation record. Older
Test31/Test32 "Active" headings are retained historical notes and are
superseded; do not resume their branches or targets. The separate interaction backlog remains in
`docs/VR-INTERACTION-REQUIREMENTS.md`.

## Historical touch/glass correction and accepted VR preference (2026-10-07)

The owner reports **Test31b Quest VR works great** and explicitly prefers its
new VR settings. Preserve that implementation and the exact Quest code40 APK.
Android Test31b's rectangular menu control strip is rejected: keep the original
circular layout/positions across menu and gameplay, retain direct menu taps,
and have optional drag-anywhere look hide only the LOOK joystick. MOVE and
action controls remain. Follow `docs/TEST31C-PROGRESS.md` on `test31c-flat-ui`.
Latest owner addition: fix VR's non-working Warthog HOG GLASS option before
packaging BOTH builds. Target 1.0.13/code41 for both editions. The accepted
Quest code40 APK stays preserved as the comparison baseline; retain its new
VR settings and change only the broken glass path. Do not publish. The later
interaction scope remains queued. This supersedes the Android-only plan.

## Historical repair: Test31 rejected (2026-10-07)

Read `docs/TEST31B-PROGRESS.md` first. The owner reports Quest startup crashes
and unusable Android touch input in Test31. Branch `test31b-startup-touch`
repairs those regressions and adds optional in-game touch-anywhere look.
Target 1.0.13/code40. The private pair is built from `3399023ae8b7d0ec57e8c42c68c40ab6c33346af`; read
`docs/TEST31B-DELIVERY.md` for checks/hashes and await owner device results. Do not use Test31's prior passing host checks as device
acceptance. Prepare a corrected private pair; keep larger interaction work queued.

## Historical Test31 delivery / retained scope (superseded by repair above)

Read `docs/ACTIVE-WORK-CHECKPOINT.md` and `docs/TEST31-PROGRESS.md` first.
The rejected branch was `test31-network-menus-vehicles`; its target was
1.0.13/code39. That private pair was built and signed from `585a5643`, with
47 regression suites passing; see `docs/TEST31-DELIVERY.md`. Await owner device
acceptance of the corrected pair before the next interaction phase. **Retained owner override:** finish and validate the full OpenCE
menus, turret fixes, Warthog window setting and upstream/network upgrade, then
package the Quest and flat APKs for testing BEFORE the manual reload/hand
contact and world/NPC interaction phase. Those later requirements remain queued
and must not be marked complete. Track all requirements in
`docs/VR-INTERACTION-REQUIREMENTS.md`. The owner now requires ALL OpenCE in-game
menu functionality, superseding the narrower browser/setup approval; see
`docs/TEST31-MENU-PLAN.md`. No publication, push, tag,
installation or game launch is authorized. Public release pointers below are
historical/public state, not permission to release this work.

## Historical GitHub release: v1.0.12 (test30 APKs)

**Published release: test30 (version 1.0.12 / code 38),** branch `test30-profiles-coopname`, on v1.0.11. Quest A/X/Y now match the button labels in VR menus (X deletes a profile; B backs out once), with gameplay mappings unchanged. Campaign hosting accepts an optional remembered server name. The network remains OpenCE Build 144 / version 21. The exact APK pair has no recorded device session at publication. See `docs/RELEASE-1.0.12.md`, `docs/RELEASE-PROVENANCE-1.0.12.md`, `docs/TEST30-PROGRESS.md` and `docs/TEST30-DELIVERY.md`.

**Published release: test29 (version 1.0.11 / code 37).** OpenCE Build 144/network 21, HUD tap and wrist-HUD refinements, two-hand movement alignment, glasses FOV and higher resolution options. The exact v1.0.11 APK pair had no owner device-session validation at publication; the owner-confirmed co-op result applies to v1.0.10/network 20. Preserve all prior releases and do not alter the repository About description. See `docs/RELEASE-1.0.11.md`, `docs/RELEASE-PROVENANCE-1.0.11.md`, `docs/TEST29-PROGRESS.md`, and `docs/OPENCE-COOP-COMPATIBILITY.md`.

**Published release: test28 (version 1.0.10 / code 36).** The user supplied `D:\HaloQuest\builds\test28-20261006-v1.0.10` and reports campaign co-op works well in testing. Test28 uses OpenCE Build 138/network 20, fixes the join-in-progress camera halt, offers co-op lobby sizes up to 128, and adds optional phone gyro aiming. High-count performance and gyro behavior were not reported as tested. See `docs/RELEASE-1.0.10.md`, `docs/RELEASE-PROVENANCE-1.0.10.md`, `docs/TEST28-PROGRESS.md` and `docs/OPENCE-COOP-COMPATIBILITY.md`. The release is Latest at https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.10. Preserve all prior releases and do not alter the repository About description.

**Published from candidate:** test29, version 1.0.11 / code 37, branch `test29-opence-144`, built on v1.0.10:
- OpenCE build 144 netcode (network 21). Current OpenCE co-op and multiplayer games are on 21, which 1.0.10 cannot join.
- The HUD head tap must now be held by the temple for a moment, so a hand passing by no longer hides the HUD.
- New HUD rows: HUD Shown/Hidden and Head Tap.
- The wrist HUD sits on the wrist and can be moved and resized.
- MOVE WITH a hand follows the gun while both hands hold it.
- [Willem Horak's PR #1](https://github.com/moistman42069/HaloCE-Quest-VR/pull/1) contributes the glasses FOV option and resolution steps up to 200%; defaults are as in 1.0.10.

See [TEST29-PROGRESS.md](docs/TEST29-PROGRESS.md) and [TEST29-DELIVERY.md](docs/TEST29-DELIVERY.md).

Test27 (version 1.0.9 / code 35) integrated OpenCE build 138's netcode (network 20) and co-op; project CE01/CE02 and network 9–11 are retired. Test26 (1.0.8 / code 34) and earlier co-op reports are historical. v1.0.6 (test24b, code 32) is the preceding public release.

**Published latest build: v1.0.3 (test21b runtime, internal 1.0.2 / code 27; test21 was code 26), branch `test21-hands-body`; see `docs/TEST21B-PROGRESS.md`, `docs/TEST21B-DELIVERY.md` and `docs/TEST21-PROGRESS.md`. It still awaits headset tests.** **Current active handoff (2026-10-04):** read `docs/ACTIVE-WORK-CHECKPOINT.md` and `docs/REPORT-2026-10-04-HANDS-IK-REGRESSION.md` before starting new work. The owner reports cut-off/floating hands returning and arm IK not following body turns. Do not presume v1.0.2 caused this: supplied logs include test20d and test20e runtime banners, while only the latter's launcher log explicitly confirms installed code 25; verify installed APK hash/version/source. Keep all raw logs/video private. The release is published; preserve the regression investigation and do not claim test21b headset acceptance until the owner reports results.

## Historical 1.0.1 and 1.0 notes

The withdrawn 1.0.1 record is `docs/RELEASE-PROVENANCE-1.0.1.md`. The 1.0/code-19 statements below remain historical context; the release status above supersedes them.



Canonical repository: `moistman42069/HaloCE-Quest-VR`, default branch `main`.
Read docs/CURRENT-STATE.md, docs/RELEASE-PROVENANCE-1.0.0.md, CONTRIBUTING.md,
and relevant player/architecture/protocol documents before changes.

Current public baseline: **release 1.0**, tag `v1.0.0`. The owner explicitly
re-authorized publication using the exact delivered test18 APKs. This supersedes
the test18 publication hold. Both APKs retain **1.0-test18 / code 19** internally;
only release filenames change. Do not rebuild, re-sign or replace them. Public
test14 stays unchanged. See RELEASE-PROVENANCE-1.0.0.md for hashes/build source.
Publication authorization is not a newly reported headset/campaign playthrough.
Future APK updates must use code >19 and need separate publication approval.

Preserve accepted VR animation handoff, Legs + Arms, room-scale legs, fingers,
contact/grip, online native melee, Safe VR geometry and Normal flat geometry.
Keep the flat touch/controller, co-op/NPC/avatar, logging, browser and managed
set implementations. Co-op is two-player for concrete lifecycle/recovery reasons;
128 PvP slots do not establish 128-player campaign or Quest hosting performance.
Do not invent disc-revision labels, verified content matching, directories or
headset acceptance. Record code, automated checks and device evidence separately.

Keep all new local work/builds on D: on the maintainer's Windows machine. Other
systems use a writable clone. Check status and read continuation docs first.
Build VR/flat serially; native staging is shared. Preserve each APK before a
flavor switch. No game install/launch or unrelated upstream push without a
corresponding instruction. Use GitHub noreply authors; never publish private
history, personal paths/emails, keys, game assets, raw logs/media or invitations.
Required third-party license notices remain intact.

Every future release must have self-contained notes in the nine-section order
in docs/RELEASE-TEMPLATE.md, installation and APK download links first. Upload
only the two APKs plus updater compatibility metadata unless another asset has
a concrete purpose. Preserve existing releases. Future version names, increasing Android codes, stable tags, APK names and
UpdatePolicy must agree. The exact-byte test18-to-1.0 promotion is a documented
owner-directed exception, including the same-code updater message.
Older test updaters require one manual install of 1.0; do not disguise that
limitation with fake compatibility metadata or duplicate legacy releases.
