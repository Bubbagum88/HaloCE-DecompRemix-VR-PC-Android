#ifndef VR_MANUAL_RELOAD_MATH_H
#define VR_MANUAL_RELOAD_MATH_H

#include <string.h>

/* Pure transaction state. Ammo belongs to the engine and is never stored here. */
enum { VR_MR_IDLE, VR_MR_OLD_HELD, VR_MR_NEED_MAG, VR_MR_NEW_HELD,
    VR_MR_NEED_CHAMBER, VR_MR_CHAMBER_HELD, VR_MR_SEATING };
/* Test54: VR_MR_SEATED (the magazine locked; charging still needed),
 * VR_MR_RACKED (the slide/handle reached the end of its travel) and
 * VR_MR_PULLED (the old magazine came free of the well) are feedback-only
 * events: they carry no ammo and exist so each step has its own haptic. */
enum { VR_MR_NONE, VR_MR_BEGIN, VR_MR_DISCARD, VR_MR_PICKUP,
    VR_MR_INSERT, VR_MR_CHARGE, VR_MR_COMMIT, VR_MR_CANCEL, VR_MR_EJECT,
    VR_MR_SEATED, VR_MR_RACKED, VR_MR_PULLED };
struct vr_mr_state { int phase, down, pulled, chambered; };
/* eject_pressed: the Reload button's rising edge. With manual reload on it
 * physically drops the magazine from IDLE and is otherwise ignored: it never
 * cancels an open transaction and never starts the native automatic reload.
 * chambered: a round stayed in the chamber when the transaction began (a
 * tactical reload), so the new magazine needs no charging. */
struct vr_mr_input {
    int valid, held, near_mag, near_pouch, near_chamber, magazine_out,
        chamber_pulled, can_load, explicit_reload, eject_pressed, loose_round, seated, no_chamber,
        chambered;
};
/* Grip is the compatibility default. Unknown/missing config values fail back
 * to grip so a typo cannot leave manual reload without an input. */
static int vr_mr_input_uses_trigger(char const *source)
{
    return source && strcmp(source, "trigger") == 0;
}
static int vr_mr_suppress_native_reload(int manual_enabled, int local_session,
    int profiled_weapon)
{
    return manual_enabled && local_session && profiled_weapon;
}
static int vr_mr_button_pressed(int was_down, int is_down)
{
    return is_down && !was_down;
}
/* The remapped VR action is sampled at render rate; the native weapon bit is
 * sampled at game-tick rate. Accept either held level so a short press cannot
 * disappear between the two input consumers. */
static int vr_mr_reload_button_down(int mapped_action_down, int native_reload_bit)
{
    return mapped_action_down || native_reload_bit;
}
/* A held reload button must not bypass the fire lock while an ejected-mag
 * transaction is waiting for a replacement or is being completed. */
static unsigned vr_mr_output_flags(int suppress_native, int valid, int phase, int event,
    unsigned suppress_flag, unsigned block_fire_flag, unsigned commit_flag)
{
    if (!valid) return suppress_native ? suppress_flag : 0;
    return suppress_flag |
        (phase != VR_MR_IDLE ? block_fire_flag : 0) |
        (event == VR_MR_COMMIT ? commit_flag : 0);
}
/* Analog trigger hysteresis prevents vibration/noise at the activation point
 * from repeatedly starting and cancelling a reload. Invalid analog values
 * fail closed. */
static int vr_mr_trigger_held(int was_held, float value)
{
    if (!(value >= 0.0f && value <= 1.0f)) return 0;
    return value > (was_held ? 0.55f : 0.75f);
}
static float vr_mr_pull_distance(float start_x, float current_x)
{
    return start_x-current_x;
}
/* Bounds are rechecked after a transient reload-state reset, but diagnostic
 * output should identify a profile once rather than repeat on every frame. */
static int vr_mr_profile_changed(int had_previous, long previous_weapon,
    long previous_model, long weapon, long model)
{
    return !had_previous || previous_weapon != weapon || previous_model != model;
}
static float vr_mr_pouch_side(int free_hand){return free_hand==1?-1.0f:1.0f;}
static int vr_mr_pouch_enabled(int hip,int shoulder,int near_hip,int near_shoulder)
{return (hip&&near_hip)||(shoulder&&near_shoulder);}
static int vr_mr_step(struct vr_mr_state *s, struct vr_mr_input const *i)
{
    int press = i->held && !s->down, release = !i->held && s->down;
    s->down = i->held;
    if (!i->valid) {
        int active = s->phase != VR_MR_IDLE;
        s->phase = VR_MR_IDLE; s->pulled = 0; s->chambered = 0;
        return active ? VR_MR_CANCEL : VR_MR_NONE;
    }
    switch (s->phase) {
    case VR_MR_IDLE:
        /* Test54: the Reload button drops the magazine wherever the free hand
         * is; the replacement comes from a body pouch. It is a magazine
         * release only: a gun with no reserve keeps its magazine. */
        if (i->eject_pressed && i->can_load && !i->loose_round) {
            s->phase = VR_MR_NEED_MAG; s->pulled = 0; s->chambered = i->chambered;
            return VR_MR_EJECT;
        }
        if (press && i->near_pouch && i->can_load && i->loose_round) {
            s->phase = VR_MR_NEW_HELD; s->chambered = i->chambered; return VR_MR_PICKUP;
        }
        if (press && i->near_mag && i->can_load && !i->loose_round) {
            s->phase = VR_MR_OLD_HELD; s->pulled = 0; s->chambered = i->chambered;
            return VR_MR_BEGIN;
        }
        break;
    case VR_MR_OLD_HELD:
        if (i->magazine_out && !s->pulled) { s->pulled = 1; if (i->held) return VR_MR_PULLED; }
        if (release) {
            s->phase = s->pulled ? VR_MR_NEED_MAG : VR_MR_IDLE;
            return s->pulled ? VR_MR_DISCARD : VR_MR_CANCEL;
        }
        break;
    case VR_MR_NEED_MAG:
        if (press && i->near_pouch && i->can_load) {
            s->phase = VR_MR_NEW_HELD; return VR_MR_PICKUP;
        }
        break;
    case VR_MR_NEW_HELD:
        /* Seated by pushing it home: aligned contact with the well inserts
         * while the grip is still held, as a real magazine locks before the
         * hand lets go. Releasing at the well inserts too; elsewhere drops. */
        if (i->near_mag && (i->held || release)) {
            s->phase = VR_MR_SEATING; return VR_MR_INSERT;
        }
        if (release) { s->phase = VR_MR_NEED_MAG; return VR_MR_DISCARD; }
        break;
    case VR_MR_SEATING:
        if (i->seated) {
            if (i->no_chamber || s->chambered) {
                s->phase = VR_MR_IDLE; s->chambered = 0; return VR_MR_COMMIT;
            }
            s->phase = VR_MR_NEED_CHAMBER; return VR_MR_SEATED;
        }
        break;
    case VR_MR_NEED_CHAMBER:
        if (press && i->near_chamber) {
            s->phase = VR_MR_CHAMBER_HELD; s->pulled = 0; return VR_MR_CHARGE;
        }
        break;
    case VR_MR_CHAMBER_HELD:
        if (i->chamber_pulled && !s->pulled) { s->pulled = 1; if (i->held) return VR_MR_RACKED; }
        if (release) {
            s->phase = s->pulled ? VR_MR_IDLE : VR_MR_NEED_CHAMBER;
            if (s->pulled) s->chambered = 0;
            return s->pulled ? VR_MR_COMMIT : VR_MR_NONE;
        }
        break;
    }
    return VR_MR_NONE;
}
#endif
