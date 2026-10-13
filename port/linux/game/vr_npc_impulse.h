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
/* Test59: DEATH FORCE (vr.death_force). The owner's Test58 session: bodies
 * shot dead with an assault rifle crumpled where they stood (a bullet's whole
 * body push was 0.04 m/s) and explosions threw them too little. 0 CLASSIC is
 * Test56's (vr_npc_hit_kick); 1 STRONG, the default, and 2 HUGE throw a body
 * along the shots and away from blasts:
 * - a shot's joints kick a quarter harder; the whole body's push comes from
 *   the burst (vr_npc_burst_body), with a little lift so it leaves the ground;
 * - a melee blow pushes the body twice as hard;
 * - an explosion throws it about twice as hard, with more lift (frag ~7 m/s,
 *   rocket ~11 m/s at its centre). HUGE is half as much again. */
enum { VR_NPC_FORCE_CLASSIC, VR_NPC_FORCE_STRONG, VR_NPC_FORCE_HUGE };
#define VR_NPC_FORCE_MAXIMUM_SPEED 16.0f
static inline int vr_npc_force_from_name(char const *name)
{
    if (!name) return VR_NPC_FORCE_STRONG;
    if (name[0] == 'c') return VR_NPC_FORCE_CLASSIC;
    if (name[0] == 'h') return VR_NPC_FORCE_HUGE;
    return VR_NPC_FORCE_STRONG;
}
static inline int vr_npc_hit_kick_force(float damage, float acceleration, int category, int area,
    float units_per_metre, int force, struct vr_npc_hit *out)
{
    float push, scale;
    if (!vr_npc_hit_kick(damage, acceleration, category, area, units_per_metre, out)) return 0;
    if (force <= VR_NPC_FORCE_CLASSIC) return 1;
    scale = force >= VR_NPC_FORCE_HUGE ? 1.5f : 1.0f;
    push = fmaxf(acceleration, 0.0f) / units_per_metre;
    if (area) {
        out->local = 2.0f;
        out->body = fminf(fminf(push * 0.6f, 12.0f) * scale, VR_NPC_FORCE_MAXIMUM_SPEED);
        out->lift = out->body * 0.5f;
    } else if (category == VR_NPC_HIT_CATEGORY_MELEE || push > 0.0f) {
        out->local = fminf(out->local * 1.25f, VR_NPC_HIT_LOCAL_MAXIMUM);
        out->body = fminf(fminf(0.1f * push, 3.0f) * scale, VR_NPC_FORCE_MAXIMUM_SPEED);
        out->lift = out->body * 0.1f;
    } else {
        /* Test66: the owner's Test65: deaths should show how they were
         * hit: a shot's joints twice Test56's (an assault rifle round
         * 2.2 m/s, a pistol 3.2, a sniper round at the 6 m/s most) */
        out->local = fminf(out->local * 2.0f * scale, VR_NPC_HIT_LOCAL_MAXIMUM);
        /* the whole body's push is the burst's (vr_npc_burst_body) */
    }
    return 1;
}
/* Test59: the whole body's push from the shots (bullets and bolts, no push of
 * their own) that hit it over the last half second, decayed: an assault
 * rifle's killing burst of 4-7 rounds (40-70 damage) ~2.6-3.7 m/s, a pistol's
 * two (50) ~3.0, a sniper round (101) ~4.7; HUGE 1.6 times. Its lift is
 * vr_npc_burst_lift's. */
static inline float vr_npc_burst_body(float burst_damage, int force)
{
    float body;
    if (!isfinite(burst_damage) || !(burst_damage > 0.0f) || force <= VR_NPC_FORCE_CLASSIC) return 0.0f;
    /* Test66: a little more of a burst (an assault rifle's killing burst
     * ~3.0-4.6 m/s, a sniper round ~5.9) */
    body = fminf(1.4f + 0.045f * burst_damage, 6.0f);
    return force >= VR_NPC_FORCE_HUGE ? fminf(body * 1.6f, 9.0f) : body;
}
static inline float vr_npc_burst_lift(float body)
{
    return isfinite(body) && body > 0.0f ? body * 0.15f : 0.0f;
}
/* a burst's damage, decayed over VR_NPC_BURST_TICKS (half a second), with a
 * new hit's added */
enum { VR_NPC_BURST_TICKS = 15 };
static inline float vr_npc_burst_add(float previous, long elapsed_ticks, float damage)
{
    float keep;
    if (!isfinite(previous) || previous < 0.0f || elapsed_ticks < 0 || elapsed_ticks > VR_NPC_BURST_TICKS) previous = 0.0f;
    keep = elapsed_ticks >= 0 && elapsed_ticks <= VR_NPC_BURST_TICKS ?
        1.0f - (float)elapsed_ticks / (float)(VR_NPC_BURST_TICKS + 1) : 0.0f;
    if (!isfinite(damage) || damage < 0.0f) damage = 0.0f;
    return previous * keep + damage;
}
/* another hit on the same body in the same tick */
static inline void vr_npc_hit_add(struct vr_npc_hit *total, struct vr_npc_hit const *hit)
{
    total->local = fminf(total->local + hit->local, VR_NPC_HIT_LOCAL_MAXIMUM);
    total->body = fmaxf(total->body, hit->body);
    total->lift = fmaxf(total->lift, hit->lift);
}

#endif
