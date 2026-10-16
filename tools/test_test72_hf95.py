"""Test72: HaloFreak95's work (their halo.exe and OpenCEMods.zip, "Halo Divers
mods by John"; their fast decals in jcompto95-tech/OpenCE PR #2, 1b9b09d4),
ported where it adds to this port.

Fast decals (display.decals_on_gpu): decals drawn from the stream their
vertices were made in, a quad list each with its colour in register 9, as the
Xbox drew them, instead of their vertices written again one attribute at a time
every frame; and quad lists drawn with one kept index buffer instead of a list
made, uploaded and thrown away per draw. On for the desktop builds (theirs);
off by default on Android and the Quest (draw-bound frames, not yet measured
there): FAST DECALS in Extra Effects (flat) and DISPLAY (VR).

Blood layers (game.blood_layers): a splat of blood is not laid where that many
splats of blood, not yet faded, already lie within its radius (in the cluster
it lands in): blood on blood is solid after a few layers, and each one more is
its pixels drawn again, blended. 0 (all, the game's own) on desktop; 6 on
Android and the Quest. BLOOD LAYERS in VR DISPLAY.

Touch aim assist (their input.touch_aim_assist): already here, as AIM ASSIST
(input.mouse_aim_assist), which covers swipe and gyro aim on Android.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
gl = read("port/linux/src/d3d8_gl.c")
decals = read("source/rasterizer/xbox/rasterizer_xbox_decals.c")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")
extra = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.video_settings.extra_effects.xml")

# ---- the kept quad indices
assert "\tGLuint quad_index_buffer;\n\tunsigned long quad_index_quads;\n" in gl
assert "\tdevice.quad_index_buffer = 0;\n\tdevice.quad_index_quads = 0;\n#ifndef HALO_ANDROID\n\tglGenBuffers(1, &device.stream_buffer);" in gl
assert "#define QUAD_INDEX_QUADS_MAXIMUM (0x10000 / 4)" in gl
bind = gl[gl.index("#ifdef HALO_WEB\nstatic BOOL quad_index_bind("):]
bind = bind[:bind.index("#endif")]
web, native = bind.split("#else")
assert "return FALSE;" in web and "glGenBuffers" not in web  # the web build as before
assert "if (!quads || quads > QUAD_INDEX_QUADS_MAXIMUM)\n\t\treturn FALSE;" in native
assert "glBufferData(GL_ELEMENT_ARRAY_BUFFER, (GLsizeiptr)(grown * 6 * sizeof(WORD)), indices, GL_STATIC_DRAW);" in native
assert native.count("state_element_array_buffer(device.quad_index_buffer);") == 2
# the pattern, worked through: the indices quad_indices made, for every size
def kept(grown):
    out = []
    for quad in range(grown):
        first = quad * 4
        out += [first, first + 1, first + 2, first, first + 2, first + 3]
    return out
def made(vertices):  # quad_indices(NULL, ...): 0 1 2, 0 2 3 per quad
    out = []
    for first in range(0, vertices - vertices % 4, 4):
        out += [first, first + 1, first + 2, first, first + 2, first + 3]
    return out
for vertices in (4, 8, 400, 1024, 4 * 0x4000):
    assert kept(vertices // 4)[:vertices // 4 * 6] == made(vertices)
assert max(kept(0x10000 // 4)) == 0xFFFF  # every index fits an unsigned short
draw = gl[gl.index("if (quad_index_bind(vertex_count / 4, &count))"):]
draw = draw[:draw.index("\n\t}\n")]
assert "glDrawElements(GL_TRIANGLES, (GLsizei)count, GL_UNSIGNED_SHORT, (const void *)0);" in draw
assert "WORD *indices = quad_indices(NULL, vertex_count, &count);" in draw and "free(indices);" in draw  # the fallback

# ---- the decals
stream = decals[decals.index("static boolean rasterizer_decals_stream_drawn(void)"):]
stream = stream[:stream.index("\n}\n")]
assert 'drawn = config_boolean("display.decals_on_gpu") != 0;' in stream and "config_changes()" in stream
path = decals[decals.index("if (rasterizer_decals_stream_drawn())"):]
path = path[:path.index("else\n")]
for line in ("IDirect3DDevice8_SetVertexData4ub(", "9,", "(byte)(PIXEL32_COMPONENT_MASK - intensity));",
             "IDirect3DDevice8_DrawVertices(", "D3DPT_QUADLIST,", "vertex_data_offset / sizeof(struct decal_vertex),",
             "4 * decal->quad_count);"):
    assert line in path, line
assert "decal_batch" in decals  # the batched path kept

# ---- the setting
android = config[config.index("#ifdef HALO_ANDROID\n\t{ \"display.decals_on_gpu\""):]
android = android[:android.index("#endif")]
assert re.search(r'\{ "display\.decals_on_gpu", _config_boolean, "false",', android.split("#else")[0])
assert re.search(r'\{ "display\.decals_on_gpu", _config_boolean, "true",', android.split("#else")[1])
assert '{ "FAST DECALS", "display.decals_on_gpu", _vr_setting_boolean, 2, { { "OFF", "false" }, { "ON", "true" } } },' in menu
assert 'op_decals_on_gpu" x="54" y="313"' in extra and 'setting="display.decals_on_gpu" values="true|false"' in extra
labels = extra[extra.index('extra_effects/labels">'):]
labels = labels[:labels.index("</strings>")]
assert re.findall(r'<string text="([^"]*)"', labels)[8] == "FAST DECALS:"

# ---- blood layers
effects_decals = read("source/effects/decals.c")
layers = effects_decals[effects_decals.index("static boolean decal_blood_layers_full("):]
layers = layers[:layers.index("\n}\n")]
assert 'layers = config_integer("game.blood_layers");' in layers
assert "if (layers <= 0 ||" in layers and "!decal_blood_named(decal_definition_index))" in layers
assert "decal_get_first_decal_index(cluster_index, layer);" in layers and "decal->intensity >= 128" in layers
assert "distance_squared3d(&decal->position, &collision->point) < radius * radius" in layers
assert "++count >= layers)" in layers
gate = effects_decals[effects_decals.index("/* port: (Test72) not where enough blood lies (game.blood_layers) */"):]
gate = gate[:gate.index("decal_new_from_collision(")]
assert "(permanent || editor_geometry ||\n\t\t\t\t\t\t!decal_blood_layers_full(decal_definition_index, &collision, radius_modifier)))" in gate
android = config[config.index('#ifdef HALO_ANDROID\n\t{ "game.blood_layers"'):]
android = android[:android.index("#endif")]
assert re.search(r'\{ "game\.blood_layers", _config_integer, "6",', android.split("#else")[0])
assert re.search(r'\{ "game\.blood_layers", _config_integer, "0",', android.split("#else")[1])
assert '{ "BLOOD LAYERS", "game.blood_layers", _vr_setting_multi, 3, { { "ALL", "game.blood_layers=0" }, { "6", "game.blood_layers=6" }, { "3", "game.blood_layers=3" } } },' in menu
# the rule, worked through: the n+1th splat on a spot is not laid; faded, far or other marks do not count
def laid(cap, existing):
    if cap <= 0:
        return True
    count = sum(1 for (blood, intensity, distance) in existing if blood and intensity >= 128 and distance < 1.0)
    return count < cap
assert laid(0, [(True, 255, 0.0)] * 50)
assert laid(6, [(True, 255, 0.1)] * 5) and not laid(6, [(True, 255, 0.1)] * 6)
assert laid(6, [(True, 255, 0.1)] * 5 + [(False, 255, 0.0)] * 9 + [(True, 60, 0.0)] * 9 + [(True, 255, 1.5)] * 9)

# ---- touch aim assist: AIM ASSIST, said for swipe and gyro
mouse = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.mouse_settings.xml")
assert "aiming by mouse, swipe or gyro, as a controller." in mouse
assert "swipe and gyro aim (HaloFreak95's input.touch_aim_assist)." in config
xinput = read("port/linux/src/xinput_sdl.c")
assert "if (touch.yaw != 0.f || touch.pitch != 0.f) mouse_aimed_ms = SDL_GetTicks();" in xinput

print("PASS: Test72 HaloFreak95: fast decals (kept quad indices; decals drawn from their stream; "
      "FAST DECALS on for desktop, off on Android/Quest until measured); blood layers (6 on Android/Quest); "
      "touch aim assist as AIM ASSIST")
