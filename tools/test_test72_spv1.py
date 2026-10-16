"""Test72: SPV1's left eye (the owner: it loads, but the left eye stretches at
times). Findings in his log (halo_log_2026-10-15_22-47-55-126_25266.txt):

- The three Custom Edition files are not in play on b30: "0x0 of tags from
  resource maps (bitmaps 0, sounds 0, loc 0)"; SPV1's protected maps carry
  their own. Ruled out there.
- 9669 "incompatible bitmap type in shader got 2d texture expected cube map":
  SPV1's content (the Custom Edition loader does convert cube maps); each
  drawn with the cube map default, as Halo does, but logged every draw
  (about 120 log writes a second). Now once a bitmap and kind, then counted.
- The load: up to 2967 draws and 26 MB of geometry a frame (the stock
  campaign: 400 to 650 draws, no stream wraps), game frames of 25 to 55 ms
  (left eye 22 ms, right 17): the headset reprojects old frames, which
  smears and stretches edges, the eye drawn first the stalest. Not proven:
  nothing in the log recorded the eyes' views.
- No eye-specific path found in the code: both eyes take eye_camera, and
  vr_render_frustum_bounds' eye_bounds[vr_render_pass] matches eye_camera's
  eye_bounds[eye] (left 0, right 1).

So the next log says: each eye's bounds, viewport, aspect and field, the map
and Custom Edition, once a map and on any change, and when the two eyes do
not mirror; which pass filled the geometry stream.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
rasterizer = read("source/rasterizer/xbox/rasterizer_xbox.c")
render = read("port/linux/game/vr_render.c")
gl = read("port/linux/src/d3d8_gl.c")
halo_vr = read("port/linux/include/halo_vr.h")

# the error once a bitmap and kind
assert "static boolean bitmap_type_error_first(long definition_index, short actual, short type)" in rasterizer
assert rasterizer.count("if (bitmap_type_error_first(bitmap_definition_index, bitmap->type, type))") == 2
assert "++repeats % 2000 == 0" in rasterizer
# the fallback itself unchanged: the kind's default
assert rasterizer.count("global_rasterizer_data->default_textures[type].index") >= 2

# the eyes' views logged
diagnostics = render[render.index("static void vr_eye_diagnostics(struct render_window const *windows)"):]
diagnostics = diagnostics[:diagnostics.index("\n}\n")]
for field in ("bounds x %.3f..%.3f y %.3f..%.3f", "viewport %d,%d-%d,%d", "custom edition %s", "field %.3f rad"):
    assert field in diagnostics, field
assert "the eyes' views do not mirror each other" in diagnostics
assert "vr_eye_diagnostics(windows);" in render
# the indices agree: eye_camera fills eye_bounds[eye], the frustum reads eye_bounds[pass]
assert "eye_camera(eye, &windows[window].rasterizer_camera, &vr_render.eye_bounds[eye]);" in render
assert "short window = (short)(eye ^ vr_render_first_eye);" in render
assert "*bounds = vr_render.eye_bounds[vr_render_pass];" in render
enum = halo_vr[halo_vr.index("_vr_render_pass_none = -1,"):]
assert re.match(r"_vr_render_pass_none = -1,\s*_vr_render_pass_left_eye,\s*_vr_render_pass_right_eye,", enum)

# the stream buffer's wraps by pass
assert 'stream buffer full during VR pass %d (0 the left eye, 1 the right eye)' in gl

print("PASS: Test72 SPV1 diagnostics: the cube-map error once a bitmap, each eye's view logged (and any asymmetry), "
      "the stream buffer's wraps by pass; the eyes' indices agree")
