"""Test59: the owner's 2026-10-12 05:36 session (log, video 05:48:10).

1. Manual reload. Twice a magazine was pulled out and held at the well for
   about three seconds (sniper 05:48:14-17, assault rifle 05:49:20-23; video
   70-73 s): the gun could not fire, and only a magazine from a pouch went in.
   The gun's own magazine now goes back in: pulled and brought back (gripped,
   or let go at the well), or taken back up where it dropped (DROPPED MAGS
   draws it). It reseats with nothing committed: the ammo never moved (only a
   replacement's commit changes it), and the gun fires again. The state
   machine is checked in test_manual_reload.py.
2. Reload jitter while walking. The magazine well is read from the gun as
   drawn each frame, but the free hand (contacts, the held magazine and the
   hand pulled onto it) was placed from the game tick's camera: walking, the
   two were up to a tick of the walk apart, stepping each tick. Both now come
   from the camera the frame was drawn from.
3. Death ragdolls barely moved when shot (an assault rifle bullet's whole-body
   push was 0.04 m/s) and explosions threw them little. DEATH FORCE (STRONG
   by default, CLASSIC is Test56's, HUGE) throws a body back along the shots
   as hard as the burst that killed it and away from blasts with lift.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")

# --- 1/2: reload wiring
reload = read("port/linux/game/vr_manual_reload.c")
update = reload[reload.index("unsigned vr_manual_reload_update(long weapon_index, int explicit_reload)"):]
update = update[:update.index("\n}\n")]
assert "if (!vr_render_drawn_camera(camera.n)) unit_get_camera_position(unit_index, &camera);" in update
assert update.index("vr_render_drawn_camera(camera.n)") < update.index("vr_hand_world(hand_index, camera.n, hand.n, forward.n, up.n)")
model = reload[reload.index("void vr_manual_reload_model(long weapon_index, long model_index, real_matrix4x3 *matrices)"):]
assert model.index("if (vr_render_drawn_camera(drawn.n)) reload.camera = drawn;") < model.index("reload_refresh_held_pose();")
render = read("port/linux/game/vr_render.c")
drawn = render[render.index("int vr_render_drawn_camera(float position[3])"):]
drawn = drawn[:drawn.index("\n}\n")]
assert "vr_render.game_camera_position" in drawn and "age <= 0.25" in drawn and "vr_render.cinematic_view" in drawn
assert "vr_render.game_camera_time = vr_pose_time();" in render
# the hands are drawn from that camera, as is the gun
assert "vr_hand_pose(controller, vr_render.game_camera_position.n, hand.n, f.n, u.n)" in render
assert "vr_weapon_view(vr_render.game_camera_position.n, position.n, forward.n, up.n)" in render
# the own magazine back: returned (4 cm clear, 3 cm and lined up), taken back up
assert "if (!reload_component_bounds_touch(&reload.socket,&reload.held,0.04f*units)) reload.pulled_clear = TRUE;" in update
assert "reload_component_bounds_touch(&reload.socket,&reload.held,0.03f*units) &&\n            (reload.pulled_clear || !input.held);" in update
assert "input.near_dropped = distance_squared3d(&hand, &dropped_magazines[slot_index].center) <= reach * reach;" in update
assert "event == VR_MR_BEGIN || event == VR_MR_PICKUP || event == VR_MR_CHARGE || event == VR_MR_RECOVER" in update
assert "lying = dropped_magazines[slot_index].matrices[reload.magazine];" in update
assert "else if (event == VR_MR_DISCARD && previous_phase == VR_MR_NEW_HELD && previous_own)" in update
assert "the gun's own magazine went back in weapon=%ld rounds=%d; ammo unchanged" in update
# a reseat never commits: the only native ammo change stays the commit flag
assert "(event == VR_MR_COMMIT ? commit_flag : 0)" in read("port/linux/game/vr_manual_reload_math.h")
dropped = reload[reload.index("static int reload_dropped_slot(void)"):]
dropped = dropped[:dropped.index("\n}\n")]
assert "!slot->provisional" in dropped and "slot->model != reload.model" in dropped

# --- 3: DEATH FORCE
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")
assert '{ "vr.death_force", _config_string, "\\"strong\\"",' in config
assert '{ "DEATH FORCE", "vr.death_force", _vr_setting_string, 3, { { "CLASSIC", "classic" }, { "STRONG", "strong" }, { "HUGE", "huge" } } }' in menu
assert menu.count("VR_IMMERSION_DEATH_FORCE,") == 2
npc = read("port/linux/game/vr_npc_interaction.c")
assert "vr_npc_hit_kick_force(damage,acceleration,category,area,vr_units_per_metre(),npc_death_force(),&hit)" in npc
assert "if(!area && category!=VR_NPC_HIT_CATEGORY_MELEE && !(acceleration>0.0f)) npc_note_burst(object,damage);" in npc
death = npc[npc.index("void vr_npc_interaction_death(long index)"):]
assert "real burst=vr_npc_burst_body(npc_burst_damage(index),npc_death_force());" in death
assert death.index("vr_npc_burst_body(") < death.index("kick=blow.local*units/(real)TICKS_PER_SECOND;")

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "port/linux/game/vr_npc_impulse.h"
static const float units = 0.32808399f;
static int near(float a, float b, float e) { return fabsf(a - b) <= e; }
int main(void)
{
 struct vr_npc_hit classic, strong, huge;
 float burst;
 /* CLASSIC is Test56's exactly */
 assert(vr_npc_hit_kick_force(10, 0, 2, 0, units, VR_NPC_FORCE_CLASSIC, &strong) && vr_npc_hit_kick(10, 0, 2, 0, units, &classic));
 assert(strong.local == classic.local && strong.body == classic.body && strong.lift == classic.lift);
 assert(vr_npc_burst_body(70, VR_NPC_FORCE_CLASSIC) == 0.0f);
 assert(vr_npc_hit_kick_force(120, 4, 3, 1, units, VR_NPC_FORCE_CLASSIC, &strong) && near(strong.body, 4.27f, .05f));
 /* names: unknown or missing is STRONG */
 assert(vr_npc_force_from_name("classic") == VR_NPC_FORCE_CLASSIC && vr_npc_force_from_name("huge") == VR_NPC_FORCE_HUGE);
 assert(vr_npc_force_from_name("strong") == VR_NPC_FORCE_STRONG && vr_npc_force_from_name(0) == VR_NPC_FORCE_STRONG && vr_npc_force_from_name("x") == VR_NPC_FORCE_STRONG);
 /* a bullet: joints a quarter harder, the body's push from the burst */
 assert(vr_npc_hit_kick_force(10, 0, 2, 0, units, VR_NPC_FORCE_STRONG, &strong));
 assert(near(strong.local, 1.1f * 1.25f, .01f));
 /* an assault rifle's killing burst: 15 rounds a second, a round every 2 ticks */
 burst = 0; for (int shot = 0; shot < 4; ++shot) burst = vr_npc_burst_add(burst, shot ? 2 : 0, 10);
 assert(burst > 30 && burst < 40);
 assert(vr_npc_burst_body(burst, VR_NPC_FORCE_STRONG) > 2.2f && vr_npc_burst_body(70, VR_NPC_FORCE_STRONG) > 3.5f);
 assert(near(vr_npc_burst_body(70, VR_NPC_FORCE_STRONG), 3.65f, .01f) && near(vr_npc_burst_body(101, VR_NPC_FORCE_STRONG), 4.735f, .01f));
 assert(vr_npc_burst_body(1000, VR_NPC_FORCE_STRONG) == 5.0f && vr_npc_burst_body(1000, VR_NPC_FORCE_HUGE) == 8.0f);
 assert(near(vr_npc_burst_body(70, VR_NPC_FORCE_HUGE), 3.65f * 1.6f, .01f));
 assert(near(vr_npc_burst_lift(3.65f), .5475f, .001f) && vr_npc_burst_lift(0) == 0.0f && vr_npc_burst_lift(NAN) == 0.0f);
 /* 30 times the old 0.04 m/s for a rifle bullet that kills */
 assert(vr_npc_burst_body(10, VR_NPC_FORCE_STRONG) >= 30 * 0.04f);
 /* the burst decays over half a second and forgets after it */
 assert(vr_npc_burst_add(100, 0, 0) == 100 && vr_npc_burst_add(100, 15, 0) > 0 && vr_npc_burst_add(100, 16, 0) == 0);
 assert(vr_npc_burst_add(100, 8, 0) < 100 && vr_npc_burst_add(100, -1, 5) == 5 && vr_npc_burst_add(NAN, 2, 5) == 5);
 assert(vr_npc_burst_add(0, 0, -3) == 0 && vr_npc_burst_add(0, 0, INFINITY) == 0);
 /* explosions: frag ~7.3 m/s with ~3.7 lift, rocket ~11, HUGE half again, capped */
 assert(vr_npc_hit_kick_force(120, 4, 3, 1, units, VR_NPC_FORCE_STRONG, &strong));
 assert(near(strong.body, 7.315f, .05f) && near(strong.lift, strong.body * .5f, .001f) && strong.local == 2.0f);
 assert(vr_npc_hit_kick_force(330, 6, 4, 1, units, VR_NPC_FORCE_STRONG, &strong) && near(strong.body, 10.97f, .05f));
 assert(vr_npc_hit_kick_force(330, 6, 4, 1, units, VR_NPC_FORCE_HUGE, &huge) && near(huge.body, 16.0f, .001f));
 assert(vr_npc_hit_kick_force(120, 4, 3, 1, units, VR_NPC_FORCE_HUGE, &huge) && near(huge.body, 7.315f * 1.5f, .05f));
 /* far from the blast, little */
 assert(vr_npc_hit_kick_force(24, .8f, 3, 1, units, VR_NPC_FORCE_STRONG, &strong) && strong.body < 1.5f);
 /* melee: twice Test56's push, a little lift */
 assert(vr_npc_hit_kick_force(45, 9, 6, 0, units, VR_NPC_FORCE_STRONG, &strong) && vr_npc_hit_kick(45, 9, 6, 0, units, &classic));
 assert(near(strong.body, fminf(2 * classic.body, 3.0f), .01f) && strong.lift > 0);
 /* bad input is refused as before */
 assert(!vr_npc_hit_kick_force(NAN, 0, 2, 0, units, VR_NPC_FORCE_STRONG, &strong));
 assert(!vr_npc_hit_kick_force(1, 0, 2, 0, 0, VR_NPC_FORCE_STRONG, &strong));
 puts("PASS: DEATH FORCE: CLASSIC as Test56; STRONG rifle bursts 2.5-3.7 m/s back with lift, sniper 4.7, frag 7.3, rocket 11.0 m/s; HUGE more, capped; bursts decay in half a second");
 return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "t.c").write_text(code, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", "-I", str(ROOT),
                    str(path / "t.c"), "-o", str(path / "t"), "-lm"], check=True)
    subprocess.run([str(path / "t")], check=True)
print("PASS: Test59 reload (the gun's own magazine back in, hands from the drawn camera) and DEATH FORCE wiring")
# Test59: a blast's own throw kept up to 12 m/s with DEATH FORCE (the 05:37
# log's explosion deaths were all clipped to speed_mps=9.00)
assert "capture_limit=.40f;" in death and "if(!vr_world_limit(velocity.n,capture_limit*units))velocity=*global_zero_vector3d;" in death
assert death.index("capture_limit=.40f;") > death.index("npc_death_force()>VR_NPC_FORCE_CLASSIC")
print("PASS: Test59 explosion deaths keep up to 12 m/s of the engine's own throw with DEATH FORCE")
