#ifndef HALO_VR_WORLD_INTERACTION_H
#define HALO_VR_WORLD_INTERACTION_H
struct network_interaction_hand;
boolean vr_world_interaction_remote(struct network_interaction_hand const *request);
void vr_world_interaction_remote_cancel(long player,int hand);
void vr_world_interaction_remote_reset(void);
void vr_world_interaction_remote_tick(void);
boolean vr_world_interaction_remote_owned(long object);
boolean vr_world_interaction_remote_contact(long player,int hand,long *object,float world_point[3]);
#ifdef HALO_VR
void vr_world_interaction_tick(void);
void vr_world_interaction_reset(void);
/* Current constrained contact for visual hand compliance (world coordinates). */
int vr_world_interaction_hand(int hand, float point[3]);
long vr_world_interaction_object(int hand);
/* Optional, local VR-only load feedback. Values use SI metres and m/s. */
void vr_world_interaction_weight_feedback(int hand, float mobility,
	float strain_metres, float speed_metres_per_second);
#else
#define vr_world_interaction_tick() ((void)0)
#define vr_world_interaction_reset() ((void)0)
#define vr_world_interaction_hand(hand,point) 0
#define vr_world_interaction_object(hand) (-1)
#define vr_world_interaction_weight_feedback(hand,mobility,strain,speed) ((void)0)
#endif
#endif
