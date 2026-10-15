#ifndef HALO_VR_SLIDE_H
#define HALO_VR_SLIDE_H
/* Test70: SLIDE (vr_slide.c): sprinting, a crouch slides on. Called from the
local player's movement (bipeds.c) each tick: sets the movement it asks for
while a slide lasts. `forward` the body's facing (world), `throttle` the
stick (forward, left), `run_speed_units` its run speed (world units a second) */
#ifdef HALO_VR
void vr_slide_update(long biped_index, real_vector3d const *forward, real_vector3d const *throttle,
	real run_speed_units, real_vector3d *movement_desired, real *acceleration_maximum);
#endif
boolean vr_slide_active(void);
#endif
