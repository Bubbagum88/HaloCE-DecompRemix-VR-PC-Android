#ifndef HALO_VR_WEIGHT_FEEDBACK_MATH_H
#define HALO_VR_WEIGHT_FEEDBACK_MATH_H
#include <math.h>
static inline float vr_weight_feedback_amplitude(float mobility, float strain_metres, float speed_metres_per_second)
{
    float resistance, strain, motion, load;
    if (!isfinite(mobility) || !isfinite(strain_metres) || !isfinite(speed_metres_per_second) ||
        strain_metres < 0 || speed_metres_per_second < 0) return 0.0f;
    resistance = fminf(1.0f, fmaxf(0.0f, (1.0f - mobility) * 0.8f));
    strain = fminf(1.0f, strain_metres / 0.35f);
    motion = fminf(1.0f, speed_metres_per_second / 2.5f);
    load = resistance * 0.55f + strain * 0.30f + motion * 0.15f;
    if (load < 0.18f) return 0.0f;
    return fminf(0.24f, 0.045f + load * 0.19f);
}
#endif
