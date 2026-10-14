#ifndef HALO_VR_COMBAT_MOVES_H
#define HALO_VR_COMBAT_MOVES_H
#include "math/real_math.h"

struct vr_combat_pose_request;
enum vr_combat_move_event_type {
    VR_COMBAT_MOVE_ATTACK_SWEEP=1,
    VR_COMBAT_MOVE_ATTACK_OVERHEAD,
    VR_COMBAT_MOVE_ATTACK_JAB,
    VR_COMBAT_MOVE_DUCK,
    VR_COMBAT_MOVE_SIDESTEP,
    VR_COMBAT_MOVE_ARM_OPENING,
    VR_COMBAT_MOVE_PUMMEL_OPENING,
    VR_COMBAT_MOVE_PUMMEL_HIT
};
enum { VR_COMBAT_MOVE_TARGETS=16 };
struct vr_combat_move_event {
    int type,hand;
    long target;
};

#ifdef HALO_VR
void vr_combat_moves_reset(void);
void vr_combat_moves_tick(long owner);
void vr_combat_moves_note_melee(long owner,long attacker);
/* Call only for a genuine unarmed native contact. This never deals damage. */
void vr_combat_moves_note_hit(long owner,long target,real_point3d const *point,
    real_vector3d const *direction,real scale);
/* Call only for an incoming native melee damage event. */
real vr_combat_moves_defend(long owner,long attacker);
int vr_combat_moves_opening(long target);
/* Event-style glyph code for the live native windup or earned opening, 0 none. */
int vr_combat_moves_cue(long target);
long vr_combat_moves_cue_target(int slot);
int vr_combat_moves_pose(long target,struct vr_combat_pose_request *out);
int vr_combat_moves_poll_event(struct vr_combat_move_event *out);
#endif
#endif
