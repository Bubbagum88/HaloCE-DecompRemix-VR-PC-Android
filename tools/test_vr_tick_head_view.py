"""The game's ticks must be able to read the tracked head (parkour, manual reload).

vr_head_view answered only while vr.stereo was set: from vr_stereo_begin at
the start of the frame's stereo pass to the frame's end. The game's ticks run
before that pass (main.c: game_time_update, then main_game_render), so every
call from a tick failed. vr_parkour_velocity reset itself on that failure and
vr_manual_reload_update cancelled silently, so parkour never acted and the
manual reload never reached its input stage (Test47's log: only
"first-person-profile-not-ready"/"stale-first-person-pose" gates). Their unit
suites stub vr_head_view, so they could not see it.

vr_aim (player_control_update, before the ticks) begins the XR frame; the
head is valid for the ticks once the frame has begun with valid views.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def body(text, signature):
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return text[start:index + 1]
    raise AssertionError(signature)


frame = read("port/linux/src/vr_frame.c")
head = body(frame, "int vr_head_view(const float position[3], const float forward[3],")
gate = head[head.index("if (!vr.stereo"):head.index("return 0;")]
assert "vr.frame_begun" in gate and "HALO_XR_FRAME_VIEWS_VALID" in head and "vr.stereo_enabled" in gate, \
    "vr_head_view must also answer between frames (from the game's ticks), not only in the stereo pass"
assert re.search(r"vr\.stereo\s*=\s*0;", body(frame, "int vr_present(")), "vr.stereo is cleared at the frame's end"
aim = body(frame, "int vr_aim(")
assert "frame_begin()" in aim, "vr_aim begins the frame before the ticks"

player_control = read("source/game/player_control.c")
assert "vr_player_control_facing(local_player_index);" in player_control
render = read("port/linux/game/vr_render.c")
assert "vr_aim(" in body(render, "void vr_player_control_facing(")

main = read("source/main/main.c")
loop = main[main.index("player_control_update((real)main_globals.halt_time_scale"):]
assert loop.index("player_control_update(") < loop.index("game_time_update(") < loop.index("main_game_render("), \
    "ticks run after player control (vr_aim) and before the frame's stereo pass"

for path, call in (("port/linux/game/vr_parkour.c", "vr_head_view(camera.n,biped->object.forward.n"),
                   ("port/linux/game/vr_manual_reload.c", "vr_head_view(camera.n, object_get(unit_index)->object.forward.n")):
    assert call in read(path), path
print("PASS: the tracked head is available to the game's ticks (parkour and manual reload no longer reset every tick)")
