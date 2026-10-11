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

/* A script's garbage_collect_now (campaign scripts call it at many
 * encounters and checkpoints) collects every garbage object out of view,
 * whatever the thresholds above: that, not the thresholds, is what made
 * bodies vanish in campaign. With retention on in solo, that forced pass
 * keeps the newest garbage objects up to the retention target (oldest go
 * first); collections for memory or object space are unaffected. 0: keep
 * none (the native behavior). */
static long objects_vr_forced_garbage_keep(long setting, int local_solo)
{
	if (!local_solo)
		return 0;
	if (setting == 75)
		return 45;
	if (setting == 100)
		return 60;
	return 0;
}

#endif
