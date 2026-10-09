# Test40 implementation and validation status

## Candidate identity

Private candidate **1.0.21-test40 / Android code51**, based on OpenCE
Build157/network24. Public v1.0.18 remains unchanged. This candidate is for
owner testing only: no GitHub publication, installation or game launch is
authorized. PC/Steam Frame work remains deferred.

## Four outstanding requests addressed

| Request | Source implementation | Exact scope and limit |
|---|---|---|
| Custom NPC rigs | New default-off **CUSTOM NPC RIGS** option reuses the live animation graph and articulated solver only for unclassified humanoid actor records that pass graph, pelvis and branch checks. Existing species paths are unchanged. | Solo/local only. The fixed engine actor enum and asset data do not provide an arbitrary skeleton retarget map. Unknown races, swarm/flying/special actors, malformed graphs and online custom layouts remain refused. This is a conservative custom humanoid fallback, not universal custom-rig support. |
| Persistent discarded magazines | New default-off **DROPPED MAGAZINES** option clones supported ejected magazine subtrees as visual-only debris, with gravity and swept sphere collision. A 32-item fixed pool has no timed expiry; when full it recycles the oldest. | Requires manual reload and a supported rifle/pistol/sniper magazine profile. Local/offline only. Visuals last for the current map session; map and game-state load/reset clears them. They are not pickupable ammo, saved, or networked. No ammo or native weapon state is changed. |
| Whole-vehicle lifting | New default-off **LIFT VEHICLES** option adds unoccupied eligible vehicles to WORLD GRAB and applies a bounded vertical velocity response through native vehicle acceleration. Native gravity and collision remain active. | WORLD GRAB must also be enabled. Solo/local only; limited to unoccupied, unnamed, unparented Warthog, Ghost, Scorpion and turret classes with valid native physics. This lifts vertically; it does not horizontally carry, rotate, throw, or steer a vehicle. Boats, aircraft, scripted/named vehicles and network sessions retain stock behavior. |
| Automatic mission-NPC rescue | New default-off **NPC RESCUE** option tracks eligible encounter actors and, after ten seconds continuously falling unsupported or outside the map, returns one to its last grounded pose if the full standing capsule is clear. | Solo VR only. It does not respawn/revive, rewrite goals, reallocate encounters, or reset the biped. Players, dead/flying/swarm/seated/script-command/cinematic/custom-animation actors and actors without a validated encounter/squad or safe capsule are refused. It clears only translational/angular velocity and wakes the reconnected actor. |

## Haptics coverage verified in this pass

The existing **WEIGHT HAPTICS** toggle now applies its capped, 120 ms
rate-limited load pulses to eligible vehicle lifts and supported locally held
NPC limbs, in addition to held props. Haptics remain OFF by default and
solo-only. Existing acquisition pulses, reload/parkour event feedback, the
global **HAPTICS** strength control, and one-shot fingertip collision-contact
pulses are retained. The device checklist asks for both-hand and comfort
verification; source checks cannot establish headset feel.

All four controls default OFF and do not change the accepted baseline when
unused. Custom rig handling, visual magazines, vehicle lifting and NPC rescue
are local-only; they never claim multiplayer/co-op authority. The Test39
network, co-op, controller, Android touch, VR settings, reload, contact, scope,
vehicle controls, menus and avatar work remains carried forward.

## Validation and acceptance

Focused ASan/UBSan harnesses cover magazine pool policy and production hooks,
vehicle eligibility/velocity limits, custom rig profile admission, and NPC
rescue dwell/eligibility/lifecycle. Full regression suites, cache-format pytest,
flat/Quest compilation, signing and package checks are recorded in
[TEST40-DELIVERY.md](TEST40-DELIVERY.md) after packaging.

No device, headset, co-op, campaign, performance or representative custom-tag
acceptance is inferred from host checks. Follow
[TEST40-DEVICE-CHECKLIST.md](TEST40-DEVICE-CHECKLIST.md) before advancing the
accepted-build pointer. `runtime_accepted` remains false.
