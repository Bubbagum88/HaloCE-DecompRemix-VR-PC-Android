#ifndef VR_MANUAL_RELOAD_H
#define VR_MANUAL_RELOAD_H
#ifdef HALO_VR
struct real_matrix4x3;
struct collision_result;
enum { VR_MANUAL_SUPPRESS_AUTO = 1, VR_MANUAL_BLOCK_FIRE = 2, VR_MANUAL_COMMIT = 4 };
void vr_manual_reload_reset(void);
void vr_manual_reload_debris_reset(void);
void vr_manual_reload_debris_prepare_for_state_restore(void);
void vr_manual_reload_debris_tick(void);
void vr_manual_reload_debris_render(void);
void vr_manual_reload_note_weapon(long weapon_index);
unsigned vr_manual_reload_update(long weapon_index, int explicit_reload);
void vr_manual_reload_model(long weapon_index, long model_index, struct real_matrix4x3 *matrices);
int vr_manual_reload_trace(float const from[3], float const vector[3], float radius,
    struct collision_result *result);
int vr_manual_reload_hand(int hand, float position[3]);
/* Test59: vr_render.c's: the camera the latest frame's gun and hands were
 * drawn from (0 if none recent) */
int vr_render_drawn_camera(float position[3]);
#endif
#endif
