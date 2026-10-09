"""Physical reload transaction and exact native ammo conservation checks."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "source/items/weapons.c").read_text()
start = source.index("static void weapon_magazine_finish_reload(\n", source.index("static void weapon_magazine_finish_reload(\n") + 1)
end = source.index("\nstatic void weapon_magazine_start_chamber", start)
finish = source[start:end]

code = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "port/linux/game/vr_manual_reload_math.h"
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
 puts("PASS: physical reload sequence, fresh grip edges, cancellation and exact native tactical/empty ammo conservation");
}
'''
with tempfile.TemporaryDirectory(prefix="manual-reload-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
                    "-I", str(ROOT), str(path / "check.c"), "-o", str(path / "check")], check=True)
    subprocess.run([str(path / "check")], check=True)
