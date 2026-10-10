"""The Android guest build must reject calls without a prototype.

The guest ABI (arm64_32, Darwin calling convention) passes variadic arguments
on the stack, promoted float arguments in double registers, and leaves narrow
return values unextended. A call to an undeclared function is therefore
silently miscompiled. That broke Test50/Test51 voice logging (platform_log was
undeclared in network_voice.c: every logged value was stack garbage and a %s
crashed the Test50 join) and the Test46+ NPC pose-clearance test
(collision_test_sphere's float radius arrived as garbage).

The game code is C89 with -w, where an implicit declaration is a suppressed
warning even when promoted, so the build swaps -w for -Wno-everything and
promotes exactly this diagnostic to an error. This suite guards that wiring and
the specific declarations; the build itself enforces the rest.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


build = read("tools/android_build.py")
assert 'prototype_flag = "-Wno-everything -Werror=implicit-function-declaration"' in build
assert 'token != "-w"' in build, "strict units must drop -w (it overrides -Werror= in C89)"
assert "cflags = strict(cflags)" in build
assert "guest_object(source, strict(game_cflags))" in build
assert '"-DHALO_LINUX_PLATFORM_LAYER", prototype_flag,' in build
assert 'startswith("source/bitmaps/libtiff/")' in build

declarations = {
    "port/linux/game/network_voice.c": "void platform_log(char const *format, ...);",
    "port/linux/game/vr_world_remote.c": "void platform_log(char const *format, ...);",
    "port/linux/game/vr_npc_interaction.c": '#include "physics/collision_features.h"',
    "source/game/game_engine.c": "void rasterizer_text_set_scale(real scale, real origin_x, real origin_y);",
    "source/objects/object_types.c": "boolean game_engine_vehicle_placement_allowed(",
    "port/linux/game/network_campaign_session.c": "short main_get_solo_level_from_name(char const *name);",
    "source/interface/ui_widget_event_handler_functions.c": "boolean playlist_profile_get_options(",
}
for path, text in declarations.items():
    assert text in read(path), f"{path} lost its declaration: {text}"

# The voice diagnostics must not reintroduce the misdiagnosis.
voice = read("port/linux/game/network_voice.c")
assert "the crash itself was the missing platform_log" in voice
print("PASS: Android guest units must declare every function they call (variadic/float/narrow-return ABI)")
