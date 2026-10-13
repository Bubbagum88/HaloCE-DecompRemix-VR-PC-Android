/* Test65: ACTIVE RAGDOLL's body reactions: a touched, grabbed or struck NPC's
 * limb and torso give with the push, drawn only (vr_body_reactions.c). */
#ifndef HALO_VR_BODY_REACTIONS_H
#define HALO_VR_BODY_REACTIONS_H
#include "math/real_math.h"
#ifdef HALO_VR
int vr_body_reactions_enabled(void);
/* a blow at `point` along `push` (any length), 0 (a brush) to 1 (a full blow) */
void vr_body_reaction_hit(long object,real_point3d const *point,real_vector3d const *push,real strength);
/* a hand holding `node` of a living body that is not lifted: the limb is drawn
 * reaching toward `target` (refreshed each tick while held) */
void vr_body_reaction_hold(long object,short node,real_point3d const *target);
void vr_body_reactions_reset(void);
/* the drawn pose with the reactions added (stock when there are none) */
real_matrix4x3 *vr_body_reaction_render(long object,real_matrix4x3 *stock);
#else
#define vr_body_reactions_enabled() 0
#define vr_body_reaction_hit(object,point,push,strength) ((void)0)
#define vr_body_reaction_hold(object,node,target) ((void)0)
#define vr_body_reactions_reset() ((void)0)
#define vr_body_reaction_render(object,stock) (stock)
#endif
#endif
