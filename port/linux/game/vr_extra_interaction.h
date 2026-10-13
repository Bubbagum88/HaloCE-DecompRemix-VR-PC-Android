#ifndef VR_EXTRA_INTERACTION_H
#define VR_EXTRA_INTERACTION_H
#include "math/real_math.h"
#ifdef HALO_VR
void vr_extra_reset(void);
void vr_extra_tick(long unit);
int vr_extra_render(float const camera[3]);
/* Test63: the grenades' own models, in the world model pass (render_objects.c) */
void vr_extra_models_render(void);
int vr_physical_grenade_busy(void);
int vr_extra_feedback_active(int hand);
real_matrix4x3 *vr_combat_render(long unit,real_matrix4x3 *stock);
int vr_combat_enabled(void);
int vr_combat_stunned(long unit);
void vr_combat_punch(long unit,int hand,real_point3d const *point,real_vector3d const *sweep);
real vr_combat_hit(long unit,long target,real_point3d const *point,real_vector3d const *direction,real scale,boolean armed);
/* Test65: an enemy's swing begun (a counter window); a hit the player took
 * (breaks the combo); units.c: the blow a lunge or counter carries */
void vr_combat_note_melee(long attacker);
void vr_combat_note_damage(long object);
boolean unit_vr_combat_strike(long unit,long target,real_vector3d const *direction,real scale);
void vr_combat_velocity(long unit,real_point3d const *position,real_vector3d *velocity);
void vr_combat_controls(long unit);
boolean unit_vr_throw_grenade(long unit,short type,real_point3d const *point,real_vector3d const *velocity);
#endif
#endif
