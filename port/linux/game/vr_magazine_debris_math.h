#ifndef VR_MAGAZINE_DEBRIS_MATH_H
#define VR_MAGAZINE_DEBRIS_MATH_H

#include <math.h>
#include <limits.h>

enum { VR_MAGAZINE_DEBRIS_CAPACITY = 32 };

/* A magazine clone belongs to the manual-reload transaction until the
 * engine's ammo commit succeeds. This small policy object is shared with the
 * native render module so cancellation tests exercise the same transitions. */
struct vr_magazine_debris_transaction {
    int slot;
    int slot_valid;
    int committed_before_spawn;
};

static void vr_magazine_debris_transaction_init(struct vr_magazine_debris_transaction *transaction)
{
    if (!transaction) return;
    transaction->slot = -1;
    transaction->slot_valid = 0;
    transaction->committed_before_spawn = 0;
}

static int vr_magazine_debris_transaction_record(struct vr_magazine_debris_transaction *transaction, int slot)
{
    if (!transaction || slot < 0 || transaction->slot_valid || transaction->committed_before_spawn) return 0;
    transaction->slot = slot;
    transaction->slot_valid = 1;
    return 1;
}

/* Return an already-rendered provisional slot for the caller to commit. If
 * rendering has not happened yet, remember that the next clone is committed. */
static int vr_magazine_debris_transaction_commit(struct vr_magazine_debris_transaction *transaction)
{
    int slot;
    if (!transaction) return -1;
    if (!transaction->slot_valid) {
        transaction->committed_before_spawn = 1;
        return -1;
    }
    slot = transaction->slot;
    vr_magazine_debris_transaction_init(transaction);
    return slot;
}

static int vr_magazine_debris_transaction_cancel(struct vr_magazine_debris_transaction *transaction)
{
    int slot;
    if (!transaction) return -1;
    slot = transaction->slot_valid ? transaction->slot : -1;
    vr_magazine_debris_transaction_init(transaction);
    return slot;
}

static int vr_magazine_debris_transaction_is_provisional(
    struct vr_magazine_debris_transaction const *transaction)
{
    return transaction && !transaction->committed_before_spawn;
}

static void vr_magazine_debris_transaction_new_reload(
    struct vr_magazine_debris_transaction *transaction)
{
    if (transaction) transaction->committed_before_spawn = 0;
}

/* Magazines stay visible for the loaded map. When the bounded pool is full,
 * preserve existing drops and decline new visuals instead of deleting old
 * ones under the player. */
static int vr_magazine_debris_choose_slot(int const *active, int count)
{
    if (!active || count <= 0 || count > VR_MAGAZINE_DEBRIS_CAPACITY) return -1;
    for (int i = 0; i < count; ++i) {
        if (!active[i]) return i;
    }
    return -1;
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

/* Object datum indices may be reassigned while a same-map save/checkpoint is
 * restored. Keep the visual drop, but stop treating its former owner index as
 * a live collision exclusion after that transition. */
static long vr_magazine_debris_owner_after_state_restore(int active, long owner, long none)
{
    return active ? none : owner;
}

#endif
