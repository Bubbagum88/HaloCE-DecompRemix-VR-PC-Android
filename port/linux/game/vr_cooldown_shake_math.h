#ifndef HALO_VR_COOLDOWN_SHAKE_MATH_H
#define HALO_VR_COOLDOWN_SHAKE_MATH_H
#include <math.h>
static inline float vr_cooldown_shake_multiplier(float metres_per_second)
{
    if (!isfinite(metres_per_second) || metres_per_second <= 0.9f) return 1.0f;
    if (metres_per_second >= 2.7f) return 2.5f;
    return 1.0f + (metres_per_second - 0.9f) * (1.5f / 1.8f);
}
static inline int vr_cooldown_shake_is_reversal(float previous_speed, float current_speed, float direction_cosine)
{
    return isfinite(previous_speed) && isfinite(current_speed) && isfinite(direction_cosine) &&
        previous_speed >= 1.0f && current_speed >= 1.0f && direction_cosine <= -0.35f;
}
static inline float vr_cooldown_shake_decay(float speed, float elapsed_seconds)
{
    if (!isfinite(speed) || !isfinite(elapsed_seconds) || speed <= 0.0f || elapsed_seconds < 0.0f)
        return 0.0f;
    return speed * expf(-fminf(elapsed_seconds, 2.0f) / 0.35f);
}
#endif
