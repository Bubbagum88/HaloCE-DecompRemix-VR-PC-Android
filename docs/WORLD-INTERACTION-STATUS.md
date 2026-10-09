# World interaction implementation and acceptance status

The Test38 interaction foundation carries into the private Test40 candidate. Optional loose-object interaction, articulated NPC handling, and the four Test40 additions are OFF by default. Source implementation and automated checks cover only the bounded paths below; headset, campaign and real multiplayer acceptance are still required. This document does not claim universal NPC support or that every original acceptance scenario has passed.

## Delivered architecture

- Loose weapons/equipment retain native item gravity, collision, angular integration and inventory ownership. Grabbing changes bounded velocities rather than teleporting objects. Eligible scenery uses the separate conservative OBB prop solver and an exact eight-tag allowlist (Covenant storage, human barricades and fallen trunks); arbitrary map scenery stays static.
- Native `acceleration_scale` is an impulse-response multiplier, not kilograms. Prop size classes and NPC species mobility are explicit gameplay strength tuning, not measured physical masses.
- NPCs use a new bounded articulated solver, actual animation-graph hierarchy, native authored hinge/axis/range semantics, swept joint spheres, self-collision and native collision-authoritative root movement. Captured limb palettes reach collision/child consumers before native weapon IK can overwrite them. The adapter preserves the native mixed coordinate-space semantics rather than assuming generic cone angles reproduce authored constraints.
- Living Grunts, Jackals, Marines and Crew permit one-hand handling. Elites, Hunters, Combat Forms and Carrier Forms require two distinct limb grips. The first heavy grip reserves contact but does not freeze the actor. Existing corpses use the same proven species information or an unambiguous loaded actor-variant reference; unidentified corpses are refused. Flying/swarm units and unusable rigs are excluded.
- Held actors retain their AI/perception/team/inventory metadata. Transient movement and trigger controls are suppressed after native persistent-control processing. Active weapon actions, scripted/named/seated actors and unsafe animation states are refused. Death does not revive an actor: it transitions to corpse handling. Live release settles, selects an available native front/back get-up, and blends through collision-aware recovery. Corpse release returns to native corpse settling without calling resurrection.
- Up to four independent articulated bodies remain active, configured from one to four. Each body has at most 64 nodes, two pins and eight constraint passes; collision sweeps occur after the constraint pass rather than at every iteration. Timing is aggregated in logs. Quest performance and comfort remain device acceptance items.
- Confirmed native collision contacts can produce capped, debounced host-authoritative impact damage through the native melee damage definition. Relative normal speed and mobility determine the bounded scale. NPC floor impacts retain native falling damage; the added NPC path handles confirmed nonfloor impacts, avoiding a second floor-damage event.
- Enhanced campaign sessions negotiate an optional interaction capability. The host validates player ownership, finite/range-limited input, session sequence and leases, and alone simulates root physics and damage. Both flat Android and VR hosts support that authority. NPC palettes are interpolated on upgraded clients with bounded bandwidth and lease expiry. Stock/mixed sessions retain their original behavior; enhanced NPC handling is not silently activated there. Legacy campaign protocol compatibility is a separate feature.
- Save/load, map changes, tracking/focus loss, player death, vehicle entry and invalid ownership cancel transient holds. Before saving, live ownership is released; no frozen AI flags or solver format are added to checkpoints.

## Test40 additions

- **Custom NPC rigs:** `vr.custom_npc_rigs` admits a validated unclassified
  humanoid fallback in solo play. It uses the loaded graph and pelvis split;
  it is not an arbitrary skeleton retargeting registry. Known native actor
  species retain their prior profiles, and unknown/non-humanoid/scripted or
  malformed graphs stay refused.
- **Discarded magazine visuals:** `vr.dropped_magazines` is a render-only,
  offline option for supported manual-reload magazine profiles. It uses a
  fixed 32-slot pool with no timed expiry and replaces the oldest when full.
  Map and game-state loads clear the visuals; they are not ammo, saved objects
  or network messages.
- **Vehicle lifting:** `vr.vehicle_lift` also requires `vr.world_interaction`.
  It applies a capped vertical velocity response through native vehicle
  acceleration for unoccupied, unnamed Warthog/Ghost/Scorpion/turret classes.
  Native collision and gravity remain active. No horizontal carry/rotation or
  network mutation is used.
- **NPC rescue:** `vr.npc_rescue` watches eligible encounter actors in solo VR.
  After ten seconds of downward unsupported/out-of-map state, it moves an NPC
  only to a recorded grounded pose with a clear full standing capsule. It does
  not reset the biped or rewrite AI/mission goals; active scripted, dead,
  flying/swarm, cinematic, seated and unsafe actors are refused.

## Requirement matrix

“Implemented” below means source paths and focused automated coverage, not headset acceptance. Partial rows name their actual limits.

| ID | Requirement | Current disposition |
|---|---|---|
| W1 | VR setting | Implemented: separate persistent object/NPC toggles, OFF by default; explicit enhanced-session permission. |
| W2 | Physical world grabbing | Implemented for loose weapons/equipment and eight audited scenery tags; arbitrary scenery excluded. |
| W3 | Grab detection | Actual collision surface and line-of-sight, bounded proximity acquisition and fresh grip edges. |
| W4 | Arbitrary surface points | Local object/limb surface anchors follow the object's transformed frame. |
| W5 | Spartan strength | Bounded springs, velocities and explicit species/size strength tuning; no kilogram claim. |
| W6 | Weight classes | Native item mobility, prop size classes and eight supported NPC species classes. |
| W7 | Two-handed grabbing | Two anchors for objects; heavy NPCs require distinct limb grips. |
| W8 | NPC interaction | Active articulated handling for the supported biped classes above. |
| W9 | Small enemies | Grunt/Jackal single-hand admission, constrained limb contact and release. |
| W10 | Large enemies | Elite/Hunter/Combat/Carrier two-hand requirements and lower mobility. |
| W11 | Friendly NPCs | Marine/Crew supported without changing diplomacy; scripted actors remain protected. |
| W12 | Ragdolls | New articulated solver, authored joint adapter, self/world collision and bounded pool. |
| W13 | Live ragdolls | Live control/palette/root ownership integrated; no rigid corpse substitute. |
| W14 | Recovery | Settling threshold and swept blend back to available native animation; blocked recovery waits. |
| W15 | Front/back recovery | Pelvis orientation selects verified available native animation without resurrection side effects. |
| W16 | AI restoration | Native metadata retained; transient interception ends with ownership. No perception deletion. |
| W17 | Scripted NPC safety | Named, recorded/custom animation, seated, command-script and other unsafe actors refused. |
| W18 | Throwing | Measured directional hand velocity, bounded native release; cancellation never manufactures a throw. |
| W19 | Trajectory | Three-axis momentum and native gravity/collision retained. |
| W20 | Impact damage | Confirmed collision-driven, native damage event, authoritative queued application. |
| W21 | Speed/mass scaling | Relative normal speed and mobility classes; not calibrated mass simulation. |
| W22 | Damage tuning | Threshold, cap and per-target debounce; subordinate to optional interaction modes. |
| W23 | Objects as weapons | Eligible held/thrown objects submit actual collision contacts to the impact path. |
| W24 | NPC impacts | Confirmed NPC nonfloor contacts can damage through the same authority path. |
| W25 | Ground slams | Physical downward motion; native NPC falling damage retained, no duplicate custom floor event. |
| W26 | Wall impacts | Swept constraints plus confirmed nonfloor impact path; no through-wall teleport. |
| W27 | Living resistance | Species mobility and two-hand gates implemented; no bespoke struggling animation system. |
| W28 | Controller stability | Tracked poses unchanged; constrained visible hands follow accepted contact. Comfort pending. |
| W29 | NPC hand pose | Limb-local contact accessor feeds visible hand placement; shared finger contact remains separate. |
| W30 | Biped grab points | Actual collision node maps to native rig; distinct heavy-limb requirement. |
| W31 | Stability | Finite/count/time guards, bounded forces, transactional solver rejection and recovery sweeps. |
| W32 | Release safety | Ownership-aware release, no throw on focus loss/reset, fresh grip required. |
| W33 | Multiple objects | Independent hand/object transactions and up to four continuing NPC bodies. |
| W34 | World weapons | Native loose weapons; pickup ends invalid hold; no duplication or new inventory shortcut. |
| W35 | Equipment | Eligible loose equipment; detonating projectiles/counter duplication excluded. |
| W36 | Vehicles/huge objects | Test40 adds default-off vertical lifting for a validated, unoccupied subset; no horizontal carry or rotation. |
| W37 | World collision | Native items, conservative prop OBB and swept NPC joint spheres; no universal mesh nonpenetration claim. |
| W38 | Player collision | Native root collision retained; closer-contact margin is separately guarded by capsule clearance. |
| W39 | Multiplayer | Native item state plus optional explicitly negotiated enhanced campaign channel. |
| W40 | Competitive play | Enhanced physical mutation disabled; stock PvP behavior preserved. |
| W41 | Co-op | Host/local and validated upgraded-client requests supported by common flat/VR host authority. |
| W42 | Mixed clients | Capability gate keeps unsupported enhanced NPC behavior off; stock functionality retained. |
| W43 | Enhanced co-op | Optional capability, validated hand requests, authoritative NPC palettes and leases implemented. |
| W44 | Authority | Host validates and simulates; clients do not author native object state. |
| W45 | Damage authority | Only authoritative simulation creates collision damage; no client-declared hit acceptance. |
| W46 | Desync recovery | Input/pose leases, session guards, invalid-object cancellation and native root replication. |
| W47 | Saves/checkpoints | Before-save cancellation, before/after-load and map resets; no save-format extension. |
| W48 | Cutscenes | Input/cinematic eligibility cancels holds and protects scripted actors. |
| W49 | Vehicle entry | Invalid seated/player-parent state releases interaction ownership. |
| W50 | Player death | Invalid/dead owner cancels; NPC death retains corpse semantics. |
| W51 | Teleport/reset | Hand-jump, unit, tick and lifecycle guards cancel without throwing. |
| W52 | Performance | Fixed-size arrays, bounded queries and timing logs; no headset performance claim. |
| W53 | Budget | 64 nodes/body, eight passes, two pins, bounded acquisition and network bandwidth. |
| W54 | Ragdoll count | Configurable one to four; released bodies retain their slot until recovery/settling. |
| W55 | Debug tools | Logs and sanitizer harnesses; force/constraint visual overlay not implemented. |
| W56 | Logging | Ownership/transition and aggregate simulation timing; avoid per-render spam. |
| W57 | Automated checks | Real extracted production lifecycle/species/pool functions, solver sanitizers and guest compilation. |
| W58 | Device checklist | Test40 checklist is recorded; all physical/campaign/network checks await owner testing. |
| W59 | Staging | Object foundation, solver, native ownership, recovery, impacts and negotiated network stages implemented. |
| W60 | Reload/fingers | Shared exclusive grip owners prevent overlap; visible contact hooks integrate with fingers. |
| W61 | Priority | Existing claims win; separate reload/vehicle/world/parkour/NPC ownership. |
| W62 | Haptics | Acquisition/reload/parkour feedback and one-shot fingertip collision pulses remain; optional, capped, rate-limited solo weight haptics cover held props, supported NPC limbs and vehicle lifting. Device comfort remains pending. |
| W63 | Game safety | No actor spawning/deletion, inventory edits or collision-disable workaround; admission guards preserved. |
| W64 | Out-of-bounds | Test40 adds optional local NPC recovery after a ten-second fall/outside-map dwell; no respawn/revive. |
| W65 | Enjoyment | Requires player feedback on strength, recovery, collisions and comfort. |
| W66 | Final acceptance | Test40 source coverage recorded; device acceptance remains pending, not implied. |

## Validation and remaining acceptance

`tools/test_vr_world_physics.py` exercises the actual spring/release/reset and articulated solver under AddressSanitizer/UndefinedBehaviorSanitizer, including 600-tick constraint/floor/recovery tests, 64-node self-collision budgets and invalid transaction rollback. `tools/test_vr_npc_interaction.py` extracts production species, ownership, pool, corpse classification, release, root velocity, snapshot and contact functions; it checks concurrent ownership, two-hand gates, round-robin snapshots, lifecycle and hook ordering. Both are registered in the project check runner. Actual guest compilation covers the NPC module in flat and VR plus modified native object, unit, biped and checkpoint hooks.

Compilation and focused checks cannot establish every authored rig's visual quality, every mission script's behavior, physical comfort, Quest frame-time cost or real multiplayer synchronization. Unsupported species/rigs, arbitrary static scenery, full six-degree-of-freedom vehicle manipulation, visual force diagnostics and automatic recovery of actively script-owned NPCs remain unsupported. Test40's bounded features are described above; owner device/campaign testing remains pending.
