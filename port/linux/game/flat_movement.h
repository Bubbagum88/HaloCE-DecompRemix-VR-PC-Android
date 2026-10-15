#ifndef HALO_FLAT_MOVEMENT_H
#define HALO_FLAT_MOVEMENT_H
/* Test72: the movement extras of the flat builds (Android, Windows, Linux):
SPRINT (hold, toggle or a full push forward), SLIDE, WALL RUN and WALL JUMP,
each off until the player turns it on (Settings > Player profile > MOVEMENT;
the movement.* settings). The VR build keeps its own (vr_slide.c,
vr_parkour.c, untouched); this module shares their pure kinematics
(vr_slide_math.h, vr_parkour_math.h, vr_sprint_melee_math.h) so the moves
feel the same, with the camera standing for the head and keys or the stick
for the arms. What needs tracked hands (climbing by hand, wall grabs, pulls)
stays VR's. Offline, or a co-op host's own player, as in VR: never a network
change. */
#ifndef HALO_VR
#include "cseries.h"
#include "math/real_math.h"

/* bipeds.c, each tick of the local player's movement: SPRINT's multiplier */
real flat_movement_sprint_scale(long unit_index);
/* bipeds.c: SLIDE (the arguments are vr_slide_update's) */
void flat_movement_slide_update(long biped_index, real_vector3d const *forward, real_vector3d const *throttle,
	real run_speed_units, real_vector3d *movement_desired, real *acceleration_maximum);
/* bipeds.c: WALL RUN and WALL JUMP change the proposed velocity before the
native capsule sweeps (the arguments are vr_parkour_velocity's) */
void flat_movement_parkour_velocity(long unit_index, real_point3d const *position, float height, float radius,
	real_vector3d *velocity);
/* game_state.c: a level or saved game loaded */
void flat_movement_reset(void);
/* whether a slide is going (for the HUD and tests) */
boolean flat_movement_sliding(void);
#endif
#endif
