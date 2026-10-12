#ifndef HALO_VR_NPC_RESCUE_H
#define HALO_VR_NPC_RESCUE_H

#include <stddef.h>
#include <stdint.h>

/* Pure state helpers shared by the game module and its offline test harness. */
struct vr_npc_rescue_timer
{
	uint32_t unsupported_since;
	uint32_t last_attempt;
	int unsupported_active;
	int attempt_valid;
};

struct vr_npc_rescue_eligibility
{
	int option_enabled;
	int local_game;
	int vr_active;
	int game_ready;
	int outside_cinematic;
	int actor_live;
	int non_player;
	int actor_attached;
	int encounter_valid;
	int squad_valid;
	int unparented;
	int not_in_vehicle;
	int not_dead;
	int not_flying;
	int not_swarm;
	int not_movie_star;
	int no_custom_animation;
	int script_state_resumable;
	int connected_to_map;
	int collision_enabled;
	int not_recording_possessed;
	int not_deleted_when_deactivated;
};

static inline int vr_npc_rescue_is_eligible(
	struct vr_npc_rescue_eligibility const *state)
{
	return state &&
		state->option_enabled && state->local_game && state->vr_active &&
		state->game_ready && state->outside_cinematic && state->actor_live &&
		state->non_player && state->actor_attached && state->encounter_valid &&
		state->squad_valid && state->unparented && state->not_in_vehicle &&
		state->not_dead && state->not_flying && state->not_swarm &&
		state->not_movie_star && state->no_custom_animation &&
		state->script_state_resumable && state->connected_to_map &&
		state->collision_enabled && state->not_recording_possessed &&
		state->not_deleted_when_deactivated;
}

static inline void vr_npc_rescue_timer_invalidate(
	struct vr_npc_rescue_timer *timer)
{
	if (!timer)
		return;
	timer->unsupported_since = 0;
	timer->last_attempt = 0;
	timer->unsupported_active = 0;
	timer->attempt_valid = 0;
}

/* Returns true at most once per retry interval after a continuous dwell. */
static inline int vr_npc_rescue_timer_due(
	struct vr_npc_rescue_timer *timer,
	uint32_t tick,
	int unsupported,
	uint32_t dwell_ticks,
	uint32_t retry_ticks)
{
	if (!timer)
		return 0;
	if (!unsupported)
	{
		timer->unsupported_active = 0;
		timer->attempt_valid = 0;
		return 0;
	}
	if (!timer->unsupported_active || tick < timer->unsupported_since)
	{
		timer->unsupported_since = tick;
		timer->unsupported_active = 1;
		timer->attempt_valid = 0;
	}
	if (tick < timer->unsupported_since ||
		tick - timer->unsupported_since < dwell_ticks)
		return 0;
	if (timer->attempt_valid &&
		(tick < timer->last_attempt || tick - timer->last_attempt < retry_ticks))
		return 0;
	timer->last_attempt = tick;
	timer->attempt_valid = 1;
	return 1;
}

/* Existing key, first empty slot, or -1 when the bounded pool is full. */
static inline ptrdiff_t vr_npc_rescue_slot_index(
	long const *keys,
	size_t count,
	long key,
	long empty_key)
{
	size_t first_empty = count;
	size_t i;
	if (!keys || key == empty_key)
		return -1;
	for (i = 0; i < count; ++i)
	{
		if (keys[i] == key)
			return (ptrdiff_t)i;
		if (keys[i] == empty_key && first_empty == count)
			first_empty = i;
	}
	return first_empty == count ? -1 : (ptrdiff_t)first_empty;
}

static inline int vr_npc_rescue_tick_went_backwards(
	int have_previous,
	uint32_t previous_tick,
	uint32_t current_tick)
{
	return have_previous && current_tick < previous_tick;
}

void vr_npc_rescue_tick(void);
void vr_npc_rescue_reset(void);

#endif
