"""Test67 precision-polish regressions. Executes production reticle/sprint and
NPC surface helpers; campaign transaction harness is in test_test67_campaigns.
Reload pose measurements against owner assets are recorded separately, not bundled.
"""
from pathlib import Path
import re, subprocess, tempfile
R=Path(__file__).resolve().parents[1]
def read(p): return (R/p).read_text(encoding='utf-8')
def fn(text,name):
 m=re.search(r'^(?:static )?[\w *]+\b'+re.escape(name)+r'\s*\([^;{]*\)\s*\{',text,re.M)
 assert m,name
 a=m.start();e=text.index('{',a)+1;depth=1
 while depth: depth+=(text[e]=='{')-(text[e]=='}');e+=1
 return text[a:e]
def run(text):
 with tempfile.TemporaryDirectory(prefix='test67-') as d:
  p=Path(d);(p/'check.c').write_text(text)
  subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I',str(R),str(p/'check.c'),'-lm','-o',str(p/'check')],check=True)
  subprocess.run([str(p/'check')],check=True)
frame=read('port/linux/src/vr_frame.c')
run(r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "port/linux/game/vr_sprint_melee_math.h"
#include "port/linux/game/vr_reload_grip_profile.h"
static struct {int crosshair_enabled,reticle_hidden,seated;float crosshair_opacity;}vr;
static int empty;
static int vr_hand_empty(void){return empty;}
'''+fn(frame,'vr_crosshair_enabled')+r'''
int main(void){
 for(int bits=0;bits<32;bits++){
  vr.crosshair_enabled=!!(bits&1);vr.reticle_hidden=!!(bits&2);vr.crosshair_opacity=bits&4?1:0;
  vr.seated=!!(bits&8);empty=!!(bits&16);
  assert(vr_crosshair_enabled()==(vr.crosshair_enabled&&!vr.reticle_hidden&&vr.crosshair_opacity>0&&(!empty||vr.seated)));
 }
 assert(vr_sprint_scale_for_effort(3,vr_sprint_effort_combine(0,1))==3);
 assert(vr_sprint_scale_for_effort(3,vr_sprint_effort_combine(1,0))==3);
 assert(vr_sprint_scale_for_effort(3,.5f)==2);
 assert(vr_sprint_scale_for_effort(99,1)==3&&vr_sprint_scale_for_effort(NAN,1)==1);
 assert(vr_sprint_scale_for_effort(1.5f,1)==1.5f&&vr_sprint_scale_for_effort(3,NAN)==1);
 struct vr_reload_grip_profile const*p=vr_reload_grip_profile_for("weapons\\assault rifle\\fp\\fp");
 assert(p&&p->frame==40&&p->frames==87);
 assert(!vr_reload_grip_profile_for("weapons\\sniper rifle\\fp\\fp"));
 assert(!vr_reload_grip_profile_for("custom\\rifle")&&!vr_reload_grip_profile_for(NULL));
 assert(!strcmp(vr_reload_grip_profile_for("weapons\\shotgun\\fp\\fp")->ammo,"frame bullet"));
 assert(!strcmp(vr_reload_grip_profile_for("weapons\\rocket launcher\\fp\\fp")->charge,"frame push_bar"));
 puts("PASS: Test67 empty-hand reticle/vehicle opt-in combinations, shared sprint 1-3x, finite limits, audited reload profile routing and Sniper preservation");
}
''')
run(r'''
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
typedef float real;typedef int boolean;
typedef union{struct{float x,y,z;};struct{float i,j,k;};float n[3];}real_point3d,real_vector3d;
#define TRUE 1
#define FALSE 0
#define PIN(a,b,c) fminf(fmaxf(a,b),c)
struct vr_articulated_native {struct{int count;struct{int parent;float position[3],radius;}nodes[4];}body;struct{real_vector3d forward;}captured[4];};
static int valid_real_point3d(real_point3d const*p){return p&&isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*v){for(int k=0;k<3;k++)v->n[k]=b->n[k]-a->n[k];}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->x*b->x+a->y*b->y+a->z*b->z;}
static void point_from_line3d(real_point3d const*p,real_vector3d const*v,float t,real_point3d*out){for(int k=0;k<3;k++)out->n[k]=p->n[k]+t*v->n[k];}
static float normalize3d(real_vector3d*v){float m=sqrtf(dot_product3d(v,v));if(m>0)for(int k=0;k<3;k++)v->n[k]/=m;return m;}
'''+fn(read('port/linux/game/vr_npc_interaction.c'),'npc_contact_surface')+r'''
int main(void){
 struct vr_articulated_native rig={0};rig.body.count=2;rig.body.nodes[1].parent=0;rig.body.nodes[1].position[2]=1;rig.body.nodes[1].radius=.1f;rig.captured[1].forward.x=1;
 real_point3d hand={.n={.3f,0,.5f}},out;
 assert(npc_contact_surface(&rig,1,&hand,1,&out)&&fabsf(out.x-.1f)<1e-6f&&out.z==.5f);
 hand.x=-.3f;assert(npc_contact_surface(&rig,1,&hand,1,&out)&&fabsf(out.x+.1f)<1e-6f);
 hand=(real_point3d){.n={0,0,.5f}};assert(npc_contact_surface(&rig,1,&hand,1,&out)&&fabsf(out.x-.1f)<1e-6f);
 hand.x=NAN;assert(!npc_contact_surface(&rig,1,&hand,1,&out));hand.x=0;
 assert(!npc_contact_surface(&rig,0,&hand,1,&out)&&!npc_contact_surface(&rig,2,&hand,1,&out));
 rig.body.nodes[1].parent=3;assert(!npc_contact_surface(&rig,1,&hand,1,&out));rig.body.nodes[1].parent=0;
 rig.body.nodes[1].radius=NAN;assert(!npc_contact_surface(&rig,1,&hand,1,&out));
 puts("PASS: Test67 skeletal capsule grab anchor: left/right contact, centre fallback, malformed/invalid bounds rejected");
}
''')
render=read('port/linux/game/vr_render.c');damage=read('source/objects/damage.c');units=read('source/units/units.c')
assert '(!vr_hand_empty() || vr.seated)' in fn(frame,'vr_crosshair_enabled')
assert '!vr_crosshair_enabled()' in frame and '!vr_crosshair_enabled()' in read('port/linux/src/d3d8_gl.c')
assert '(vehicle_grip ? 0.10f : 0.06f) * units' in render and 'owner == VR_INTERACTION_NPC' in render
assert 'damage_definition->category == _damage_category_melee' in damage
assert '!vr_combat_regular_blow(damage->owner_object_index, current_object_index)' in damage
assert 'vr_combat_damage_end();' in units
learner=fn(render,'vr_reload_grip_learn')
assert 'profile->frame - 1' in learner and 'profile->frame + 1' in learner
assert 'graph->nodes.count == profile->nodes' in learner and 'pose->frame_count == profile->frames' in learner
assert learner.index('vr_reload_grip.part_valid[0] = vr_reload_grip.distance[0] <= 0.18f * units;') < learner.index('if (profile &&')
assert 'distance3d(&previous.position, &relative.position) > .01f * units' in learner
print('PASS: Test67 damage category/context isolation, bounded hand attachment, reload pose shape/stability checks')

hud=read("source/interface/hud_weapon.c")
assert "if (vr_crosshair_capture < 0)\n\t\t\treturn;" in hud
