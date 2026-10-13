#ifndef HALO_VR_NPC_INTERACTION_H
#define HALO_VR_NPC_INTERACTION_H
#include "math/real_math.h"
/* Test61: 24 (16 before): the owner asked for more bodies at once */
#define VR_NPC_INTERACTION_POOL_SIZE 24
void vr_npc_interaction_tick(void);
void vr_npc_interaction_reset(void);
void vr_npc_interaction_cancel(void);
void vr_npc_interaction_controls(long index);
void vr_npc_interaction_velocity(long index, float velocity[3]);
void vr_npc_interaction_palette(long index);
int vr_npc_interaction_owned(long index);
int vr_npc_interaction_restrained(long index);
int vr_npc_interaction_hand(int hand,float point[3]);
long vr_npc_interaction_object(int hand);
int vr_npc_interaction_remote(long player_index,int hand,int held,const float world[3]);
void vr_npc_interaction_remote_cancel(long player_index,int hand);
/* WORLD surface coordinate, transformed by channel if it needs root-local. */
int vr_npc_interaction_remote_contact(long player,int hand,long *object,float point[3]);
int vr_npc_interaction_snapshot(long *index,int *count,real_matrix4x3 *matrices,int capacity);
/* Test54: a supported NPC just killed falls as a ragdoll (vr.death_ragdolls) */
void vr_npc_interaction_death(long index);
/* Test55: where a biped was just hit (object_cause_damage), for the death
 * ragdoll's impact-located kick. Test56: and how hard (vr_npc_impulse.h):
 * damage and acceleration already scaled by the hit's scale; area: an
 * explosion's damage. */
void vr_npc_interaction_note_damage(long object,real_point3d const *point,real_vector3d const *direction,
    real damage,real acceleration,short category,int area);
/* Test65: ticks a hand has held `index` (-1: not held); a living NPC knocked
 * off its feet along `direction` at `speed_mps` (TRUE when it went down) */
long vr_npc_interaction_hold_age(long index);
int vr_npc_interaction_knock(long index,real_point3d const *point,real_vector3d const *direction,real speed_mps);
#endif
