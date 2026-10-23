"""Test56 polish pass: pure math under ASan/UBSan, and the production wiring.

Owner's Test55 report (2026-10-11 logs and videos): bodies jittering and never
resting (tools/test_test56_ragdoll.py), every death falling the same way
whatever killed it, NPCs slow to get up after a ragdoll (at most 1 s), and the
vehicle, throwing and hand items listed in docs/TEST56-FIELD-GUIDE.md.
"""
from pathlib import Path
import subprocess
import tempfile

import network_expected as netv  # noqa: E402 (tools/: the versions this build hosts and joins)
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
assert "kick=blow.local*units/(real)TICKS_PER_SECOND;" in death  # Test59: after DEATH FORCE's burst
assert "MAX(want-along,0.0f)" in death, "the blow adds to the engine's own push, never doubles it"
assert "kick_mps=%.1f push_mps=%.1f lift_mps=%.1f explosion=%d force=%d" in death  # Test59: lift and DEATH FORCE logged
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

# Throwing: THROW 2X by default, the release peak for props and NPCs; a thrown
# thing shoves what it hits (before the damage, so a kill carries).
world = read("port/linux/game/vr_world_interaction.c")
impact = read("port/linux/game/vr_interaction_impact.c")
assert '{ "vr.throw_strength", _config_real, "2.0",' in config
assert 'npc_setting("vr.throw_strength",2.0f,0.75f,2.0f)' in npc
# Test66: props and vehicles throw at OBJECT THROW (2 as before; 0 lets them drop)
assert 'config_real("vr.object_throw")' in world and "isfinite(strength) && strength > 0.0" in world
assert "vr_world_throw_peak((float const (*)[3])npc.history[hand]" in npc
assert "vr_world_throw_peak((float const (*)[3])held->history" in world
collision = body(impact, "static void apply_collision(")
assert collision.index("impact_shove(target,victim,velocity,entries[i].mobility,units);") < collision.index("object_cause_contact_damage(&damage,target,")

# Heavy holds: the "heavy hold one hand" line only on a real let-go (it
# repeated ~100 times a test), the weight felt in the remaining hand, both
# hands buzz when the second takes a heavy body up.
release_body = body(npc, "static void release(")
assert "if(was_held && npc.active && npc.started && npc.held[1-hand] && npc.held[0]+npc.held[1]<npc.minimum_hands) {" in release_body
assert "if(!npc.is_remote) vr_haptic(1-hand,.45f,.08f);" in release_body
assert "if(!use_remote && npc.minimum_hands>1) {vr_haptic(0,.5f,.05f);vr_haptic(1,.5f,.05f);}" in npc
# LIFT (was NPC HOLD; same key) also for props, turrets and vehicles, relative
# to its 1.5 default so props are held as before by default
assert '{ "LIFT", "vr.npc_hold_strength",' in menu
assert 'vr_world_lift_strength((float)config_real("vr.npc_hold_strength"))' in world
# CHARGE GRAB: the charging handle's extra reach, 4 cm (Test55) by default
reload_source = read("port/linux/game/vr_manual_reload.c")
assert '{ "vr.charge_grab_radius", _config_real, "0.04",' in config and '"CHARGE GRAB", "vr.charge_grab_radius"' in menu
assert 'config_real("vr.charge_grab_radius")' in reload_source

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
# Test58: the wheel node in the world; node_matrix is the marker's local
# offset, which put the wheel at the map's origin in Test56/57
assert "center=nodes[markers[0].node_index].position;normal=nodes[markers[0].node_index].up;" in prepare
assert "center=markers[0].node_matrix.position" not in prepare
assert "contact_radius+=vr_wheel_profiles[vr_wheel.kind].extra-0.04f;" in handles  # Test57: per vehicle
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

# OpenCE Builds 189-190: 189 (Custom Edition map sharing) raises the network
# to 27; Test59 hosts OpenCE network 28 (Build 201), answering map sharing's
# requests as a host that shares none (network_distributed.c). Build 190's lobby fix
# (2059b6ce) is the host's alone: a machine joining or leaving (no player yet)
# no longer stops and restarts the countdown or holds the start; it joins the
# game in progress (network_game_server_start_late_joiner).
server = read("source/networking/network_server_manager.c")
limits = read("port/linux/include/halo_port_limits.h")
assert "#define HALO_PORT_NETWORK_VERSION %d" % netv.CURRENT in limits
# (Test66: map sharing itself, OpenCE Build 201's map_share.c: the server
# waits for a machine still downloading the map)
assert "map_share_machine_needs_map(" in server and '#include "map_share.h"' in server
countdown = body(server, "boolean server_ok_to_countdown(")
assert "server_has_a_player_on_each_machine" not in countdown and "server_has_enough_machines(server) &&" in countdown
precached = body(server, "static boolean network_game_server_have_all_machines_have_precached(\n\tstruct network_game_server *server)\n{")
# (Test66: and a machine still downloading the map, map_share.c, holds no start either)
assert ("if (!network_game_server_machine_has_players(server, machine->machine_index) ||\n"
        "\t\t\t\tmap_share_machine_needs_map(machine->machine_index))\n\t\t\t\tcontinue;") in precached

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "port/linux/game/vr_npc_impulse.h"
#include "port/linux/game/vr_world_math.h"
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
 /* throws: the hand's peak at release, not a lagging average: a swing that
  * peaks and slows as the grip opens throws at about its peak */
 {
  float history[VR_WORLD_THROW_HISTORY][3], peak[3], out[3];
  int count = 0, next = 0;
  float swing[6] = {.05f, .15f, .30f, .32f, .20f, .10f}; /* units a tick */
  for (int t = 0; t < 6; ++t) { float m[3] = {swing[t], 0, 0}; vr_world_throw_note(history, &count, &next, m); }
  assert(count == VR_WORLD_THROW_HISTORY && vr_world_throw_peak((float const (*)[3])history, count, peak));
  assert(fabsf(peak[0] - .31f) < 1e-5f); /* the two fastest of the last four */
  /* the old blend of the average (~.2) and the last tick (.1) threw ~.14 */
  assert(vr_world_throw_velocity_spartan(peak, peak, 2.0f, 1.0f, 1.0f, out) && out[0] > .4f);
  /* one noisy tick does not spike it */
  { float spike[VR_WORLD_THROW_HISTORY][3] = {{.1f,0,0},{.1f,0,0},{.1f,0,0},{.9f,0,0}};
    assert(vr_world_throw_peak((float const (*)[3])spike, 4, peak) && peak[0] == .5f); }
  { float bad[1][3] = {{NAN, 0, 0}}; assert(!vr_world_throw_peak((float const (*)[3])bad, 1, peak)); }
  assert(!vr_world_throw_peak((float const (*)[3])history, 0, peak));
 }
 /* LIFT for props: the default (1.5) holds them as before (1), IRON lifts harder */
 assert(fabsf(vr_world_lift_strength(1.5f) - 1.0f) < 1e-6f && vr_world_lift_strength(2.5f) > 1.6f && vr_world_lift_strength(0.75f) == 0.75f && vr_world_lift_strength(NAN) == 1.0f);
 puts("PASS: Test56 throws at the hand's release peak; LIFT for props");
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
print("PASS: Test56 wiring (shot-reactive death kicks; NPC recovery within 1 s; THROW 2X, release peak, impact shove; heavy-hold log once and haptics; LIFT for props; CHARGE GRAB; immersive vehicles steer the right way from the drawn pose, Warthog wheel node, steering apart from head aiming, grip pose)")
