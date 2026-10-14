"""Test54 refinement: hold/throw/body-touch/climb/melee math and their wiring.

Owner report (2026-10-11 logs and videos): no replacement magazine source,
Marines and other NPCs not grabbable (every miss had collision_candidates=0 at
the 4 cm palm radius), climbing misses on sloped rock, open-hand swings making
melee blows, contorted fingers against walls, thrown bodies vanishing, the
assault rifle's operating handle sliding while walking. This suite runs the
pure math with assertions under ASan/UBSan and pins the production wiring.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
npc = read("port/linux/game/vr_npc_interaction.c")
world = read("port/linux/game/vr_world_interaction.c")
parkour = read("port/linux/game/vr_parkour.c")
frame = read("port/linux/src/vr_frame.c")
render = read("port/linux/game/vr_render.c")
fpw = read("source/interface/first_person_weapons.c")
units = read("source/units/units.c")
native = read("port/linux/game/vr_articulated_native.c")
config = read("port/linux/src/port_config.c")

# NPC acquisition: authored collision model first, then live bone capsules.
assert "model_node=(short)npc_body_touch(probe_rig,&probe,body_reach,units," in npc
# Test67: a combat pose is drawn only: the hand on the drawn body is looked
# for on Halo's own pose, local hands only; the hold follows the hand
assert "if(!use_remote)vr_combat_drawn_to_native(it.index,&point,&probe);" in npc
assert "npc.target[h]=npc.previous[h]=point;" in npc
assert 'npc_setting("vr.npc_grab_assist",0.10f,0.0f,0.25f)' in npc  # Test66: from the body's surface, to 25 cm
assert "body_capsule_hits=%d" in npc
# Hold strength and throws.
assert 'npc_setting("vr.npc_hold_strength",1.5f,0.75f,2.5f)' in npc
assert "vr_world_throw_velocity_spartan(have_peak?peak.n:npc.velocity[hand].n,have_peak?peak.n:npc.last_delta[hand].n," in npc  # Test55: Spartan class; Test56: release peak
assert "vr_world_throw_velocity_spartan(have_peak ? peak.n : held->velocity.n, have_peak ? peak.n : held->last_change.n," in world  # Test55; Test56: release peak
# Released bodies: the root follows the pelvis; the rig is not dragged by it.
assert "npc_begin_root_follow();" in npc
assert "if(!(npc.root_follow&&npc.settling&&!npc.held[0]&&!npc.held[1]))" in npc
# Death ragdolls: hooked at death, gated by its own setting, survive NPC GRAB off.
assert "if (!feigned && !vr_player_body)\n\t\tvr_npc_interaction_death(unit_index);" in units
assert "boolean vr_player_body = unit->unit.player_index != NONE;" in units
assert 'config_boolean("vr.death_ragdolls")' in npc
assert '(npc.death&&config_boolean("vr.death_ragdolls"))' in npc
assert '{ "vr.death_ragdolls", _config_boolean, "false"' in config
# Mass by carried joints.
assert "inverse_mass=1.0f/(1.0f+0.35f*(real)below[n])" in native
# Climbing: radius setting, through-the-wall hold, slopes/ledges, grace.
assert "parkour_grab_through(unit,&camera,&point,parkour_grab_radius(units),waist_z,&hit)" in parkour
assert "parkour.hand[hand].grace=VR_PK_GRIP_GRACE_TICKS" in parkour
# Melee: open hand never strikes with a grab/climb feature on.
assert "vr_melee_hand_permitted(vr.melee_requires_fist || config_boolean(\"vr.assisted_combat\")," in frame
# Hands: controller authority and eased finger contact.
assert "real_point3d tracked_hand = hand;" in render
assert "real length, limit = (vehicle_grip ? 0.10f : 0.06f) * units;" in render
assert "t = *state_t * (1.0f - ease);" in render
# First-person gun parts keep the gun's pose through walking/sway overlays.
assert fpw.count("vr_first_person_parts_save(first_person_weapon, animation_graph);") == 2
assert fpw.count("vr_first_person_parts_restore(first_person_weapon, model, animation_graph);") == 2
moving = fpw.index("if (first_person_weapon->moving_animation.index!=NONE)\n\t\t\t\t{\n\t\t\t\t\tstruct animation *moving_animation")
assert fpw.rindex("vr_first_person_parts_save", 0, moving) > fpw.rindex("firing_animation_index", 0, moving)

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "port/linux/game/vr_world_math.h"
#include "port/linux/game/vr_parkour_math.h"
#include "port/linux/game/vr_sprint_melee_math.h"
int main(void){
 const float units=0.32808399f, g=0.0f;
 /* hold strength: a stronger hold follows the same error faster */
 { float error[3]={0.1f*units,0,0},zero[3]={0,0,0},weak[3],strong[3],stock[3];
   assert(vr_world_spring(error,zero,.5f,1,units,g,stock));
   assert(vr_world_spring_strength(error,zero,.5f,1,units,g,1.0f,weak));
   assert(fabsf(weak[0]-stock[0])<1e-6f); /* strength 1 is the stock spring */
   assert(vr_world_spring_strength(error,zero,.5f,1,units,g,2.5f,strong));
   assert(strong[0]>weak[0]*1.5f);
   /* an Elite (low mobility) still lags a Grunt at the same strength */
   float elite[3];assert(vr_world_spring_strength(error,zero,.25f,1,units,g,1.5f,elite));
   float grunt[3];assert(vr_world_spring_strength(error,zero,.5f,1,units,g,1.5f,grunt));
   assert(elite[0]<grunt[0]);
   float bad[3];assert(!vr_world_spring_strength(error,zero,NAN,1,units,g,1.5f,bad));
   /* clamps: absurd strength is bounded */
   float huge[3];assert(vr_world_spring_strength(error,zero,.5f,1,units,g,100.0f,huge));
   float top[3];assert(vr_world_spring_strength(error,zero,.5f,1,units,g,2.5f,top));
   assert(fabsf(huge[0]-top[0])<1e-6f); }
 /* throws: the latest motion dominates, strength scales, the cap holds */
 { float avg[3]={0.01f,0,0},latest[3]={0.03f,0,0},out[3];
   assert(vr_world_throw_velocity(avg,latest,1.0f,units,out));
   assert(fabsf(out[0]-(0.01f*0.35f+0.03f*0.65f))<1e-6f);
   float strong[3];assert(vr_world_throw_velocity(avg,latest,2.0f,units,strong));
   assert(fabsf(strong[0]-2*out[0])<1e-6f);
   float fast[3]={10,0,0},capped[3];assert(vr_world_throw_velocity(fast,fast,1.0f,units,capped));
   assert(fabsf(capped[0]-units*0.24f)<1e-5f);
   float nan3[3]={NAN,0,0};assert(!vr_world_throw_velocity(nan3,latest,1.0f,units,out)); }
 /* body capsules: distance to a bone segment */
 { float a[3]={0,0,0},b[3]={0,0,1},p[3]={0.05f,0,0.5f},q[3]={0,0,2};
   assert(fabsf(vr_world_segment_distance(p,a,b)-0.05f)<1e-6f);
   assert(fabsf(vr_world_segment_distance(q,a,b)-1.0f)<1e-6f);
   assert(vr_world_segment_distance(p,a,a)>0.49f); }
 /* climbing: walls, steep rock and overhangs anywhere; tops only above the waist */
 { float wall[3]={1,0,0},slope[3]={0.8f,0,0.6f},gentle[3]={0.5f,0,0.866f},top[3]={0,0,1},roof[3]={0,0,-1},bad[3]={NAN,0,0};
   assert(vr_pk_climbable(wall,0)&&vr_pk_climbable(slope,0)&&vr_pk_climbable(roof,0));
   assert(!vr_pk_climbable(gentle,0)&&!vr_pk_climbable(top,0)); /* the floor at the feet */
   assert(vr_pk_climbable(top,1)&&vr_pk_climbable(gentle,1));   /* a ledge's top */
   assert(!vr_pk_climbable(bad,1));
   assert(vr_pk_vertical(wall)&&!vr_pk_vertical(slope)); /* wall running is unchanged */ }
 /* melee: open hands grab, fists strike, guns strike */
 { assert(!vr_melee_hand_permitted(0,1,0,0.1f,0.1f,0));  /* open hand, grab features on */
   assert(vr_melee_hand_permitted(0,0,0,0.1f,0.1f,0));   /* no grab features: as before */
   assert(vr_melee_hand_permitted(0,1,0,0.5f,0.1f,0));   /* half-closed, fist not required */
   assert(!vr_melee_hand_permitted(1,1,0,0.5f,0.1f,0));  /* FIST REQUIRED needs a fist */
   assert(vr_melee_hand_permitted(1,1,0,0.9f,0.9f,0));
   assert(vr_melee_hand_permitted(1,1,1,0.0f,0.0f,0));   /* the gun strikes */
   assert(!vr_melee_hand_permitted(0,0,1,1,1,1));        /* a hand holding something else */
   assert(!vr_melee_hand_permitted(0,0,0,NAN,0,0)); }
 puts("PASS: Test54 hold strength, throw velocity, body capsules, climb surfaces and fist/open-hand melee");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test54-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                    "-fsanitize=address,undefined", "-I", str(ROOT), str(path / "check.c"), "-o", str(path / "check"),
                    "-lm"], check=True)
    subprocess.run([str(path / "check")], check=True)
print("PASS: Test54 wiring (NPC body touch, hold/throw strength, root follow, death ragdolls, climb grip, melee, hands, gun parts)")
