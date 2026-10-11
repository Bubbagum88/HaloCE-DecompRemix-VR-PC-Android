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
import shutil
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


build = read("tools/android_build.py")
assert 'prototype_flag = "-Wno-everything -Werror=implicit-function-declaration"' in build
assert 'token != "-w"' in build, "strict units must drop -w (it overrides -Werror= in C89)"
# Every guest unit (game, port, platform, runtime, musl, libtiff, Opus and the
# other third-party code) is compiled through guest_object, which applies it.
guest_object = build[build.index("    def guest_object("):]
guest_object = guest_object[:guest_object.index("\n\n")]
assert "cflags = strict(cflags)" in guest_object, "guest_object must make every unit strict"
assert "libtiff/" not in build, "libtiff is reachable (screenshots) and must not be exempt"

declarations = {
    "port/linux/game/network_voice.c": "void platform_log(char const *format, ...);",
    "port/linux/game/vr_world_remote.c": "void platform_log(char const *format, ...);",
    "port/linux/game/vr_npc_interaction.c": '#include "physics/collision_features.h"',
    "source/game/game_engine.c": "void rasterizer_text_set_scale(real scale, real origin_x, real origin_y);",
    "source/objects/object_types.c": "boolean game_engine_vehicle_placement_allowed(",
    "port/linux/game/network_campaign_session.c": "short main_get_solo_level_from_name(char const *name);",
    "source/interface/ui_widget_event_handler_functions.c": "boolean playlist_profile_get_options(",
    "source/bitmaps/libtiff/tiffioP.h": "extern\tvoid *debug_malloc(unsigned int, unsigned char, const char *, long);",
}
for path, text in declarations.items():
    assert text in read(path), f"{path} lost its declaration: {text}"

# The flags themselves: once strict() has rewritten them, a C89 unit built
# with -w must still fail on an undeclared call (where clang is available).
clang = shutil.which("clang")
if clang:
    namespace = {}
    source = build[build.index("    prototype_flag = "):build.index("    def guest_object(")]
    exec(textwrap.dedent(source), namespace)
    flags = namespace["strict"]("-std=gnu89 -w").split()
    with tempfile.TemporaryDirectory() as tmp:
        unit = Path(tmp) / "unit.c"
        unit.write_text('int f(void) { return undeclared_call(1.5f, "x"); }\n', encoding="utf-8")
        result = subprocess.run([clang, *flags, "-fsyntax-only", str(unit)], capture_output=True, text=True)
        assert result.returncode != 0 and "implicit" in result.stderr, result.stderr
        unit.write_text("int g(int); int f(void) { return g(1); }\n", encoding="utf-8")
        result = subprocess.run([clang, *flags, "-fsyntax-only", str(unit)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    print("PASS: the strict guest flags reject an undeclared call even in C89 with -w")

# The voice diagnostics must not reintroduce the misdiagnosis.
voice = read("port/linux/game/network_voice.c")
assert "the crash itself was the missing platform_log" in voice
print("PASS: Android guest units must declare every function they call (variadic/float/narrow-return ABI)")
