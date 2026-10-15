## Latest release: v1.0.37 (Test70), 2026-10-15

Published: `https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.37`.
The APKs retain their Test70 identity (`1.0.37-test70`, code 82); stable asset
names are used for launcher updates. See `docs/RELEASE-1.0.37.md`,
`docs/RELEASE-PROVENANCE-1.0.37.md`, and `docs/TEST70-DELIVERY-STATUS.md`.
Automated checks passed; device acceptance remains pending. Keep experimental
and WIP features labeled as such.

## Owner direction for the next release

The project is expanding beyond Quest/Android: the owner plans PCVR, flat PC,
Steam Frame, and Pico adaptations. For the next release, revisit the project and
repository title/description, README/About wording, platform support matrix,
build/install instructions, controls, compatibility notes, credits, and release
assets so they accurately cover the platforms actually supported then. Do not
rename the current v1.0.37 release or claim a platform is supported before its
build and validation are ready.

## Private candidate after it: Test71 (1.0.38-test71 / code83)

Every campaign mod installs from the launcher in one tap, as SPV1 does (the
owner: "i want all of the mods to work like that for future reference"):
Lumoria from halomaps.org (file ids 6503-6506; ModMap.extra replaces "fid
0"), Altheros from moddb.com through the launcher's WebView
(ModDownloadActivity: moddb refuses other clients) and unpacked on the device
(ArchiveExtractor, libarchive-android 1.1.6 / libarchive 3.8.1: its RAR5
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

# Current development state

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


## Previous private candidate: Test61 (2026-10-12)

**1.0.28-test61 / Android code73**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). The immersive vehicle
controls stay under the hands (steady seat, the hands' level frame, no jump);
IMMERSIVE VEHICLE turns on FIRST PERSON; impacts hurt (the unarmed blow);
24 rig slots; dead Elites and Hunters lift with one hand; more settings come
on together; a button held from a menu is no reload. Item outcomes:
[TEST61-CHECKLIST.md](TEST61-CHECKLIST.md); APKs and hashes:
[TEST61-DELIVERY-STATUS.md](TEST61-DELIVERY-STATUS.md). Device acceptance
pending.

## Previous private candidate: Test60 (2026-10-12)

**1.0.27-test60 / Android code72**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). Impact damage works
on every NPC: slams onto floors and walls count, thrown and slammed bodies
strike other bodies and vehicles, and allies take the blow in full; DEATH
RAGDOLLS turns on NPC GRAB, NPC RESCUE and IMPACT DAMAGE, and the other
features turn on what they play best with. Item outcomes:
[TEST60-CHECKLIST.md](TEST60-CHECKLIST.md); APKs and hashes:
[TEST60-DELIVERY-STATUS.md](TEST60-DELIVERY-STATUS.md). Device acceptance
pending.

## Previous private candidate: Test59 (2026-10-12)

**1.0.26-test59 / Android code71**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). Real first-person
hands in vehicles, controls placed from the eyes, COMFORT REACH and TANK
DRIVE; OpenCE Build 201 with network 28 hosting and 11-28 joining (All
compatible by default, 27 selectable); the gun's own magazine goes back in
and reload is steady while walking; DEATH FORCE ragdoll throws. Item
outcomes: [TEST59-CHECKLIST.md](TEST59-CHECKLIST.md); APKs and hashes:
[TEST59-DELIVERY-STATUS.md](TEST59-DELIVERY-STATUS.md). Device acceptance
pending.

## Previous private candidate: Test58 (2026-10-11)

**1.0.25-test58 / Android code70**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). Fixes Test57's
immersive vehicle controls, which were placed out of reach (the Warthog's
wheel at the map's origin from a marker's local offset; the Scorpion's stick
inside the hull), steadies the mounted reticle with the immersive controls,
and adds the off-by-default TANK HATCH view. Item outcomes:
[TEST58-CHECKLIST.md](TEST58-CHECKLIST.md); APKs and hashes:
[TEST58-DELIVERY-STATUS.md](TEST58-DELIVERY-STATUS.md). Device acceptance
pending.

## Previous private candidate: Test57 (2026-10-11)

**1.0.24-test57 / Android code69**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). A final polish pass on
Test56 from the owner's Test56 session: every drivable vehicle its own
immersive controls (Warthog virtual wheel, Ghost handlebar, Scorpion/Wraith
drive stick, Banshee flight bar), a centre tick, a within-reach highlight,
grab-miss logging and CONTROL GLOW / STEER HAPTICS / BANSH SLIDE rows; the
assault rifle's safety button verified as authored; ragdolls and holster
calibration reviewed and unchanged. Item outcomes:
[TEST57-CHECKLIST.md](TEST57-CHECKLIST.md); APKs and hashes:
[TEST57-DELIVERY-STATUS.md](TEST57-DELIVERY-STATUS.md). Device acceptance
pending.

## Previous private candidate: Test56 (2026-10-11)

**1.0.23-test56 / Android code68**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). A polish pass on Test55
from the owner's two Test55 sessions: a parent-relative ragdoll solver for
every species (Hunters and Flood included), shot-reactive death ragdolls,
NPCs up within 1 s (NPC RECOVERY), immersive vehicles that steer the right
way without stutter and steer apart from head aiming, the Warthog wheel rim,
grip poses, throws at the release peak with THROW 2X, impact shoves, LIFT for
everything held, CHARGE GRAB and heavy-hold haptics; OpenCE Build190's lobby
countdown fix (Build189 is network 27 and not taken). Item outcomes:
[TEST56-CHECKLIST.md](TEST56-CHECKLIST.md); APKs and hashes:
[TEST56-DELIVERY-STATUS.md](TEST56-DELIVERY-STATUS.md). Device acceptance
pending.

## Previous private candidate: Test55 (2026-10-11)

**1.0.22-test55 / Android code67**, branch `test39-interaction-completion`,
for the owner's Quest and phone tests (not a release). A polish pass on
Test54 from the owner's Test54 session and messages: named campaign objects
grabbable (Shades and other vehicles, bodies, weapons, props), busy NPCs,
one-hand restraint, Spartan throws, looser ragdolls, magazine grip and
charging lock-on, automatic wall running, pouch/holster calibration with
markers, one IMMERSION menu, immersive vehicle controls with first-person
hands, zoom on the right stick with physical melee, and OpenCE Build 188's
decal batching. Item outcomes: [TEST55-CHECKLIST.md](TEST55-CHECKLIST.md);
APKs and hashes: [TEST55-DELIVERY-STATUS.md](TEST55-DELIVERY-STATUS.md).
Device acceptance pending.

## Previous private candidate: Test54 (2026-10-11)

**1.0.21-test54 / Android code66**, branch `test39-interaction-completion`,
built from 938a0448 for the owner's Quest and phone tests (not a release).
It follows the owner's Test53 report (voice working online, wall run and wall
jump working) and refines manual reload, NPC grabbing, throwing, ragdolls
(new DEATH RAGDOLLS), climbing, melee/grab separation, hands and fingers, and
the steady first-person gun parts; IMMERSION+ holds the technical options.
Item outcomes: [TEST54-CHECKLIST.md](TEST54-CHECKLIST.md); APKs and hashes:
[TEST54-DELIVERY-STATUS.md](TEST54-DELIVERY-STATUS.md); online scope:
[TEST54-NETWORK.md](TEST54-NETWORK.md). Device acceptance pending.

## Previous private candidate: Test53 (2026-10-11)

**1.0.20-test53 / Android code65**, branch `test39-interaction-completion`,
built for the owner's Quest and phone tests (not a release). Test52 (code64)
was committed but never built; Test53 supersedes it. Every change since
v1.0.18 and every requested item is in [TEST53-CHECKLIST.md](TEST53-CHECKLIST.md)
with implemented / automated / device outcomes; the delivered APKs and hashes
are in [TEST53-DELIVERY-STATUS.md](TEST53-DELIVERY-STATUS.md).

- Voice: v1.0.19 crashed when a player spoke (the assembly converter
  corrupted Opus's `cache_bits50`; see
  [TEST52-CRASH-ANALYSIS.md](TEST52-CRASH-ANALYSIS.md)). Fixed and hardened;
  the owner reported voice working on Test53.
- Interaction features had two blocking defects, now fixed: grabs used a
  zero-length pill sweep that cannot report a touch, and parkour/manual
  reload could not read the head pose from game ticks. Also: bounded NPC
  handoff, body retention through campaign script collections, co-op host
  parkour, the IMMERSION settings page.
- OpenCE Build184 / network 26: hosting 26, clients 11–26, All compatible
  networks by default, selected Build177–184 fixes. Not a full Build184
  rebase; browser (WebRTC) players cannot join this app's hosts.

## Superseded/withdrawn release attempt: v1.0.19 (2026-10-10)

Historical text follows. Its former publication/tag assertions and next-step
instructions are superseded by the verified v1.0.18 pointer at the top; this
section is retained to explain Test51-53's reported failures and fixes.

Release source is based on test39-interaction-completion, merged with the
latest main landing-page/logo update. The owner confirmed on Quest that the
Test51 build no longer crashes when joining. (A voice-chat confirmation
recorded here earlier was wrong: the owner then reported that v1.0.19 closes
as soon as a player speaks; see Test53 above.) The
stable release uses version 1.0.19 / Android code63. Build157/network24 remains
the engine baseline with selected compatible changes through Build177, not a
full Build177 rebase. See [RELEASE-1.0.19.md](RELEASE-1.0.19.md) and
[RELEASE-PROVENANCE-1.0.19.md](RELEASE-PROVENANCE-1.0.19.md).

Important: Parkour, ragdolls/body-retention changes, wall grabbing and
enemy/NPC/ally grabbing remain unfinished or unreliable; enemy grabbing may
activate but is broken and not recommended. Manual physical reload has not
been confirmed as working end-to-end. The release calls these limits out at
the top rather than presenting settings as completed features.

Preserve public v1.0.18 and all older releases/artifacts. Keep PC/Steam Frame
deferred. Future work should start from the v1.0.19 tag/source and the
unimplemented interaction requirements, not from a superseded Test51 hold.

## Superseded private candidate: Test48 (2026-10-10)

Test48 remains preserved at
`D:\HaloQuest\builds\test48-20261010-v1.0.29-test48-final`. Its original audit
and delivery record remain available in [TEST48-REGRESSION-AUDIT.md](TEST48-REGRESSION-AUDIT.md)
and [TEST48-DELIVERY-STATUS.md](TEST48-DELIVERY-STATUS.md). Test49 removes the
added per-update head-to-hand haptic path implicated by the continuous-buzz
report while retaining the signed-datum fix.

## Superseded private candidate: Test47 (2026-10-09)

Candidate target is **1.0.28-test47 / Android code58** on
`test39-interaction-completion`. It carries forward Test46/Test45 and all
recorded work since public v1.0.18. Its engine base is OpenCE Build157/network24
with selected compatible changes through Build177; this is not a full Build177
engine rebase and network24 is unchanged. The complete requirement disposition
and evidence are tracked in
[TEST47-REQUIREMENT-DISPOSITION.md](TEST47-REQUIREMENT-DISPOSITION.md);
the upstream scope is in [TEST47-OPENCE177-INTEGRATION.md](TEST47-OPENCE177-INTEGRATION.md).
Source/test status is separated from headset acceptance.

Test47 APKs and matching source/build ZIPs are packaged at
`D:\HaloQuest\builds\test47-20261010-v1.0.28-test47-final`. The full regression suite
passed in standalone, VR and flat build workflows; package checks passed for
both signed APKs and their source/build archives. This is a private owner test
candidate. No Quest/Android device acceptance is recorded, and public v1.0.18
remains the published release.

The priority arm solver fix preserves authored bone lengths and clamps wrist
reach. Compared with the public v1.0.18 tag, this deliberately removes its
up-to-18% arm extension and 35% compression workaround, which the supplied
video showed as visible deformation. Manual
reload reads the mapped VR USE/RELOAD action directly as well as the native
weapon reload bit, keeps authored-part contact and Grip/Trigger acquisition,
and records input/contact/ownership changes. Right-stick click remains melee.
Solo VR's new BODY RETENTION setting raises active-garbage thresholds from
OpenCE 50/30 to 75/45 by default (100/60 is optional, STOCK restores upstream);
it remains disabled for all network and multiplayer sessions and cannot promise
a fixed corpse count under memory pressure. The local solo multiplayer-map path avoids stale campaign continuation units,
uses a valid native game-type spawn when present or a validated in-BSP fallback,
and selects the multiplayer biped. Campaign and network player paths remain
scoped to their previous logic.

All prior interaction features remain in the source candidate: contact-driven
object/NPC handling and recovery, ragdoll integration, parkour/climbing,
manual reload, haptics, dropped magazines, bounded vehicle lifting, voice,
managed game data, Android controls, co-op, networking, VR settings, Safe
Geometry, scopes, calibration and launcher. Their actual status and device
checks are itemized in the Test47 disposition; no headset/Android-device
acceptance is inferred from host tests.

Use [TEST47-DELIVERY-STATUS.md](TEST47-DELIVERY-STATUS.md),
[TEST47-PLAYER-NOTES.md](TEST47-PLAYER-NOTES.md), and
[TEST47-DEVICE-CHECKLIST.md](TEST47-DEVICE-CHECKLIST.md). Preserve all older
artifacts and public v1.0.18. Do not publish, install or launch the game.
PC/Steam Frame remains deferred.

## Superseded private candidate: Test40

Test40 is **1.0.21-test40 / Android code51**, based on OpenCE Build157/network24.
Its delivered package and exact record remain in
`D:\HaloQuest\builds\test40-20261008-v1.0.21-test40-delivery` and
[TEST40-DELIVERY.md](TEST40-DELIVERY.md). It introduced the bounded custom rig,
magazine debris, vehicle lift and NPC rescue options. Test41 preserves these
features; do not change the accepted public release based on candidate results.

## Superseded private candidate: Test39

Test39 was **1.0.20-test39 / Android code50**, based on OpenCE Build157/network24.
Its archived candidate and delivery record remain at
`D:\HaloQuest\builds\test39-20261008-v1.0.20-test39-final`; it is superseded by
Test40 for ongoing work and did not alter public v1.0.18.

## Historical public release: v1.0.18 (2026-10-08)

The owner authorized publication of **Halo CE Quest VR + Android 1.0.18** as
the new Latest release. It is built from the Test37 network-browser work on
OpenCE Build157/network24, Android code48. Both APKs, updater metadata,
release guide and provenance are published at
[GitHub v1.0.18](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.18).
Prior releases and the GitHub About description remain unchanged. Exact APK
hashes and final package checks are in
[RELEASE-PROVENANCE-1.0.18.md](RELEASE-PROVENANCE-1.0.18.md).

The launcher adds a population-sorted client network target: exact 11–24 or
All compatible (11–24). Hosting stays on 24. Original Xbox-map PvP can use
11–22; campaign/co-op and Custom Edition require host 23/24. This is not a
claim of exhaustive hardware cross-play or every ISO/revision combination.
Read [RELEASE-1.0.18.md](RELEASE-1.0.18.md) for complete user instructions,
controls and boundaries.

## Historical Test37 candidate record (2026-10-08)

Final local branch: `test37-network-browser`. Both APKs compiled; all62 regression suites have passing results. See [TEST37-DELIVERY.md](TEST37-DELIVERY.md) for exact APK hashes, packaging gates and test limitations. Device acceptance is pending.

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
while this candidate was in private testing. Source checks and compilation do
not establish every historical server, map revision or co-op combination.
Read [TEST37-PROGRESS.md](TEST37-PROGRESS.md),
[TEST37-UPSTREAM-INTEGRATION.md](TEST37-UPSTREAM-INTEGRATION.md) and
[TEST37-PLAYER-NOTES.md](TEST37-PLAYER-NOTES.md) for its contemporaneous
evidence and delivery state. The owner later authorized publication; the
release pointer above supersedes this candidate status.

## Superseded test36 candidate work (2026-10-08)

The accepted public pointer is still v1.0.16 / code45 / OpenCE Build148 /
network23. The archived test36 candidate was 1.0.17-test36 / code46 /
Build157 / network24. Its pair was packaged for owner testing;
hashes and final checks are in TEST36-DELIVERY.md. It ports selected upstream networking and
gameplay changes and adds evidence-only two-hand aim and hand-aim fallback
diagnostics. The reported scope shift is consistent with the source switching
from calibrated weapon-hand aim to the line between the two grips; with no
device log, the aim behavior remains unchanged. The candidate is not headset-
accepted and must not advance this public/accepted pointer. The two launcher
screens also have the persistent Halo-inspired display-font toggle, support
contact and original-XISO recommendation; the existing updater was audited
against live v1.0.16 metadata and not changed. Read
[TEST36-PROGRESS.md](TEST36-PROGRESS.md),
[TEST36-UPSTREAM-INTEGRATION.md](TEST36-UPSTREAM-INTEGRATION.md), and
[TEST36-DELIVERY.md](TEST36-DELIVERY.md).

## Historical public release: v1.0.16 (2026-10-07)

Release **Halo CE Quest VR + Android 1.0.16** is published as Latest from
OpenCE Build 148 / network 23, version code 45. The release includes Android
and Quest APKs plus updater metadata; prior releases remain intact and the
GitHub About description is unchanged. Release notes, hashes and build
provenance are in [RELEASE-1.0.16.md](RELEASE-1.0.16.md) and
[RELEASE-PROVENANCE-1.0.16.md](RELEASE-PROVENANCE-1.0.16.md).

The exact v1.0.16 APK pair has no recorded Android or Quest device session.
Publication does not imply device acceptance. The most recent owner-confirmed
platform baselines remain Test31b VR and Test31c Android; Test35 carries those
settings/touch baselines forward. Continue using logs and device reports to
validate new runtime behavior.

## Test35 implementation summary (now released)

Test35 targets Android/Quest version 1.0.16/code45. It ports applicable
OpenCE Build148 changes while retaining network23: tag validation corrects
negative/NaN particle collision radii and widths in particle, particle-system,
contrail, weather, effect and breakable-surface records; point physics also
clamps any computed invalid radius before its assertion and reports it once.
The native halt screen identifies the platform/build and puts recent error
messages first. Build148 does not change network compatibility. Test34's CE
cache/BSP validation, map identity, capacity/co-op/camera fixes, server-row
pointer selection, scope diagnostics/alignment and the owner-accepted Android
touch / VR settings baselines remain. See [TEST35-PROGRESS.md](TEST35-PROGRESS.md),
[TEST35-UPSTREAM-INTEGRATION.md](TEST35-UPSTREAM-INTEGRATION.md), and
[TEST35-DELIVERY.md](TEST35-DELIVERY.md) for the engineering record.

SPV1 remains experimental. Its listed map files exceed 128 MiB but fit the
current Custom Edition parser's 384 MiB ordinary / 576 MiB upgraded file caps;
the launcher explains that size alone does not establish gameplay support.

Preserve the owner-confirmed baselines: Test31b Quest VR settings and Test31c
flat Android touch/gameplay. The prior v1.0.12 release remains archived at
network 21; it is not compatible with v1.0.16/network 23.

## Historical owner-accepted private baseline: Test31c Android; Test31b VR

On 2026-10-07 the owner reports the mobile port works great and requests leaving
its gameplay/touch implementation as-is. This applies to Test31c/code41,
runtime `173708ec068993a7256c7f0431b5d001ba46f8e6`; exact artifacts and hashes:
[TEST31C-DELIVERY.md](TEST31C-DELIVERY.md). The prior accepted VR settings design
remains a standing preference. This is not blanket acceptance of all VR vehicle
features: passenger tracking, recentering, turret controls and HUD gestures are
the next requested refinements. See [TEST32-PROGRESS.md](TEST32-PROGRESS.md).
The older pending Android entries below are superseded by this owner result.


## Private device result: Test31b VR accepted; Android UI correction pending

On 2026-10-07 the owner reported that Test31b **VR works great**, and specifically
requested that its **new VR settings design be preserved as a standing preference**.
Accepted Quest artifact: `HaloCE-Quest-test31b.apk`, 1.0.13/code40, runtime
`3399023ae8b7d0ec57e8c42c68c40ab6c33346af`, SHA-256
`d391f40a9bce4d127d5f91ceb34c84c96011ba5366db4cb99224d80c274de020`.
This is the owner's reported acceptance, not a claim that every feature was
individually tested. Preserve this APK and VR implementation.

The same candidate's Android UI is **not accepted**: its menu transition
replaced the familiar circular touch controls with a rectangular strip.
`test31c-flat-ui` restores that presentation while retaining direct menu taps
and making optional free look hide only LOOK. See `TEST31C-PROGRESS.md`.
Public GitHub v1.0.12 remains unchanged.

Follow-up before Test31c packaging: owner reports Warthog HOG GLASS does not
work and requests that specific VR fix plus both replacement APKs. Code40
remains the accepted VR comparison baseline, with this glass issue now noted.
Test31c/code41 device acceptance remains pending for both editions.

## Historical public release: v1.0.12 (test30 APKs)

**Published as Latest on 2026-10-07** from `D:\HaloQuest\builds\test30-20261007-v1.0.12`. Version **1.0.12 / code 38**, OpenCE Build 144/network 21. This incremental release fixes Quest face-button behavior in VR menus and adds an optional remembered name for campaign co-op hosts; prior release features remain. See [`RELEASE-1.0.12.md`](RELEASE-1.0.12.md), [`RELEASE-PROVENANCE-1.0.12.md`](RELEASE-PROVENANCE-1.0.12.md), and [`TEST30-DELIVERY.md`](TEST30-DELIVERY.md). Previous releases remain intact; the GitHub About description was not changed.

No device-session result for the exact v1.0.12 APK pair was supplied before publication. Automated tests and release hashes are recorded in test30 docs; they do not substitute for device acceptance. Network version remains 21, so v1.0.11 peers remain compatible. The 128-player capacity and resolution above 100% are not performance-certified.

The prior public release is v1.0.11. Historical progress and older release notes below are retained as records, not current compatibility guidance.

## Historical release: test30 (1.0.12 / code 38)

**Published as Latest:** test30, version 1.0.12 / code 38, branch `test30-profiles-coopname`, on v1.0.11. The owner confirmed the prior build was in good shape and reported that X did nothing in the VR main menu when deleting a profile. Menus now map Quest A/X/Y to the on-screen labels, while B goes back once; gameplay bindings are unchanged. Campaign hosting has an optional remembered server name. See [TEST30-PROGRESS.md](TEST30-PROGRESS.md), [TEST30-DELIVERY.md](TEST30-DELIVERY.md), and [RELEASE-PROVENANCE-1.0.12.md](RELEASE-PROVENANCE-1.0.12.md). No device session on this exact pair is recorded yet.

## Post-release validation: test30

Validate VR menu profile deletion and navigation, ensure gameplay controls are unchanged, test named and unnamed co-op hosts and browser display, and check Android/Quest gameplay. Preserve logs from each peer for connection/desync/crash reports. See [TEST30-DELIVERY.md](TEST30-DELIVERY.md).

## Historical progress

The following entries preserve the state before test28. First-person vehicles remain experimental and opt-in. Test27 (1.0.9) introduced OpenCE Build 138's netcode and co-op at network 20; test26 and earlier records document the retired project-owned protocol. See [`TEST28-PROGRESS.md`](TEST28-PROGRESS.md), [`OPENCE-COOP-COMPATIBILITY.md`](OPENCE-COOP-COMPATIBILITY.md), and [`COOP-PLAYER-COUNT.md`](COOP-PLAYER-COUNT.md) for current details. The older OpenCE network 16 / project network 11 comparison below is historical and superseded.

**Historical test22–test24b campaign status:** co-op used the project's two-player protocol. This was replaced by OpenCE-native co-op in test27; use the current status at the top of this file.

The released build is test24b (comfort page, configurable smooth/snap turning and vignette, SPV1 status notice) on top of test24 (co-op client cutscene activation, host/join instructions and public listing by default), test23 (Quest button remapping and grenade controls) and test22 (campaign host-crash fix). Detailed records: [`TEST24B-PROGRESS.md`](TEST24B-PROGRESS.md), [`TEST24-PROGRESS.md`](TEST24-PROGRESS.md), [`TEST23-PROGRESS.md`](TEST23-PROGRESS.md), [`TEST22-PROGRESS.md`](TEST22-PROGRESS.md). The earlier hand/IK report is historical, not the active release handoff.

## Historical 1.0.1 withdrawal and original 1.0.0 release notes

The withdrawn 1.0.1 record is `docs/RELEASE-PROVENANCE-1.0.1.md`. The 1.0/code-19 statements below remain historical context; the release status above supersedes them.



The following entries record the earlier release-1.0 state as of 2026-10-03. They are historical and superseded by the test20e / v1.0.2 baseline at the top of this file. Canonical public repository: [moistman42069/HaloCE-Quest-VR](https://github.com/moistman42069/HaloCE-Quest-VR), branch **main**. Release 1.0 advanced main to the complete code and public documentation at that time. The initial test13a import is historical; private identifying metadata remains excluded. Older private Git history remains a backup, not the continuation branch.

## Historical release: 1.0.0 (exact delivered test18 APKs)

The owner stated “go ahead and NOW proceed with the 1.0 release instructions
using these recent apks”. This supersedes the publication hold for the exact
pair in TEST18-DELIVERY.md. Release `v1.0.0` uses professional 1.0 filenames but
preserves **1.0-test18 / code 19** inside both APKs. No rebuild or re-sign occurs.
Public test14 remains unchanged. [Release notes](RELEASE-1.0.0.md),
[exact provenance](RELEASE-PROVENANCE-1.0.0.md).

The runtime includes test17 networking/data fixes plus test18 vehicle-camera map
lifecycle cleanup, headset-based tutorial gaze, explicit vehicle steering and
seat adjustments. **Third Person + Right Hand** are the vehicle defaults;
**Legs + Arms** remains the body default. Prior animation/grip behavior remains.
[Source evidence and tests](TEST18-PROGRESS.md).

All 13 targeted suites, both builds and packaging checks passed. Cache checks:
127 passed, 4 missing-fixture skips. Publication approval is not a new detailed
headset/phone/full-campaign test result; retain the device follow-up checklist.

### Continuation

- Future APKs need code >19 and a consistent semantic version; separate release
  approval is required. Preserve both public releases and their exact assets.
- The preserved code-19 updater can call the 1.0 promotion inconsistent because
  it has the same version code. Documented workaround: test18 users already have
  these binaries. In the next build, handle same-code promotions using version-code
  metadata before offering an update; keep downgrade/signature/hash guards.
- Bundled test18 guide/candidate wording is preserved inside the exact APKs;
  current web docs explain public 1.0 status. A future rebuild regenerates guides.
- Runtime source is `f45e32dd73b15280a5db4e5d4a4b2643f2c28379`; tag source adds
  publication documents only. Historical holds below are superseded for this pair.

## Historical candidate: test17 (basis of 1.0)

Branch `test17-network-data-profiles`, version 1.0-test17/code 18. The owner reports
test16 animations significantly improved and requests preserving native online
melee. Six test16 logs identify two networking defects now addressed: running PvP
hosts rejected by the campaign flag collision, and action-only bit 15 reaching
unit controls. Reviewed upstream departure/rejoin guards and v11 option semantics
are included. Both launchers add managed ISO/extracted data sets, detected build
and fingerprint labels, and explicit ISO/revision compatibility guidance.
[Findings, preserved scope and tests](TEST17-PROGRESS.md),
[data library](GAME-DATA-LIBRARY.md), [delivery](TEST17-DELIVERY.md).
The owner subsequently authorized 1.0 from this baseline; test14 stays available unchanged.

## Prior candidate: test16 (unpublished)

Branch `test16-native-actions` continues the complete final test15 implementation.
Version 1.0-test16/code 17 adds VR Safe geometry defaults/upgrades and native action
arm ownership. Flat defaults to Normal. See [test16 checkpoint](TEST16-PROGRESS.md)
and [candidate delivery](TEST16-DELIVERY.md). The owner supplied test15 normal/Safe
bridge evidence and a weapon-action stretching video. The follow-up confirms
improved action animation but reports the multiplayer faults addressed in test17. Test14 remains the public accepted pair; no new release is authorized.

## Prior candidate: test15 (unpublished)

Campaign capacity was audited: CE01 remains two-player; [findings and expansion requirements](COOP-PLAYER-LIMITS.md).

The added flat Android controller pass is included; see [gamepad support](ANDROID-GAMEPAD.md).

Branch `test15-community-refinements` carries the next VR/flat pair, version 1.0-test15/code 16. See [test15 checkpoint](TEST15-PROGRESS.md) for implementation, evidence, tests and remaining device validation. [Candidate delivery record](TEST15-DELIVERY.md) identifies the new APK pair and completed checks. Test14 remains the accepted public pair. No test15 release publication is authorized before owner testing.

## Accepted release: test14

On 2026-10-03, after receiving the replacement pair, the owner stated "this is it" and explicitly requested these APKs as the latest public release. This lifts the earlier release hold **for the exact delivered test14 pair**. [Release](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/halo-ce-quest-test14).

Both Quest VR and flat Android are `1.0-test14`, code 15, ARM64, built from `696a7bbe9321565d90207042067658cb8814cad1`. Subsequent commits update documentation only. Client NPC control ownership/resting state, one-shot AI animation events, unarmed vehicle-seat replication and campaign pause-menu routing are corrected. Both builds, all five targeted suites and signature/version/integrity/privacy checks passed before delivery. Exact hashes: [release provenance](RELEASE-PROVENANCE.md). The original [delivery record](TEST14-DELIVERY.md) preserves pre-acceptance evidence.

The owner accepted the pair for publication; no detailed new mission/device matrix was supplied. Do not turn that acceptance into a claim that all campaign transitions, ten missions, phones or networks have passed. Preserve the exact APKs; future changes need their own candidate result.

## Historical versions

Test13a VR/code 14 changed the body default to Legs + Arms; flat test13/code 13 retained touch and avatar reception. The initial public release was withdrawn when co-op NPC issues were reported. Test14 replaces both. `SOURCE-IDENTITY.json` describes only the initial public import. Earlier private source history stays private.

## Observed device evidence

The owner reported improved gameplay, working multiplayer/settings/Downloads logs, good room-scale legs and then that Legs + Arms works great. Earlier Quest 3 baseline observations included immersive launch and approximately 72 Hz play. These are specific reports, not an all-device/all-feature certification. The supplied test12 log ended through normal cleanup/exit; footage showed menu overlap and chest/shoulder crowding that motivated test13.

The 2026-10-03 follow-up reports successful Quest/flat co-op connectivity and full VR body movement visible on flat Android. The supplied Quest log identifies **test13**, not test13a, and records avatar negotiation. Footage/report show sliding NPCs and a stuck falling character. This narrows the failure to NPC presentation; it does not establish full campaign/checkpoint acceptance. Private media and logs stay outside Git.

## Current implementation

| Area | Included | Remaining evidence/limits |
| --- | --- | --- |
| Quest render/input | Native OpenXR, tracked headset/Touch, hand aiming, room-scale, scope, menu pointer, vehicle/cinematic options | Other headsets and all performance settings not accepted |
| Body | Four views, inferred full-body rig, room-scale feet, bounded shoulder reach, smooth elbows/twist, local torso hiding | Extreme/cross-body/overhead poses and custom rigs can still clip; no hip/foot trackers |
| Hands | Controller-driven finger poses, smoothing, palm/finger/world and approximate held-gun contact | Not optical hand tracking/full hand rigid-body simulation |
| Grip | Deliberate support grip default, fixed support anchor, first-grip protection, physical/locked weapons and holsters | Paired network physical weapon behavior unverified; off by default online |
| Movement/melee | Offline arm-run sprint and close contact, stock network speed/collision, impact or swing melee | Physical reload deferred; button reload works |
| Settings | Generated pages/dynamic storage, directional stepping, body and graphics options | Custom pause tags may not provide same menu |
| PvP browser | Full bounded feed, population sort then paging, four catalogs, invites/LAN, reviewed v9-v11 compatibility | Only ChupathingyCE preset verified; not retail PC/MCC/Xbox protocol |
| Campaign co-op | Separate host/join/browser/protocol, campaign authority/replication/transitions | Paired session and test14 release accepted; detailed full campaign coverage and public-directory announcement verification remain open |
| Remote avatars | Negotiated render-only snapshots, owner/bounds checks, interpolation/expiry, flat receiver | Owner confirmed VR body movement on flat partner; world skeleton has no separate fingers; old peers stock |
| Flat input | Customizable multi-touch overlay, swipe/fire-drag aim, Xbox-style gamepad settings, lifecycle release | Phone layout/input validation and Type/Light profile labels pending |
| Managed data | ISO/XISO/extracted imports, inbox, cache-build/fingerprint detection, atomic set selection, isolated saves | Exact disc-revision hash matrix and per-server content fingerprints unavailable |
| Logging/content | Per-launch Download/HaloCE logs with fallback; SPV1 original-map recovery | Custom content/dependencies remain experimental |

## Standing follow-up coverage

1. Reproduce reports with exact APK, settings, device, map and log; preserve the delivered binary/source.
2. Paired Quest/Quest and Quest/flat co-op: cinematic, AI/weapon/door behavior, checkpoints, both-dead recovery, BSP, restart/next mission, disconnect/reconnect.
3. Observe replicated VR head/arms/torso/legs and held weapons; check death/respawn and loss fallback. Test supporting PvP host with old/new peers.
4. Exercise flat touch movement+fire+aim, pointer cancellation/focus changes, gamepad coexistence, labels and screen sizes.
5. Diagnose any remaining menu/body/grip regressions from footage; maintain the approved Legs + Arms default and room-scale leg behavior.

Test14 is accepted for public release. Historical TEST9-TEST14 investigation/delivery documents retain their original test-time status; this file and release provenance take precedence. Source/privacy review must exclude personal author emails, workstation paths, signing keys and private evidence from public artifacts. Required third-party attribution remains intact.
