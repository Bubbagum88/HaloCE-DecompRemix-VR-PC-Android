# Test60 checklist (impacts for every NPC, settings that come on together)

Sources: the owner's Test59 session (`halo_log_2026-10-12_07-04-04`, video
`20261012-071258`) and message: everything working well; NPC RESCUE was not
turned on with DEATH RAGDOLLS, and the other automatic settings should be
checked too (IMPACT DAMAGE and NPC GRAB with ragdolls); slamming friendly
NPCs did no impact damage, and it should work with every NPC. Columns:
**Implemented**, **Automated** (host check), **Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test60 |
|---|---|---|
| No `VR impact` line in the whole log, though marines (`species=7 friendly=1`) and enemies were thrown at 24 m/s with IMPACT DAMAGE on (video: IMPACT SPEED 4 M/S, IMPACT DAMAGE ON) | (1) a joint's sphere met the floor or a wall but its centre's path (the only probe) missed it: slams flat onto the ground never counted; (2) the probe used the line-of-sight flags (0xC2AD), which leave out bipeds, and the ragdoll's own sweep (dead-biped flags 0xC0A0) passes through bipeds and vehicles: a body never struck another | A sphere contact is probed straight into the face it met; a fast joint is tested against bodies and vehicles, stops at them and strikes them (not players) |
| Allies barely hurt by a blow | Impact damage carried the player's team: the engine applied allies' friendly-damage resistance and friendly-fire rules | A blow carries no team (still credited to the player): every NPC takes it in full |
| `vr.death_ragdolls set to true`, NPC RESCUE set by hand afterwards | DEATH RAGDOLLS had no dependencies; soft requirements did not chain | DEATH RAGDOLLS turns on NPC GRAB, NPC RESCUE, IMPACT DAMAGE; a feature turned on automatically pulls its own soft requirements (FIST REQUIRED) |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Floor and wall slams count | `vr_articulated_native_sweep`: probe into the met plane (`VR_IMPACT_TEST_FLAGS`, bipeds included); floors still need over 6 m/s, damage by the speed into the surface | test_test56_ragdoll (glancing 27 m/s slam counts, 1 m/s does not) | Slam a held marine onto the ground |
| Bodies strike bodies and vehicles | `VR_IMPACT_BODY_TEST_FLAGS` ray over a fast joint's move; the joint stops at the hit; players never | test_test56_ragdoll (stop at the body, struck object reported; a player's body passes; no impact unless thrown) | Throw a Grunt into an Elite or a marine into a marine |
| Allies take the blow | `vr_interaction_impact.c`: `owner_team_index=NONE` for the struck body and the thrown body itself | test_test60_toggles (wiring), test_interaction_impact | Marine hurt or killed by a slam |
| Momentum on the struck body | Unchanged (Test56 impact shove, before the damage) | test_interaction_impact | Struck NPC staggers |
| DEATH RAGDOLLS turns on NPC GRAB, NPC RESCUE, IMPACT DAMAGE | `vr_menu_dependency_table` (soft) | test_test60_toggles (real resolver) | Turn DEATH RAGDOLLS on in a fresh profile |
| NPC GRAB, WORLD GRAB, LIFT VEHICLES turn on IMPACT DAMAGE (NPC GRAB also NPC RESCUE) | same | test_test60_toggles | — |
| Vehicle refinements turn on IMMERSIVE VEHICLE; HOLSTER HAPTICS turns on HOLSTERS | same | test_test60_toggles | — |
| Chained soft requirements | `vr_menu_dependencies`: a feature turned on automatically in this choice counts as chosen | test_test60_toggles (FIST REQUIRED through NPC GRAB) | — |
| Turned off by hand stays off; released with its feature | Unchanged rules | test_test60_toggles | — |
| Keep working | Ragdoll settle and limits unchanged (impacts only while thrown/held); voice, network 28, vehicles, reload untouched | full suite, test_test56_ragdoll (12 skeletons x 9 falls) | Regression list |
