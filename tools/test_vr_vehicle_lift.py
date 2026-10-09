"""Exercise vehicle-lift math and guard its production integration path.

The compiled harness covers bounded helper behavior. Static assertions verify
the engine candidate gates, default-off option, native velocity path and
cancellation hooks. This cannot prove in-game collision feel or headset safety.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "port/linux/game/vr_vehicle_lift_math.h"
GAMEPLAY = ROOT / "port/linux/game/vr_world_interaction.c"
CONFIG = ROOT / "port/linux/src/port_config.c"
MENU = ROOT / "port/linux/game/vr_menu.c"
OUT = ROOT / "build/vehicle-lift-math-tests"
OUT.mkdir(parents=True, exist_ok=True)

source = r'''
#include <assert.h>
#include <float.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "vr_vehicle_lift_math.h"

static struct vr_vehicle_lift_candidate candidate(void)
{
    struct vr_vehicle_lift_candidate c;
    memset(&c, 0, sizeof(c));
    c.feature_enabled = 1;
    c.offline_session = 1;
    c.supported_vehicle_type = 1;
    c.valid_native_physics = 1;
    c.mass_point_count = 8;
    c.powered_mass_point_count = 2;
    c.native_mass = 100.0f;
    return c;
}

static void assert_zero(float const v[3])
{
    assert(v[0] == 0.0f && v[1] == 0.0f && v[2] == 0.0f);
}

int main(void)
{
    struct vr_vehicle_lift_candidate c = candidate();
    float current[3] = {0, 0, 0};
    float request[3] = {0, 0, 10};
    float one_hand[3], two_hands[3], impulse[3], force_cap, angular[3], release_linear[3], release_angular[3];
    struct vr_vehicle_lift_state state;

    assert(vr_vehicle_lift_eligible(&c));
    c.feature_enabled = 0; assert(!vr_vehicle_lift_eligible(&c)); c.feature_enabled = 1;
    c.feature_enabled = 2; assert(!vr_vehicle_lift_eligible(&c)); c.feature_enabled = 1;
    c.offline_session = 0; assert(!vr_vehicle_lift_eligible(&c)); c.offline_session = 1;
    c.supported_vehicle_type = 0; assert(!vr_vehicle_lift_eligible(&c)); c.supported_vehicle_type = 1;
    c.valid_native_physics = 0; assert(!vr_vehicle_lift_eligible(&c)); c.valid_native_physics = 1;
    c.parented = 1; assert(!vr_vehicle_lift_eligible(&c)); c.parented = 0;
    c.occupied = 1; assert(!vr_vehicle_lift_eligible(&c)); c.occupied = 0;
    c.destroyed = 1; assert(!vr_vehicle_lift_eligible(&c)); c.destroyed = 0;
    c.scripted_or_mission_owned = 1; assert(!vr_vehicle_lift_eligible(&c)); c.scripted_or_mission_owned = 0;
    c.mass_point_count = 0; assert(!vr_vehicle_lift_eligible(&c)); c.mass_point_count = 33; assert(!vr_vehicle_lift_eligible(&c)); c.mass_point_count = 8;
    c.powered_mass_point_count = -1; assert(!vr_vehicle_lift_eligible(&c));
    c.powered_mass_point_count = 9; assert(!vr_vehicle_lift_eligible(&c)); c.powered_mass_point_count = 2;
    c.native_mass = 0; assert(!vr_vehicle_lift_eligible(&c));
    c.native_mass = NAN; assert(!vr_vehicle_lift_eligible(&c));
    c.native_mass = INFINITY; assert(!vr_vehicle_lift_eligible(&c));
    c.native_mass = FLT_MAX; assert(!vr_vehicle_lift_eligible(&c));
    c.native_mass = FLT_TRUE_MIN; assert(!vr_vehicle_lift_force_cap(c.native_mass, 1, 1.0f, &force_cap));
    c = candidate();
    assert(!vr_vehicle_lift_eligible(NULL));

    assert(vr_vehicle_lift_target_velocity(current, request, 1, 1.0f, one_hand));
    assert(vr_vehicle_lift_target_velocity(current, request, 2, 1.0f, two_hands));
    assert(fabsf(one_hand[2] - 0.035f) < 1e-6f);
    assert(fabsf(two_hands[2] - 0.0525f) < 1e-6f);
    assert(vr_vl_length3(one_hand) <= 0.20 + 1e-7);
    assert(vr_vl_length3(two_hands) <= 0.20 + 1e-7);
    assert(!vr_vehicle_lift_target_velocity(current, request, 0, 1.0f, one_hand)); assert_zero(one_hand);
    assert(!vr_vehicle_lift_target_velocity(current, request, 3, 1.0f, one_hand)); assert_zero(one_hand);
    assert(!vr_vehicle_lift_target_velocity(current, request, 1, NAN, one_hand)); assert_zero(one_hand);
    current[0] = 0.201f;
    assert(!vr_vehicle_lift_target_velocity(current, request, 1, 1.0f, one_hand)); assert_zero(one_hand);
    current[0] = 0;
    request[0] = NAN;
    assert(!vr_vehicle_lift_target_velocity(current, request, 1, 1.0f, one_hand)); assert_zero(one_hand);
    request[0] = 0;

    assert(vr_vehicle_lift_target_velocity(current, request, 1, 1.0f, one_hand));
    assert(vr_vehicle_lift_force_cap(100.0f, 1, 1.0f, &force_cap));
    assert(fabsf(force_cap - 3.5f) < 1e-5f);
    assert(vr_vehicle_lift_impulse(current, one_hand, 100.0f, 1, 1.0f, impulse));
    assert(fabsf(impulse[2] - 3.5f) < 1e-5f);
    assert(vr_vl_length3(impulse) <= 100.0 * 0.035 + 1e-5);
    assert(vr_vehicle_lift_force_cap(100.0f, 2, 1.0f, &force_cap));
    assert(fabsf(force_cap - 5.25f) < 1e-5f);
    assert(vr_vehicle_lift_target_velocity(current, request, 2, 1.0f, two_hands));
    assert(vr_vehicle_lift_impulse(current, two_hands, 100.0f, 2, 1.0f, impulse));
    assert(fabsf(impulse[2] - 5.25f) < 1e-5f);
    assert(vr_vl_length3(impulse) <= force_cap + 1e-5f);

    request[2] = 0.201f;
    assert(!vr_vehicle_lift_impulse(current, request, 100.0f, 1, 1.0f, impulse));
    assert_zero(impulse);
    request[2] = 0.035f;
    assert(!vr_vehicle_lift_impulse(current, request, NAN, 1, 1.0f, impulse));
    assert_zero(impulse);
    assert(!vr_vehicle_lift_force_cap(FLT_MAX, 2, 99.0f, &force_cap));
    assert(force_cap == 0.0f);

    request[0] = 1.0f;
    assert(vr_vehicle_lift_angular_target(request, 1.0f, angular));
    assert(fabs(vr_vl_length3(angular) - 0.08) < 1e-6);
    request[0] = NAN;
    assert(!vr_vehicle_lift_angular_target(request, 1.0f, angular)); assert_zero(angular);
    request[0] = 0.2f;
    assert(vr_vehicle_lift_angular_target(request, 1.0f, angular));
    assert(fabsf(angular[0] - 0.024f) < 1e-6f);

    current[0] = 1.0f; current[1] = 0.0f; current[2] = 0.0f;
    request[0] = 0.0f; request[1] = 0.0f; request[2] = 0.0f;
    angular[0] = 0.0f; angular[1] = 0.2f; angular[2] = 0.0f;
    assert(vr_vehicle_lift_release(current, angular, 1.0f, release_linear, release_angular));
    assert(fabs(vr_vl_length3(release_linear) - 0.20) < 1e-6);
    assert(fabs(vr_vl_length3(release_angular) - 0.08) < 1e-6);
    current[1] = INFINITY;
    assert(!vr_vehicle_lift_release(current, angular, 1.0f, release_linear, release_angular));
    assert_zero(release_linear); assert_zero(release_angular);
    current[1] = 0.0f;

    memset(&state, 0x7f, sizeof(state));
    state.active = 1; state.object_index = 42; state.hand_count = 2;
    state.last_target_velocity[0] = 1.0f;
    assert(!vr_vehicle_lift_cancel(&state, VR_VEHICLE_LIFT_CANCEL_NONE));
    assert(state.active && state.object_index == 42 && state.hand_count == 2);
    for (int reason = VR_VEHICLE_LIFT_CANCEL_RELEASE;
         reason <= VR_VEHICLE_LIFT_CANCEL_DEATH; ++reason)
    {
        state.active = 1; state.object_index = 42; state.hand_count = 2;
        state.last_target_velocity[0] = 1.0f;
        assert(vr_vehicle_lift_cancel(&state, reason));
        assert(!state.active && state.object_index == -1 && !state.hand_count);
        assert_zero(state.last_target_velocity);
    }
    state.active = 1; state.object_index = 42;
    assert(vr_vehicle_lift_cancel(&state, 999));
    assert(!state.active && state.object_index == -1);

    puts("PASS: fail-closed eligibility; one/two-hand speed caps; angular target and bounded release; invalid/overspeed rejection; seat/map/session cancellation");
    return 0;
}
'''

binary_source = OUT / "vehicle_lift.c"
binary_source.write_text(source)
binary = OUT / "vehicle_lift"
subprocess.run(
    ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
     "-I", str(HEADER.parent), str(binary_source), "-lm", "-o", str(binary)],
    check=True,
)
subprocess.run([str(binary)], check=True)

# These helpers must remain independent of gameplay/network/transform APIs.
header_text = HEADER.read_text(encoding="utf-8").lower()
for forbidden in ("networking/", "distributed_send", "object_set_position", "vehicle_datum_get"):
    assert forbidden not in header_text, f"unexpected engine integration in pure math helper: {forbidden}"
print("PASS: math helper remains free of game and network APIs")

# Production integration contract. These checks deliberately inspect function
# bodies so a dormant helper or unrelated matching string cannot satisfy them.
gameplay = GAMEPLAY.read_text(encoding="utf-8")
config = CONFIG.read_text(encoding="utf-8")
menu = MENU.read_text(encoding="utf-8")

def function_body(source, name):
    match = re.search(r"\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", source, re.S)
    assert match, f"missing function body: {name}"
    opening = source.find("{", match.start())
    depth = 0
    for pos in range(opening, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:pos]
    raise AssertionError(f"unterminated function body: {name}")

enabled = function_body(gameplay, "vehicle_lift_enabled")
assert 'config_boolean("vr.vehicle_lift")' in enabled
assert "game_connection() == _game_connection_local" in enabled

candidate_path = function_body(gameplay, "candidate")
assert "if (vehicle_lift_enabled()) mask |= _object_mask_vehicle;" in candidate_path
assert "if (is_vehicle && !vehicle_lift_enabled()) continue;" in candidate_path

vehicle_get = function_body(gameplay, "vehicle_lift_get")
for required in (
    "vehicle_lift_enabled()", "vehicle->object.parent_object_index != NONE",
    "vehicle->object.name_index != NONE", "_object_movie_star_bit",
    "_object_dead_bit",
    "vehicle->unit.driver_object_index != NONE", "vehicle->unit.gunner_object_index != NONE",
    "vehicle_lift_type_supported(definition->vehicle_type)",
    "unit_seat_filled(index, seat_index)",
    "MAXIMUM_MASS_POINTS_PER_PHYSICS", "MAXIMUM_POWERED_MASS_POINTS_PER_PHYSICS",
    "isfinite(physics->mass)", "vr_vehicle_lift_eligible(&candidate)",
):
    assert required in vehicle_get, f"vehicle eligibility gate missing: {required}"
assert "point_index < physics->mass_points.count" in vehicle_get
assert "isfinite(point->mass)" in vehicle_get
assert "valid_real_point3d(&point->position)" in vehicle_get

apply = function_body(gameplay, "vehicle_lift_apply")
for required in (
    "vehicle_lift_get(index)", "vr_vehicle_lift_target_velocity(",
    "magnitude3d(&delta) > units * 0.0526f", "vehicle_accelerate(index, &delta)",
    "requested_velocity.n[axis] = error->n[axis] * alpha",
    "scale_vector3d(&up, gravity, &gravity_velocity)",
    "add_vectors3d(&requested_velocity, &gravity_velocity, &requested_velocity)",
    "vr_vehicle_lift_angular_target(angular.n, mobility, target_angular.n)",
    "vehicle->object.angular_velocity = target_angular",
    "hand_count == 2", "hands[0].local_grab", "hands[1].local_grab",
):
    assert required in apply, f"native bounded lift path missing: {required}"
for forbidden in ("object_set_position", "object_set_orientation", "network_send", "distributed_send"):
    assert forbidden not in apply, f"vehicle lift must not use {forbidden}"
assert "cross_product3d(global_up3d, acceleration, &torque)" not in apply

assert "return vehicle_lift_get(index) ? object_get(index) : NULL;" in function_body(
    gameplay, "interaction_grabbable")
grabbable = function_body(gameplay, "interaction_grabbable")
assert "world_grab_enabled()" in grabbable
assert 'config_boolean("vr.custom_scenery_grab")' in function_body(gameplay, "world_grab_enabled")
assert "!grabbable(held->index)" in function_body(gameplay, "vr_world_interaction_tick")
tick = function_body(gameplay, "vr_world_interaction_tick")
assert 'reason=outside-safe-envelope grip=held' in tick
assert "release_hand(hand, FALSE, units" not in tick[tick.index("if (!vehicle_lift_apply"):tick.index("vr_world_interaction_weight_feedback(hand, mobility")]
assert "item->object.type == _object_type_vehicle" in tick
assert "vehicle_lift_apply(held->index, &error, hand, count, units, &mobility)" in tick
assert "vr_world_interaction_weight_feedback(hand, mobility" in tick
assert "vr_world_interaction_weight_feedback(h, mobility" in tick
assert "magnitude3d(&item->object.translational_velocity)" in tick
release = function_body(gameplay, "release_hand")
assert "vr_vehicle_lift_release(vehicle->object.translational_velocity.n" in release
assert "vehicle->object.translational_velocity = linear;" in release
assert "vehicle->object.angular_velocity = angular;" in release
assert re.search(
    r'"vr\.vehicle_lift",\s*_config_boolean,\s*"false",\s*"HALO_VR_VEHICLE_LIFT",\s*_environment_value,\s*_platform_vr',
    config,
), "vehicle lift must be a default-off VR setting"
assert "independent of world grab" in config.lower()
assert '"vr.vehicle_lift", _vr_setting_boolean' in menu
assert '"LIFT VEHICLES"' in menu
assert '(!world_grab_enabled() && !vehicle_lift_enabled())' in tick
assert 'if (world_grab_enabled())' in candidate_path
print("PASS: default-off local vehicle candidate; type/seat/script/parent/destroyed/native-physics gates; tracked 6-DOF constraints; bounded free release; lifecycle cancellation")
