#ifndef VR_EXTRA_INTERACTION_H
#define VR_EXTRA_INTERACTION_H
#include "math/real_math.h"
#ifdef HALO_VR
void vr_extra_reset(void);
long vr_extra_action_owner(void);
/* Test72: a deflection's feedback: by a held gun (block) or a stroke; a
 * bullet's lighter (a rifle's stream of them) */
void vr_extra_projectile_feedback(int hand,real_point3d const *point,int block,int light);
void vr_extra_tick(long unit);
/* Test70: whether fist combat knocks this kind down (a slide into it too) */
boolean vr_combat_knockable(long target);
int vr_extra_render(float const camera[3]);
/* Test63: the grenades' own models, in the world model pass (render_objects.c) */
void vr_extra_models_render(void);
int vr_physical_grenade_busy(void);
int vr_extra_feedback_active(int hand);
real_matrix4x3 *vr_combat_render(long unit,real_matrix4x3 *stock);
/* Test67: a point on an enemy as drawn mapped onto Halo's own pose (combat
 * poses are render-only); FALSE and unchanged when nothing is drawn differently */
int vr_combat_drawn_to_native(long unit,real_point3d const *point,real_point3d *native_point);
int vr_combat_enabled(void);
int vr_combat_stunned(long unit);
int vr_combat_control_opening(long unit);
int vr_combat_punch(long unit,int hand,real_point3d const *point,real_vector3d const *sweep);
real vr_combat_hit(long unit,long target,real_point3d const *point,real_vector3d const *direction,real scale,boolean armed);
real vr_combat_damage_share(void);
/* Test73 (10d): on a co-op client, the shove vr_combat_hit gave this tick's
blow (its host gives it: unit_vr_remote_strike), once; FALSE: none */
boolean vr_combat_take_remote_shove(real_vector3d *shove);
int vr_combat_regular_blow(long owner,long target);
void vr_combat_damage_end(void);
void vr_combat_swing_hit(int hand);
void unit_vr_guard_feedback(long unit,boolean parry);
real vr_combat_defend(long victim,long attacker);
/* Test65: an enemy's swing begun (a counter window); a hit the player took
 * (breaks the combo); units.c: the blow a lunge or counter carries */
void vr_combat_note_melee(long attacker);
void vr_combat_note_damage(long object);
boolean unit_vr_combat_strike(long unit,long target,real_vector3d const *direction,real scale);
/* Test72: the blow on a body a hand holds, where the fist meets it */
boolean unit_vr_combat_strike_point(long unit,long target,real_point3d const *point,real_vector3d const *direction,real scale);
void vr_combat_velocity(long unit,real_point3d const *position,real_vector3d *velocity);
void vr_combat_controls(long unit);
boolean unit_vr_throw_grenade(long unit,short type,real_point3d const *point,real_vector3d const *velocity);
#endif
#endif
