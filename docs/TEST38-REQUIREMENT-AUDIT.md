# Test38 interaction requirement audit

This is a source audit, not headset acceptance. Reviewed against the original
manual-reload/hand-contact request and the later vehicle, parkour and closer-contact
requests. The master requirements ledger remains separate. Existing automated
results establish bounded logic; they do not establish comfort, visual quality,
frame time or interoperability on every server.

## Hand contact: M12-M29

| Requirement | Source disposition | Remaining limit / acceptance |
| --- | --- | --- |
| M12 surface interaction | Refined underlying contact search and native feature volumes in `vr_render.c`; not smoothing alone. | Alyx-like feel is a headset target, not a verified outcome. |
| M13 independent fingers | Five separate finger contacts and state histories; thumb/index/middle/ring/pinky ancestry discovered from model. | Controller ring/pinky input shares a requested curl; environmental responses are independent. |
| M14 continuous contact | Continuous curl/joint values, bounded intermediate-pose search and interval refinement. | Search is finite; concave geometry can have unsearched clear poses. |
| M15 multiple joints | Three joints per recognized finger, actual segment lengths and terminal extension. | Missing/invalid chains retain fallback; not articulated finger rigid bodies. |
| M16 probes | Native collision features inflated by 5 mm, gathered once per hand pose; reuse across candidate segments. Dense sets above 96 features use rays. Reload components use authored rigid-vertex bounds; held world/NPC fingers use only their object's native swept-pill collision. | Held main gun still uses a capsule approximation; component bounds are envelopes, not render triangles. |
| M17 penetration | Static and dynamic native collision types considered; surface entry reacts immediately. | No guarantee of zero penetration in all custom/scaled meshes; native collision may differ from rendered art. Deep controller penetration remains difficult. |
| M18 smoothing | Direction persistence, release smoothing and same-pose stereo history preservation. Epoch/unit/graph reset invalidates stale state. | No user-facing per-joint damping tuning; assess snapping and wall transitions physically. |
| M19 palm | Seven head-to-palm rays sample a volume; held-gun capsule pushout and sweep cooperate with world collision. | Approximation, not a fully swept convex palm. Intentional held-object/parkour poses use their own constrained target. |
| M20 positional compliance | CONTACT LIMIT 8–40 cm (default18): over-limit constrained arm/hand shrinks out coherently over80ms; returns below75% limit. Gun excluded, avatar pose captured before visual collapse. No wall-crossing teleport or severed wrist. | Transition is a bounded visual hide/reveal policy, not a physical controller constraint. Comfort and whole-body presentation require headset checks. Production cap/hysteresis fixture passes. |
| M21 contact haptics | Short contact-entry pulse, bounded amplitude and 80 ms clear rearm; held action modules have separate feedback. | Existing weapon/world-pressure feedback is a separate retained behavior. Evaluate combined haptic comfort. |
| M22 grip priority | Exclusive ownership prevents stealing. Reload fingers conform only to the held component; world/NPC fingers conform only to the owned native collider. Unrelated walls cannot pry a grip open; other owners retain their established poses. | Missing native colliders retain grip curl. Collision shapes can differ from art; each species/prop needs physical evaluation. |
| M23 held components | Real detached magazine/needle/charging mesh bounds drive palm/finger contact; component-held hand target guides onto bounds over80ms. Predicted tracking updates visuals; no detached-part scan in render. | Bounds are conservative; seven supported weapon profiles and both hands need headset contact checks. Production bound/trace/target fixtures pass. |
| M24 handedness | Per-controller state, weapon-hand selection, mirrored finger solver and two-hand ownership. Latest owner override: independent shoulder/hip toggles, automatically on the free-hand side. | Both toggle states and handedness sign tested; physical reach/seated ergonomics remain device checks. |
| M25 performance | Static storage, bounded search, cached per-pose feature collection and dense-query fallback; aggregate counters. | Quest CPU/frame-time measurement remains pending. Do not equate bounded work with verified frame-rate parity. |
| M26 diagnostics | Optional CONTACT LOG aggregates queries/gathers/fallbacks/contact maxima outside render queries; FINGER VOLUME selects ray fallback. | No new probe/axis/palm-plane visualization was found; original visualization list was optional. |
| M27 automation | Production solver math/hysteresis, finger joint/mirror and shared ownership; actual reload palette/bounds/trace, hand cap and owned-collider routing. Whole scenery module/native sync fixtures added separately. | Tests cannot validate full native collision scenes or physical feel. See individual feature documents for exact coverage. |
| M28 device checklist | Full original 52-step list preserved in `TEST38-DEVICE-CHECKLIST.md`, plus world checklist. | All physical steps remain pending until actually performed; unsupported cases must be marked with a reason, never passed silently. |
| M29 staged strategy | Separate reload/contact/vehicle/world/parkour modules and documented authored-tag investigation; real ammo path retained. | Source integration review is complete; completion of an automated helper does not complete device acceptance. |

See `TEST38-HAND-CONTACT.md`, `MANUAL-RELOAD.md`, and
`TEST38-SCOPE-VEHICLES.md` for source evidence and supported cases. M1-M11 reload
requirements have their own explicit disposition in `MANUAL-RELOAD.md`.

## Later vehicle requirements

- Optional physical handles are OFF by default (wheel visibility defaults ON
  within that optional mode) and apply
  only to first-person drivers. Ordinary steering remains selected when no hand
  is latched; stick throttle is preserved.
- Right/left physical grip edges claim hands exclusively. Seat changes,
  tracking/focus loss, recenter, death and invalid geometry release ownership.
- Warthog uses real wheel-grip markers; Ghost/Scorpion/Banshee use the authored
  seated cyborg hand pair, with missing-marker fallback. This is an explicitly
  virtual control, not a claim that every original cockpit contains a wheel.
- Vehicle-specific closed ring/yoke geometry uses native triangle rendering and
  UNSC/Covenant color families. Separate visibility toggle hides the control
  without disabling grabs. Reach, lateral, height and size settings move visual
  geometry and hand targets together.
- Preserved seated torso/legs plus arm IK support the held pose. Closed-mesh,
  steering bounds, angle wrap, two-hand release and fallback tests pass; actual
  cockpit appearance/reach/comfort and collision with the cockpit need testing.
- Mounted preview removes proven target attraction while retaining geometric
  convergence. Actual projectiles retain native targeting/spread. Residual
  simulation-rate stepping is not claimed fixed without headset evidence.
- All 11 gun-class scope profiles are configurable, including SPNKR and OTHER.
  This adjusts existing tag-defined zoom only; it does not give every gun zoom.

## Later closer-contact requirement

Implemented offline local-player capsule policy: GRAB CONTACT AUTO/OFF/ON,
AUTO with world grabbing, BODY RADIUS 18-60 cm (default 25 cm), never larger than
stock. Existing CLOSE CONTACT remains separate. Shrinking is immediate;
expansion progresses at up to 1 cm/tick only when the proposed native capsule
is clear. No global tag/NPC hitbox edits. This allows closer contact, not
wall-clipping or guaranteed zero art overlap. Occupied-space state tests exist;
real narrow passages, stairs, crouch and return-to-stock need device checks.

## Later parkour requirement

Current source provides three independent persistent OFF defaults: wallrun,
walljump and grip climb. It feeds native biped velocity before normal capsule
collision, with bounded speed/time/leap settings; no teleport or collision
bypass. Wallrun requires movement/jump context near vertical geometry;
walljump is look-directed with an outward component. Climbing uses free hands,
grip edges, planted visual hand anchors and release momentum. Interaction owners
exclude conflicting reload/vehicle/world grips.

This is offline local-player functionality. Network players, vehicles,
cinematics, dead units and disabled settings retain their normal paths. Static
BSP/scenery is the admitted wall surface set; moving-object climbing is not
promised. Lifecycle and numerical tests are separate from actual feel. Verify
wallrun duration, walljump direction, two-hand climb/release, recenter, checkpoint
load and collision under low frame rate on device before acceptance.

## Review findings for integration owner

The audit reported finite-center/joint validation and cache ignore-object
identity for finger volume queries, and palm relaxation during intentional
ownership. The owner corrected all three findings.
`test_test38_contact_volume.py` executes the production gather/cache function
under ASan/UBSan: NaN center/segments/units, identity and epoch changes, the
96/97 feature boundary, saturated lists and oversized hands. It passed. This
proves the guard/cache policy, not native collision scenes or device quality. The full physics/NPC integration is being reviewed by
its owner and is outside this bounded M12-M29 audit.
