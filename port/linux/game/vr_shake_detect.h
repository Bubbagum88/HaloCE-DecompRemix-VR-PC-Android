/*
VR_SHAKE_DETECT.H

Test70: a held weapon shaken on purpose, told from aiming, walking, tracking
jitter and melee swings. The owner: plasma shake cooling did not work, and
the needler should reload when shaken (manual reload).

Test39's detector needed the hand faster than 1 m/s in both 33 ms samples
either side of a turn, but a shaking hand's speed passes through zero at
each turn: a brisk 4 Hz, 10 cm shake gave about 0.96 m/s there and was
missed. Here a stroke is the movement between two turns of direction, and
counts by its own peak speed and length: fast enough (STROKE_PEAK), longer
than tracking jitter (STROKE_MINIMUM) and shorter than a swing (a melee
punch or arm-swinging run moves the hand far more, STROKE_MAXIMUM). A shake
is such strokes close together. Pure: positions in metres relative to the
head (walking and turning do not shake the gun), times in seconds.
Tested by tools/test_test70_weapons.py.
*/

#ifndef VR_SHAKE_DETECT_H
#define VR_SHAKE_DETECT_H

#include <math.h>

#define VR_SHAKE_STROKE_PEAK 0.8f
#define VR_SHAKE_STROKE_MINIMUM 0.04f
#define VR_SHAKE_STROKE_MAXIMUM 0.30f
#define VR_SHAKE_STILL 0.15f
#define VR_SHAKE_STROKES 8

struct vr_shake
{
	int valid;
	double time;
	float position[3], velocity[3];
	/* the way the hand last moved (faster than VR_SHAKE_STILL): a turn is
	told against it, so a sample that falls at the turn itself, nearly still,
	does not hide the turn */
	float heading[3];
	/* the stroke now: where it began, its fastest, its farthest */
	float stroke_start[3], stroke_peak, stroke_length;
	/* the recent counted strokes: when each ended and its peak */
	double stroke_time[VR_SHAKE_STROKES];
	float stroke_speed[VR_SHAKE_STROKES];
	int stroke_next;
};

static void vr_shake_reset(struct vr_shake *shake)
{
	int index;

	shake->valid = 0;
	shake->stroke_peak = shake->stroke_length = 0.0f;
	shake->stroke_next = 0;
	for (index = 0; index < VR_SHAKE_STROKES; index++)
	{
		shake->stroke_time[index] = -1.0e9;
		shake->stroke_speed[index] = 0.0f;
	}
}

static float vr_shake_distance(float const a[3], float const b[3])
{
	float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2];

	return sqrtf(x * x + y * y + z * z);
}

/* One sample. Returns 1 when it ended a counted stroke */
static int vr_shake_sample(struct vr_shake *shake, float const position[3], double now)
{
	float velocity[3], speed, previous;
	double elapsed;
	int axis, counted = 0;

	if (!isfinite(position[0]) || !isfinite(position[1]) || !isfinite(position[2]) || !isfinite(now))
	{
		vr_shake_reset(shake);
		return 0;
	}
	elapsed = now - shake->time;
	if (!shake->valid || elapsed <= 0.0 || elapsed > 0.15)
	{
		/* (a pause in the samples: a fresh start, the strokes kept) */
		shake->valid = 1;
		shake->time = now;
		for (axis = 0; axis < 3; axis++)
		{
			shake->position[axis] = shake->stroke_start[axis] = position[axis];
			shake->velocity[axis] = shake->heading[axis] = 0.0f;
		}
		shake->stroke_peak = shake->stroke_length = 0.0f;
		return 0;
	}
	for (axis = 0; axis < 3; axis++)
		velocity[axis] = (float)((position[axis] - shake->position[axis]) / elapsed);
	speed = sqrtf(velocity[0] * velocity[0] + velocity[1] * velocity[1] + velocity[2] * velocity[2]);
	previous = sqrtf(shake->heading[0] * shake->heading[0] + shake->heading[1] * shake->heading[1] +
		shake->heading[2] * shake->heading[2]);
	/* a turn: the hand moving back the way it came */
	if (speed > VR_SHAKE_STILL && previous > VR_SHAKE_STILL &&
		velocity[0] * shake->heading[0] + velocity[1] * shake->heading[1] + velocity[2] * shake->heading[2] < 0.0f)
	{
		if (shake->stroke_peak >= VR_SHAKE_STROKE_PEAK && shake->stroke_length >= VR_SHAKE_STROKE_MINIMUM &&
			shake->stroke_length <= VR_SHAKE_STROKE_MAXIMUM)
		{
			shake->stroke_time[shake->stroke_next] = now;
			shake->stroke_speed[shake->stroke_next] = shake->stroke_peak;
			shake->stroke_next = (shake->stroke_next + 1) % VR_SHAKE_STROKES;
			counted = 1;
		}
		for (axis = 0; axis < 3; axis++)
			shake->stroke_start[axis] = shake->position[axis];
		shake->stroke_peak = shake->stroke_length = 0.0f;
	}
	if (speed > shake->stroke_peak)
		shake->stroke_peak = speed;
	{
		float length = vr_shake_distance(position, shake->stroke_start);
		if (length > shake->stroke_length)
			shake->stroke_length = length;
	}
	for (axis = 0; axis < 3; axis++)
	{
		shake->position[axis] = position[axis];
		shake->velocity[axis] = velocity[axis];
		if (speed > VR_SHAKE_STILL)
			shake->heading[axis] = velocity[axis];
	}
	shake->time = now;
	return counted;
}

/* the counted strokes of the last `window` seconds: how many, and their
mean peak speed */
static int vr_shake_strokes(struct vr_shake const *shake, double now, double window, float *mean_speed)
{
	int index, count = 0;
	float total = 0.0f;

	for (index = 0; index < VR_SHAKE_STROKES; index++)
	{
		if (now - shake->stroke_time[index] <= window && now >= shake->stroke_time[index])
		{
			count++;
			total += shake->stroke_speed[index];
		}
	}
	if (mean_speed)
		*mean_speed = count ? total / (float)count : 0.0f;
	return count;
}

/* Shake cooling: how much faster a hot weapon cools. Two strokes within
0.6 s cool at 1.5x, rising with their speed to 3x at 2.5 m/s; nothing
otherwise */
static float vr_shake_cooling_multiplier(struct vr_shake const *shake, double now)
{
	float speed, t;

	if (vr_shake_strokes(shake, now, 0.6, &speed) < 2)
		return 1.0f;
	t = (speed - VR_SHAKE_STROKE_PEAK) / (2.5f - VR_SHAKE_STROKE_PEAK);
	t = t < 0.0f ? 0.0f : t > 1.0f ? 1.0f : t;
	return 1.5f + t * 1.5f;
}

/* The needler's shake reload: four strokes within 1.2 s, averaging 1 m/s
(more deliberate than cooling's: a reload is not to be set off by chance) */
static int vr_shake_reload_ready(struct vr_shake const *shake, double now)
{
	float speed;

	return vr_shake_strokes(shake, now, 1.2, &speed) >= 4 && speed >= 1.0f;
}

/* after a shake has done its work: those strokes forgotten */
static void vr_shake_spent(struct vr_shake *shake)
{
	int index;

	for (index = 0; index < VR_SHAKE_STROKES; index++)
		shake->stroke_time[index] = -1.0e9;
}

#endif
