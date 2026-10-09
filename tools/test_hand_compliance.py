"""Bounded compliance and actual held-object finger query routing."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'port/linux/game/vr_render.c').read_text()
compliance_start=source.index('static void vr_limit_hand_compliance(')
compliance_brace=source.index('{',compliance_start);compliance_end=compliance_brace+1;compliance_depth=1
while compliance_depth:compliance_depth+=(source[compliance_end]=='{')-(source[compliance_end]=='}');compliance_end+=1
compliance=source[compliance_start:compliance_end]
assert 'vr_hand_compliance_node_visibility(visibility,' in compliance
assert 'vr_hand_compliance_node_position(' in compliance
assert 'vr_node_under(graph,node,hand)' in compliance
contact_start=source.index('static void vr_hand_contact_feedback(')
contact_brace=source.index('{',contact_start);contact_end=contact_brace+1;contact_depth=1
while contact_depth:contact_depth+=(source[contact_end]=='{')-(source[contact_end]=='}');contact_end+=1
contact=source[contact_start:contact_end]
assert 'vr_contact_pulse(&state[controller], vr_pose_time(), touching)' in contact
assert 'vr_haptic(controller, PIN(strength, 0.05f, 0.35f), 0.025f)' in contact
start=source.index('static boolean vr_finger_trace(');brace=source.index('{',start);end=brace+1;depth=1
while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
query=source[start:end]
code=r'''
#include <assert.h>
#include <string.h>
#include "port/linux/game/vr_hand_compliance_math.h"
typedef float real;typedef int boolean;
typedef struct{float n[3];}real_point3d,real_vector3d;
struct collision_result{float t;long object_index;};
struct collision_plane{float t;};
struct collision_model_instance{long object_index;};
struct collision_model_test_pill_result{struct{float t;}bsp_result;};
#define TRUE 1
#define FALSE 0
#define PIN(x,lo,hi) ((x)<(lo)?(lo):(x)>(hi)?(hi):(x))
static int vr_finger_volume_hand=-1,vr_finger_reload_only,vr_finger_owned_valid;
static struct collision_model_instance vr_finger_owned_model={77};
static struct{int usable,features;float finger_radius;}vr_finger_volume[2];
static struct{int queries,ray_fallbacks;}vr_contact_stats;
static int generic_calls,owned_calls,reload_calls,overlap,owned_hit=1;
static float vr_units_per_metre(void){return 1;}
static int vr_manual_reload_trace(float const*a,float const*b,float radius,struct collision_result*out){(void)a;(void)b;assert(radius==.004f);reload_calls++;out->t=.4f;return 1;}
static int collision_model_test_point(struct collision_model_instance const*i,real_point3d const*p){(void)p;assert(i->object_index==77);owned_calls++;return overlap;}
static int collision_model_test_pill(struct collision_model_instance const*i,real_point3d const*p,real_vector3d const*v,float r,struct collision_model_test_pill_result*out){(void)p;(void)v;assert(i->object_index==77&&r==.004f);owned_calls++;out->bsp_result.t=.3f;return owned_hit;}
static int vr_touch_trace(real_point3d const*a,real_vector3d const*b,long ignore,struct collision_result*out){(void)a;(void)b;(void)ignore;(void)out;generic_calls++;return 0;}
static int collision_features_test_point(int const*a,real_point3d const*b,struct collision_plane*c){(void)a;(void)b;(void)c;generic_calls++;return 0;}
static int collision_features_test_vector(int const*a,real_point3d const*b,real_vector3d const*c,struct collision_plane*d){(void)a;(void)b;(void)c;(void)d;generic_calls++;return 0;}
static int vr_weapon_trace(real_point3d const*a,real_vector3d const*b,float r,struct collision_result*c){(void)a;(void)b;(void)c;(void)r;generic_calls++;return 0;}
'''+query+r'''
int main(void){
 struct vr_hand_compliance s={0};
 assert(vr_hand_compliance_step(&s,.1f,.18f,0,1)==1);
 assert(vr_hand_compliance_step(&s,.3f,.18f,.04f,0)==.5f);
 assert(vr_hand_compliance_step(&s,.3f,.18f,.04f,0)==0);
 assert(vr_hand_compliance_step(&s,.16f,.18f,.04f,0)==0); /* recovery hysteresis */
 assert(vr_hand_compliance_step(&s,.1f,.18f,.04f,0)==.5f);
 assert(vr_hand_compliance_step(&s,.1f,.18f,.04f,0)==1);
 assert(vr_hand_compliance_step(&s,NAN,.18f,0,1)==0);
 assert(vr_hand_compliance_step(&s,.1f,NAN,0,1)==1);
 assert(vr_hand_compliance_step(&s,.5f,.18f,0,1)==0); /* reset cannot flash a distant hand */
 /* Compliance fades the arm but preserves the hand/finger subtree at its
    solved, collision-constrained pose. */
 assert(vr_hand_compliance_node_visibility(0,1)==1);
 assert(vr_hand_compliance_node_visibility(.35f,1)==1);
 assert(vr_hand_compliance_node_visibility(.35f,0)==.35f);
 assert(vr_hand_compliance_node_visibility(NAN,0)==0);
 assert(fabsf(vr_hand_compliance_node_position(1.0f,.2f,0,1)-.2f)<1e-6f);
 assert(fabsf(vr_hand_compliance_node_position(1.0f,.2f,.35f,1)-.2f)<1e-6f);
 assert(fabsf(vr_hand_compliance_node_position(1.0f,.2f,.35f,0)-.72f)<1e-6f);
 real_point3d point={{0}};real_vector3d vector={{1,0,0}};struct collision_result hit;
 vr_finger_reload_only=1;assert(vr_finger_trace(&point,&vector,-1,&hit)&&hit.t==.4f&&reload_calls==1&&!generic_calls&&!owned_calls);
 vr_finger_reload_only=0;vr_finger_owned_valid=1;
 assert(vr_finger_trace(&point,&vector,-1,&hit)&&hit.t==.3f&&hit.object_index==77&&owned_calls==2&&!generic_calls);
 overlap=1;assert(vr_finger_trace(&point,&vector,-1,&hit)&&hit.t==0&&owned_calls==3);
 overlap=0;owned_hit=0;assert(!vr_finger_trace(&point,&vector,-1,&hit)&&!generic_calls);
 vr_finger_owned_valid=0;assert(!vr_finger_trace(&point,&vector,-1,&hit)&&generic_calls==1);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'hand.c';exe=Path(tmp)/'hand';c.write_text(code)
    subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(ROOT),str(c),'-lm','-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('hand compliance + production owned-collider isolation passed (ASan/UBSan)')
