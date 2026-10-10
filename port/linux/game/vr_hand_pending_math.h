#ifndef HALO_VR_HAND_PENDING_MATH_H
#define HALO_VR_HAND_PENDING_MATH_H

/* If a requested empty-hand transition times out while the same weapon is
 * still active, the action failed and the gun must remain represented as held.
 * A real weapon change (including no active weapon) keeps the normal state. */
static inline int vr_hand_pending_timeout_state(int pending_state,
	int current_state, long active_weapon, int empty_state, int held_state)
{
	return pending_state == empty_state && active_weapon != -1 ?
		held_state : current_state;
}

#endif
