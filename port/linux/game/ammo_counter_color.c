/*
AMMO_COUNTER_COLOR.C

Test72 (HaloFreak95's display.ammo_counter_color): the assault rifle's
display in your hands - its ammo counter's digits, its compass, its icons and
readout - in a multiplayer armor color instead of its own blue
(display.ammo_counter_color: "default", or "white", "black", "red"...).

The display is the first-person rifle's transparent (chicago) shaders,
"weapons\assault rifle\fp\shaders\numbers", "...\compass", "...\icons" and
"...\ar data"; only the first-person model has them (the rifle seen in others'
hands is "weapons\assault rifle\shaders\ar lod"). Each of their transparent
groups is drawn recolored (d3d8_gl_set_recolor, as the visor is: the chosen
color at each pixel's brightness, brightened, the digits' glow being additive
light over the rifle). The groups drawn before one (its presorted chain) are
drawn as they were: the recolor is the group's own. Only the drawing changes:
nothing goes over the network.
*/

#include "cseries.h"
#include "real_math.h"
#include "saved games/player_profile.h"
#include "tag_files/tag_groups.h"

#include <string.h>

/* port/linux/src/port_config.c */
const char *config_string(const char *name);
unsigned long config_changes(void);
/* cache_files.c */
long tag_loaded(long group_tag, char const *name);
/* port/linux/src/d3d8_gl.c: the draws that follow recolored (curve 0: not) */
void d3d8_gl_set_recolor(float red, float green, float blue, float curve);

/* shader_transparent_chicago's group tag */
#define AMMO_COUNTER_SHADER_CHICAGO_TAG 0x73636869 /* 'schi' */

/* the armor colors, in the profile's order (player_profile.c) */
static char const *const ammo_counter_color_names[] =
{
	"white", "black", "red", "blue", "gray", "yellow", "green", "pink", "purple",
	"cyan", "cobalt", "orange", "teal", "sage", "brown", "tan", "maroon", "salmon",
};
enum { AMMO_COUNTER_COLOR_BLACK = 1 };

/* the first-person assault rifle's display, as the maps name its shaders */
static char const *const ammo_counter_shader_names[] =
{
	"weapons\\assault rifle\\fp\\shaders\\numbers",
	"weapons\\assault rifle\\fp\\shaders\\compass",
	"weapons\\assault rifle\\fp\\shaders\\icons",
	"weapons\\assault rifle\\fp\\shaders\\ar data",
};

static unsigned long ammo_counter_color_changes = (unsigned long)-1;
static short ammo_counter_color_index = NONE;
static boolean ammo_counter_color_looked = FALSE;
static void const *ammo_counter_color_shaders[NUMBEROF(ammo_counter_shader_names)];
/* the group being drawn is recolored */
static boolean ammo_counter_color_on = FALSE;

static void ammo_counter_color_update(
	void)
{
	char const *value;
	short index;

	if (ammo_counter_color_changes == config_changes())
		return;
	ammo_counter_color_changes = config_changes();
	ammo_counter_color_index = NONE;
	value = config_string("display.ammo_counter_color");
	for (index = 0; value && index < (short)NUMBEROF(ammo_counter_color_names); index++)
	{
		if (!strcmp(value, ammo_counter_color_names[index]))
			ammo_counter_color_index = index;
	}
}

static boolean ammo_counter_color_is_display(
	void const *shader)
{
	short index;

	if (!shader)
		return FALSE;
	if (!ammo_counter_color_looked)
	{
		ammo_counter_color_looked = TRUE;
		for (index = 0; index < (short)NUMBEROF(ammo_counter_shader_names); index++)
		{
			long tag_index = tag_loaded(AMMO_COUNTER_SHADER_CHICAGO_TAG, ammo_counter_shader_names[index]);

			ammo_counter_color_shaders[index] =
				tag_index != NONE ? tag_get(AMMO_COUNTER_SHADER_CHICAGO_TAG, tag_index) : NULL;
		}
	}
	for (index = 0; index < (short)NUMBEROF(ammo_counter_shader_names); index++)
	{
		if (shader == ammo_counter_color_shaders[index])
			return TRUE;
	}
	return FALSE;
}

static void ammo_counter_color_set(
	boolean on)
{
	if (on)
	{
		if (ammo_counter_color_index == AMMO_COUNTER_COLOR_BLACK)
		{
			/* (black light cannot be added: a dim smoke grey, the digits still read) */
			d3d8_gl_set_recolor(0.30f, 0.30f, 0.32f, 0.8f);
		}
		else
		{
			/* (the color at the pixel's brightness, curved up and doubled: the
			blue's own brightness is low, its glow mostly the blue channel) */
			real_rgb_color color = player_profile_get_rgb_color(ammo_counter_color_index);

			d3d8_gl_set_recolor(color.red * 2.0f, color.green * 2.0f, color.blue * 2.0f, 0.6f);
		}
	}
	else
	{
		d3d8_gl_set_recolor(0.0f, 0.0f, 0.0f, 0.0f);
	}
	ammo_counter_color_on = on;
}

/* from rasterizer_transparent_geometry_group_draw: a group about to be drawn
(its shader); returns what to give ammo_counter_color_group_end after */
boolean ammo_counter_color_group_begin(
	void const *shader)
{
	boolean previous = ammo_counter_color_on;
	boolean on;

	ammo_counter_color_update();
	on = ammo_counter_color_index != NONE && ammo_counter_color_is_display(shader);
	/* (a group drawn while a display group is (its chain) is drawn as it was) */
	if (on || previous)
		ammo_counter_color_set(on);
	return previous;
}

void ammo_counter_color_group_end(
	boolean previous)
{
	if (ammo_counter_color_on != previous)
		ammo_counter_color_set(previous);
}

/* a new map: its shaders looked up again (objects.c, with visor_color_reset) */
void ammo_counter_color_reset(
	void)
{
	short index;

	ammo_counter_color_looked = FALSE;
	for (index = 0; index < (short)NUMBEROF(ammo_counter_shader_names); index++)
		ammo_counter_color_shaders[index] = NULL;
	if (ammo_counter_color_on)
		ammo_counter_color_set(FALSE);
}
