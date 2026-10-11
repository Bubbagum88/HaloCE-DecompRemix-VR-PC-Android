"""Test55 polish pass: restrain/throw-class/friction math and the production wiring.

Owner's Test54 report (2026-10-11 logs and videos): Elites and Marines hard to
grab, weak throws, puppet-like ragdolls sliding on floors, magazines held at
odd angles, the charging handle hard to catch, wall running too manual,
rudimentary vehicle controls fighting controller steering, Shades (and, it
turned out, most campaign vehicles, bodies, weapons and props) refused because
their levels give them script names, a fist zooming, frame rate falling in big
fights (decals). This suite runs the pure math under ASan/UBSan and pins the
production wiring.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
npc = read("port/linux/game/vr_npc_interaction.c")
world = read("port/linux/game/vr_world_interaction.c")
props = read("port/linux/game/vr_world_props.c")
items = read("source/items/items.c")
native = read("port/linux/game/vr_articulated_native.c")
reload = read("port/linux/game/vr_manual_reload.c")
reload_math = read("port/linux/game/vr_manual_reload_math.h")
parkour = read("port/linux/game/vr_parkour.c")
frame = read("port/linux/src/vr_frame.c")
render = read("port/linux/game/vr_render.c")
handles = read("port/linux/game/vr_vehicle_handles.h")
menu = read("port/linux/game/vr_menu.c")
config = read("port/linux/src/port_config.c")
fpw = read("source/interface/first_person_weapons.c")
decals = read("source/rasterizer/xbox/rasterizer_xbox_decals.c")
damage = read("source/objects/damage.c")

def body(text, signature):
    start = text.index(signature)
    brace = text.index("{", start)
    depth, at = 1, brace + 1
    while depth:
        depth += (text[at] == "{") - (text[at] == "}")
        at += 1
    return text[start:at]

# NPCs: busy/diving/meleeing NPCs are grabbable; one hand restrains a heavy
# body (no lift); the death ragdoll reads the species before claiming a slot.
eligible = body(npc, "static struct unit_datum *eligible(")
assert "_unit_state_ai_impulse" in eligible and "_unit_state_melee_attack" in eligible
assert "w->weapon.state!=_weapon_state_idle" not in eligible
assert "vr_world_restrain(" in npc and "restraint-slipped" in npc
death = body(npc, "void vr_npc_interaction_death(long index)")
assert death.index("species=unit_species(u,index);") < death.index("npc.active=1;"), "species read before the slot is marked active (it read its own blank slot: species 0)"
assert "vr_npc_interaction_note_damage(object_index, &damage->epicenter, &damage->direction," in damage
# Script-named objects (most campaign placements) are no longer refused;
# cutscene (movie star) control still is.
for name, text in (("eligible", eligible), ("continuable", body(npc, "static struct unit_datum *continuable(")),
                   ("death", death), ("vehicle_lift_get", body(world, "static struct vehicle_datum *vehicle_lift_get(")),
                   ("prop_get", body(props, "static struct object_datum *prop_get(")),
                   ("item_vr_grabbable", body(items, "struct item_datum *item_vr_grabbable(")),
                   ("capture", body(native, "int vr_articulated_native_capture("))):
    assert "name_index" not in text, name
    assert "_object_movie_star_bit" in text, name
assert "type == VR_VEHICLE_TYPE_ALIEN_FIGHTER" in body(world, "static boolean vehicle_lift_type_supported(")
assert "VR_VEHICLE_TYPE_HUMAN_PLANE" not in body(world, "static boolean vehicle_lift_type_supported(")
# Throws: Spartan class for NPCs and for held props/weapons.
assert "vr_world_throw_velocity_spartan(npc.velocity[hand].n" in npc
assert "vr_world_throw_velocity_spartan(held->velocity.n" in world
# Ragdolls: floor friction and leaf joints.
assert "friction" in read("port/linux/game/vr_articulated_native.h")
# Manual reload: grip pose, forgiving insertion, charging lock-on and grace.
assert "matrix4x3_multiply(&gun_inverse, &reload.socket, &relative);" in reload
assert "reload_component_bounds_touch(&reload.socket,&reload.held,0.03f*units)" in reload
assert "VR_MR_CHAMBER_HELD ? 0.04f : 0.0f" in reload
assert "vr_pose_time() - reload.grip_press_time <= 0.35" in reload
assert "(press || (i->grace_press && i->held)) && i->near_chamber" in reload_math
assert "owner == VR_INTERACTION_RELOAD || owner == VR_INTERACTION_VEHICLE" in render
# Wall run: eight probes plus the wall being run on, released-stick runs,
# speed floor/cap, level hold, chaining after a wall jump.
assert "for(int direction=0;direction<9;direction++)" in parkour
assert "reach=radius+0.35f*units;" in parkour
assert "parkour.walljump_age<=2*TICKS_PER_SECOND" in parkour
assert "fmaxf(parkour.run_speed,4.0f*per_second)*multiplier,4.0f*per_second,2.0f*per_second,9.0f*per_second" in parkour
assert "if(progress<0.6f)velocity->k=0.0f;" in parkour
assert "vr_pk_leap(look.n,wall.plane.n.n" in parkour, "wall jump toward the look direction unchanged"
# Calibration: keys, zone helpers shared by markers and triggers, menu rows.
for key in ("pouch_hip", "pouch_shoulder", "holster_hip", "holster_shoulder"):
    for axis in ("out", "up", "back"):
        assert f'{{ "vr.{key}_{axis}", _config_real, "0.0"' in config, (key, axis)
assert '{ "vr.reload_pouch_size", _config_real, "0.16"' in config
assert "reload_pouch_place(which, sides[index], offset);" in body(frame, "int vr_reload_pouch_zone(")
assert "reload_pouch_place(which, sides[index], offset);" in body(frame, "int vr_calibration_markers(")
assert "holster_place(index, offset);" in body(frame, "int vr_calibration_markers(")
assert frame.count("holster_place(index, offset);") >= 2, "holster trigger and marker share holster_place"
assert "vr_calibration_markers(vr_render.game_camera_position.n,marker_points,marker_radii,8)" in handles
assert "vr_calibration_note_shown(1);" in menu and "vr_calibration_note_shown(2);" in menu
# One IMMERSION category with topic screens.
assert '"IMMERSION+"' not in menu and "vr_menu_immersion_sections" in menu
# Vehicles: controls own the steering; first-person hands; Warthog's own wheel.
assert "return 1;\n}\n/* Test55: where a hand holding the controls is drawn" in handles
assert "vr_wheel.angle*=0.92f;" in handles
assert "vr_render_vehicle_first_person_hands()" in render
assert '"IMMERSIVE VEHICLE", "vr.vehicle_handles"' in menu
# Zoom moves to the right stick's click with physical melee.
zoom = body(frame, "static int stick_zoom_active(void)")
assert "physical_melee_allowed()" in zoom and "VR_BUTTON_ACTION_MELEE" in zoom
assert "vr.zoom_down = touch_source_down(VR_BUTTON_SOURCE_RIGHT_STICK, right, left);" in frame
# OpenCE Build 188: decals drawn in batches (fights left hundreds in view).
assert "rasterizer_decals_draw_batch" in decals and "DECAL_BATCH_MAXIMUM_DECALS 256" in decals

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "port/linux/game/vr_world_math.h"
#include "port/linux/game/vr_manual_reload_math.h"
int main(void){
 const float units=0.32808399f;
 /* throw classes: light one-hand 2.4, Marine-weight 1.8, two-hand heavy 1.25 */
 assert(vr_world_throw_class(1,.5f)==2.4f&&vr_world_throw_class(1,.35f)==1.8f&&vr_world_throw_class(2,.25f)==1.25f);
 { float avg[3]={0.01f,0,0},latest[3]={0.02f,0,0},out[3],base[3];
   assert(vr_world_throw_velocity(avg,latest,1.0f,units,base));
   assert(vr_world_throw_velocity_spartan(avg,latest,1.0f,2.4f,units,out));
   assert(fabsf(out[0]-base[0]*2.4f)<1e-6f);
   float fast[3]={10,0,0};assert(vr_world_throw_velocity_spartan(fast,fast,2.0f,2.5f,units,out));
   assert(fabsf(out[0]-units*0.8f)<1e-5f); /* never above 24 m/s */
   float bad[3]={NAN,0,0};assert(!vr_world_throw_velocity_spartan(bad,latest,1,1,units,out)); }
 /* one hand on a heavy body: horizontal drag only, at most 0.8 m/s, no lift */
 { float error[3]={1,1,1},current[3]={0,0,-.01f},out[3];
   assert(vr_world_restrain(error,current,.25f,units,out));
   assert(out[2]==current[2]);
   assert(sqrtf(out[0]*out[0]+out[1]*out[1])<=units*0.8f/30.0f+1e-6f);
   float small[3]={0.001f,0,0},o2[3];assert(vr_world_restrain(small,current,.25f,units,o2)&&o2[0]>0&&o2[0]<0.001f); }
 /* charging grace: a squeeze just before reaching the handle still takes it */
 { struct vr_mr_state s={.phase=VR_MR_NEED_CHAMBER,.down=1};
   struct vr_mr_input i={.valid=1,.held=1,.near_chamber=1,.grace_press=0};
   assert(vr_mr_step(&s,&i)==VR_MR_NONE); /* held from before, no grace: no */
   i.grace_press=1;assert(vr_mr_step(&s,&i)==VR_MR_CHARGE&&s.phase==VR_MR_CHAMBER_HELD); }
 puts("PASS: Test55 throw classes, Spartan cap, one-hand restraint, charging grace");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test55-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                    "-fsanitize=address,undefined", "-I", str(ROOT), str(path / "check.c"), "-o", str(path / "check"),
                    "-lm"], check=True)
    subprocess.run([str(path / "check")], check=True)
print("PASS: Test55 wiring (NPC eligibility and restraint, named objects, Banshee lift, Spartan throws, ragdoll friction, reload grip/charging, wall run, calibration, one IMMERSION, vehicles, stick zoom, Build 188 decal batches)")
