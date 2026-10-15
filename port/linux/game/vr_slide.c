/*
VR_SLIDE.C

Test70: SLIDE (the owner: "Sprint + Crouch = Slide"; optional). Sprinting on
the ground, a crouch begun (the button's, or with CROUCH SLIDES the head
lowered) slides the local player on with the run's momentum, giving it up
to friction and slope (vr_slide_math.h), steered a little by the stick. It
ends when the player stands, has slowed to a walk, runs its time, leaves
the ground, meets a wall, or jumps (JUMP CANCELS: at once, the momentum
carried into the jump, so a wall run can follow).

Sliding into an NPC strikes it (SLIDE IMPACT): by the speed, how square on,
and the kind (fist combat's: Grunts and Jackals are knocked down, Elites
staggered, Hunters barely moved and the slide stops on them); a small share
of a melee's damage, never a kill by itself.

Offline only (a local game), as sprint is: network movement is unchanged.
*/

#ifdef HALO_VR

#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "game/players.h"
#include "game/game_allegiance.h"
#include "units/units.h"
#include "units/bipeds.h"
#include "objects/objects.h"
#include "objects/object_definitions.h"
#include "ai/actors.h"
#include "cutscene/cinematics.h"
#include "camera/director.h"
#include "objects/damage.h"
#include "vr_slide.h"
#include "vr_slide_math.h"
#include "vr_npc_interaction.h"
#include "vr_extra_interaction.h"
#include "../src/vr.h"
#include "../src/port_config.h"

void platform_log(char const *format, ...);
void vr_body_reaction_hit(long object, real_point3d const *point, real_vector3d const *push, real strength);

#define VR_SLIDE_MAXIMUM_HITS 8

static struct
{
	boolean active;
	long biped;
	float velocity[2]; /* metres a second, world horizontal */
	long ticks, airborne_ticks, stall_ticks, sprint_recent;
	boolean crouch_was;
	long hit[VR_SLIDE_MAXIMUM_HITS];
	int hit_count;
} slide = { FALSE, NONE };

static boolean vr_slide_eligible(long biped_index, short *local_out)
{
	short local = local_player_get_next(NONE);
	long player = local != NONE ? local_player_get_player_index(local) : NONE;

	if (local_out) *local_out = local;
	return config_boolean("vr.slide") && vr_active() && game_connection() == _game_connection_local &&
		player != NONE && player_get(player)->unit_index == biped_index && !cinematic_in_progress() &&
		!director_inhibited_input(local);
}

static void vr_slide_end(char const *why)
{
	if (slide.active)
		platform_log("VR slide: ended (%s) after %.2f s at %.1f m/s", why, slide.ticks / 30.0,
			sqrt(slide.velocity[0] * slide.velocity[0] + slide.velocity[1] * slide.velocity[1]));
	slide.active = FALSE;
	slide.ticks = slide.airborne_ticks = slide.stall_ticks = 0;
	slide.hit_count = 0;
}

boolean vr_slide_active(void)
{
	return slide.active;
}

/* An NPC in the slide's way: struck once a slide */
static void vr_slide_impacts(long biped_index, struct biped_datum *biped, float units, float speed)
{
	struct object_iterator it;
	struct unit_datum *other;
	real_vector3d direction = { slide.velocity[0], slide.velocity[1], 0.0f };
	float damage = (float)config_real("vr.slide_damage");

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
		if (slide.hit_count < VR_SLIDE_MAXIMUM_HITS)
			slide.hit[slide.hit_count++] = target;
		definition = object_definition_get(other->definition_index);
		{
			real_vector3d push;
			real mobility = definition && isfinite(definition->object.acceleration_scale) ?
				PIN(definition->object.acceleration_scale, 0.0f, 1.0f) : 1.0f;
			boolean knocked = vr_combat_knockable(target) && speed >= 6.0f && facing >= 0.7f;
			/* the push: the slide's speed shared by how freely it moves (a
			Hunter's acceleration scale keeps it nearly still) */
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
			vr_haptic(0, 0.6f, 0.06f);
			vr_haptic(1, 0.6f, 0.06f);
			platform_log("VR slide: struck %08lx at %.1f m/s (%s, damage %.2f)", target, speed,
				knocked ? "knocked down" : mobility < 0.4f ? "barely moved" : "staggered", scale);
			/* a body that does not give stops the slide */
			if (mobility < 0.4f)
				vr_slide_end("a heavy enemy");
		}
		if (!slide.active)
			return;
	}
}

void vr_slide_update(long biped_index, real_vector3d const *forward, real_vector3d const *throttle,
	real run_speed_units, real_vector3d *movement_desired, real *acceleration_maximum)
{
	struct biped_datum *biped;
	float units = vr_units_per_metre(), run, speed, actual;
	boolean crouch, crouch_edge, airborne, physical;
	real_vector3d horizontal;

	if (!vr_slide_eligible(biped_index, NULL) || !(units > 0.0f) || !forward || !movement_desired ||
		!(biped = biped_try_and_get(biped_index)))
	{
		if (slide.active)
			vr_slide_end("unavailable");
		slide.crouch_was = FALSE;
		return;
	}
	if (slide.active && slide.biped != biped_index)
		vr_slide_end("another body");
	run = (float)run_speed_units / units;
	crouch = TEST_FLAG(biped->unit.control_flags, _unit_control_crouch_modifier_bit);
	crouch_edge = crouch && !slide.crouch_was;
	slide.crouch_was = crouch;
	airborne = TEST_FLAG(biped->biped.flags, _biped_airborne_bit);
	physical = vr_physical_crouching();
	horizontal = biped->object.translational_velocity;
	horizontal.k = 0.0f;
	actual = (float)magnitude3d(&horizontal) * 30.0f / units;
	if (vr_sprint_effort() >= 0.5f)
		slide.sprint_recent = 9;
	else if (slide.sprint_recent > 0)
		slide.sprint_recent--;

	if (!slide.active)
	{
		/* a crouch begun while sprinting on the ground, at a run or faster */
		if (!crouch_edge || slide.sprint_recent <= 0 || airborne || !(actual >= 0.85f * run) ||
			(physical && !config_boolean("vr.slide_physical_crouch")))
			return;
		speed = vr_slide_entry_speed(actual, (float)config_real("vr.slide_momentum"));
		normalize3d(&horizontal);
		slide.velocity[0] = (float)horizontal.i * speed;
		slide.velocity[1] = (float)horizontal.j * speed;
		slide.active = TRUE;
		slide.biped = biped_index;
		slide.ticks = slide.airborne_ticks = slide.stall_ticks = 0;
		slide.hit_count = 0;
		vr_haptic(0, 0.35f, 0.08f);
		vr_haptic(1, 0.35f, 0.08f);
		platform_log("VR slide: started at %.1f m/s (run %.1f; %s crouch)", speed, run, physical ? "physical" : "button");
	}

	/* the end of it */
	if (!crouch)
	{
		vr_slide_end("stood");
		return;
	}
	if (TEST_FLAG(biped->unit.control_flags, _unit_control_jump_bit) && config_boolean("vr.slide_jump_cancel"))
	{
		/* (the jump keeps the slide's momentum: the body has it already) */
		vr_slide_end("jump");
		return;
	}
	slide.airborne_ticks = airborne ? slide.airborne_ticks + 1 : 0;
	if (slide.airborne_ticks > 8)
	{
		vr_slide_end("left the ground");
		return;
	}
	if (slide.ticks > (long)(vr_slide_duration((float)config_real("vr.slide_momentum")) * 30.0f))
	{
		vr_slide_end("time");
		return;
	}
	speed = sqrtf(slide.velocity[0] * slide.velocity[0] + slide.velocity[1] * slide.velocity[1]);
	/* a wall: the body barely moving where the slide would take it */
	if (slide.ticks > 3 && actual < 0.35f * speed)
	{
		if (++slide.stall_ticks >= 2)
		{
			vr_slide_end("a wall");
			return;
		}
	}
	else
		slide.stall_ticks = 0;

	/* the step: friction, slope and the stick */
	{
		float ground[3] = { (float)biped->biped.ground_plane.n.i, (float)biped->biped.ground_plane.n.j,
			(float)biped->biped.ground_plane.n.k };
		float steer[2] = { 0.0f, 0.0f }, amount = 0.0f;
		real_vector3d facing = *forward;
		facing.k = 0.0f;
		if (throttle && normalize3d(&facing) > 0.001f)
		{
			/* the stick in the world: forward along the facing, sideways to its left */
			steer[0] = (float)(facing.i * throttle->i - facing.j * throttle->j);
			steer[1] = (float)(facing.j * throttle->i + facing.i * throttle->j);
			amount = (float)sqrt(throttle->i * throttle->i + throttle->j * throttle->j);
		}
		speed = vr_slide_step(slide.velocity, 1.0f / 30.0f, (float)config_real("vr.slide_friction"),
			airborne ? NULL : ground, steer, amount);
		if (speed < 0.5f * run)
		{
			vr_slide_end("slowed");
			return;
		}
		/* the body asked to move so, in its facing's frame (forward, left),
		per tick; reached at once */
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
	if (config_real("vr.slide_damage") > 0.0)
		vr_slide_impacts(biped_index, biped, units, speed);
}

#else

#include "cseries.h"
#include "vr_slide.h"
boolean vr_slide_active(void) { return FALSE; }

#endif
