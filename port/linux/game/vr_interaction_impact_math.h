#ifndef VR_INTERACTION_IMPACT_MATH_H
#define VR_INTERACTION_IMPACT_MATH_H
#include <math.h>
/* Explicit gameplay tuning: kinetic scaling, not a claim of kilogram mass.
 * Native acceleration_scale is inverse impulse response. */
static float vr_interaction_impact_scale(float normal_speed, float units,
    float mobility, float threshold, float maximum)
{
    float speed, weight, energy;
    if (!isfinite(normal_speed) || !isfinite(units) || units <= 0 ||
        !isfinite(mobility) || mobility <= 0 || !isfinite(threshold) ||
        !isfinite(maximum) || threshold < 0 || maximum <= 0) return 0;
    speed = normal_speed * 30.0f / units;
    if (speed <= threshold) return 0;
    weight = fminf(4.0f, fmaxf(0.25f, 1.0f / mobility));
    energy = (speed * speed - threshold * threshold) * weight / 36.0f;
    return fminf(maximum, fmaxf(0, energy));
}
/* Test56: the share of a thrown thing's velocity that a struck body or
 * vehicle takes (momentum, gameplay-tuned): a light prop 0.3, a heavy body
 * up to 0.48; the shove itself is capped at VR_IMPACT_SHOVE_MAXIMUM m/s. */
#define VR_IMPACT_SHOVE_MAXIMUM 4.0f
static float vr_interaction_impact_share(float mobility)
{
    float weight;
    if (!isfinite(mobility) || mobility <= 0) return 0;
    weight = fminf(4.0f, fmaxf(0.25f, 1.0f / mobility));
    return 0.6f * weight / (weight + 1.0f);
}
#endif
