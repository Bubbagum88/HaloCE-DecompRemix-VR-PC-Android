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
/* Test71: the held weapon's model is the needler's rig (a mod's needler) */
int vr_manual_reload_needle_rig(long weapon_index);
int vr_manual_reload_trace(float const from[3], float const vector[3], float radius,
    struct collision_result *result);
int vr_manual_reload_hand(int hand, float position[3]);
/* A brief reload click currently owns that hand's surface feedback. */
int vr_manual_reload_feedback_active(int hand);
/* Test59: vr_render.c's: the camera the latest frame's gun and hands were
 * drawn from (0 if none recent) */
int vr_render_drawn_camera(float position[3]);
/* Test66: the part the reload holds (0 the magazine, 1 the slide or handle)
 * and how far its grip has closed (0..1); 0 when none */
int vr_manual_reload_grip_state(int *part, float *amount);
/* Test66: vr_render.c's: the magazine (0) or handle (1) as the drawn off
 * hand holds it in the weapon's own reload animation (world) */
int vr_render_reload_grip(int part, struct real_matrix4x3 *out);
#endif
#endif
