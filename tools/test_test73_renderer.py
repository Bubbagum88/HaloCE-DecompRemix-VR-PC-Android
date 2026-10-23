"""Test73: the renderer's parity with OpenCE build 244 (item 7). This port's d3d8_gl.c had kept its own copy through the
232-244 merges, and lacked these upstream commits, ported 2026-10-20 (each checked then on flat Windows against the
baseline, b30's frames identical):

- 197c19947: desktop vertex streams bound once per stream (glVertexAttribFormat/glBindVertexBuffer), framebuffers
  moved to the front of their list, floorf without its call (scaled_pixel), a checkpoint of the constants written,
  four recent pixel shaders, buffer uploads in 4 KB pieces. Not taken: its recent render target cache (it would hand
  out targets render_targets_evict frees);
- b449c43e2: the vertex constants' serials 64-bit (this port's guest is 32-bit and VR draws each eye: they wrapped);
- a3277d94d: a deleted texture forgotten by the binding shadows (xgpu_gl_texture_deleted, from render targets and
  the menus' art too), a framebuffer's shadow forgotten with it, a clear forgetting only the state it changed;
- 1068da0c3: shader keys and uniform inputs compared a word at a time (words_equal);
- f876a526d: a water mip composite rebuilt only when one of its levels' targets was written;
- ef6ea26fd: desktop texture units bound in one call (glBindTextures);
- bf4d5d8fa: one sampler object per sampler state (a cache of them);
- c40d7b22f: the HUD ammo meter's discrete thresholds read with texelFetch (its art and atlas were here already).

Pinned in the source, and the helpers whose results must not change compiled and compared with what they replace:
scaled_pixel with floorf, words_equal with memcmp, xgpu_gl_texture_deleted with a binding table.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_renderer'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?(?:inline )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


def run(name, source):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (name + '.c')
    path.write_text(source, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-O2', '-Wall', '-Werror', '-fsanitize=address,undefined', str(path), '-lm',
                    '-o', str(OUT / name)], check=True)
    result = subprocess.run([str(OUT / name)], check=True, capture_output=True, text=True)
    print(result.stdout.strip())


gl = read('port/linux/src/d3d8_gl.c')
menus = read('port/linux/src/menu_files.c')
xgpu = read('port/linux/src/xgpu.h')
psh = read('port/linux/src/nv2a_psh.c')

# 197c19947
assert 'glVertexAttribFormat(index, size, type, normalized, (GLuint)relative_offset);' in gl
assert re.search(r'glBindVertexBuffer\(binding, buffer, \(GLintptr\)buffer_offset, stride\);', gl)
assert '#define BUFFER_UPLOAD_PIECE 4096' in gl
assert '#define RECENT_FRAGMENT_COUNT 4' in gl
assert 'constants_checkpoint_serial' in gl
assert 'floorf' not in fn(gl, 'scaled_pixel')
assert 'return scaled_pixel(coordinate, target_scale[axis]);' in fn(gl, 'target_pixel')
# b449c43e2
assert 'static unsigned long long constant_serials[XGPU_VERTEX_CONSTANT_COUNT];' in gl
assert 'static unsigned long long constants_serial;' in gl
# a3277d94d
assert 'void xgpu_gl_texture_deleted(unsigned int texture);' in xgpu
assert 'xgpu_gl_texture_deleted(entry->target.texture);' in gl
for function in ('halo_menus_art_register', 'halo_menus_art_forget'):
    body = fn(menus, function)
    assert re.search(r'xgpu_gl_texture_deleted\(art\[index\]\.texture\);\s*glDeleteTextures\(1, &art\[index\]\.texture\);',
                     body), function + ': the texture is forgotten before it is deleted'
clear = fn(gl, 'D3DDevice_Clear')
assert clear.count('clear_state_forget();') >= 1 and 'memset(&gl_state, 0xff' not in clear
assert 'framebuffer_forget_texture(entry->target.texture);' in gl
# 1068da0c3
assert 'words_equal(&recent[index]->key, key, sizeof(*key))' in gl
assert 'words_equal(&entry->key, key, sizeof(*key))' in gl
assert '!words_equal(inputs, draw_uniform_inputs, sizeof(inputs))' in gl
# f876a526d
assert re.search(r'unsigned long level_written\[MIP_COMPOSITE_LEVELS\];', gl)
# ef6ea26fd
assert 'glBindTextures((GLuint)first, (GLsizei)(last - first + 1), &gl_textures[first]);' in gl
# bf4d5d8fa
assert re.search(r'\} sampler_cache\[SAMPLER_CACHE_SIZE\];', gl) and 'sampler_parameters(GLuint sampler, const DWORD *inputs)' in gl
# c40d7b22f
assert 'float threshold = texelFetch(tex0, pixel, 0).r;' in psh and '(OpenCE c40d7b22f)' in psh
print('PASS: the renderer ports pinned: 197c19947, b449c43e2, a3277d94d, 1068da0c3, f876a526d, ef6ea26fd, bf4d5d8fa, '
      'c40d7b22f')

run('scaled_pixel', r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
typedef int GLint;
''' + fn(gl, 'scaled_pixel') + r'''
int main(void)
{
	static const float scales[] = { 1.0f, 0.5f, 1.25f, 1.5f, 2.0f, 2.25f, 3.0f, 0.3333333f, 4.0f };
	long count = 0;
	int scale_index, step;

	srand(73);
	for (scale_index = 0; scale_index < (int)(sizeof(scales) / sizeof(scales[0])); scale_index++)
	{
		/* (every quarter pixel from -2048 to 4096, where the halves fall, and random places) */
		for (step = -8192; step <= 16384; step++)
		{
			float coordinate = (float)step * 0.25f;
			float value = coordinate * scales[scale_index] + 0.5f;

			if (scaled_pixel(coordinate, scales[scale_index]) != (GLint)floorf(value))
			{
				printf("FAIL: scaled_pixel(%g, %g) = %d, floorf gives %d\n", coordinate, scales[scale_index],
					scaled_pixel(coordinate, scales[scale_index]), (GLint)floorf(value));
				return 1;
			}
			count++;
		}
		for (step = 0; step < 200000; step++)
		{
			float coordinate = ((float)rand() / (float)RAND_MAX - 0.3f) * 9000.0f;
			float value = coordinate * scales[scale_index] + 0.5f;

			if (scaled_pixel(coordinate, scales[scale_index]) != (GLint)floorf(value))
			{
				printf("FAIL: scaled_pixel(%.9g, %g)\n", coordinate, scales[scale_index]);
				return 1;
			}
			count++;
		}
	}
	printf("PASS: scaled_pixel equals floorf(coordinate * scale + 0.5) on %ld cases, negatives and halves included "
		"(OpenCE 197c19947)\n", count);
	return 0;
}
''')

run('words_equal', r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int BOOL;
typedef unsigned int DWORD;
''' + fn(gl, 'words_equal') + r'''
int main(void)
{
	static DWORD a[128], b[128];
	long trial, equal = 0;

	srand(73);
	for (trial = 0; trial < 400000; trial++)
	{
		unsigned long size = 4 * (unsigned long)(1 + rand() % 128);
		unsigned long index;

		for (index = 0; index < 128; index++)
			a[index] = b[index] = (DWORD)rand() * 2654435761u;
		if (rand() % 2)
		{
			/* (one bit of one byte different, anywhere in the compared part) */
			unsigned long byte = (unsigned long)rand() % size;

			((unsigned char *)b)[byte] ^= (unsigned char)(1u << (rand() % 8));
		}
		if (words_equal(a, b, size) != !memcmp(a, b, size))
		{
			printf("FAIL: words_equal and memcmp disagree on %lu bytes\n", size);
			return 1;
		}
		equal += words_equal(a, b, size);
	}
	if (!equal || equal == 400000) { puts("FAIL: the cases do not cover both outcomes"); return 1; }
	printf("PASS: words_equal agrees with memcmp on 400000 keys of 4 to 512 bytes (OpenCE 1068da0c3)\n");
	return 0;
}
''')

state = re.search(r'static struct\s*\{[\s\S]*?\} gl_state;', gl)
assert state, 'gl_state'
assert re.search(r'GLuint textures\[D3DTSS_MAXSTAGES\]\[3\];', state.group(0)), 'the texture binding shadows'
run('texture_deleted', r'''
#include <stdio.h>
#include <string.h>
#define D3DTSS_MAXSTAGES 4
typedef unsigned int GLuint;
static struct { GLuint textures[D3DTSS_MAXSTAGES][3]; } gl_state;
''' + fn(gl, 'xgpu_gl_texture_deleted') + r'''
int main(void)
{
	int unit, slot;

	for (unit = 0; unit < D3DTSS_MAXSTAGES; unit++)
		for (slot = 0; slot < 3; slot++)
			gl_state.textures[unit][slot] = (GLuint)(10 + (unit * 3 + slot) % 5);
	xgpu_gl_texture_deleted(12);
	for (unit = 0; unit < D3DTSS_MAXSTAGES; unit++)
		for (slot = 0; slot < 3; slot++)
		{
			GLuint was = (GLuint)(10 + (unit * 3 + slot) % 5);

			if (gl_state.textures[unit][slot] != (was == 12 ? (GLuint)-1 : was))
			{
				puts("FAIL: a deleted texture is still bound in the shadows, or another was forgotten");
				return 1;
			}
		}
	puts("PASS: a deleted texture is forgotten in every unit and slot that had it, and only it (OpenCE a3277d94d)");
	return 0;
}
''')
# halo-ce-universal b1f28fd8d / b4282ad85: a texture's menu art looked up again only when the art registered changes
textures = read('port/linux/src/xbox_textures.c')
assert re.search(r'static unsigned long art_serial = 1;', menus)
for function in ('halo_menus_art_register', 'halo_menus_art_forget'):
    assert 'art_serial++;' in fn(menus, function), function + ' changes the art without saying so'
assert 'return art_serial;' in fn(menus, 'menu_art_serial')
assert re.search(r'if \(entry->menu_serial != menu_art_serial\(\)\)\s*\{\s*entry->menu_serial = menu_art_serial\(\);\s*'
                 r'entry->menu_levels = 0;\s*entry->menu_texture = menu_art_texture\(entry->data, &entry->menu_levels\);',
                 textures)
assert textures.count('menu_art_texture(') == 1, 'every menu art lookup goes through the serial'

# halo-ce-universal 8e23d89d7 + 1b75787d2: shadows' and dynamic lights' draws rasterized only inside the screen's
# rectangle of the box they can change; universal's GL renderer never narrowed it (its halo_draw_scissor is a no-op
# there), so the GL side is this port's: the rectangle intersected with the viewport's scissor, an empty one drawing
# nothing; debug.gpu_draw_scissor false to compare
config = read('port/linux/src/port_config.c')
assert re.search(r'\{ "debug\.gpu_draw_scissor", _config_boolean, "true",', config)
raster = fn(gl, 'apply_raster_state')
assert re.search(r'if \(draw_scissor\.on\)\s*\{\s*GLint x0 = target_pixel\(draw_scissor\.x0, 0\), y0 = target_pixel\(draw_scissor\.y0, 1\);',
                 raster), 'the draw rectangle in the bound target\'s pixels'
assert 'scissor[2] = x1 > x0 ? x1 - x0 : 0;' in raster and 'scissor[3] = y1 > y0 ? y1 - y0 : 0;' in raster
assert 'GL_SCISSOR_TEST, draw_scissor.on || (scissor[2] > 0 && scissor[3] > 0)' in raster, 'an empty rectangle draws nothing'
assert 'enabled = config_boolean("debug.gpu_draw_scissor");' in fn(gl, 'halo_draw_scissor')
environment = read('source/rasterizer/xbox/rasterizer_xbox_environment.c')
shadows = read('source/rasterizer/xbox/rasterizer_xbox_shadows.c')
for name, text, opened in (('the diffuse lights', fn(environment, '_rasterizer_environment_diffuse_light_draw'), 1),
                           ('the specular lights', fn(environment, '_rasterizer_environment_specular_light_draw'), 1),
                           ('the shadows', fn(shadows, '_rasterizer_environment_shadow_draw'), 1)):
    assert text.count('rasterizer_port_scissor_points(NULL, 0);') == opened, name + ': the rectangle is let go after its draw'
assert 'if (specular_light_vertex_shader_permutation_index == 0)\n\t\t\t\trasterizer_environment_port_light_scissor();' in environment
rasterizer = read('source/rasterizer/xbox/rasterizer_xbox.c')
run('scissor_points', r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#define TRUE 1
#define FALSE 0
#define MIN(a, b) ((a) > (b) ? (b) : (a))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define PIN(v, a, b) ((v) < (a) ? (a) : ((v) > (b) ? (b) : (v)))
typedef int boolean;
typedef float real;
typedef struct { real x, y, z; } real_point3d;
typedef struct { real i, j, k; } real_vector3d;
typedef struct { real scale; real_vector3d forward, left, up; real_point3d position; } real_matrix4x3;
struct render_frustum { real_matrix4x3 world_to_view; boolean projection_valid; real projection_matrix[4][4]; };
struct render_camera { struct { short x0, y0, x1, y1; } viewport_bounds; };
static struct { struct render_camera camera; struct render_frustum frustum; } global_window_parameters;
static struct { int on; real x0, y0, x1, y1; } drawn;
static void halo_draw_scissor(unsigned char on, float x0, float y0, float x1, float y1)
{
	drawn.on = on; drawn.x0 = x0; drawn.y0 = y0; drawn.x1 = x1; drawn.y1 = y1;
}
''' + fn(read('source/math/matrix_math.c'), 'matrix4x3_transform_point') +
    re.search(r'#define RASTERIZER_PORT_SCISSOR_NEAR 0\.01f\n', rasterizer).group(0) +
    fn(rasterizer, 'rasterizer_port_scissor_add') + fn(rasterizer, 'rasterizer_port_scissor_points') + r'''
static real random_real(real low, real high) { return low + (high - low) * (real)rand() / (real)RAND_MAX; }
static void random_axes(real_vector3d *a, real_vector3d *b, real_vector3d *c)
{
	/* (an orthonormal frame from a random rotation: Gram-Schmidt of random vectors) */
	real_vector3d u = { random_real(-1, 1), random_real(-1, 1), random_real(-1, 1) };
	real_vector3d v = { random_real(-1, 1), random_real(-1, 1), random_real(-1, 1) };
	real length = sqrtf(u.i * u.i + u.j * u.j + u.k * u.k), dot;

	u.i /= length; u.j /= length; u.k /= length;
	dot = u.i * v.i + u.j * v.j + u.k * v.k;
	v.i -= dot * u.i; v.j -= dot * u.j; v.k -= dot * u.k;
	length = sqrtf(v.i * v.i + v.j * v.j + v.k * v.k);
	v.i /= length; v.j /= length; v.k /= length;
	*a = u; *b = v;
	c->i = u.j * v.k - u.k * v.j; c->j = u.k * v.i - u.i * v.k; c->k = u.i * v.j - u.j * v.i;
}
int main(void)
{
	long cases, samples = 0, empty = 0, partly_behind = 0;

	srand(73);
	for (cases = 0; cases < 20000; cases++)
	{
		struct render_frustum *frustum = &global_window_parameters.frustum;
		struct render_camera *camera = &global_window_parameters.camera;
		real_point3d corners[8], center = { random_real(-12, 12), random_real(-12, 12), random_real(-12, 12) };
		real_vector3d axes[3];
		real half[3] = { random_real(0.05f, 6), random_real(0.05f, 6), random_real(0.05f, 6) };
		int corner, sample, behind = 0, in_front = 0;

		random_axes(&frustum->world_to_view.forward, &frustum->world_to_view.left, &frustum->world_to_view.up);
		frustum->world_to_view.scale = 1.0f;
		frustum->world_to_view.position.x = random_real(-2, 2);
		frustum->world_to_view.position.y = random_real(-2, 2);
		frustum->world_to_view.position.z = random_real(-2, 2);
		frustum->projection_valid = TRUE;
		/* (an eye's asymmetric frustum, as render_camera_build_frustum makes it) */
		frustum->projection_matrix[0][0] = random_real(0.7f, 2.0f);
		frustum->projection_matrix[1][1] = random_real(0.7f, 2.0f);
		frustum->projection_matrix[2][0] = random_real(-0.3f, 0.3f);
		frustum->projection_matrix[2][1] = random_real(-0.3f, 0.3f);
		camera->viewport_bounds.x0 = 0; camera->viewport_bounds.y0 = 0;
		camera->viewport_bounds.x1 = (short)(cases % 2 ? 640 : 1440); camera->viewport_bounds.y1 = (short)(cases % 2 ? 480 : 1584);
		random_axes(&axes[0], &axes[1], &axes[2]);
		for (corner = 0; corner < 8; corner++)
		{
			real s0 = (corner & 1) ? half[0] : -half[0], s1 = (corner & 2) ? half[1] : -half[1];
			real s2 = (corner & 4) ? half[2] : -half[2];

			corners[corner].x = center.x + axes[0].i * s0 + axes[1].i * s1 + axes[2].i * s2;
			corners[corner].y = center.y + axes[0].j * s0 + axes[1].j * s1 + axes[2].j * s2;
			corners[corner].z = center.z + axes[0].k * s0 + axes[1].k * s1 + axes[2].k * s2;
		}
		rasterizer_port_scissor_points(corners, 8);
		if (!drawn.on) { puts("FAIL: a box with a valid projection was not given a rectangle"); return 1; }
		for (sample = 0; sample < 300; sample++)
		{
			real s0 = random_real(-1, 1) * half[0], s1 = random_real(-1, 1) * half[1], s2 = random_real(-1, 1) * half[2];
			real_point3d point = { center.x + axes[0].i * s0 + axes[1].i * s1 + axes[2].i * s2,
				center.y + axes[0].j * s0 + axes[1].j * s1 + axes[2].j * s2,
				center.z + axes[0].k * s0 + axes[1].k * s1 + axes[2].k * s2 }, view;
			real x, y, width, height;

			matrix4x3_transform_point(&frustum->world_to_view, &point, &view);
			if (view.z > -RASTERIZER_PORT_SCISSOR_NEAR) { behind = 1; continue; }
			in_front = 1;
			x = (frustum->projection_matrix[0][0] * view.x + frustum->projection_matrix[2][0] * view.z) / -view.z;
			y = -(frustum->projection_matrix[1][1] * view.y + frustum->projection_matrix[2][1] * view.z) / -view.z;
			if (x < -1 || x > 1 || y < -1 || y > 1)
				continue;
			width = camera->viewport_bounds.x1 - camera->viewport_bounds.x0;
			height = camera->viewport_bounds.y1 - camera->viewport_bounds.y0;
			x = (x + 1) * 0.5f * width; y = (y + 1) * 0.5f * height;
			samples++;
			if (x < drawn.x0 - 1e-2f || x > drawn.x1 + 1e-2f || y < drawn.y0 - 1e-2f || y > drawn.y1 + 1e-2f)
			{
				printf("FAIL: case %ld: a point of the box on the screen at (%.2f, %.2f) is outside its rectangle "
					"(%.2f, %.2f)-(%.2f, %.2f)\n", cases, x, y, drawn.x0, drawn.y0, drawn.x1, drawn.y1);
				return 1;
			}
		}
		partly_behind += behind && in_front;
		if (drawn.x1 <= drawn.x0 && drawn.y1 <= drawn.y0)
			empty++;
	}
	rasterizer_port_scissor_points(NULL, 0);
	if (drawn.on) { puts("FAIL: count 0 did not give the whole viewport back"); return 1; }
	global_window_parameters.frustum.projection_valid = FALSE;
	{
		real_point3d corners[8] = { { 0 } };

		rasterizer_port_scissor_points(corners, 8);
		if (drawn.on) { puts("FAIL: a frustum with no projection was narrowed"); return 1; }
	}
	if (!empty || !partly_behind) { puts("FAIL: the cases do not cover boxes behind and across the camera"); return 1; }
	printf("PASS: a box's rectangle on the screen holds every point of it in front of the camera (%ld points of "
		"20000 boxes, %ld across the camera, %ld wholly behind it: empty) (halo-ce-universal 8e23d89d7, 1b75787d2)\n",
		samples, partly_behind, empty);
	return 0;
}
''')
print('PASS: Test73 renderer parity')
