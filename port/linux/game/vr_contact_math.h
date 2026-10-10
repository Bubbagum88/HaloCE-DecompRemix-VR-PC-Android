#ifndef VR_CONTACT_MATH_H
#define VR_CONTACT_MATH_H

#include <math.h>

/* Fixed cost: at most eight pose queries. A partially bent finger can clear
 * geometry even when both extreme poses intersect it. Search each direction
 * in order before refining the first clear interval; preserve contact direction
 * whenever it still has a clear solution. No heap or world state here. */
typedef float (*vr_contact_query)(void *context, int direction, float amount);
static float vr_contact_search(vr_contact_query query, void *context,
    int previous_direction, float initial_score, int *direction)
{
    int preferred = previous_direction > 0 ? 1 : -1;
    float best_score = isfinite(initial_score) ? initial_score : 0.0f, best_amount = 0.0f;
    int best_direction = preferred, calls = 0;
    for (int way = 0; way < 2; ++way) {
        int d = way ? -preferred : preferred;
        float low = 0.0f;
        for (int step = 1; step <= 3; ++step) {
            float high = step / 3.0f;
            float score = query(context, d, high);
            ++calls;
            if (!isfinite(score)) score = 0.0f;
            if (score > best_score) {
                best_score = score; best_amount = high; best_direction = d;
            }
            if (score >= 1.0f) {
                while (calls < 8) {
                    float middle = 0.5f * (low + high);
                    score = query(context, d, middle);
                    ++calls;
                    if (isfinite(score) && score >= 1.0f) high = middle;
                    else low = middle;
                }
                *direction = d;
                return high;
            }
            low = high;
        }
    }
    /* Fully enclosed geometry has no guaranteed solution. Keep the least
     * penetrating tested pose instead of forcing maximum curl. */
    *direction = best_direction;
    return best_amount;
}

struct vr_contact_pulse_state {
    double time, released_since;
    int touching, initialized;
};

/* A contact pulse must be perceptible at first touch, then rise with palm
 * penetration and fingertip coverage. The global vr.haptics master is applied
 * by vr_haptic() after this value is calculated. */
static float vr_contact_haptic_strength(float depth_metres, int finger_contacts)
{
    float depth, fingers;
    if (!isfinite(depth_metres) || depth_metres < 0.0f) depth_metres = 0.0f;
    if (finger_contacts < 0) finger_contacts = 0;
    if (finger_contacts > 5) finger_contacts = 5;
    depth = fminf(depth_metres, 0.12f) / 0.12f;
    fingers = (float)finger_contacts;
    return fminf(0.75f, 0.20f + 0.42f * depth + 0.035f * fingers);
}

/* One short pulse per contact, rearmed only after 80ms clear. Repeated render
 * passes at the same pose time never renew a vibration. */
static int vr_contact_pulse(struct vr_contact_pulse_state *state,
    double now, int touching)
{
    int pulse = 0;
    if (!isfinite(now)) { state->initialized = 0; return 0; }
    if (!state->initialized || now < state->time || now - state->time > 0.25) {
        state->touching = 0;
        state->released_since = now - 0.08;
        state->initialized = 1;
    } else if (now == state->time) return 0;
    if (touching) {
        pulse = !state->touching && now - state->released_since >= 0.079999;
        state->touching = 1;
    } else {
        if (state->touching) state->released_since = now;
        state->touching = 0;
    }
    state->time = now;
    return pulse;
}
#endif
