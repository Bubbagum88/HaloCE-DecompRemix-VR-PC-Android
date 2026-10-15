## Latest release: v1.0.37 (Test70), 2026-10-15

Published: `https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.37`.
The APKs retain their Test70 identity (`1.0.37-test70`, code 82); stable asset
names are used for launcher updates. See `docs/RELEASE-1.0.37.md`,
`docs/RELEASE-PROVENANCE-1.0.37.md`, and `docs/TEST70-DELIVERY-STATUS.md`.
Automated checks passed; device acceptance remains pending. Keep experimental
and WIP features labeled as such.

## Private candidate after it: Test71 (1.0.38-test71 / code83)

Every campaign mod installs from the launcher in one tap, as SPV1 does (the
owner: "i want all of the mods to work like that for future reference"):
Lumoria from halomaps.org (file ids 6503-6506; ModMap.extra replaces "fid
0"), Altheros from moddb.com through the launcher's WebView
(ModDownloadActivity: moddb refuses other clients) and unpacked on the device
(ArchiveExtractor, libarchive-android 1.1.7 / libarchive 3.8.8: its RAR5
extracts to the recipe's 13 SHA-256s off-device). Import (folder, .zip, now
.rar) stays as every mod's fallback. Manual reload: mods' guns by their own
model nodes and magazine (vr_reload_generic_profile.h; SPV1's names are all
"<protected>" at run time, so none of its guns had a profile); a second
magazine reloads itself (weapons.c holds back only magazine 0's triggers).
Altheros stays "Experimental — currently not working" (the owner).
Read docs/TEST71-CHECKLIST.md, TEST71-DEVICE-CHECKLIST.md and
TEST71-DELIVERY-STATUS.md. Not published; whether moddb accepts the WebView
hand-off needs a headset.

Release-preparation polish on Test69, 1.0.37-test70 / code82. Read
docs/TEST70-CHECKLIST.md (every owner item and its disposition),
TEST70-FIELD-GUIDE.md, TEST70-DEVICE-CHECKLIST.md, TEST70-CONTROLS-AUDIT.md,
TEST70-UPSTREAM-NETWORK.md and TEST70-DELIVERY-STATUS.md.
MCC: the "problem with the disc" error came from GulchCE's three MCC hooks in
cache_files_windows.c lost in Test67's merge (restored). Launcher: campaign
status labels (Altheros and MCC experimental), Project Lumoria (zip import,
recipe), What's New (assets/whats_new.txt, once per version). Remapping asks
(vr_button_remap.h, A = VR_MENU_CONFIRM_FUNCTION 104), MIRROR BUTTONS,
left-hand lettered guns mirrored back whole, locked holstering, shake
detection by strokes (vr_shake_detect.h: cooling while hot, needler shake
reload), rocket/canister ready when seated, Pistol/AR magazine fit
(vr.reload_grip_fit), SLIDE (vr_slide.c), BULLET TIME (vr_bullet_time.c,
R UP), HIT ASSIST, LUNGE HOP, GRAB ASSIST 15 cm and its mapping fixed,
tree climbing retries and rays, wall jumps by the look. OpenCE is still
build-206; HALOFREAK95's new fast-decals reviewed, not taken. Network 29
unchanged. Published; v1.0.31 remains preserved. No install/launch by the
publisher. Device acceptance pending. Altheros' next step (model memory, up to
56.5 MB a level) needs a log.
Edit scripts on Windows must write bytes (Python text mode turned LF files
into CRLF once in this session; fixed before committing).

## Active private Test69 (2026-10-14)

Packaged candidate: `D:\HaloQuest\builds\test69-20261014-v1.0.36-test69`.
Runtime `03c364ea`; both 145-suite build runs passed.
See the delivery record for hashes and pending device checks; this is not
headset acceptance.

Test68 + The Altheros Experience's scripts, 1.0.36-test69 / code81. Read
docs/TEST69-CHECKLIST.md, TEST69-FIELD-GUIDE.md, TEST69-DEVICE-CHECKLIST.md and
TEST69-DELIVERY-STATUS.md. Owner: Altheros "still gives a blue screen"; the
log showed b40 refused for OpenSauce script functions. A scan of all ten
levels found everything missing: pp_set_effect_instance_active/_fade,
pp_bloom_set_exposure (accepted, not drawn), object_data_get_real/_set_real
(a30's gravity lift, real) in custom_edition_opensauce.c (indices 0x7100-),
and Halo PC's rasterizer_fps (sets of a constant are no-ops,
custom_edition_scripts.c; no engine global added: checkpoint state). Tests
test_test69_opensauce, test_test69_scripts. Network 29 unchanged. Private
only: no push/publish/install/launch. Device acceptance pending.

## Active private Test68 (2026-10-14)

OpenCE Build 206 on Test67, 1.0.35-test68 / code80. Read docs/TEST68-CHECKLIST.md,
TEST68-FIELD-GUIDE.md, TEST68-DEVICE-CHECKLIST.md and TEST68-DELIVERY-STATUS.md.
Owner: "update everything to match the details of it [OpenCE] and build new apks".
Network 29 (hosts 29, joins 11..29): Custom Edition maps keep their names, the
game record's map version is the map's hash's; a client of a host before 29
finds the map by name and checks the header checksum
(custom_edition_map_version_is_checksum; test_test68_network29). Map sharing
restart and validation hardening, stb_vorbis floor fix. Everything of Test67
kept (VR, MCC maps solo, the fork's features, community extras on 87-92).
Built and packaged from c331ef2b: D:\HaloQuestuilds	est68-20261014-v1.0.35-test68
(143 suites passed before each flavor; audit and package checks passed).
Private only: no push/publish/install/launch. Device acceptance pending.

## Active private Test67 (2026-10-13)

Precision polish on Test66, 1.0.34-test67 / code79. Read docs/TEST67-CHECKLIST.md,
TEST67-EVIDENCE.md, TEST67-FIELD-GUIDE.md and TEST67-DEVICE-CHECKLIST.md.
Owner confirms Test66 Sniper grip, Warthog/Ghost/tank and improved ragdolls/parkour;
other device checks remain pending. Changes: stable authored reload grips (Sniper
preserved), 3x optional sprint range, skeletal grab contact, deliberate fist strokes,
melee difficulty and readable guard/parry, empty-hand reticle suppression, optional
campaign preparation and hash verification. Saved settings preserved. No voice
change; network 28 unchanged. Private only: no push/publish/install/launch. Delivery status is
in docs/TEST67-DELIVERY-STATUS.md. Public v1.0.31 remains unchanged.
Later Test67 additions: per-enemy threat memory, original Halo combat cues,
COMBAT MOVES physical dodge/arm/pummel openings and procedural poses, projectile
deflection with fists or a deliberately swung gun, and the evidence-backed
Altheros large-resource fix. Native collisions, fuse/attribution, NPC ownership
and existing online gates remain. See the complete guide/checklist; device
acceptance is still pending.
Test68 merged into Test67 (one candidate, still 1.0.34-test67 / code79):
GulchCE Halo 1 MCC maps solo only (online MCC deferred; MCC network 42 not
supported), launcher Steam Workshop (JavaSteam; token only), installed-map
manager and imports; OpenCE testing 52e33a39 hardening; every jcompto95-tech
(HALOFREAK95) fork branch, adapted (third person flat-only, Extra Effects,
overshield, corpse/decal limits, stencil shadows, projectile effects and blood,
weapons physics on Jolt, Armor menu, text chat, vote-ban), visuals off/classic by
default. Owner allowed the fork's community extras on new message kinds 87-92
(network.community_extras, launcher Server Browser switch); stock peers ignore
them. VR BUTTONS has ALL TO DEFAULT first. Suites: test_test67_fork,
test_test67_mcc_upstream (890 pass, 140 of them 32-bit under qemu-i386),
test_test67_upstream_harness.

> **Published:** v1.0.31 (Test64/code76) is now Latest. See `docs/PUBLIC-RELEASE-1.0.31-HANDOFF.md` for source/publication and updater verification. Historical holds below are superseded for this release.

> **Public promotion authorized 2026-10-12:** the owner requested Test64 as
> public **v1.0.31**, retaining the exact `1.0.31-test64`/code76 APKs.
> This supersedes the historical local-only publication holds below for this release.
> Read `docs/RELEASE-1.0.31.md` and `docs/RELEASE-PROVENANCE-1.0.31.md`.
> Publication is for user testing/log collection; it does not certify the device checklist.
> Runtime source remains `d1a61e06`; experimental systems remain WIP.

# Agent and contributor continuation

## Active private Test66 candidate (2026-10-13)

Private **1.0.33-test66 / Android code78**, branch `test39-interaction-completion`.
Resumed from `d34e42b1`; Test65 feedback and later owner additions are recorded in
`docs/TEST66-CHECKLIST.md`. Read that file, `docs/TEST66-OPENCE-PARITY.md`,
`docs/TEST66-FIELD-GUIDE.md` and `docs/TEST66-DEVICE-CHECKLIST.md` before continuing.
Includes applicable OpenCE Build 201 integrations, host-side Jolt dynamic ragdolls,
map sharing, custom campaign switching (SPV1 / Altheros / original), and the
vehicle, reload, fist, grab, wall-run, left-hand, grenade and weapon-pull refinements.
Network remains 28 hosting / 11-28 client targets; voice codec/audio paths preserved.
Public baseline is v1.0.31; older baseline claims below are historical.
Local-only completion: no push, tag, release, installation or launch.
Both APK builds and three complete 131-suite runs passed. Exact APK source is
`0b5c7e628060d977f7613f28433cca094a3f35d0`; delivery folder is
`D:\HaloQuest\builds\test66-20261013-v1.0.33-test66`. Signatures, versions,
source lineage and artifact hashes are recorded in `docs/TEST66-DELIVERY-STATUS.md`
and the package manifests. Device acceptance remains pending.
PC / Steam Frame remain deferred. Preserve user settings and known working paths.

## Historical public-baseline check: v1.0.18 (superseded by v1.0.31)

A live check on 2026-10-12 of
[GitHub releases/latest](https://github.com/moistman42069/HaloCE-Quest-VR/releases/latest)
resolved to [v1.0.18](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.18),
**OpenCE network24 / Android code48**. The public release points at commit
`3867cd0ed565e8da97f3e9c62c27e316e30a4b73`; the local annotated
`v1.0.18^{}` resolves to that same commit. The APK runtime source is
`2680beaa42d9b53098a21198200f79c76aa3b308`, as recorded in the 1.0.18
release provenance.

The older v1.0.19 "current public" claim below is superseded: that release
attempt was withdrawn/cancelled in the conversation and is not the current
latest release. No local v1.0.19 tag exists. Preserve its notes as history,
but do not use them as a live release pointer or instruction to check it out.
Continue private Test65 on its stated branch. Public v1.0.18 and all earlier
release assets remain unchanged; no publication is authorized.

## Previous private Test65 candidate (2026-10-13)

Private **1.0.32-test65 / Android code77**, branch `test39-interaction-completion`,
on Test64 = public 1.0.31: Arkham Shadow fist combat (it never acquired: the
tick's head view; lunge 6 m, combo meter and takedown, counters, ENEMY HEALTH
3X, knockdown ragdolls), the Warthog (no Banshee yoke on its wheel, GRIP
GUIDE, COCKPIT LOCK), HAND SWAP 10 cm, held vehicles never crush their holder,
held-NPC impacts safe for allies, thrown corpses kept, ACTIVE RAGDOLL, GRAB
RAGDOLL (on lift), world grab assist, WEAPON PULL. Dual wield not implemented
(design noted in the delivery status). Read `docs/TEST65-CHECKLIST.md`,
`TEST65-DELIVERY-STATUS.md`, `TEST65-DEVICE-CHECKLIST.md`; Test64's and
Test63's device checks are also still pending. No protocol or voice change.
Local commits only; no push/publish/install/launch.

Built and packaged: APK source `098a5a9182095b293f8243736da70f7478e072c1`,
delivery `D:\HaloQuest\builds\test65-20261013-v1.0.32-test65`; full suite,
both native builds, ABI lint and package verification passed.

## Previous private Test64 candidate (2026-10-12)

Private **1.0.31-test64 / Android code76**, branch `test39-interaction-completion`,
Test63 (APK source `e2849e9b`) plus one fix: opening VR SETTINGS crashed
(owner's 14:09 Test63 log, signal 11 in `vr_menu_setting_text`) because
Test63's settings index was also built for the category list (17 categories,
three screens) and read `vr_menu_pages[VR_MENU_PAGE_COUNT]`; `vr_menu_paged`
now builds the index for a category's own pages only. test_test31_vr_menu
has 17 categories (fails without the fix under AddressSanitizer). Read
`docs/TEST64-CHECKLIST.md`, `TEST64-DELIVERY-STATUS.md`,
`TEST64-DEVICE-CHECKLIST.md`; all of Test63's device checks are still
pending (`TEST63-DEVICE-CHECKLIST.md`). No protocol or voice change. Local
commits only; no push/publish/install/launch.

Built and packaged: APK source `d1a61e06d08b5ed044a941c447e8872661aea0fa`,
delivery `D:\HaloQuest\builds\test64-20261012-v1.0.31-test64`; full suite,
both native builds and package verification passed.

## Previous private Test63 candidate (2026-10-12)

Private **1.0.30-test63 / Android code75**, branch `test39-interaction-completion`,
continuing Test62 (APK source `ed60571f`, kept whole). From the owner's
fresh-install Test62 session (12:06 log and video, reviewed completely):
BUTTON SPRINT owns the left stick's click and a reticle whose toggle has no
button is shown (`vr_reload_settings`; the Buttons menu skips L STICK under
sprint); X with an action on offer never drops the magazine
(`player->action_result`); chest grenades sit in a torso frame
(`vr_torso_place`, follows past 35 degrees, holds while looking down), use the
game's frag/plasma projectile models (`vr_extra_models_render`, world model
pass) and are taken at the drawn palm within 12 cm with a hover tick; the
fist assist acquires (FIST REACH 1-3 m, 2.5 default; 45-degree gaze cone;
hooks count; step up to 5 m/s; target slowed x.35, not frozen; a grab or
climb ends it; miss diagnostics); world contact tests the nearest bounds
first and skips objects over 4 units (b30's purple c_storage crate was
starved by trees and the crashed Pelican); the Warthog's own model wheel is
drawn at the virtual wheel and turned (`vr_vehicle_controls_matrices`), the
Ghost/Scorpion/Banshee controls are redesigned shaded parts, and the
`vr.handle_*` rows show a live blue calibration preview. New ONE-HAND
HEAVIES (`vr.npc_one_hand_heavy`, off, requires NPC GRAB). Owner defaults:
WALL SPEED 1.5X, WALL LEAP 1.5X, THROW POWER 1.5X (CLIMB LAUNCH 1X, WALL TIME
2 S unchanged). A category of 3+ screens opens an index of its sections
(`VR_MENU_INDEX_FROM`). No protocol or voice change.

Full suite (127 suites), both native builds, ABI lint and package
verification passed. APK source is `e2849e9b4effc9b1dab195bda0217e3aeabaf30e`;
delivery is `D:\HaloQuest\builds\test63-20261012-v1.0.30-test63`.

Read `docs/TEST63-CHECKLIST.md`, `docs/TEST63-FIELD-GUIDE.md`,
`docs/TEST63-DEVICE-CHECKLIST.md`, `docs/TEST63-DELIVERY-STATUS.md`.
Saved settings stay; new defaults reach fresh installs. Automated checks are
not device evidence: device acceptance is pending for all of Test63.
Local commits only; no push/publish/install/launch. PC/Steam Frame deferred.
Every local commit message ends with the requested Claude co-author trailer.

## Previous private Test62 candidate (2026-10-12)

Private **1.0.29-test62 / Android code74**, branch `test39-interaction-completion`.
Original four requests: settled-eye immersive control anchors (3 s cap),
all-vehicle CTRL offsets; 5 cm default body grab assist; stationary first-hand
heavy restraint/two-hand lift; native impact fallback/configured floor-slam
threshold, 60 m death range and guarded parent-relative solver.

Expanded scope: adjusted-palm manual reload and event-haptic priority; parkour
defaults (14 cm climb contact, 2 s wallrun); optional experimental enemy-only
FIST COMBAT (gaze/punch approach, combo restraint, brief stun/rear strike,
highlights and native hurt feedback); adjustable chest PHYS GRENADES with
native counts/projectiles; shared AIM STEADY and fresh final-wrist scope
origin, including zero-offset frames. Slams/physical melee use a native
contact-damage wrapper: real shield depletion and body-hit art only after
body vitality loss, with a loaded material-response fallback and diagnostic
vitality logs. Both flavor regression/build gates passed; final package verification is recorded in the delivery record.

HOST VR ACTIONS is an opt-in co-op Server Setup permission for the host's new
fist/grenade actions, requiring existing VR INTERACTIONS/all-peer handshake.
PvP and guests retain native actions; manual reload/custom-rig/debris local
restrictions remain. Existing NPC pose sync supports four remote machines,
not unlimited peers. Protocol and voice implementations are unchanged.
Euphoria-style active control/better solver replacement was assessed and not
added; keep the tested solver and <=1 s living-NPC recovery.

Both native builds, regression gates and final package verification passed. APK source is `ed60571ff85eaacbfe178cc98872d603bad32085`; delivery is `D:\HaloQuest\builds\test62-20261012-v1.0.29-test62`. Device acceptance remains pending. Read
`docs/TEST62-CHECKLIST.md`, `docs/TEST62-FIELD-GUIDE.md`,
`docs/TEST62-DEVICE-CHECKLIST.md`, `docs/TEST62-DELIVERY-STATUS.md`.
Saved settings stay; new defaults do not overwrite a user's stored choices.
Do not treat historical guide claims as fresh runtime evidence.
Local commits only; no push/publish/install/launch. PC/Steam Frame deferred.
Every local commit message ends with the requested Claude co-author trailer.


## Previous private Test61 candidate (2026-10-12)

Continue on `test39-interaction-completion`; private `1.0.28-test61`, Android
code73 (docs/TEST61-DELIVERY-STATUS.md; docs/TEST61-CHECKLIST.md,
TEST61-DEVICE-CHECKLIST.md). Immersive vehicle controls are held under the
hands: the seat's eyes stay still while they are up and the controls sit in
the hands' level frame (vr_render.c steady anchor, vr_vehicle_handles.h);
IMMERSIVE VEHICLE requires VIEW FIRST PERSON (value requirements in
vr_menu.c). Impacts use the engine's unarmed melee blow (the Chief has no
unit melee damage: every impact was dropped before); 24 NPC rig slots with a
corpse's slot reclaimed for a new death; dead Elites/Hunters one-handed;
NPC GRAB/WORLD GRAB bring CUSTOM NPC RIGS/CUSTOM SCENERY; a button held from
a menu is no reload. Owner: settings a feature plays best with come on with
it; regress nothing.

## Previous private Test60 candidate (2026-10-12)

Continue on `test39-interaction-completion`; private `1.0.27-test60`, Android
code72 (docs/TEST60-DELIVERY-STATUS.md; docs/TEST60-CHECKLIST.md,
TEST60-DEVICE-CHECKLIST.md). Impacts for every NPC: a ragdoll joint's sphere
contact is probed into the face it met, fast joints are tested against
bodies and vehicles (the dead-biped sweep passes through them) and stop at
them, and a blow carries no team so allies take it in full
(vr_articulated_native.c, vr_interaction_impact.c). DEATH RAGDOLLS turns on
NPC GRAB, NPC RESCUE and IMPACT DAMAGE; grabs turn on IMPACT DAMAGE; vehicle
refinements turn on IMMERSIVE VEHICLE (soft rows in vr_menu_dependency_table;
a feature turned on automatically pulls its own soft requirements). Owner:
settings a feature plays best with come on with it, no redundant toggles;
regress nothing.

## Previous private Test59 candidate (2026-10-12)

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

## Superseded/withdrawn release attempt: v1.0.19 (2026-10-10)

Historical text follows. Its former publication/tag assertions and next-step
instructions are superseded by the verified v1.0.18 pointer at the top; this
section is retained to explain Test51-53's reported failures and fixes.

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
