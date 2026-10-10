#ifndef VR_HAPTICS_MATH_H
#define VR_HAPTICS_MATH_H

#include <math.h>

/* Keep malformed config/runtime values away from OpenXR while preserving the
 * existing per-effect amplitude and duration behavior for valid values. */
static float vr_haptics_level(float level)
{
    if (!isfinite(level)) return 0.0f;
    return level < 0.0f ? 0.0f : level > 1.0f ? 1.0f : level;
}

static int vr_haptics_scale(float level, float amplitude, float seconds,
    float *scaled_amplitude)
{
    float safe_level = vr_haptics_level(level);
    if (!scaled_amplitude || safe_level <= 0.0f || !isfinite(amplitude) ||
        amplitude <= 0.0f || !isfinite(seconds) || seconds <= 0.0f)
        return 0;
    amplitude *= safe_level;
    if (!isfinite(amplitude) || amplitude <= 0.0f) return 0;
    *scaled_amplitude = amplitude > 1.0f ? 1.0f : amplitude;
    return 1;
}

#endif
