"""Bound optional shake-cooling and weight-haptic math and isolation guards."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/vr-optional-feedback"
OUT.mkdir(parents=True, exist_ok=True)

c = r'''
#include <assert.h>
#include <math.h>
#include "vr_cooldown_shake_math.h"
#include "vr_weight_feedback_math.h"
int main(void) {
    assert(vr_cooldown_shake_multiplier(0.0f) == 1.0f);
    assert(vr_cooldown_shake_multiplier(0.9f) == 1.0f);
    assert(fabsf(vr_cooldown_shake_multiplier(1.8f) - 1.75f) < 0.0001f);
    assert(vr_cooldown_shake_multiplier(2.7f) == 2.5f);
    assert(vr_cooldown_shake_multiplier(NAN) == 1.0f);
    assert(vr_cooldown_shake_multiplier(INFINITY) == 1.0f);
    assert(vr_cooldown_shake_is_reversal(1.2f, 1.1f, -0.5f));
    assert(!vr_cooldown_shake_is_reversal(1.2f, 1.1f, 0.5f));
    assert(!vr_cooldown_shake_is_reversal(0.2f, 1.1f, -0.9f));
    assert(!vr_cooldown_shake_is_reversal(NAN, 1.1f, -0.9f));
    assert(vr_cooldown_shake_decay(2.0f, 0.0f) == 2.0f);
    assert(vr_cooldown_shake_decay(2.0f, 0.35f) < 0.75f);
    assert(vr_cooldown_shake_decay(NAN, 0.1f) == 0.0f);
    float light = vr_weight_feedback_amplitude(1.0f, 0.0f, 0.0f);
    float heavy = vr_weight_feedback_amplitude(0.12f, 0.0f, 0.0f);
    float strained = vr_weight_feedback_amplitude(0.5f, 0.35f, 0.0f);
    assert(light == 0.0f && heavy > 0.0f && strained > heavy);
    assert(vr_weight_feedback_amplitude(NAN, 1.0f, 1.0f) == 0.0f);
    assert(vr_weight_feedback_amplitude(0.0f, INFINITY, 0.0f) == 0.0f);
    assert(vr_weight_feedback_amplitude(0.0f, 5.0f, 20.0f) <= 0.24f);
}
'''
source = OUT / "feedback.c"
source.write_text(c, encoding="utf-8")
binary = OUT / "feedback"
subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-fsanitize=address,undefined", "-I", str(ROOT / "port/linux/game"),
                str(source), "-lm", "-o", str(binary)], check=True)
subprocess.run([str(binary)], check=True)

cool = (ROOT / "port/linux/game/vr_cooldown_shake.c").read_text(encoding="utf-8")
weapons = (ROOT / "source/items/weapons.c").read_text(encoding="utf-8")
config = (ROOT / "port/linux/src/port_config.c").read_text(encoding="utf-8")
menu = (ROOT / "port/linux/game/vr_menu.c").read_text(encoding="utf-8")
world = (ROOT / "port/linux/game/vr_world_interaction.c").read_text(encoding="utf-8")
assert 'config_boolean("vr.cooldown_shake")' in cool
assert 'game_connection()!=_game_connection_local' in cool
assert 'weapon_index!=current_weapon' in cool
assert 'vr_cooldown_shake_is_reversal(previous_speed,speed,direction_cosine)' in cool
assert 'shake.reversal_count>=2' in cool
assert 'vr_cooldown_shake_decay(shake.speed,(float)elapsed)' in cool
assert 'TEST_FLAG(weapon->weapon.flags, _weapon_overheated_bit)' in weapons
assert 'heat_loss *= vr_cooldown_shake_rate(weapon_index)' in weapons
assert '"vr.cooldown_shake", _config_boolean, "false"' in config
assert '"vr.weight_haptics", _config_boolean, "false"' in config
assert '"SHAKE COOLING", "vr.cooldown_shake"' in menu
assert '"WEIGHT HAPTICS", "vr.weight_haptics"' in menu
assert '"CUSTOM SCENERY", "vr.custom_scenery_grab"' in menu
assert '"CUSTOM NPC RIGS", "vr.custom_npc_rigs"' in menu
assert 'game_connection()!=_game_connection_local' in world
assert 'vr_haptic(hand,amplitude,0.12f)' in world
assert 'void vr_world_interaction_weight_feedback(int hand, float mobility,' in world
assert 'vr_world_interaction_weight_feedback(hand, mobility, (float)(strain / units), (float)speed);' in world
reset = world[world.index('void vr_world_interaction_reset(void)'):]
assert 'weight_haptic_at[0]=weight_haptic_at[1]=0' in reset
assert 'vr.cooldown_shake", _config_boolean, "false"' in config
assert 'vr.weight_haptics", _config_boolean, "false"' in config
assert 'vr.custom_scenery_grab", _config_boolean, "false"' in config
assert 'vr.custom_npc_rigs", _config_boolean, "false"' in config
print("PASS: shake cooling is bounded, selected-weapon-only, toggle-gated and offline-only; weight haptics are capped, toggle-gated and local-only")
