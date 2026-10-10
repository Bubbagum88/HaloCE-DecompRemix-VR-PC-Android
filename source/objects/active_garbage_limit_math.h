#ifndef HALO_OBJECTS_ACTIVE_GARBAGE_LIMIT_MATH_H
#define HALO_OBJECTS_ACTIVE_GARBAGE_LIMIT_MATH_H

/* VR solo corpse-retention choices tune the engine's shared active-garbage
 * threshold. This is deliberately not a corpse-count promise: corpses, debris
 * and other garbage share the pool, while memory/object pressure can collect
 * earlier. Online and local multiplayer always keep the native thresholds. */
static long objects_vr_active_garbage_limit(long native_limit, long setting,
	int target_limit, int local_solo)
{
	if (!local_solo)
		return native_limit;
	if (setting == 75)
		return target_limit ? 45 : 75;
	if (setting == 100)
		return target_limit ? 60 : 100;
	return native_limit;
}

#endif
