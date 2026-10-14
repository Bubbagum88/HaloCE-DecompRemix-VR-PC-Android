# Test66 checklist

Source: the owner's 2026-10-13 Test65 feedback brief (62 points, main
priorities 1-47), the 16:08 and 16:24 logs and videos (broad gameplay;
ragdolls and the Silent Cartographer wall run), the 17:37 weapon-pull log and
video, and the owner's later additions (OBJECT THROW, waist grenades, "all of
OpenCE, map sharing included", WEAPON PULL like Half-Life 2 VR, OpenCE's
dynamic ragdolls, SPV1 warnings, The Altheros Experience). Columns:
**Implemented**, **Automated** (host checks), **Device** (pending for all).

## Evidence

| Observation | Cause found | Test66 |
|---|---|---|
| Warthog view drops into the dash for ~1.5 s (video 4:41, 5:36, 5:41) | `vr_seat_steady_anchor` re-captured and held the seat's eye point whenever the head marker strayed > 0.5 m | eye point fixed per seat while the controls are up; strays logged |
| Wheel released/reset when turned far | each hand's turn wrapped at +-180 degrees from its grab | `vr_wheel_grip_follow`: unwrapped frame to frame, wheel 120 degrees, steering lock 60 |
| ENEMY HEALTH at max had no effect | the damage scale's minimum dominates (`(1-scale)*min + rand*scale`) | fist share applied as the damage multiplier |
| Grab misses on armour ("collision_candidates=0") | assist measured from the bone centre line | assist from the body surface (`collision_model_touch_sphere`), 10 cm default, 25 cm max |
| Held corpses vanish | at rest / on the garbage list; root left behind | `npc_keep_held`; root follows the held torso |
| Silent Cartographer wall run fails | only abs(nz) < 0.35, one probe height | runnable to abs(nz) < 0.6, three probes, normal blending, 6-tick gap grace |
| WEAPON PULL does nothing and has no switch (17:37 log) | line of sight into the ground; gun hand refused; 1 m reach | rebuilt as gravity gloves with WEAPON PULL / PULL REACH / PULL STYLE / PULL GLOW |
| Grenades warp when lowered | placed from the head's pitch; LOD switch | torso frame from the neck; drawn at full detail, 0.75 scale |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Keep immersive vehicle visuals; Warthog camera snap; wheel hold/turn | yes | test_test22, test_test38_vehicle_handles, test_test66 | pending |
| Vehicle profiles validation (Ghost, tank, Banshee unchanged) | reviewed, unchanged | existing vehicle suites | pending |
| IMMERSION > VEHICLES page (all immersive vehicle rows), calibration kept | yes | test_vr_immersion_menu, test_test66 | pending |
| LEFT-HAND MODE | yes | test_test66 | pending |
| Manual reload: Halo grip poses, grip lock, per-weapon, mag-well axis + haptics + seat pulse, well assist, charge handle axis lock, charge radius kept | yes | test_reload_contact, test_test59_reload_ragdoll, test_test66 | pending |
| Fist combat: ENEMY HEALTH, airborne lunge, bone hit regions, coherent mode, block/parry/stun, enemy kinds, Elite answers | yes | test_test62_extra, test_test66 | pending |
| NPC grab assist (works, max really larger), light/heavy lifts | yes | test_test60_toggles, test_vr_npc_interaction, test_test54_interactions | pending |
| Ragdolls: held never vanish, thrown persist, shot/slam impulses, shot-reactive deaths | yes | test_test59_reload_ragdoll, test_test66 | pending |
| Wall run on curved/angled/segmented walls | yes | test_test66 (compiled wall-face harness) | pending |
| OBJECT/VEHICLE THROW, auto with world/vehicle grab | yes | test_vr_world_physics, test_test60_toggles | pending |
| Grenades: smaller, waist, no warp | yes | test_test20d, test_test62_extra | pending |
| WEAPON PULL (gravity gloves) | yes | test_test66 (11 compiled scenarios), test_test65 | pending |
| Dependencies auto-enabled, optional ones configurable | yes (audit below) | test_test60_toggles, menu suites | pending |
| OpenCE parity, map sharing included (Build 201 verified latest) | yes, with reasoned exclusions | full suite incl. test_test31 (Build 201 hashes), test_test56/57/59 map-share pins, upstream harness test_map_share_names | pending |
| OpenCE dynamic ragdolls (Jolt) as the base, our mechanics on it | yes | test_test66_ragdolls (Jolt in the host, bridge parity) | pending |
| SPV1 launcher warnings removed | yes | test_test66_campaigns | pending |
| The Altheros Experience as a second custom campaign; switching | yes | test_test66_campaigns; cache_file_report loads all 10 maps | pending |
| Logs and videos reviewed | yes | n/a | n/a |
| Regress nothing | full suite green | 131+ suites | pending |

## Vehicle validation

The Ghost (handlebar), Scorpion and Wraith (drive stick) and Banshee (flight
bar) profiles in `vr_vehicle_handles.h` were read against the Test65 videos
and left unchanged: the owner reports the Ghost and tank good, the Banshee is
untested. The Warthog alone uses the new unwrapped wheel follow
(`VR_WHEEL_TURN_LIMIT`); every other kind still clamps with `VR_WHEEL_LOCK`.

## Dependency audit

Hard and soft rows in `vr_menu_dependency_table`: FIST COMBAT and NPC GRAB
bring GRAB ASSIST (soft, value 10 cm, met at 9.5 cm or more), WORLD GRAB and
VEHICLE LIFT bring OBJECT THROW (soft, 2X, met above 0), DEATH RAGDOLLS
brings NPC GRAB, NPC RESCUE and IMPACT DAMAGE (as Test60), vehicle
refinements bring IMMERSIVE VEHICLE (as Test60). WEAPON PULL, LEFT-HAND
MODE, DEATH PHYSICS and the display options are independent switches.
Saved settings stay; only new keys get defaults (grenades moved once to the
waist).

## Resumed audit

Compared the original Test65 feedback and later additions in the local Claude
transcript against this checklist and the handoff. Build 201 remains the latest
published OpenCE release at the resumed check. No merge markers remain in the
source/port/tools trees. Voice codec/capture/playback and host audio changes were
checked against Test65: the new voice drawing is the only voice-runtime edit.
Found an incorrectly escaped speaker bitmap path (single backslashes: C interprets
backslash-v as a vertical tab). Corrected the path and added a check which failed
before the fix and passed afterward. No codec or protocol change.
The guide now distinguishes intended behavior from device validation and does not
claim an untested Banshee result or an exact six-times punch count.

The distribution notices were missing the newly bundled Jolt and Lucide licenses.
Both complete notices and credits were added so generated APK field guides and
packaged archives carry the third-party attribution.

The first post-identity full run exposed an older Test26 banner assertion. Its
gameplay harnesses passed; the identity check now also accepts the exact verified
Build201/network28 banner. No gameplay assertion was removed.

Resumed map-sharing audit: the host-only signalling code never fills another
internet player's key hash. The newly added lookup previously returned that zero
key as a usable seed. It now refuses missing keys, so upstream clients are not
sent unusable sources. The host download uses its established address separately;
LAN sources are unaffected. A compiled test covers stopped signalling, missing
peers, empty keys, valid keys and lock release. No wire format/version changed.

The initial rerun finished with two stale identity pins (Test26 and Test34);
both were updated for the Build201 banner, preserving their behavior checks.
The final full runs below use the corrected pins.

## Final automated runs

All 131 registered suites passed in the standalone rerun and before each
flavor build. Both native/Gradle builds, built-image Opus table checks and
guest ABI lint passed. Additional sanitized production bridge tests verified
contact layout, signed IDs, guards and buffer bounds. APK versions, signer,
19 Jolt host imports and native dependencies were checked independently.
Exact artifacts and limitations: `TEST66-DELIVERY-STATUS.md`. All device
entries above remain pending.
