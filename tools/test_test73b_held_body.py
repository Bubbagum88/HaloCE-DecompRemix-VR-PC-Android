"""Test73b: a corpse held as a shield stays drawn (a tester: "the body point of origin doesn't come with you, so they
become invisible").

The engine draws, lights, shoots and finds an object by its bounding sphere, which object_compute_node_matrices takes
from the native pose (a corpse's lies at its root), before vr_npc_interaction_palette gives the node matrices the
pose in the hands. The hands' spring holds the root where the grab found it (as if the body were rigid), so a body
hanging from the hands was a metre and more from its sphere (the owner's Quest log, Test73: "its root brought to the
body in the hands (1.1 m behind)", Test66's catch-up past a metre) and was culled while in view. A held corpse's
bounds are now about the pose drawn, as OpenCE's ragdolls' are about theirs (ragdoll.c, the same rule: the
skeleton's middle, its reach and a quarter unit more, at least the definition's radius, the place in the map taken
again), every tick it is held; a middle outside the map leaves them as they were.

Run here: npc_bounds_about_pose (production) against a stand-in world, with negative controls; the palette's wiring.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]
npc = (ROOT / 'port/linux/game/vr_npc_interaction.c').read_text(encoding='utf-8')
ragdoll = (ROOT / 'port/linux/game/ragdoll.c').read_text(encoding='utf-8')
assert '\r' not in npc

# ---------- the wiring: after the pose in the hands is written, held corpses only, every tick they are held
palette = function(npc, 'vr_npc_interaction_palette')
# (the palette's own last write, not the settling hand-backs', which are indented further)
written = '\n    for(n=0;n<npc.rig.body.count;++n) native[n]=npc.rig.captured[n];\n'
call = ('    if(npc.started&&(npc.held[0]||npc.held[1])&&TEST_FLAG(u->object.damage_flags,_object_dead_bit))\n'
        '        npc_bounds_about_pose(index,u,native,npc.rig.body.count);\n')
assert palette.count(written) == 1 and call in palette
assert palette.index(written) < palette.index(call)
assert palette.index('its root brought to the body in the hands') < palette.index(call)  # (Test66's catch-up kept)
assert '#include "scenario/scenario.h"' in npc
# (OpenCE's ragdolls' rule, which this follows)
assert 'ragdoll_length(&half) + 0.25f);' in ragdoll and 'definition->object.bounding_radius,' in ragdoll
assert 'biped->object.bounding_sphere_center = center;' in ragdoll and 'object_reconnect_to_map(biped_index, NULL);' in ragdoll

BOUNDS = function(npc, 'npc_bounds_about_pose')
PROGRAM = r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef float real;
typedef union { struct { real x, y, z; }; real n[3]; } real_point3d;
typedef union { struct { real i, j, k; }; real n[3]; } real_vector3d;
typedef struct { real scale; real_vector3d forward, left, up; real_point3d position; } real_matrix4x3;
struct location { long cluster_index; short leaf_index; };
struct unit_datum { long definition_index; struct { short type; real_point3d bounding_sphere_center; real bounding_sphere_radius; } object; };
struct biped_definition { struct { real bounding_radius; } object; };
#define NONE (-1)
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
static int checks, connected = 1, disconnects, reconnects, cache_updates;
static long reconnected_cluster;
#define CHECK(c, what) do { checks++; if (!(c)) { printf("FAIL: %s\n", what); exit(1); } } while (0)
static struct biped_definition elite = { { 0.35f } };
static struct biped_definition *biped_definition_get(long index) { CHECK(index == 7, "its own definition"); return &elite; }
static int valid_real_point3d(real_point3d const *p) { return isfinite(p->x) && isfinite(p->y) && isfinite(p->z); }
static real magnitude3d(real_vector3d const *v) { return sqrtf(v->i * v->i + v->j * v->j + v->k * v->k); }
/* (the map: a box; outside it, no cluster) */
static void scenario_location_from_point(struct location *location, real_point3d const *p)
{
    location->leaf_index = 0;
    location->cluster_index = fabsf(p->x) < 50 && fabsf(p->y) < 50 && fabsf(p->z) < 50 ? 3 : NONE;
}
static void object_disconnect_from_map(long index) { CHECK(index == 42 && connected, "disconnected once, connected"); connected = 0; disconnects++; }
static void object_reconnect_to_map(long index, struct location const *location)
{
    CHECK(index == 42 && !connected && location && location->cluster_index != NONE, "reconnected where it is");
    connected = 1; reconnects++; reconnected_cluster = location->cluster_index;
}
void object_bounds_cache_update(long object_index, short type, real_point3d const *center, real radius)
{
    (void)center; (void)radius;
    CHECK(object_index == 42 && type == 0, "the packed copy too"); cache_updates++;
}
#include "bounds.inc"
static real_matrix4x3 pose[3];
static void place(int n, real x, real y, real z) { pose[n].position.x = x; pose[n].position.y = y; pose[n].position.z = z; }
int main(void)
{
    struct unit_datum u = { 7, { 0, { { 0.f, 0.f, 0.f } }, 0.35f } };
    /* the native sphere at the root (0,0,0); the body hanging from the hands a metre and a half off (0.5 units) */
    place(0, 0.5f, 0.0f, 0.3f); place(1, 0.5f, 0.0f, 0.5f); place(2, 0.6f, 0.1f, 0.1f);
    npc_bounds_about_pose(42, &u, pose, 3);
    CHECK(fabsf(u.object.bounding_sphere_center.x - 0.55f) < 1e-5f && fabsf(u.object.bounding_sphere_center.y - 0.05f) < 1e-5f &&
        fabsf(u.object.bounding_sphere_center.z - 0.3f) < 1e-5f, "the sphere about the pose drawn");
    CHECK(fabsf(u.object.bounding_sphere_radius - (sqrtf(0.05f * 0.05f + 0.05f * 0.05f + 0.2f * 0.2f) + 0.25f)) < 1e-5f,
        "its reach and a quarter unit");
    CHECK(disconnects == 1 && reconnects == 1 && cache_updates == 1 && reconnected_cluster == 3, "its place taken again");
    /* a curled body: never smaller than its definition's radius */
    place(0, 1.0f, 1.0f, 1.0f); place(1, 1.0f, 1.0f, 1.0f); place(2, 1.0f, 1.0f, 1.0f);
    npc_bounds_about_pose(42, &u, pose, 3);
    CHECK(u.object.bounding_sphere_radius == 0.35f, "at least the definition's radius");
    /* its middle outside the map: as it was */
    {
        real_point3d before = u.object.bounding_sphere_center;
        int was = reconnects;
        place(0, 90.f, 0.f, 0.f); place(1, 90.f, 0.f, 0.f); place(2, 90.f, 0.f, 0.f);
        npc_bounds_about_pose(42, &u, pose, 3);
        CHECK(reconnects == was && !memcmp(&before, &u.object.bounding_sphere_center, sizeof(before)), "outside: unchanged");
        place(0, NAN, 0.f, 0.f);
        npc_bounds_about_pose(42, &u, pose, 3);
        CHECK(reconnects == was, "an invalid pose: unchanged");
        npc_bounds_about_pose(42, &u, pose, 0);
        CHECK(reconnects == was && connected, "no nodes: nothing");
    }
    printf("ok %d\n", checks);
    return 0;
}
'''


def run(bounds):
    compiler = shutil.which('clang') or shutil.which('cc')
    assert compiler, 'a C compiler'
    with tempfile.TemporaryDirectory(prefix='test73b-held-body-') as work:
        Path(work, 'bounds.inc').write_text(bounds)
        Path(work, 'held.c').write_text(PROGRAM)
        built = subprocess.run([compiler, '-std=gnu11', '-Wall', '-Werror', '-Wno-unused-function', '-I', work,
                                str(Path(work, 'held.c')), '-lm', '-o', str(Path(work, 'held'))],
                               capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        result = subprocess.run([str(Path(work, 'held'))], capture_output=True, text=True)
        return result.returncode, result.stdout


status, output = run(BOUNDS)
assert status == 0 and output.startswith('ok'), output
for code, what in [(mutated(BOUNDS, 'u->object.bounding_sphere_center=center;', ''), 'the sphere left at the root'),
                   (mutated(BOUNDS, 'magnitude3d(&half)+.25f', 'magnitude3d(&half)'), 'the reach without its margin'),
                   (mutated(BOUNDS, '    if(location.cluster_index==NONE) return;\n', ''), 'moved outside the map')]:
    status, output = run(code)
    assert status == 1 and output.startswith('FAIL'), (what, output)
print('PASS: a corpse in the hands is drawn, lit, shot and found where it is held (its bounds about the pose drawn, '
      'as OpenCE\'s ragdolls\'; its place in the map taken again; outside the map, left as it was), every tick it is '
      'held (3 negative controls)')
