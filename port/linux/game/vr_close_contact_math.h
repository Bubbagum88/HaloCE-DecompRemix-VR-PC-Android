#ifndef VR_CLOSE_CONTACT_MATH_H
#define VR_CLOSE_CONTACT_MATH_H
#include <math.h>
static float vr_close_radius_target(float stock, float baseline, float metres,
    float units, int enabled)
{
    if (!enabled || !isfinite(stock) || !isfinite(units) || stock <= 0 || units <= 0) return baseline;
    if (!isfinite(metres)) metres = .25f;
    if (metres < .18f) metres = .18f;
    if (metres > .60f) metres = .60f;
    return fminf(stock, metres * units);
}
static float vr_close_radius_step(float current, float target, float units)
{
    if (!isfinite(current) || current <= 0) return target;
    /* Shrinking cannot enter a previously blocked solid. Expanding requires
     * the caller's full capsule overlap check for this proposed step. */
    return target <= current ? target : fminf(target, current + .01f * units);
}
#endif
