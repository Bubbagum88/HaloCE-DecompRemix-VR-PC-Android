"""Hand contact acquisition must use an overlap test, not a zero-length sweep.

Test40-Test51 Quest logs recorded hundreds of "VR NPC: contact grab miss ...
collision_overlaps=0" and "VR world: contact grab miss" lines with the hand
contact radius at its 8 cm maximum, against 11-16 eligible NPCs at a time:
NPC, loose-object, vehicle-lift and remote co-op grabs almost never started.
Each asked collision_model_test_pill whether the hand's sphere touched a
model, sweeping it along a zero vector. That test finds where a moving pill
first touches geometry; its edge test divides by the squared length of the
sweep and returns FALSE when the sweep is zero (its sphere test, which does
handle a pill that starts in contact, is reached only after that), so a
stationary hand touching an edge or a curved body part never counted.

collision_model_touch_sphere (source/physics/collision_models.c) replaces it:
each node's BSP sphere test (surfaces within the radius) or a point-in-solid
test (a hand pushed inside), reporting the touched node nearest the hand.
The decompiled collision_model_test_sphere, a stub that always answered
FALSE, now uses it as well.

This suite runs the engine's own pill edge test to show the zero-sweep miss,
and checks that no acquisition path sweeps a zero vector again.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "contact-acquisition-test"


def function(text, signature):
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return text[start:index + 1]
    raise AssertionError(signature)


bsp = (ROOT / "source/physics/collision_bsp.c").read_text(encoding="utf-8", errors="replace")
sphere = function(bsp[bsp.index("static boolean sphere_test_vector(", bsp.index("static boolean sphere_test_vector(") + 1):],
                  "static boolean sphere_test_vector(")
pill = function(bsp[bsp.index("static boolean pill_test_vector(", bsp.index("static boolean pill_test_vector(") + 1):],
                "static boolean pill_test_vector(")

clang = shutil.which("clang")
if clang:
    OUT.mkdir(parents=True, exist_ok=True)
    harness = OUT / "pill.c"
    harness.write_text(r'''
#include <math.h>
#include <stdio.h>
typedef float real;
typedef int boolean;
#define TRUE 1
#define FALSE 0
#define FLOOR(n,floor) ((n)<(floor)?(floor):(n))
typedef struct { real x, y, z; } real_point3d;
typedef struct { real i, j, k; } real_vector3d;
static void vector_from_points3d(real_point3d const *a, real_point3d const *b, real_vector3d *v)
{ v->i = b->x - a->x; v->j = b->y - a->y; v->k = b->z - a->z; }
static real dot_product3d(real_vector3d const *a, real_vector3d const *b) { return a->i*b->i + a->j*b->j + a->k*b->k; }
static real magnitude_squared3d(real_vector3d const *a) { return dot_product3d(a, a); }
static real square_root(real x) { return sqrtf(x); }
''' + sphere + "\n" + pill + r'''
int main(void)
{
	/* an edge 1 m long; a hand 1 cm beside its middle; an 8 cm hand sphere
	(world units: 1 m = 0.328) */
	real_point3d base = { 0, 0, 0 };
	real_vector3d edge = { 0.328f, 0, 0 };
	real_point3d hand = { 0.164f, 0.00328f, 0 };
	real_vector3d still = { 0, 0, 0 }, nudge = { 0, 0.0001f, 0 };
	real radius = 0.08f * 0.328f, t = 1, edge_t = 0;
	int stationary = pill_test_vector(&base, &edge, radius, &hand, &still, &t, &edge_t);
	int moving = pill_test_vector(&base, &edge, radius, &hand, &nudge, &t, &edge_t);
	printf("stationary=%d moving=%d\n", stationary, moving);
	return !(stationary == 0 && moving == 1);
}
''', encoding="utf-8")
    binary = OUT / "pill"
    built = subprocess.run([clang, "-O1", str(harness), "-lm", "-o", str(binary)], capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    run = subprocess.run([str(binary)], capture_output=True, text=True)
    assert run.returncode == 0, "the engine's pill edge test no longer misses a zero sweep: " + run.stdout
    print("PASS: the engine's pill test misses a stationary hand sphere touching an edge (" + run.stdout.strip() + ")")
else:
    print("SKIP: no clang for the pill test reproduction")

models = (ROOT / "source/physics/collision_models.c").read_text(encoding="utf-8")
touch = function(models, "boolean collision_model_touch_sphere(")
assert "collision_bsp_test_sphere(collision_bsp, 0, NULL, &transformed_center," in touch
assert "bsp3d_test_point(&collision_bsp->bsp3d, 0, &transformed_center) == NONE" in touch
assert "inverted_matrix.scale * radius" in touch
assert "return collision_model_touch_sphere(instance, center, radius, NULL);" in \
    function(models, "boolean collision_model_test_sphere(")
assert "boolean collision_model_touch_sphere(" in (ROOT / "source/physics/collision_models.h").read_text(encoding="utf-8")

for name in ("vr_npc_interaction.c", "vr_world_interaction.c", "vr_world_remote.c"):
    code = (ROOT / "port/linux/game" / name).read_text(encoding="utf-8")
    assert "collision_model_touch_sphere(" in code, name
    for call in re.findall(r"collision_model_test_pill\([^;]*\)", code):
        raise AssertionError(f"{name}: hand acquisition must not sweep a pill: {call}")
    assert "stationary" not in code, name
print("PASS: NPC, loose-object/vehicle and remote co-op grabs test hand-sphere overlap (surfaces or inside), "
      "never a zero-length pill sweep")
