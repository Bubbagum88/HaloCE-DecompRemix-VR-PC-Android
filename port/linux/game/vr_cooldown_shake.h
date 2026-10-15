#ifndef HALO_VR_COOLDOWN_SHAKE_H
#define HALO_VR_COOLDOWN_SHAKE_H
/* the held weapon's heat loss multiplier (1: none), sampled each tick */
float vr_cooldown_shake_rate(long weapon_index);
/* Test70: the needler with MANUAL RELOAD: its automatic reload waits for a
shake (or the reload button), which starts the native reload */
enum { VR_NEEDLER_SHAKE_SUPPRESS_AUTO = 1, VR_NEEDLER_SHAKE_RELOAD = 2 };
unsigned vr_needler_shake_update(long weapon_index, boolean reload_button);
#endif
