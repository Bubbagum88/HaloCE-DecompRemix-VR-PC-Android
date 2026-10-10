#ifndef HALO_VR_WEAPON_RELEASE_LATCH_H
#define HALO_VR_WEAPON_RELEASE_LATCH_H

/* A grip release can coincide with another interaction owning that hand.
 * Preserve the release edge only while the same weapon remains selected and
 * the controller is still tracked/focused. Never synthesize a drop after
 * tracking loss, recenter, focus loss, weapon change, or a new grip. */
struct vr_weapon_release_latch
{
	long weapon;
	int pending;
};

enum
{
	VR_WEAPON_RELEASE_NONE,
	VR_WEAPON_RELEASE_READY,
	VR_WEAPON_RELEASE_DEFERRED
};

static inline void vr_weapon_release_latch_reset(struct vr_weapon_release_latch *latch)
{
	if (!latch) return;
	latch->weapon = -1;
	latch->pending = 0;
}

static inline int vr_weapon_release_latch_step(struct vr_weapon_release_latch *latch,
	long weapon, int physical_weapons, int focused, int tracked, int recentred,
	int grip_held, int grip_pressed, int grip_released, int interaction_owned)
{
	if (!latch) return VR_WEAPON_RELEASE_NONE;
	if (!physical_weapons || !focused || !tracked || recentred || weapon < 0 ||
		grip_held || grip_pressed || (latch->pending && latch->weapon != weapon))
	{
		vr_weapon_release_latch_reset(latch);
		return VR_WEAPON_RELEASE_NONE;
	}
	if (grip_released)
	{
		if (interaction_owned)
		{
			latch->pending = 1;
			latch->weapon = weapon;
			return VR_WEAPON_RELEASE_DEFERRED;
		}
		vr_weapon_release_latch_reset(latch);
		return VR_WEAPON_RELEASE_READY;
	}
	if (latch->pending && !interaction_owned)
	{
		vr_weapon_release_latch_reset(latch);
		return VR_WEAPON_RELEASE_READY;
	}
	return VR_WEAPON_RELEASE_NONE;
}

#endif
