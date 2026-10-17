/*
HOLSTERED_WEAPONS.C

Test72 (HaloFreak95's display.holstered_weapons, off by default): every biped
wears the weapons it carries but does not hold - a long gun slung across its
back, a pistol or needler on its right thigh - instead of their vanishing as
the stock game has them.

A weapon carried but not held is detached from its unit and taken off the map
(units.c): nothing of the game's is changed here. As a biped is drawn
(render_objects.c), each such weapon's model is drawn again in its default
pose (model_get_node_matrices), placed by the biped's drawn nodes ("bip01
spine1" for the back, "bip01 r thigh" for the leg, as the maps' bipeds name
them: one without them wears nothing), lit as the biped is and taking its
camouflage. Not while seated, not for a biped drawn in part (the first-person
legs, the headset's own body), not in shadows; the flag and the ball are
never worn. Only the drawing: nothing simulated, nothing sent between
machines, the same on every build.
*/

#include "cseries.h"
#include "math/real_math.h"
#include "objects/object_definitions.h"
#include "objects/objects.h"
#include "units/units.h"
#include "items/weapons.h"
#include "models/model_definitions.h"
#include "models/models.h"
#include "render/render.h"
#include "render/render_cameras_internal.h"
#include "tag_files/tag_groups.h"

#include <math.h>
#include <string.h>

/* port/linux/src/port_config.c */
int config_boolean(const char *name);
unsigned long config_changes(void);

/* how far the slung gun's middle lies behind the spine node and beside the
thigh node, and down the thigh, in world units (1 = 3.048 m) */
#define HOLSTERED_BACK_OUT (0.075f)
#define HOLSTERED_THIGH_OUT (0.045f)
#define HOLSTERED_THIGH_DOWN (0.075f)

static boolean holstered_weapons_on(void)
{
	static unsigned long changes = (unsigned long)-1;
	static boolean on = FALSE;

	if (changes != config_changes())
	{
		changes = config_changes();
		on = config_boolean("display.holstered_weapons") != 0;
	}
	return on;
}

/* a weapon's kind as worn: 0 not worn, 1 on the back, 2 on the thigh */
static short holstered_weapon_kind(long weapon_index)
{
	char const *name = tag_get_name(object_get(weapon_index)->definition_index);

	if (!name || strstr(name, "flag") || strstr(name, "ball"))
		return 0;
	return strstr(name, "pistol") || strstr(name, "needler") ? 2 : 1;
}

static boolean holstered_normalize(real_vector3d *v)
{
	real length = (real)sqrt(v->i * v->i + v->j * v->j + v->k * v->k);

	if (!(length > 1e-4f))
		return FALSE;
	v->i /= length;
	v->j /= length;
	v->k /= length;
	return TRUE;
}

static void holstered_cross(real_vector3d const *a, real_vector3d const *b, real_vector3d *out)
{
	out->i = a->j * b->k - a->k * b->j;
	out->j = a->k * b->i - a->i * b->k;
	out->k = a->i * b->j - a->j * b->i;
}

/* the gun's frame for a place on the body: its barrel (forward) and its top
(up), its middle at `middle` */
static void holstered_draw(long unit_index, long weapon_index, real_point3d const *middle,
	real_vector3d const *forward, real_vector3d const *up, struct render_lighting const *lighting,
	struct render_model_effect const *effect)
{
	struct object_datum *weapon = object_get(weapon_index);
	struct object_definition *definition = object_definition_get(weapon->definition_index);
	long model_index = definition->object.model.index;
	real_matrix4x3 matrices[MAXIMUM_NODES_PER_MODEL];
	real_vector3d left;
	real_point3d origin;
	real_point3d const *offset = &definition->object.bounding_offset;
	real radius = definition->object.bounding_radius > 0.0f ? definition->object.bounding_radius : 0.1f;
	struct model *model;

	(void)unit_index;
	if (model_index == NONE)
		return;
	model = model_definition_get(model_index);
	if (!model || model->nodes.count <= 0 || model->nodes.count > MAXIMUM_NODES_PER_MODEL)
		return;
	/* (the model's origin placed so its bounding middle is at `middle`) */
	holstered_cross(up, forward, &left);
	origin.x = middle->x - (forward->i * offset->x + left.i * offset->y + up->i * offset->z);
	origin.y = middle->y - (forward->j * offset->x + left.j * offset->y + up->j * offset->z);
	origin.z = middle->z - (forward->k * offset->x + left.k * offset->y + up->k * offset->z);
	model_get_node_matrices(model, matrices, &origin, forward, up);
	render_model(model_index,
		render_frustum_sphere_diameter_in_pixels(&render.frustum, middle, radius),
		matrices,
		(char const *)weapon->object.region_permutations,
		weapon->object.outgoing_change_colors,
		weapon->object.outgoing_function_values,
		lighting,
		middle,
		radius,
		effect,
		weapon_index,
		weapon->object.forced_shader_permutation_index,
		0);
}

/* from render_object_list (render_objects.c), as a biped has been drawn with
`lighting` and its model effect (what its children take) */
void holstered_weapons_render(
	long unit_index,
	real_matrix4x3 const *nodes,
	struct render_lighting const *lighting,
	struct render_model_effect const *effect)
{
	struct object_datum *object;
	struct unit_datum *unit;
	long model_index;
	short spine;
	short thigh;
	short slot;
	short backs = 0;

	if (!holstered_weapons_on() || !nodes || !lighting)
		return;
	object = object_get(unit_index);
	if (!TEST_FLAG(_object_mask_biped, object->object.type) || object->object.parent_object_index != NONE)
		return;
	/* (a seated biped is attached to its seat: its parent, above) */
	unit = unit_get(unit_index);
	model_index = object_definition_get(object->definition_index)->object.model.index;
	if (model_index == NONE)
		return;
	spine = model_find_node(model_index, "bip01 spine1");
	thigh = model_find_node(model_index, "bip01 r thigh");
	for (slot = 0; slot < MAXIMUM_WEAPONS_PER_UNIT; slot++)
	{
		long weapon_index = unit->unit.weapon_object_indices[slot];
		struct object_datum *weapon;
		short kind;
		real_vector3d body_forward = object->object.forward;
		real_vector3d body_up = object->object.up;
		real_vector3d body_right;
		real_vector3d forward;
		real_vector3d up;
		real_point3d middle;

		if (weapon_index == NONE || slot == unit->unit.current_weapon_index)
			continue;
		weapon = object_try_and_get(weapon_index);
		/* (one attached is drawn as the biped's child: being drawn or put away) */
		if (!weapon || weapon->object.parent_object_index != NONE)
			continue;
		kind = holstered_weapon_kind(weapon_index);
		if (kind == 0)
			continue;
		if (!holstered_normalize(&body_forward) || !holstered_normalize(&body_up))
			continue;
		holstered_cross(&body_forward, &body_up, &body_right);
		if (kind == 2 && thigh != NONE)
		{
			/* the thigh: the barrel down the thigh's bone (its x), the gun's
			top facing forward, beside the leg, outward */
			real_matrix4x3 const *leg = &nodes[thigh];
			real along;

			forward = leg->forward;
			if (!holstered_normalize(&forward))
				continue;
			if (forward.i * body_up.i + forward.j * body_up.j + forward.k * body_up.k > 0.0f)
			{
				forward.i = -forward.i;
				forward.j = -forward.j;
				forward.k = -forward.k;
			}
			along = body_forward.i * forward.i + body_forward.j * forward.j + body_forward.k * forward.k;
			up.i = body_forward.i - forward.i * along;
			up.j = body_forward.j - forward.j * along;
			up.k = body_forward.k - forward.k * along;
			if (!holstered_normalize(&up))
				continue;
			middle.x = leg->position.x + forward.i * HOLSTERED_THIGH_DOWN + body_right.i * HOLSTERED_THIGH_OUT;
			middle.y = leg->position.y + forward.j * HOLSTERED_THIGH_DOWN + body_right.j * HOLSTERED_THIGH_OUT;
			middle.z = leg->position.z + forward.k * HOLSTERED_THIGH_DOWN + body_right.k * HOLSTERED_THIGH_OUT;
		}
		else if (spine != NONE)
		{
			/* the back: across it, the barrel up over the left shoulder (a
			second long gun over the right), lying flat against it */
			real side = backs++ == 0 ? -1.0f : 1.0f;
			real_matrix4x3 const *back = &nodes[spine];

			forward.i = body_up.i * 0.8f + body_right.i * side * 0.6f;
			forward.j = body_up.j * 0.8f + body_right.j * side * 0.6f;
			forward.k = body_up.k * 0.8f + body_right.k * side * 0.6f;
			holstered_cross(&body_forward, &forward, &up);
			if (!holstered_normalize(&forward) || !holstered_normalize(&up))
				continue;
			middle.x = back->position.x - body_forward.i * HOLSTERED_BACK_OUT;
			middle.y = back->position.y - body_forward.j * HOLSTERED_BACK_OUT;
			middle.z = back->position.z - body_forward.k * HOLSTERED_BACK_OUT;
		}
		else
		{
			continue;
		}
		holstered_draw(unit_index, weapon_index, &middle, &forward, &up, lighting, effect);
	}
}
