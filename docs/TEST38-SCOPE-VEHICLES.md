# Test38 scope, mounted reticle and physical vehicle controls

## Source-backed reticle correction

Mounted reticles called `vr_preview_player_projectile`, which called native
`player_aim_projectile_internal` with target bookkeeping disabled but still ran
`aim_assist` and blended toward targets. Ordinary hand weapon reticles already
used convergence without this attraction. Mounted previews now use that same
non-attracting geometric convergence helper; real shots retain native autoaim,
spread and target bookkeeping. This fixes a demonstrated code path matching the
reported enemy snapping. Remaining simulation-rate motion needs headset review.

## Scope settings

All 11 gun classes have independent position and size profiles, including SPNKR
and OTHER/custom weapons. Legacy pistol/sniper keys and defaults are retained.
An adjustment changes an existing native zoom view; it does not invent zoom for
a weapon whose tags do not provide one. Profile table drives frame load, menu
and reset. Existing 30 cm adjustment bounds apply.

## Physical vehicle handle plan and evidence

Default OFF, first-person drivers only. No change to ordinary steering when no
hand is latched. Physical grip edge near native seated hand contact latches;
release, tracking/focus loss, recenter, seat change, death or invalid data clears.
Throttle remains on the stick. No host physics or protocol mutation.

Inspected private production-imported original XISO a10/b30 map tags using
`custom_edition_tag_footprints.Cache`; raw maps/metadata remain private. Cyborg
model has authored `left hand` and `right hand` markers on hand nodes 17/18,
with upperarm->forearm->hand chains. Warthog has `left hand wheel grip` and
`right hand wheel grip` on its authored steering-wheel node. Ghost has elite
handle markers but no universal cyborg pair; Scorpion has passenger hand
markers, not a driver pair; Banshee has no handle markers. Therefore fallback
for those vehicles must use the seated cyborg animation's actual hand markers,
never invented vehicle offsets. A missing marker or invalid chain disables
physical handles for that seat and preserves existing control.

Implementation will preserve the native seated torso/legs and adapt only free
arms, while held hands follow authored native driver-animation contacts. Virtual controls use angular hand displacement bounded to 60 degrees. Vehicle
profiles have distinct ring/yoke polygon geometry and UNSC olive/Covenant purple
colors. A separate visibility toggle hides only the visual, retaining grab
controls. Each profile has reach, left/right, height and size adjustments that
move both visible geometry and grab targets together. Native vehicle geometry
is unchanged; this is an explicitly virtual cockpit control.

The closed six-face bars use the native depth-tested triangle batch. Only eye
passes emit the mesh. The preexisting debug visibility flag is temporarily
saved/enabled for the batch then restored; the normal debug draw is performed
exactly once. The engine clears the debug batch in rasterizer_window_end, so
left/right eyes do not accumulate duplicated triangles. No render logging is
introduced; pending diagnostics are emitted by the input tick.

Tests execute real steering code for wrap, finite/zero inputs, two hands,
release/tracking/recenter ownership reset, 60-degree clamp and fallback. The
actual bar mesh is replayed and checked as a closed 6-face manifold (each edge
belongs to two faces). Scope tests execute all 11 profiles in both hands;
projectile tests prove actual shots retain attraction and bookkeeping while
mounted previews omit it. Guest VR objects compile. Physical device validation
is still required for reach/comfort, rendering and vehicle response.
