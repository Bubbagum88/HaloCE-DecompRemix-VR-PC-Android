# Test42 current source disposition — 2026-10-09

This file preserves the original detailed M1-M29 / W1-W66 request matrix and
its investigation history. The old “Deferred — dependency W” cells below are
the initial pre-implementation status, not the current Test42 result. Use
[TEST42-REQUIREMENT-DISPOSITION.md](TEST42-REQUIREMENT-DISPOSITION.md) for the
current feature-by-feature source status and explicit remaining limits; use
[TEST42-DEVICE-CHECKLIST.md](TEST42-DEVICE-CHECKLIST.md) for owner runtime
acceptance. Test42 does not claim that every broad physical-interaction idea is
universal or device-verified.

## Current Test42 snapshot

Test42 carries the bounded Test38-41 implementations forward: profiled,
solo-only manual reload; local and consent/host-gated interactions; validated
custom humanoid graph fallback; map-session visual magazine debris; bounded
vertical lift of eligible vehicles; limited live-NPC fall recovery; configurable
reach, climb and rig slots; one master haptics control; and session diagnostics.
See the Test42 disposition for exact constraints, including no universal rig
retargeter, save-persistent/networked magazine objects, whole-vehicle carry or
rotation, native corpse-ragdoll-cap change, or universal NPC rescue. Those scope
limits are recorded explicitly; do not describe them as completed merely
because related toggles exist.

Test42 also adds Android-only touch-layout export/import and per-control
hide/restore in the existing HUD editor. The format is versioned and bounded;
old touch profiles remain visible by default. This does not change Quest VR
touch input or gamepad preferences.

---

## Historical Test41 source disposition (superseded by Test42 above)

The private candidate at that checkpoint was **Test41 / 1.0.22-test41 / code52**, based on OpenCE
Build157/network24. The owner reports that new interaction options appeared to
do nothing in a solo campaign. Test41 adds session/config diagnostics, a
12-40 cm reach used by world/NPC/parkour contact, mapping for broad NPC root
collision hits, and 16-direction horizontal climb probes. It labels the 1-8
pool slider **NPC RIG SLOTS** because that setting caps this mod's physical
interaction rigs, not Halo's native corpse-ragdoll limit. One HAPTICS setting
scales all vibration. The NPC fixture now executes production actor eligibility
instead of a permissive stub. See [TEST41-DELIVERY-STATUS.md](TEST41-DELIVERY-STATUS.md),
[TEST41-REQUIREMENT-DISPOSITION.md](TEST41-REQUIREMENT-DISPOSITION.md), and
[TEST41-DEVICE-CHECKLIST.md](TEST41-DEVICE-CHECKLIST.md). Automated checks do
not establish Quest action success; owner testing remains required. PC/Steam
Frame is deferred and public v1.0.18 remains unchanged.

Test40's retained scope includes graph-validated custom humanoid fallback,
map-session visual magazine debris, bounded vertical lifting of supported
vehicles, and delayed recovery for eligible live encounter NPCs. These are not
universal skeleton remapping, saved/networked magazine objects, full vehicle
rotation/horizontal carry, NPC revival or universal custom-tag compatibility.

---

# Historical Test38 source freeze and packaging override - 2026-10-08

The owner's latest usage-limit override is to finish current work and package
both private APKs now. This supersedes the earlier full-scope packaging hold.
Source is frozen; complete validation and packaging without feature expansion.
The original M1-M29 / W1-W66 requirements remain preserved below, including
historical instructions; they do not override this latest delivery decision.

Read [TEST38-DELIVERY-STATUS.md](TEST38-DELIVERY-STATUS.md) for the exact completed,
restricted, remaining and unstarted work. Seven manual-reload profiles,
world/NPC/ragdoll interactions and optional parkour are implemented with explicit
device checks pending. Campaign networks 15-24 use the normal compatibility path;
12-14 require the legacy opt-in. Enhanced co-op interactions support at most four
remote peers, independently of native co-op capacity.

Optional physical features retain native behavior in unsupported sessions.
Manual reload and parkour remain solo-only; enhanced network interactions need
a compatible, consenting host/peer set. No automated result establishes headset
acceptance or universal compatibility. Do not publish or install this candidate.

Evidence: TEST38-PROGRESS.md, WORLD-INTERACTION-STATUS.md, MANUAL-RELOAD.md,
TEST38-REQUIREMENT-AUDIT.md and TEST38-DEVICE-CHECKLIST.md. Historical deferred
statuses below are not the current disposition; consult the delivery status.

---

# Subsequent VR interaction requirements

Current source-pass update: M1–M29 have been worked through with evidence and
explicit remaining device checks in MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md.
The earlier dependency/packaging history below is preserved; it is not the current
source status. Latest pouch override uses independent hip/shoulder toggles on the
free-hand side. No headset acceptance is inferred from source tests.

## Latest owner packaging override — 2026-10-07

The owner subsequently requested BOTH APKs once the full OpenCE in-game menus,
turret fixes, window setting and upstream/network upgrade are finished and
validated, **before** beginning the manual/world interaction phase. That narrow
baseline delivery is now authorized. It does not finish, cancel, or waive any
M/W item below. Keep these workstreams queued and tracked for the next phase.

### Earlier hold (superseded for the baseline delivery above)

Do not package or deliver either APK until **all three task prompts** have been
worked through in full. A passing test31 baseline alone does not clear this
hold. This supersedes the earlier instruction to deliver test31 before starting
these additional workstreams. Keep implementation sequential: baseline fixes
and menus, manual reload/hand contact, then world interaction/NPC handling.
Device acceptance remains pending until the eventual combined candidate is
tested; do not make prior device acceptance a circular prerequisite for doing
the remaining authorized source work. Complete available source/build/test
validation between subsystems instead.

Acknowledging a row or recording an initial dependency does not complete it.
Investigate each dependency and resolve what can be resolved. Any genuinely
unsupported behavior or remaining external dependency requires specific evidence
and an explicit disposition before the packaging decision. No unsupported
feature may be presented as implemented.

Owner requests received after test31 began. **Order: finish and validate test31,
then manual reload/finger architecture investigation and reported plan, then
world-interaction investigation and reported plan.** No new feature here is
implemented or accepted yet. Do not introduce architecture changes before the
required investigation/plan. Work one subsystem at a time; preserve classic
behavior with optional interaction settings OFF by default.

Statuses below are initial dependency deferrals, not final dispositions. Each
row must acquire investigation evidence, implementation/partial/not-viable
decision, automated evidence, and explicit device/network acceptance status
before its workstream can be declared complete. Full request text is retained
in private work records; headings provide stable requirement IDs.

## Manual reload and finger/palm interaction

Dependency M: completed/stable test31, then inspection of reload/ammo authority,
weapon models/nodes/animations, current hands/collision/haptics and interaction
priorities. Report the plan and limits before architecture changes. Start with
AR, expand deliberately. Preserve both left shoulder and left hip grip-only
retrieval, both weapon hands, spatial magazine insertion, ammo conservation,
all interruptions/resets, classic fallback, and standalone performance.

| ID | Requirement | Status | Evidence / next dependency |
|---|---|---|---|
| M1 | Optional manual weapon reloading | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M2 | Physical magazine retrieval | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M3 | Magazine models | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M4 | Magazine removal from the weapon | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M5 | Magazine insertion | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M6 | Weapon state and ammunition synchronization | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M7 | Charging handle / cocking / chambering interactions | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M8 | Weapon-specific interaction definitions | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M9 | Two-handed weapon interaction during reloading | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M10 | Reload cancellation and edge cases | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M11 | Haptic interaction pass | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M12 | Improve finger interaction with world surfaces | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M13 | Per-finger contact behavior | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M14 | Continuous finger solving rather than binary poses | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M15 | Joint-level finger behavior | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M16 | Collision probes | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M17 | Prevent visible penetration | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M18 | Contact smoothing | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M19 | Palm interaction | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M20 | Hand positional compliance | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M21 | Finger contact haptics | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M22 | Interaction with grab poses | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M23 | Interaction with weapons and magazines | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M24 | Left/right hand parity | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M25 | Performance requirements | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M26 | Debugging facilities | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M27 | Automated tests where realistic | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M28 | Device-test checklist | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |
| M29 | Implementation strategy | Source pass complete; device checks pending | See MANUAL-RELOAD.md and TEST38-REQUIREMENT-AUDIT.md for exact implementation, tests and limits. |

## World interaction, NPCs, ragdolls and impacts

Dependency W: prior assigned work, followed by architecture investigation W59
phase A. Generic props must be verified before two-hand objects or live NPCs;
start NPC work with Grunts, then recovery/AI/damage before expanding classes.
Networking follows stable local behavior. Stock OpenCE wire checks and avatar
messages remain intact. PvP stays disabled unless synchronized fairness and
compatibility are demonstrated. No articulated-ragdoll capability is assumed.

| ID | Requirement | Status | Evidence / next dependency |
|---|---|---|---|
| W1 | VR setting | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W2 | Physical gripping of world objects | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W3 | Grab detection | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W4 | Grabbing from arbitrary points | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W5 | Spartan strength | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W6 | Weight classes | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W7 | Two-handed physical grabbing | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W8 | NPC physical interaction | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W9 | Small enemy grabbing | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W10 | Larger enemy grabbing | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W11 | Friendly NPC interaction | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W12 | Ragdoll system | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W13 | Live ragdoll behavior | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W14 | Dynamic recovery | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W15 | Recovery pose selection | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W16 | AI state restoration | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W17 | Scripted NPC safety | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W18 | Physical throwing | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W19 | Throw trajectory | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W20 | Impact damage | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W21 | Speed-based and mass-based damage | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W22 | Damage caps and tuning | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W23 | Object-as-weapon interaction | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W24 | NPC-to-NPC impacts | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W25 | Ground slams | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W26 | Wall impacts | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W27 | Grab resistance for living NPCs | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W28 | Avoid controller instability | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W29 | Hand pose while grabbing NPCs | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W30 | Grab points on bipeds | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W31 | Constraint stability | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W32 | Object release safety | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W33 | Multiple object interactions | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W34 | Grabbing weapons from the world | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W35 | Grenades and equipment | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W36 | Vehicles and extremely large objects | Test40 adds default-off, local vertical lifting for a validated unoccupied native subset. | No horizontal carry/rotation, boats/aircraft, named/scripted/occupied or network vehicles; see TEST40 disposition. |
| W37 | World collision | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W38 | Player-body collision considerations | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W39 | Co-op and multiplayer compatibility | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W40 | Competitive multiplayer | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W41 | Co-op support | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W42 | Mixed-client co-op | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W43 | Port-only enhanced co-op features | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W44 | Authority | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W45 | Damage authority | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W46 | Desync recovery | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W47 | Save/checkpoint behavior | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W48 | Cutscenes | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W49 | Vehicles | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W50 | Player death | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W51 | Teleport/recenter/state reset | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W52 | Performance | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W53 | Physics budgeting | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W54 | Maximum active ragdolls | **Implemented for the mod's articulated NPC interaction rigs:** `NPC RIG SLOTS` exposes 1–8 simultaneous active interaction/settling/recovery rigs, default 8 for new configs. | This is not a change to Halo's native corpse-ragdoll limit or garbage-collection policy. The engine retains corpse lifetime/count behavior; device performance at eight mod rigs remains a headset acceptance item. |
| W55 | Debug tools | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W56 | Logging | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W57 | Automated testing | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W58 | Device test plan | Test40-specific device checklist is written; execution pending owner testing. | Automated test/build results are not headset, mission or network acceptance. |
| W59 | Recommended implementation order | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W60 | Interaction with the previously requested manual reload and finger systems | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W61 | Interaction priority model | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W62 | Haptics | Test41 routes acquisition, reload, parkour, fingertip contact and bounded local load feedback through one master `vr.haptics` strength setting. | 0 disables every effect; higher values scale all effects. Load feedback remains rate-limited and local-only. Device strength/comfort acceptance remains pending. |
| W63 | Avoid game-breaking behavior | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W64 | Out-of-bounds protection | Test40 adds default-off local recovery of eligible live encounter NPCs after sustained unsupported falling. | Ten-second dwell; only a last-grounded position with a clear standing capsule; no respawn/revive or active-script takeover. |
| W65 | Physical interaction should remain fun | Deferred — dependency W | Investigate after preceding work; no physical/network evidence yet. |
| W66 | Final acceptance requirement | Source and automated checks recorded for Test40; owner device/campaign acceptance pending. | Do not advance accepted/public pointer until explicit owner acceptance. |

## Evidence required at delivery

Preserve both complete device checklists: M28 (52 checks) and W58 (70 checks).
They cover settings, both-hand interactions, authentic magazine/charging poses,
independent fingers/palm compliance, nonpenetration, throws/mass, NPC species,
recovery/AI/scripts, discrete authoritative impact damage, collision filtering,
checkpoint/death/cutscene/vehicle/tracking cleanup, Quest frame times and mixed
Quest/Android/stock-OpenCE sessions. Compilation is not physical acceptance;
simulations are not multiplayer acceptance. Revisit every row in the final
workstream report, including unsupported entities and explicit dependencies.
