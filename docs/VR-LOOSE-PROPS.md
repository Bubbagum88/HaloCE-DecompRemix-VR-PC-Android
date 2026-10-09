# Movable loose scenery

Source implementation; headset/co-op acceptance pending. WORLD GRAB remains
off by default. Untouched scenery retains its original native behavior.

## Supported stock assets

The supplied identical Original/Rev 1/Rev 2 map data was inspected across all
ten campaign maps and Blood Gulch. These authored loose objects have collision
models, zero native scenery acceleration, no physics tag and no animation graph:

- Covenant storage container and large storage container.
- Human barricade large, large gap, small and small visor.
- Fallen leafy tree trunk and short fallen trunk.

Only those exact stock tag paths are enabled. Named/scripted objects, animated
objects, parented objects, objects with children, no-collision objects and
structural trees/stumps remain ineligible. The A10 oxygen-tank fixture is not
treated as a loose prop. An unknown/custom scenery tag is not made movable
merely because its model looks small.

## Physics and interaction

The shared world-grip code chooses a real collision contact, retains one/two-hand
ownership and sends bounded linear/angular velocity. Native items still use
their existing item physics. Scenery is never cast to an item or vehicle.

At first grab, the scenery solver builds an oriented bounding box from its
actual active collision BSP vertices, transformed through the current collision
node matrices. Up to 64 modified objects are tracked; no geometry/object copies
or per-frame allocations are created. Large objects respond more slowly using
bounded radius-based mobility, since their stock tags have no physical mass.

Translation tests the swept box against native world/object polygons, spheres
and cylinders. Blocked diagonals resolve as separate swept axes so objects can
slide. Angular motion uses a conservative expansion based on distance from the
object origin to the farthest box corner, including offset centers. Saturated
collision feature lists reject motion. Gravity and bounded angular movement
continue after release until resting. Conservative bounds can require lifting
a large/concave prop farther from obstacles before rotating it; they do not
claim triangle-perfect rigid-body physics.

Impact normals come from the encountered authored plane or closest sphere/
capsule surface. Deep/degenerate contacts without an evidenced normal block
movement without fabricating impact damage. Normal damage authority and player
attribution remain in the shared impact subsystem.

External/scripted transform changes cancel this solver's ownership. Turning
WORLD GRAB off locally, or losing negotiated host compatibility, freezes
modified props at their last collision-safe transforms rather than teleporting
them back. Before saving, active prop velocities are zeroed and their native
object transforms are saved normally. Map/load reset clears transient state
without dereferencing stale objects; a restored prop can be grabbed again.

## Network behavior

Co-op host authority uses the existing OpenCE scenery/machine transform packet:
`COOP_MOVED_OBJECTS` already includes scenery. Native refresh continues carrying
previously moved objects to clients, including after custom grabbing stops.
The sender now notices up-axis changes as well as position/forward changes, so
rolling around an unchanged forward axis is transmitted. No competing custom
prop transform stream or new stock wire layout is introduced.

Interaction requests still require the shared capability/consent checks. A
stock/incompatible host does not gain custom physics from a joining VR client.

## Automated evidence

- `test_prop_collision.py`: SAT/capsule primitive edge, face, corner and finite
  guards used by the solver.
- `test_vr_world_props.py`: entire production module with counted native-query
  fixtures; eligibility, authored bounds, untouched baseline, floor sliding,
  wall tunneling rejection, saturated lists, authority changes, config-off and
  save freeze, script relocation, offset rotation bounds and impact normals.
- `test_prop_native_sync.py`: production native sender; pure roll, unchanged
  state, periodic refresh and parent exclusion.

Fixtures run under AddressSanitizer/UndefinedBehaviorSanitizer. They establish
source behavior, not headset comfort or live peer synchronization acceptance.
