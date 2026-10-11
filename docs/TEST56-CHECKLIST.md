# Test56 checklist (polish after Test55)

Sources: the owner's Test55 sessions (`halo_log_2026-10-11_15-00-59`, video
15:01:18: night fight against Elites, Grunts, Jackals and Hunters;
`..._15-04-40`, video 15:05:35: campaign, then the Blood Gulch Ghost and
Warthog), the Test56 request (D:\HaloQuest\TEST56-HANDOFF.md) and later
messages: all NPCs including Hunters and the Flood; NPC recovery never over
1 s; immersive vehicle behaviour only with IMMERSIVE VEHICLE on; settings that
only serve another feature turn on with it; OpenCE Builds 189 and 190.
Columns: **Implemented**, **Automated** (host check), **Device**
(Quest/phone only).

## Evidence

| Observation | Cause found | Test56 |
|---|---|---|
| Death ragdolls never rest: `settle still pending ... max_node_step` 0.04–0.13 units a tick after 5 s; living NPCs limp the full 5 s | Joint limits (authored relative to the parent bone, `biped_limp_noodle.c` flags: 0x1 ball, 0x2 hinge, 0x4 rigid) were compared in world space; an Elite's rigid spine held the chest upright while the body fell, and the passes fought every tick | Parent-relative solver; offline simulation on the 12 stock skeletons: the old solver left 56 of 78 cases unsettled, the new one rests every case (most in 1–2 s) |
| Every death fell the same way | One fixed 2.2 m/s kick, no damage size | Kick from the killing damage effect (damage, acceleration, category, explosion), at the hit |
| NPCs slow to get up | 150-tick settle limit for the living | Up as soon as at rest; at most NPC RECOVERY (≤1 s); 0.4 s blend |
| Ghost turns right when the hands go left (owner); Warthog hands off the wheel and stutter (video) | Steering added the turn to the heading; controls placed on the newest tick while the vehicle is drawn a tick behind | Sign fixed for every control; controls on the drawn pose; Warthog rim from its wheel node |
| Open hands on the Ghost bar (video) | Finger curls only from finger tracking | Grip pose blend 0.12 s, with or without tracking |
| "heavy hold one hand" 103 times in the 15:00 log | Logged by release() every tick for the gun hand | Logged on a real let-go only |
| Elite throws ≈9 m/s, weak throws | Lagging average blended with a slowing last tick; THROW 1X | Peak of the last four ticks; THROW 2X |
| Ghost hood fills the first-person view (video 15:05) | The Ghost's seat is built for a third-person camera | Not changed (no measured value); GHOST UP / GHOST FWD exist; device check |
| Clip ends on the Quest home screen | Owner quit from the system menu: `session STOPPING`, `the game exited (0)` | Not a crash; nothing to fix |
| HUD hint text cut at the right edge in the recording | The recording crops one eye; the hint is drawn by the native HUD | Not changed; device check |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Ragdoll solver, all species | `vr_articulated_native_prepare/_step`: rigid pieces shape-matched, frames follow their bones, ball cones and hinge arcs (no hyperextension, continuous hinge memory), self contact, one swept move per joint, repair pass | test_test56_ragdoll (12 skeletons × 5 falls, ASan/UBSan) | Kill Elites, Grunts, Jackals, Hunters, Marines, Flood |
| Shot-reactive deaths | `vr_npc_impulse.h`; damage.c passes damage, acceleration, category, explosion; rifle ~1.1, pistol ~1.5, sniper ~3.8 m/s at the hit; melee shove; blasts throw away and up; pellets add; native push never doubled | test_test56_polish | Head, leg, side shots; grenades |
| NPC recovery ≤1 s | `vr.npc_recovery` (0.25–1 s, default 1 s) on IMMERSION → ADVANCED; rest ≥10 ticks then up; corpses keep the 5 s settle and never recover | test_test56_polish, test_vr_npc_interaction | Let go of a living NPC |
| THROW 2X, release peak | `vr.throw_strength` 2.0; `vr_world_throw_peak` for props and NPCs | test_test56_polish, test_vr_world_physics | Throw a Grunt, a crate |
| Impact shove | `impact_shove` before damage; capped 4 m/s; scaled by the struck object's acceleration scale | test_test56_polish, test_interaction_impact | Throw a body at an Elite, a Warthog |
| Elite/Hunter one hand, two hands | One hand restrains (no lift), second lifts/carries/throws; light NPCs one hand; haptics on the weight arriving and the second hand | test_vr_npc_interaction, test_test56_polish | Grab, add a hand, let go of one |
| LIFT | NPC HOLD renamed LIFT (same key); props/turrets/vehicles via `vr_world_lift_strength` (default leaves props unchanged) | test_test56_polish | Lift a Shade at each LIFT setting |
| CHARGE GRAB | `vr.charge_grab_radius` 2–10 cm (default 4 cm = Test55), every weapon; on RELOAD; POUCH SIZE to POUCH PLACES | test_test56_polish, test_vr_immersion_menu | Pistol slide, AR handle |
| Immersive vehicles | Only with IMMERSIVE VEHICLE: sign fixed, Ghost twist+tilt, Scorpion tank sticks, Banshee roll+pitch, 1.5° dead zone, 60° lock, time-based centring, haptics; drawn-pose anchoring; Warthog wheel node rim (+2 cm reach); two hands averaged, either alone | test_test38_vehicle_handles, test_test56_polish | Each vehicle, both hands, one hand |
| Steering apart from aiming | `vr_vehicle_handles_facing` replaces only the driver's facing; head aims; online client keeps Test55 | test_test56_polish | Ghost/Banshee guns, Scorpion turret follow the head |
| Ordinary vehicle controls | Untouched with IMMERSIVE VEHICLE off | test_test38_vehicle_handles, full suite | Drive with it off |
| Middle-finger gesture | Dropped: Touch, Touch Plus and Touch Pro have no middle-finger sensor; "trigger + grip released" is a normal resting/clicking pose and would misfire | — | — |
| OpenCE Builds 189–190 | 189 (Custom Edition map sharing) raises the network to 27: not taken. 190's lobby countdown fix (2059b6ce, host only, nothing sent changes) taken; its map-sharing commit not | test_test56_polish (network 26 pinned, countdown) | Host a lobby, have someone join during the countdown |
| Wall run, manual reload | Unchanged (settled) | full suite | Regression list |
| Keep working | Voice code untouched; no protocol change; co-op path unchanged | full suite | Regression list |
