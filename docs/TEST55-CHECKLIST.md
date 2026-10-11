# Test55 checklist (polish after Test54)

Sources: the owner's Test54 session (`halo_log_2026-10-11_12-04-36`, video
12:10:06), the Blood Gulch vehicle test (`..._12-52-06`, video 12:52:41), the
31-point Test55 request (D:\HaloQuest\work\next\TEST55-HANDOFF.md), and later
messages: OpenCE Build 188; vehicle lifting and Shade turrets; apply each fix
to everything it fits; zoom on a fist. Columns: **Implemented**,
**Automated** (host check), **Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test55 |
|---|---|---|
| Shades could not be grabbed | Stock Xbox USA a50/c10/b40/c40/d20: 59 of 61 placed Shades are script-named; lifting refused named vehicles (Shades do have point physics: 4 mass points) | Named objects allowed everywhere; movie stars excluded |
| Same rule elsewhere | Nearly all campaign vehicles named; bodies 88/95 (c10), 50/50 (b40); weapons 43/45 and equipment 201/203 (b40); scenery up to 148/293 (d40) | Items, scenery, NPCs, bodies, rig capture, death ragdolls |
| Elites and Marines rarely grabbable | Busy weapon / dive / melee states refused (~12 of 32 eligible) | Allowed |
| One hand on an Elite did nothing | Heavy bodies needed both hands to start; releasing one dropped both | One-hand restraint and drag; other hand keeps hold |
| Weak throws (no impact lines) | Hand speed only, 7 m/s cap | Spartan classes 2.4/1.8/1.25, ≤24 m/s, impact damage both ways |
| Every death ragdoll species=0 | Species read from its own blank slot | Read before activation |
| Puppet ragdolls sliding | Leaf joints never rotated; no floor friction; uniform death velocity | Leaf rotation, Coulomb floor friction, hit-located kick |
| 8 missed squeezes on the AR handle in 4 s | 4 cm palm at the press frame only | +4 cm lock-on, 0.35 s grace |
| Magazine at an odd angle, pointing finger | Socket's world angle at the palm; controller finger curls | Gun-hand relation, centred in the palm, fist curls |
| Draws 590 → 3,030 per frame in a long fight, back to 530 after a revert | Decals (bullet holes/blood), one draw each per eye | OpenCE Build 188 decal batching |
| Fist zooms | Zoom is the off-hand index trigger | Right stick click with physical melee (if free) |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| OpenCE Build 188 | 185–188 reviewed: no network change (still 26); decal batching adopted (`rasterizer_xbox_decals.c` = Build 188's); browser/web-only and renderer-internal changes not taken | test_test55_polish | Join a 188 server; fps in a long fight |
| One IMMERSION menu | Sections WEAPONS/RELOAD/POUCH PLACES/HOLSTER PLACES/MOVEMENT/BODY/GRAB + NPCS/ADVANCED; NEXT names the topic; dependencies unchanged (required only) | test_vr_immersion_menu, test_test25 | Page through |
| Magazine grip | Gun-hand relation, palm-centred, fist curls; insertion 3 cm / ~63° | test_manual_reload, test_test55_polish | Look and insert |
| Slide / charging handle | +4 cm, 0.35 s grace, existing pull axis and haptics | test_test55_polish (state machine) | Pistol, AR, sniper |
| Calibration | 12 offsets ±20 cm + POUCH SIZE; the same functions place triggers and markers; blue markers while rows show; pouches mirror left-handed | test_test55_polish | Move each, watch the ball |
| Wall running | 8+1 probes, released-stick runs, 4–9 m/s × WALL SPEED, inward hold, level 60%, chaining 2 s; wall jump unchanged | test_vr_parkour, test_test55_polish | Run, chain, jump |
| NPC grabbing | Busy/dive/melee eligible; named; restraint; weight haptics; Spartan throws; impact damage | test_vr_npc_interaction, test_test55_polish | Elites, Marines, throws |
| Ragdolls | Leaf joints, floor friction, floor impact >6 m/s, hit-located kick | build + suites | Kill and throw bodies |
| Vehicle controls | Rim/handle grab (contact +4 cm), controls own steering and self-centre, Banshee yoke pitch, new Ghost/Scorpion/Banshee meshes, none for the Warthog, first-person hands with finger poses, IMMERSIVE VEHICLE | test_test38_vehicle_handles | Each vehicle |
| Vehicle lifting / Shades | Named vehicles; Banshee added; movie stars, occupied, parented, destroyed, Pelican/dropship stay stock | test_vr_vehicle_lift | Lift a Shade on a50/c10 |
| Apply fixes everywhere | Named objects (items, scenery, NPCs, bodies, rigs, death ragdolls, vehicles); Spartan throws for props/weapons too | test_test55_polish, test_vr_world_physics | Throw a crate and a gun |
| Zoom on a fist | Right stick click when physical melee is in use, on foot, and nothing else is mapped there | test_test55_polish | Fist: no zoom; click: zoom |
| Keep working | Voice code untouched; no protocol change; co-op path unchanged | full suite | Regression list |
