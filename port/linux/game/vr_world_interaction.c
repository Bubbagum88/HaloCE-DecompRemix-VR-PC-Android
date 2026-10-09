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
#include "physics/physics.h"
#include "physics/physics_definitions.h"
#include "units/units.h"
#include "units/vehicle_datum.h"
#include "units/vehicle_definitions.h"
#include "units/vehicles.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_world_interaction.h"
#include "vr_world_math.h"
#include "vr_weight_feedback_math.h"
#include "vr_world_props.h"
#include "vr_interaction_impact.h"
#include "network_coop.h"
#include "network_interaction.h"
#include "vr_vehicle_lift_math.h"
#include <math.h>
#include <string.h>

void platform_log(char const *format, ...);

static struct world_hand {
    boolean active, sample_valid;
    long index;
    real_point3d local_grab, previous, point;
    real_vector3d velocity, local_forward, local_up, forward, up;
} hands[2];
static long last_tick = NONE, last_unit = NONE;
static int previous_grip[2] = {1,1};
static unsigned long weight_haptic_at[2];
unsigned long system_milliseconds(void);

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
	struct object_datum *object = vr_world_object_get(index);
	if (object)
		return object;
	return vehicle_lift_get(index) ? object_get(index) : NULL;
}

/* Apply only a tiny, capped global-up velocity response. The native vehicle
 * update retains gravity and swept collision; we never set position/rotation. */
static boolean vehicle_lift_apply(long index, real_vector3d const *error,
	int hands, real units, real *mobility_out)
{
	struct vehicle_datum *vehicle = vehicle_lift_get(index);
	struct object_definition *definition;
	real_vector3d up, current_vertical, requested_vertical, target_vertical, delta;
	real speed, up_speed, horizontal_speed_squared, max_speed, vertical_limit;
	real mobility, alpha, error_up, target_up;
	if (!vehicle || !error || !mobility_out || (hands != 1 && hands != 2) ||
		!isfinite(units) || !(units > 0.0f && units < 100.0f) ||
		!valid_real_vector3d(error) || !valid_real_vector3d(global_up3d))
		return FALSE;
	up = *global_up3d;
	if (normalize3d(&up) < 0.99f || !valid_real_vector3d(&up))
		return FALSE;
	speed = magnitude3d(&vehicle->object.translational_velocity);
	if (!isfinite(speed) || speed > units * 0.20f)
		return FALSE;
	up_speed = dot_product3d(&vehicle->object.translational_velocity, &up);
	scale_vector3d(&up, up_speed, &current_vertical);
	definition = object_definition_get(vehicle->definition_index);
	if (!definition || !isfinite(definition->object.acceleration_scale))
		return FALSE;
	mobility = PIN(definition->object.acceleration_scale, 0.25f, 2.0f);
	alpha = (hands == 2 ? 0.50f : 0.35f) * (real)sqrt(mobility);
	error_up = dot_product3d(error, &up);
	requested_vertical = current_vertical;
	for (int axis = 0; axis < 3; ++axis)
		requested_vertical.n[axis] += up.n[axis] * error_up * alpha;
	if (!vr_vehicle_lift_target_velocity(current_vertical.n, requested_vertical.n,
		hands, units, target_vertical.n))
		return FALSE;
	/* Leave the existing horizontal speed untouched while respecting the total
	 * grab-speed envelope. */
	horizontal_speed_squared = 0.0f;
	for (int axis = 0; axis < 3; ++axis)
	{
		real horizontal = vehicle->object.translational_velocity.n[axis] - up.n[axis] * up_speed;
		horizontal_speed_squared += horizontal * horizontal;
	}
	max_speed = units * 0.20f;
	if (!isfinite(horizontal_speed_squared) || horizontal_speed_squared > max_speed * max_speed)
		return FALSE;
	vertical_limit = (real)sqrt((double)max_speed * max_speed - horizontal_speed_squared);
	if (!isfinite(vertical_limit))
		return FALSE;
	target_up = PIN(dot_product3d(&target_vertical, &up), -vertical_limit, vertical_limit);
	scale_vector3d(&up, target_up, &target_vertical);
	for (int axis = 0; axis < 3; ++axis)
		delta.n[axis] = target_vertical.n[axis] - current_vertical.n[axis];
	if (!valid_real_vector3d(&delta) || magnitude3d(&delta) > units * 0.0526f)
		return FALSE;
	/* vehicle_accelerate adds a bounded velocity delta. A pure global-up input
	 * has zero cross product with global_up3d, so it cannot inject yaw torque. */
	vehicle_accelerate(index, &delta);
	*mobility_out = mobility;
	return TRUE;
}

void vr_world_interaction_weight_feedback(int hand, float mobility,
	float strain_metres, float speed_metres_per_second)
{
    unsigned long now;
    float amplitude;
    if(hand<0||hand>1||!config_boolean("vr.weight_haptics")||
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
static void release_hand(int hand, boolean throwing, real units)
{
    struct world_hand *held = &hands[hand];
    struct object_datum *item = held->active ? grabbable(held->index) : NULL;
    if (held->active) {
        if (throwing && item && item->object.type != _object_type_vehicle &&
            !(hands[1-hand].active && hands[1-hand].index == held->index)) {
            real_vector3d velocity = held->velocity;
            if (vr_world_limit(velocity.n, units * 0.24f))
                vr_world_object_velocity(held->index, &velocity, &item->object.angular_velocity);
        }
        platform_log("VR world: release hand=%d object=%08lx throw=%d", hand, held->index, throwing);
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
    real best = 0.12f * units;
    long selected = NONE;
    int narrow_tests=0;
    real_vector3d ray;
    struct collision_result hit;
    unsigned long mask = _object_mask_weapon | _object_mask_equipment | _object_mask_scenery;
    if (vehicle_lift_enabled()) mask |= _object_mask_vehicle;
    object_iterator_new(&iterator, mask, 0);
    while ((item = object_iterator_next(&iterator)) != NULL) {
        boolean is_vehicle = item->object.type == _object_type_vehicle;
        real distance;
        if (is_vehicle && !vehicle_lift_enabled()) continue;
        if (!grabbable(iterator.index) || vr_world_interaction_remote_owned(iterator.index)) continue;
        vector_from_points3d(point, &item->object.bounding_sphere_center, &ray);
        distance = magnitude3d(&ray);
        if (distance > item->object.bounding_sphere_radius + best ||
            (!is_vehicle && distance > 0.8f * units)) continue;
        if (++narrow_tests>32) break;
        if (collision_test_vector(FLAG(_collision_test_front_facing_surfaces_bit) |
            FLAG(_collision_test_back_facing_surfaces_bit) | FLAG(_collision_test_structure_bit) |
            FLAG(_collision_test_objects_bit) | _collision_test_objects_all_types_flags,
            point, &ray, unit, &hit)) {
            if (hit.type != _collision_result_object || hit.object_index != iterator.index) continue;
            vector_from_points3d(point, &hit.point, &ray);
            distance = magnitude3d(&ray);
        } else continue; /* A bounding sphere is only broad phase, not a surface. */
        if (distance < best) {
            real_point3d surface=hit.point;
            vector_from_points3d(camera,&surface,&ray);
            if (collision_test_vector(_collision_test_for_line_of_sight_flags,camera,&ray,unit,&hit) &&
                !(hit.type==_collision_result_object && hit.object_index==iterator.index)) continue;
            best=distance; selected=iterator.index; *contact=surface;
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
    int hand;
    unsigned int buttons;
    float triggers[2],thumbs[4];
    if (!vr_active() || !config_boolean("vr.world_interaction") ||
        !vr_controller(&buttons,triggers,thumbs) ||
        !vr_world_authority(game_connection()==_game_connection_local,
            game_connection()==_game_connection_network_server,network_coop_active()) ||
        (game_connection()!=_game_connection_local && !network_interaction_host_ready()) ||
        cinematic_in_progress() || !vr_aiming() || !(units > 0)) { vr_world_interaction_reset(); return; }
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
            previous_grip[hand]=1; release_hand(hand, FALSE, units); continue;
        }
        if (held->sample_valid) {
            vector_from_points3d(&held->previous, &point, &change);
            if (magnitude3d(&change) > 0.45f*units) { release_hand(hand,FALSE,units); continue; }
            for (int n=0;n<3;++n) held->velocity.n[n] = held->velocity.n[n]*0.55f + change.n[n]*0.45f;
        }
        held->previous = held->point = point; held->forward=forward; held->up=up; held->sample_valid=TRUE;
        if (held->active && (!grip || !grabbable(held->index) || vr_interaction_owner(hand)!=VR_INTERACTION_WORLD)) {
            release_hand(hand, !grip && released && vr_interaction_owner(hand)==VR_INTERACTION_WORLD, units); continue;
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
                vr_haptic(hand,0.25f,0.035f);
                platform_log("VR world: grab hand=%d object=%08lx second=%d",hand,index,hands[1-hand].active&&hands[1-hand].index==index);
            }
        }
    }
    for (hand=0;hand<2;++hand) {
        struct world_hand *held=&hands[hand];
        struct object_datum *item;
        real_vector3d error = {0}, offset, target_forward, target_up, angular, second, velocity;
        int count=0, h;
        real mobility;
        if (!held->active || (hand==1 && hands[0].active && hands[0].index==held->index)) continue;
        item=grabbable(held->index); if (!item) continue;
        for (h=0;h<2;++h) if (hands[h].active && hands[h].index==held->index) {
            world_vector(&item->object.forward,&item->object.up,(real_vector3d *)&hands[h].local_grab,&offset);
            for (int n=0;n<3;++n) error.n[n] += hands[h].point.n[n]-item->object.position.n[n]-offset.n[n];
            ++count;
        }
        scale_vector3d(&error,1.0f/count,&error);
        if (magnitude3d(&error)>0.65f*units) { release_hand(hand,FALSE,units); continue; }
        if (item->object.type == _object_type_vehicle) {
            if (!vehicle_lift_apply(held->index, &error, count, units, &mobility)) {
                release_hand(hand, FALSE, units);
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
            release_hand(hand,FALSE,units); continue;
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
                for (int n=0;n<3;++n) angular.n[n]=angular.n[n]*0.25f+second.n[n];
            }
        }
        scale_vector3d(&angular,0.12f,&angular);
        if (vr_world_limit(angular.n,0.15f)) vr_world_object_velocity(held->index,&velocity,&angular);
    }
}
#endif
