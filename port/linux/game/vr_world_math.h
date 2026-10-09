#ifndef HALO_VR_WORLD_MATH_H
#define HALO_VR_WORLD_MATH_H
#include <math.h>
static int vr_world_authority(int local, int server, int campaign)
{
    return local || (server && campaign);
}
/* Velocities are world units/tick (the native item_update convention). */
static int vr_world_limit(float v[3], float limit)
{
    float length;
    int i;
    for (i = 0; i < 3; ++i) if (!isfinite(v[i])) return 0;
    length = sqrtf(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
    if (!isfinite(length) || !isfinite(limit) || limit <= 0) return 0;
    if (length > limit) for (i = 0; i < 3; ++i) v[i] *= limit / length;
    return 1;
}
static int vr_world_spring(float const error[3], float const current[3],
    float mobility, int hands, float units, float gravity, float out[3])
{
    float delta[3], desired[3], alpha;
    int i;
    if (!(units > 0 && units < 100) || !isfinite(mobility) || !isfinite(gravity)) return 0;
    mobility = fmaxf(0.25f, fminf(2.0f, mobility));
    alpha = (hands == 2 ? 0.50f : 0.35f) * sqrtf(mobility);
    for (i = 0; i < 3; ++i) desired[i] = error[i] * alpha;
    if (!vr_world_limit(desired, units * (hands == 2 ? 0.18f : 0.12f))) return 0;
    desired[2] += gravity;
    for (i = 0; i < 3; ++i) delta[i] = desired[i] - current[i];
    if (!vr_world_limit(delta, units * 0.035f * mobility * (hands == 2 ? 1.5f : 1.0f))) return 0;
    for (i = 0; i < 3; ++i) out[i] = current[i] + delta[i];
    return vr_world_limit(out, units * 0.20f);
}
#endif
