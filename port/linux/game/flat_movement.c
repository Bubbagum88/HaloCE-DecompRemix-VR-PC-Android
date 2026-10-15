/* Test72: the flat builds' movement extras (flat_movement.h): SPRINT, SLIDE,
 * WALL RUN and WALL JUMP for Android, Windows and Linux without a headset.
 * The owner: "for the flat/android ports see about adding the parkour features
 * to them alongside slide, sprint with toggle options ... those seem to not
 * need to be VR exclusive", and "wall grab wouldnt really be there of course".
 *
 * The VR build's modules (vr_slide.c, vr_parkour.c) are left exactly as they
 * are; this one repeats their game-side flow without the headset (the camera
 * aims a wall jump, a key or a full push forward sprints) and shares their
 * kinematics (vr_slide_math.h, vr_parkour_math.h, vr_sprint_melee_math.h).
 * Every extra is off until turned on (movement.*), acts only on the local
 * player's own body, offline (sprint, slide) or on a co-op host (wall moves),
 * and never touches the network. */
#ifndef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "game/players.h"
#include "units/units.h"
#include "units/bipeds.h"
#include "units/biped_definitions.h"
#include "objects/objects.h"
#include "objects/object_definitions.h"
#include "objects/damage.h"
#include "ai/actors.h"
#include "ai/actor_types.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "physics/collisions.h"
#include "../src/port_config.h"
#include "flat_movement.h"
#include "network_coop.h"
#include "vr_npc_interaction.h"
#include "vr_body_reactions.h"
#include "vr_slide_math.h"
#include "vr_parkour_math.h"
#include "vr_sprint_melee_math.h"

void platform_log(char const *format, ...);
/* xinput_sdl.c: controls.sprint held (in play) */
int platform_sprint_held(void);

/* Halo's world unit is ten feet: the flat game has no headset to scale it */
#define FLAT_UNITS_PER_METRE (1.0f / 3.048f)
#define FLAT_WALL_FLAGS (FLAG(_collision_test_structure_bit) | FLAG(_collision_test_objects_bit) | \
	FLAG(_collision_test_objects_scenery_bit))
/* a wall run starts on a wall reached within a second of pressing Jump (vr_parkour.c's) */
#define FLAT_WALLRUN_ENTRY_TICKS (TICKS_PER_SECOND)
/* SPRINT AUTO: the stick held fully forward this long */
#define FLAT_SPRINT_AUTO_TICKS 12
#define FLAT_SLIDE_MAXIMUM_HITS 8

/* ---------- who may: the local player's own body, in play */

static short flat_local(long unit_index)
{
	short local = local_player_get_next(NONE);
	long player = local != NONE ? local_player_get_player_index(local) : NONE;

	if (player == NONE || player_get(player)->unit_index != unit_index || unit_index == NONE)
		return NONE;
	if (cinematic_in_progress() || director_inhibited_input(local))
		return NONE;
	return local;
}

/* ---------- SPRINT */

static struct
{
	long unit, tick;
	int latched, was_pressed;
	long forward_ticks;
	boolean auto_running;
	float effort;
} sprint = { NONE, NONE };

/* this tick's sprint (0 or 1), once a tick whatever asks */
static float flat_sprint_effort(long unit_index)
{
	struct biped_datum *biped = biped_try_and_get(unit_index);
	char const *mode = config_string("movement.sprint");
	long tick = game_time_get();
	boolean toggle = mode && !strcmp(mode, "toggle"), hold = mode && !strcmp(mode, "hold");
	boolean automatic = mode && !strcmp(mode, "auto");
	boolean seated, eligible;

	if (sprint.unit == unit_index && sprint.tick == tick)
		return sprint.effort;
	if (sprint.unit != unit_index)
	{
		sprint.latched = sprint.was_pressed = 0;
		sprint.forward_ticks = 0;
		sprint.auto_running = FALSE;
	}
	sprint.unit = unit_index;
	sprint.tick = tick;
	sprint.effort = 0.0f;
	if (!biped || (!toggle && !hold && !automatic))
	{
		sprint.latched = 0;
		return 0.0f;
	}
	seated = biped->object.parent_object_index != NONE;
	eligible = !seated && !game_time_get_paused();
	if (automatic)
	{
		/* a full push forward (a stick or a touch stick), held a moment */
		float forward = (float)biped->unit.throttle.i, sideways = fabsf((float)biped->unit.throttle.j);
		if (!eligible || forward < 0.5f)
		{
			sprint.forward_ticks = 0;
			sprint.auto_running = FALSE;
		}
		else if (forward >= 0.9f && sideways < 0.5f && ++sprint.forward_ticks >= FLAT_SPRINT_AUTO_TICKS)
			sprint.auto_running = TRUE;
		sprint.effort = sprint.auto_running ? 1.0f : 0.0f;
	}
	else
	{
		/* the VR build's latch: a fresh press toggles; a seat clears it */
		sprint.effort = vr_button_sprint_input_mode(1, toggle, platform_sprint_held() != 0, 0, eligible, 1, seated,
			&sprint.latched, &sprint.was_pressed) ? 1.0f : 0.0f;
	}
	return sprint.effort;
}

real flat_movement_sprint_scale(long unit_index)
{
	/* stock servers negotiate no sprint: offline only, as VR's (vr_player_sprint_scale) */
	if (game_connection() != _game_connection_local || flat_local(unit_index) == NONE)
		return 1.0f;
	return vr_sprint_scale_for_effort((float)config_real("movement.sprint_speed"), flat_sprint_effort(unit_index));
}

/* ---------- SLIDE (vr_slide.c's flow, the button crouch) */

static struct
{
	boolean active;
	long biped;
	float velocity[2]; /* metres a second, world horizontal */
	long ticks, airborne_ticks, stall_ticks, sprint_recent;
	boolean crouch_was;
	long hit[FLAT_SLIDE_MAXIMUM_HITS];
	int hit_count;
} slide = { FALSE, NONE };

boolean flat_movement_sliding(void)
{
	return slide.active;
}

static void flat_slide_end(char const *why)
{
	if (slide.active)
		platform_log("flat slide: ended (%s) after %.2f s at %.1f m/s", why, slide.ticks / 30.0,
			sqrt(slide.velocity[0] * slide.velocity[0] + slide.velocity[1] * slide.velocity[1]));
	slide.active = FALSE;
	slide.ticks = slide.airborne_ticks = slide.stall_ticks = 0;
	slide.hit_count = 0;
}

/* fist combat's kinds (vr_extra_interaction.c): Grunts, Jackals and the rest
are knocked down by a fast slide; Elites and Hunters are not */
static boolean flat_knockable(long target)
{
	struct unit_datum *u = target != NONE ? unit_try_and_get(target) : NULL;
	struct actor_datum *a = u && u->unit.actor_index != NONE ? actor_try_and_get(u->unit.actor_index) : NULL;
	return !a || (a->meta.type != _actor_elite && a->meta.type != _actor_hunter);
}

static void flat_slide_impacts(long biped_index, struct biped_datum *biped, float units, float speed)
{
	struct object_iterator it;
	struct unit_datum *other;
	real_vector3d direction = { slide.velocity[0], slide.velocity[1], 0.0f };
	float damage = (float)config_real("movement.slide_damage");

	if (!(speed > 4.0f) || normalize3d(&direction) < 0.001f)
		return;
	object_iterator_new(&it, _object_mask_biped, 0);
	while ((other = object_iterator_next(&it)) != NULL)
	{
		real_vector3d to;
		real distance, facing, reach;
		float scale;
		int index;
		long target = it.index;
		struct object_definition *definition;

		if (target == biped_index || TEST_FLAG(other->object.damage_flags, _object_dead_bit) ||
			other->unit.player_index != NONE || other->object.parent_object_index != NONE)
			continue;
		for (index = 0; index < slide.hit_count && slide.hit[index] != target; index++)
			;
		if (index < slide.hit_count)
			continue;
		vector_from_points3d(&biped->object.bounding_sphere_center, &other->object.bounding_sphere_center, &to);
		to.k = 0.0f;
		distance = normalize3d(&to);
		reach = biped->object.bounding_sphere_radius * 0.6f + other->object.bounding_sphere_radius * 0.6f + 0.25f * units;
		if (distance > reach)
			continue;
		facing = dot_product3d(&to, &direction);
		scale = vr_slide_impact_scale(speed, facing, damage);
		if (scale <= 0.0f)
			continue;
		if (slide.hit_count < FLAT_SLIDE_MAXIMUM_HITS)
			slide.hit[slide.hit_count++] = target;
		definition = object_definition_get(other->definition_index);
		{
			real_vector3d push;
			real mobility = definition && isfinite(definition->object.acceleration_scale) ?
				PIN(definition->object.acceleration_scale, 0.0f, 1.0f) : 1.0f;
			boolean knocked = flat_knockable(target) && speed >= 6.0f && facing >= 0.7f;
			scale_vector3d(&direction, speed * 0.5f * mobility * units / 30.0f, &push);
			push.k = 0.08f * units * mobility;
			if (knocked)
				vr_npc_interaction_knock(target, &other->object.bounding_sphere_center, &direction, speed * 0.7f);
			else
			{
				biped_accelerate(target, &push);
				vr_body_reaction_hit(target, &other->object.bounding_sphere_center, &direction, 0.6f * mobility);
			}
			{
				long blow = unit_unarmed_melee_damage(biped_index);
				struct damage_data hit;
				if (blow == NONE)
					blow = damage_globals_impact_effect();
				if (blow != NONE)
				{
					damage_data_new(&hit, blow);
					hit.owner_object_index = biped_index;
					hit.owner_player_index = biped->unit.player_index;
					hit.owner_team_index = biped->object.owner_team_index;
					hit.origin = hit.epicenter = other->object.bounding_sphere_center;
					hit.direction = direction;
					hit.scale = scale;
					object_cause_contact_damage(&hit, target, NONE, NONE, NONE, &direction);
				}
			}
			platform_log("flat slide: struck %08lx at %.1f m/s (%s, damage %.2f)", target, speed,
				knocked ? "knocked down" : mobility < 0.4f ? "barely moved" : "staggered", scale);
			if (mobility < 0.4f)
				flat_slide_end("a heavy enemy");
		}
		if (!slide.active)
			return;
	}
}

void flat_movement_slide_update(long biped_index, real_vector3d const *forward, real_vector3d const *throttle,
	real run_speed_units, real_vector3d *movement_desired, real *acceleration_maximum)
{
	struct biped_datum *biped;
	float units = FLAT_UNITS_PER_METRE, run, speed, actual;
	boolean crouch, crouch_edge, airborne;
	real_vector3d horizontal;

	if (!config_boolean("movement.slide") || game_connection() != _game_connection_local ||
		flat_local(biped_index) == NONE || !forward || !movement_desired ||
		!(biped = biped_try_and_get(biped_index)))
	{
		if (slide.active)
			flat_slide_end("unavailable");
		slide.crouch_was = FALSE;
		return;
	}
	if (slide.active && slide.biped != biped_index)
		flat_slide_end("another body");
	run = (float)run_speed_units / units;
	crouch = TEST_FLAG(biped->unit.control_flags, _unit_control_crouch_modifier_bit);
	crouch_edge = crouch && !slide.crouch_was;
	slide.crouch_was = crouch;
	airborne = TEST_FLAG(biped->biped.flags, _biped_airborne_bit);
	horizontal = biped->object.translational_velocity;
	horizontal.k = 0.0f;
	actual = (float)magnitude3d(&horizontal) * 30.0f / units;
	if (flat_sprint_effort(biped_index) >= 0.5f)
		slide.sprint_recent = 9;
	else if (slide.sprint_recent > 0)
		slide.sprint_recent--;

	if (!slide.active)
	{
		/* a crouch begun while sprinting on the ground, at a run or faster */
		if (!crouch_edge || slide.sprint_recent <= 0 || airborne || !(actual >= 0.85f * run))
			return;
		speed = vr_slide_entry_speed(actual, (float)config_real("movement.slide_momentum"));
		normalize3d(&horizontal);
		slide.velocity[0] = (float)horizontal.i * speed;
		slide.velocity[1] = (float)horizontal.j * speed;
		slide.active = TRUE;
		slide.biped = biped_index;
		slide.ticks = slide.airborne_ticks = slide.stall_ticks = 0;
		slide.hit_count = 0;
		platform_log("flat slide: started at %.1f m/s (run %.1f)", speed, run);
	}
	if (!crouch)
	{
		flat_slide_end("stood");
		return;
	}
	if (TEST_FLAG(biped->unit.control_flags, _unit_control_jump_bit) && config_boolean("movement.slide_jump_cancel"))
	{
		flat_slide_end("jump");
		return;
	}
	slide.airborne_ticks = airborne ? slide.airborne_ticks + 1 : 0;
	if (slide.airborne_ticks > 8)
	{
		flat_slide_end("left the ground");
		return;
	}
	if (slide.ticks > (long)(vr_slide_duration((float)config_real("movement.slide_momentum")) * 30.0f))
	{
		flat_slide_end("time");
		return;
	}
	speed = sqrtf(slide.velocity[0] * slide.velocity[0] + slide.velocity[1] * slide.velocity[1]);
	if (slide.ticks > 3 && actual < 0.35f * speed)
	{
		if (++slide.stall_ticks >= 2)
		{
			flat_slide_end("a wall");
			return;
		}
	}
	else
		slide.stall_ticks = 0;
	{
		float ground[3] = { (float)biped->biped.ground_plane.n.i, (float)biped->biped.ground_plane.n.j,
			(float)biped->biped.ground_plane.n.k };
		float steer[2] = { 0.0f, 0.0f }, amount = 0.0f;
		real_vector3d facing = *forward;
		facing.k = 0.0f;
		if (throttle && normalize3d(&facing) > 0.001f)
		{
			steer[0] = (float)(facing.i * throttle->i - facing.j * throttle->j);
			steer[1] = (float)(facing.j * throttle->i + facing.i * throttle->j);
			amount = (float)sqrt(throttle->i * throttle->i + throttle->j * throttle->j);
		}
		speed = vr_slide_step(slide.velocity, 1.0f / 30.0f, (float)config_real("movement.slide_friction"),
			airborne ? NULL : ground, steer, amount);
		if (speed < 0.5f * run)
		{
			flat_slide_end("slowed");
			return;
		}
		if (normalize3d(&facing) > 0.001f)
		{
			real vx = slide.velocity[0] * units / 30.0f, vy = slide.velocity[1] * units / 30.0f;
			movement_desired->i = vx * facing.i + vy * facing.j;
			movement_desired->j = -vx * facing.j + vy * facing.i;
			movement_desired->k = 0.0f;
			if (acceleration_maximum)
				*acceleration_maximum = MAX(*acceleration_maximum, (real)(speed * units / 30.0f));
		}
	}
	slide.ticks++;
	if (config_real("movement.slide_damage") > 0.0)
		flat_slide_impacts(biped_index, biped, units, speed);
}

/* ---------- WALL RUN and WALL JUMP (vr_parkour.c's, without the hands) */

static struct
{
	long unit, tick;
	int jump_down, jump_age, run_ticks, running, jumped_wall, wall_valid;
	int walljump_age, lost_ticks;
	real run_speed;
	real_vector3d wall_normal;
	real_point3d wall_point;
} wall = { NONE, NONE };

static void flat_wall_reset(void)
{
	memset(&wall, 0, sizeof(wall));
	wall.unit = wall.tick = NONE;
	wall.jump_down = 1;
	wall.jump_age = 1000;
	wall.walljump_age = 1000;
}

void flat_movement_reset(void)
{
	flat_wall_reset();
	flat_slide_end("reset");
	slide.crouch_was = FALSE;
	sprint.unit = sprint.tick = NONE;
	sprint.latched = sprint.was_pressed = 0;
	sprint.auto_running = FALSE;
}

static boolean flat_wall_surface(real_point3d const *from, real_vector3d const *vector, long unit, int low,
	struct collision_result *result)
{
	memset(result, 0, sizeof(*result));
	result->object_index = NONE;
	if (!collision_test_vector(FLAT_WALL_FLAGS, from, vector, unit, result) || !(result->t >= 0 && result->t <= 1))
		return FALSE;
	return vr_pk_runnable(result->plane.n.n, low) ? TRUE : FALSE;
}

/* local play, and a co-op host's own player (vr_parkour.c's rule: a client's
prediction would be refused by the host, and in PvP it would be an advantage) */
static boolean flat_wall_allowed(long unit)
{
	short connection = game_connection();
	struct biped_datum *biped;

	if (!(connection == _game_connection_local || (connection == _game_connection_network_server && network_coop_active())))
		return FALSE;
	if (flat_local(unit) == NONE || game_time_get_paused())
		return FALSE;
	biped = biped_try_and_get(unit);
	return biped && biped->object.parent_object_index == NONE && !TEST_FLAG(biped->object.damage_flags, _object_dead_bit) &&
		!TEST_FLAG(biped->biped.flags, _biped_no_collision_bit) && !TEST_FLAG(biped->unit.flags, _unit_suspended_bit);
}

void flat_movement_parkour_velocity(long unit, real_point3d const *position, float height, float radius,
	real_vector3d *velocity)
{
	struct biped_datum *biped;
	struct collision_result hit_wall;
	real_vector3d left, wall_move = { 0 };
	real units = FLAT_UNITS_PER_METRE, per_second = FLAT_UNITS_PER_METRE / (real)TICKS_PER_SECOND, throttle;
	boolean run_on = config_boolean("movement.parkour_wallrun"), jump_on = config_boolean("movement.parkour_walljump");
	int jump, edge, airborne, wall_found = 0;
	long tick = game_time_get();

	if (!run_on && !jump_on)
	{
		if (wall.unit != NONE || wall.running)
			flat_wall_reset();
		return;
	}
	if (!flat_wall_allowed(unit))
	{
		if (unit == wall.unit)
			flat_wall_reset();
		return; /* NPCs and network players never enter this path */
	}
	if (tick == wall.tick && unit == wall.unit)
		return;
	if (unit != wall.unit || tick < wall.tick || tick > wall.tick + 1)
		flat_wall_reset();
	wall.unit = unit;
	wall.tick = tick;
	biped = biped_get(unit);
	jump = TEST_FLAG(biped->unit.control_flags, _unit_control_jump_bit);
	edge = jump && !wall.jump_down;
	wall.jump_down = jump;
	if (edge)
		wall.jump_age = 0;
	else if (wall.jump_age < 1000)
		wall.jump_age++;
	if (wall.walljump_age < 1000)
		wall.walljump_age++;
	airborne = TEST_FLAG(biped->biped.flags, _biped_airborne_bit);
	if (!airborne)
	{
		wall.run_ticks = 0;
		wall.jumped_wall = 0;
		wall.wall_valid = 0;
	}
	throttle = sqrtf(biped->unit.throttle.i * biped->unit.throttle.i + biped->unit.throttle.j * biped->unit.throttle.j);
	left.i = -biped->object.forward.j;
	left.j = biped->object.forward.i;
	left.k = 0;
	{
		/* eight directions at the knee, the waist and the chest, and while
		running a longer probe toward the wall run on (vr_parkour.c's) */
		static real const levels[3] = { 0.55f, 0.85f, 0.30f };
		int level, direction;
		for (level = 0; level < 3; level++)
		{
			for (direction = 0; direction < 9; direction++)
			{
				real_vector3d ray;
				struct collision_result hit;
				real_point3d from = *position;
				real reach = radius + 0.18f * units;
				int axis;
				from.z += height * levels[level];
				if (direction < 8)
				{
					real angle = (real)direction * 0.7853982f;
					for (axis = 0; axis < 3; axis++)
						ray.n[axis] = biped->object.forward.n[axis] * cosf(angle) + left.n[axis] * sinf(angle);
				}
				else
				{
					if (!wall.running || !wall.wall_valid)
						continue;
					scale_vector3d(&wall.wall_normal, -1.0f, &ray);
					reach = radius + 0.35f * units;
				}
				ray.k = 0;
				if (normalize3d(&ray) < 0.001f)
					continue;
				scale_vector3d(&ray, reach, &ray);
				if (flat_wall_surface(&from, &ray, unit, level == 2, &hit) && (!wall_found || hit.t < hit_wall.t))
				{
					hit_wall = hit;
					wall_found = TRUE;
				}
			}
		}
	}
	if (wall_found)
	{
		boolean changed = FALSE;
		if (wall.wall_valid && dot_product3d(&wall.wall_normal, &hit_wall.plane.n) < 0.5f)
		{
			real_vector3d separation;
			vector_from_points3d(&wall.wall_point, &hit_wall.point, &separation);
			if (magnitude3d(&separation) > 0.5f * units && !wall.running)
			{
				wall.run_ticks = 0;
				wall.jumped_wall = 0;
				changed = TRUE;
			}
		}
		if (!wall.wall_valid || changed)
		{
			wall.wall_normal = hit_wall.plane.n;
			wall.wall_point = hit_wall.point;
			wall.wall_valid = 1;
		}
		else if (wall.running)
		{
			vr_pk_blend_normal(wall.wall_normal.n, hit_wall.plane.n.n);
			wall.wall_point = hit_wall.point;
		}
		wall.lost_ticks = 0;
	}
	else if (wall.running && wall.wall_valid && airborne && wall.lost_ticks < 6)
	{
		/* a run keeps over a seam or a step for a fifth of a second */
		memset(&hit_wall, 0, sizeof(hit_wall));
		hit_wall.object_index = NONE;
		hit_wall.point = wall.wall_point;
		hit_wall.plane.n = wall.wall_normal;
		wall_found = TRUE;
		wall.lost_ticks++;
	}
	if (jump_on && edge && airborne && wall_found && !wall.jumped_wall)
	{
		/* away from the wall, the way the camera looks (VR: the head) */
		real scale = vr_pk_bound((float)config_real("movement.walljump_scale"), 1, 0.5f, 1.5f);
		real upward = biped_definition_get(biped->definition_index)->biped.jump_velocity * scale;
		real_vector3d from_wall = wall.running && wall.wall_valid ? wall.wall_normal : hit_wall.plane.n;
		real_vector3d look = biped->unit.aiming_vector;
		float stick[2] = { 0, 0 }, carried[3] = { (float)velocity->i, (float)velocity->j, (float)velocity->k };
		real_vector3d facing = biped->object.forward;
		facing.k = 0;
		if (normalize3d(&look) < 0.001f)
			look = biped->object.forward;
		if (normalize3d(&facing) > 0.001f)
		{
			stick[0] = (float)(facing.i * biped->unit.throttle.i - facing.j * biped->unit.throttle.j);
			stick[1] = (float)(facing.j * biped->unit.throttle.i + facing.i * biped->unit.throttle.j);
		}
		vr_pk_wall_leap(look.n, from_wall.n, carried, stick, 5.0f * per_second * scale, upward, velocity->n);
		platform_log("flat wall jump: wall %.2f/%.2f/%.2f%s", from_wall.i, from_wall.j, from_wall.k,
			wall.running ? " (run wall)" : "");
		wall.jumped_wall = 1;
		wall.running = 0;
		wall.run_ticks = (int)(3 * TICKS_PER_SECOND);
		wall.walljump_age = 0;
		return;
	}
	if (run_on && airborne && wall.running && wall_found && throttle > 0.5f)
	{
		/* steered away from the wall: the run ends there */
		real_vector3d stick;
		stick.i = biped->object.forward.i * biped->unit.throttle.i + left.i * biped->unit.throttle.j;
		stick.j = biped->object.forward.j * biped->unit.throttle.i + left.j * biped->unit.throttle.j;
		stick.k = 0;
		if (normalize3d(&stick) > 0.001f && dot_product3d(&stick, &hit_wall.plane.n) > 0.6f)
		{
			platform_log("flat wall run: ended (steered away, %d ticks)", wall.run_ticks);
			wall.running = 0;
			wall.run_ticks = (int)(3 * TICKS_PER_SECOND);
			return;
		}
	}
	if (run_on && airborne && wall_found && (wall.running ? TRUE : throttle > 0.6f) &&
		(wall.running || wall.jump_age <= FLAT_WALLRUN_ENTRY_TICKS || wall.walljump_age <= 2 * TICKS_PER_SECOND) &&
		wall.run_ticks < vr_pk_bound((float)config_real("movement.wallrun_duration"), 2.0f, 0.5f, 3) * TICKS_PER_SECOND)
	{
		real speed = sqrtf(velocity->i * velocity->i + velocity->j * velocity->j);
		real into;
		int axis;
		if (throttle > 0.3f)
		{
			wall_move.i = biped->object.forward.i * biped->unit.throttle.i + left.i * biped->unit.throttle.j;
			wall_move.j = biped->object.forward.j * biped->unit.throttle.i + left.j * biped->unit.throttle.j;
		}
		else
		{
			wall_move.i = velocity->i;
			wall_move.j = velocity->j;
		}
		wall_move.k = 0;
		into = dot_product3d(&wall_move, &hit_wall.plane.n);
		for (axis = 0; axis < 3; axis++)
			wall_move.n[axis] -= into * hit_wall.plane.n.n[axis];
		wall_move.k = 0;
		if (normalize3d(&wall_move) > (throttle > 0.3f ? 0.15f : 0.001f) && speed > 1.0f * per_second)
		{
			real multiplier = vr_pk_bound((float)config_real("movement.wallrun_speed"), 1.25f, 1, 2);
			real limit = vr_pk_bound((float)config_real("movement.wallrun_duration"), 2.0f, 0.5f, 3) * TICKS_PER_SECOND;
			real progress = PIN((real)wall.run_ticks / limit, 0.0f, 1.0f);
			if (!wall.running)
				wall.run_speed = speed;
			speed = vr_pk_bound(fmaxf(wall.run_speed, 4.0f * per_second) * multiplier, 4.0f * per_second,
				2.0f * per_second, 9.0f * per_second);
			velocity->i = velocity->i * 0.65f + wall_move.i * speed * 0.35f;
			velocity->j = velocity->j * 0.65f + wall_move.j * speed * 0.35f;
			velocity->i -= hit_wall.plane.n.i * 0.3f * per_second;
			velocity->j -= hit_wall.plane.n.j * 0.3f * per_second;
			if (velocity->k < 0.0f)
			{
				if (progress < 0.6f)
					velocity->k = 0.0f;
				else
					velocity->k *= PIN((progress - 0.6f) / 0.4f, 0.0f, 1.0f);
			}
			if (!wall.running)
				platform_log("flat wall run: started (chained=%d)", wall.walljump_age <= 2 * TICKS_PER_SECOND);
			wall.running = 1;
			wall.run_ticks++;
			return;
		}
	}
	wall.running = 0;
}
#endif
