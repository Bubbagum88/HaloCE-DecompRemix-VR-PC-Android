#ifndef HALO_VR_WORLD_MATH_H
#define HALO_VR_WORLD_MATH_H
#include <math.h>
static int vr_world_authority(int local, int server, int campaign)
{
    return local || (server && campaign);
}
/* Contact tolerance for the tracked palm collider. This is a sphere radius,
 * not a ray reach: callers must verify overlap with the contacted collision
 * model or world surface before Grip can acquire it. */
static inline float vr_world_hand_contact_radius(float metres, float units_per_metre)
{
    if (!isfinite(metres) || !isfinite(units_per_metre) || units_per_metre <= 0.0f)
        return 0.0f;
    if (metres < 0.02f) metres = 0.02f;
    if (metres > 0.08f) metres = 0.08f;
    return metres * units_per_metre;
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
static inline int vr_world_spring(float const error[3], float const current[3],
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
/* Test54: the same spring with a hold strength (VR NPC HOLD: 0.75..2.5; 1 is
 * the spring above). Strength stiffens the follow and raises its speed and
 * acceleration limits, so a one-hand Grunt stays in the hand while an Elite or
 * Hunter (low mobility, two hands) still drags behind it. */
static inline int vr_world_spring_strength(float const error[3], float const current[3],
    float mobility, int hands, float units, float gravity, float strength, float out[3])
{
    float delta[3], desired[3], alpha;
    int i;
    if (!(units > 0 && units < 100) || !isfinite(mobility) || !isfinite(gravity) || !isfinite(strength)) return 0;
    strength = fmaxf(0.75f, fminf(2.5f, strength));
    mobility = fmaxf(0.25f, fminf(2.0f, mobility));
    alpha = fminf(0.85f, (hands == 2 ? 0.50f : 0.35f) * sqrtf(mobility) * strength);
    for (i = 0; i < 3; ++i) desired[i] = error[i] * alpha;
    if (!vr_world_limit(desired, units * (hands == 2 ? 0.18f : 0.12f) * fminf(strength, 1.75f))) return 0;
    desired[2] += gravity;
    for (i = 0; i < 3; ++i) delta[i] = desired[i] - current[i];
    if (!vr_world_limit(delta, units * 0.035f * mobility * (hands == 2 ? 1.5f : 1.0f) * strength)) return 0;
    for (i = 0; i < 3; ++i) out[i] = current[i] + delta[i];
    return vr_world_limit(out, units * 0.20f * fminf(strength, 1.75f));
}
/* Test54: a release velocity weighted to the latest hand motion (an average
 * alone lags a flick's peak), scaled by VR THROW STRENGTH and capped. */
static inline int vr_world_throw_velocity(float const average[3], float const latest[3],
    float strength, float units, float out[3])
{
    int i;
    if (!isfinite(strength)) strength = 1.0f;
    strength = fmaxf(0.75f, fminf(2.0f, strength));
    for (i = 0; i < 3; ++i) {
        if (!isfinite(average[i]) || !isfinite(latest[i])) return 0;
        out[i] = (average[i] * 0.35f + latest[i] * 0.65f) * strength;
    }
    return vr_world_limit(out, units * 0.24f * strength);
}
/* Distance from a point to the segment a-b (articulated bone capsules). */
static inline float vr_world_segment_distance(float const point[3], float const a[3], float const b[3])
{
    float ab[3], ap[3], length2 = 0.0f, t = 0.0f, d2 = 0.0f;
    int i;
    for (i = 0; i < 3; ++i) { ab[i] = b[i] - a[i]; ap[i] = point[i] - a[i]; length2 += ab[i] * ab[i]; t += ap[i] * ab[i]; }
    t = length2 > 1e-12f ? fmaxf(0.0f, fminf(1.0f, t / length2)) : 0.0f;
    for (i = 0; i < 3; ++i) { float d = ap[i] - ab[i] * t; d2 += d * d; }
    return isfinite(d2) ? sqrtf(d2) : INFINITY;
}
#endif
