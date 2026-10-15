"""Test72: stereoscopic 3D on the flat builds (flat_stereo.c).

The owner: "Do not simply duplicate the same camera frame twice. Render actual
left/right viewpoints with proper eye/camera offset, projection, convergence
and aspect handling. Turning stereo off must return to the normal
single-camera flat rendering path." Modes: SBS (full, half), TAB (full,
half), anaglyph; separation, convergence, eye swap, HUD depth, reticle
depth, reset.

- render.c draws a single player's window once for each eye, each camera
  moved half the separation along its right, each frustum squeezed (half
  formats) and shifted to converge (off-axis); off, or split screen, or a
  screenshot: the path as it was.
- The first-person weapon is posed once from between the eyes; mirrors are
  left out while an eye is drawn; anaglyph's second eye keeps the first's
  colour and each writes its channels only.
- The HUD and the reticle move sideways in each eye by the disparity of a
  point at their depth (d3d8_gl.c's screen offset).
- Measured on the Windows build's frames (Blood Gulch, 768x480 game screen,
  2428-pixel screenshots, 64 mm, 2.5 m): the disparity at infinity was 21-22
  pixels (SBS half; predicted 21.7), 43-44 (SBS full; 43.6), 40-43 (TAB half;
  43.7), 21-22 (TAB full; 21.8); the HUD at 1 m -65 (predicted -65), the
  reticle at 25 m +39 (predicted +39). The model below is the one those
  numbers checked.
- Settings: Video Setup > STEREO 3D, the desktop build's; DEFAULTS resets.
"""
from pathlib import Path
import json
import math
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
stereo = read("port/linux/game/flat_stereo.c")
header = read("port/linux/game/flat_stereo.h")
render = read("source/render/render.c")
hud = read("source/interface/hud_weapon.c")
gl = read("port/linux/src/d3d8_gl.c")
config = read("port/linux/src/port_config.c")
SCREEN = "port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.video_settings.stereo.xml"
VIDEO = "port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.video_settings.xml"

# --- flat builds only; the VR build keeps its own eyes
assert "\n#ifndef HALO_VR\n" in stereo and stereo.rstrip().endswith("#endif")
assert "#ifndef HALO_VR" in header
# every use in shared code is inside #ifndef HALO_VR (or #ifdef HALO_VR's #else)
def calls_outside_vr(text, name):
    stack = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#if"):
            stack.append("flat" if stripped == "#ifndef HALO_VR" else "vr" if stripped == "#ifdef HALO_VR" else "other")
        elif stripped.startswith("#else") and stack:
            stack[-1] = {"flat": "vr", "vr": "flat"}.get(stack[-1], stack[-1])
        elif stripped.startswith("#endif") and stack:
            stack.pop()
        elif ("flat_stereo" in stripped or "_flat_stereo_layer" in stripped) and not stripped.startswith(("/*", "*")):
            assert "flat" in stack, (name, stripped)


for text, name in ((render, "render.c"), (hud, "hud_weapon.c"), (gl, "d3d8_gl.c")):
    calls_outside_vr(text, name)

# --- the settings: flat scope, defaults that leave the game as it was
declared = {}
for match in re.finditer(r'\{ "(display\.stereo[a-z_]*)", _config_(\w+), "((?:\\.|[^"\\])*)", "(\w+)", _environment_value,\s*(_platform_\w+)', config):
    declared[match.group(1)] = (match.group(2), match.group(3), match.group(4), match.group(5))
assert declared == {
    "display.stereo": ("string", '\\"off\\"', "HALO_STEREO", "_platform_flat"),
    "display.stereo_separation": ("real", "64", "HALO_STEREO_SEPARATION", "_platform_flat"),
    "display.stereo_convergence": ("real", "2.5", "HALO_STEREO_CONVERGENCE", "_platform_flat"),
    "display.stereo_swap": ("boolean", "false", "HALO_STEREO_SWAP", "_platform_flat"),
    "display.stereo_hud_depth": ("real", "0", "HALO_STEREO_HUD_DEPTH", "_platform_flat"),
    "display.stereo_reticle_depth": ("real", "0", "HALO_STEREO_RETICLE_DEPTH", "_platform_flat"),
}, declared
used = set(re.findall(r'"(display\.stereo[a-z_]*)"', stereo))
assert used == set(declared), used ^ set(declared)
modes = dict(re.findall(r'!strcmp\(mode, "(\w+)"\)\)\s*return (_stereo_\w+);', stereo))
assert modes == {"off": "_stereo_off", "sbs_half": "_stereo_sbs_half", "sbs_full": "_stereo_sbs_full",
                 "tab_half": "_stereo_tab_half", "tab_full": "_stereo_tab_full", "anaglyph": "_stereo_anaglyph"}, modes
assert "return _stereo_off;\n}" in stereo  # anything else is off
# out-of-range values fall back to the defaults
assert "if (!(separation >= 0.0f && separation <= 200.0f))\n\t\tseparation = 64.0f;" in stereo
assert "if (!(convergence >= 0.25f && convergence <= 100.0f))\n\t\tconvergence = 2.5f;" in stereo
assert "if (!(depth > 0.0f && depth <= 100.0f))\n\t\treturn 0.0f;" in stereo

# --- off is the path as it was: one window, one camera; split screen and screenshots untouched
assert "if (player_windows == 1 && screenshot_index == NULL && flat_stereo_active())" in render
loop = render[render.index("if (player_windows == 1 && screenshot_index == NULL && flat_stereo_active())"):]
loop = loop[:loop.index("#endif")]
assert "for (eye = 0; eye < 2; eye++)" in loop and "struct render_window eye_window = *window;" in loop
assert "flat_stereo_begin_eye(&eye_window, eye);" in loop and "render_player_frame(&eye_window, NULL);" in loop
assert "flat_stereo_end_eye();" in loop and "continue;" in loop
assert "!windoze[window_index].console_window && windoze[window_index].local_player_index != NONE" in render
for guard in ("if (stereo.eye == NONE || !bounds)\n\t\treturn;", "if (stereo.eye == NONE || !camera)\n\t\treturn;",
              "if (stereo.eye == NONE || stereo.mode != _stereo_anaglyph)\n\t\treturn 0xFFFFFFFFUL;",
              "if (stereo.eye == NONE || stereo.layer == _flat_stereo_layer_world)\n\t\treturn 0.0f;"):
    assert guard in stereo, guard
assert "return stereo.eye == 1 && stereo.mode == _stereo_anaglyph;" in stereo  # keep colour: anaglyph's second eye only

# --- the weapon once from between the eyes, mirrors out, anaglyph masks
assert "if (!flat_stereo_second_eye())" in render and "flat_stereo_center_camera(&render.camera);" in render
assert "!flat_stereo_drawing_eye())" in render
assert "parameters.suppress_clear = flat_stereo_keep_color();" in render
assert "flat_stereo_frustum_bounds(&frustum_bounds);" in render
assert "rs[D3DRS_COLORWRITEENABLE] & (DWORD)flat_stereo_color_write_mask()" in gl
assert "#define STEREO_WRITE_RED 0x00010000UL" in stereo and "#define STEREO_WRITE_GREEN 0x00000100UL" in stereo
assert "#define STEREO_WRITE_BLUE 0x00000001UL" in stereo and "#define STEREO_WRITE_ALPHA 0x01000000UL" in stereo
assert ("return seen == 0 ? (STEREO_WRITE_RED | STEREO_WRITE_ALPHA) : "
        "(STEREO_WRITE_GREEN | STEREO_WRITE_BLUE | STEREO_WRITE_ALPHA);") in stereo
assert stereo.count("swap ? (short)(1 - ") == 2  # the view and the colour both follow the swap

# --- the HUD's and the reticle's layers, and the screen offset that carries them
assert "int stereo_layer = flat_stereo_layer(_flat_stereo_layer_hud);\n\t\t\tinterface_draw_screen();\n\t\t\tflat_stereo_layer(stereo_layer);" in render
assert hud.count("flat_stereo_layer(_flat_stereo_layer_reticle);") == 2 and hud.count("flat_stereo_layer(stereo_layer);") == 2
assert hud.count("crosshairs_draw(\n") == 2 + 2  # two definitions (declaration, body) and two calls
assert "#define SCREEN_OFFSET ((float)ui_offset + flat_stereo_screen_offset())" in gl
assert "inputs[count++] = float_to_dword(SCREEN_OFFSET);" in gl and "converted->screen_offset = SCREEN_OFFSET;" in gl
assert "(DWORD)UI_OFFSET" not in gl

# --- the model, against what the frames measured
UNITS_PER_METRE = 1 / 3.048
assert "#define FLAT_STEREO_UNITS_PER_METRE (1.0f / 3.048f)" in stereo
assert "stereo.offset = side * separation * 0.001f * FLAT_STEREO_UNITS_PER_METRE;" in stereo
assert "-side * (separation * 0.001f / convergence) / (tangent * aspect)" in stereo
assert "(real)(viewport->x1 - viewport->x0) * 0.5f / (stereo.squeeze_x * aspect * tangent)" in stereo
assert "(1.0f / stereo.convergence - 1.0f / depth)" in stereo
assert "stereo.squeeze_x = stereo.mode == _stereo_sbs_half ? 2.0f : stereo.mode == _stereo_tab_half ? 0.5f : 1.0f;" in stereo

VFOV, WIDTH, HEIGHT, SCALE = 0.8397, 768, 480, 2428 / 768


def eye(mode):
    w, h = (WIDTH / 2, HEIGHT) if mode.startswith("sbs") else (WIDTH, HEIGHT / 2)
    squeeze = {"sbs_half": 2.0, "tab_half": 0.5}.get(mode, 1.0)
    aspect = w / h
    return w, squeeze, aspect, math.tan(VFOV / 2)


def infinity_disparity(mode, separation=0.064, convergence=2.5):
    w, squeeze, aspect, tangent = eye(mode)
    shift = (separation / convergence) / (tangent * aspect)  # the two eyes' together, in bounds units
    return shift * w / (2 * squeeze) * SCALE  # bounds 2*squeeze wide over w pixels


def layer_disparity(mode, depth, separation=0.064, convergence=2.5):
    w, squeeze, aspect, tangent = eye(mode)
    pixels_per_tangent = w * 0.5 / (squeeze * aspect * tangent)
    return pixels_per_tangent * separation * (1 / convergence - 1 / depth) * SCALE


for mode, measured in (("sbs_half", (21, 22)), ("sbs_full", (43, 44)), ("tab_half", (40, 43)), ("tab_full", (21, 22))):
    predicted = infinity_disparity(mode)
    assert measured[0] - 2 <= predicted <= measured[1] + 2, (mode, predicted, measured)
assert abs(layer_disparity("sbs_full", 1.0) - -65) < 1.5
assert abs(layer_disparity("sbs_full", 25.0) - 39) < 1.5
# a layer at the convergence distance is at the screen, as SCREEN (0) is
assert layer_disparity("sbs_full", 2.5) == 0

# --- the settings screen: Video Setup > STEREO 3D, desktop
screen = ET.parse(ROOT / SCREEN).getroot()
spinners = {w.get("setting"): w for w in screen.iter("widget") if w.get("type") == "spinner"}
assert set(spinners) == set(declared), set(spinners) ^ set(declared)
for setting, widget in spinners.items():
    strings, values = widget.get("strings").split("|"), widget.get("values").split("|")
    assert len(strings) == len(values), setting
    assert any(on.get("run") == "port setting load" for on in widget.iter("on")), setting
    default = declared[setting][1].strip('\\"')
    assert default in values or any(float(v) == float(default) for v in values if re.match(r"^[\d.]+$", v)), (setting, default)
    for value in values:
        if declared[setting][0] == "real":
            assert 0 <= float(value) <= 200
assert spinners["display.stereo"].get("values").split("|") == list(modes)
assert spinners["display.stereo_hud_depth"].get("values").split("|")[0] == "0"
assert spinners["display.stereo_reticle_depth"].get("values").split("|")[0] == "0"
runs = [on.get("run") for on in screen.iter("on")]
assert "port settings defaults" in runs and "port settings save" in runs
labels = [s.get("text") for s in screen.iter("strings") if s.get("name").endswith("/labels") for s in s]
helps = [s.get("text") for s in screen.iter("strings") if s.get("name").endswith("/help_strings") for s in s]
assert len(helps) == len(labels) + 1 and helps[0] == ""
for text in helps[1:]:
    assert all(len(line) <= 52 for line in text.split("\\n")), text  # the help box's width
assert all(len(label) <= 20 for label in labels)
for value in [s for w in spinners.values() for s in w.get("strings").split("|")]:
    assert len(value) <= 9, value  # the spinner's 147 pixels
video = read(VIDEO)
assert 'op_stereo" x="54" y="373" platform="desktop"/>' in video
assert 'open="main_menu/settings_select/player_setup/player_profile_edit/video_settings/stereo/stereo_settings_screen"' in video
video_labels = [s.get("text") for s in ET.parse(ROOT / VIDEO).getroot().iter("strings") if s.get("name").endswith("/labels") for s in s]
assert video_labels[11] == "STEREO 3D:"
files = json.loads(read("port/assets/menus/menus.json"))["files"]
assert SCREEN.split("menus/")[1] in files

print("test_test72_stereo: ok")
