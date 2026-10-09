/* Optional loose-item interaction. Native item_update retains all collision,
 * gravity and orientation integration. No object is teleported or recreated.
 * Live NPC ragdolls and networking require their own proven implementations. */
#ifdef HALO_VR
#include "cseries.h"
#include "game/game.h"
#include "game/players.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "items/items.h"
#include "objects/object_definitions.h"
#include "physics/collisions.h"
#include "physics/collision_models.h"
#include "physics/collision_bsp.h"
#include "physics/physics.h"
#include "physics/physics_definitions.h"
#include "units/units.h"
#include "units/vehicle_datum.h"
#include "units/vehicle_definitions.h"
#include "units/vehicles.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_world_interaction.h"
#include "vr_npc_interaction.h"
#include "vr_world_math.h"
#include "vr_interaction_hold_math.h"
#include "vr_weight_feedback_math.h"
#include "vr_world_props.h"
#include "vr_interaction_impact.h"
#include "network_coop.h"
#include "network_interaction.h"
#include "vr_vehicle_lift_math.h"
#include <float.h>
#include <math.h>
#include <string.h>

void platform_log(char const *format, ...);

static struct world_hand {
    boolean active, sample_valid, strain_logged;
    long index;
    real_point3d local_grab, previous, point;
    real_vector3d velocity, local_forward, local_up, forward, up;
} hands[2];
static long last_tick = NONE, last_unit = NONE;
static int previous_grip[2] = {1,1};
static unsigned long weight_haptic_at[2];
static int interaction_diag_connection = -2;
static int interaction_diag_features = -1;
static int interaction_diag_vr = -1;
static int interaction_diag_coop = -1;
static int interaction_diag_game = -1;
static int interaction_diag_map = -1;
static int interaction_diag_contact_cm = -1;
static int interaction_diag_slots = -1;
static int interaction_diag_haptics_milli = -1;
static long interaction_diag_tick = NONE;
unsigned long system_milliseconds(void);
static void world_vector(real_vector3d const *forward, real_vector3d const *up,
	real_vector3d const *local, real_vector3d *world);

/* vehicle_definition is private to vehicles.c. This prefix is copied from
 * that source definition (unit, flags, vehicle_type, pad); the offset assert
 * keeps the type read tied to the pinned native layout. */
struct vr_vehicle_definition_prefix
{
	struct unit_definition unit;
	unsigned long flags;
	short vehicle_type;
	short pad;
};
typedef char vr_vehicle_type_offset_assert[
	offsetof(struct vr_vehicle_definition_prefix, vehicle_type) == 0x2F4 ? 1 : -1];

enum
{
	VR_VEHICLE_TYPE_HUMAN_TANK = 0,
	VR_VEHICLE_TYPE_HUMAN_JEEP,
	VR_VEHICLE_TYPE_HUMAN_BOAT,
	VR_VEHICLE_TYPE_HUMAN_PLANE,
	VR_VEHICLE_TYPE_ALIEN_SCOUT,
	VR_VEHICLE_TYPE_ALIEN_FIGHTER,
	VR_VEHICLE_TYPE_TURRET,
	VR_VEHICLE_TYPE_COUNT
};

static boolean vehicle_lift_enabled(void)
{
	return config_boolean("vr.vehicle_lift") &&
		game_connection() == _game_connection_local;
}

static boolean world_grab_enabled(void)
{
	/* CUSTOM SCENERY is itself an opt-in world-grab path, so a hand-edited
	 * config need not also discover an undocumented prerequisite toggle. */
	return config_boolean("vr.world_interaction") ||
		config_boolean("vr.custom_scenery_grab");
}

static boolean vehicle_lift_type_supported(short type)
{
	/* The first integrated subset uses ground-native update families only.
	 * Boats and powered aircraft use distinct buoyancy/flight solvers and stay
	 * stock until their hand-force behavior is separately validated. */
	return type == VR_VEHICLE_TYPE_HUMAN_TANK ||
		type == VR_VEHICLE_TYPE_HUMAN_JEEP ||
		type == VR_VEHICLE_TYPE_ALIEN_SCOUT ||
		type == VR_VEHICLE_TYPE_TURRET;
}

/* Only engine-native vehicle classes with validated physics are accepted.
 * Named/movie-star vehicles, occupied seats and malformed/custom physics are
 * conservatively left to stock behavior. */
static struct vehicle_datum *vehicle_lift_get(long index)
{
	struct vehicle_datum *vehicle;
	struct vr_vehicle_definition_prefix const *definition;
	struct physics_definition *physics;
	struct vr_vehicle_lift_candidate candidate;
	struct unit_definition const *unit_definition;
	long physics_index;
	short seat_index;
	if (!vehicle_lift_enabled() ||
		!(vehicle = vehicle_datum_try_and_get(index)) ||
		vehicle->object.parent_object_index != NONE ||
		vehicle->object.name_index != NONE ||
		TEST_FLAG(vehicle->object.damage_flags, _object_dead_bit) ||
		TEST_FLAG(vehicle->object.flags, _object_movie_star_bit) ||
		vehicle->unit.driver_object_index != NONE ||
		vehicle->unit.gunner_object_index != NONE)
		return NULL;
	definition = (struct vr_vehicle_definition_prefix const *)vehicle_definition_get(vehicle->definition_index);
	if (!definition || definition->vehicle_type < VR_VEHICLE_TYPE_HUMAN_TANK ||
		definition->vehicle_type >= VR_VEHICLE_TYPE_COUNT ||
		!vehicle_lift_type_supported(definition->vehicle_type))
		return NULL;
	unit_definition = &definition->unit;
	if (unit_definition->unit.seats.count < 0 || unit_definition->unit.seats.count > 32 ||
		(unit_definition->unit.seats.count > 0 && !unit_definition->unit.seats.address))
		return NULL;
	for (seat_index = 0; seat_index < unit_definition->unit.seats.count; ++seat_index)
		if (unit_seat_filled(index, seat_index))
			return NULL;
	physics_index = unit_definition->object.physics.index;
	if (physics_index == NONE ||
		unit_definition->object.physics.group_tag != POINT_PHYSICS_DEFINITION_TAG)
		return NULL;
	physics = physics_definition_get(physics_index);
	if (!physics || physics->mass_points.count < 1 ||
		physics->mass_points.count > MAXIMUM_MASS_POINTS_PER_PHYSICS ||
		!physics->mass_points.address || physics->powered_mass_points.count < 0 ||
		physics->powered_mass_points.count > MAXIMUM_POWERED_MASS_POINTS_PER_PHYSICS ||
		physics->powered_mass_points.count > physics->mass_points.count ||
		(physics->powered_mass_points.count > 0 && !physics->powered_mass_points.address) ||
		!isfinite(physics->mass) || !(physics->mass > 0.0f))
		return NULL;
	for (long point_index = 0; point_index < physics->mass_points.count; ++point_index)
	{
		struct mass_point_definition const *point = TAG_BLOCK_GET_ELEMENT(
			&physics->mass_points, point_index, struct mass_point_definition);
		if (!point || !isfinite(point->mass) || point->mass < 0.0f ||
			!isfinite(point->radius) || point->radius < 0.0f ||
			!valid_real_point3d(&point->position) ||
			!valid_real_vector3d(&point->forward) || !valid_real_vector3d(&point->up))
			return NULL;
	}
	memset(&candidate, 0, sizeof(candidate));
	candidate.feature_enabled = config_boolean("vr.vehicle_lift");
	candidate.offline_session = game_connection() == _game_connection_local;
	candidate.supported_vehicle_type = vehicle_lift_type_supported(definition->vehicle_type);
	candidate.valid_native_physics = TRUE;
	candidate.parented = vehicle->object.parent_object_index != NONE;
	candidate.occupied = vehicle->unit.driver_object_index != NONE ||
		vehicle->unit.gunner_object_index != NONE;
	candidate.destroyed = TEST_FLAG(vehicle->object.damage_flags, _object_dead_bit);
	candidate.scripted_or_mission_owned = vehicle->object.name_index != NONE ||
		TEST_FLAG(vehicle->object.flags, _object_movie_star_bit);
	candidate.mass_point_count = physics->mass_points.count;
	candidate.powered_mass_point_count = physics->powered_mass_points.count;
	candidate.native_mass = physics->mass;
	if (!vr_vehicle_lift_eligible(&candidate))
		return NULL;
	return vehicle;
}

static struct object_datum *interaction_grabbable(long index)
{
	struct object_datum *object;
	/* Keep the two independently selectable paths independent. Previously this
	 * helper always admitted ordinary props, while the top-level tick required
	 * WORLD GRAB even when only LIFT VEHICLES was enabled. */
	if (world_grab_enabled() &&
		(object = vr_world_object_get(index)))
		return object;
	if (vehicle_lift_enabled())
		return vehicle_lift_get(index) ? object_get(index) : NULL;
	return NULL;
}

/* Follow the tracked hand anchors with a bounded native linear/angular
 * velocity response. vehicle_accelerate wakes the native physics path; its
 * built-in global-up yaw impulse is replaced with our bounded hand pose below.
 * The engine still integrates position/orientation and resolves collision. */
static boolean vehicle_lift_apply(long index, real_vector3d const *error,
	int hand, int hand_count, real units, real *mobility_out)
{
	struct vehicle_datum *vehicle = vehicle_lift_get(index);
	struct object_definition *definition;
	struct physics_definition *physics;
	real_vector3d requested_velocity, target_velocity, delta, up, gravity_velocity, target_forward, target_up;
	real_vector3d angular, second, target_angular, local_line, object_line, hand_line;
	real speed, angular_speed, gravity, mobility, alpha;
	int axis;
	if (!vehicle || !error || !mobility_out || hand < 0 || hand > 1 ||
		(hand_count != 1 && hand_count != 2) ||
		!isfinite(units) || !(units > 0.0f && units < 100.0f) ||
		!valid_real_vector3d(error) || !valid_real_vector3d(global_up3d))
		return FALSE;
	if (!hands[hand].active || hands[hand].index != index ||
		(hand_count == 2 && (!hands[1 - hand].active || hands[1 - hand].index != index)))
		return FALSE;
	up = *global_up3d;
	if (normalize3d(&up) < 0.99f || !valid_real_vector3d(&up))
		return FALSE;
	speed = magnitude3d(&vehicle->object.translational_velocity);
	angular_speed = magnitude3d(&vehicle->object.angular_velocity);
	if (!valid_real_vector3d(&vehicle->object.translational_velocity) ||
		!valid_real_vector3d(&vehicle->object.angular_velocity) ||
		!isfinite(speed) || speed > units * 0.20f ||
		!isfinite(angular_speed) || angular_speed > 0.15f)
		return FALSE;
	definition = object_definition_get(vehicle->definition_index);
	if (!definition || definition->object.physics.index == NONE ||
		!isfinite(definition->object.acceleration_scale))
		return FALSE;
	physics = physics_definition_get(definition->object.physics.index);
	if (!physics || !isfinite(physics->gravity_scale) || physics->gravity_scale < 0.0f ||
		physics->gravity_scale > 4.0f || !isfinite(global_gravity))
		return FALSE;
	mobility = PIN(definition->object.acceleration_scale, 0.25f, 2.0f);
	alpha = (hand_count == 2 ? 0.50f : 0.35f) * (real)sqrt(mobility);
	gravity = physics->gravity_scale * global_gravity;
	if (!isfinite(gravity) || gravity > units * 0.20f)
		return FALSE;
	/* The point constraint acts in all three world axes. Compensate exactly for
	 * this vehicle physics tag's native downward gravity before its next step. */
	for (axis = 0; axis < 3; ++axis)
		requested_velocity.n[axis] = error->n[axis] * alpha;
	scale_vector3d(&up, gravity, &gravity_velocity);
	add_vectors3d(&requested_velocity, &gravity_velocity, &requested_velocity);
	if (!valid_real_vector3d(&requested_velocity) ||
		!vr_vehicle_lift_target_velocity(vehicle->object.translational_velocity.n,
			requested_velocity.n, hand_count, units, target_velocity.n))
		return FALSE;
	for (axis = 0; axis < 3; ++axis)
		delta.n[axis] = target_velocity.n[axis] - vehicle->object.translational_velocity.n[axis];
	if (!valid_real_vector3d(&delta) || magnitude3d(&delta) > units * 0.0526f ||
		!valid_real_vector3d(&vehicle->object.forward) ||
		!valid_real_vector3d(&vehicle->object.up) ||
		magnitude3d(&vehicle->object.forward) < 0.9f || magnitude3d(&vehicle->object.up) < 0.9f ||
		!valid_real_vector3d(&hands[hand].forward) || !valid_real_vector3d(&hands[hand].up) ||
		magnitude3d(&hands[hand].forward) < 0.9f || magnitude3d(&hands[hand].up) < 0.9f)
		return FALSE;
	/* Match the vehicle's grabbed orientation to its tracked hand. With two
	 * hands, their line adds a second independent orientation constraint. */
	world_vector(&hands[hand].forward, &hands[hand].up, &hands[hand].local_forward, &target_forward);
	world_vector(&hands[hand].forward, &hands[hand].up, &hands[hand].local_up, &target_up);
	if (!valid_real_vector3d(&target_forward) || !valid_real_vector3d(&target_up) ||
		normalize3d(&target_forward) < 0.9f || normalize3d(&target_up) < 0.9f)
		return FALSE;
	cross_product3d(&vehicle->object.forward, &target_forward, &angular);
	cross_product3d(&vehicle->object.up, &target_up, &second);
	add_vectors3d(&angular, &second, &angular);
	if (hand_count == 2)
	{
		vector_from_points3d(&hands[0].local_grab, &hands[1].local_grab, &local_line);
		world_vector(&vehicle->object.forward, &vehicle->object.up, &local_line, &object_line);
		vector_from_points3d(&hands[0].point, &hands[1].point, &hand_line);
		if (!valid_real_vector3d(&object_line) || !valid_real_vector3d(&hand_line))
			return FALSE;
		if (normalize3d(&object_line) > 0.01f && normalize3d(&hand_line) > 0.01f)
		{
			cross_product3d(&object_line, &hand_line, &second);
			for (axis = 0; axis < 3; ++axis)
				angular.n[axis] = angular.n[axis] * 0.25f + second.n[axis];
		}
	}
	if (!vr_vehicle_lift_angular_target(angular.n, mobility, target_angular.n))
		return FALSE;
	/* vehicle_accelerate wakes native vehicle physics and applies the bounded
	 * linear delta. Its built-in translation-to-yaw coupling is immediately
	 * replaced by the tracked-hand angular target above. No transforms teleport. */
	vehicle_accelerate(index, &delta);
	vehicle->object.angular_velocity = target_angular;
	*mobility_out = mobility;
	return TRUE;
}

void vr_world_interaction_weight_feedback(int hand, float mobility,
	float strain_metres, float speed_metres_per_second)
{
    unsigned long now;
    float amplitude;
    if(hand<0||hand>1||config_real("vr.haptics")<=0.0||
       game_connection()!=_game_connection_local)return;
    now=system_milliseconds();
    if(weight_haptic_at[hand]&&now-weight_haptic_at[hand]<120)return;
    amplitude=vr_weight_feedback_amplitude(mobility,strain_metres,speed_metres_per_second);
    if(amplitude<=0)return;
    weight_haptic_at[hand]=now;
    /* Refresh a low-amplitude 120 ms action at the same cadence so the load
     * sensation feels sustained rather than like isolated impact taps. */
    vr_haptic(hand,amplitude,0.12f);
}

static void weight_feedback(int hand, float mobility, real strain,
	real_vector3d const *velocity, real units)
{
	real speed;
	if (!(units > 0.0f) || !velocity) return;
	speed = magnitude3d(velocity) * (real)TICKS_PER_SECOND / units;
	vr_world_interaction_weight_feedback(hand, mobility, (float)(strain / units), (float)speed);
}

static void local_vector(real_vector3d const *forward, real_vector3d const *up,
    real_vector3d const *world, real_vector3d *local)
{
    real_vector3d left;
    cross_product3d(up, forward, &left);
    local->i = dot_product3d(forward, world);
    local->j = dot_product3d(&left, world);
    local->k = dot_product3d(up, world);
}
static void world_vector(real_vector3d const *forward, real_vector3d const *up,
    real_vector3d const *local, real_vector3d *world)
{
    real_vector3d left;
    int n;
    cross_product3d(up, forward, &left);
    for (n=0;n<3;++n) world->n[n] = forward->n[n]*local->i + left.n[n]*local->j + up->n[n]*local->k;
}
static char const *interaction_connection_name(int connection)
{
	switch (connection)
	{
	case _game_connection_local: return "local";
	case _game_connection_network_client: return "network-client";
	case _game_connection_network_server: return "network-server";
	case _game_connection_film_playback: return "film";
	default: return "unknown";
	}
}
/* Log effective state only when its session/settings identity changes. This
 * makes solo-vs-network gating and required toggles visible without a per-frame
 * log flood. */
static void interaction_log_session_state(void)
{
	int connection = game_connection();
	int features =
		(config_boolean("vr.world_interaction") ? 1 : 0) |
		(config_boolean("vr.vehicle_lift") ? 2 : 0) |
		(config_boolean("vr.npc_interaction") ? 4 : 0) |
		(config_boolean("vr.npc_rescue") ? 8 : 0) |
		(config_boolean("vr.custom_npc_rigs") ? 16 : 0) |
		(config_boolean("vr.custom_scenery_grab") ? 32 : 0) |
		(config_boolean("vr.dropped_magazines") ? 64 : 0) |
		(config_boolean("vr.manual_reload") ? 128 : 0);
	int active = vr_active();
	int coop = network_coop_active();
	int in_game = game_in_progress();
	int map_loaded = game_map_loaded();
	int contact_cm = (int)(PIN((real)config_real("vr.interaction_reach"), 0.02f, 0.08f) * 100.0f + 0.5f);
	int slots = (int)config_integer("vr.npc_max_ragdolls");
	int haptics_milli = (int)(PIN((real)config_real("vr.haptics"), 0.0f, 1.0f) * 1000.0f + 0.5f);
	long tick = game_time_get();
	if (slots < 1) slots = 1;
	if (slots > VR_NPC_INTERACTION_POOL_SIZE) slots = VR_NPC_INTERACTION_POOL_SIZE;
	if (interaction_diag_connection == connection && interaction_diag_features == features &&
		interaction_diag_vr == active && interaction_diag_coop == coop &&
		interaction_diag_game == in_game && interaction_diag_map == map_loaded &&
		interaction_diag_contact_cm == contact_cm && interaction_diag_slots == slots &&
		interaction_diag_haptics_milli == haptics_milli &&
		(tick >= interaction_diag_tick || interaction_diag_tick == NONE))
		return;
	interaction_diag_connection = connection;
	interaction_diag_features = features;
	interaction_diag_vr = active;
	interaction_diag_coop = coop;
	interaction_diag_game = in_game;
	interaction_diag_map = map_loaded;
	interaction_diag_contact_cm = contact_cm;
	interaction_diag_slots = slots;
	interaction_diag_haptics_milli = haptics_milli;
	interaction_diag_tick = tick;
	platform_log("VR interactions: session=%s(%d) in_game=%d map_loaded=%d vr=%d coop=%d world_grab=%d vehicle_lift=%d npc_grab=%d npc_rescue=%d custom_rigs=%d custom_scenery=%d mag_debris=%d manual_reload=%d contact_radius=%dcm npc_rig_slots=%d/%d haptics=%.2f%s",
		interaction_connection_name(connection), connection, in_game, map_loaded, active, coop,
		features & 1 ? 1 : 0, features & 2 ? 1 : 0, features & 4 ? 1 : 0,
		features & 8 ? 1 : 0, features & 16 ? 1 : 0, features & 32 ? 1 : 0,
		features & 64 ? 1 : 0, features & 128 ? 1 : 0,
		contact_cm, slots, VR_NPC_INTERACTION_POOL_SIZE, (float)config_real("vr.haptics"),
		connection == _game_connection_local ? "" : "; local-only interactions suppressed in this network/film session");
}
#define grabbable interaction_grabbable
int vr_world_interaction_hand(int hand, float point[3])
{
    struct object_datum *item;
    real_vector3d offset;
    int n;
    if (hand<0 || hand>1 || !hands[hand].active || !point ||
        !(item=grabbable(hands[hand].index))) return FALSE;
    world_vector(&item->object.forward,&item->object.up,(real_vector3d *)&hands[hand].local_grab,&offset);
    for(n=0;n<3;++n) point[n]=item->object.position.n[n]+offset.n[n];
    return TRUE;
}
long vr_world_interaction_object(int hand)
{
    return hand>=0 && hand<2 && hands[hand].active && grabbable(hands[hand].index) ? hands[hand].index : NONE;
}
static void release_hand(int hand, boolean throwing, real units,char const *reason)
{
    struct world_hand *held = &hands[hand];
    struct object_datum *item = held->active ? grabbable(held->index) : NULL;
    if (held->active) {
        if (throwing && item && !(hands[1-hand].active && hands[1-hand].index == held->index)) {
            if (item->object.type == _object_type_vehicle) {
                struct vehicle_datum *vehicle = vehicle_lift_get(held->index);
                real_vector3d linear, angular;
                if (vehicle) {
                    if (!vr_vehicle_lift_release(vehicle->object.translational_velocity.n,
                        vehicle->object.angular_velocity.n, units, linear.n, angular.n)) {
                        linear = *global_zero_vector3d;
                        angular = *global_zero_vector3d;
                    }
                    vehicle->object.translational_velocity = linear;
                    vehicle->object.angular_velocity = angular;
                    platform_log("VR world: vehicle free release hand=%d object=%08lx linear_speed_m_tick=%.3f angular_speed_tick=%.3f",
                        hand, held->index, (float)magnitude3d(&linear) / units,
                        (float)magnitude3d(&angular));
                }
            } else {
                real_vector3d velocity = held->velocity;
                if (vr_world_limit(velocity.n, units * 0.24f))
                    vr_world_object_velocity(held->index, &velocity, &item->object.angular_velocity);
            }
        }
		platform_log("VR world: release hand=%d object=%08lx grip=%s throw=%d reason=%s",
			hand, held->index, throwing?"up":"held", throwing, reason?reason:"unspecified");
    }
    memset(held, 0, sizeof(*held));
    vr_interaction_release(hand, VR_INTERACTION_WORLD);
}
void vr_world_interaction_reset(void)
{
    /* Never dereference old object IDs during map teardown/checkpoint reset. */
    for(int hand=0;hand<2;++hand) if(hands[hand].active)
        vr_interaction_release(hand, VR_INTERACTION_WORLD);
    memset(hands, 0, sizeof(hands));
    previous_grip[0]=previous_grip[1]=1;
    weight_haptic_at[0]=weight_haptic_at[1]=0;
    last_tick = last_unit = NONE;
}
static long candidate(real_point3d const *point, real_point3d const *camera, long unit, real units,
    real_point3d *contact)
{
    struct object_iterator iterator;
    struct object_datum *item;
    real contact_radius = (real)vr_world_hand_contact_radius((float)config_real("vr.interaction_reach"), (float)units);
    real best_center_distance = FLT_MAX;
    long selected = NONE;
    int narrow_tests=0;
    real_vector3d ray;
    struct collision_result hit;
    real_vector3d stationary = { 0.0f, 0.0f, 0.0f };
    unsigned long mask = 0;
    if (world_grab_enabled())
        mask |= _object_mask_weapon | _object_mask_equipment | _object_mask_scenery;
    if (vehicle_lift_enabled()) mask |= _object_mask_vehicle;
    if (!mask) return NONE;
    object_iterator_new(&iterator, mask, 0);
    while ((item = object_iterator_next(&iterator)) != NULL) {
        boolean is_vehicle = item->object.type == _object_type_vehicle;
        real distance;
        struct collision_model_instance model;
        struct collision_model_test_pill_result model_hit;
        if (is_vehicle && !vehicle_lift_enabled()) continue;
        if (!grabbable(iterator.index) || vr_world_interaction_remote_owned(iterator.index)) continue;
        vector_from_points3d(point, &item->object.bounding_sphere_center, &ray);
        distance = magnitude3d(&ray);
        if (distance > item->object.bounding_sphere_radius + contact_radius) continue;
        if (++narrow_tests>32) break;
        /* The bounding sphere only rejects distant objects. Acquisition
         * requires the tracked hand's finite collision sphere to overlap the
         * object's authored collision model; no hand-to-target ray selects it. */
        if (!collision_model_instance_new(&model, iterator.index) ||
            !collision_model_test_pill(&model, point, &stationary, contact_radius, &model_hit)) continue;
        vector_from_points3d(point, &item->object.bounding_sphere_center, &ray);
        distance = magnitude3d(&ray);
        /* Keep LOS solely as a through-wall guard for a hand pose that has
         * penetrated the player's visible world collision. It cannot acquire
         * a target; model overlap above is mandatory. */
        vector_from_points3d(camera, point, &ray);
        if (collision_test_vector(_collision_test_for_line_of_sight_flags, camera, &ray, unit, &hit) &&
            !(hit.type == _collision_result_object && hit.object_index == iterator.index)) continue;
        if (distance < best_center_distance) {
            best_center_distance = distance; selected = iterator.index; *contact = *point;
        }
    }
    return selected;
}
void vr_world_interaction_tick(void)
{
    short local;
    long player, unit, tick = game_time_get();
    real units = vr_units_per_metre();
    real_point3d camera;
    int hand, h, n;
    unsigned int buttons;
    float triggers[2],thumbs[4];
    interaction_log_session_state();
    if (!vr_active() ||
        (!world_grab_enabled() && !vehicle_lift_enabled()) ||
        !vr_controller(&buttons,triggers,thumbs) ||
        !vr_world_authority(game_connection()==_game_connection_local,
            game_connection()==_game_connection_network_server,network_coop_active()) ||
        (game_connection()!=_game_connection_local && !network_interaction_host_ready()) ||
        cinematic_in_progress() || !(units > 0)) { vr_world_interaction_reset(); return; }
    local = local_player_get_next(NONE);
    player = local != NONE ? local_player_get_player_index(local) : NONE;
    unit = player != NONE ? player_get(player)->unit_index : NONE;
    if (unit == NONE || director_inhibited_input(local) || object_get(unit)->object.parent_object_index != NONE ||
        TEST_FLAG(object_get(unit)->object.damage_flags, _object_dead_bit)) { vr_world_interaction_reset(); return; }
    if (tick==last_tick && unit==last_unit) return;
    if (tick < last_tick || tick > last_tick+1 || unit != last_unit) vr_world_interaction_reset();
    last_tick = tick; last_unit = unit;
    unit_get_camera_position(unit, &camera);
    for (hand=0;hand<2;++hand) {
        struct world_hand *held = &hands[hand];
        int pressed = 0, released = 0, grip = vr_interaction_grip(hand, &pressed, &released);
        real_point3d point;
        real_vector3d forward, up, change;
        boolean allowed = !(hand == vr_weapon_hand() && !vr_hand_empty()) &&
            !(hand != vr_weapon_hand() && vr_two_handed());
        /* Physics ticks need their own edge history: a72Hz rendered-frame
         * edge may fall between30Hz game ticks. Require release after reset. */
        pressed = grip && !previous_grip[hand];
        released = !grip && previous_grip[hand];
        previous_grip[hand]=grip;
        if (!allowed || !vr_hand_world(hand, camera.n, point.n, forward.n, up.n)) {
            previous_grip[hand]=1; release_hand(hand, FALSE, units,
				allowed?"hand-tracking-lost":"hand-no-longer-free"); continue;
        }
        if (held->sample_valid) {
            vector_from_points3d(&held->previous, &point, &change);
            if (magnitude3d(&change) > 0.45f*units) {
				held->velocity=*global_zero_vector3d;
				if(!held->strain_logged)platform_log("VR world: hand sample rebased hand=%d object=%08lx grip=%d held=%d movement_m=%.3f",
					hand,held->active?held->index:NONE,grip,held->active,(float)magnitude3d(&change)/(float)units);
				held->strain_logged=TRUE;
			} else for (n=0;n<3;++n) held->velocity.n[n] = held->velocity.n[n]*0.55f + change.n[n]*0.45f;
        }
        if(held->active) {
			int limited=0;
			if(!vr_interaction_hold_target_step(held->point.n,point.n,.45f*units,&limited)) {
				release_hand(hand,FALSE,units,"invalid-hand-target");continue;
			}
			if(limited&&!held->strain_logged) {
				platform_log("VR world: hold target rate-limited hand=%d object=%08lx grip=held max_step_m=0.450",
					hand,held->index);held->strain_logged=TRUE;
			} else if(!limited)held->strain_logged=FALSE;
		} else held->point=point;
		held->previous=point;held->forward=forward;held->up=up;held->sample_valid=TRUE;
        if (held->active && (!grip || !grabbable(held->index) || vr_interaction_owner(hand)!=VR_INTERACTION_WORLD)) {
            boolean intentional=!grip && released && vr_interaction_owner(hand)==VR_INTERACTION_WORLD;
			release_hand(hand,intentional,units,intentional?"grip-released":(!grip?"grabbable-lost":"interaction-owner-lost")); continue;
        }
        if (!held->active && grip && pressed && vr_interaction_owner(hand)==VR_INTERACTION_NONE) {
            real_point3d contact;
            long index = candidate(&point, &camera, unit, units, &contact);
            struct object_datum *item = index != NONE ? grabbable(index) : NULL;
            if (item && vr_interaction_claim(hand,VR_INTERACTION_WORLD)) {
                held->active=TRUE; held->index=index;
                vector_from_points3d(&item->object.position,&contact,&change);
                local_vector(&item->object.forward,&item->object.up,&change,(real_vector3d *)&held->local_grab);
                local_vector(&forward,&up,&item->object.forward,&held->local_forward);
                local_vector(&forward,&up,&item->object.up,&held->local_up);
                held->velocity=*global_zero_vector3d;
                vr_haptic(hand,0.25f,0.035f);
				platform_log("VR world: grab hand=%d object=%08lx second=%d acquisition=authored-contact-plus-fresh-grip",
					hand,index,hands[1-hand].active&&hands[1-hand].index==index);
            } else platform_log("VR world: contact grab miss hand=%d radius=%.2f cm world=%d vehicle_lift=%d (hand sphere did not overlap an eligible collision model)",
                hand,(float)vr_world_hand_contact_radius((float)config_real("vr.interaction_reach"),(float)units)*100.0f/(float)units,
                world_grab_enabled(),vehicle_lift_enabled());
        }
    }
    for (hand=0;hand<2;++hand) {
        struct world_hand *held=&hands[hand];
        struct object_datum *item;
        real_vector3d error = {0}, offset, target_forward, target_up, angular, second, velocity;
        int count=0;
        real mobility;
        if (!held->active || (hand==1 && hands[0].active && hands[0].index==held->index)) continue;
        item=grabbable(held->index); if (!item) continue;
        for (h=0;h<2;++h) if (hands[h].active && hands[h].index==held->index) {
            world_vector(&item->object.forward,&item->object.up,(real_vector3d *)&hands[h].local_grab,&offset);
            for (n=0;n<3;++n) error.n[n] += hands[h].point.n[n]-item->object.position.n[n]-offset.n[n];
            ++count;
        }
        scale_vector3d(&error,1.0f/count,&error);
		if (magnitude3d(&error)>0.65f*units) {
			if(!held->strain_logged)platform_log("VR world: hold strain hand=%d object=%08lx grip=held separation_m=%.3f action=keep-contact",
				hand,held->index,(float)magnitude3d(&error)/(float)units);
			held->strain_logged=TRUE;
		} else if(magnitude3d(&error)<0.50f*units)held->strain_logged=FALSE;
        if (item->object.type == _object_type_vehicle) {
			if (!vehicle_lift_apply(held->index, &error, hand, count, units, &mobility)) {
				if(!held->strain_logged)platform_log("VR world: vehicle lift paused hand=%d object=%08lx reason=outside-safe-envelope grip=held",
					hand,held->index);
				held->strain_logged=TRUE;
                continue;
            }
			{
				real strain_metres = magnitude3d(&error) / units;
				real speed_metres_per_second = magnitude3d(&item->object.translational_velocity) *
					(real)TICKS_PER_SECOND / units;
				if (count == 1)
					vr_world_interaction_weight_feedback(hand, mobility, (float)strain_metres,
						(float)speed_metres_per_second);
				else for (h = 0; h < 2; ++h)
					if (hands[h].active && hands[h].index == held->index)
						vr_world_interaction_weight_feedback(h, mobility, (float)strain_metres,
							(float)speed_metres_per_second);
			}
            continue;
        }
        mobility=vr_world_object_mobility(held->index);
        vr_interaction_impact_track(held->index,unit,mobility,units);
        if (!vr_world_spring(error.n,item->object.translational_velocity.n,mobility,count,units,global_gravity,velocity.n)) {
			if(!held->strain_logged)platform_log("VR world: constraint paused hand=%d object=%08lx reason=invalid-physics-state grip=held",
				hand,held->index);
			held->strain_logged=TRUE;continue;
        }
        if(count==1) weight_feedback(hand,mobility,magnitude3d(&error),&velocity,units);
        else for(h=0;h<2;h++) if(hands[h].active&&hands[h].index==held->index)
            weight_feedback(h,mobility,magnitude3d(&error),&velocity,units);
        world_vector(&held->forward,&held->up,&held->local_forward,&target_forward);
        world_vector(&held->forward,&held->up,&held->local_up,&target_up);
        cross_product3d(&item->object.forward,&target_forward,&angular);
        cross_product3d(&item->object.up,&target_up,&second);
        add_vectors3d(&angular,&second,&angular);
        if (count==2) {
            real_vector3d local_line, object_line, hand_line;
            vector_from_points3d(&hands[0].local_grab,&hands[1].local_grab,&local_line);
            world_vector(&item->object.forward,&item->object.up,&local_line,&object_line);
            vector_from_points3d(&hands[0].point,&hands[1].point,&hand_line);
            if (normalize3d(&object_line)>0.01f && normalize3d(&hand_line)>0.01f) {
                cross_product3d(&object_line,&hand_line,&second);
                for (n=0;n<3;++n) angular.n[n]=angular.n[n]*0.25f+second.n[n];
            }
        }
        scale_vector3d(&angular,0.12f,&angular);
        if (vr_world_limit(angular.n,0.15f)) vr_world_object_velocity(held->index,&velocity,&angular);
    }
}
#endif
