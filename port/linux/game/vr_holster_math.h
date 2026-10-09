#ifndef HALO_VR_HOLSTER_MATH_H
#define HALO_VR_HOLSTER_MATH_H

#include <string.h>

enum { VR_HOLSTER_SLOT_COUNT = 4 };

static inline void vr_holster_slots_clear(long slots[VR_HOLSTER_SLOT_COUNT])
{
	int i;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i) slots[i] = -1;
}

static inline void vr_holster_store(long slots[VR_HOLSTER_SLOT_COUNT], int zone,
	long weapon)
{
	int i;
	if (!slots || zone < 0 || zone >= VR_HOLSTER_SLOT_COUNT || weapon < 0) return;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i)
		if (slots[i] == weapon) slots[i] = -1;
	slots[zone] = weapon;
}

static inline int vr_holster_inventory_contains(long weapon,
	long const *inventory, int count)
{
	int i;
	if (weapon < 0 || !inventory || count < 0 || count > 16) return 0;
	for (i = 0; i < count; ++i) if (inventory[i] == weapon) return 1;
	return 0;
}

static inline void vr_holster_prune(long slots[VR_HOLSTER_SLOT_COUNT],
	long const *inventory, int count)
{
	int i;
	if (!slots || !inventory || count < 0 || count > 16) return;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i)
		if (slots[i] >= 0 && !vr_holster_inventory_contains(slots[i], inventory, count))
			slots[i] = -1;
}

#endif
