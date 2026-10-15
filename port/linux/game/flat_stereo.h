#ifndef HALO_FLAT_STEREO_H
#define HALO_FLAT_STEREO_H
/* Test72: stereoscopic 3D for the flat builds (display.stereo): the owner's
SBS (full or half), TAB / over-under (full or half) and anaglyph. Real left
and right viewpoints, not one frame twice: the player's window is drawn once
for each eye (render.c's render_frame), each camera moved half the eye
separation to its side, each frustum shifted to meet the other at the
convergence distance (an off-axis projection), squeezed for the half
formats. Off: the single camera, exactly as before. Not in VR, which has
its own eyes. */
#ifndef HALO_VR
#include "cseries.h"
#include "math/real_math.h"

struct render_window;
struct render_camera;

/* whether this frame's player window is drawn as two eyes */
boolean flat_stereo_active(void);
/* the window as that eye sees it (its cameras and viewport); eye 0 left */
void flat_stereo_begin_eye(struct render_window *window, short eye);
void flat_stereo_end_eye(void);
/* render.c: the eye's frustum, squeezed and shifted (render_player_frame) */
void flat_stereo_frustum_bounds(real_rectangle2d *bounds);
/* render.c: the camera between the eyes (the first-person weapon is posed
once a frame from it, as the VR build's) and whether this is the second eye */
void flat_stereo_center_camera(struct render_camera *camera);
boolean flat_stereo_second_eye(void);
/* whether an eye is being drawn (render.c leaves mirrors out then) */
boolean flat_stereo_drawing_eye(void);
/* render.c: anaglyph's second eye draws over the first (its depth cleared) */
boolean flat_stereo_keep_color(void);
/* d3d8_gl.c: the colour channels this eye writes (anaglyph), else all */
unsigned long flat_stereo_color_write_mask(void);

/* what is being drawn: the HUD and the reticle have depths of their own
(display.stereo_hud_depth, _reticle_depth); render.c and hud_weapon.c set
it around them, and it returns the one before */
enum
{
	_flat_stereo_layer_world,
	_flat_stereo_layer_hud,
	_flat_stereo_layer_reticle,
};
int flat_stereo_layer(int layer);
/* d3d8_gl.c: how far right this eye's screen-space drawing (the HUD's)
moves for its layer's depth, in the screen's units (0 at the screen) */
float flat_stereo_screen_offset(void);
#endif
#endif
