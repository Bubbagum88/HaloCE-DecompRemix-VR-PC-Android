# Test58 checklist (vehicle controls fix after Test57)

Sources: the owner's Test57 session (`halo_log_2026-10-11_21-03-46`,
`..._21-04-41`, video 21:02:11) and messages: the Warthog's virtual wheel and
any way to steer the tank were missing; reticles jittery with immersive
vehicles; the virtual wheel must follow the vehicle itself, everywhere; the
tank view is liked as it is (a hatch view only as a toggle). Columns:
**Implemented**, **Automated** (host check), **Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test58 |
|---|---|---|
| `immersive warthog steering wheel not taken by hand 0: 53998.0 cm away` (every squeeze) | `object_marker.node_matrix` is the marker's offset from its node (`model_get_marker_by_name`: `matrix4x3_from_point_and_quaternion(&node_matrix, &instance->translation, ...)`), not the node; Test56/57 used it as the wheel's world centre, so the wheel sat ~2 m from the map origin | The wheel node itself (`nodes[marker.node_index]`), kept in the vehicle's frame, placed on the vehicle as drawn |
| `immersive scorpion drive stick not taken by hand 1: 227.2 cm away` | The stick sat between the driver's hand markers, inside the hull | Stick and Banshee bar 35 cm ahead of / 40 cm below the eyes |
| Scorpion view inside the hull (video) | Seat built for the chase camera | Unchanged (owner likes it); TANK HATCH option, off |
| Jittery reticle with immersive vehicles | Head aims; the mounted gun's preview ray moves on 30 Hz ticks from the ticked vehicle | Ray turned by the head's turn since the tick (≤ 11°), origin on the drawn vehicle |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Warthog wheel on the vehicle | Wheel node world matrix; vehicle-frame anchor; drawn pose each frame | test_test57b_vehicle_anchor (5 places/headings/tilts; old line restored fails at 566 m) | See and grab the wheel on two maps |
| Stick / bar reachable | Chest anchor for Scorpion/Wraith/Banshee | test_test57b_vehicle_anchor | Grab the stick and the bar |
| Out-of-reach / missing markers | Over 1 m from the eyes or no markers → chest anchor, logged; never placed from a head outside the vehicle | test_test57b_vehicle_anchor | — |
| Anchor log | `anchored at <where>, <n> cm from the eyes` | test_test57_vehicles | Read the log |
| Steady reticle | Head turn since the tick applied to the mounted ray; drawn-vehicle origin; only with the immersive controls | test_test57_vehicles | Ghost, Banshee, Scorpion reticle |
| TANK HATCH | Ray onto the tank's own hull above the head; eyes 12 cm over it; eased; tanks only; off by default | test_test57_vehicles | Optional |
| Keep working | Ghost handlebar placement unchanged; normal vehicle controls unchanged; no protocol change | full suite | Regression list |
