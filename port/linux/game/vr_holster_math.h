#ifndef HALO_VR_HOLSTER_MATH_H
#define HALO_VR_HOLSTER_MATH_H

#include <string.h>

enum { VR_HOLSTER_SLOT_COUNT = 4 };

/* Datum handles are signed 32-bit bit patterns on this build. A live handle
 * may therefore be negative; only the all-bits-set NONE value is invalid. */
#define VR_HOLSTER_INVALID_DATUM (-1L)

static inline void vr_holster_slots_clear(long slots[VR_HOLSTER_SLOT_COUNT])
{
	int i;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i) slots[i] = VR_HOLSTER_INVALID_DATUM;
}

static inline void vr_holster_store(long slots[VR_HOLSTER_SLOT_COUNT], int zone,
	long weapon)
{
	int i;
	if (!slots || zone < 0 || zone >= VR_HOLSTER_SLOT_COUNT || weapon == VR_HOLSTER_INVALID_DATUM) return;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i)
		if (slots[i] == weapon) slots[i] = VR_HOLSTER_INVALID_DATUM;
	slots[zone] = weapon;
}

static inline void vr_holster_forget(long slots[VR_HOLSTER_SLOT_COUNT],
	long weapon)
{
	int i;
	if (!slots || weapon == VR_HOLSTER_INVALID_DATUM) return;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i)
		if (slots[i] == weapon) slots[i] = VR_HOLSTER_INVALID_DATUM;
}

static inline int vr_holster_inventory_contains(long weapon,
	long const *inventory, int count)
{
	int i;
	if (weapon == VR_HOLSTER_INVALID_DATUM || !inventory || count < 0 || count > 16) return 0;
	for (i = 0; i < count; ++i) if (inventory[i] == weapon) return 1;
	return 0;
}

static inline void vr_holster_prune(long slots[VR_HOLSTER_SLOT_COUNT],
	long const *inventory, int count)
{
	int i;
	if (!slots || !inventory || count < 0 || count > 16) return;
	for (i = 0; i < VR_HOLSTER_SLOT_COUNT; ++i)
		if (slots[i] != VR_HOLSTER_INVALID_DATUM &&
			!vr_holster_inventory_contains(slots[i], inventory, count))
			slots[i] = VR_HOLSTER_INVALID_DATUM;
}

#endif
