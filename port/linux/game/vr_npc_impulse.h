#ifndef VR_NPC_IMPULSE_H
#define VR_NPC_IMPULSE_H

#include <math.h>

/* Test56: how a killing blow moves a death ragdoll, read from the damage
 * effect the engine just applied (object_cause_damage). In the stock Xbox
 * maps bullets and bolts carry no push of their own (instantaneous
 * acceleration 0: pistol 25 damage, assault rifle 10, sniper 101, charged
 * plasma 70), melee and explosions do (Elite melee 2.5 world units/s, Hunter
 * melee 9, frag grenade 4, rocket 6). So:
 * - a shot kicks the joints where it lands, harder for heavier rounds (an
 *   assault rifle bullet ~1.1 m/s, a pistol ~1.6, a sniper round ~3.8), plus
 *   a little of the whole body;
 * - a melee blow kicks harder, and its own push moves the body;
 * - an explosion throws the whole body away from the blast with some lift.
 * Hits landing on one body in the same tick (shotgun pellets, a burst) add
 * up, at most VR_NPC_HIT_LOCAL_MAXIMUM. Speeds in m/s. */
enum { VR_NPC_HIT_CATEGORY_MELEE = 6 };
#define VR_NPC_HIT_LOCAL_MAXIMUM 6.0f
struct vr_npc_hit { float local, body, lift; };
/* damage: the effect's upper bound times its scale; acceleration: its
 * instantaneous acceleration (world units/s) times its scale; area: the
 * damage is an explosion's (it already falls off with distance) */
static inline int vr_npc_hit_kick(float damage, float acceleration, int category, int area,
    float units_per_metre, struct vr_npc_hit *out)
{
    float push;
    if (!out || !isfinite(damage) || !isfinite(acceleration) || !isfinite(units_per_metre) ||
        !(units_per_metre > 0.0f)) return 0;
    if (damage < 0.0f) damage = 0.0f;
    if (acceleration < 0.0f) acceleration = 0.0f;
    push = acceleration / units_per_metre;
    if (area) {
        out->local = 1.5f;
        out->body = fminf(push * 0.35f, 7.0f);
        out->lift = out->body * 0.45f;
    } else if (category == VR_NPC_HIT_CATEGORY_MELEE || push > 0.0f) {
        out->local = fminf(1.5f + 0.02f * damage + 0.1f * push, VR_NPC_HIT_LOCAL_MAXIMUM);
        out->body = fminf(0.05f * push, 1.5f);
        out->lift = 0.0f;
    } else {
        out->local = fminf(fmaxf(0.8f + 0.03f * damage, 1.0f), 4.5f);
        out->body = fminf(0.004f * damage, 0.5f);
        out->lift = 0.0f;
    }
    return 1;
}
/* another hit on the same body in the same tick */
static inline void vr_npc_hit_add(struct vr_npc_hit *total, struct vr_npc_hit const *hit)
{
    total->local = fminf(total->local + hit->local, VR_NPC_HIT_LOCAL_MAXIMUM);
    total->body = fmaxf(total->body, hit->body);
    total->lift = fmaxf(total->lift, hit->lift);
}

#endif
