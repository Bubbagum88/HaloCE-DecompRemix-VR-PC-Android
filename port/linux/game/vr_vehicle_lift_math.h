/*
 * Fail-closed math and lifecycle helpers for bounded VR vehicle lifting.
 *
 * This header does not access game objects, networking or transforms. A later
 * Gameplay integration applies bounded linear/angular velocity through the
 * engine's vehicle update; authored gravity, collision and transform
 * integration remain native.
 */
#ifndef HALO_VR_VEHICLE_LIFT_MATH_H
#define HALO_VR_VEHICLE_LIFT_MATH_H

#include <float.h>
#include <math.h>
#include <string.h>

enum
{
	VR_VEHICLE_LIFT_MAX_MASS_POINTS = 32,
	VR_VEHICLE_LIFT_CANCEL_NONE = 0,
	VR_VEHICLE_LIFT_CANCEL_RELEASE = 1,
	VR_VEHICLE_LIFT_CANCEL_FEATURE_OFF = 2,
	VR_VEHICLE_LIFT_CANCEL_SEAT_TRANSITION = 3,
	VR_VEHICLE_LIFT_CANCEL_MAP_TRANSITION = 4,
	VR_VEHICLE_LIFT_CANCEL_SESSION_TRANSITION = 5,
	VR_VEHICLE_LIFT_CANCEL_TRACKING_LOSS = 6,
	VR_VEHICLE_LIFT_CANCEL_OBJECT_INVALID = 7,
	VR_VEHICLE_LIFT_CANCEL_DEATH = 8
};

/* Facts the engine integration must establish from the live vehicle/tag. */
struct vr_vehicle_lift_candidate
{
	int feature_enabled;
	int offline_session;
	int supported_vehicle_type;
	int valid_native_physics;
	int parented;
	int occupied;
	int destroyed;
	int scripted_or_mission_owned;
	int mass_point_count;
	int powered_mass_point_count;
	float native_mass;
};

/* Transient helper state only; never serialized or sent over the network. */
struct vr_vehicle_lift_state
{
	int active;
	int object_index;
	int hand_count;
	float last_target_velocity[3];
};

static int vr_vl_finite3(float const v[3])
{
	return v && isfinite(v[0]) && isfinite(v[1]) && isfinite(v[2]);
}

static double vr_vl_length3(float const v[3])
{
	return hypot(hypot((double)v[0], (double)v[1]), (double)v[2]);
}

static void vr_vl_zero3(float v[3])
{
	if (v)
	{
		v[0] = 0.0f;
		v[1] = 0.0f;
		v[2] = 0.0f;
	}
}

static int vr_vl_limit3(float v[3], double maximum)
{
	double length;
	int n;
	if (!v || !vr_vl_finite3(v) || !isfinite(maximum) || !(maximum > 0.0))
	{
		vr_vl_zero3(v);
		return 0;
	}
	length = vr_vl_length3(v);
	if (!isfinite(length))
	{
		vr_vl_zero3(v);
		return 0;
	}
	if (length > maximum)
		for (n = 0; n < 3; ++n)
			v[n] = (float)((double)v[n] * maximum / length);
	return vr_vl_finite3(v);
}

/* Unknown vehicle types, network sessions, occupied/scripted vehicles and
 * malformed native physics are rejected. No heuristic/tag-name fallback. */
static int vr_vehicle_lift_eligible(struct vr_vehicle_lift_candidate const *c)
{
	if (!c || c->feature_enabled != 1 || c->offline_session != 1 ||
		c->supported_vehicle_type != 1 || c->valid_native_physics != 1 ||
		c->parented || c->occupied || c->destroyed || c->scripted_or_mission_owned ||
		c->mass_point_count < 1 ||
		c->mass_point_count > VR_VEHICLE_LIFT_MAX_MASS_POINTS ||
		c->powered_mass_point_count < 0 ||
		c->powered_mass_point_count > c->mass_point_count ||
		c->powered_mass_point_count > VR_VEHICLE_LIFT_MAX_MASS_POINTS ||
		!isfinite(c->native_mass) || !(c->native_mass > 0.0f) ||
		(double)c->native_mass > (double)FLT_MAX / (100.0 * 0.035 * 1.5))
		return 0;
	return 1;
}

/*
 * Produce a desired native velocity from a bounded hand-driven target.
 * `current` and `requested` are engine world-units per game tick; `units_per_metre`
 * supplies the same scale used by the existing VR interaction solver.
 * Existing vehicle speed above the conservative lift envelope is rejected so
 * acquiring a fast vehicle cannot abruptly brake or redirect it.
 *
 * This is a velocity target only. The engine must integrate it and resolve
 * collision; never write the object's position or orientation directly.
 */
static int vr_vehicle_lift_target_velocity(float const current[3],
	float const requested[3], int hands, float units_per_metre, float out[3])
{
	double max_speed, max_delta, current_speed, delta[3], delta_speed, target[3];
	int n;
	vr_vl_zero3(out);
	if (!out || !vr_vl_finite3(current) || !vr_vl_finite3(requested) ||
		(hands != 1 && hands != 2) || !isfinite(units_per_metre) ||
		!(units_per_metre > 0.0f && units_per_metre < 100.0f))
		return 0;
	max_speed = (double)units_per_metre * 0.20;
	max_delta = (double)units_per_metre * 0.035 * (hands == 2 ? 1.5 : 1.0);
	current_speed = vr_vl_length3(current);
	if (!isfinite(current_speed) || current_speed > max_speed)
		return 0;
	for (n = 0; n < 3; ++n)
		delta[n] = (double)requested[n] - (double)current[n];
	delta_speed = hypot(hypot(delta[0], delta[1]), delta[2]);
	if (!isfinite(delta_speed))
		return 0;
	if (delta_speed > max_delta && delta_speed > 0.0)
		for (n = 0; n < 3; ++n)
			delta[n] *= max_delta / delta_speed;
	for (n = 0; n < 3; ++n)
		target[n] = (double)current[n] + delta[n];
	delta_speed = hypot(hypot(target[0], target[1]), target[2]);
	if (!isfinite(delta_speed))
		return 0;
	if (delta_speed > max_speed && delta_speed > 0.0)
		for (n = 0; n < 3; ++n)
			target[n] *= max_speed / delta_speed;
	for (n = 0; n < 3; ++n)
	{
		if (!isfinite(target[n]) || fabs(target[n]) > FLT_MAX)
			return 0;
		out[n] = (float)target[n];
	}
	return 1;
}

/* Map orientation error into a conservative angular velocity (radians/tick).
 * The caller computes hand-to-object basis error from tracked poses. */
static int vr_vehicle_lift_angular_target(float const error[3], float mobility,
	float out[3])
{
	int n;
	vr_vl_zero3(out);
	if (!out || !vr_vl_finite3(error) || !isfinite(mobility) || mobility < 0.25f || mobility > 2.0f)
		return 0;
	for (n = 0; n < 3; ++n)
		out[n] = error[n] * 0.12f * sqrtf(mobility);
	return vr_vl_limit3(out, 0.08);
}

/* Let the native solver continue from a bounded free-release velocity. A
 * malformed state is zeroed instead of being propagated into physics. */
static int vr_vehicle_lift_release(float const linear[3], float const angular[3],
	float units_per_metre, float linear_out[3], float angular_out[3])
{
	int n;
	vr_vl_zero3(linear_out);
	vr_vl_zero3(angular_out);
	if (!linear_out || !angular_out || !vr_vl_finite3(linear) || !vr_vl_finite3(angular) ||
		!isfinite(units_per_metre) || !(units_per_metre > 0.0f && units_per_metre < 100.0f))
		return 0;
	for (n = 0; n < 3; ++n)
	{
		linear_out[n] = linear[n];
		angular_out[n] = angular[n];
	}
	if (!vr_vl_limit3(linear_out, (double)units_per_metre * 0.20) ||
		!vr_vl_limit3(angular_out, 0.08))
	{
		vr_vl_zero3(linear_out);
		vr_vl_zero3(angular_out);
		return 0;
	}
	return 1;
}

/* Native physics_update consumes force/mass as a per-game-tick velocity
 * delta, with no caller-provided dt. This cap is therefore expressed in the
 * decomp's native force-per-update units and scales with authored mass. */
static int vr_vehicle_lift_force_cap(float native_mass, int hands,
	float units_per_metre, float *out_cap)
{
	double max_delta, cap;
	if (out_cap)
		*out_cap = 0.0f;
	if (!out_cap || (hands != 1 && hands != 2) || !isfinite(native_mass) || !(native_mass > 0.0f) ||
		!isfinite(units_per_metre) || !(units_per_metre > 0.0f && units_per_metre < 100.0f))
		return 0;
	max_delta = (double)units_per_metre * 0.035 * (hands == 2 ? 1.5 : 1.0);
	cap = (double)native_mass * max_delta;
	if (!isfinite(cap) || !(cap > 0.0) || cap > FLT_MAX)
		return 0;
	*out_cap = (float)cap;
	if (!isfinite(*out_cap) || !(*out_cap > 0.0f))
	{
		*out_cap = 0.0f;
		return 0;
	}
	return 1;
}

/*
 * Convert an already-validated target into a bounded native per-tick impulse.
 * Its magnitude is capped by native_mass * max_delta_velocity. Gravity and
 * collision response remain native; no position or orientation is written.
 */
static int vr_vehicle_lift_impulse(float const current[3], float const target[3],
	float native_mass, int hands, float units_per_metre, float impulse[3])
{
	double max_delta, current_speed, target_speed, delta[3], delta_speed, impulse_speed;
	float force_cap;
	int n;
	vr_vl_zero3(impulse);
	if (!impulse || !vr_vl_finite3(current) || !vr_vl_finite3(target) ||
		(hands != 1 && hands != 2) ||
		!vr_vehicle_lift_force_cap(native_mass, hands, units_per_metre, &force_cap))
		return 0;
	current_speed = vr_vl_length3(current);
	target_speed = vr_vl_length3(target);
	if (!isfinite(current_speed) || !isfinite(target_speed) ||
		current_speed > (double)units_per_metre * 0.20 ||
		target_speed > (double)units_per_metre * 0.20)
		return 0;
	max_delta = (double)units_per_metre * 0.035 * (hands == 2 ? 1.5 : 1.0);
	for (n = 0; n < 3; ++n)
		delta[n] = (double)target[n] - (double)current[n];
	delta_speed = hypot(hypot(delta[0], delta[1]), delta[2]);
	if (!isfinite(delta_speed) || delta_speed > max_delta + 1.0e-7)
		return 0;
	for (n = 0; n < 3; ++n)
	{
		double value = (double)native_mass * delta[n];
		if (!isfinite(value) || fabs(value) > FLT_MAX)
		{
			vr_vl_zero3(impulse);
			return 0;
		}
		impulse[n] = (float)value;
	}
	impulse_speed = vr_vl_length3(impulse);
	if (!isfinite(impulse_speed) || impulse_speed > (double)force_cap + 1.0e-5)
	{
		vr_vl_zero3(impulse);
		return 0;
	}
	return 1;
}

/* Every non-NONE reason, including an unrecognized value, clears transient
 * ownership. Integrations must map seat/map/session/feature transitions here. */
static int vr_vehicle_lift_cancel(struct vr_vehicle_lift_state *state, int reason)
{
	if (reason == VR_VEHICLE_LIFT_CANCEL_NONE)
		return 0;
	if (state)
	{
		memset(state, 0, sizeof(*state));
		state->object_index = -1;
	}
	return 1;
}

#endif /* HALO_VR_VEHICLE_LIFT_MATH_H */
