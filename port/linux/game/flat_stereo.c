/* Test72: stereoscopic 3D for the flat builds (flat_stereo.h). The owner:
"Do not simply duplicate the same camera frame twice. Render actual left/right
viewpoints with proper eye/camera offset, projection, convergence and aspect
handling. Turning stereo off must return to the normal single-camera flat
rendering path."

display.stereo: "off", "sbs_half" (each eye squeezed into half the width:
3D televisions), "sbs_full" (each eye at its own shape, side by side: cross-
or parallel-eyed viewing, video players), "tab_half", "tab_full" (over and
under, left eye on top) and "anaglyph" (red for the left eye, cyan for the
right: either through colour write masks on the whole screen). Eye
separation (mm) and convergence (m) as set; display.stereo_swap exchanges the
eyes. The HUD is drawn in each eye's view, at the screen unless
display.stereo_hud_depth puts it further or nearer (each eye's HUD moved
sideways by the disparity a point at that distance has); the reticle the
same with display.stereo_reticle_depth. Mirrors (they assume the whole
screen) are left out while stereo is on. */
#ifndef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "render/render.h"
#include "render/render_cameras.h"
#include "../src/port_config.h"
#include "flat_stereo.h"

void platform_log(char const *format, ...);

/* Halo's world unit is ten feet */
#define FLAT_STEREO_UNITS_PER_METRE (1.0f / 3.048f)
/* D3DCOLORWRITEENABLE_RED / _GREEN / _BLUE / _ALPHA (the Xbox's d3d8 values) */
#define STEREO_WRITE_RED 0x00010000UL
#define STEREO_WRITE_GREEN 0x00000100UL
#define STEREO_WRITE_BLUE 0x00000001UL
#define STEREO_WRITE_ALPHA 0x01000000UL

enum
{
	_stereo_off,
	_stereo_sbs_half,
	_stereo_sbs_full,
	_stereo_tab_half,
	_stereo_tab_full,
	_stereo_anaglyph,
};

static struct
{
	int mode;           /* this frame's */
	short eye;          /* the eye being drawn, NONE between */
	real offset;        /* world units the camera moved for it (signed, along its right) */
	real_vector3d right;
	real shift;         /* the frustum's sideways shift for convergence, in its bounds' units */
	real squeeze_x;     /* the frustum's widening for the half formats */
	int logged_mode;
	real pixels_per_tangent; /* the eye's screen units for a tangent's width */
	real side;          /* -0.5 the eye seeing from the left, 0.5 the right */
	real separation;    /* metres */
	real convergence;   /* metres */
	int layer;          /* _flat_stereo_layer_* */
} stereo = { _stereo_off, NONE, 0.0f, { 0 }, 0.0f, 1.0f, -1, 0.0f, 0.0f, 0.0f, 0.0f, _flat_stereo_layer_world };

static int flat_stereo_mode(void)
{
	char const *mode = config_string("display.stereo");

	if (!mode || !*mode || !strcmp(mode, "off"))
		return _stereo_off;
	if (!strcmp(mode, "sbs_half"))
		return _stereo_sbs_half;
	if (!strcmp(mode, "sbs_full"))
		return _stereo_sbs_full;
	if (!strcmp(mode, "tab_half"))
		return _stereo_tab_half;
	if (!strcmp(mode, "tab_full"))
		return _stereo_tab_full;
	if (!strcmp(mode, "anaglyph"))
		return _stereo_anaglyph;
	return _stereo_off;
}

boolean flat_stereo_active(void)
{
	stereo.mode = flat_stereo_mode();
	if (stereo.mode != stereo.logged_mode)
	{
		platform_log("stereo: %s", config_string("display.stereo"));
		stereo.logged_mode = stereo.mode;
	}
	return stereo.mode != _stereo_off;
}

/* the half of a rectangle an eye is drawn in: 0 the first (left, top) */
static void stereo_half(rectangle2d *bounds, int horizontal, short half)
{
	if (horizontal)
	{
		short middle = (short)((bounds->x0 + bounds->x1) / 2);
		if (half == 0)
			bounds->x1 = middle;
		else
			bounds->x0 = middle;
	}
	else
	{
		short middle = (short)((bounds->y0 + bounds->y1) / 2);
		if (half == 0)
			bounds->y1 = middle;
		else
			bounds->y0 = middle;
	}
}

void flat_stereo_begin_eye(struct render_window *window, short eye)
{
	real separation = (real)config_real("display.stereo_separation");
	real convergence = (real)config_real("display.stereo_convergence");
	boolean swap = config_boolean("display.stereo_swap");
	short seen = swap ? (short)(1 - eye) : eye; /* which eye this view is for */
	real side = seen == 0 ? -0.5f : 0.5f;
	real tangent;
	int axis;
	struct render_camera *cameras[2] = { &window->render_camera, &window->rasterizer_camera };
	int index;

	if (!(separation >= 0.0f && separation <= 200.0f))
		separation = 64.0f;
	if (!(convergence >= 0.25f && convergence <= 100.0f))
		convergence = 2.5f;
	stereo.eye = eye;
	cross_product3d(&window->render_camera.forward, &window->render_camera.up, &stereo.right);
	if (normalize3d(&stereo.right) < 0.0001f)
	{
		stereo.right = *global_zero_vector3d;
	}
	stereo.offset = side * separation * 0.001f * FLAT_STEREO_UNITS_PER_METRE;
	tangent = (real)tan(window->render_camera.vertical_field_of_view * 0.5f);
	stereo.squeeze_x = stereo.mode == _stereo_sbs_half ? 2.0f : stereo.mode == _stereo_tab_half ? 0.5f : 1.0f;
	if (eye == 0)
	{
		static int logged = -1;
		if (logged != stereo.mode)
		{
			platform_log("stereo: vertical field %.4f rad, viewport %dx%d, separation %.1f mm, convergence %.2f m",
				window->render_camera.vertical_field_of_view,
				window->render_camera.viewport_bounds.x1 - window->render_camera.viewport_bounds.x0,
				window->render_camera.viewport_bounds.y1 - window->render_camera.viewport_bounds.y0,
				separation, convergence);
			logged = stereo.mode;
		}
	}
	for (index = 0; index < 2; index++)
	{
		struct render_camera *camera = cameras[index];
		for (axis = 0; axis < 3; axis++)
			camera->position.n[axis] += stereo.right.n[axis] * stereo.offset;
		if (stereo.mode == _stereo_sbs_half || stereo.mode == _stereo_sbs_full)
		{
			stereo_half(&camera->viewport_bounds, TRUE, eye);
			camera->window_bounds = camera->viewport_bounds;
		}
		else if (stereo.mode == _stereo_tab_half || stereo.mode == _stereo_tab_full)
		{
			stereo_half(&camera->viewport_bounds, FALSE, eye);
			camera->window_bounds = camera->viewport_bounds;
		}
	}
	/* the frustum shifted toward the other eye by half the separation at the
	convergence distance, so that a point there is in the same place in both.
	Its x bounds run -1..1 over the viewport and 1 is the viewport's aspect
	times the vertical half-field's tangent (render_cameras.c's projection:
	measured on frames, the disparity at infinity is the separation over the
	convergence times the pixels a tangent spans) */
	{
		rectangle2d const *viewport = &window->render_camera.viewport_bounds;
		real aspect = (viewport->y1 > viewport->y0) ?
			(real)(viewport->x1 - viewport->x0) / (real)(viewport->y1 - viewport->y0) : 1.0f;

		stereo.shift = tangent > 0.0001f && aspect > 0.0001f ?
			-side * (separation * 0.001f / convergence) / (tangent * aspect) : 0.0f;
		/* half the viewport's width spans the frustum's half-width, which is
		the squeeze times the aspect in tangents */
		stereo.pixels_per_tangent = tangent > 0.0001f && aspect > 0.0001f ?
			(real)(viewport->x1 - viewport->x0) * 0.5f / (stereo.squeeze_x * aspect * tangent) : 0.0f;
	}
	stereo.side = side;
	stereo.separation = separation * 0.001f;
	stereo.convergence = convergence;
}

void flat_stereo_end_eye(void)
{
	stereo.eye = NONE;
}

void flat_stereo_frustum_bounds(real_rectangle2d *bounds)
{
	real center, half;
	static int logged = -1;

	if (stereo.eye == NONE || !bounds)
		return;
	center = (bounds->x0 + bounds->x1) * 0.5f;
	half = (bounds->x1 - bounds->x0) * 0.5f * stereo.squeeze_x;
	if (stereo.eye == 0 && logged != stereo.mode)
	{
		platform_log("stereo: eye bounds x %.4f..%.4f y %.4f..%.4f, shift %.4f, squeeze %.2f",
			bounds->x0, bounds->x1, bounds->y0, bounds->y1, stereo.shift, stereo.squeeze_x);
		logged = stereo.mode;
	}
	bounds->x0 = center - half + stereo.shift;
	bounds->x1 = center + half + stereo.shift;
}

void flat_stereo_center_camera(struct render_camera *camera)
{
	int axis;

	if (stereo.eye == NONE || !camera)
		return;
	for (axis = 0; axis < 3; axis++)
		camera->position.n[axis] -= stereo.right.n[axis] * stereo.offset;
}

boolean flat_stereo_second_eye(void)
{
	return stereo.eye == 1;
}

boolean flat_stereo_drawing_eye(void)
{
	return stereo.eye != NONE;
}

boolean flat_stereo_keep_color(void)
{
	return stereo.eye == 1 && stereo.mode == _stereo_anaglyph;
}

int flat_stereo_layer(int layer)
{
	int previous = stereo.layer;

	stereo.layer = layer;
	return previous;
}

float flat_stereo_screen_offset(void)
{
	real depth;

	if (stereo.eye == NONE || stereo.layer == _flat_stereo_layer_world)
		return 0.0f;
	depth = (real)config_real(stereo.layer == _flat_stereo_layer_reticle ?
		"display.stereo_reticle_depth" : "display.stereo_hud_depth");
	if (!(depth > 0.0f && depth <= 100.0f))
		return 0.0f;
	/* a point at that distance: the disparity a frustum converging at
	stereo.convergence gives it, half for each eye (positive is further) */
	return (float)(stereo.side * stereo.pixels_per_tangent * stereo.separation *
		(1.0f / stereo.convergence - 1.0f / depth));
}

unsigned long flat_stereo_color_write_mask(void)
{
	boolean swap;
	short seen;

	if (stereo.eye == NONE || stereo.mode != _stereo_anaglyph)
		return 0xFFFFFFFFUL;
	swap = config_boolean("display.stereo_swap");
	seen = swap ? (short)(1 - stereo.eye) : stereo.eye;
	/* red-cyan: the left eye's red, the right eye's green and blue */
	return seen == 0 ? (STEREO_WRITE_RED | STEREO_WRITE_ALPHA) : (STEREO_WRITE_GREEN | STEREO_WRITE_BLUE | STEREO_WRITE_ALPHA);
}
#endif
