"""Execute the real remote grip transaction against a deterministic host oracle."""
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/world-remote-tests';out.mkdir(parents=True,exist_ok=True)
code=(ROOT/'port/linux/game/vr_world_remote.c').read_text()
code=re.sub(r'^#include.*$','',code,flags=re.M)
stub=r'''
#include <assert.h>
#include <float.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#include "vr_world_math.h"
typedef int boolean;typedef float real;typedef unsigned char byte;
typedef union {struct{float i,j,k;};float n[3];} real_vector3d;
typedef real_vector3d real_point3d;
enum {FALSE,TRUE};
#define NONE (-1)
#define FLAG(x) (1u<<(x))
#define TEST_FLAG(value,bit) (!!((value)&FLAG(bit)))
enum{_object_dead_bit=0};
enum {_object_mask_weapon=1,_object_mask_equipment=2,_object_mask_scenery=4,_collision_test_front_facing_surfaces_bit=0,_collision_test_back_facing_surfaces_bit=1,_collision_test_structure_bit=2,_collision_test_objects_bit=3,_collision_test_objects_all_types_flags=255,_collision_test_for_line_of_sight_flags=1000,_collision_result_object=1};
struct object_datum{long definition_index;struct{real_point3d position,bounding_sphere_center;real radius,bounding_sphere_radius,scale;real_vector3d forward,up,translational_velocity,angular_velocity;}object;};
struct player_datum{long unit_index;};struct object_iterator{long index;};
struct collision_model_instance{long object;};struct collision_model_test_pill_result{short node_index,region_index,bsp_index;};
struct unit_datum{struct{long parent_object_index;unsigned damage_flags;}object;};
static struct unit_datum owner_unit={{NONE,0}};
struct collision_result{int type;long object_index;real_point3d point;};
struct object_definition{struct{float acceleration_scale;}object;};
struct network_interaction_hand{long player,unit,object;byte hand,kind,held,pressed;real_point3d position;real_vector3d forward,up;unsigned long sequence;};
static struct object_datum items[3];static struct player_datum p={10};static struct object_definition def={{1}};
static int ready=1,tick,blocked,velocity_calls,track_calls;static long local_held=NONE;
static real global_gravity=.003f;
static int network_interaction_host_ready(void){return ready;}
static long game_time_get(void){return tick;}
static float config_real(char const*k){return !strcmp(k,"vr.interaction_reach")?.04f:1.f;}
static struct player_datum*player_try_and_get(long i){return i==7||i==8?&p:0;}
static struct unit_datum*unit_try_and_get(long i){return i==10?&owner_unit:0;}
static struct object_datum*vr_world_object_get(long i){return i==1||i==2?&items[i]:0;}
static float vr_world_object_mobility(long i){(void)i;return def.object.acceleration_scale;}
static long vr_world_interaction_object(int h){(void)h;return local_held;}
static void cross_product3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*c){real_vector3d v={{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};*c=v;}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(real_vector3d const*a){return sqrtf(dot_product3d(a,a));}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static int collision_model_instance_new(struct collision_model_instance*m,long object){if(object!=1&&object!=2)return 0;m->object=object;return 1;}
static int collision_model_test_pill(struct collision_model_instance const*m,real_point3d const*p,real_vector3d const*v,float radius,struct collision_model_test_pill_result*r){real_vector3d d;(void)v;vector_from_points3d(p,&items[m->object].object.bounding_sphere_center,&d);if(magnitude3d(&d)>items[m->object].object.bounding_sphere_radius+radius)return 0;r->node_index=0;return 1;}
static void scale_vector3d(real_vector3d const*a,float s,real_vector3d*b){for(int i=0;i<3;i++)b->n[i]=a->n[i]*s;}
static void add_vectors3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*c){for(int i=0;i<3;i++)c->n[i]=a->n[i]+b->n[i];}
static void unit_get_camera_position(long i,real_point3d*p){(void)i;memset(p,0,sizeof(*p));}
static int collision_test_vector(unsigned flags,real_point3d const*a,real_vector3d const*b,long ignore,struct collision_result*h){(void)a;(void)b;(void)ignore;h->type=_collision_result_object;h->object_index=(blocked&&flags==1000)?2:1;h->point=(real_point3d){{.1f,0,0}};return 1;}
static void object_iterator_new(struct object_iterator*i,int mask,int f){(void)mask;(void)f;i->index=0;}
static void*object_iterator_next(struct object_iterator*i){return ++i->index<3?&items[i->index]:0;}
static void vr_world_object_velocity(long i,real_vector3d const*v,real_vector3d const*a){velocity_calls++;items[i].object.translational_velocity=*v;items[i].object.angular_velocity=*a;}
static void vr_interaction_impact_track(long i,long owner,float m,float u){(void)i;(void)owner;(void)m;(void)u;track_calls++;}
'''
tests=r'''
int main(void){
 assert(vr_world_authority(1,0,0));
 items[1].object.scale=1;items[1].object.bounding_sphere_radius=.05f;items[1].object.bounding_sphere_center.i=.1f;
 items[1].object.forward.i=1;items[1].object.up.k=1;
 struct network_interaction_hand r={.player=7,.unit=10,.object=NONE,.held=1,.pressed=1,.position={{.1f,0,0}},.forward={{1,0,0}},.up={{0,0,1}}};
 ready=0;assert(!vr_world_interaction_remote(&r));ready=1;
 r.position.i=.21f;assert(!vr_world_interaction_remote(&r));assert(!vr_world_interaction_remote_owned(1)); /* 6 cm from authored surface: old 12 cm ray reach is rejected */
 r.position.i=.1f;
 blocked=1;assert(!vr_world_interaction_remote(&r));blocked=0;
 local_held=1;assert(!vr_world_interaction_remote(&r));local_held=NONE;
 r.pressed=0;assert(!vr_world_interaction_remote(&r));r.pressed=1;
 assert(vr_world_interaction_remote(&r));assert(vr_world_interaction_remote_owned(1));
 struct network_interaction_hand enemy=r;enemy.player=8;assert(!vr_world_interaction_remote(&enemy));
 r.hand=1;assert(vr_world_interaction_remote(&r));
 tick=1;r.position.i=.15f;r.pressed=0;assert(vr_world_interaction_remote(&r));
 vr_world_interaction_remote_tick();assert(velocity_calls==1&&track_calls==1);
 r.held=0;assert(vr_world_interaction_remote(&r));assert(velocity_calls==1);
 r.hand=0;assert(vr_world_interaction_remote(&r));assert(velocity_calls==2);
 assert(!vr_world_interaction_remote_owned(1));
 r.held=r.pressed=1;assert(vr_world_interaction_remote(&r));int before=velocity_calls;
 vr_world_interaction_remote_cancel(7,0);assert(velocity_calls==before&&!vr_world_interaction_remote_owned(1));
 assert(vr_world_interaction_remote(&r));tick+=10;vr_world_interaction_remote_tick();assert(velocity_calls==before&&!vr_world_interaction_remote_owned(1));
 assert(vr_world_interaction_remote(&r));r.position.i=2;assert(!vr_world_interaction_remote(&r));assert(!vr_world_interaction_remote_owned(1));
 r.position.i=.1f;assert(vr_world_interaction_remote(&r));ready=0;vr_world_interaction_remote_tick();assert(!vr_world_interaction_remote_owned(1)&&velocity_calls==before);
 ready=1;assert(vr_world_interaction_remote(&r));owner_unit.object.damage_flags=FLAG(_object_dead_bit);
 vr_world_interaction_remote_tick();assert(!vr_world_interaction_remote_owned(1)&&velocity_calls==before);
 assert(!vr_world_interaction_remote(&r));owner_unit.object.damage_flags=0;
 assert(vr_world_interaction_remote(&r));owner_unit.object.parent_object_index=20;
 assert(!vr_world_interaction_remote(&r)&&!vr_world_interaction_remote_owned(1)&&velocity_calls==before);
 owner_unit.object.parent_object_index=NONE;
 puts("PASS: production remote world grip: host capability, collision-model palm contact, LOS guard, exclusive ownership, fresh press, two-hand release, cancellation/lease and native physics");
}
'''
c=out/'remote.c';c.write_text(stub+code+tests);binary=out/'remote'
subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
 '-I'+str(ROOT/'port/linux/game'),str(c),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
assert 'collision_model_test_pill(&model,&request->position,&stationary,contact_radius,&model_hit)' in code
finder=code[code.index('static long find_candidate('):code.index('boolean vr_world_interaction_remote(')]
assert 'collision_model_test_pill(' in finder and 'collision_test_vector(' not in finder
assert '.12f*units()' not in code and '.12f*u' not in code
