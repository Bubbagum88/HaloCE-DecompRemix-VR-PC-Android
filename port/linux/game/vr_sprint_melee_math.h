#ifndef HALO_VR_SPRINT_MELEE_MATH_H
#define HALO_VR_SPRINT_MELEE_MATH_H

#include <math.h>

static inline int vr_fist_melee_permitted(int required, float squeeze,
	float trigger, int interaction_owned)
{
	if (interaction_owned) return 0;
	if (!required) return 1;
	return isfinite(squeeze) && isfinite(trigger) && squeeze >= 0.75f && trigger >= 0.75f;
}

static inline int vr_button_sprint_input(int enabled, int pressed,
	int recenter_chord, int focused, int aiming, int seated)
{
	return enabled && pressed && !recenter_chord && focused && aiming && !seated;
}

static inline float vr_sprint_effort_combine(float arm_effort, int button_active)
{
	if (!isfinite(arm_effort)) arm_effort = 0.0f;
	if (arm_effort < 0.0f) arm_effort = 0.0f;
	if (arm_effort > 1.0f) arm_effort = 1.0f;
	return button_active ? 1.0f : arm_effort;
}

static inline float vr_sprint_scale_for_effort(float configured_scale, float effort)
{
	if (!isfinite(configured_scale)) configured_scale = 1.0f;
	if (configured_scale < 1.0f) configured_scale = 1.0f;
	if (configured_scale > 1.5f) configured_scale = 1.5f;
	if (!isfinite(effort)) effort = 0.0f;
	if (effort < 0.0f) effort = 0.0f;
	if (effort > 1.0f) effort = 1.0f;
	return 1.0f + (configured_scale - 1.0f) * effort;
}

#endif
