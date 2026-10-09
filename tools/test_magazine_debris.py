"""Exercise bounded magazine-debris policy and guard its native integration."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
build = ROOT / "build" / "magazine-debris-tests"
build.mkdir(parents=True, exist_ok=True)

c = r'''
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include "vr_magazine_debris_math.h"
int main(void) {
    int active[VR_MAGAZINE_DEBRIS_CAPACITY] = {0};
    unsigned age[VR_MAGAZINE_DEBRIS_CAPACITY] = {0};
    assert(VR_MAGAZINE_DEBRIS_CAPACITY == 32);
    assert(vr_magazine_debris_choose_slot(active, age, VR_MAGAZINE_DEBRIS_CAPACITY) == 0);
    active[0] = active[1] = active[2] = 1;
    age[0] = 40; age[1] = 5; age[2] = 99;
    assert(vr_magazine_debris_choose_slot(active, age, VR_MAGAZINE_DEBRIS_CAPACITY) == 3);
    for (int i=3;i<VR_MAGAZINE_DEBRIS_CAPACITY;i++) active[i]=1,age[i]=(unsigned)i;
    assert(vr_magazine_debris_choose_slot(active, age, VR_MAGAZINE_DEBRIS_CAPACITY) == 2);
    assert(vr_magazine_debris_choose_slot(active, age, 0) == -1);
    unsigned age_counter=UINT_MAX-1;
    assert(vr_magazine_debris_advance_age(&age_counter) && age_counter==UINT_MAX);
    assert(vr_magazine_debris_advance_age(&age_counter) && age_counter==UINT_MAX);
    float speed[3]={.01f,.02f,.03f};
    assert(vr_magazine_debris_speed_valid(speed,.04f));
    speed[0]=NAN;assert(!vr_magazine_debris_speed_valid(speed,.04f));
    speed[0]=.04f;speed[1]=speed[2]=0;assert(vr_magazine_debris_speed_valid(speed,.04f));
    assert(!vr_magazine_debris_speed_valid(speed,.039f));
    assert(vr_magazine_debris_spawn_allowed(1,1,1,64,1,.02f,.2f));
    assert(!vr_magazine_debris_spawn_allowed(0,1,1,64,1,.02f,.2f));
    assert(!vr_magazine_debris_spawn_allowed(1,0,1,64,1,.02f,.2f));
    assert(!vr_magazine_debris_spawn_allowed(1,1,1,65,1,.02f,.2f));
    assert(!vr_magazine_debris_spawn_allowed(1,1,1,64,0,.02f,.2f));
    assert(!vr_magazine_debris_spawn_allowed(1,1,1,64,1,NAN,.2f));
    assert(!vr_magazine_debris_spawn_allowed(1,1,1,64,1,.21f,.2f));
    puts("PASS: persistent magazine pool, oldest-slot recycling, saturating age, finite speed and fail-closed spawn bounds");
}
'''
src = build / "test.c"
exe = build / "test_magazine_debris"
src.write_text(c)
subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-fsanitize=address,undefined", "-I" + str(ROOT / "port/linux/game"),
                str(src), "-lm", "-o", str(exe)], check=True)
subprocess.run([str(exe)], check=True)

reload = (ROOT / "port/linux/game/vr_manual_reload.c").read_text()
objects = (ROOT / "source/objects/objects.c").read_text()
renderer = (ROOT / "source/render/render_objects.c").read_text()
state = (ROOT / "source/saved games/game_state.c").read_text()
spawn = reload[reload.index("static void debris_spawn_from_reload"):reload.index("void vr_manual_reload_debris_tick")]
tick = reload[reload.index("void vr_manual_reload_debris_tick"):reload.index("void vr_manual_reload_debris_render")]
render = reload[reload.index("void vr_manual_reload_debris_render"):reload.index("static boolean reload_near")]
map_init = objects[objects.index("void objects_initialize_for_new_map"):objects.index("void objects_dispose_from_old_map")]
map_dispose = objects[objects.index("void objects_dispose_from_old_map"):objects.index("void objects_dispose(")]
assert 'config_boolean("vr.dropped_magazines")' in spawn
assert 'game_connection() != _game_connection_local' in spawn
assert 'reload.kind != RELOAD_MAGAZINE' in spawn
assert "vr_mr_step" in reload and "previous_phase == VR_MR_OLD_HELD" in reload
assert "collision_move_sphere" in tick and "global_gravity" in tick
assert "game_connection() != _game_connection_local" in tick
assert "render_model(" in render and "0x5A000000 + index, 0, 0" in render
assert "_render_model_first_person_bit" not in render
assert "vr_manual_reload_debris_tick();" in objects
assert "vr_manual_reload_debris_render();" in renderer
assert re.search(r"else\s*\{\s*process_rendered_objects\(&data\);\s*#ifdef HALO_VR\s*[^}]*vr_manual_reload_debris_render\(\);", renderer)
assert state.count("vr_manual_reload_debris_reset();") >= 2
assert "vr_manual_reload_debris_reset();" in map_init
assert "vr_manual_reload_debris_reset();" in map_dispose
assert "weapon_magazine_finish_reload" not in spawn + tick + render
assert "VR_MAGAZINE_DEBRIS_LIFETIME_TICKS" not in reload
assert "static boolean dropped_magazines_have_state" in reload
reset = reload[reload.index("void vr_manual_reload_debris_reset"):reload.index("static void debris_spawn_from_reload")]
assert "if (!dropped_magazines_have_state) return;" in reset
assert "dropped_magazines_have_state = FALSE;" in reset
config = (ROOT / "port/linux/src/port_config.c").read_text()
menu = (ROOT / "port/linux/game/vr_menu.c").read_text()
assert re.search(r'"vr\.dropped_magazines",\s*_config_boolean,\s*"false"', config)
assert '"MAG DEBRIS", "vr.dropped_magazines"' in menu
print("PASS: visual-only offline spawn, native swept collision, persistent world-pass render, save/map lifecycle reset and no ammo mutation")
