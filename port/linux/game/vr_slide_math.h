/*
VR_SLIDE_MATH.H

Test70: SLIDE, the owner's Sprint + Crouch = Slide. Pure kinematics of one
slide in metres and seconds, tested by tools/test_test70_movement.py; the
game's side (when it starts, the biped, impacts) is vr_slide.c.

A slide keeps the run it began with and gives it up gradually: friction
takes a share of its speed each second, a slope adds or takes the share of
gravity along it, and the stick steers it a little. It ends when it has
slowed to a walk, has run its time, or (vr_slide.c) the player stands,
jumps, leaves the ground or meets a wall.
*/

#ifndef VR_SLIDE_MATH_H
#define VR_SLIDE_MATH_H

#include <math.h>

/* friction 1x: a 10 m/s slide is down to about 4.5 m/s in a second */
#define VR_SLIDE_FRICTION 0.8f
/* the share of gravity along a slope a sliding body feels (the rest is the
ground's grip) */
#define VR_SLIDE_SLOPE_SHARE 0.55f
/* steering: degrees a second at a full stick */
#define VR_SLIDE_STEER_DEGREES 50.0f
#define VR_SLIDE_GRAVITY 9.8f

/* the speed a slide starts at: the run it comes from, given a lift by
`momentum` (DISTANCE 0.5x to 2x), never past 14 m/s */
static float vr_slide_entry_speed(float speed, float momentum)
{
	float entry;

	if (!isfinite(speed) || !(speed > 0.0f))
		return 0.0f;
	if (!isfinite(momentum) || momentum < 0.5f || momentum > 2.0f)
		momentum = 1.0f;
	entry = speed * (1.0f + 0.15f * momentum);
	return entry > 14.0f ? 14.0f : entry;
}

/* how long a slide may last, seconds */
static float vr_slide_duration(float momentum)
{
	if (!isfinite(momentum) || momentum < 0.5f || momentum > 2.0f)
		momentum = 1.0f;
	return 0.55f + 0.55f * momentum;
}

/* One step of a slide's velocity (metres a second, horizontal: v[0], v[1])
over `dt` seconds. `ground` the ground's normal (unit; NULL or not ground:
no slope), `steer` the stick's direction in the same frame (zero: none) and
`steer_amount` 0 to 1. Returns the speed after it. */
static float vr_slide_step(float v[2], float dt, float friction, float const ground[3],
	float const steer[2], float steer_amount)
{
	float speed;

	if (!isfinite(dt) || dt <= 0.0f || dt > 0.25f)
		return sqrtf(v[0] * v[0] + v[1] * v[1]);
	if (!isfinite(friction) || friction < 0.25f || friction > 3.0f)
		friction = 1.0f;
	/* friction: a share of the speed each second */
	{
		float keep = expf(-VR_SLIDE_FRICTION * friction * dt);
		v[0] *= keep;
		v[1] *= keep;
	}
	/* a slope: gravity's part along the ground, horizontally (down a slope
	faster, up one slower) */
	if (ground && isfinite(ground[0]) && isfinite(ground[1]) && isfinite(ground[2]) && ground[2] > 0.5f)
	{
		float a = VR_SLIDE_GRAVITY * VR_SLIDE_SLOPE_SHARE;
		v[0] += ground[0] * ground[2] * a * dt;
		v[1] += ground[1] * ground[2] * a * dt;
	}
	speed = sqrtf(v[0] * v[0] + v[1] * v[1]);
	/* steering: turned toward the stick, a little */
	if (steer && speed > 0.001f && isfinite(steer_amount) && steer_amount > 0.0f)
	{
		float length = sqrtf(steer[0] * steer[0] + steer[1] * steer[1]);
		if (length > 0.001f)
		{
			float sx = steer[0] / length, sy = steer[1] / length;
			float ux = v[0] / speed, uy = v[1] / speed;
			float cross = ux * sy - uy * sx, dot = ux * sx + uy * sy;
			float angle = atan2f(cross, dot);
			float limit = VR_SLIDE_STEER_DEGREES * 0.01745329f * dt * (steer_amount > 1.0f ? 1.0f : steer_amount);
			float turn = angle > limit ? limit : angle < -limit ? -limit : angle;
			float c = cosf(turn), s = sinf(turn);
			/* (no turning back on itself: a stick pulled back brakes) */
			if (dot > -0.5f)
			{
				float x = ux * c - uy * s, y = ux * s + uy * c;
				v[0] = x * speed;
				v[1] = y * speed;
			}
			else
			{
				float brake = expf(-1.5f * dt * steer_amount);
				v[0] *= brake;
				v[1] *= brake;
				speed *= brake;
			}
		}
	}
	return speed;
}

/* Sliding into an NPC: the blow's share of a melee's damage (0 below 4 m/s,
up to half a melee at 10 m/s and faster; never a kill by itself) and of a
knockdown's push, by the speed it is struck at, how square on (`facing`, the
cosine between the slide and the line to it), and the DAMAGE setting */
static float vr_slide_impact_scale(float speed, float facing, float damage)
{
	float t;

	if (!isfinite(speed) || !isfinite(facing) || !isfinite(damage) || damage <= 0.0f || facing < 0.5f)
		return 0.0f;
	t = (speed - 4.0f) / 6.0f;
	if (t <= 0.0f)
		return 0.0f;
	if (t > 1.0f)
		t = 1.0f;
	if (damage > 3.0f)
		damage = 3.0f;
	return 0.5f * t * facing * damage;
}

#endif
