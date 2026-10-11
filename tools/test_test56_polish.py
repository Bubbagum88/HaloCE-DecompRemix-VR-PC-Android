"""Test56 polish pass: pure math under ASan/UBSan, and the production wiring.

Owner's Test55 report (2026-10-11 logs and videos): bodies jittering and never
resting (tools/test_test56_ragdoll.py), every death falling the same way
whatever killed it, NPCs slow to get up after a ragdoll (at most 1 s), and the
vehicle, throwing and hand items listed in docs/TEST56-FIELD-GUIDE.md.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
npc = read("port/linux/game/vr_npc_interaction.c")
damage = read("source/objects/damage.c")


def body(text, start):
    at = text.index(start)
    depth = 0
    for i in range(text.index("{", at), len(text)):
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return text[at:i + 1]
    raise AssertionError(start)


# Shot-reactive deaths: the damage hook passes the effect's damage, push,
# category and explosion flag (after the effect is looked up); the death kick
# uses them instead of one fixed 2.2 m/s.
hook = damage[damage.index("damage_effect = damage_effect_definition_get(damage->definition_index);"):]
assert hook.index("vr_npc_interaction_note_damage(") < hook.index("damage_was_modified = FALSE;")
assert "damage_definition->damage_upper_bound * damage->scale" in hook
assert "damage_definition->instantaneous_acceleration * damage->scale" in hook
assert "TEST_FLAG(damage->flags, _damage_area_of_effect_bit)" in hook
death = body(npc, "void vr_npc_interaction_death(long index)")
assert "2.2f*units" not in death
assert "real kick=blow.local*units/(real)TICKS_PER_SECOND" in death
assert "MAX(want-along,0.0f)" in death, "the blow adds to the engine's own push, never doubles it"
assert "kick_mps=%.1f push_mps=%.1f explosion=%d" in death
note = body(npc, "void vr_npc_interaction_note_damage(")
assert "vr_npc_hit_add(&npc_damage_notes[last].hit,&hit);" in note, "pellets in one tick add up"

# NPC recovery: a living NPC lies limp at most NPC RECOVERY (default and
# maximum 1 s), getting up sooner once at rest; corpses keep the 5 s settle.
menu = read("port/linux/game/vr_menu.c")
config = read("port/linux/src/port_config.c")
assert 'npc_setting("vr.npc_recovery",1.0f,0.25f,1.0f)*(real)TICKS_PER_SECOND' in npc
assert "int limit=dead?NPC_SETTLE_LIMIT_TICKS:npc_recovery_ticks(),rest=dead?30:MIN(10,limit);" in npc
assert "overdue=npc.settling>=limit;" in npc and "(npc.settling>=rest && maximum<" in npc
assert "NPC_RECOVERY_BLEND_TICKS=12," in npc and "npc.recovery=NPC_RECOVERY_BLEND_TICKS;" in npc
assert "NPC_HANDOFF_LIMIT_TICKS=9 " in npc and "NPC_SETTLE_LIMIT_TICKS=150," in npc
assert '{ "vr.npc_recovery", _config_real, "1.0",' in config
assert '"NPC RECOVERY", "vr.npc_recovery", _vr_setting_real, 4,' in menu and '{ "1 S", "1.0" } } }' in menu
advanced = menu[menu.index("\t/* ADVANCED */"):menu.index("static struct vr_menu_section const vr_menu_immersion_sections")]
assert "VR_IMMERSION_NPC_RECOVERY," in advanced and '{ "ADVANCED", 8 }' in menu

# Immersive vehicles (only with IMMERSIVE VEHICLE on: every path goes through
# vr_vehicle_handles_enabled, which reads vr.vehicle_handles).
handles = read("port/linux/game/vr_vehicle_handles.h")
render = read("port/linux/game/vr_render.c")
players = read("source/game/players.c")
assert 'config_boolean("vr.vehicle_handles")' in body(handles, "static int vr_vehicle_handles_enabled(")
# right is right (Test55 added the turn to the heading: inverted everywhere)
assert "real yaw=vr_yaw(&vr_wheel.simulated_forward)-steer;" in handles
# the controls sit on the vehicle as drawn (the stutter and the hands off the
# Warthog's wheel: the latest tick's pose ran a tick ahead of the drawn one)
assert "render_interpolation_object_node_matrices(vr_wheel.vehicle)" in body(handles, "static void vr_wheel_drawn_refresh(")
assert "vr_wheel_drawn_refresh();" in body(handles, "static int vr_vehicle_handles_hand(")
assert "vr_wheel_drawn_refresh();" in body(handles, "boolean vr_render_vehicle_controls(")
# the Warthog's wheel: its own node's centre and leaning plane
prepare = body(handles, "static int vr_vehicle_handles_prepare(")
assert "center=markers[0].node_matrix.position;normal=markers[0].node_matrix.up;" in prepare
assert "if(vr_wheel.kind==0) contact_radius+=0.02f;" in handles
# steering apart from aiming: the controls give the driver's facing, the
# head the aiming (the Ghost's and Banshee's guns, the Scorpion's turret);
# an online client keeps Test55's facing from the controls
assert "vr_vehicle_handles_facing(player->unit_index, control_data.facing_vector.n);" in players
assert players.index("control_data.looking_vector = control_data.aiming_vector;") < players.index("vr_vehicle_handles_facing(player->unit_index")
facing = body(render, "void vr_player_control_facing(")
assert "int hand_may_aim = handles ? 0 : vr_vehicle_aim_source();" in facing
assert "if (!vr_vehicle_steering_split()) forward = steering;" in facing
assert "return game_connection()!=_game_connection_network_client;" in handles
# hands grip the controls (and magazines) over a tenth of a second, even
# without finger tracking, and ease back to the tracked fingers
assert "grip_blend[controller] = PIN(grip_blend[controller] + (gripping ? step : -step) / 0.12f, 0.0f, 1.0f);" in render
assert "if (tracked_fingers || grip_blend[controller] > 0.0f)" in render

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "port/linux/game/vr_npc_impulse.h"
static const float units = 0.32808399f;
int main(void)
{
 struct vr_npc_hit ar, pistol, sniper, elite, hunter, frag, rocket, far, total;
 /* stock Xbox damage effects: damage upper bound, instantaneous acceleration */
 assert(vr_npc_hit_kick(10, 0, 2, 0, units, &ar));        /* assault rifle bullet */
 assert(vr_npc_hit_kick(25, 0, 2, 0, units, &pistol));    /* pistol bullet */
 assert(vr_npc_hit_kick(101, 0, 5, 0, units, &sniper));   /* sniper bullet */
 assert(vr_npc_hit_kick(35, 2.5f, 6, 0, units, &elite));  /* Elite melee */
 assert(vr_npc_hit_kick(45, 9, 6, 0, units, &hunter));    /* Hunter melee */
 assert(vr_npc_hit_kick(120, 4, 3, 1, units, &frag));     /* frag grenade, at the blast */
 assert(vr_npc_hit_kick(330, 6, 4, 1, units, &rocket));   /* rocket */
 assert(vr_npc_hit_kick(120 * .2f, 4 * .2f, 3, 1, units, &far)); /* frag, far out */
 /* heavier rounds snap harder; bullets barely move the whole body */
 assert(ar.local >= 1.0f && ar.local < pistol.local && pistol.local < sniper.local && sniper.local <= 4.5f);
 assert(ar.body < .1f && sniper.body <= .5f && ar.lift == 0);
 /* melee shoves: a Hunter's blow harder than an Elite's */
 assert(elite.local > pistol.local && hunter.local > elite.local && hunter.local <= VR_NPC_HIT_LOCAL_MAXIMUM);
 assert(hunter.body > elite.body && hunter.body <= 1.5f);
 /* explosions throw the body with lift, a rocket harder than a grenade, less
  * far from the blast, never beyond 7 m/s */
 assert(frag.body > 3 && rocket.body > frag.body && rocket.body <= 7.0f && frag.lift > 1);
 assert(far.body < frag.body * .3f);
 /* shotgun pellets in one tick add up, capped */
 float rifle = ar.local;
 total = ar; for (int i = 0; i < 15; ++i) vr_npc_hit_add(&total, &ar);
 assert(total.local == VR_NPC_HIT_LOCAL_MAXIMUM);
 /* refusals */
 assert(!vr_npc_hit_kick(NAN, 0, 2, 0, units, &ar) && !vr_npc_hit_kick(1, INFINITY, 2, 0, units, &ar));
 assert(!vr_npc_hit_kick(1, 0, 2, 0, 0, &ar) && !vr_npc_hit_kick(1, 0, 2, 0, units, 0));
 assert(vr_npc_hit_kick(-5, -1, 2, 0, units, &ar) && ar.local == 1.0f);
 printf("PASS: Test56 shot-reactive deaths (rifle %.1f, pistol %.1f, sniper %.1f, Hunter melee %.1f m/s; frag throws %.1f, rocket %.1f m/s)\n",
     rifle, pistol.local, sniper.local, hunter.local, frag.body, rocket.body);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test56-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-I", str(ROOT),
                    str(path / "check.c"), "-o", str(path / "check"), "-lm"], check=True)
    subprocess.run([str(path / "check")], check=True)
print("PASS: Test56 wiring (shot-reactive death kicks; NPC recovery within 1 s; immersive vehicles steer the right way from the drawn pose, Warthog wheel node, steering apart from head aiming, grip pose)")
