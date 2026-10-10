#ifndef VR_ARM_IK_MATH_H
#define VR_ARM_IK_MATH_H

#include <math.h>

/* Keep the authored upper-arm and forearm lengths. When the controller is
 * outside the arm's physical reach, solve the wrist at the nearest reachable
 * point instead of scaling the bones to meet it. */
static int vr_arm_ik_reach_bounds(float upper, float fore, int tracked,
	float *minimum, float *maximum)
{
	float min_reach, max_reach;
	if (!minimum || !maximum || !isfinite(upper) || !isfinite(fore) ||
		upper <= 0.0f || fore <= 0.0f)
		return 0;
	max_reach = upper + fore;
	min_reach = fabsf(upper - fore) + 0.001f;
	if (tracked)
	{
		/* The tracked arm keeps the existing 145 degree elbow bend limit. */
		float bend_minimum_squared = upper * upper + fore * fore -
			1.638304f * upper * fore;
		if (!isfinite(bend_minimum_squared))
			return 0;
		if (bend_minimum_squared > 0.0f)
		{
			float bend_minimum = sqrtf(bend_minimum_squared);
			if (bend_minimum > min_reach)
				min_reach = bend_minimum;
		}
	}
	if (!isfinite(max_reach) || !isfinite(min_reach) || max_reach <= 0.0f)
		return 0;
	if (min_reach > max_reach)
		min_reach = max_reach;
	*minimum = min_reach;
	*maximum = max_reach;
	return 1;
}

static float vr_arm_ik_clamp_distance(float distance, float minimum, float maximum)
{
	if (!isfinite(distance) || !isfinite(minimum) || !isfinite(maximum) ||
		minimum < 0.0f || maximum < minimum)
		return 0.0f;
	if (distance < minimum)
		return minimum;
	if (distance > maximum)
		return maximum;
	return distance;
}

#endif
