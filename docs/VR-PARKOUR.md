# Optional VR parkour

Source implementation and automated checks are available; headset acceptance is
pending. Wallrunning, walljumping and grip climbing are independent **off by
default** options in VR Controls. They currently operate in local games only.
Network games preserve stock player movement and send no custom movement packets.

## Controls and tuning

- **WALLRUN:** move and jump beside a vertical wall while maintaining movement
  input. The character follows the wall tangent with reduced downward speed for
  a limited time. `WALL SPEED` is a 1–2x multiplier on entry speed, bounded to
  7 m/s; it does not multiply speed again each tick. `WALL TIME` is 0.5–3 seconds.
- **WALLJUMP:** press Jump anew while airborne next to a wall or while gripping
  one. The leap follows the headset's look direction with an outward component
  and upward lift. `WALL LEAP` scales it from 0.5–1.5. Holding Jump does not repeat
  it. One jump per wall is allowed until landing or reaching a substantially
  different wall; the same wall cannot provide unlimited repeated boosts.
- **GRIP CLIMB:** press a free hand's grip within 10 cm of a vertical collision
  surface. Pull your hand to move your body while that hand stays visually on
  the surface. The normal capsule collision still stops walls and ceilings.
  Either free hand can hold; both can share the load. The hand holding a gun
  cannot also grab a wall. Release grip to let go. Pulling then releasing can
  launch you, scaled by `CLIMB LAUNCH` (0–1.5; zero disables the launch impulse).

Climbing uses map structure and scenery collision. Moving scenery invalidates
the grip; moving vehicles, NPCs, uncollidable art, floors and ceilings are not
climbing anchors. Lost tracking or focus releases ownership without turning
that loss into an arm-launch gesture. Reload/world/vehicle grip ownership is
respected. Existing Jump mappings and movement input are used directly.

## Implementation and evidence

The hook is inside `biped_update_physics`, after native desired motion/gravity
and before its capsule sweeps. It changes only the proposed velocity; native
wall, ceiling, floor and body collision, collision response and landing state
remain responsible for final position. No teleport, noclip/flying flag, or
global biped tag change is used. Native velocities are per tick, so tuning in
metres per second is converted with the current VR units and tick rate.

Wallrunning uses up to four short body probes per tick while enabled. Climbing
uses six short probes only on a fresh grip, then follows the cached static
anchor with bounded native velocity. Grips have reach limits; climbing speed
is capped at 4 m/s, arm-launch contribution at 8 m/s and combined departure at
10 m/s. Disabling all parkour adds no collision queries and does not change
normal proposed motion. Map/checkpoint loads, death, seats, cinematics, input
inhibition, focus loss, configuration disable and controller ownership changes
release transient state. Grounding and meaningful wall changes rearm the
bounded jump/run state.

The source audit caught an important native API detail: structure collision
results do not assign `object_index`. Parkour initializes optional fields and
checks result type before any object lookup. A poisoned BSP-index regression
fixture proves that a structure grip does not dereference that field.

`tools/test_vr_parkour.py` compiles the production module with controlled engine
fixtures under AddressSanitizer and UndefinedBehaviorSanitizer. It checks
disabled/network isolation, BSP metadata, grip ownership/focus transitions,
weapon-hand exclusion, climb/release, timer exhaustion, stable speed multiplier,
strafe direction, fresh-edge walljump, same-wall exhaustion, and finite limits.
The full module and biped hook also compile with the Android guest ABI.

## Device checks still required

Test both handednesses and every toggle separately, then together: wall approach,
corners, ceilings, ledges, sloped surfaces, variable height/radius, one/two hand
climb, arm release, jump off in different look directions, weapon switching,
reload/grab ownership, tracking interruption, pause, death, seat entry, checkpoint
and map transitions. Compare normal locomotion with options off and confirm
network play stays native. Record comfort, collision and frame timing before
calling the feature headset-accepted.
