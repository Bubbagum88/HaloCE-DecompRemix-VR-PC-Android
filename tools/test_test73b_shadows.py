"""Test73b: the stencil shadows as HaloFreak95 made them again, and the VR player's body shadow.

1. The owner, on Test73's headset run: "stencil shadows is a bit fucked up ... lets just leave it as intended by
   halofreak95, reverting it to whatever he had set there in his base stencil shadows fork". Test73's 10j (the
   pass moved between the level's lightmaps and its dynamic lights, the game's stencil bit kept in bit 7) drew
   black shadows and a ground without its colour on the Quest. render.c calls stencil_shadows_render where his
   fork does (halofreak/stencil-shadows 2c055e464: after rasterizer_transparent_geometry_stop, before the screen
   fog), and the flat builds' stencil_shadows.c is Test72's token for token (his, with this port's one face a draw
   and his game.shadow_objects_stop).
2. The owner: "i do want a vr player body shadow", "(unless its somehow immersion breaking/visually broken)",
   "should also work with the games normal shadows if possible". In the headset the player's body casts both
   shadows as it is drawn there, whole (vr_render_body_shadow_matrices, vr_render.c: the observer palette, the
   head turned as the headset is, the arms reaching the hands shown), what it holds none (the game holds the gun
   elsewhere than the hands shown); the stencil volume's caps sit 12 cm along the light (the same shadow on the
   level, none on the first-person arms and gun near the body's own arms); the game's shadow map is widened to
   the hands. stencil_shadow_casters runs here in both builds (VR with and without the body's pose, the headset
   off), with negative controls.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    text = (ROOT / rel).read_text(encoding='utf-8')
    assert '\r' not in text, rel
    return text


render = read('source/render/render.c')
shadows = read('port/linux/game/stencil_shadows.c')
objects = read('source/render/render_objects.c')
vr_source = read('port/linux/game/vr_render.c')
header = read('port/linux/include/halo_vr.h')

# ---- 1. where HaloFreak95's fork draws them: once, after the transparent geometry, before the screen fog
assert render.count('stencil_shadows_render();') == 1
call = render.index('stencil_shadows_render();')
assert render.index('rasterizer_transparent_geometry_stop();') < call < render.index('structure_render_fog_screen();')
assert not (render.index('structure_render_lightmaps();') < call < render.index('lights_render_diffuse();'))
for leftover in ('STENCIL_SHADOW_GAME_BIT', 'STENCIL_SHADOW_COUNT_BITS', 'stencil_shadow_stencil_quad',
                 'D3DCOLORWRITEENABLE_RED | D3DCOLORWRITEENABLE_GREEN'):
    assert leftover not in shadows, leftover
assert shadows.count('IDirect3DDevice8_Clear(global_d3d_device, 0, NULL, D3DCLEAR_STENCIL, 0, 1.f, 0);') == 2
assert 'D3DRS_COLORWRITEENABLE, D3DCOLORWRITEENABLE_ALL);' in shadows and '#define STENCIL_SHADOW_KEEP 0.55f' in shadows


def flat_tokens(source):
    """the source as a build without HALO_VR has it: comments gone, HALO_VR blocks dropped (their #else kept)"""
    source = re.sub(r'/\*.*?\*/', ' ', source, flags=re.S)
    kept, stack = [], []
    for line in source.split('\n'):
        directive = line.strip()
        if directive.startswith('#if'):
            stack.append(('vr' if directive in ('#ifdef HALO_VR', '#if defined(HALO_VR)') else 'other',
                          directive in ('#ifdef HALO_VR', '#if defined(HALO_VR)')))
            if stack[-1][0] == 'other' and all(not skip for _, skip in stack[:-1]):
                kept.append(line)
            continue
        if directive.startswith('#else') and stack and stack[-1][0] == 'vr':
            stack[-1] = ('vr', not stack[-1][1])
            continue
        if directive.startswith('#endif') and stack:
            kind, _ = stack.pop()
            if kind == 'other' and all(not skip for _, skip in stack):
                kept.append(line)
            continue
        if all(not skip for _, skip in stack):
            kept.append(line)
    return re.findall(r'[A-Za-z_][A-Za-z_0-9]*|\d[\w.]*|\S', '\n'.join(kept))


test72 = subprocess.run(['git', '-C', str(ROOT), 'show', 'f77f6a11:port/linux/game/stencil_shadows.c'],
                        check=True, capture_output=True).stdout.decode('utf-8')
assert flat_tokens(shadows) == flat_tokens(test72), "the flat builds' stencil shadows differ from Test72's"
print('PASS: the stencil shadows where HaloFreak95 draws them (after the transparent geometry), no 10j stencil bits '
      'left, and the flat builds\' stencil_shadows.c token for token Test72\'s (his, one face a draw, objects stop)')

# ---- 2a. the stencil shadows' casters, run in both builds
casters = function(shadows, 'stencil_shadow_casters')
PROGRAM = r'''
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char boolean;
typedef float real;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
typedef struct { real x, y, z; } real_point3d;
typedef struct real_matrix4x3 real_matrix4x3;
enum { _object_type_biped, _object_type_vehicle, _object_type_weapon, _object_type_scenery };
enum { STENCIL_SHADOW_MAXIMUM_OBJECTS = 16 };
#define STENCIL_SHADOW_RANGE 30.f
struct object_datum { struct { short type; long parent_object_index, first_child_object_index, next_object_index;
    real_point3d bounding_sphere_center; real bounding_sphere_radius; } object; };
static struct object_datum objects[6];
static long drawn[6];
static short drawn_count;
static struct { struct { real_point3d position; } camera; } global_window_parameters;
static int headset, posed;
static struct object_datum *object_try_and_get(long index) { return index >= 0 && index < 6 ? &objects[index] : NULL; }
static struct object_datum *object_get(long index) { return &objects[index]; }
static short render_objects_rendered(long const **indices) { *indices = drawn; return drawn_count; }
static real distance3d(real_point3d const *a, real_point3d const *b)
{ return sqrtf((a->x - b->x) * (a->x - b->x) + (a->y - b->y) * (a->y - b->y) + (a->z - b->z) * (a->z - b->z)); }
#ifdef HALO_VR
static char palette;
static int vr_active(void) { return headset; }
static real_matrix4x3 const *vr_render_body_shadow_matrices(long index, short *count)
{ (void)count; return posed && index == 0 ? (real_matrix4x3 const *)&palette : NULL; }
#endif
#include "casters.inc"
static int expect(char const *what, long const *want, short want_count)
{
    long got[STENCIL_SHADOW_MAXIMUM_OBJECTS];
    short count = stencil_shadow_casters(got, 0), i;
    int ok = count == want_count;
    for (i = 0; ok && i < count; i++) ok = got[i] == want[i];
    if (!ok) { printf("FAIL %s: %d casters:", what, count); for (i = 0; i < count; i++) printf(" %ld", got[i]); printf("\n"); }
    return ok;
}
int main(void)
{
    /* the player's unit 0 holding weapon 1; an Elite 2 and a Warthog 3 near; a crate 4; a far Jackal 5 */
    static short const types[6] = { _object_type_biped, _object_type_weapon, _object_type_biped, _object_type_vehicle,
        _object_type_scenery, _object_type_biped };
    long i;
    int ok = 1;
    for (i = 0; i < 6; i++) {
        objects[i].object.type = types[i];
        objects[i].object.parent_object_index = i == 1 ? 0 : NONE;
        objects[i].object.first_child_object_index = i == 0 ? 1 : NONE;
        objects[i].object.next_object_index = NONE;
        objects[i].object.bounding_sphere_center.x = i == 5 ? 100.f : (real)i;
        objects[i].object.bounding_sphere_radius = 0.3f;
        drawn[drawn_count++] = i;
    }
    {
        static long const flat[] = { 0, 1, 2, 3 }, vr_posed[] = { 0, 2, 3 }, vr_unposed[] = { 2, 3 };
#ifdef HALO_VR
        headset = 1; posed = 1; ok &= expect("headset, the body posed", vr_posed, 3);
        headset = 1; posed = 0; ok &= expect("headset, no body drawn", vr_unposed, 2);
        headset = 0; posed = 1; ok &= expect("VR build, no headset", flat, 4);
#else
        (void)vr_posed; (void)vr_unposed; (void)headset; (void)posed;
        ok &= expect("flat", flat, 4);
#endif
    }
    if (ok) printf("ok\n");
    return !ok;
}
'''


def run_casters(code, vr):
    compiler = shutil.which('clang') or shutil.which('cc')
    assert compiler, 'a C compiler'
    with tempfile.TemporaryDirectory() as work:
        Path(work, 'casters.inc').write_text(code)
        Path(work, 'casters.c').write_text(PROGRAM)
        build = subprocess.run([compiler, '-std=gnu99', '-Wall', '-Werror', '-Wno-unused-function', '-I', work,
                                *(['-DHALO_VR'] if vr else []), str(Path(work, 'casters.c')), '-o',
                                str(Path(work, 'casters')), '-lm'], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        result = subprocess.run([str(Path(work, 'casters'))], capture_output=True, text=True)
        return result.returncode, result.stdout


for vr in (False, True):
    status, output = run_casters(casters, vr)
    assert status == 0, output
for fault in [('if (vr_render_body_shadow_matrices(own_unit, NULL))\n\t\t\tcasters[count++] = own_unit;',
               'casters[count++] = own_unit;'),
              ('object_try_and_get(own_unit) && vr_active())', 'object_try_and_get(own_unit))')]:
    status, output = run_casters(mutated(casters, *fault), True)
    assert status == 1 and output.startswith('FAIL'), (fault, output)
print('PASS: stencil casters run in both builds: flat, and the VR build without a headset, the player with the gun '
      'in hand (HaloFreak95\'s); in the headset the body as drawn there and no gun, nothing when no body is drawn '
      '(2 negative controls)')

# ---- 2b. the stencil volume of the headset's body: its pose, its caps off it along the light
volume = function(shadows, 'stencil_shadow_object')
assert '#define STENCIL_SHADOW_VR_BODY_NUDGE 0.04f' in shadows
assert 'nodes = vr_render_body_shadow_matrices(object_index, &posed);' in volume
assert 'if (posed != node_count)\n\t\t\treturn;' in volume
assert volume.index('nodes = vr_render_body_shadow_matrices(') < volume.index('cached = stencil_shadow_cached_get(')
assert 'if (vr_body)\n\t\t\tnudge = MAX(nudge, STENCIL_SHADOW_VR_BODY_NUDGE);' in volume

# ---- 2c. the game's own shadows: the player's body in the headset casts one, posed as drawn, its map wide enough
admit = function(objects, 'render_object')
assert '|| vr_render_body_shadow_matrices(data->object_index, NULL)' in admit
listed = function(objects, 'render_object_list')
assert 'real_matrix4x3 const *vr_shadow_body = data->shadow ?' in listed
assert '|| vr_body || legs ||\n\t\t\tvr_shadow_body)' in listed
assert 'vr_shadow_body ? (real_matrix4x3 *)vr_shadow_body :\n\t\t\t\t\t\tnetwork_vr_pose_render(' in listed
assert listed.index('FLAG(_render_model_shadow_bit)') > listed.index('vr_shadow_body ? (real_matrix4x3 *)vr_shadow_body')
assert '!vr_body && !legs && !vr_shadow_body)' in listed
assert 'real_matrix4x3 const *vr_shadow_body = NULL;' in listed  # (the flat builds: none)
begin = function(objects, 'render_object_shadow_begin')
assert 'radius = vr_render_body_shadow_radius(data->object_index, center.n, radius);' in begin
assert begin.index('vr_render_body_shadow_radius') < begin.index('rasterizer_environment_shadow_begin(')

# ---- 2d. the pose: the observer palette, made when a peer or a shadow may take it, this frame's only
publish = function(vr_source, 'vr_publish_body')
assert 'boolean published = network_vr_pose_wanted();' in publish
assert 'if (!published && !vr_body_shadows_wanted()) return;' in publish
assert 'if (published)\n        network_vr_pose_capture(unit, m, count);' in publish
assert publish.index('vr_body_arms_to_hands(unit, graph, m, count, heading);') < publish.index('vr_body_observer.unit = unit;')
getter = function(vr_source, 'vr_render_body_shadow_matrices')
assert 'if (!vr_render_full_body(object_index))' in getter
assert 'vr_body_observer.time != vr_pose_time()' in getter and 'vr_body_observer.unit != object_index' in getter
wanted = function(vr_source, 'vr_body_shadows_wanted')
assert 'config_boolean("display.stencil_shadows")' in wanted and 'return stencil || render_shadows;' in wanted
assert 'struct real_matrix4x3 const *vr_render_body_shadow_matrices(long object_index, short *count);' in header
assert 'float vr_render_body_shadow_radius(long object_index, float const center[3], float radius);' in header
print('PASS: the VR body\'s shadows: the stencil volume from its drawn pose, caps 12 cm along the light; the game\'s '
      'shadow cast by it (posed as drawn, nothing it holds, its map wide to the hands); the observer palette made '
      'when a peer or a shadow takes it, this frame\'s only')
