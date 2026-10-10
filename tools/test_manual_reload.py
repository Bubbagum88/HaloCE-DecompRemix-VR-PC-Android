"""Physical reload transaction and exact native ammo conservation checks."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "source/items/weapons.c").read_text()
reload_source = (ROOT / "port/linux/game/vr_manual_reload.c").read_text()
input_source = (ROOT / "port/linux/src/vr_frame.c").read_text()
config_source = (ROOT / "port/linux/src/port_config.c").read_text()
menu_source = (ROOT / "port/linux/game/vr_menu.c").read_text()
assert "vr_mr_profile_changed(bounds_log_initialized, bounds_logged_weapon" in reload_source
assert "bounds_logged_model, weapon_index, reload.model" in reload_source
assert "model=%ld magazine=%d chamber=%d" in reload_source
assert "bounds_log_initialized=TRUE" in reload_source
assert 'config_string("vr.reload_input")' in reload_source
assert 'reload_hand_touches_part(0,&reload.socket,&hand)' in reload_source
assert 'reload_hand_touches_part(1,&reload.charge,&hand)' in reload_source
assert 'reload_near(&hand,&hip,contact_radius)' in reload_source
assert 'reload_near(&hand,&shoulder,contact_radius)' in reload_source
assert '0.09f*units' not in reload_source and '0.075f*units' not in reload_source
assert '0.19f*units' not in reload_source and '0.16f*units' not in reload_source
assert "vr_interaction_trigger(hand_index)" in reload_source
assert "vr_interaction_claim_input(hand_index, VR_INTERACTION_RELOAD, input.held)" in reload_source
assert "int vr_manual_reload_action_down(void)" in input_source
assert "HALO_XR_BUTTON_X" in input_source[input_source.index("static unsigned int touch_buttons"):input_source.index("static void layout_controls")]
assert '"vr.button_melee", _config_string, "\\"right_stick\\""' in config_source
assert '"vr.reload_input", _config_string, "\\"grip\\""' in config_source
assert '{ "RELOAD INPUT", "vr.reload_input", _vr_setting_string, 2, { { "GRIP", "grip" }, { "TRIGGER", "trigger" } } }' in menu_source
assert "vr_mr_trigger_held(interaction_trigger_held[hand], vr.frame.trigger[hand])" in input_source
assert "input.eject_pressed = reload_pressed;" in reload_source
assert "vr_manual_reload_action_down()" in reload_source
assert "vr_mr_reload_button_down(mapped_action_down, explicit_reload)" in reload_source
assert "weapon->weapon.state == _weapon_state_primary_recoil && !reload_pressed" in reload_source
assert "VR manual reload input: weapon=%ld phase=%d grip=%d" in reload_source
assert "grip ownership refused" in reload_source
assert "input.can_load = magazine->rounds_total > 0;" in reload_source
assert "magazine->rounds_loaded < magazine_definition->rounds_loaded_maximum" not in reload_source
assert "VR_MR_EJECT" in reload_source and "reload.debris_pending = TRUE;" in reload_source
assert "VR manual reload attempt: weapon=%ld phase=%d action=%s" in reload_source
assert "unsigned manual = vr_manual_reload_update(weapon_index" in source
assert "weapon->weapon.control_flags, _weapon_control_reload_bit" in source
assert 'if (reload.have_attachment) matrix4x3_multiply(&hand_matrix, &reload.attachment, &reload.held);' in reload_source
assert "static boolean reload_attach_to_hand(" in reload_source
assert "if (event == VR_MR_PICKUP)" in reload_source
assert "attached.position = hand;" in reload_source
assert "reload_attach_to_hand(&hand_matrix, &attached)" in reload_source
assert "replacement-attachment-invalid" in reload_source
assert "VR manual reload gate: weapon=%ld reason=%s" in reload_source
assert "hand=(%.3f,%.3f,%.3f) magazine=(%.3f,%.3f,%.3f)" in reload_source
assert "return vr_mr_output_flags(suppress_native, input.valid, reload.state.phase, event," in reload_source
assert "if (explicit_reload || !input.valid)" not in reload_source
start = source.index("static void weapon_magazine_finish_reload(\n", source.index("static void weapon_magazine_finish_reload(\n") + 1)
end = source.index("\nstatic void weapon_magazine_start_chamber", start)
finish = source[start:end]

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "port/linux/game/vr_manual_reload_math.h"
#include "port/linux/game/vr_reload_contact_math.h"
struct weapon_magazine { short rounds_loaded,rounds_total,state,state_timer; } mag;
struct weapon_magazine_definition { unsigned flags; short rounds_reloaded,rounds_loaded_maximum; } md;
struct weapon_definition { struct { int magazines; } weapon; } wd;
struct weapon_datum { long definition_index; struct { unsigned flags; } item;
 struct { unsigned control_flags; } weapon; } weapon;
struct { int infinite_ammo; } cheat;
#define TAG_BLOCK_GET_ELEMENT(block,index,type) ((void)(block),(void)(index),&md)
#define TEST_FLAG(value,bit) (((value) & (1u<<(bit))) != 0)
#define FALSE 0
#define _magazine_unchambered 2
static struct weapon_datum *weapon_get(long n){(void)n;return &weapon;}
static struct weapon_magazine *weapon_magazine_get(struct weapon_datum *w,short n){(void)w;(void)n;return &mag;}
static struct weapon_definition *weapon_definition_get(long n){(void)n;return &wd;}
static void weapon_magazine_start_reload(long n,short m,int v){(void)n;(void)m;(void)v;assert(0 && "unexpected partial reload loop");}
''' + finish + r'''
static int step(struct vr_mr_state *s,int held,int near_mag,int pouch,int chamber,int out,int pulled){
 struct vr_mr_input i={.valid=1,.held=held,.near_mag=near_mag,.near_pouch=pouch,
  .near_chamber=chamber,.magazine_out=out,.chamber_pulled=pulled,.can_load=1,.seated=1};
 return vr_mr_step(s,&i);
}
int main(void){
 struct vr_mr_state s={0};
 { float lo[3]={-.02f,-.03f,-.01f},hi[3]={.02f,.03f,.01f},p[3]={.055f,0,0},zero[3]={0,0,0},fraction,normal[3];
   assert(vr_reload_sphere_touches_box(p,lo,hi,.04f)); /* physical palm overlaps authored part bounds */
   p[0]=.061f;assert(!vr_reload_sphere_touches_box(p,lo,hi,.04f)); /* old 9 cm center reach is rejected */
   p[0]=.02f;p[1]=.03f;p[2]=.01f;assert(vr_reload_sphere_touches_box(p,lo,hi,0));
   assert(vr_reload_box(p,zero,lo,hi,0,&fraction,normal));
   p[0]=NAN;assert(!vr_reload_sphere_touches_box(p,lo,hi,.04f)); }
 assert(vr_mr_profile_changed(0,0,0,17,29));
 assert(!vr_mr_profile_changed(1,17,29,17,29));
 assert(vr_mr_profile_changed(1,17,29,18,29));
 assert(vr_mr_profile_changed(1,17,29,17,30));
 assert(!vr_mr_suppress_native_reload(0,1,1)); /* classic mode keeps native reload */
 assert(!vr_mr_suppress_native_reload(1,0,1)); /* online games keep network-safe reload */
 assert(vr_mr_suppress_native_reload(1,1,1));  /* profiled solo manual mode suppresses it */
 assert(!vr_mr_suppress_native_reload(1,1,0)); /* unknown profiles fall back to native reload */
 assert(!vr_mr_input_uses_trigger("grip") && !vr_mr_input_uses_trigger(NULL));
 assert(!vr_mr_input_uses_trigger("invalid")); /* unknown config safely uses default Grip */
 assert(vr_mr_input_uses_trigger("trigger"));
 assert(!vr_mr_button_pressed(0,0) && vr_mr_button_pressed(0,1));
 assert(!vr_mr_button_pressed(1,1) && vr_mr_button_pressed(0,1));
 assert(!vr_mr_reload_button_down(0,0));
 assert(vr_mr_reload_button_down(1,0));
 assert(vr_mr_reload_button_down(0,1));
 { int was_down=0;
   int held=vr_mr_reload_button_down(1,0);
   assert(vr_mr_button_pressed(was_down,held));was_down=held;
   held=vr_mr_reload_button_down(0,1); /* native level overlaps mapped input */
   assert(!vr_mr_button_pressed(was_down,held));was_down=held;
   held=vr_mr_reload_button_down(0,0);
   assert(!held&&!vr_mr_button_pressed(was_down,held));
   held=vr_mr_reload_button_down(1,0);
   assert(vr_mr_button_pressed(0,held)); }
 { struct vr_mr_state held_reload={0}; int was_down=0, reload_edge;
   struct vr_mr_input eject_input={.valid=1,.can_load=1,.near_mag=1};
   reload_edge=vr_mr_button_pressed(was_down,1);was_down=1;
   eject_input.eject_pressed=reload_edge;
   int eject_event=vr_mr_step(&held_reload,&eject_input);
   assert(eject_event==VR_MR_EJECT&&held_reload.phase==VR_MR_NEED_MAG);
   assert(vr_mr_output_flags(1,eject_input.valid,held_reload.phase,eject_event,1u,2u,4u)==3u);
   /* Raw Reload stays held, but only the rising edge is sent to the state
      machine. The still-open transaction must continue to block firing. */
   reload_edge=vr_mr_button_pressed(was_down,1);
   eject_input.eject_pressed=reload_edge;eject_input.near_mag=0;eject_input.held=0;
   int held_event=vr_mr_step(&held_reload,&eject_input);
   assert(!reload_edge&&held_event==VR_MR_NONE&&held_reload.phase==VR_MR_NEED_MAG);
   assert(vr_mr_output_flags(1,eject_input.valid,held_reload.phase,held_event,1u,2u,4u)==3u);
   /* A new Reload edge deliberately cancels; firing unlocks only after the
      transaction is back at IDLE. */
   was_down=0;reload_edge=vr_mr_button_pressed(was_down,1);
   eject_input.explicit_reload=reload_edge;
   int cancel_event=vr_mr_step(&held_reload,&eject_input);
   assert(cancel_event==VR_MR_CANCEL&&held_reload.phase==VR_MR_IDLE);
   assert(vr_mr_output_flags(1,eject_input.valid,held_reload.phase,cancel_event,1u,2u,4u)==1u);
 }
 assert(!vr_mr_trigger_held(0,0.75f) && vr_mr_trigger_held(0,0.751f));
 assert(vr_mr_trigger_held(1,0.56f) && !vr_mr_trigger_held(1,0.55f));
 assert(!vr_mr_trigger_held(0,NAN) && !vr_mr_trigger_held(0,-0.01f) && !vr_mr_trigger_held(0,1.01f));
 assert(step(&s,1,0,0,0,0,0)==VR_MR_NONE); /* grip away from gun */
 assert(step(&s,1,1,0,0,0,0)==VR_MR_NONE); /* held grip never auto-locks */
 step(&s,0,1,0,0,0,0);
 assert(step(&s,1,1,0,0,0,0)==VR_MR_BEGIN);
 assert(step(&s,0,1,0,0,0,0)==VR_MR_CANCEL); /* not pulled out */
 assert(step(&s,1,1,0,0,0,0)==VR_MR_BEGIN);
 step(&s,1,0,0,0,1,0);
 assert(step(&s,0,0,0,0,1,0)==VR_MR_DISCARD);
 assert(step(&s,1,0,0,0,0,0)==VR_MR_NONE); /* cannot conjure fresh mag away from pouch */
 step(&s,0,0,0,0,0,0);
 assert(step(&s,1,0,1,0,0,0)==VR_MR_PICKUP);
 assert(step(&s,0,0,0,0,0,0)==VR_MR_DISCARD); /* missed socket */
 assert(step(&s,1,0,1,0,0,0)==VR_MR_PICKUP);
 assert(step(&s,0,1,0,0,0,0)==VR_MR_INSERT);
 assert(s.phase==VR_MR_SEATING);
 struct vr_mr_input early={.valid=1,.held=0,.near_chamber=1,.can_load=1};
 assert(vr_mr_step(&s,&early)==VR_MR_NONE&&s.phase==VR_MR_SEATING);
 assert(step(&s,1,0,0,0,0,0)==VR_MR_NONE);
 step(&s,0,0,0,0,0,0);
 assert(step(&s,1,0,0,1,0,0)==VR_MR_CHARGE);
 assert(step(&s,0,0,0,0,0,0)==VR_MR_NONE); /* insufficient pull */
 assert(step(&s,1,0,0,1,0,0)==VR_MR_CHARGE);
 step(&s,1,0,0,0,0,1);
 assert(step(&s,0,0,0,0,0,1)==VR_MR_COMMIT);
 for(int j=0;j<100;j++) assert(step(&s,0,0,0,0,0,0)==VR_MR_NONE); /* one commit only */
 for(int phase=0;phase<=VR_MR_SEATING;phase++) for(int why=0;why<2;why++) {
  s=(struct vr_mr_state){.phase=phase,.pulled=1,.down=1};
  struct vr_mr_input i={.valid=!why,.explicit_reload=!why,.held=1,.can_load=1};
  assert(vr_mr_step(&s,&i)!=(int)VR_MR_COMMIT);assert(s.phase==VR_MR_IDLE);
 } /* tracking/drop/switch/seat/network invalidation and explicit B cannot award ammo */
 /* Gun-local displacement: translating gun and hand together preserves local x. */
 for(int gun=-100;gun<=100;gun++) {
  float world_hand=gun+0.25f, local_hand=world_hand-gun;
  assert(vr_mr_pull_distance(0.25f,local_hand)==0);
 }
 assert(vr_mr_pull_distance(0.25f,0.20f)>0.035f);
 s=(struct vr_mr_state){0};
 struct vr_mr_input shell={.valid=1,.held=1,.can_load=1,.near_mag=1,.loose_round=1};
 assert(vr_mr_step(&s,&shell)==VR_MR_NONE); /* no imaginary shotgun magazine removal */
 shell.held=0;vr_mr_step(&s,&shell);shell.held=1;shell.near_pouch=1;
 assert(vr_mr_step(&s,&shell)==VR_MR_PICKUP);
 for(int capacity=4;capacity<=60;capacity++) for(int loaded=0;loaded<=capacity;loaded++)
 for(int reserve=0;reserve<=capacity*2;reserve++) for(int infinite=0;infinite<2;infinite++)
 for(int shell_load=0;shell_load<2;shell_load++) for(int waste=0;waste<2;waste++) {
  md=(struct weapon_magazine_definition){.flags=waste,.rounds_reloaded=shell_load?1:capacity,.rounds_loaded_maximum=capacity};
  mag=(struct weapon_magazine){.rounds_loaded=loaded,.rounds_total=reserve};weapon.item.flags=2;
  cheat.infinite_ammo=infinite;weapon.weapon.control_flags=0x20;weapon_magazine_finish_reload(0,0);
  int add=reserve<md.rounds_reloaded?reserve:md.rounds_reloaded;
  int retained=waste?0:loaded;
  int wanted=retained+add<capacity?retained+add:capacity;
  assert(mag.rounds_loaded==wanted);
  assert(mag.rounds_total==(infinite?reserve:retained+reserve-wanted));
  assert(mag.rounds_loaded>=0&&mag.rounds_loaded<=capacity&&mag.rounds_total>=0);
 }
 {
  assert(vr_mr_pouch_side(0)==1&&vr_mr_pouch_side(1)==-1);
  for(int hip=0;hip<2;hip++)for(int shoulder=0;shoulder<2;shoulder++) {
   assert(vr_mr_pouch_enabled(hip,shoulder,1,0)==hip);
   assert(vr_mr_pouch_enabled(hip,shoulder,0,1)==shoulder);
   assert(vr_mr_pouch_enabled(hip,shoulder,1,1)==(hip||shoulder));
   assert(!vr_mr_pouch_enabled(hip,shoulder,0,0));
  }
  struct vr_mr_state crystal={.phase=VR_MR_IDLE};
  struct vr_mr_input physical={.valid=1,.can_load=1,.loose_round=1,.no_chamber=1,.held=1,.near_pouch=1};
  assert(vr_mr_step(&crystal,&physical)==VR_MR_PICKUP);
  physical.held=0;physical.near_mag=1;
  assert(vr_mr_step(&crystal,&physical)==VR_MR_INSERT);
  assert(vr_mr_step(&crystal,&physical)==VR_MR_NONE);
  physical.seated=1;assert(vr_mr_step(&crystal,&physical)==VR_MR_COMMIT);
  assert(crystal.phase==VR_MR_IDLE&&vr_mr_step(&crystal,&physical)==VR_MR_NONE);
 }
 /* Contextual reload-button ejection requires actual hand contact and reserve.
    Its replacement pickup must transition through the same hand-attached path
    as direct grip removal (guarded above in the production source). It supports
    a full-mag tactical replacement and leaves loose rounds separate. */
 {
  struct vr_mr_state eject={0};
  struct vr_mr_input i={.valid=1,.can_load=1,.near_mag=1,.eject_pressed=1};
  assert(vr_mr_step(&eject,&i)==VR_MR_EJECT);
  assert(eject.phase==VR_MR_NEED_MAG);
  assert(vr_mr_output_flags(1,1,eject.phase,VR_MR_EJECT,1u,2u,4u)==3u);
  i.eject_pressed=0;i.near_mag=0;i.near_pouch=1;i.held=1;
  assert(vr_mr_step(&eject,&i)==VR_MR_PICKUP);
  i.held=0;i.near_mag=1;
  assert(vr_mr_step(&eject,&i)==VR_MR_INSERT);
  i.seated=1;
  assert(vr_mr_step(&eject,&i)==VR_MR_NONE);
  i.held=1;i.near_chamber=1;
  assert(vr_mr_step(&eject,&i)==VR_MR_CHARGE);
  i.chamber_pulled=1;i.held=0;
  assert(vr_mr_step(&eject,&i)==VR_MR_COMMIT);
  eject=(struct vr_mr_state){0};
  i=(struct vr_mr_input){.valid=1,.can_load=1,.near_mag=0,.eject_pressed=1};
  assert(vr_mr_step(&eject,&i)==VR_MR_NONE); /* no contact */
  i.near_mag=1;i.can_load=0;
  assert(vr_mr_step(&eject,&i)==VR_MR_NONE); /* no reserve */
  i.can_load=1;i.loose_round=1;
  assert(vr_mr_step(&eject,&i)==VR_MR_NONE); /* no magazine eject for loose rounds */
 }
 puts("PASS: physical reload sequence, fresh grip edges, cancellation and exact native tactical/empty ammo conservation");
}
'''
with tempfile.TemporaryDirectory(prefix="manual-reload-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
                    "-I", str(ROOT), str(path / "check.c"), "-o", str(path / "check")], check=True)
    subprocess.run([str(path / "check")], check=True)
