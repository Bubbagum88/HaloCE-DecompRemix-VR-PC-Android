# Test40 requirement disposition

This is the current source-scope record for the four items previously listed
as unfinished. It separates implemented bounded behavior from broader
compatibility and device acceptance.

| Requirement | Test40 status | Remaining limitation / evidence |
|---|---|---|
| Arbitrary custom NPC rigs | Partially implemented as an opt-in, solo-only fallback for unclassified humanoid records with a valid native graph, pelvis and split hierarchy. Standard actor classes preserve their existing path. | The engine has a fixed 16-value actor enum and no arbitrary bone-retarget/profile registry. Do not claim every custom rig works. Unknown race, non-humanoid, invalid or differently indexed graph/collision assets are refused. Device testing with real custom CE tags remains pending. |
| Persistent discarded magazines | Implemented for supported magazine profiles as map-session visual debris: gravity, native swept sphere collision, current world pass, fixed 32-item pool, oldest recycled only when full. | No pickup/ammo entity, save persistence, multiplayer replication, spin simulation or arbitrary weapon profile. Save/checkpoint loads and map lifecycle reset visuals. Verify stereo depth and Quest performance. |
| Whole-vehicle lifting | Implemented as optional bounded vertical lifting through the existing vehicle physics update. | Not full six-degree-of-freedom manipulation. No horizontal carry, rotation, throw or handle steering. Only unoccupied unnamed Warthog/Ghost/Scorpion/turret with valid physics; WORLD GRAB required; offline only. Device acceptance pending. |
| Automatic mission-NPC rescue | Implemented as optional ten-second recovery to a cached grounded pose after downward unsupported/out-of-map state, with standing-capsule clearance and encounter validation. | No revive/respawn or script-goal rewrite. Script-owned, dead, flying/swarm, cinematic, seated, custom-animation or invalid-capsule cases stay native. Device testing across missions/checkpoints remains pending. |
| Interaction/lifting haptics | Existing acquisition, reload, parkour and fingertip collision-contact pulses are retained. Optional `WEIGHT HAPTICS` now also covers held props, supported NPC limbs and vehicle lifting with the shared amplitude cap and per-hand rate limit. | OFF by default and solo-only. Confirm comfort and left/right behavior on headset; collision haptics stay transition-based rather than continuous. |
| Existing Test39 features | Carried forward; defaults and networking are unchanged. | Re-run regression suites and both flavor builds; owner device testing remains pending. |
| PC / Steam Frame | Deferred by request. | No PC or Steam Frame port work in this candidate. |

All new controls default OFF. None of the new physics or NPC actions runs in
network games. Host checks do not prove headset comfort, native collision
quality, all custom content, or mission-script safety in every campaign state.
