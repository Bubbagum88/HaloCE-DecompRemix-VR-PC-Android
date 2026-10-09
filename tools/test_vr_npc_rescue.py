"""Run the rescue policy helpers without the game runtime or any game data."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "npc-rescue-test"
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = OUT / "npc_rescue_policy.c"
BINARY = OUT / "npc_rescue_policy"

SOURCE.write_text(r'''#include <assert.h>
#include <string.h>
#include "vr_npc_rescue.h"

static struct vr_npc_rescue_eligibility eligible_state(void)
{
    struct vr_npc_rescue_eligibility s;
    memset(&s, 1, sizeof(s));
    return s;
}

int main(void)
{
    struct vr_npc_rescue_eligibility e = eligible_state();
    struct vr_npc_rescue_timer timer = {0};
    long keys[3] = {-1, -1, -1};

    assert(vr_npc_rescue_is_eligible(&e));
    e.option_enabled = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.option_enabled = 1;
    e.local_game = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.local_game = 1;
    e.vr_active = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.vr_active = 1;
    e.game_ready = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.game_ready = 1;
    e.outside_cinematic = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.outside_cinematic = 1;
    e.actor_live = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.actor_live = 1;
    e.non_player = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.non_player = 1;
    e.actor_attached = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.actor_attached = 1;
    e.encounter_valid = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.encounter_valid = 1;
    e.squad_valid = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.squad_valid = 1;
    e.unparented = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.unparented = 1;
    e.not_in_vehicle = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_in_vehicle = 1;
    e.not_dead = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_dead = 1;
    e.not_flying = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_flying = 1;
    e.not_swarm = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_swarm = 1;
    e.not_movie_star = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_movie_star = 1;
    e.no_custom_animation = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.no_custom_animation = 1;
    e.no_script_ownership = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.no_script_ownership = 1;
    e.connected_to_map = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.connected_to_map = 1;
    e.collision_enabled = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.collision_enabled = 1;
    e.not_recording_possessed = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_recording_possessed = 1;
    e.not_deleted_when_deactivated = 0; assert(!vr_npc_rescue_is_eligible(&e)); e.not_deleted_when_deactivated = 1;
    assert(vr_npc_rescue_is_eligible(&e));

    /* Continuous dwell is required; stable contact resets the timer. */
    assert(!vr_npc_rescue_timer_due(&timer, 0, 1, 300, 60));
    assert(!vr_npc_rescue_timer_due(&timer, 299, 1, 300, 60));
    assert(vr_npc_rescue_timer_due(&timer, 300, 1, 300, 60));
    assert(!vr_npc_rescue_timer_due(&timer, 359, 1, 300, 60));
    assert(vr_npc_rescue_timer_due(&timer, 360, 1, 300, 60));
    assert(!vr_npc_rescue_timer_due(&timer, 361, 0, 300, 60));
    assert(!timer.unsupported_active && !timer.attempt_valid);
    assert(!vr_npc_rescue_timer_due(&timer, 362, 1, 300, 60));
    assert(!vr_npc_rescue_timer_due(&timer, 661, 1, 300, 60));
    assert(vr_npc_rescue_timer_due(&timer, 662, 1, 300, 60));

    /* A rewind restarts the dwell; explicit invalidation clears all timer data. */
    assert(vr_npc_rescue_tick_went_backwards(1, 662, 12));
    assert(!vr_npc_rescue_tick_went_backwards(1, 12, 12));
    assert(!vr_npc_rescue_tick_went_backwards(0, 662, 12));
    assert(!vr_npc_rescue_timer_due(&timer, 12, 1, 300, 60));
    vr_npc_rescue_timer_invalidate(&timer);
    assert(!timer.unsupported_active && !timer.attempt_valid &&
           timer.unsupported_since == 0 && timer.last_attempt == 0);

    /* Slot lookup reuses exact identities and refuses a full pool. */
    assert(vr_npc_rescue_slot_index(keys, 3, 17, -1) == 0);
    keys[0] = 17;
    assert(vr_npc_rescue_slot_index(keys, 3, 17, -1) == 0);
    keys[1] = 18; keys[2] = 19;
    assert(vr_npc_rescue_slot_index(keys, 3, 20, -1) == -1);
    keys[1] = -1;
    assert(vr_npc_rescue_slot_index(keys, 3, 20, -1) == 1);
    assert(vr_npc_rescue_slot_index(keys, 3, -1, -1) == -1);
    return 0;
}
''', encoding="utf-8")

subprocess.run(
    [
        "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-I", str(ROOT / "port" / "linux" / "game"),
        str(SOURCE), "-o", str(BINARY),
    ],
    check=True,
)
subprocess.run([str(BINARY)], check=True)

# Production integration contract: the option is a separate, default-off,
# local VR feature; eligible actors keep native AI state and only move after a
# grounded-pose, capsule and dwell check. Lifecycle resets are mandatory.
rescue = (ROOT / "port/linux/game/vr_npc_rescue.c").read_text(encoding="utf-8")
config = (ROOT / "port/linux/src/port_config.c").read_text(encoding="utf-8")
menu = (ROOT / "port/linux/game/vr_menu.c").read_text(encoding="utf-8")
objects = (ROOT / "source/objects/objects.c").read_text(encoding="utf-8")
state = (ROOT / "source/saved games/game_state.c").read_text(encoding="utf-8")
assert 'config_boolean("vr.npc_rescue")' in rescue
assert 'game_connection() == _game_connection_local' in rescue
assert "VR_NPC_RESCUE_DWELL_TICKS = 10 * TICKS_PER_SECOND" in rescue
assert "biped_approximate_surface_index" in rescue
assert "collision_test_pill" in rescue
assert "object_set_position(" in rescue
assert "object_activate(object_index)" in rescue
for forbidden in ("object_reset(", "unit_port_resurrect(", "actor_set_active(",
                  "unit_interaction_recover(", "actor_move_halt(", "network_send("):
    assert forbidden not in rescue, f"rescue must preserve native mission/AI state: {forbidden}"
assert re.search(
    r'"vr\.npc_rescue",\s*_config_boolean,\s*"false",\s*"HALO_VR_NPC_RESCUE"', config
), "rescue must be default-off"
assert '"NPC RESCUE", "vr.npc_rescue"' in menu
assert objects.count("vr_npc_rescue_reset();") >= 2, "rescue state must reset on map init/disposal"
assert "vr_npc_rescue_tick();" in objects
assert state.count("vr_npc_rescue_reset();") >= 2, "rescue IDs/timers must reset around game-state loads"
assert "#include \"vr_npc_rescue.h\"" in objects and "#include \"vr_npc_rescue.h\"" in state
print("PASS: NPC rescue production gates, native AI preservation, grounded capsule placement and map/save lifecycle integration")
