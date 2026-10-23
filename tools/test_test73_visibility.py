"""Test73: the desktop visibility tests (port/linux/src/d3d8_gl.c, GulchCE's fix: OpenCE 711aa46d0 + aecdd895d).

The production functions (the batches' queries, their initialisation, the tests' begin/end/result, and each frame's
batch sent before the swap and read after it, OpenCE a0f22cbba) are extracted from d3d8_gl.c and run on Mesa's desktop
OpenGL 4.5 (llvmpipe, a surfaceless EGL
context), once with the mapped query buffer behind a fence (every driver but AMD's own) and once with each query read on
the CPU (AMD's: GL_VENDOR "ATI Technologies Inc." stood in for). Each test draws a rectangle of a known number of
pixels. Checked: slot 0 is a test's own (this port mapped it to 1 before); counts arrive as frames are presented, in
order, divided by each test's area; a result not known yet is the slot's earlier count, never a wait or
D3DERR_TESTINCOMPLETE; with no batch free a test is dropped and its slot keeps its count; without queries every test is
fully visible. No headset, game data or packaging.
"""
from pathlib import Path
import glob
import os
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/test73-visibility"
OUT.mkdir(parents=True, exist_ok=True)
d3d = (ROOT / "port/linux/src/d3d8_gl.c").read_text(encoding="utf-8")


def fn(source, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', source, re.M)
    assert m, name
    start = source.index("{", m.start())
    end = start + 1
    depth = 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[m.start():end] + "\n"


# (static wiring: each frame's batch sent before the swap and the earlier ones read after it, OpenCE a0f22cbba; the
# batch path desktop-only, slot 0 kept)
present = fn(d3d, "D3DDevice_Present")
send_at = present.index("#ifndef HALO_ANDROID\n\t\tvisibility_send_batch();\n#endif")
read_at = present.index("#ifndef HALO_ANDROID\n\t\t/* (after the window's swap, or the headset's frame in its place) */\n"
                        "\t\tvisibility_read_batch();\n#endif")
assert send_at < present.index("platform_video_swap();") < read_at
assert "if (!index)\n\t\tindex = 1;" not in d3d, "slot 0 is a test's own"
assert "device.visibility_results" not in d3d and "visibility_unscaled" not in d3d
batch_struct = d3d[d3d.index("struct visibility_batch\n{"):]
batch_struct = batch_struct[:batch_struct.index("};") + 2]
# (OpenCE a0f22cbba: what a count's place holds until the GPU has copied it)
uncopied = re.search(r"^#define VISIBILITY_UNCOPIED .*$", d3d, re.M).group(0)
batch_struct = uncopied + "\n" + batch_struct

# EGL headers: the project's Android NDK's (as tools/test_test31_graphics.py)
headers = OUT / "include"
if not (headers / "EGL/egl.h").exists():
    candidates = glob.glob(os.path.expanduser("~/android-ndk*/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include")) + \
        glob.glob("/mnt/d/HaloQuest/*ndk*/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include") + \
        glob.glob(os.path.expanduser("~/Android/Sdk/ndk/*/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include")) + \
        glob.glob("/mnt/c/Users/*/AppData/Local/Android/Sdk/ndk/*/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include")
    candidates = [c for c in candidates if Path(c, "EGL/egl.h").exists()]
    assert candidates, "EGL headers missing: install/use the project Android NDK"
    headers.mkdir(exist_ok=True)
    for directory in ("KHR", "EGL"):
        shutil.copytree(Path(sorted(candidates)[-1]) / directory, headers / directory, dirs_exist_ok=True)

functions = "".join(fn(d3d, name) for name in (
    "visibility_query_compare", "visibility_queries_initialize", "visibility_results_initialize",
    "visibility_readback_gl_ok", "D3DDevice_BeginVisibilityTest", "D3DDevice_EndVisibilityTest",
    "D3DDevice_GetVisibilityTestResult", "visibility_fall_back_to_queries", "visibility_send_batch",
    "visibility_read_batch"))
for name in ("visibility_query_compare", "visibility_queries_initialize", "visibility_results_initialize",
             "visibility_readback_gl_ok", "visibility_read_batch"):
    functions = functions.replace("static ", "static ", 1)

harness = r'''
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
typedef unsigned int GLuint, GLenum, GLbitfield; typedef int GLint, GLsizei; typedef unsigned char GLboolean;
typedef char GLchar; typedef ptrdiff_t GLsizeiptr, GLintptr; typedef unsigned long long GLuint64; typedef float GLfloat;
typedef struct __GLsync *GLsync;
typedef int BOOL; typedef unsigned long DWORD; typedef unsigned int UINT; typedef unsigned long long ULONGLONG;
typedef long HRESULT;
#define TRUE 1
#define FALSE 0
#define WINAPI
#define S_OK 0
#define GL_NO_ERROR 0
#define GL_VENDOR 0x1F00
#define GL_RENDERER 0x1F01
#define GL_VERSION 0x1F02
#define GL_SAMPLES_PASSED 0x8914
#define GL_QUERY_RESULT 0x8866
#define GL_QUERY_RESULT_AVAILABLE 0x8867
#define GL_QUERY_BUFFER 0x9192
#define GL_QUERY_BUFFER_BINDING 0x9193
#define GL_MAP_READ_BIT 0x0001
#define GL_MAP_WRITE_BIT 0x0002
#define GL_MAP_PERSISTENT_BIT 0x0040
#define GL_MAP_COHERENT_BIT 0x0080
#define GL_SYNC_GPU_COMMANDS_COMPLETE 0x9117
#define GL_SYNC_FLUSH_COMMANDS_BIT 0x00000001
#define GL_ALREADY_SIGNALED 0x911A
#define GL_TIMEOUT_EXPIRED 0x911B
#define GL_CONDITION_SATISFIED 0x911C
#define GL_TRIANGLES 0x0004
#define GL_FRAMEBUFFER 0x8D40
#define GL_RENDERBUFFER 0x8D41
#define GL_RGBA8 0x8058
#define GL_COLOR_ATTACHMENT0 0x8CE0
#define GL_FRAMEBUFFER_COMPLETE 0x8CD5
#define GL_VERTEX_SHADER 0x8B31
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_LINK_STATUS 0x8B82
#define GL_COLOR_BUFFER_BIT 0x4000
#define VISIBILITY_TEST_SLOTS 4096
#define VISIBILITY_BATCH_COUNT 3
#define VISIBILITY_QUERY GL_SAMPLES_PASSED
#define VISIBILITY_ALL_SAMPLES 1000000
#define F(type, name, args) static type (*p_##name) args;
#define FUNCTIONS \
 F(void, glCreateQueries, (GLenum, GLsizei, GLuint *)) F(GLboolean, glIsQuery, (GLuint)) F(GLenum, glGetError, (void)) \
 F(const unsigned char *, glGetString, (GLenum)) F(void, glGenBuffers, (GLsizei, GLuint *)) \
 F(void, glBindBuffer, (GLenum, GLuint)) F(void, glBufferStorage, (GLenum, GLsizeiptr, const void *, GLbitfield)) \
 F(void *, glMapBufferRange, (GLenum, GLintptr, GLsizeiptr, GLbitfield)) F(void, glDeleteBuffers, (GLsizei, const GLuint *)) \
 F(void, glBeginQuery, (GLenum, GLuint)) F(void, glEndQuery, (GLenum)) F(void, glGetIntegerv, (GLenum, GLint *)) \
 F(GLenum, glClientWaitSync, (GLsync, GLbitfield, GLuint64)) F(GLsync, glFenceSync, (GLenum, GLbitfield)) \
 F(void, glDeleteSync, (GLsync)) F(void, glGetQueryObjectuiv, (GLuint, GLenum, GLuint *)) \
 F(void, glGetQueryBufferObjectuiv, (GLuint, GLuint, GLenum, GLintptr)) F(void, glFlush, (void)) F(void, glFinish, (void)) \
 F(void, glGenFramebuffers, (GLsizei, GLuint *)) F(void, glBindFramebuffer, (GLenum, GLuint)) \
 F(void, glGenRenderbuffers, (GLsizei, GLuint *)) F(void, glBindRenderbuffer, (GLenum, GLuint)) \
 F(void, glRenderbufferStorage, (GLenum, GLenum, GLsizei, GLsizei)) \
 F(void, glFramebufferRenderbuffer, (GLenum, GLenum, GLenum, GLuint)) F(GLenum, glCheckFramebufferStatus, (GLenum)) \
 F(GLuint, glCreateShader, (GLenum)) F(void, glShaderSource, (GLuint, GLsizei, const GLchar *const *, const GLint *)) \
 F(void, glCompileShader, (GLuint)) F(GLuint, glCreateProgram, (void)) F(void, glAttachShader, (GLuint, GLuint)) \
 F(void, glLinkProgram, (GLuint)) F(void, glGetProgramiv, (GLuint, GLenum, GLint *)) F(void, glUseProgram, (GLuint)) \
 F(GLint, glGetUniformLocation, (GLuint, const GLchar *)) F(void, glUniform4f, (GLint, GLfloat, GLfloat, GLfloat, GLfloat)) \
 F(void, glGenVertexArrays, (GLsizei, GLuint *)) F(void, glBindVertexArray, (GLuint)) \
 F(void, glDrawArrays, (GLenum, GLint, GLsizei)) F(void, glViewport, (GLint, GLint, GLsizei, GLsizei)) \
 F(void, glClear, (GLbitfield))
FUNCTIONS
#undef F
/* (AMD's own driver stood in for: its vendor string) */
static int as_amd;
static const unsigned char *test_vendor(GLenum name)
{ return name == GL_VENDOR && as_amd ? (const unsigned char *)"ATI Technologies Inc." : p_glGetString(name); }
#define glCreateQueries p_glCreateQueries
#define glIsQuery p_glIsQuery
#define glGetError p_glGetError
#define glGetString test_vendor
#define glGenBuffers p_glGenBuffers
#define glBindBuffer p_glBindBuffer
#define glBufferStorage p_glBufferStorage
#define glMapBufferRange p_glMapBufferRange
#define glDeleteBuffers p_glDeleteBuffers
#define glBeginQuery p_glBeginQuery
#define glEndQuery p_glEndQuery
#define glGetIntegerv p_glGetIntegerv
#define glClientWaitSync p_glClientWaitSync
#define glFenceSync p_glFenceSync
#define glDeleteSync p_glDeleteSync
#define glGetQueryObjectuiv p_glGetQueryObjectuiv
#define glGetQueryBufferObjectuiv p_glGetQueryBufferObjectuiv
#define glFlush p_glFlush
static int logs;
static void platform_log(const char *format, ...) { (void)format; logs++; }
static int config_boolean(const char *name) { (void)name; return 1; }
/* debug.fixed_step (port_config.c): each sealed batch waited for */
static int fixed_step;
static int halo_fixed_step(void) { return fixed_step; }
''' + batch_struct + r'''
static struct
{
	BOOL gl_ready, visibility_test_active, visibility_unavailable, visibility_logging;
	GLuint active_query;
	BOOL query_pending[VISIBILITY_TEST_SLOTS];
	float query_area[VISIBILITY_TEST_SLOTS];
	GLuint visibility_known[VISIBILITY_TEST_SLOTS];
	struct visibility_batch visibility_batches[VISIBILITY_BATCH_COUNT];
	unsigned long visibility_batch;
	ULONGLONG visibility_serial;
	GLuint visibility_buffer;
	volatile GLuint *visibility_mapped;
	struct { unsigned long submitted, completed, samples, nonzero, maximum, unavailable, dropped, failures; } visibility_stats;
	unsigned long frame;
} device;
static float target_scale[2] = { 1.0f, 1.0f };
static int target_samples = 1;
/* (declared ahead, as d3d8_gl.c does before the device is made) */
static BOOL visibility_queries_initialize(void);
static void visibility_results_initialize(void);
static BOOL visibility_readback_gl_ok(const char *phase);
static void visibility_read_batch(void);
static void visibility_send_batch(void);
''' + functions + r'''
static GLuint program; static GLint rect;
/* a test of the slot: w x h pixels drawn */
static void test(DWORD slot, int w, int h)
{
	D3DDevice_BeginVisibilityTest();
	p_glUniform4f(rect, 0.0f, 0.0f, (float)w, (float)h);
	p_glDrawArrays(GL_TRIANGLES, 0, 6);
	assert(D3DDevice_EndVisibilityTest(slot) == S_OK);
}
static UINT result(DWORD slot)
{
	UINT value = 12345; ULONGLONG time = 1;
	assert(D3DDevice_GetVisibilityTestResult(slot, &value, &time) == S_OK && time == 0);
	return value;
}
/* a present: this frame's batch sent before the swap, the earlier ones read after it (OpenCE a0f22cbba) */
static void present(void) { visibility_send_batch(); p_glFinish(); visibility_read_batch(); device.frame++; }
static void run(int amd)
{
	memset(&device, 0, sizeof(device));
	as_amd = amd; device.gl_ready = TRUE;
	assert(visibility_queries_initialize());
	visibility_results_initialize();
	assert(amd ? device.visibility_mapped == NULL : device.visibility_mapped != NULL);
	/* nothing tested yet: 0 */
	assert(result(0) == 0 && result(1) == 0);
	test(0, 10, 10); test(1, 4, 5); test(4095, 1, 1);
	/* not read before the frame is presented: still the slots' earlier counts, not a wait */
	assert(result(0) == 0 && result(1) == 0);
	for (int i = 0; i < 3 && (result(0) != 100 || result(1) != 20); i++) present();
	/* slot 0 its own, apart from slot 1 (this port used to map 0 to 1) */
	assert(result(0) == 100 && result(1) == 20 && result(4095) == 1);
	/* a target drawn at twice the size each way: its count in the game's pixels */
	target_scale[0] = target_scale[1] = 2.0f;
	test(1, 20, 20);
	target_scale[0] = target_scale[1] = 1.0f;
	for (int i = 0; i < 3 && result(1) != 100; i++) present();
	assert(result(1) == 100 && result(0) == 100);
	/* the same slot twice in a frame: the later stands */
	test(2, 3, 3); test(2, 6, 6);
	for (int i = 0; i < 3 && result(2) != 36; i++) present();
	assert(result(2) == 36);
	/* no batch free (every one waiting to be read): the test dropped, the slot's count kept */
	{
		unsigned long batch = device.visibility_batch, dropped = device.visibility_stats.dropped;
		device.visibility_batch = VISIBILITY_BATCH_COUNT;
		test(0, 7, 7);
		assert(device.visibility_stats.dropped == dropped + 1 && result(0) == 100);
		device.visibility_batch = batch;
	}
	/* many frames: every batch reused, nothing lost or failed */
	for (int frame = 0; frame < 40; frame++) { test(3, 1 + frame % 7, 2); present(); }
	present(); present();
	assert(result(3) == 2u * (1 + 39 % 7) && device.visibility_stats.failures == 0);
	/* debug.fixed_step (tests that play the same every time): the batch sealed at one present is waited for at
	the next, with no glFinish first, so its counts come at that frame whatever the GPU's speed */
	fixed_step = 1;
	test(5, 5, 4);
	visibility_send_batch(); visibility_read_batch(); device.frame++;
	visibility_send_batch(); visibility_read_batch(); device.frame++;
	assert(result(5) == 20 && device.visibility_stats.failures == 0);
	fixed_step = 0;
	/* no queries to be had: every test fully visible */
	device.visibility_unavailable = TRUE;
	test(9, 1, 1);
	assert(result(9) == VISIBILITY_ALL_SAMPLES);
	printf("PASS: %s: slot 0 its own, counts by present in order and by area, earlier counts while pending, later test of "
		"a slot stands, dropped without a free batch, 40 frames' batches reused, fixed step waits at the next present, "
		"no queries fully visible\n",
		amd ? "CPU reads (AMD's driver)" : "fenced query buffer");
}
int main(void)
{
	PFNEGLGETPLATFORMDISPLAYEXTPROC get = (void *)eglGetProcAddress("eglGetPlatformDisplayEXT");
	EGLDisplay display; EGLint major, minor, count; EGLConfig config; EGLContext context;
	const EGLint attributes[] = { EGL_SURFACE_TYPE, EGL_PBUFFER_BIT, EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT, EGL_NONE };
	const EGLint version[] = { EGL_CONTEXT_MAJOR_VERSION, 4, EGL_CONTEXT_MINOR_VERSION, 5,
		EGL_CONTEXT_OPENGL_PROFILE_MASK, EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT, EGL_NONE };
	static const char *vertex = "#version 450 core\nuniform vec4 rect;\nvoid main(){vec2 c[6]=vec2[](vec2(0,0),vec2(1,0),vec2(1,1),vec2(0,0),vec2(1,1),vec2(0,1));"
		"vec2 p=rect.xy+c[gl_VertexID]*rect.zw;gl_Position=vec4(p/32.0-1.0,0.0,1.0);}\n";
	static const char *fragment = "#version 450 core\nout vec4 color;\nvoid main(){color=vec4(1);}\n";
	GLuint vs, fs, fbo, rb, vao; GLint linked = 0;
	assert(get);
	display = get(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, NULL);
	assert(eglInitialize(display, &major, &minor) && eglBindAPI(EGL_OPENGL_API));
	assert(eglChooseConfig(display, attributes, &config, 1, &count) && count);
	context = eglCreateContext(display, config, EGL_NO_CONTEXT, version);
	assert(context != EGL_NO_CONTEXT && eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, context));
#define F(type, name, args) p_##name = (type (*) args)eglGetProcAddress(#name); assert(p_##name);
	FUNCTIONS
#undef F
	printf("desktop GL: %s / %s\n", p_glGetString(GL_RENDERER), p_glGetString(GL_VERSION));
	p_glGenFramebuffers(1, &fbo); p_glBindFramebuffer(GL_FRAMEBUFFER, fbo);
	p_glGenRenderbuffers(1, &rb); p_glBindRenderbuffer(GL_RENDERBUFFER, rb);
	p_glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, 64, 64);
	p_glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rb);
	assert(p_glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE);
	p_glViewport(0, 0, 64, 64); p_glClear(GL_COLOR_BUFFER_BIT);
	vs = p_glCreateShader(GL_VERTEX_SHADER); p_glShaderSource(vs, 1, &vertex, NULL); p_glCompileShader(vs);
	fs = p_glCreateShader(GL_FRAGMENT_SHADER); p_glShaderSource(fs, 1, &fragment, NULL); p_glCompileShader(fs);
	program = p_glCreateProgram(); p_glAttachShader(program, vs); p_glAttachShader(program, fs); p_glLinkProgram(program);
	p_glGetProgramiv(program, GL_LINK_STATUS, &linked); assert(linked);
	p_glUseProgram(program); rect = p_glGetUniformLocation(program, "rect");
	p_glGenVertexArrays(1, &vao); p_glBindVertexArray(vao);
	run(0);
	run(1);
	return 0;
}
'''
source = OUT / "visibility.c"
source.write_text(harness, encoding="utf-8")
exe = OUT / "visibility"
subprocess.run(["clang", "-std=gnu11", "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=undefined",
                "-Wall", "-Wno-unused-function", "-D__GBM__", "-I", str(headers), str(source),
                "-Wl,-l:libEGL.so.1", "-o", str(exe)], check=True)
subprocess.run([str(exe)], check=True, env={**os.environ, "LIBGL_ALWAYS_SOFTWARE": "1"})
