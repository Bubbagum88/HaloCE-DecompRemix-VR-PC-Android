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

/* Test54: an open hand is for grabbing, a fist (or a hand holding a gun) for
 * striking. With any grab or climb feature on, a hand open on both the grip
 * and the trigger never strikes, so reaching fast for an NPC or a ledge makes
 * no melee blow or sound; FIST REQUIRED additionally needs a closed fist on an
 * empty hand. A gun-holding hand strikes with the gun. */
static inline int vr_melee_hand_permitted(int fist_required, int grab_features,
	int armed, float squeeze, float trigger, int interaction_owned)
{
	int open;
	if (interaction_owned) return 0;
	if (armed) return 1;
	if (!isfinite(squeeze) || !isfinite(trigger)) return 0;
	open = squeeze < 0.35f && trigger < 0.35f;
	if (grab_features && open) return 0;
	return vr_fist_melee_permitted(fist_required, squeeze, trigger, 0);
}

static inline int vr_button_sprint_input(int enabled, int pressed,
	int recenter_chord, int focused, int aiming, int seated)
{
	return enabled && pressed && !recenter_chord && focused && aiming && !seated;
}

/* The toggle shares left-stick click with the recenter chord.  It only
 * changes state on a fresh press while eligible; focus loss, seating,
 * aiming, disabling sprint, or recentering clears the latch.  Remembering
 * the press even while ineligible prevents a held button from activating
 * sprint when the player returns to an eligible state. */
static inline int vr_button_sprint_input_mode(int enabled, int toggle_mode,
	int pressed, int recenter_chord, int focused, int aiming, int seated,
	int *latched, int *was_pressed)
{
	int eligible = enabled && focused && aiming && !seated;
	int rising_edge;

	if (!latched || !was_pressed)
		return 0;
	rising_edge = pressed && !*was_pressed;
	*was_pressed = pressed;
	if (!eligible || recenter_chord)
		*latched = 0;
	else if (toggle_mode && rising_edge)
		*latched = !*latched;
	else if (!toggle_mode)
		*latched = 0;
	return toggle_mode ? (*latched && eligible && !recenter_chord) :
		(eligible && pressed && !recenter_chord);
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
	if (configured_scale > 3.0f) configured_scale = 3.0f;
	if (!isfinite(effort)) effort = 0.0f;
	if (effort < 0.0f) effort = 0.0f;
	if (effort > 1.0f) effort = 1.0f;
	return 1.0f + (configured_scale - 1.0f) * effort;
}

#endif
