/* Test71: a manual reload profile for any first-person weapon model, from
 * its own nodes and its weapon's magazine: the owner's "adapt manual reload
 * to any custom weapons/new weapon meshes given by the mods". The stock
 * table (vr_manual_reload.c) knew six models by their tag names; a mod's
 * weapon has a name of its own, and a protected map (SPV1) hides every
 * name ("<protected>"), its stock rifles' included. Each kind's nodes are
 * the stock models' own names, which mods keep (SPV1's eleven rigs, Project
 * Lumoria's), and on the stock rigs these rules give exactly the stock table
 * (tools/test_test71_reload.py). Pure: tested on the host. */
#ifndef VR_RELOAD_GENERIC_PROFILE_H
#define VR_RELOAD_GENERIC_PROFILE_H

#include <string.h>

/* the order of vr_manual_reload.c's RELOAD_ kinds */
enum
{
	VR_RELOAD_GENERIC_MAGAZINE,
	VR_RELOAD_GENERIC_SHELL,
	VR_RELOAD_GENERIC_TUBES,
	VR_RELOAD_GENERIC_CANISTER
};

struct vr_reload_generic
{
	char const *ammo, *chamber;
	int kind;
};

static char const *vr_reload_generic_find(char const *const *names, int count, char const *const *wanted)
{
	for (int want = 0; wanted[want]; want++)
		for (int index = 0; index < count; index++)
			if (names[index] && !strcmp(names[index], wanted[want]))
				return wanted[want];
	return NULL;
}

/* 1 and the profile when the model can be reloaded by hand: `names` its
 * nodes; `magazines` its weapon's magazine count, the first's rounds loaded
 * at most and rounds a reload puts in (1: shell by shell). An energy weapon
 * (no magazine, or none to load) and a rig with no part to take are left
 * to the game's own reload. */
static int vr_reload_generic_profile(char const *const *names, int count, int magazines,
	int loaded_maximum, int rounds_reloaded, struct vr_reload_generic *out)
{
	static char const *const tubes[] = { "frame tubes", NULL };
	static char const *const push_bar[] = { "frame push_bar", NULL };
	static char const *const canister[] = { "frame ammo", NULL };
	static char const *const cover[] = { "frame cover", NULL };
	static char const *const magazine[] = { "frame magazine", NULL };
	static char const *const loose[] = { "frame bullet", "frame shell", NULL };
	/* a magazine's gun charged by its handle (rifles), slide (pistols, SMGs) or bolt */
	static char const *const magazine_chamber[] = { "frame ophandle", "frame slide", "frame bolt",
		"frame charging handle", "frame charging_handle", "frame cock", "frame pump", NULL };
	/* a gun loaded shell by shell, pumped (shotguns) or cocked */
	static char const *const shell_chamber[] = { "frame pump", "frame cock", "frame ophandle", "frame slide",
		"frame bolt", NULL };
	char const *ammo, *chamber;

	if (!names || count <= 0 || !out || magazines < 1 || loaded_maximum <= 0 || rounds_reloaded <= 0)
		return 0;
	if ((ammo = vr_reload_generic_find(names, count, tubes)) &&
		(chamber = vr_reload_generic_find(names, count, push_bar)))
	{
		out->ammo = ammo; out->chamber = chamber; out->kind = VR_RELOAD_GENERIC_TUBES;
		return 1;
	}
	if ((ammo = vr_reload_generic_find(names, count, canister)) &&
		(chamber = vr_reload_generic_find(names, count, cover)))
	{
		out->ammo = ammo; out->chamber = chamber; out->kind = VR_RELOAD_GENERIC_CANISTER;
		return 1;
	}
	if (rounds_reloaded == 1 && loaded_maximum > 1 &&
		(ammo = vr_reload_generic_find(names, count, loose)) &&
		(chamber = vr_reload_generic_find(names, count, shell_chamber)))
	{
		out->ammo = ammo; out->chamber = chamber; out->kind = VR_RELOAD_GENERIC_SHELL;
		return 1;
	}
	if ((ammo = vr_reload_generic_find(names, count, magazine)) &&
		(chamber = vr_reload_generic_find(names, count, magazine_chamber)))
	{
		out->ammo = ammo; out->chamber = chamber; out->kind = VR_RELOAD_GENERIC_MAGAZINE;
		return 1;
	}
	return 0;
}

/* the needler's rig (its needles), whatever its name: shaken to reload */
static int vr_reload_generic_needle_rig(char const *const *names, int count)
{
	static char const *const needles[] = { "frame needle01", NULL };
	static char const *const body[] = { "frame body", NULL };
	return vr_reload_generic_find(names, count, needles) && vr_reload_generic_find(names, count, body);
}

#endif
