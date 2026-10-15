/*
VR_BUTTON_REMAP.H

Test70: what a remapped VR button does to the others. The owner's report:
a player put USE / RELOAD on A, and JUMP, which had A, was moved to another
button without a word (test23's rule: no button ever does two actions).
Now nothing moves by itself. A button another action has is a conflict the
player resolves: cancel, swap the two, clear the other, or have both on the
button. Pure: tested by tools/test_test70_controls.py.

`sources` holds each action's button (VR_BUTTON_SOURCE_* of port/linux/src/
vr.h, as ints): NONE_SOURCE is no button, HOLD_SOURCE switch grenades held
(not a button, never a conflict).
*/

#ifndef VR_BUTTON_REMAP_H
#define VR_BUTTON_REMAP_H

enum
{
	VR_REMAP_CANCEL,
	VR_REMAP_SWAP,
	VR_REMAP_CLEAR,
	VR_REMAP_SHARE,
	VR_REMAP_RESOLUTIONS
};

/* the action other than `action` that has `source`, or -1: none has it, or
it is no button */
static int vr_remap_conflict(int const *sources, int count, int action, int source,
	int none_source, int hold_source)
{
	int other;

	if (source == none_source || source == hold_source)
		return -1;
	for (other = 0; other < count; other++)
	{
		if (other != action && sources[other] == source)
			return other;
	}
	return -1;
}

/* `action` given `source`, the conflict with `other` (-1: none) resolved
as chosen. Returns 1 when anything changed. A swap gives the other the
button `action` had; "hold" is no button the other can have, so it is then
left with none. Only `action` and `other` ever change. */
static int vr_remap_apply(int *sources, int count, int action, int source, int other, int resolution,
	int none_source, int hold_source)
{
	int old;

	if (action < 0 || action >= count || resolution == VR_REMAP_CANCEL)
		return 0;
	old = sources[action];
	if (other >= 0 && other < count && other != action)
	{
		if (resolution == VR_REMAP_SWAP)
			sources[other] = old == hold_source ? none_source : old;
		else if (resolution == VR_REMAP_CLEAR)
			sources[other] = none_source;
		/* (VR_REMAP_SHARE: the other keeps the button too) */
	}
	sources[action] = source;
	return 1;
}

/* the next of `value_count` row values from `index` by `step` (+1/-1),
past `skipped` (-1: none skipped; Button Sprint holds the left stick) */
static int vr_remap_step(int index, int step, int value_count, int skipped)
{
	int next;

	if (value_count <= 0)
		return 0;
	if (index < 0 || index >= value_count)
		index = 0;
	next = (index + (step < 0 ? -1 : 1) + value_count) % value_count;
	if (next == skipped && value_count > 1)
		next = (next + (step < 0 ? -1 : 1) + value_count) % value_count;
	return next;
}

#endif
