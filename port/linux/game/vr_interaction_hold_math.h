#ifndef HALO_VR_INTERACTION_HOLD_MATH_H
#define HALO_VR_INTERACTION_HOLD_MATH_H

#include <math.h>
#include <string.h>

/* Keep an already acquired contact tether attached while bounding how far
 * its target may move in one simulation step. This is a solver safety limit,
 * never a reason to release while Grip remains held. */
static inline int vr_interaction_hold_target_step(float target[3],
	float const desired[3], float maximum_step, int *limited)
{
	float delta[3], length_squared = 0.0f, length, scale;
	int axis;
	if (limited) *limited = 0;
	if (!target || !desired || !isfinite(maximum_step) || maximum_step <= 0.0f || maximum_step >= 100.0f)
		return 0;
	for (axis = 0; axis < 3; ++axis)
	{
		if (!isfinite(target[axis]) || !isfinite(desired[axis])) return 0;
		delta[axis] = desired[axis] - target[axis];
		length_squared += delta[axis] * delta[axis];
	}
	if (!isfinite(length_squared)) return 0;
	length = sqrtf(length_squared);
	if (!isfinite(length)) return 0;
	if (length > maximum_step)
	{
		scale = maximum_step / length;
		for (axis = 0; axis < 3; ++axis) target[axis] += delta[axis] * scale;
		if (limited) *limited = 1;
	}
	else memcpy(target, desired, sizeof(delta));
	return 1;
}

#endif
