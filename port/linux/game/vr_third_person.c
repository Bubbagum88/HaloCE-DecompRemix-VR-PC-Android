/*
VR_THIRD_PERSON.C

Test72 (the owner: "make it so third person works in vr. of course, when
enabled, all inputs get auto converted to work for third person, then
reverted back to their previous/initial state after third person is turned
off"): VR THIRD PERSON (vr.third_person, GAMEPLAY), on foot in a campaign or
co-op, as the flat game's third person is (never in multiplayer).

The camera is the flat game's over-the-shoulder one (third_person.c), set
behind the player along the headset's heading - the way the stick turns -
not along the aim, so looking about does not swing it; the head looks about
from it. The body is drawn as the game animates it, its carried weapons with
it; the first-person gun and arms are not drawn.

The controls are made third person's while it is engaged: the head aims (at
what it looks at: the aim goes from the player's eyes to where the head's
gaze meets the world, so the crosshair's mark is hit), the hands' physical
features - holding and holstering guns, manual reload, grenades from the
chest, physical melee, FIST COMBAT, deflection, grabbing the world and
NPCs, weapon pull, climbing, arm-run, room-scale walking, crouching and
sliding by the head, the wrist HUD and the hand-held scope - are off, the
buttons doing their work. These are values held over the settings'
(config_override: never written to the file), given up all at once when
third person ends - turned off, a vehicle entered, a multiplayer game - so
every setting is as it was. A setting changed in the menu meanwhile keeps
the player's choice.
*/

#ifdef HALO_VR

#include "cseries.h"
#include "game/game_engine.h"
#include "game/players.h"
#include "units/units.h"
#include "objects/objects.h"
#include "../src/vr.h"
#include "../src/port_config.h"

/* port/linux/src (platform.h: not for the game's own sources) */
void platform_log(const char *format, ...);

/* the settings third person holds, and their value meanwhile */
static struct
{
	char const *name;
	char const *value;
} const vr_third_person_settings[] =
{
	{ "vr.aim", "head" },
	{ "vr.weapons", "locked" },
	{ "vr.holsters", "false" },
	{ "vr.manual_reload", "false" },
	{ "vr.physical_grenades", "false" },
	{ "vr.melee_speed", "0" },
	{ "vr.assisted_combat", "false" },
	{ "vr.projectile_parry", "false" },
	{ "vr.world_interaction", "false" },
	{ "vr.npc_interaction", "false" },
	{ "vr.weapon_pull", "false" },
	{ "vr.parkour_climb", "false" },
	{ "vr.arm_run", "false" },
	{ "vr.roomscale", "false" },
	{ "vr.crouch_height", "0" },
	{ "vr.slide_physical_crouch", "false" },
	{ "vr.wrist_hud", "false" },
	{ "vr.scope", "false" },
};

static boolean vr_third_person_held = FALSE;

static boolean vr_third_person_setting(void)
{
	static unsigned long changes = (unsigned long)-1;
	static boolean on = FALSE;

	if (changes != config_changes())
	{
		changes = config_changes();
		on = config_boolean("vr.third_person") != 0;
	}
	return on;
}

/* whether third person is engaged: set, a campaign's or co-op's, the local
player on foot (alive or dead: its controls stay third person's until it is
back) */
static boolean vr_third_person_wanted(long unit_index)
{
	struct object_datum *object = unit_index != NONE ? object_try_and_get(unit_index) : NULL;

	if (!vr_active() || !vr_third_person_setting() || game_engine_running() || !object)
		return FALSE;
	return object->object.parent_object_index == NONE;
}

static void vr_third_person_hold(boolean hold)
{
	int index, held = 0;

	if (hold == vr_third_person_held)
		return;
	vr_third_person_held = hold;
	if (hold)
	{
		for (index = 0; index < (int)NUMBEROF(vr_third_person_settings); index++)
			held += config_override(vr_third_person_settings[index].name, vr_third_person_settings[index].value);
		platform_log("vr: third person on: the head aims, the hands' physical features off for it (%d settings held, "
			"restored when it ends)", held);
	}
	else
	{
		config_override_clear();
		platform_log("vr: third person off: every setting as it was");
	}
	vr_reload_settings();
}

/* (vr_render.c, the local player's control each tick) */
void vr_third_person_update(long unit_index)
{
	/* (between a death and the next body, as it was) */
	if (unit_index == NONE && vr_active() && vr_third_person_setting() && !game_engine_running())
		return;
	vr_third_person_hold(vr_third_person_wanted(unit_index));
}

/* whether third person is engaged (its controls in force) */
boolean vr_third_person_engaged(void)
{
	return vr_third_person_held;
}

/* (third_person.c) the way the camera faces: the headset's heading, level */
boolean vr_third_person_forward(real_vector3d *forward)
{
	float heading[3];

	if (!vr_heading_forward(heading))
		return FALSE;
	forward->i = heading[0];
	forward->j = heading[1];
	forward->k = 0.0f;
	return TRUE;
}

#endif
