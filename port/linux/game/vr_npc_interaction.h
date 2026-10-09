#ifndef HALO_VR_NPC_INTERACTION_H
#define HALO_VR_NPC_INTERACTION_H
#include "math/real_math.h"
void vr_npc_interaction_tick(void);
void vr_npc_interaction_reset(void);
void vr_npc_interaction_cancel(void);
void vr_npc_interaction_controls(long index);
void vr_npc_interaction_velocity(long index, float velocity[3]);
void vr_npc_interaction_palette(long index);
int vr_npc_interaction_owned(long index);
int vr_npc_interaction_hand(int hand,float point[3]);
long vr_npc_interaction_object(int hand);
int vr_npc_interaction_remote(long player_index,int hand,int held,const float world[3]);
void vr_npc_interaction_remote_cancel(long player_index,int hand);
/* WORLD surface coordinate, transformed by channel if it needs root-local. */
int vr_npc_interaction_remote_contact(long player,int hand,long *object,float point[3]);
int vr_npc_interaction_snapshot(long *index,int *count,real_matrix4x3 *matrices,int capacity);
#endif
