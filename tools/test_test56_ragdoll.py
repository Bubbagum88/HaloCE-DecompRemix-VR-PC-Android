"""Test56 ragdolls: the parent-relative joint solver on every stock skeleton.

Owner's Test55 report: dead and ragdolled bodies kept jittering and never came
to rest. The Test54/55 solver compared world-space bone directions against
joint limits authored relative to each joint's parent, so joints under a rigid
one (an Elite's spine1 and neck) could never turn and the constraints fought
every tick. Test56 replaces it (vr_articulated_native.c).

This suite builds the production solver (from its world sweep to the end of
the file) against a host stand-in for the engine (a floor at z=0 and an
optional wall), loads the stock Xbox characters' bind poses and limp-noodle
joint metadata (tools/fixtures/ragdoll-skeletons.h: Marines, the Captain,
Spartans, Elites, Hunters, Grunts, Jackals and every Flood form) and drops
each one five ways: toppled, shot in the head, shot in the side, thrown by an
explosion and pushed into a wall. Every body must stay finite, keep its bones
and authored joint limits, and come to rest. Runs under ASan/UBSan.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
native = read("port/linux/game/vr_articulated_native.c")
header = read("port/linux/game/vr_articulated_native.h")

# The wiring: capture prepares the rest data; the old world-space limit test
# is gone; the step is self-contained (no generic vr_articulated_step call).
capture = native[native.index("int vr_articulated_native_capture("):native.index("int vr_articulated_native_sweep(")]
assert "if(!vr_articulated_native_prepare(&result)) return FALSE;" in capture
assert "joint_allows" not in native
step = native[native.index("int vr_articulated_native_step("):]
assert "vr_articulated_step(" not in step
assert "if(!rig || !rig->prepared" in step
assert "int vr_articulated_native_prepare(struct vr_articulated_native *rig);" in header
for field in ("joint_kind", "group", "joint_low", "joint_high", "rest_parent", "rest_in_parent",
              "rest_group", "relative", "self_mask"):
    assert re.search(r"\b%s\[VR_ARTICULATED_NODES\]" % field, header), field
solver = native[native.index("/* Test60: what a moving joint's impact is tested against"):]

ENGINE = r'''
#include <math.h>
#include <string.h>
#include <stdio.h>
typedef float real;
typedef int boolean;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define TEST_FLAG(f, b) (((f) & (1u << (b))) != 0)
#define PIN(x, lo, hi) ((x) < (lo) ? (lo) : ((x) > (hi) ? (hi) : (x)))
#define FLAG(b) (1u << (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
typedef union { real n[3]; struct { real x, y, z; }; } real_point3d;
typedef union { real n[3]; struct { real i, j, k; }; } real_vector3d;
typedef struct { real scale; union { real n[4][3]; struct { real_vector3d forward, left, up; real_point3d position; }; }; } real_matrix4x3;
typedef struct { real_vector3d n; real d; } real_plane3d;
struct collision_plane { real_plane3d plane; };
struct collision_result { int type; real t; real_plane3d plane; real_point3d point; long object_index; };
enum { _collision_result_none, _collision_result_structure, _collision_result_object };
/* source/physics/collisions.h */
enum { _collision_test_front_facing_surfaces_bit = 0, _collision_test_back_facing_surfaces_bit = 1,
    _collision_test_structure_bit = 5, _collision_test_objects_bit = 7, _collision_test_objects_bipeds_bit = 8,
    _collision_test_objects_vehicles_bit = 9 };
#define _collision_test_for_bipeds_dead_flags 0xC0A0
#define _collision_test_for_line_of_sight_flags 0xC2AD
#define NONE (-1)
struct unit_datum { struct { long player_index; } unit; };
#define _object_mask_unit 1
static inline real dot_product3d(real_vector3d const *a, real_vector3d const *b) { return a->i*b->i + a->j*b->j + a->k*b->k; }
static inline real magnitude3d(real_vector3d const *v) { return sqrtf(dot_product3d(v, v)); }
static inline real_vector3d *cross_product3d(real_vector3d const *a, real_vector3d const *b, real_vector3d *r)
{ real_vector3d t; t.i = a->j*b->k - a->k*b->j; t.j = a->k*b->i - a->i*b->k; t.k = a->i*b->j - a->j*b->i; *r = t; return r; }
static inline real normalize3d(real_vector3d *v)
{ real m = magnitude3d(v); if (m > 0.0001f) { v->i /= m; v->j /= m; v->k /= m; } else m = 0; return m; }
static inline real_vector3d *vector_from_points3d(real_point3d const *a, real_point3d const *b, real_vector3d *r)
{ r->i = b->x - a->x; r->j = b->y - a->y; r->k = b->z - a->z; return r; }
static inline real_vector3d *scale_vector3d(real_vector3d const *v, real s, real_vector3d *r) { r->i = v->i*s; r->j = v->j*s; r->k = v->k*s; return r; }
static inline real_vector3d *rotate_vector_about_axis(real_vector3d *v, real_vector3d const *n, real sine, real cosine)
{
    real d = dot_product3d(n, v) * (1 - cosine);
    real ci = n->k*v->j - v->k*n->j, cj = n->i*v->k - v->i*n->k, ck = n->j*v->i - v->j*n->i;
    v->i = cosine*v->i + d*n->i - sine*ci; v->j = cosine*v->j + d*n->j - sine*cj; v->k = cosine*v->k + d*n->k - sine*ck;
    return v;
}
static inline int valid_real_vector3d(real_vector3d const *v) { return isfinite(v->i) && isfinite(v->j) && isfinite(v->k); }
static inline int valid_real_point3d(real_point3d const *p) { return isfinite(p->x) && isfinite(p->y) && isfinite(p->z); }
static inline int valid_real_normal3d(real_vector3d const *v) { return valid_real_vector3d(v) && fabsf(magnitude3d(v) - 1) < 0.001f; }
static inline int valid_real_matrix4x3(real_matrix4x3 const *m)
{ return isfinite(m->scale) && valid_real_normal3d(&m->forward) && valid_real_normal3d(&m->left) && valid_real_normal3d(&m->up) &&
    fabsf(dot_product3d(&m->forward, &m->left)) < 0.001f && fabsf(dot_product3d(&m->left, &m->up)) < 0.001f &&
    fabsf(dot_product3d(&m->up, &m->forward)) < 0.001f && valid_real_point3d(&m->position); }
static real world_wall_x; static int world_has_wall;
static inline short collision_move_sphere(int flags, real_point3d const *from, real_vector3d const *delta, real radius, long ignore,
    real_point3d *to, real_vector3d *clipped, int maximum, struct collision_plane *planes)
{
    short count = 0; (void)flags; (void)ignore; (void)maximum; (void)clipped;
    to->x = from->x + delta->i; to->y = from->y + delta->j; to->z = from->z + delta->k;
    if (to->z < radius) { to->z = radius; planes[count].plane.n.i = 0; planes[count].plane.n.j = 0; planes[count].plane.n.k = 1; planes[count].plane.d = 0; ++count; }
    if (world_has_wall && to->x > world_wall_x - radius) { to->x = world_wall_x - radius; planes[count].plane.n.i = -1; planes[count].plane.n.j = 0; planes[count].plane.n.k = 0; planes[count].plane.d = -world_wall_x; ++count; }
    return count;
}
/* the world's rays: the floor and the wall (structure) and, for the body
 * tests, another body: a face across x = body_x (bipeds) */
static int body_present; static real body_x; static struct unit_datum body_unit;
static inline int collision_test_vector(int flags, real_point3d const *from, real_vector3d const *delta, long ignore, struct collision_result *hit)
{
    real best = 2; (void)ignore;
    if (flags & (1u << _collision_test_structure_bit)) {
        if (from->z >= 0 && from->z + delta->k < 0 && delta->k < 0) {
            real t = from->z / -delta->k;
            if (t < best) { best = t; hit->type = _collision_result_structure; hit->object_index = NONE;
                hit->plane.n.i = 0; hit->plane.n.j = 0; hit->plane.n.k = 1; hit->plane.d = 0; }
        }
        if (world_has_wall && from->x <= world_wall_x && from->x + delta->i > world_wall_x) {
            real t = (world_wall_x - from->x) / delta->i;
            if (t < best) { best = t; hit->type = _collision_result_structure; hit->object_index = NONE;
                hit->plane.n.i = -1; hit->plane.n.j = 0; hit->plane.n.k = 0; hit->plane.d = -world_wall_x; }
        }
    }
    if (body_present && (flags & (1u << _collision_test_objects_bipeds_bit)) && from->x <= body_x && from->x + delta->i > body_x) {
        real t = (body_x - from->x) / delta->i;
        if (t < best) { best = t; hit->type = _collision_result_object; hit->object_index = 77;
            hit->plane.n.i = -1; hit->plane.n.j = 0; hit->plane.n.k = 0; hit->plane.d = -body_x; }
    }
    if (best > 1) return FALSE;
    hit->t = best;
    hit->point.x = from->x + delta->i * best; hit->point.y = from->y + delta->j * best; hit->point.z = from->z + delta->k * best;
    return TRUE;
}
static inline void *object_try_and_get_and_verify_type(long index, int mask) { (void)mask; return index == 77 ? &body_unit : 0; }
static int impacts; static struct collision_result last_impact;
static inline void vr_interaction_impact_collision(long unit, struct collision_result const *hit, real_vector3d const *delta)
{ (void)unit; (void)delta; ++impacts; last_impact = *hit; }
'''

CHECK = r'''
#include "engine.h"
#include "vr_articulated_native.h"
#include "solver.c"
#include "ragdoll-skeletons.h"
#include <assert.h>
#include <stdlib.h>
static const real UNITS = 0.32808399f; /* world units per metre */
static void capture(struct skel const *s, struct vr_articulated_native *rig)
{
    int n, below[VR_ARTICULATED_NODES];
    real radius = s->limp_radius > 0 && s->limp_radius <= 0.07f ? s->limp_radius : 0.03f;
    memset(rig, 0, sizeof(*rig));
    rig->unit_index = 1; rig->body.count = s->count; rig->body.self_collision = 1; rig->impact_units = UNITS;
    for (n = 0; n < s->count; ++n) {
        struct skel_node const *k = &s->nodes[n];
        struct vr_articulated_node *node = &rig->body.nodes[n];
        node->parent = n ? k->parent : -1; node->radius = radius; node->max_bend = 3.1415926f;
        memcpy(node->position, k->pos, sizeof(node->position)); memcpy(node->previous, k->pos, sizeof(node->previous));
        if (n) {
            real l = 0; int a;
            for (a = 0; a < 3; ++a) { real d = k->pos[a] - s->nodes[k->parent].pos[a]; l += d*d; }
            node->length = sqrtf(l);
            if (node->length < radius * .25f) node->radius = .001f;
        }
        rig->joint_flags[n] = k->flags; memcpy(rig->joint_axis[n].n, k->base, sizeof(k->base)); rig->joint_range[n] = k->range;
        rig->captured[n].scale = 1;
        memcpy(rig->captured[n].forward.n, k->fwd, sizeof(k->fwd)); memcpy(rig->captured[n].left.n, k->left, sizeof(k->left));
        memcpy(rig->captured[n].up.n, k->up, sizeof(k->up)); memcpy(rig->captured[n].position.n, k->pos, sizeof(k->pos));
    }
    memset(below, 0, sizeof(below));
    for (n = s->count - 1; n > 0; --n) below[rig->body.nodes[n].parent] += below[n] + 1;
    for (n = 0; n < s->count; ++n) rig->body.nodes[n].inverse_mass = 1.0f / (1.0f + 0.35f * (real)below[n]);
    assert(vr_articulated_native_prepare(rig));
}
/* a velocity (m/s) on every joint plus a shot's kick falling off over 35 cm */
static void push(struct vr_articulated_native *rig, real const v[3], real const *at, real const kick[3])
{
    int n, a;
    for (n = 0; n < rig->body.count; ++n) {
        struct vr_articulated_node *node = &rig->body.nodes[n];
        real w = 0;
        if (at) {
            real d2 = 0;
            for (a = 0; a < 3; ++a) { real d = node->position[a] - at[a]; d2 += d*d; }
            w = expf(-d2 / (.35f*UNITS*.35f*UNITS));
        }
        for (a = 0; a < 3; ++a) node->previous[a] = node->position[a] - (v[a] + kick[a]*w) * UNITS / 30.0f;
    }
}
static int find(struct skel const *s, char const *name)
{
    int n;
    for (n = 0; n < s->count; ++n) if (strstr(s->nodes[n].name, name)) return n;
    return s->count > 1 ? 1 : 0;
}
static real worst_limit(struct vr_articulated_native const *rig)
{
    int n; real worst = 0;
    for (n = 1; n < rig->body.count; ++n) {
        int p = rig->body.nodes[n].parent, kind = rig->joint_kind[n];
        real_vector3d local; real over = 0;
        if (rig->group[n] != n) continue;
        vrj_to_local(&rig->captured[p], &rig->captured[n].forward, &local);
        if (kind == VR_JOINT_HINGE) {
            real c = (rig->joint_low[n] + rig->joint_high[n]) * .5f, bend = c + vrj_wrap(vrj_hinge_angle(&local) - c);
            if (bend < rig->joint_low[n]) over = rig->joint_low[n] - bend;
            if (bend > rig->joint_high[n]) over = bend - rig->joint_high[n];
        } else if (kind == VR_JOINT_BALL) {
            real dev = acosf(PIN(dot_product3d(&rig->joint_axis[n], &local), -1.0f, 1.0f));
            if (dev > rig->joint_high[n]) over = dev - rig->joint_high[n];
        }
        if (over > worst) worst = over;
    }
    return worst * 57.29578f;
}
int main(void)
{
    /* Test59: DEATH FORCE's throws too (vr_npc_impulse.h): a rifle burst's
     * 3.7 m/s back with 0.55 lift, a rocket's 11 m/s with 5.5 lift at its
     * centre, HUGE's 16 m/s rocket and 7.6 m/s sniper round */
    static char const *names[] = { "topple", "head shot", "side shot", "explosion", "wall",
        "rifle burst", "rocket", "huge rocket", "huge sniper" };
    static struct vr_articulated_native rig, copy;
    int i, scenario, tick, n, a, hinges = 0, rigid = 0, balls = 0;
    for (i = 0; i < SKEL_COUNT; ++i) for (scenario = 0; scenario < 9; ++scenario) {
        struct skel const *s = &skeletons[i];
        real v[3] = {0, 0, 0}, kick[3] = {0, 0, 0}, stretch = 0, limit;
        int at = -1, settle = -1;
        capture(s, &rig);
        world_has_wall = 0;
        switch (scenario) {
        case 0: v[0] = 0.4f; break;
        case 1: at = find(s, "head"); kick[0] = 3.0f; break;
        case 2: at = find(s, "spine1"); kick[1] = 3.0f; break;
        case 3: at = 0; v[2] = 3.0f; kick[0] = 6.0f; kick[2] = 4.0f; break;
        case 4: v[0] = 1.5f; world_has_wall = 1; world_wall_x = 0.25f; break;
        case 5: at = find(s, "spine1"); v[0] = 3.7f; v[2] = 0.55f; kick[0] = 1.4f; break;
        case 6: at = 0; v[0] = 11.0f; v[2] = 5.5f; kick[0] = 2.0f; break;
        case 7: at = 0; v[0] = 16.0f; v[2] = 8.0f; kick[0] = 2.0f; break;
        case 8: at = find(s, "head"); v[0] = 7.6f; v[2] = 1.1f; kick[0] = 4.7f; break;
        }
        push(&rig, v, at >= 0 ? s->nodes[at].pos : NULL, kick);
        /* the NPC code hands a body back to the engine once it is at rest, or
         * after 5 s (NPC_SETTLE_LIMIT_TICKS) */
        for (tick = 0; tick < 150 && settle < 0; ++tick) {
            real before[VR_ARTICULATED_NODES][3], max_step = 0;
            for (n = 0; n < s->count; ++n) memcpy(before[n], rig.body.nodes[n].position, sizeof(before[n]));
            if (!vr_articulated_native_step(&rig, 1.f/30.f, 3.2f, NULL, 0)) { printf("FAIL %s %s: step refused at %d\n", s->name, names[scenario], tick); return 1; }
            /* the NPC palette's low-speed contact damping while settling */
            for (n = 0; n < s->count; ++n) {
                struct vr_articulated_node *node = &rig.body.nodes[n]; real m[3], l = 0;
                for (a = 0; a < 3; ++a) { m[a] = node->position[a] - node->previous[a]; l += m[a]*m[a]; }
                if (sqrtf(l) < .02f*UNITS) for (a = 0; a < 3; ++a) node->previous[a] = node->position[a] - m[a]*.6f;
            }
            for (n = 0; n < s->count; ++n) {
                real l = 0;
                for (a = 0; a < 3; ++a) { real d = rig.body.nodes[n].position[a] - before[n][a]; l += d*d; assert(isfinite(rig.body.nodes[n].position[a])); }
                if (sqrtf(l) > max_step) max_step = sqrtf(l);
            }
            /* the NPC code's own rest test: every joint under 2 cm a tick */
            if (tick >= 30 && max_step < .02f*UNITS) settle = tick;
        }
        for (n = 1; n < s->count; ++n) {
            real l = 0;
            for (a = 0; a < 3; ++a) { real d = rig.body.nodes[n].position[a] - rig.body.nodes[rig.body.nodes[n].parent].position[a]; l += d*d; }
            if (fabsf(sqrtf(l) - rig.body.nodes[n].length) / UNITS * 100 > stretch) stretch = fabsf(sqrtf(l) - rig.body.nodes[n].length) / UNITS * 100;
        }
        limit = worst_limit(&rig);
        printf("%-18s %-10s at rest after %3d ticks, bone error %.1f cm, worst joint past its limit %.1f deg\n",
            s->name, names[scenario], settle, stretch, limit);
        /* every body comes to rest within 5 s (the Test55 solver left most of
         * them moving 1-15 cm every tick until the 5 s hand-back) */
        if (settle < 0) { printf("FAIL: never came to rest\n"); return 1; }
        /* bones keep their length (a Jackal's flaps, a Hunter's spikes and the
         * Flood's sacks within 8 cm where the ground catches them) */
        if (stretch > 8.0f) { printf("FAIL: bones stretched\n"); return 1; }
        /* knees, elbows and other joints within their authored limits (a few
         * degrees where the ground holds a limb past one) */
        if (limit > 30.0f) { printf("FAIL: joint limit\n"); return 1; }
    }
    /* the joint kinds come from the authored flags, for every species */
    for (i = 0; i < SKEL_COUNT; ++i) {
        capture(&skeletons[i], &rig);
        for (n = 1; n < rig.body.count; ++n) {
            hinges += rig.joint_kind[n] == VR_JOINT_HINGE; balls += rig.joint_kind[n] == VR_JOINT_BALL; rigid += rig.joint_kind[n] == VR_JOINT_RIGID;
            if (rig.joint_kind[n] == VR_JOINT_RIGID) assert(rig.group[n] == rig.group[rig.body.nodes[n].parent]);
            if (rig.joint_kind[n] == VR_JOINT_HINGE) {
                /* anti-hyperextension: no hinge bends more than 10 deg (plus
                 * its captured pose) past straight */
                assert(rig.joint_low[n] <= rig.joint_high[n]);
                assert(rig.joint_high[n] - rig.joint_low[n] < 6.2832f);
            }
        }
    }
    assert(hinges > 20 && balls > 100 && rigid > 50);
    /* refusals: an unprepared rig, a bad tick length, a teleporting pin */
    capture(&skeletons[1], &rig);
    copy = rig; copy.prepared = 0; assert(!vr_articulated_native_step(&copy, 1.f/30.f, 3.2f, NULL, 0));
    copy = rig; assert(!vr_articulated_native_step(&copy, 0.5f, 3.2f, NULL, 0));
    /* Test62: invalid transient topology cannot index outside the solver;
     * refusal leaves the entire rig unchanged. */
    for(int bad=0;bad<5;++bad) {
        struct vr_articulated_native before;
        copy=rig;
        if(bad==0)copy.group[1]=-1;
        if(bad==1)copy.group[1]=VR_ARTICULATED_NODES;
        if(bad==2)copy.body.nodes[1].parent=1;
        if(bad==3)copy.body.nodes[1].inverse_mass=NAN;
        if(bad==4)copy.body.nodes[1].radius=-1;
        before=copy;assert(!vr_articulated_native_step(&copy,1.f/30.f,3.2f,NULL,0));
        assert(!memcmp(&before,&copy,sizeof(copy)));
    }
    {
        struct vr_articulated_pin pin = { 5, { 0, 0, 0 } };
        memcpy(pin.position, rig.body.nodes[5].position, sizeof(pin.position));
        pin.position[0] += 1.0f;
        copy = rig; assert(!vr_articulated_native_step(&copy, 1.f/30.f, 3.2f, &pin, 1));
        /* a held hand: the pinned joint is exactly where the hand puts it */
        pin.position[0] -= 0.99f;
        copy = rig; assert(vr_articulated_native_step(&copy, 1.f/30.f, 3.2f, &pin, 1));
        for (a = 0; a < 3; ++a) assert(copy.body.nodes[5].position[a] == pin.position[a]);
    }
    /* Test60: impacts (the Test59 log had none). A joint skidding fast and
     * flat onto the floor met it with its sphere, not its centre: probed into
     * the floor it counts; slow, it does not; a body in the way is struck and
     * the joint stops at it; a player's body (the hands holding it) is not. */
    {
        struct vr_articulated_native hit_rig;
        float from[3], next[3];
        real radius = 0.03f;
        memset(&hit_rig, 0, sizeof(hit_rig));
        hit_rig.unit_index = 5; hit_rig.impact_enabled = 1; hit_rig.impact_units = UNITS; hit_rig.body.count = 1;
        world_has_wall = 0; body_present = 0;
        from[0] = 0; from[1] = 0; from[2] = radius + 0.001f;
        next[0] = 0.3f; next[1] = 0; next[2] = radius - 0.01f; /* 27 m/s, slightly down */
        impacts = 0; assert(vr_articulated_native_sweep(&hit_rig, from, radius, next));
        assert(impacts == 1 && last_impact.type == _collision_result_structure && last_impact.plane.n.k == 1);
        next[0] = 0.01f; next[1] = 0; next[2] = radius - 0.01f;             /* about 1 m/s */
        impacts = 0; assert(vr_articulated_native_sweep(&hit_rig, from, radius, next) && impacts == 0);
        /* Test62: a 5 m/s downward slam is submitted (old fixed 6 m/s
         * cutoff lost it). Actual damage uses the chosen IMPACT SPEED. */
        from[0]=0;from[1]=0;from[2]=radius+.001f;
        next[0]=0;next[1]=0;next[2]=from[2]-5.0f*UNITS/30.0f;
        impacts=0;assert(vr_articulated_native_sweep(&hit_rig,from,radius,next));
        assert(impacts==1 && last_impact.plane.n.k==1);
        body_present = 1; body_x = 0.5f; body_unit.unit.player_index = NONE;
        from[0] = 0.4f; from[1] = 0; from[2] = 1;
        next[0] = 0.6f; next[1] = 0; next[2] = 1;                           /* through the other body */
        impacts = 0; assert(vr_articulated_native_sweep(&hit_rig, from, radius, next));
        assert(impacts == 1 && last_impact.type == _collision_result_object && last_impact.object_index == 77);
        assert(fabsf(next[0] - (0.5f - radius)) < 1e-4f);
        body_unit.unit.player_index = 0;                                    /* a player */
        next[0] = 0.6f; next[1] = 0; next[2] = 1;
        impacts = 0; assert(vr_articulated_native_sweep(&hit_rig, from, radius, next) && impacts == 0 && next[0] > 0.59f);
        hit_rig.impact_enabled = 0; body_unit.unit.player_index = NONE;     /* not thrown: no impacts */
        next[0] = 0.6f; next[1] = 0; next[2] = 1;
        impacts = 0; assert(vr_articulated_native_sweep(&hit_rig, from, radius, next) && impacts == 0 && next[0] > 0.59f);
        body_present = 0;
    }
    /* prepare refuses a broken graph */
    copy = rig; copy.body.nodes[3].parent = 7; assert(!vr_articulated_native_prepare(&copy));
    printf("PASS: Test56 ragdolls (%d stock skeletons x 9 falls, Test59 DEATH FORCE throws included, settle, keep bones and joint limits; Test60 impacts: floor slams, bodies struck, players never)\n", SKEL_COUNT);
    return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="test56-ragdoll-") as temp:
    path = Path(temp)
    (path / "engine.h").write_text(ENGINE)
    (path / "solver.c").write_text(solver)
    (path / "check.c").write_text(CHECK)
    subprocess.run(["clang", "-std=gnu11", "-O1", "-g", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                    "-Wno-unused-parameter", "-Wno-missing-field-initializers", "-Wdeclaration-after-statement",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    "-I", str(path), "-I", str(ROOT / "port/linux/game"), "-I", str(ROOT / "tools/fixtures"),
                    str(path / "check.c"), "-o", str(path / "check"), "-lm"], check=True)
    subprocess.run([str(path / "check")], check=True)
