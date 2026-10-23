"""Test73, item 10 (the owner's 10-18 Quest log, Test70, a Scorpion drive): what it showed, and what was done.

1. "EXCEPTION assert in cache_files.c,#298", "00000000 is not a tag index: an empty tag is used", then "attempt to
   play a sound that was not a mono 22k ... sound" (three times): a sound played with tag index 0, which is a tag
   (the map's scenario, its first: tag_get gave the empty tag). A dead body woken by a moving vehicle
   (ragdoll_update's vehicle pass) was made a ragdoll without ragdoll_thud_prepare, its thud sound left 0 by
   ragdoll_allocate's memset; its first landing played it. Now every ragdoll starts with NONE, and the woken body
   prepares its thud as the others (a body fall). Compiled here: ragdoll_allocate's own setting-up lines and
   ragdoll_thud_update on a landing body: the body fall plays, never tag 0.
2. "too many dynamic vertices requested from rasterizer" / "build_sprite failed to allocate dynamic vertices":
   each particle system particle draws through build_sprites_begin(..., 2, ...), a buffer and 8 unlit vertices
   for its state and again for its transition; their pool was raised from 512 to 4096 (halo_port_capacity.h)
   while the buffer table stayed 1024 and the unlit vertices 4 per particle. Both now count them; the overflow says
   which limit it met. Pinned, with the 16-bit index reasoning (a draw's indices start at its own first vertex).
3. "seat eyes held in place; the head marker strayed 110 cm" every two seconds for minutes: the Scorpion's driver
   climbs in for longer than the controls' three seconds of settling; the eyes were held mid-climb. A stray that
   lasts three seconds is now taken (test_test22 runs it: the 110 cm case retaken, Test66's 1.5 s dip still not).
4. "a script tried to delete the player (or the horse he rode in on, or his six-shooter)" x2, then a revert: the
   stock engine refusing a level script's object_destroy of the vehicle the player rode (hs_object_destroy's own
   guard, as on the Xbox); the revert was the player's, from the pause menu (a pointer click logged just before).
   No change: pinned that the guard is the stock one.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_log_fixes'
ragdoll = (ROOT / 'port/linux/game/ragdoll.c').read_text(encoding='utf-8')
rasterizer = (ROOT / 'source/rasterizer/rasterizer.h').read_text(encoding='utf-8')
primitives = (ROOT / 'source/rasterizer/xbox/rasterizer_xbox_draw_primitives.c').read_text(encoding='utf-8')
capacity = (ROOT / 'port/linux/include/halo_port_capacity.h').read_text(encoding='utf-8')
particles = (ROOT / 'source/effects/particle_systems.c').read_text(encoding='utf-8')
sprites = (ROOT / 'source/render/render_sprite.c').read_text(encoding='utf-8')
gl = (ROOT / 'port/linux/src/d3d8_gl.c').read_text(encoding='utf-8')
script = (ROOT / 'source/hs/hs_library_external.c').read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


# ---------- 1. the thud sound
allocate = fn(ragdoll, 'ragdoll_allocate')
setup = allocate[allocate.index('\tcsmemset(&ragdolls[free_index], 0, sizeof(ragdolls[free_index]));'):
                 allocate.index('\treturn &ragdolls[free_index];')]
assert 'ragdolls[free_index].thud_sound = NONE;' in setup
assert setup.index('csmemset') < setup.index('thud_sound = NONE')
wake = ragdoll[ragdoll.index('struct ragdoll *ragdoll = ragdoll_allocate(iterator.index);'):]
wake = wake[:wake.index('break;')]
assert 'ragdoll_thud_prepare(ragdoll, iterator.index, FALSE);' in wake
# every place a ragdoll is made prepares its thud (and each starts as NONE besides)
calls = [m.start() for m in re.finditer(r'= ragdoll_allocate\(', ragdoll)]
assert len(calls) == 4, len(calls)
for at in calls:
    assert 'ragdoll_thud_prepare(ragdoll, ' in ragdoll[at:at + 700], ragdoll[at:at + 200]
fields = ragdoll[ragdoll.index('\tlong thud_sound;\n'):ragdoll.index('\treal_vector3d last_velocity;\n') + len('\treal_vector3d last_velocity;\n')]

HARNESS = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;
typedef int boolean;
typedef unsigned char byte;
#define TRUE 1
#define FALSE 0
#define NONE (-1L)
#define PIN(x,l,h) ((x)<(l)?(l):((x)>(h)?(h):(x)))
#define csmemset memset
typedef union { struct { real i, j, k; }; real n[3]; } real_vector3d;
typedef union { struct { real x, y, z; }; real n[3]; } real_point3d;
struct ragdoll { long object_index, start_time, last_update_time;
%s};
static struct ragdoll ragdolls[4];
static struct { real gravity_scale; } ragdoll_parameters = { 1.0f };
static real global_gravity = 0.0035f;
static long tick;
static long game_time_get(void) { return tick; }
static real ragdoll_length(real_vector3d const *v) { return sqrtf(v->i * v->i + v->j * v->j + v->k * v->k); }
static void ragdoll_sub(real_point3d const *a, real_point3d const *b, real_vector3d *out)
{ out->i = a->x - b->x; out->j = a->y - b->y; out->k = a->z - b->z; }
static int valid_real_vector3d(real_vector3d const *v) { return isfinite(v->i) && isfinite(v->j) && isfinite(v->k); }
static long ragdoll_body_fall_sound(long biped) { (void)biped; return 0x12345678; }
static real_point3d const *global_origin3d; static real_vector3d const *global_forward3d;
static long played[8]; static int plays;
static void object_impulse_sound_new(long object, long sound, short node, real_point3d const *p, real_vector3d const *f,
	real scale) { (void)object; (void)node; (void)p; (void)f; (void)scale; played[plays++] = sound; }
static struct ragdoll *allocated(long object_index, short free_index)
{
	/* (ragdoll_allocate's own setting up of the slot it gives) */
	ragdolls[free_index].thud_sound = 0x7777; /* (what the slot held before) */
%s	return &ragdolls[free_index];
}
%s
int main(void)
{
	struct ragdoll *r = allocated(42, 1);
	real_vector3d falling = {{ 0, 0, -0.2f }}, landed = {{ 0, 0, 0 }};

	assert(r->thud_sound == NONE && r->object_index == 42);
	/* falling, then the ground stops it: its thud is the body fall, never tag 0 */
	tick = 100; ragdoll_thud_update(r, 42, &falling);
	tick = 101; ragdoll_thud_update(r, 42, &landed);
	assert(plays == 1 && played[0] == 0x12345678);
	printf("a woken body's first landing: the body fall sound, not tag 0\n");
	return 0;
}
''' % (fields, setup.replace('ragdolls[free_index]', 'ragdolls[free_index]'), fn(ragdoll, 'ragdoll_thud_update'))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'thud.c').write_text(HARNESS, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-function', '-Wno-unused-variable',
                '-fsanitize=address,undefined', '-fno-sanitize-recover=all', str(OUT / 'thud.c'), '-lm', '-o',
                str(OUT / 'thud')], check=True)
print(subprocess.run([str(OUT / 'thud')], check=True, capture_output=True, text=True).stdout.strip())

# ---------- 2. the dynamic vertices
particles_max = int(re.search(r'#define HALO_PORT_MAXIMUM_PARTICLES (\d+)', capacity)[1])
system_max = int(re.search(r'#define HALO_PORT_MAXIMUM_SYSTEM_PARTICLES (\d+)', capacity)[1])
assert 'RASTERIZER_MAXIMUM_DYNAMIC_UNLIT_VERTICES = 4 * HALO_PORT_MAXIMUM_PARTICLES + 8 * HALO_PORT_MAXIMUM_SYSTEM_PARTICLES,' in rasterizer
assert 'RASTERIZER_MAXIMUM_DYNAMIC_VERTEX_BUFFERS = 1024 + 2 * HALO_PORT_MAXIMUM_SYSTEM_PARTICLES,' in rasterizer
unlit, buffers = 4 * particles_max + 8 * system_max, 1024 + 2 * system_max
assert (unlit, buffers) == (65536, 9216), (unlit, buffers)
# (why 8 and 2: a system particle's state and transition draws, two sprites' worth each)
assert particles.count('build_sprites_begin(\n\t\t\t\t\t\t\t&sprite_data,\n\t\t\t\t\t\t\t2,') == 2
assert 'NUMBER_OF_VERTICES_PER_QUADRILATERAL*data->maximum_sprite_count);' in sprites
# (a sprite draw's indices start at its first vertex: the stream starts there, so the larger pool needs no 32-bit index)
draw = fn(gl, 'D3DDevice_DrawVertices')
assert 'setup_streams(start_vertex, vertex_count);' in draw and 'GL_UNSIGNED_SHORT' in draw
# (the buffer table's entries are longs everywhere, no short indices)
assert not re.search(r'short\s+\w*vertex_buffer_index', primitives + sprites)
new = fn(primitives, '_rasterizer_dynamic_vertices_new')
assert '"dynamic vertices of type %d: %ld of %ld in use, %ld more asked; %ld of %d buffers in use",' in new
assert new.index('### ERROR too many dynamic vertices requested from rasterizer') < new.index('dynamic vertices of type %d')

# ---------- 4. the script's delete: the stock guard
guard = fn(script, 'hs_object_destroy')
assert 'if (!object_is_or_contains_player(object_index))' in guard and 'the horse he rode in on' in guard

print('PASS: Test73 10-18 log: woken bodies thud with a body fall, never tag 0; the dynamic vertex pools count the '
      'particle system particles (%d unlit vertices, %d buffers); the seat eyes retaken after a lasting stray '
      '(test_test22); the script delete was the stock guard' % (unlit, buffers))
