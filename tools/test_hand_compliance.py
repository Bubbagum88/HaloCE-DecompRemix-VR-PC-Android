"""Guard fixed-length arm reach and test held-object finger routing."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "port/linux/game/vr_render.c").read_text()

# The candidate deliberately removes v1.0.18's bone-length stretch/compression
# workaround after the supplied video showed visible arm deformation. The wrist
# clamps to authored reach; do not reintroduce the later subtree fade/scale.
assert '"vr_hand_compliance_math.h"' not in source
assert '#include "vr_arm_ik_math.h"' in source
assert "vr_limit_hand_compliance" not in source
assert "vr_hand_compliance_node_visibility" not in source
assert "matrices[node].scale*=node_visibility" not in source
assert "travel = MIN(travel, 0.08f * vr_units_per_metre());" in source
arm_solver = source[source.index("static void vr_solve_arm("):source.index("static ", source.index("static void vr_solve_arm(") + 20)]
assert "vr_arm_ik_reach_bounds(" in arm_solver
assert "vr_arm_ik_clamp_distance(distance, minimum, maximum)" in arm_solver
assert "upper_length *= " not in arm_solver and "fore_length *= " not in arm_solver
assert "vr_solve_arm(graph, matrices, chain, shoulder, &target, &pole, !free_hand" in source
assert "vr_hand_contact_feedback(controller, unit, graph," in source

# NPC grabbing must never replace the controller-space render target with the
# lagging articulated NPC contact node. The NPC query may still report an
# interaction-owned hand into its separate output, but the player arm follows
# the tracked hand target below.
render_hand = source[source.index("boolean npc_grip = !world_grip"):
                     source.index("if (tracking == 1)", source.index("boolean npc_grip = !world_grip"))]
assert "vr_npc_interaction_hand(controller, npc_contact.n)" in render_hand
assert "target.x = hand.x - f.i * 0.075f * units;" in render_hand
assert "target.y = hand.y - f.j * 0.075f * units;" in render_hand
assert "target.z = hand.z - f.k * 0.075f * units;" in render_hand
assert "vr_npc_interaction_hand(controller, hand.n)" not in render_hand

query_start = source.index("static boolean vr_finger_trace(")
query_brace = source.index("{", query_start)
query_end = query_brace + 1
depth = 1
while depth:
    depth += (source[query_end] == "{") - (source[query_end] == "}")
    query_end += 1
query = source[query_start:query_end]

code = r'''
#include <assert.h>
#include <math.h>
#include <string.h>
typedef float real;
typedef int boolean;
typedef struct { float n[3]; } real_point3d, real_vector3d;
struct collision_result { float t; long object_index; };
struct collision_plane { float t; };
struct collision_model_instance { long object_index; };
struct collision_model_test_pill_result { struct { float t; } bsp_result; };
#define TRUE 1
#define FALSE 0
#define PIN(x,lo,hi) ((x)<(lo)?(lo):(x)>(hi)?(hi):(x))
static int vr_finger_volume_hand=-1, vr_finger_reload_only, vr_finger_owned_valid;
static struct collision_model_instance vr_finger_owned_model={77};
static struct { int usable,features; float finger_radius; } vr_finger_volume[2];
static struct { int queries,ray_fallbacks; } vr_contact_stats;
static int generic_calls,owned_calls,reload_calls,overlap,owned_hit=1;
static float vr_units_per_metre(void) { return 1; }
static int vr_manual_reload_trace(float const*a,float const*b,float radius,struct collision_result*out) {
    (void)a;(void)b;assert(radius==.004f);reload_calls++;out->t=.4f;return 1;
}
static int collision_model_test_point(struct collision_model_instance const*i,real_point3d const*p) {
    (void)p;assert(i->object_index==77);owned_calls++;return overlap;
}
static int collision_model_test_pill(struct collision_model_instance const*i,real_point3d const*p,
    real_vector3d const*v,float r,struct collision_model_test_pill_result*out) {
    (void)p;(void)v;assert(i->object_index==77&&r==.004f);owned_calls++;out->bsp_result.t=.3f;return owned_hit;
}
static int vr_touch_trace(real_point3d const*a,real_vector3d const*b,long ignore,struct collision_result*out) {
    (void)a;(void)b;(void)ignore;(void)out;generic_calls++;return 0;
}
static int collision_features_test_point(int const*a,real_point3d const*b,struct collision_plane*c) {
    (void)a;(void)b;(void)c;generic_calls++;return 0;
}
static int collision_features_test_vector(int const*a,real_point3d const*b,real_vector3d const*c,struct collision_plane*d) {
    (void)a;(void)b;(void)c;(void)d;generic_calls++;return 0;
}
static int vr_weapon_trace(real_point3d const*a,real_vector3d const*b,float r,struct collision_result*c) {
    (void)a;(void)b;(void)c;(void)r;generic_calls++;return 0;
}
'''+query+r'''
int main(void) {
    real_point3d point={{0}};
    real_vector3d vector={{1,0,0}};
    struct collision_result hit;
    vr_finger_reload_only=1;
    assert(vr_finger_trace(&point,&vector,-1,&hit)&&hit.t==.4f);
    assert(reload_calls==1&&!generic_calls&&!owned_calls);
    vr_finger_reload_only=0;vr_finger_owned_valid=1;
    assert(vr_finger_trace(&point,&vector,-1,&hit)&&hit.t==.3f&&hit.object_index==77);
    assert(owned_calls==2&&!generic_calls);
    overlap=1;
    assert(vr_finger_trace(&point,&vector,-1,&hit)&&hit.t==0&&owned_calls==3);
    overlap=0;owned_hit=0;
    assert(!vr_finger_trace(&point,&vector,-1,&hit)&&!generic_calls);
    vr_finger_owned_valid=0;
    assert(!vr_finger_trace(&point,&vector,-1,&hit)&&generic_calls==1);
    return 0;
}
'''

with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp) / "hand.c"
    exe = Path(tmp) / "hand"
    c.write_text(code)
    subprocess.run(
        ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
         "-I", str(ROOT), str(c), "-lm", "-o", str(exe)], check=True
    )
    subprocess.run([str(exe)], check=True)

print("hand contact: authored arm lengths and bounded wrist reach; no post-solve subtree scaling; held-collider finger routing passed")
