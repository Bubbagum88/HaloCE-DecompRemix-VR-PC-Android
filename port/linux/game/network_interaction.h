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

/* Test73 (item 10d, the owner: one co-op VR toggle for the host and every
player): VR INTERACTIONS (net.physical_interactions, the host's) also covers
these, each said by the host (what it allows) and by each client (what it
uses) when they negotiate. A host or client without them never says them, so
a mixed session keeps stock controls for those. */
enum
{
	NETWORK_VR_RELOAD = 1,    /* manual reload: a client's commit sent to the host */
	NETWORK_VR_GRENADES = 2,  /* physical grenades: a client's throw sent to the host */
	NETWORK_VR_MOVEMENT = 4,  /* parkour and slides: the host's movement bound allows them */
	NETWORK_VR_MELEE = 8,     /* physical melee and fist combat: a client's blows sent to the host */
	NETWORK_VR_FEATURES = 15
};
enum { NETWORK_VR_ACTION_RELOAD = 1, NETWORK_VR_ACTION_GRENADE = 2, NETWORK_VR_ACTION_STRIKE = 3 };
/* whether this machine's player may use the feature now: in a local game,
yes; a co-op host, when VR INTERACTIONS is on and every client negotiated;
a client, when its host said it allows the feature */
boolean network_interaction_vr_allowed(unsigned long feature);
/* (the host) whether a client's player uses the feature, as its machine
said: player is the player's datum index */
boolean network_interaction_player_vr(long player, unsigned long feature);
/* (the host) whether a unit is a client's player's whose weapons are
reloaded by hand (no automatic reload when empty) */
boolean network_interaction_unit_manual_reload(long unit);
/* (a client) an action for the host: a reload's commit (object: the held
weapon's tag) or a grenade's throw (object: its type; at position with
vector a tick) */
void network_interaction_client_action(byte kind,long player,long unit,long object,
    real_point3d const *position,real_vector3d const *vector);
/* (a client) a fist blow for the host (the owner: "make it so everyone can do
advanced fist combat"): the body struck, where, along what, its strength, its
fist combat's share and the shove that goes with it (world units a tick) */
void network_interaction_client_strike(long player,long unit,long target,real_point3d const *point,
    real_vector3d const *direction,real scale,real multiplier,real_vector3d const *shove);
#endif
