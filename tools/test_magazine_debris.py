"""Exercise bounded magazine-debris policy and guard its native integration."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
build = ROOT / "build" / "magazine-debris-tests"
build.mkdir(parents=True, exist_ok=True)

c = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "vr_magazine_debris_math.h"
#include "vr_manual_reload_math.h"
int main(void) {
    int active[VR_MAGAZINE_DEBRIS_CAPACITY] = {0};
    assert(VR_MAGAZINE_DEBRIS_CAPACITY == 32);
    assert(vr_magazine_debris_choose_slot(active, VR_MAGAZINE_DEBRIS_CAPACITY) == 0);
    active[0] = active[1] = active[2] = 1;
    assert(vr_magazine_debris_choose_slot(active, VR_MAGAZINE_DEBRIS_CAPACITY) == 3);
    for (int i=3;i<VR_MAGAZINE_DEBRIS_CAPACITY;i++) active[i]=1;
    assert(vr_magazine_debris_choose_slot(active, VR_MAGAZINE_DEBRIS_CAPACITY) == -1);
    active[11]=0;
    assert(vr_magazine_debris_choose_slot(active, VR_MAGAZINE_DEBRIS_CAPACITY) == 11);
    assert(vr_magazine_debris_choose_slot(active, 0) == -1);
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
    assert(vr_magazine_debris_owner_after_state_restore(1, 17, -1) == -1);
    assert(vr_magazine_debris_owner_after_state_restore(1, -1, -1) == -1);
    assert(vr_magazine_debris_owner_after_state_restore(0, 17, -1) == 17);

    /* Join the real reload state machine to the production debris policy:
       the ejected clone is provisional until native ammo commits. */
    {
        struct vr_mr_state reload={.phase=VR_MR_NEED_MAG};
        struct vr_mr_input cancel={.valid=0,.held=1}; /* Test54: Reload no longer cancels; a weapon switch or tracking loss does */
        struct vr_magazine_debris_transaction tx;
        int drops[2]={0,0}, provisional[2]={0,0};
        vr_magazine_debris_transaction_init(&tx);
        assert(vr_magazine_debris_transaction_record(&tx,0));
        drops[0]=provisional[0]=1; /* rendered after VR_MR_DISCARD */
        assert(vr_mr_step(&reload,&cancel)==VR_MR_CANCEL);
        int removed=vr_magazine_debris_transaction_cancel(&tx);
        assert(removed==0&&provisional[removed]&&drops[removed]);
        drops[removed]=provisional[removed]=0;
        assert(!drops[0]&&reload.phase==VR_MR_IDLE); /* native ammo is unchanged */

        /* Weapon swap, tracking loss and checkpoint restore share the same
           cleanup. A successful reload keeps exactly one committed visual. */
        assert(vr_magazine_debris_transaction_record(&tx,1));
        drops[1]=provisional[1]=1;
        removed=vr_magazine_debris_transaction_cancel(&tx);assert(removed==1);
        drops[removed]=provisional[removed]=0;assert(!drops[1]);
        assert(vr_magazine_debris_transaction_record(&tx,0));
        drops[0]=provisional[0]=1;
        int committed=vr_magazine_debris_transaction_commit(&tx);
        assert(committed==0&&provisional[committed]);
        provisional[committed]=0;
        assert(drops[0]&&!provisional[0]);

        /* If ammo commit beats rendering, the later clone is born committed. */
        assert(vr_magazine_debris_transaction_commit(&tx)==-1);
        assert(!vr_magazine_debris_transaction_is_provisional(&tx));
        assert(!vr_magazine_debris_transaction_record(&tx,1));
        vr_magazine_debris_transaction_new_reload(&tx);
        assert(vr_magazine_debris_transaction_is_provisional(&tx));
    }
    puts("PASS: bounded map-session magazine pool, same-map restore owner rebasing, finite speed and fail-closed spawn bounds");
}
'''
src = build / "test.c"
exe = build / "test_magazine_debris"
src.write_text(c)
subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                "-fsanitize=address,undefined", "-I" + str(ROOT / "port/linux/game"),
                str(src), "-lm", "-o", str(exe)], check=True)
subprocess.run([str(exe)], check=True)

reload = (ROOT / "port/linux/game/vr_manual_reload.c").read_text()
objects = (ROOT / "source/objects/objects.c").read_text()
renderer = (ROOT / "source/render/render_objects.c").read_text()
state = (ROOT / "source/saved games/game_state.c").read_text()
spawn = reload[reload.index("static void debris_spawn_from_reload"):reload.index("void vr_manual_reload_debris_tick")]
tick = reload[reload.index("void vr_manual_reload_debris_tick"):reload.index("void vr_manual_reload_debris_render")]
render = reload[reload.index("void vr_manual_reload_debris_render"):reload.index("static boolean reload_hand_touches_part")]
map_init = objects[objects.index("void objects_initialize_for_new_map"):objects.index("void objects_dispose_from_old_map")]
map_dispose = objects[objects.index("void objects_dispose_from_old_map"):objects.index("void objects_dispose(")]
before_load = state[state.index("static void game_state_call_before_load_procs"):state.index("static void game_state_call_after_load_procs")]
after_load = state[state.index("static void game_state_call_after_load_procs"):state.index("void game_state_dispose")]
assert 'config_boolean("vr.dropped_magazines")' in spawn
assert 'config_boolean("vr.manual_reload")' in spawn
assert 'game_connection() != _game_connection_local' in spawn
assert 'reload.kind != RELOAD_MAGAZINE' in spawn
assert "vr_mr_step" in reload and "previous_phase == VR_MR_OLD_HELD" in reload
assert "debris_cancel_transaction();" in reload
assert "debris_commit_transaction();" in reload
assert "vr_magazine_debris_transaction_record(&reload.debris_transaction, slot_index)" in spawn
assert "slot->provisional = vr_magazine_debris_transaction_is_provisional" in spawn
assert "collision_move_sphere" in tick and "global_gravity" in tick
assert "game_connection() != _game_connection_local" in tick
assert "render_model(" in render and "0x5A000000 + index, 0, 0" in render
assert "_render_model_first_person_bit" not in render
assert "vr_manual_reload_debris_tick();" in objects
assert "vr_manual_reload_debris_render();" in renderer
assert re.search(r"else\s*\{\s*process_rendered_objects\(&data\);\s*#ifdef HALO_VR\s*[^}]*vr_manual_reload_debris_render\(\);", renderer)
assert "vr_manual_reload_debris_prepare_for_state_restore();" in before_load
assert before_load.index("vr_manual_reload_debris_prepare_for_state_restore();") < before_load.index("(*proc)();")
assert "vr_manual_reload_debris_reset();" not in before_load + after_load
assert "vr_manual_reload_debris_reset();" not in state
assert "vr_manual_reload_debris_reset();" in map_init
assert "vr_manual_reload_debris_reset();" in map_dispose
assert "weapon_magazine_finish_reload" not in spawn + tick + render
assert "VR_MAGAZINE_DEBRIS_LIFETIME_TICKS" not in reload
assert "oldest visual" not in reload
assert "existing drops retained, new visuals skipped" in reload
assert "memcpy(slot->colors, source_weapon->object.outgoing_change_colors" in spawn
assert "memcpy(slot->function_values, source_weapon->object.outgoing_function_values" in spawn
assert "object_try_and_get_and_verify_type(slot->weapon" not in render
assert "slot->colors, slot->function_values" in render
assert "static boolean dropped_magazines_have_state" in reload
reset = reload[reload.index("void vr_manual_reload_debris_reset"):reload.index("static void debris_spawn_from_reload")]
assert "if (dropped_magazines_have_state)" in reset
assert "dropped_magazines_have_state = FALSE;" in reset
config = (ROOT / "port/linux/src/port_config.c").read_text()
menu = (ROOT / "port/linux/game/vr_menu.c").read_text()
assert re.search(r'"vr\.dropped_magazines",\s*_config_boolean,\s*"false"', config)
assert '"MAG DEBRIS", "vr.dropped_magazines"' in menu
assert "VR_MAGAZINE_DEBRIS_CAPACITY = 32" in (ROOT / "port/linux/game/vr_magazine_debris_math.h").read_text()
print("PASS: visual-only offline spawn, native swept collision, retention across same-map state restores, clear on map lifecycle/disable/online, 32-slot no-eviction cap and no ammo mutation")
