# Test57 checklist (final polish after Test56)

Sources: the owner's Test56 session (`halo_log_2026-10-11_19-56-20`, video
20:05:22: Blood Gulch Ghost, Warthog and Scorpion; `..._20-06-57`, video
20:07:02: the assault rifle close-up), the Test57 request, and later messages:
use a virtual Warthog wheel unless the model's can be guaranteed; refine the
Ghost; a hidden virtual wheel should line up with the real one; toggles for
anything applicable. Columns: **Implemented**, **Automated** (host check),
**Device** (Quest/phone only).

## Evidence

| Observation | Cause found | Test57 |
|---|---|---|
| Warthog wheel never taken: 50 s of driving, no `steering from the gripped controls` (owner: grip held) | The model's rim geometry checks out on the stock map (wheel node up axis toward the driver, rim ~15 cm); no miss was logged, so the cause could not be proved | A drawn virtual wheel; the grab region is the drawn wheel itself (face and rim, 12 cm reach); misses are logged with distance |
| Ghost grabs every time | — | Kept; centre tick and highlight added at the owner's request |
| 13 left-trigger presses in the Warthog | The trigger zooms (the Warthog driver has no zoom); grip is the grab | Unchanged; the guide says grip |
| AR "red dot" part | Stock `weapons\assault rifle\fp\fp`: node 31 "frame safety button"; idle/moving/firing hold it at (-0.0005, 0, 0.0247); "ready" starts it 0.0067 units in and ends there; overlays only sway it | As authored; no change |
| Scorpion view starts inside the hull | Seat camera built for third person | Not changed (no measured value); TANK UP/FWD; device check |
| Holster/pouch calibration | Triggers and markers share `holster_place` / `reload_pouch_place`, `heading_point`, the same radii and the same hip/shoulder enable rule | No change |

## Items

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Warthog virtual wheel | Drawn rim/spokes/hub/turn mark, 2.5 cm in front of the model's wheel; face grab (not the hub's middle); reach palm+8 cm; two hands averaged, either alone; VIRTUAL WHEEL hidden → grab on the model's wheel exactly | test_test38_vehicle_handles, test_test57_vehicles | Grab, turn, one hand, hidden |
| Scorpion / Wraith drive stick | One stick between the hands, tilted the way to go; knob grab; profile "drive stick" | test_test38_vehicle_handles | Drive the Scorpion |
| Banshee flight bar | Roll or slide (12 cm full lock) to turn; push/pull pitch; BANSH SLIDE | test_test38_vehicle_handles | Fly |
| Ghost | Steering and reach unchanged; centre tick; highlight | test_test38_vehicle_handles | Drive |
| Per-vehicle profiles | Name table (Warthog, Ghost, Scorpion, Wraith, Banshee), control name, reach | test_test57_vehicles | — |
| Haptics | Grab, turning ticks, centre tick, full lock, release; STEER HAPTICS | test_test38_vehicle_handles | Feel |
| Highlight | Controls lighten while a free hand is within reach; CONTROL GLOW | test_test57_vehicles | See |
| Hand poses | Fingers close around held controls over 0.12 s and ease back (Test56) | test_test56_polish | See |
| Transitions | Entering resets to the vehicle's profile, centred; exiting clears grips and claims | test_test38_vehicle_handles | Ghost → Warthog → Scorpion → Banshee |
| Normal controls | Nothing runs or draws without IMMERSIVE VEHICLE | test_test57_vehicles | Drive with it off |
| AR safety button | Verified against stock animations; unchanged | — | — |
| Ragdolls | Reviewed; unchanged (no safe, clear gain) | full suite | — |
| Holster calibration | Reviewed; consistent; unchanged | full suite | Quick look |
| Keep working | Voice code untouched; no protocol change; network 26 | full suite | Regression list |
