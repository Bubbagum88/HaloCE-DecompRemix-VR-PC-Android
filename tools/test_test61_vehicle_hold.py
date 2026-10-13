"""Test61: the immersive vehicle controls stay under the hands.

Owner's Test60 session (2026-10-12 07:58 log, 08:03 video): driving the
Warthog in first person with HORIZON LEVEL, the hands kept coming off the
wheel. The wheel was placed on the vehicle's body, which pitched and rolled
under the hands (tracked in a level frame), so a roll read as steering and the
grip slid; its own place (96 to 99 cm from the eyes) sat on the old 1 m limit,
so it jumped between there and the chest; and the eyes the hands are placed
from eased after the driver's head marker, which leans with the steering
animation. This suite compiles the production placement (vr_vehicle_handles.h
vr_wheel_place) and pins the steady seat (vr_render.c).
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
handles = read("port/linux/game/vr_vehicle_handles.h")
render = read("port/linux/game/vr_render.c")

# the seat's eyes held still while the controls are up, only then
assert "static int vr_vehicle_handles_steady(void);" in render
assert "else if (now > steady.time && !vr_vehicle_handles_steady())" in render
assert 'config_boolean("vr.vehicle_handles")' in handles[handles.index("static int vr_vehicle_handles_enabled"):]
steady = handles[handles.index("static int vr_vehicle_handles_steady(void)\n{"):]
steady = steady[:steady.index("\n}\n")]
assert "vr_wheel.valid" in steady and "vr_vehicle_handles_enabled(vr_wheel.unit)" in steady
# the place measured once, from the eyes
assert "vr_wheel_hand_frame(&nodes[0],&head,&hands);" in handles
assert "vr_wheel.local[0]=dot_product3d(&delta,&hands.forward);" in handles
assert "#define VR_FAR_REACH 1.5f" in handles

struct = handles[handles.index("static struct {\n    long unit, vehicle;"):handles.index("} vr_wheel;") + len("} vr_wheel;")]
point = handles[handles.index("static real_point3d vr_wheel_point("):handles.index("/* Test56: the controls placed on the vehicle where it is drawn.")]
place = handles[handles.index("/* Test59: in front of the chest"):handles.index("/* the player's offsets, size and switches")]

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;
typedef union { struct { real x, y, z; }; real n[3]; } real_point3d;
typedef union { struct { real i, j, k; }; real n[3]; } real_vector3d;
typedef struct { real scale; real_vector3d forward, left, up; real_point3d position; } real_matrix4x3;
#define PIN(x, lo, hi) ((x) < (lo) ? (lo) : (x) > (hi) ? (hi) : (x))
#define VR_STICK_LENGTH 0.16f
#include "vr_vehicle_controls_math.h"
static struct { real_point3d game_camera_position; struct { int driver; real offset; } seat; } vr_render;
static float heading_yaw;
/* Test65: COCKPIT LOCK (off for the level-frame checks below) and the
 * cockpit's frame as the vehicle is drawn (vr_frame.c vr_cockpit_frame) */
static int cockpit_lock, cockpit_on;
static real_matrix4x3 cockpit_frame;
static int config_boolean(char const *k) { return !strcmp(k, "vr.vehicle_cockpit_lock") && cockpit_lock; }
static int vr_cockpit_frame(float f[3], float l[3], float u[3])
{
    if (!cockpit_on) return 0;
    for (int i = 0; i < 3; i++) { f[i] = cockpit_frame.forward.n[i]; l[i] = cockpit_frame.left.n[i]; u[i] = cockpit_frame.up.n[i]; }
    return 1;
}
static int vr_heading_forward(float f[3]) { f[0] = cosf(heading_yaw); f[1] = sinf(heading_yaw); f[2] = 0; return 1; }
static real vr_units_per_metre(void) { return 1.0f; }
static int valid_real_point3d(real_point3d const *p) { return isfinite(p->x) && isfinite(p->y) && isfinite(p->z); }
static real dot_product3d(real_vector3d const *a, real_vector3d const *b) { return a->i * b->i + a->j * b->j + a->k * b->k; }
static real magnitude3d(real_vector3d const *v) { return sqrtf(dot_product3d(v, v)); }
static real normalize3d(real_vector3d *v) { real m = magnitude3d(v); if (m > 0) { v->i /= m; v->j /= m; v->k /= m; } return m; }
static void cross_product3d(real_vector3d const *a, real_vector3d const *b, real_vector3d *c)
{ real_vector3d r = {{ a->j * b->k - a->k * b->j, a->k * b->i - a->i * b->k, a->i * b->j - a->j * b->i }}; *c = r; }
static void vector_from_points3d(real_point3d const *a, real_point3d const *b, real_vector3d *v)
{ for (int i = 0; i < 3; i++) v->n[i] = b->n[i] - a->n[i]; }
''' + struct + "\n" + point + "\n" + place + r'''
/* the vehicle's body: heading 0.4 rad, pitched and rolled */
static real_matrix4x3 body(real pitch, real roll)
{
    real_matrix4x3 m; real y = 0.4f;
    real_vector3d f = {{ cosf(y) * cosf(pitch), sinf(y) * cosf(pitch), sinf(pitch) }};
    real_vector3d l0 = {{ -sinf(y), cosf(y), 0 }}, u0;
    cross_product3d(&f, &l0, &u0); normalize3d(&u0);
    m.scale = 1; m.forward = f;
    for (int i = 0; i < 3; i++) { m.left.n[i] = l0.n[i] * cosf(roll) + u0.n[i] * sinf(roll); m.up.n[i] = u0.n[i] * cosf(roll) - l0.n[i] * sinf(roll); }
    m.position.x = 10; m.position.y = 20; m.position.z = 1;
    return m;
}
/* where a still hand sits on the wheel (its turn as the update reads it) */
static real read_turn(real_point3d hand)
{
    real_vector3d d; vector_from_points3d(&vr_wheel.center, &hand, &d);
    return atan2f(dot_product3d(&d, &vr_wheel.plane_up), dot_product3d(&d, &vr_wheel.plane_left));
}
static real gap(void)
{ real_vector3d d; vector_from_points3d(&vr_render.game_camera_position, &vr_wheel.center, &d); return magnitude3d(&d); }
int main(void)
{
    real_matrix4x3 level = body(0, 0);
    real_point3d hand;
    vr_render.game_camera_position.x = 10.2f; vr_render.game_camera_position.y = 20.1f; vr_render.game_camera_position.z = 1.8f;
    heading_yaw = 0.4f;
    /* the Warthog: its wheel 97 cm from the eyes, ahead and below, leaning back */
    vr_wheel.kind = 0; vr_wheel.wheel_front = 1; vr_wheel.comfort = 1; vr_wheel.scale = 1; vr_wheel.radius = 0.17f;
    vr_wheel.local[0] = 0.80f; vr_wheel.local[1] = 0.0f; vr_wheel.local[2] = -0.55f;
    vr_wheel.axis[0] = -0.98f; vr_wheel.axis[1] = 0; vr_wheel.axis[2] = 0.17f;
    vr_wheel_place(&level);
    /* not thrown to the chest (Test60's metre), brought in to COMFORT REACH */
    assert(!vr_wheel.far && fabsf(gap() - 0.55f) < 0.002f);
    real_point3d center = vr_wheel.center; real_vector3d normal = vr_wheel.normal;
    hand = vr_wheel.target[0];
    real held = read_turn(hand);
    /* pitched 12 degrees and rolled 20 under the still hand: the wheel stays
     * put and the hand reads the same turn (Test60 read the roll as steering) */
    for (int t = 0; t < 40; t++) {
        real_matrix4x3 rough = body(0.21f * sinf(t * 0.7f), 0.35f * sinf(t * 1.3f));
        vr_wheel_place(&rough);
        for (int i = 0; i < 3; i++) {
            assert(fabsf(vr_wheel.center.n[i] - center.n[i]) < 1e-4f);
            assert(fabsf(vr_wheel.normal.n[i] - normal.n[i]) < 1e-4f);
        }
        assert(fabsf(read_turn(hand) - held) < 1e-4f && !vr_wheel.far);
    }
    /* the wheel turns with the seat's heading, as the hands do */
    heading_yaw = 1.0f;
    vr_wheel_place(&level);
    assert(fabsf(gap() - 0.55f) < 0.002f && fabsf(vr_wheel.root.forward.i - cosf(1.0f)) < 1e-5f && vr_wheel.root.up.k == 1.0f);
    heading_yaw = 0.4f;
    /* COMFORT REACH off: on its own place, 97 cm (the drawn wheel 2.5 cm nearer) */
    vr_wheel.comfort = 0;
    vr_wheel_place(&level);
    assert(!vr_wheel.far && gap() > 0.93f && gap() < 0.98f);
    /* a marker gone wrong (1.6 m): in front of the chest, and logged */
    vr_wheel.local[0] = 1.5f; vr_wheel.local[2] = -0.6f;
    vr_wheel_place(&level);
    assert(vr_wheel.far && fabsf(gap() - sqrtf(0.35f * 0.35f + 0.40f * 0.40f)) < 0.002f);
    /* the drive stick (from the eyes, in front of the chest) is as before */
    vr_wheel.kind = 2; vr_wheel.head_anchored = 1; vr_wheel.far = 0;
    vr_wheel_place(&level);
    assert(!vr_wheel.far && fabsf(gap() - sqrtf(0.35f * 0.35f + 0.40f * 0.40f)) < 0.002f);
    /* Test65: COCKPIT LOCK. The hands turn with the cockpit as drawn
     * (vr_frame.c); the Warthog's wheel is placed in the same frame, so seen
     * from the eyes in that frame it never moves while the Warthog pitches,
     * rolls and turns (the owner's Test64 drive: "the wheel and camera isnt
     * stable and snaps") */
    vr_wheel.kind = 0; vr_wheel.head_anchored = 0; vr_wheel.far = 0; vr_wheel.comfort = 1;
    vr_wheel.local[0] = 0.80f; vr_wheel.local[1] = 0.0f; vr_wheel.local[2] = -0.55f;
    cockpit_on = 1;
    {
        real first[3] = { 0, 0, 0 };
        for (int t = 0; t < 12; t++) {
            real_matrix4x3 rough = body(0.21f * sinf(t * 0.7f), 0.35f * sinf(t * 1.3f));
            real_vector3d d; real seen[3];
            cockpit_frame = rough;
            vr_wheel_place(&rough);
            vector_from_points3d(&vr_render.game_camera_position, &vr_wheel.center, &d);
            seen[0] = dot_product3d(&d, &rough.forward); seen[1] = dot_product3d(&d, &rough.left); seen[2] = dot_product3d(&d, &rough.up);
            if (!t) for (int i = 0; i < 3; i++) first[i] = seen[i];
            for (int i = 0; i < 3; i++) assert(fabsf(seen[i] - first[i]) < 1e-4f);
            assert(fabsf(gap() - 0.55f) < 0.002f && !vr_wheel.far);
            assert(fabsf(vr_wheel.root.up.k - rough.up.k) < 1e-5f);
        }
    }
    cockpit_on = 0;
    /* boarding with the lock on (before it is up): measured in the vehicle's
     * own frame, the one the lock eases to */
    cockpit_lock = 1; vr_render.seat.driver = 1; vr_wheel.valid = 0;
    {
        real_matrix4x3 rough = body(0.15f, -0.2f), frame;
        vr_wheel_hand_frame(&rough, &vr_render.game_camera_position, &frame);
        for (int i = 0; i < 3; i++) {
            assert(fabsf(frame.up.n[i] - rough.up.n[i]) < 1e-4f && fabsf(frame.forward.n[i] - rough.forward.n[i]) < 1e-4f);
        }
        vr_wheel.valid = 1;
        vr_wheel_hand_frame(&rough, &vr_render.game_camera_position, &frame);
        assert(frame.up.k == 1.0f); /* placed, not yet locked: the level frame */
    }
    cockpit_lock = 0; vr_render.seat.driver = 0; vr_wheel.valid = 0;
    puts("PASS: Test61 vehicle hold: the controls placed in the hands' level frame from the seat's eyes; pitch and roll move neither them nor the turn a still hand reads; the Warthog's wheel kept at COMFORT REACH, never thrown to the chest; a marker past 1.5 m in front of the chest; Test65 COCKPIT LOCK: the wheel rides the cockpit frame, measured on boarding in the vehicle's own");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test61-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function", "-Wno-unused-parameter",
                    "-Wno-missing-field-initializers", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    "-I", str(ROOT / "port/linux/game"), str(path / "check.c"), "-o", str(path / "check"), "-lm"], check=True)
    subprocess.run([str(path / "check")], check=True)
print("PASS: Test61 wiring (seat eyes held still while the immersive controls are up, only then; place measured once from the eyes)")
