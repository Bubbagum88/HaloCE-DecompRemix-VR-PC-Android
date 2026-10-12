# Test38 hand contact and closer interaction

## Implemented behavior

- Five independent fingers retain the existing three-joint ancestry-based pose
  solver, including mirrored controller/weapon-hand mapping.
- Native collision features are collected around the hand once per pose and
  reused for candidate finger poses. Inflating those features by 5 mm gives
  finger segments volume against level geometry and moving objects. The held
  first-person gun retains its separate capsule approximation.
- The enclosing hand volume comes from actual joint lengths, including the
  existing terminal-finger extension. Invalid or unusually large hands and
  dense feature sets above 96 features use the established ray implementation.
  No incomplete/truncated feature cache is treated as proof of clearance.
- Contact search checks intermediate poses even when both extreme poses are
  blocked, then refines a clear interval. It uses at most eight candidate poses
  per colliding finger, preserving the previous direction where possible. If
  nothing improves clearance, it retains the input pose instead of forcing a
  fully curled finger. This is a bounded search, not a guarantee that every
  possible concave mesh has a collision-free hand pose.
- Existing release smoothing and palm-volume contact remain. A second eye at
  the same pose time no longer resets contact history. Unit, graph and explicit
  map/checkpoint epochs invalidate cached contacts.
- Hand contact produces one short haptic pulse on entry. It needs 80 ms clear
  before rearming; resting against a surface does not buzz every rendered frame.
  Manual reload and steering retain their own action feedback.
- A deliberate reload/world/vehicle/parkour grip owns its finger curl; contact
  solving does not pry an intentional grasp open. A manually held magazine hand
  is not pushed away from the gun's approximate barrel capsule. A held world's
  item contact follows the collision-constrained item rather than the raw hand.

`CONTACT VOLUMES` allows returning to ray-based contact. `CONTACT LOG` enables
five-second aggregate query/gather/fallback/contact statistics. Logging occurs
in the control update, not inside per-eye collision queries. Both settings are
in the VR controls pages; normal diagnostic logging is off.

## Closer contact

The existing `CLOSE CONTACT` toggle and its small stock-radius reduction remain.
`GRAB CONTACT` adds `AUTO` (default), `OFF`, and `ON`. AUTO applies the adjustable
radius when world interaction is enabled; ON enables it independently; OFF
retains the prior close-contact policy. `BODY RADIUS` adjusts 18–60 cm, bounded
by the original tag radius. Default is 25 cm.

This adjusts the local player's real capsule, not an imaginary air gap. Its
height/feet relationship stays native, its radius stays nonzero, and ordinary
collision sweeps remain. Shrinking is immediate; expansion is at most 1 cm per
simulation tick and is refused while the proposed capsule overlaps geometry.
Saturated collision-feature queries also refuse expansion. Move into open
space to finish restoring a larger radius. No shared tag is edited.

Custom player radius is offline only. Network games retain their stock
movement/collision contract. The setting does not shrink other characters,
remove their hitboxes, or promise zero visual mesh overlap in every custom map.

## Validation and limits

`test_test38_contact.py` exercises production bounded search, intermediate
clearance, direction persistence, invalid values and haptic timing under
ASan/UBSan. `test_quest_vr_math.py` retains production finger joint, bone-length,
mirroring and continuous curl tests. `test_test38_close_contact.py` exercises
actual radius policy and state transitions with an occupied/free-space oracle;
native geometry queries still require device scenes.

Real headset comfort, moving/scaled custom geometry, total CPU frame time,
deep controller penetration and the complete M28 checklist remain device
acceptance items. The solver changes visual hand poses, not tracked hardware
or world hitboxes. It cannot force the player's physical hand to stop at a
virtual surface or guarantee exact contact with every rendered triangle.
