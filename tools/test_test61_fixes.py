"""Test61: the owner's Test60 session (2026-10-12 08:09 log, The Silent Cartographer).

- Slamming and throwing marines still did no damage: the blow read only the
  player unit's own melee damage, which the Master Chief does not have, and
  returned unseen (vr_interaction_impact.c; behaviour: test_interaction_impact).
- Some enemies did not ragdoll on explosions: every NPC RIG SLOT taken (8,
  corpses settling up to 5 s); now 24 slots, and a death that still finds them
  taken takes the slot of the corpse settled longest; a skipped death says why.
- Dead Elites and Hunters lift with one hand (two only while alive).
- The gun stopped firing with ammo: a menu closed with the button still held,
  27 ms later read as a reload press that ejected the magazine (8 s blocked).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
impact = read("port/linux/game/vr_interaction_impact.c")
npc = read("port/linux/game/vr_npc_interaction.c")
header = read("port/linux/game/vr_npc_interaction.h")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")
frame = read("port/linux/src/vr_frame.c")

# the blow: the engine's own unarmed melee lookup
assert "blow=unit_unarmed_melee_damage(entries[i].owner);" in impact
assert impact.count("damage_data_new(&damage,blow);") == 2 and "melee_damage.index" not in impact

# 24 rig slots, by default too; the menu offers up to 24
assert "#define VR_NPC_INTERACTION_POOL_SIZE 24" in header
assert '{ "vr.npc_max_ragdolls", _config_integer, "24",' in config
assert '{ "24", "vr.npc_max_ragdolls=24" } } }' in menu
# a death with every slot taken takes the longest-settled corpse's (1 s at
# least, never a held or remote one); a skipped death is logged with its reason
corpse = npc[npc.index("static struct npc_state *npc_corpse_slot(void)"):]
corpse = corpse[:corpse.index("\n}\n")]
for part in ("state->death", "!state->is_remote", "!state->held[0] && !state->held[1]", "state->settling>=30",
             "biped_start_limp_body_physics(index);", "reset_one();"):
    assert part in corpse, part
assert 'if(!(state=free_state()) && !(state=npc_corpse_slot())) {npc_death_skipped(index,"every-rig-slot-busy");return;}' in npc
assert 'npc_death_skipped(index,"farther-than-40m")' in npc and '"unsupported-species"' in npc

# dead bodies lift with one hand
profile = npc[npc.index("static int interaction_profile("):]
profile = profile[:profile.index("\n}\n")]
assert "TEST_FLAG(unit->object.damage_flags,_object_dead_bit)) *hands=1;" in profile
assert "npc.recovery=0;npc.minimum_hands=1;}" in npc

# a button held as a menu closes is not a reload until let go
action = frame[frame.index("int vr_manual_reload_action_down(void)"):]
action = action[:action.index("\n}\n")]
assert "if (vr.reload_held_from_menu)\n\t\treturn 0;" in action
assert "if (menus_active && (vr.pad_buttons & HALO_XR_BUTTON_X))\n\t\tvr.reload_held_from_menu = 1;" in frame
print("PASS: Test61 fixes (impacts use the unarmed melee blow; 24 rig slots and a corpse's slot for a new death, skipped deaths logged; dead Elites and Hunters one-handed; a menu's held button is no reload)")
