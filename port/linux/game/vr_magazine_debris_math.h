#ifndef VR_MAGAZINE_DEBRIS_MATH_H
#define VR_MAGAZINE_DEBRIS_MATH_H

#include <math.h>
#include <limits.h>

enum { VR_MAGAZINE_DEBRIS_CAPACITY = 32 };

/* Deterministic fixed-pool policy: use a free slot, otherwise recycle the
 * oldest. A bad age input is treated as the oldest slot, never as free. */
static int vr_magazine_debris_choose_slot(int const *active, unsigned const *age, int count)
{
    int selected = -1;
    unsigned oldest = 0;
    if (!active || !age || count <= 0 || count > VR_MAGAZINE_DEBRIS_CAPACITY) return -1;
    for (int i = 0; i < count; ++i) {
        if (!active[i]) return i;
        if (selected < 0 || age[i] >= oldest) { selected = i; oldest = age[i]; }
    }
    return selected;
}

/* Saturating map-session age is used only to recycle the oldest visual when
 * the fixed pool fills. Active debris has no timed expiry. */
static int vr_magazine_debris_advance_age(unsigned *age)
{
    if (!age) return 0;
    if (*age < UINT_MAX) ++*age;
    return 1;
}

static int vr_magazine_debris_speed_valid(float const velocity[3], float maximum)
{
    float squared = 0.0f;
    if (!velocity || !isfinite(maximum) || maximum <= 0.0f) return 0;
    for (int i = 0; i < 3; ++i) {
        if (!isfinite(velocity[i])) return 0;
        squared += velocity[i] * velocity[i];
    }
    return isfinite(squared) && squared <= maximum * maximum;
}

static int vr_magazine_debris_spawn_allowed(int enabled, int local_session,
    int supported_profile, int node_count, unsigned long long component_nodes,
    float radius, float maximum_radius)
{
    if (!enabled || !local_session || !supported_profile || node_count <= 0 || node_count > 64 ||
        component_nodes == 0 || !isfinite(radius) || !isfinite(maximum_radius) ||
        radius <= 0.0f || maximum_radius <= 0.0f || radius > maximum_radius) return 0;
    return 1;
}

#endif
