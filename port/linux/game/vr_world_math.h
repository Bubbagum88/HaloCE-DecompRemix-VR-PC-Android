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
/* Test56: LIFT STRENGTH (vr.npc_hold_strength, the NPC hold's 0.75..2.5 with
 * SPARTAN 1.5 its default) for props, turrets and vehicles: relative to that
 * default, so the default holds them exactly as before (strength 1) and IRON
 * lifts heavy things (a Shade, a Ghost) more readily. */
static inline float vr_world_lift_strength(float setting)
{
    if (!isfinite(setting)) return 1.0f;
    return fmaxf(0.75f, fminf(2.5f, fmaxf(0.75f, fminf(2.5f, setting)) / 1.5f));
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
/* Test55: Spartan throwing strength by weight class (a gameplay class, not a
 * kilogram claim): a body a hand lifts easily (Grunt, Jackal: one hand, light)
 * flies 2.4x the hand's speed, a one-hand Marine 1.8x, a two-hand Elite or
 * Hunter 1.25x. */
static inline float vr_world_throw_class(int hands, float mobility)
{
    if (hands > 1) return 1.25f;
    return isfinite(mobility) && mobility >= 0.4f ? 2.4f : 1.8f;
}
/* Test55: the NPC throw: the release velocity above times VR THROW STRENGTH
 * and the weight class, capped at the class's multiple of the Test54 cap and
 * never above 24 m/s (0.8 m a tick). */
static inline int vr_world_throw_velocity_spartan(float const average[3], float const latest[3],
    float strength, float spartan, float units, float out[3])
{
    int i;
    if (!isfinite(strength)) strength = 1.0f;
    strength = fmaxf(0.75f, fminf(2.0f, strength));
    if (!isfinite(spartan)) spartan = 1.0f;
    spartan = fmaxf(1.0f, fminf(2.5f, spartan));
    if (!(units > 0.0f && units < 100.0f)) return 0;
    for (i = 0; i < 3; ++i) {
        if (!isfinite(average[i]) || !isfinite(latest[i])) return 0;
        out[i] = (average[i] * 0.35f + latest[i] * 0.65f) * strength * spartan;
    }
    return vr_world_limit(out, fminf(units * 0.24f * strength * spartan, units * 0.8f));
}
/* Test56: the hand's motion at release: the mean of the two fastest of the
 * last VR_WORLD_THROW_HISTORY ticks' movements. A throw peaks just before the
 * grip opens, so the last tick is often already slowing (the Test54/55
 * blend of a smoothed average and the last tick threw short and unevenly),
 * and one noisy tick alone cannot spike it. history: per-tick movements in
 * any order. */
#define VR_WORLD_THROW_HISTORY 4
static inline int vr_world_throw_peak(float const history[][3], int count, float out[3])
{
    int i, k, first = -1, second = -1;
    float speed[VR_WORLD_THROW_HISTORY];
    if (!history || !out || count < 1) return 0;
    if (count > VR_WORLD_THROW_HISTORY) count = VR_WORLD_THROW_HISTORY;
    for (i = 0; i < count; ++i) {
        speed[i] = history[i][0] * history[i][0] + history[i][1] * history[i][1] + history[i][2] * history[i][2];
        if (!isfinite(speed[i])) return 0;
        if (first < 0 || speed[i] > speed[first]) { second = first; first = i; }
        else if (second < 0 || speed[i] > speed[second]) second = i;
    }
    for (k = 0; k < 3; ++k)
        out[k] = second < 0 ? history[first][k] : (history[first][k] + history[second][k]) * 0.5f;
    return 1;
}
/* a tick's hand movement into the history ring */
static inline void vr_world_throw_note(float history[][3], int *count, int *next, float const movement[3])
{
    int k;
    if (!history || !count || !next || !movement) return;
    if (*next < 0 || *next >= VR_WORLD_THROW_HISTORY) *next = 0;
    for (k = 0; k < 3; ++k) history[*next][k] = movement[k];
    *next = (*next + 1) % VR_WORLD_THROW_HISTORY;
    if (*count < VR_WORLD_THROW_HISTORY) ++*count;
}
/* Test55: one hand on a body that needs two restrains it: the horizontal
 * velocity pulls toward the hand's anchor, slowly (heavier is slower, at most
 * 0.8 m/s), and the vertical stays the body's own (no lift). */
static inline int vr_world_restrain(float const error[3], float const current[3],
    float mobility, float units, float out[3])
{
    float desired[3], alpha;
    int i;
    if (!(units > 0 && units < 100) || !isfinite(mobility)) return 0;
    for (i = 0; i < 3; ++i) if (!isfinite(error[i]) || !isfinite(current[i])) return 0;
    mobility = fmaxf(0.1f, fminf(1.0f, mobility));
    alpha = 0.25f * sqrtf(mobility);
    desired[0] = error[0] * alpha; desired[1] = error[1] * alpha; desired[2] = 0.0f;
    if (!vr_world_limit(desired, units * (0.8f / 30.0f))) return 0;
    out[0] = desired[0]; out[1] = desired[1]; out[2] = current[2];
    return 1;
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
