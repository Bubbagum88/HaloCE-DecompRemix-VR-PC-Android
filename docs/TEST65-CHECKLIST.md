# Test65 checklist

Source: the owner's 2026-10-13 message and the logs/videos of 2026-10-12
(`halo_log_2026-10-12_17-02-50` Warthog drive, `com.halo.decomp.vr-20261012-172952`
video, `halo_log_2026-10-12_17-48-57` grabs and throws, a tester's
`orca_share_media...` log, the 22:11 logs). Columns: **Implemented**,
**Automated** (host checks), **Device** (Quest only).

## Evidence

| Observation | Cause found | Test65 |
|---|---|---|
| 65 fist strikes in the Test64 logs, zero "VR fist combat" lines | `vr_combat_punch` asked `vr_head_view`, which refuses a tick that runs before this frame begins (player_control: the fist sweep comes before `vr_aim`) | `vr_head_view_recent` (the last frame's head) |
| Warthog video: a violet bar with blue tips across the wheel | the Warthog with its own wheel bone fell through to the Banshee's flight yoke branch | its own branch; GRIP GUIDE (off) |
| Warthog wheel/camera unstable, snapping (17:28-17:30 drive, 50-60 fps) | eyes turned with the drawn vehicle and level; hands and wheel in a level frame turned by the 30 Hz tick heading | COCKPIT LOCK: one drawn seat frame for eyes, hands, aim and wheel |
| Tester: crushed lifting/throwing Shade turrets | turret grabbed 16:39:48, checkpoint back 16:39:55; thrown 16:40:02, back 16:40:05: `physics_compute_biped_collision` gives vehicle collision damage when it cannot fit the biped clear | `vr_world_interaction_protects` |
| Marine grabbed 17:56:46, self impact 0.58 at +0.27 s, then six full-scale hits on an ally while held | held bodies' limbs meeting the floor and allies counted as blows (globals falling damage) | grace, slam-only, allies spared, thrown allies half |
| Thrown corpses vanish; "settle still pending ... max_node_step 0.2 ... garbage_queued=1" | handed back moving with the clean-up mark restored; the engine collects active unseen garbage | torso-based rest up to 10 s; mark deferred until at rest |
| "contact grab miss ... nearest c gun turret ... -210 cm" | 4 cm palm must touch the collision surface | assist pass (GRAB ASSIST + 3 cm) |
| Pistol rack passed the gun to the other hand | swap reach 20 cm | HAND SWAP 10 cm |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Fist combat acquires | `vr_extra_interaction.c`, `vr_frame.c vr_head_view_recent` | test_test62_extra (tick before the frame) | item 1 |
| Lunge, blow on arrival | `combat_engage`, `combat_tick`, `units.c unit_vr_combat_strike` | test_test62_extra | 1 |
| Combo meter, takedown, ENEMY HEALTH | `vr_combat_hit`, `damage.c vr_combat_note_damage` | test_test62_extra | 2, 4 |
| Counters | `units.c unit_melee_attack_begin` -> `vr_combat_note_melee`; `vr_combat_stunned` | test_test62_extra | 3 |
| Knockdowns | `vr_npc_interaction_knock` | test_test65 (wiring) | 2, 3 |
| No Banshee yoke on the Warthog; GRIP GUIDE | `vr_vehicle_handles.h` | test_test65 | 5 |
| COCKPIT LOCK | `vr_frame.c view/vr_aim`, `vr_render.c vr_cockpit_update`, `vr_wheel_hand_frame` | test_test65 (view), test_test61_vehicle_hold, test_test25 | 5 |
| HAND SWAP | `vr_frame.c`, CONTROLS row | test_test65, test_test21 | 6 |
| Turrets never crush their holder | `physics.c`, `vr_world_interaction.c` | test_vr_world_physics | 7 |
| Held NPC impacts | `vr_interaction_impact.c` | test_interaction_impact | 8 |
| Thrown bodies kept | `vr_npc_interaction.c` deferred clean-up | test_vr_npc_interaction | 8 |
| GRAB RAGDOLL, ACTIVE RAGDOLL, touch push | `vr_npc_interaction.c`, `vr_body_reactions.c` | test_test65 (reaction poses) | 9 |
| WEAPON PULL, PULL GLOW | `vr_weapon_pickup.c`, `players.c player_vr_take_weapon` | test_test65 (wiring) | 10 |
| World grab assist | `vr_world_interaction.c candidate` | full suite | 11 |
| Dual wield | not implemented (engine fires only the current weapon) | - | - |
