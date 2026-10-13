/* Test65: WEAPON PULL: a weapon lying within reach glows, and a grip pulls
 * it into the hand and equips it (vr_weapon_pickup.c). */
#ifndef HALO_VR_WEAPON_PICKUP_H
#define HALO_VR_WEAPON_PICKUP_H
#ifdef HALO_VR
void vr_weapon_pickup_reset(void);
/* player_control.c, each tick, after the hands' actions */
void vr_weapon_pickup_tick(short local_player_index);
/* the per-eye controls pass: the glow on what a hand can pull */
int vr_weapon_pickup_render(float const camera[3]);
/* whether `hand` is pulling a weapon (its grip is spoken for) */
int vr_weapon_pickup_busy(int hand);
#else
#define vr_weapon_pickup_reset() ((void)0)
#define vr_weapon_pickup_tick(local) ((void)0)
#define vr_weapon_pickup_render(camera) 0
#define vr_weapon_pickup_busy(hand) 0
#endif
#endif
