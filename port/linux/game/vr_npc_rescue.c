/*
 * Opt-in solo rescue for live mission actors that remain unsupported for a
 * long dwell. The module never respawns actors, allocates squad locations,
 * rewrites AI goals, or runs in network sessions/cinematics.
 */
#include "cseries.h"
#include "game/game.h"
#include "objects/objects.h"
#include "scenario/scenario.h"
#include "scenario/scenario_definitions.h"
#include "ai/actors.h"
#include "ai/actor_types.h"
#include "ai/actor_definitions.h"
#include "ai/ai_scenario_definitions.h"
#include "ai/encounters.h"
#include "units/units.h"
#include "units/bipeds.h"
#include "units/biped_definitions.h"
#include "physics/collisions.h"
#include "cutscene/cinematics.h"
#include "tag_files/tag_groups.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_npc_rescue.h"
#include <math.h>
#include <string.h>

#ifdef HALO_VR

void platform_log(char const *, ...);

enum
{
	VR_NPC_RESCUE_DWELL_TICKS = 10 * TICKS_PER_SECOND,
	VR_NPC_RESCUE_RETRY_TICKS = 2 * TICKS_PER_SECOND,
	VR_NPC_RESCUE_MAX_PILL_HEIGHT = 20,
	VR_NPC_RESCUE_MAX_PILL_RADIUS = 10
};

struct vr_npc_rescue_entry
{
	long object_index;
	long actor_index;
	long encounter_index;
	long definition_index;
	short squad_index;
	boolean seen;
	boolean safe_position_valid;
	struct vr_npc_rescue_timer timer;
	real_point3d safe_position;
	real_point3d safe_ground_point;
	real_vector3d safe_forward;
	real_vector3d safe_up;
};

static struct vr_npc_rescue_entry rescue_entries[MAXIMUM_ACTORS];
static boolean rescue_entries_initialized;
static boolean rescue_tick_initialized;
static uint32_t rescue_last_tick;
static boolean rescue_overflow_reported;
static boolean rescue_map_identity_valid;
static long rescue_scenario_index;
static short rescue_structure_bsp_index;

static void vr_npc_rescue_clear_entry(struct vr_npc_rescue_entry *entry)
{
	if (!entry)
		return;
	entry->object_index = NONE;
	entry->actor_index = NONE;
	entry->encounter_index = NONE;
	entry->definition_index = NONE;
	entry->squad_index = NONE;
	entry->seen = FALSE;
	entry->safe_position_valid = FALSE;
	vr_npc_rescue_timer_invalidate(&entry->timer);
	memset(&entry->safe_position, 0, sizeof(entry->safe_position));
	memset(&entry->safe_ground_point, 0, sizeof(entry->safe_ground_point));
	memset(&entry->safe_forward, 0, sizeof(entry->safe_forward));
	memset(&entry->safe_up, 0, sizeof(entry->safe_up));
}

void vr_npc_rescue_reset(void)
{
	long i;
	for (i = 0; i < MAXIMUM_ACTORS; ++i)
		vr_npc_rescue_clear_entry(&rescue_entries[i]);
	rescue_entries_initialized = TRUE;
	rescue_tick_initialized = FALSE;
	rescue_last_tick = 0;
	rescue_overflow_reported = FALSE;
	rescue_map_identity_valid = FALSE;
	rescue_scenario_index = NONE;
	rescue_structure_bsp_index = NONE;
}

static struct vr_npc_rescue_entry *vr_npc_rescue_entry_for(long object_index)
{
	long keys[MAXIMUM_ACTORS];
	ptrdiff_t slot;
	long i;
	for (i = 0; i < MAXIMUM_ACTORS; ++i)
		keys[i] = rescue_entries[i].object_index;
	slot = vr_npc_rescue_slot_index(keys, MAXIMUM_ACTORS, object_index, NONE);
	if (slot < 0)
		return NULL;
	if (rescue_entries[slot].object_index == NONE)
	{
		vr_npc_rescue_clear_entry(&rescue_entries[slot]);
		rescue_entries[slot].object_index = object_index;
	}
	return &rescue_entries[slot];
}

static boolean vr_npc_rescue_valid_encounter_squad(
	struct actor_datum const *actor,
	struct encounter_datum **encounter_out)
{
	struct scenario *scenario = global_scenario_try_and_get();
	struct encounter_datum *encounter;
	long encounter_absolute_index;
	if (encounter_out)
		*encounter_out = NULL;
	if (!actor || !scenario || actor->meta.encounter_index == NONE ||
		actor->meta.squad_index < 0 || !scenario->ai_encounters.address ||
		!encounter_data || !squad_array)
		return FALSE;
	encounter_absolute_index = DATUM_INDEX_TO_ABSOLUTE_INDEX(actor->meta.encounter_index);
	if (!VALID_INDEX(encounter_absolute_index, scenario->ai_encounters.count))
		return FALSE;
	encounter = encounter_try_and_get(actor->meta.encounter_index);
	if (!encounter || !encounter->active ||
		actor->meta.squad_index >= encounter->squad_count ||
		actor->meta.squad_index >= MAXIMUM_SQUADS_PER_ENCOUNTER ||
		encounter->squad_base < 0 ||
		encounter->squad_base + actor->meta.squad_index >= MAXIMUM_SQUADS_PER_MAP)
		return FALSE;
	{
		struct encounter_definition *definition = TAG_BLOCK_GET_ELEMENT(
			&scenario->ai_encounters,
			encounter_absolute_index,
			struct encounter_definition);
		if (!definition || !definition->squads.address ||
			!VALID_INDEX(actor->meta.squad_index, definition->squads.count))
			return FALSE;
	}
	if (encounter_out)
		*encounter_out = encounter;
	return TRUE;
}

static boolean vr_npc_rescue_candidate_eligibility(
	long object_index,
	struct unit_datum *unit,
	struct actor_datum **actor_out,
	struct encounter_datum **encounter_out)
{
	struct vr_npc_rescue_eligibility check;
	struct actor_datum *actor = NULL;
	struct encounter_datum *encounter = NULL;
	struct biped_definition *biped_definition;
	struct actor_definition *actor_definition;
	if (actor_out)
		*actor_out = NULL;
	if (encounter_out)
		*encounter_out = NULL;
	memset(&check, 0, sizeof(check));
	check.option_enabled = config_boolean("vr.npc_rescue");
	check.local_game = game_connection() == _game_connection_local;
	check.vr_active = vr_active();
	check.game_ready = game_in_progress() && game_map_loaded() && game_time_initialized() &&
		global_structure_bsp_get() != NULL && global_bsp3d_get() != NULL;
	if (!unit || !check.option_enabled || !check.local_game || !check.vr_active ||
		!check.game_ready)
		return FALSE;
	check.outside_cinematic = !cinematic_in_progress();
	check.non_player = unit->unit.player_index == NONE;
	check.not_dead = !TEST_FLAG(unit->object.damage_flags, _object_dead_bit);
	check.unparented = unit->object.parent_object_index == NONE;
	check.not_in_vehicle = unit->unit.parent_seat_index == NONE;
	check.connected_to_map = TEST_FLAG(unit->object.flags, _object_connected_to_map_bit);
	check.collision_enabled = !TEST_FLAG(unit->object.flags, _object_no_collisions_bit) &&
		!TEST_FLAG(unit->object.flags, _object_garbage_bit);
	check.not_deleted_when_deactivated =
		!TEST_FLAG(unit->object.flags, _object_deleted_when_deactivated_bit);
	check.not_movie_star = !TEST_FLAG(unit->object.flags, _object_movie_star_bit);
	check.not_recording_possessed = !TEST_FLAG(unit->unit.flags, _unit_possessed_by_recording_bit);
	check.no_custom_animation = !unit_is_playing_custom_animation(object_index) &&
		unit->unit.animation.state != _unit_state_user_animation;
	if (unit->unit.actor_index != NONE)
		actor = actor_try_and_get(unit->unit.actor_index);
	check.not_in_vehicle = check.not_in_vehicle && actor && actor->input.vehicle_index == NONE;
	check.actor_attached = actor && actor->meta.unit_index == object_index &&
		actor->meta.encounter_index != NONE;
	check.actor_live = actor && actor->meta.active && !actor->meta.erase_next_tick;
	check.no_script_ownership = actor && actor->state.command_list_index == NONE &&
		!actor->state.command_list_immediate && actor->state.action != _actor_action_obey;
	check.not_flying = actor && !actor->state.flying && actor->meta.definition_index != NONE &&
		unit->definition_index != NONE;
	check.not_swarm = actor && !actor->meta.swarm && unit->unit.swarm_actor_index == NONE &&
		actor->meta.type >= 0 && actor->meta.type < NUMBER_OF_ACTOR_TYPES &&
		!actor_type_get_swarm(actor->meta.type);
	check.encounter_valid = vr_npc_rescue_valid_encounter_squad(actor, &encounter);
	check.squad_valid = check.encounter_valid && encounter != NULL;
	if (!check.actor_attached || !check.actor_live || !check.no_script_ownership ||
		!check.not_flying || !check.not_swarm || !check.encounter_valid)
		return FALSE;
	actor_definition = actor_definition_get(actor->meta.definition_index);
	biped_definition = biped_definition_get(unit->definition_index);
	if (!actor_definition || !biped_definition)
		return FALSE;
	check.not_flying = !TEST_FLAG(actor_definition->flags, _actor_definition_flying_bit) &&
		!TEST_FLAG(actor_definition->flags, _actor_definition_swarm_actor_bit) &&
		!TEST_FLAG(biped_definition->biped.flags, _biped_flying_bit) &&
		!TEST_FLAG(biped_definition->biped.flags, _biped_spherical_bit);
	check.not_swarm = check.not_swarm &&
		!TEST_FLAG(actor_definition->flags, _actor_definition_swarm_actor_bit);
	if (actor_out)
		*actor_out = actor;
	if (encounter_out)
		*encounter_out = encounter;
	return vr_npc_rescue_is_eligible(&check);
}

static boolean vr_npc_rescue_record_safe_position(
	struct vr_npc_rescue_entry *entry,
	struct unit_datum *unit,
	long surface_index,
	real_point3d const *surface_point)
{
	if (!entry || !unit || surface_index == NONE ||
		!valid_real_point3d(surface_point) ||
		TEST_FLAG(unit->object.flags, _object_outside_of_map_bit) ||
		!valid_real_point3d(&unit->object.position) ||
		!valid_real_vector3d_axes2(&unit->object.forward, &unit->object.up) ||
		scenario_leaf_index_from_point(&unit->object.position) == NONE)
		return FALSE;
	entry->safe_position = unit->object.position;
	entry->safe_ground_point = *surface_point;
	entry->safe_forward = unit->object.forward;
	entry->safe_up = unit->object.up;
	entry->safe_position_valid = TRUE;
	return TRUE;
}

static boolean vr_npc_rescue_destination_clear(
	long object_index,
	struct unit_datum *unit,
	struct vr_npc_rescue_entry const *entry)
{
	real_point3d current_base;
	real_point3d current_origin;
	real_point3d target_base;
	real_vector3d pill_vector;
	struct biped_definition *definition;
	real unused_height = 0.f;
	real height;
	real radius = 0.f;
	struct collision_result collision;
	if (!unit || !entry || !entry->safe_position_valid ||
		!valid_real_point3d(&entry->safe_position) ||
		!valid_real_point3d(&entry->safe_ground_point) ||
		scenario_leaf_index_from_point(&entry->safe_ground_point) == NONE ||
		!valid_real_vector3d_axes2(&entry->safe_forward, &entry->safe_up) ||
		scenario_leaf_index_from_point(&entry->safe_position) == NONE)
		return FALSE;
	definition = biped_definition_get(unit->definition_index);
	if (!definition || TEST_FLAG(definition->biped.flags, _biped_spherical_bit))
		return FALSE;
	object_get_origin(object_index, &current_origin);
	biped_get_physics_pill(object_index, &current_base, &unused_height, &radius);
	/* The native helper intentionally collapses ordinary AI bipeds to spheres
	 * for movement. Rescue clearance is stricter: use the authored standing
	 * height with the exact native radius so a restored upright NPC has room. */
	height = definition->biped.collision_height_standing - 2.f * radius;
	if (!valid_real_point3d(&current_origin) || !valid_real_point3d(&current_base) ||
		!isfinite(height) || !isfinite(radius) || height <= 0.f || radius <= 0.f ||
		height > VR_NPC_RESCUE_MAX_PILL_HEIGHT || radius > VR_NPC_RESCUE_MAX_PILL_RADIUS)
		return FALSE;
	target_base.x = entry->safe_position.x + current_base.x - current_origin.x;
	target_base.y = entry->safe_position.y + current_base.y - current_origin.y;
	target_base.z = entry->safe_position.z + current_base.z - current_origin.z;
	if (!valid_real_point3d(&target_base))
		return FALSE;
	scale_vector3d(global_up3d, height, &pill_vector);
	if (!valid_real_vector3d(&pill_vector))
		return FALSE;
	return !collision_test_pill(
		_collision_test_for_bipeds_living_flags,
		&target_base,
		&pill_vector,
		radius,
		object_index,
		&collision);
}

static void vr_npc_rescue_consider(long object_index)
{
	struct unit_datum *unit = (struct unit_datum *)object_try_and_get_and_verify_type(
		object_index,
		_object_mask_biped);
	struct actor_datum *actor = NULL;
	struct encounter_datum *encounter = NULL;
	struct vr_npc_rescue_entry *entry = NULL;
	real_point3d surface_point;
	long surface_index;
	boolean outside;
	boolean unsupported;
	boolean falling;
	long tick = game_time_get();
	if (!unit)
		return;
	entry = vr_npc_rescue_entry_for(object_index);
	if (!vr_npc_rescue_candidate_eligibility(object_index, unit, &actor, &encounter))
	{
		if (entry)
			vr_npc_rescue_clear_entry(entry);
		return;
	}
	if (!entry)
	{
		if (!rescue_overflow_reported)
		{
			platform_log("VR NPC rescue: tracking capacity exhausted; remaining actors fail closed");
			rescue_overflow_reported = TRUE;
		}
		return;
	}
	if (entry->actor_index != unit->unit.actor_index ||
		entry->encounter_index != actor->meta.encounter_index ||
		entry->squad_index != actor->meta.squad_index ||
		entry->definition_index != unit->definition_index)
	{
		vr_npc_rescue_clear_entry(entry);
		entry->object_index = object_index;
		entry->actor_index = unit->unit.actor_index;
		entry->encounter_index = actor->meta.encounter_index;
		entry->squad_index = actor->meta.squad_index;
		entry->definition_index = unit->definition_index;
	}
	entry->seen = TRUE;
	outside = TEST_FLAG(unit->object.flags, _object_outside_of_map_bit);
	surface_index = biped_approximate_surface_index(object_index, &surface_point);
	falling = biped_flying_through_air(object_index);
	/* A normal jump briefly has no support. Only a downward-moving fall can
	 * start the long unsupported dwell; leaving the map remains an immediate
	 * qualifying state. */
	unsupported = outside ||
		((surface_index == NONE || falling) &&
		isfinite(unit->object.translational_velocity.k) &&
		unit->object.translational_velocity.k < 0.f);
	if (!unsupported)
	{
		vr_npc_rescue_timer_due(
			&entry->timer,
			(uint32_t)tick,
			FALSE,
			VR_NPC_RESCUE_DWELL_TICKS,
			VR_NPC_RESCUE_RETRY_TICKS);
		/* An upward jump can be temporarily unsupported without being a
		 * recovery condition. Keep the prior grounded transform until contact
		 * is positively confirmed again. */
		if (surface_index != NONE &&
			!vr_npc_rescue_record_safe_position(
				entry, unit, surface_index, &surface_point))
			entry->safe_position_valid = FALSE;
		return;
	}
	if (!vr_npc_rescue_timer_due(
			&entry->timer,
			(uint32_t)tick,
			TRUE,
			VR_NPC_RESCUE_DWELL_TICKS,
			VR_NPC_RESCUE_RETRY_TICKS))
		return;
	/* object_set_position disconnects from map and asserts that the object is
	 * connected; eligibility enforces this before reaching the native mutation. */
	if (!entry->safe_position_valid ||
		!vr_npc_rescue_destination_clear(object_index, unit, entry))
		return;
	object_set_position(
		object_index,
		&entry->safe_position,
		&entry->safe_forward,
		&entry->safe_up);
	/* Wake only after the checked pose is reconnected. Avoid object_reset: it
	 * dispatches biped_reset and would erase the NPC's runtime mission state. */
	object_activate(object_index);
	unit->object.translational_velocity = *global_zero_vector3d;
	unit->object.angular_velocity = *global_zero_vector3d;
	SET_FLAG(unit->object.flags, _object_at_rest_bit, FALSE);
	vr_npc_rescue_timer_due(
		&entry->timer,
		(uint32_t)tick,
		FALSE,
		VR_NPC_RESCUE_DWELL_TICKS,
		VR_NPC_RESCUE_RETRY_TICKS);
	platform_log(
		"VR NPC rescue: moved actor %ld to its last grounded capsule-clear position; AI orders, inventory and encounter allocation preserved",
		unit->unit.actor_index);
}

void vr_npc_rescue_tick(void)
{
	struct object_iterator iterator;
	long tick;
	long i;
	if (!rescue_entries_initialized)
		vr_npc_rescue_reset();
	if (!config_boolean("vr.npc_rescue") || !vr_active() ||
		game_connection() != _game_connection_local || !game_in_progress() ||
		!game_map_loaded() || !game_time_initialized() || cinematic_in_progress() ||
		!global_structure_bsp_get() || !global_bsp3d_get())
	{
		vr_npc_rescue_reset();
		return;
	}
	tick = game_time_get();
	if (tick < 0)
	{
		vr_npc_rescue_reset();
		return;
	}
	if (rescue_map_identity_valid &&
		(rescue_scenario_index != global_scenario_index ||
		rescue_structure_bsp_index != global_structure_bsp_index))
		vr_npc_rescue_reset();
	rescue_map_identity_valid = TRUE;
	rescue_scenario_index = global_scenario_index;
	rescue_structure_bsp_index = global_structure_bsp_index;
	if (vr_npc_rescue_tick_went_backwards(
		rescue_tick_initialized,
		rescue_last_tick,
		(uint32_t)tick))
		vr_npc_rescue_reset();
	if (rescue_tick_initialized && (uint32_t)tick == rescue_last_tick)
		return;
	rescue_tick_initialized = TRUE;
	rescue_last_tick = (uint32_t)tick;
	for (i = 0; i < MAXIMUM_ACTORS; ++i)
		rescue_entries[i].seen = FALSE;
	object_iterator_new(&iterator, _object_mask_biped, 0);
	while (object_iterator_next(&iterator))
	{
		long object_index = iterator.index;
		vr_npc_rescue_consider(object_index);
	}
	for (i = 0; i < MAXIMUM_ACTORS; ++i)
	{
		if (rescue_entries[i].object_index != NONE && !rescue_entries[i].seen)
			vr_npc_rescue_clear_entry(&rescue_entries[i]);
	}
}

#else
void vr_npc_rescue_tick(void) {}
void vr_npc_rescue_reset(void) {}
#endif
