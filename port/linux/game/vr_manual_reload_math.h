#ifndef VR_MANUAL_RELOAD_MATH_H
#define VR_MANUAL_RELOAD_MATH_H

/* Pure transaction state. Ammo belongs to the engine and is never stored here. */
enum { VR_MR_IDLE, VR_MR_OLD_HELD, VR_MR_NEED_MAG, VR_MR_NEW_HELD,
    VR_MR_NEED_CHAMBER, VR_MR_CHAMBER_HELD, VR_MR_SEATING };
enum { VR_MR_NONE, VR_MR_BEGIN, VR_MR_DISCARD, VR_MR_PICKUP,
    VR_MR_INSERT, VR_MR_CHARGE, VR_MR_COMMIT, VR_MR_CANCEL };
struct vr_mr_state { int phase, down, pulled; };
struct vr_mr_input {
    int valid, held, near_mag, near_pouch, near_chamber, magazine_out,
        chamber_pulled, can_load, explicit_reload, loose_round, seated, no_chamber;
};
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
    if (!i->valid || i->explicit_reload) {
        int active = s->phase != VR_MR_IDLE;
        s->phase = VR_MR_IDLE; s->pulled = 0;
        return active ? VR_MR_CANCEL : VR_MR_NONE;
    }
    switch (s->phase) {
    case VR_MR_IDLE:
        if (press && i->near_pouch && i->can_load && i->loose_round) {
            s->phase = VR_MR_NEW_HELD; return VR_MR_PICKUP;
        }
        if (press && i->near_mag && i->can_load && !i->loose_round) {
            s->phase = VR_MR_OLD_HELD; s->pulled = 0; return VR_MR_BEGIN;
        }
        break;
    case VR_MR_OLD_HELD:
        if (i->magazine_out) s->pulled = 1;
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
        if (release) {
            s->phase = i->near_mag ? VR_MR_SEATING : VR_MR_NEED_MAG;
            return i->near_mag ? VR_MR_INSERT : VR_MR_DISCARD;
        }
        break;
    case VR_MR_SEATING:
        if (i->seated) {
            s->phase = i->no_chamber ? VR_MR_IDLE : VR_MR_NEED_CHAMBER;
            if(i->no_chamber)return VR_MR_COMMIT;
        }
        break;
    case VR_MR_NEED_CHAMBER:
        if (press && i->near_chamber) {
            s->phase = VR_MR_CHAMBER_HELD; s->pulled = 0; return VR_MR_CHARGE;
        }
        break;
    case VR_MR_CHAMBER_HELD:
        if (i->chamber_pulled) s->pulled = 1;
        if (release) {
            s->phase = s->pulled ? VR_MR_IDLE : VR_MR_NEED_CHAMBER;
            return s->pulled ? VR_MR_COMMIT : VR_MR_NONE;
        }
        break;
    }
    return VR_MR_NONE;
}
#endif
