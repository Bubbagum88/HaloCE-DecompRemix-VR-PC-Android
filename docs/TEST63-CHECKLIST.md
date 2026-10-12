# Test63 implementation and evidence checklist

Private **1.0.30-test63 / code75**; branch `test39-interaction-completion`.
Baseline: Test62 (`ed60571f`, record `ad299703`), kept whole. Sources: the
owner's fresh-install Test62 session (`halo_log_2026-10-12_12-06-10-677`,
video `com.halo.decomp.vr-20261012-120642-0.mp4`, both reviewed completely:
the log line by line for settings, inputs, grabs, impacts, vehicles and
deaths; the video by contact sheets of the whole 8.5 minutes and dense
frames of each event) and the owner's requests. Columns: **Implemented**,
**Verified automatically** (host checks), **Verified on device** (the
owner's headset; none yet).

## Evidence

| Observation (log / video) | Cause found | Test63 |
|---|---|---|
| `reticle hidden (vr.button_reticle)` 12:10:53, `button sprint enabled` 12:11:04, reticle never back | Sprint frees the click from the toggle; a hidden reticle had no button left | Sprint owns the click; a toggle without a button shows the reticle; menu skips L STICK under sprint |
| X at the Warthog: `event=8 ... spawned visual magazine`, then the seat (12:09:37) | Reload button = action button; eject read the press first | No eject while `player->action_result` offers an action |
| Video 1:16–1:34: hand closed on the chest ball, no `grabbed chest slot` | Pickup measured from the controller grip + 3 cm, 9 cm; slot from the head's heading | Drawn palm, 12 cm, hover tick, miss log; torso chest frame |
| Green/blue balls in the video | Placeholder shells | Game's frag/plasma projectile models (world model pass) |
| No `acquired` line in the log; fist hits on contact only | 1.5 m reach; the punch's own line to the target's centre required | 2.5 m, 45-degree gaze cone, hooks count, step up to 5 m/s, target slowed not frozen, diagnostics |
| `contact grab miss` at the beach crates (12:11:23–12:14:47) | 32 contact tests spent on trees/Pelican (17 m bounds) in iteration order | Nearest bounds first; >4 units skipped; nearest named in the miss log |
| Warthog wheel: flat ring and T spokes (video 1:34–1:54) | Debug boxes | The model's own wheel bone moved/turned; others redesigned shaded parts |
| VEHICLES offset rows (video 2:44–2:52) with nothing seen | No preview; the paused menu froze the controls; a setting change cleared them | Blue preview while a `vr.handle_*` row shows; offsets read live; no clear during calibration |
| Settings: WALL SPEED 1.5X, WALL LEAP 1.5X, CLIMB LAUNCH back to 1X, THROW POWER 1.5X (log 12:07:10–12:07:31, video 0:44–0:50, 2:45) | Owner's choices | Defaults (saved choices stay) |

## Requests

| Request | Implemented | Verified automatically | Verified on device |
|---|---|---|---|
| Reticle / sprint / L-stick | Ownership in `vr_reload_settings`; menu skip; existing move-aside/restore kept | test_test63 pins; test_test31_vr_menu, test_test60_toggles | Pending |
| Input conflict audit | Sprint vs reticle; X action vs magazine release; grab hands end the fist step; existing ownership (`vr_interaction_claim`) for grenade/reload/world/NPC/parkour/vehicle/holster | test_test63, test_test62_extra, reload/contact suites | Pending |
| Grenade body anchoring | `vr_torso_place` chest frame (35 degree cone, holds looking down) | test_test63 compiles and steps the production torso code | Pending |
| Real grenade meshes | Projectile model, neutral colours, world model pass | test_test62_extra (no-model fallback), test_test63 pins | Pending |
| Grenade interaction | Drawn palm, 12 cm, hover/miss feedback, existing momentum/count/ownership rules | test_test62_extra (palm 10 cm taken, 15 cm not; chest frame) | Pending |
| Melee assist acquisition, lunge, continuity, feedback, grab handover | `vr_combat_punch`/`vr_combat_velocity`; existing highlights, flash, stun, native hurt/damage | test_test62_extra (2.5 m, 3.2 m refused, hook, away refused, 5 m/s, slowed, grab ends) | Pending |
| Ordinary physical melee unchanged with assist off | Assist code gated by FIST COMBAT | test_test62_extra fist gate | Pending |
| Vehicle meshes | Warthog model wheel (`vr_vehicle_controls_matrices`), shaded tubes for the rest | test_test38/57/57b/61 vehicle suites, test_test63 pins | Pending |
| Vehicle calibration and preview | Existing per-vehicle + all-vehicle offsets; live preview with reach spheres and axes | test_test57b (production prepare/read), test_test63 pins | Pending |
| Purple crate | Ordered contact candidates | test_contact_acquisition, test_vr_world_props, test_test63 | Pending |
| ONE-HAND HEAVIES | `vr.npc_one_hand_heavy`, hard dependency on NPC GRAB | test_test60_toggles, test_test63 | Pending |
| Owner defaults | WALL SPEED / WALL LEAP / THROW POWER 1.5X; FIST REACH 2.5 m | test_test63 | Pending |
| Settings index | Category index for 3+ screens; jump rows; MORE | test_test31_vr_menu (index rows open their screens; 451 allocation failures recovered; pause lifecycle) | Pending |
| Dependencies / settings audit | Required vs optional unchanged except ONE-HAND HEAVIES → NPC GRAB (required); no new auto-enabled optional features | test_test60_toggles | Pending |
| Regress nothing | Test62 behaviour kept; voice and protocol untouched | Full suite before each flavor build | Pending |

## Limits

- None of Test63 has been tried on a headset or phone.
- The grenade models and the Warthog wheel bone come from the stock maps'
  tags; a map without them falls back to the drawn shapes.
- The assist is a bounded step and target slowing; no camera turns,
  teleports or animation locks.
- Network: new actions stay local or co-op host only (HOST VR ACTIONS), as
  in Test62. No protocol change.
