"""Test72: the left eye alone garbled (the owner: "the left eye shows model
stretching, warping, etc. like a bunch of garbled meshes. right eye is fine",
in SPV1 and in a multiplayer match, worse as the frame rate falls).

The left eye is the frame's first pass: it advances the frame's state
(VR_RENDER_REPEAT) and begins after everything between frames, where the
right eye begins straight after the left's resolve, which sets the GL state
anew. So:
- the first eye begins from GL state set anew, as the second does;
- vr.eye_order (DISPLAY > EYE ORDER) draws the right eye first, the frame's
  state then advancing in its pass: garbling that follows it is the first
  pass's, garbling that stays is the left eye's own;
- [vr-eyes] logs each eye's draws and streamed bytes, and says when the eyes
  draw different amounts.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
halo_vr = read("port/linux/include/halo_vr.h")
render = read("port/linux/game/vr_render.c")
gl = read("port/linux/src/d3d8_gl.c")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")

# ---- the repeat follows the eye drawn first
vr_part = halo_vr[:halo_vr.index("#else")]
assert "extern int vr_render_first_eye;" in vr_part and "void halo_vr_first_eye_begin(void);" in vr_part
assert "#define VR_RENDER_REPEAT() ((VR_RENDER_EYE() && vr_render_pass != vr_render_first_eye) || \\" in vr_part
assert "vr_render_pass == _vr_render_pass_right_eye || \\\n\tvr_render_pass == _vr_render_pass_hud" not in vr_part
assert "#define VR_RENDER_REPEAT() 0" in halo_vr  # flat builds unchanged
assert "int vr_render_first_eye = _vr_render_pass_left_eye;" in render  # left first unless asked

order = render[render.index("static int vr_render_eye_order(void)"):]
order = order[:order.index("\n}\n")]
assert 'strcmp(config_string("vr.eye_order"), "right") == 0 ?' in order
assert "_vr_render_pass_right_eye : _vr_render_pass_left_eye;" in order

windows = render[render.index("short vr_render_windows("):]
windows = windows[:windows.index("\n}\n")]
assert "vr_render_first_eye = vr_render_eye_order();" in windows
assert windows.index("vr_render_first_eye = vr_render_eye_order();") < windows.index("short window = (short)(eye ^ vr_render_first_eye);")
assert "vr_render.pass_of_window[eye ^ vr_render_first_eye] =\n\t\t\teye ? _vr_render_pass_right_eye : _vr_render_pass_left_eye;" in windows
assert "vr_render.eye_of_window[eye ^ vr_render_first_eye] = (short)eye;" in windows
assert "vr_render.pass_of_window[0] = _vr_render_pass_left_eye;" not in windows

# the mapping, worked through: window 0 holds the first eye, which alone of
# the two is no repeat; each eye's window resolves that eye and frames it
LEFT, RIGHT = 0, 1
for first in (LEFT, RIGHT):
    pass_of_window, eye_of_window, camera_of_window = {}, {}, {}
    for eye in (0, 1):
        window = eye ^ first
        camera_of_window[window] = eye
        pass_of_window[window] = RIGHT if eye else LEFT
        eye_of_window[window] = eye
    assert pass_of_window[0] == first
    for window in (0, 1):
        assert eye_of_window[window] == pass_of_window[window] == camera_of_window[window]
    repeat = {p: p != first for p in (LEFT, RIGHT)}
    assert [p for p in (LEFT, RIGHT) if not repeat[p]] == [first]

# the diagnostics read each eye's own window
diagnostics = render[render.index("static void vr_eye_diagnostics(struct render_window const *windows)"):]
diagnostics = diagnostics[:diagnostics.index("\n}\n")]
assert diagnostics.count("windows[eye ^ vr_render_first_eye]") == 2 and "&windows[eye]." not in diagnostics

# ---- the first eye begins as the second does
begin = render[render.index("void vr_render_window_begin("):]
begin = begin[:begin.index("\n}\n")]
assert "if (VR_RENDER_EYE() && vr_render_pass == vr_render_first_eye)\n\t\thalo_vr_first_eye_begin();" in begin
assert begin.index("vr_render_pass = (vr_render.stereo") < begin.index("halo_vr_first_eye_begin();")
first = gl[gl.index("void halo_vr_first_eye_begin(void)"):]
first = first[:first.index("\n}\n")]
for line in ("if (!device.gl_ready)", "glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);", "glBindBuffer(GL_PIXEL_PACK_BUFFER, 0);",
             "glBindVertexArray(device.vertex_array);", "xgpu_gl_state_invalidate();"):
    assert line in first, line
resolve = gl[gl.index("void halo_vr_resolve_eye(int eye)"):]
resolve = resolve[:resolve.index("\n}\n")]
assert "xgpu_gl_state_invalidate();" in resolve  # what the second eye begins after
# both inside the VR build's part of the file
vr_block = gl[gl.index("/* ---------- the headset's stereo frames"):]
assert vr_block.index("void halo_vr_first_eye_begin(void)") < vr_block.index("#endif")

# ---- [vr-eyes]
count = gl[gl.index("static void vr_pass_count(unsigned long draws, unsigned long bytes)"):]
count = count[:count.index("\n}\n")]
assert "if (vr_render_pass >= 0 && vr_render_pass < 6)" in count
assert "#define vr_pass_count(draws, bytes) ((void)0)" in gl
assert gl.count("vr_pass_count(1, 0);") == 1 and gl.count("vr_pass_count(0, size);") == 2
assert "upload_perf.draws++;\n\tvr_pass_count(1, 0);" in gl
assert gl.count("upload_perf.upload_bytes += size;\n\tvr_pass_count(0, size);") == 2
perf = gl[gl.index("static void upload_perf_frame(BOOL safe)"):]
perf = perf[:perf.index("\n}\n")]
assert '"[vr-eyes] per frame: left eye %.0f draws (%.0f KB), right eye %.0f draws (%.0f KB), "' in perf
assert "the eyes drew different amounts" in perf
assert "memset(vr_pass_draws, 0, sizeof(vr_pass_draws));" in perf

# ---- the setting
assert re.search(r'\{ "vr\.eye_order", _config_string, "\\"left\\"", "HALO_VR_EYE_ORDER", _environment_value, _platform_vr,', config)
assert '{ "EYE ORDER", "vr.eye_order", _vr_setting_string, 2, { { "LEFT FIRST", "left" }, { "RIGHT FIRST", "right" } } },' in menu
effects = menu[menu.index("static struct vr_menu_setting const vr_menu_effects[] ="):]
effects = effects[:effects.index("};")]
assert '"EYE ORDER"' in effects and effects.count("\n\t{ ") + effects.count("\n\tVR_MENU_EFFECT(") == 15  # two screens, as before (+ FAST DECALS, BLOOD LAYERS, HOLSTERED GUNS)

print("PASS: Test72 eyes: the first eye begins from GL state set anew; EYE ORDER draws the right eye first "
      "(the frame's state advancing with it); [vr-eyes] compares the eyes' draws")
