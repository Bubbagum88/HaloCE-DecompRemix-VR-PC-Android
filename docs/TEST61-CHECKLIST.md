# Test61 checklist (the wheel in your hands, impacts that hurt, more ragdolls)

Sources: the owner's Test60 sessions (`halo_log_2026-10-12_07-58-42`, video
`20261012-080350`, `halo_log_2026-10-12_08-09-52`) and messages: the Warthog
still needs refining (the grip on the wheel); IMMERSIVE VEHICLE did not turn
on first person; friendly NPCs slammed to the ground still took no damage;
some enemies did not ragdoll on explosions ("just raise the slots, a max of
24"); CUSTOM NPC RIGS and CUSTOM SCENERY should come on as needed; dead
Elites and Hunters should lift with one hand; the gun briefly stopped firing
with a magazine and ammo in (fix only if pinpointed). Columns:
**Implemented**, **Automated** (host check), **Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test61 |
|---|---|---|
| Video, HORIZON LEVEL: wheel, dashboard and hands drift apart over bumps; log: "placed in front of the chest" after "anchored at native contacts, 96-99 cm" | Controls fixed to the vehicle's body, which pitches and rolls under hands tracked in a level frame (a roll read as steering); the eyes (and hands) eased after the driver's head marker, which leans with the steering animation; the Warthog's own spot sat on the 1 m fallback limit, so the wheel jumped | Seat eyes held still while the controls are up; controls placed in the hands' level frame, turned to the seat's heading; place decided once on boarding; fallback only past 1.5 m |
| `vr.vehicle_handles set to true` at 07:59:28, seat "view third person" at 08:00:25, FIRST PERSON set by hand at 08:00:38 | The resolver only knew on/off requirements | IMMERSIVE VEHICLE requires VIEW FIRST PERSON (hard); TANK HATCH, HOG GLASS bring it (soft) |
| 08:09 log: marines (`friendly=1`) thrown at 24 m/s, no `VR impact` line in any log | The blow read only the player unit's own melee damage; the Master Chief has none (the engine falls back to the unarmed melee weapon's), so every impact returned unseen | `unit_unarmed_melee_damage`, as the engine's own melee does; a one-time log if no blow exists |
| Some enemies not ragdolled on explosions; 8 rig slots, corpses settle up to 5 s; refusals not logged | Slots exhausted by group kills | 24 slots (default 24, menu 4-24); a death with every slot busy takes the longest-settled corpse's slot; skipped deaths logged with a reason |
| 08:12 CUSTOM NPC RIGS / CUSTOM SCENERY turned on by hand | Not auto-enabled | NPC GRAB → CUSTOM NPC RIGS, WORLD GRAB → CUSTOM SCENERY (soft; they do not hold their grab on) |
| 08:11:16.961 menu BACK, 08:11:16.988 reload-button attempt, rounds 24/60, phase 2 until 08:11:24.8 | A button held as a menu closed read as a fresh reload press (the reload's edge history does not run in menus); a reload in progress blocks fire | X held while a menu is up is no reload until let go |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Steady seat | `vr_render.c` `vr_seat_steady_anchor` holds while `vr_vehicle_handles_steady()` | test_test22 (a leaning head moves the held eyes not at all), test_test61_vehicle_hold | Drive over hills |
| Controls in the hands' frame | `vr_vehicle_handles.h` `vr_wheel_hand_frame`, `vr_wheel_place`, boarding measure | test_test61_vehicle_hold (pitch/roll move neither the wheel nor a still hand's turn), test_test57b (5 places/tilts) | Wheel under the hands |
| No jump | `VR_FAR_REACH 1.5f`, constant offset | test_test61_vehicle_hold, test_test57_vehicles | — |
| IMMERSIVE VEHICLE → FIRST PERSON | `vr_menu.c` value requirements | test_test60_toggles | Fresh profile |
| Impacts hurt | `vr_interaction_impact.c` | test_interaction_impact (Chief without his own melee), test_test61_fixes | Slam a marine |
| 24 slots, corpse slot, skip log | `vr_npc_interaction.h/.c`, `port_config.c`, menu | test_vr_npc_interaction (24 ceiling), test_test20d, test_test61_fixes | Grenade a group |
| One-hand corpses | `interaction_profile`, palette | test_test61_fixes | Lift a dead Elite |
| Custom rigs/scenery auto | `vr_menu.c` | test_test60_toggles | — |
| Pouches, sprint toggle | `vr_menu.c` | test_test60_toggles | — |
| Menu-held reload | `vr_frame.c` | test_test61_fixes | Close a menu holding the button |
| Keep working | Network protocol and voice untouched; ragdoll solver unchanged | full suite | Regression list |
