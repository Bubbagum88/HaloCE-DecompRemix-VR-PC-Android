#ifndef HALO_NETWORK_INTERACTION_H
#define HALO_NETWORK_INTERACTION_H
#include "math/real_math.h"
enum { NETWORK_INTERACTION_WORLD=1, NETWORK_INTERACTION_NPC=2 };
struct network_interaction_hand {
    long player, unit, object;
    byte hand, kind, held, pressed;
    real_point3d position;
    real_vector3d forward, up;
    unsigned long sequence;
};
void network_interaction_client_cancel(byte hand,long player,long unit);
void network_interaction_client_send(byte hand,byte held,byte features,long player,long unit,
    real_point3d const *position,real_vector3d const *forward,real_vector3d const *up);
void vr_interaction_client_tick(boolean ready, boolean npc_ready);
void vr_interaction_client_reset(void);
void vr_interaction_client_result(long unit,byte hand,byte features,unsigned long sequence,long object,float const local[3]);
int vr_interaction_client_hand(int hand,float point[3]);
long vr_interaction_client_object(int hand);
void network_interaction_reset(void);
void network_interaction_tick(void);
void network_interaction_receive(long machine, byte type, void const *data, short count, word size);
boolean network_interaction_host_ready(void);
boolean network_interaction_npc_ready(void);
boolean network_interaction_palette_owned(long unit);
void network_interaction_palette(long unit);
real_matrix4x3 *network_interaction_render(long unit, real_matrix4x3 *stock);
#endif
