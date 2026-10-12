# Test59 checklist (vehicles, OpenCE Build 201 / network 28, reload, ragdolls)

Sources: the owner's Test58 sessions (`halo_log_2026-10-12_05-18-10`, video
05:19; `halo_log_2026-10-12_05-36-50`, video `20261012-054810`) and messages:
the Warthog hard to drive (arm stretch) and the free hand turning with the
wheel; Ghost grips hard to grab; no visible way to move the tank; hands flat
and fingerless in vehicles ("keep everything else about the body in the
vehicle the same"); OpenCE Build 201 and the latest network, with All
compatible as the default and every network (27 too) in the selector; a
pulled magazine would not go back in; reload jittery while moving; ragdolls
should fly back with bullet damage and away from explosions. Columns:
**Implemented**, **Automated** (host check), **Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test59 |
|---|---|---|
| Flat, fingerless hands in vehicles; the free hand turned with the wheel | A driver's weapon is stowed (`active_weapon=-1`), so no first-person rig existed; the body's arms, steered by the driver animation, held the controls | The stowed weapon lends its first-person rig while the immersive controls steer (gun hidden); the body's arms fold only then |
| Warthog wheel 74-97 cm, Ghost bar 71 cm from the eyes; 12-17 cm misses | Controls on the model's markers, out at arm's length | COMFORT REACH: past 55 cm, in toward the eyes on the same line (a hidden wheel stays on the model's) |
| `drive stick not taken: 220 cm away` | Stick placed from the eyes once, 0.5 s into boarding | Stick, Banshee bar and marker-less controls from the eyes every frame |
| Tank: no visible way to move | The stick only turned | TANK DRIVE: push/pull the stick for throttle |
| Pulled magazine held at the well 3 s (05:48:14-17, 05:49:20-23; video 70-73 s), never went back | OLD_HELD had no way back in: only a pouch's magazine could be inserted | The gun's own magazine reseats (returned, let go at the well, or taken back up), ammo unchanged |
| Jitter grabbing the magazine while walking | Well from the drawn gun, hand from the game tick's camera | Both from the drawn camera (`vr_render_drawn_camera`) |
| `death ragdoll ... push_mps=0.0-0.4` for shot deaths; `speed_mps=9.00` for every explosion death | A bullet's body push was 0.004 x damage; the engine's blast throw clipped to 9 m/s | DEATH FORCE: burst push (rifle 2.5-3.7 m/s with lift), blasts ~2x with lift, blast throw kept to 12 m/s |
| OpenCE Build 201 = network 28 | 27: map sharing (messages 83-86); 28: BSP, lights, second-weapon rules, held downloading players | Hosts 28; joins 11-28; map requests answered "not shared"; 28's rules ported |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Real hands in vehicles | `vr_render_vehicle_hands_weapon`, `first_person_weapon_switch_weapons`, render visible with `vr_render_vehicle_first_person_hands` | test_test57_vehicles | Finger gestures on the wheel; the free hand stays still |
| Controls from the eyes | `head_anchored` for stick, bar, marker-less | test_test57b_vehicle_anchor (boarding case) | Get in the tank: stick in front of the chest |
| COMFORT REACH | VEHICLES row, on; 55 cm pull; hidden wheel exempt; >1 m chest fallback | test_test57b_vehicle_anchor | Warthog wheel within easy reach |
| Ghost grips | +2 cm reach, grab span -50%..115% | test_test57_vehicles | Grab both grips first try |
| TANK DRIVE | VEHICLES row, on; `players.c` throttle, further of stick and thumbstick; local/host | test_test38_vehicle_handles | Drive the Scorpion with the stick |
| Network 28 hosting, 11-28 joining | `halo_port_limits.h`; launcher `NetworkProfile` 28..11; default 0 | test_test59_network28, test_test37_network_profiles (targets 11-28, 29 refused) | Selector shows 28, 27; All compatible default |
| Map sharing answer | `map_share_handle_message` (stream only, joined machines, lobby too) | test_test59_network28 (real responder, forged requests) | An OpenCE CE client without the map is told at once |
| Network 28 rules | `hs.c` BSP, `game_engine.c` lights, `units.c`/`network_objects.c` second weapon | test_test59_network28 | MP match with an OpenCE 28 player |
| Build 201 extras | Overshield drain (hud_unit.c), client bodies (network_objects.c, VR-held excluded), transparent groups 2048, static debug vertices | test_test59_network28 | — |
| Own magazine back in | `VR_MR_RESEAT`, `VR_MR_RECOVER`; returned = 4 cm clear then 3 cm aligned, or let go at the well | test_manual_reload, test_test59_reload_ragdoll | Pull, push back, fire |
| Reload steady walking | Drawn camera for hand, contacts and held magazine | test_test59_reload_ragdoll | Reload while walking |
| DEATH FORCE | IMMERSION > RAGDOLLS row (new topic: DEATH RAGDOLLS, DEATH FORCE, BODY RETENTION) CLASSIC/STRONG/HUGE (strong); burst table; blast cap 12 m/s | test_test59_reload_ragdoll; test_test56_ragdoll (rifle burst, rocket, huge rocket, huge sniper settle in < 5 s for 12 skeletons) | AR kill flies back; grenade throws |
| NPC recovery | Unchanged: living NPCs up within 1 s | test_test56_polish | — |
| Keep working | Voice untouched; ordinary vehicle controls unchanged without IMMERSIVE VEHICLE; tank view unchanged (TANK HATCH off) | full suite | Regression list |
