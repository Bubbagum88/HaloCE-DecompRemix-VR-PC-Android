"""Execute production detached-component trace and authored vertex-bound builder."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
manual=(ROOT/'port/linux/game/vr_manual_reload.c').read_text()
models=(ROOT/'source/models/models.c').read_text()
render=(ROOT/'port/linux/game/vr_render.c').read_text()
def function(text,name):
    start=text.index(name);start=text.rfind('\n',0,start)+1
    brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
assert 'if(vr_finger_reload_only)' in render
assert 'gripping && !vr_finger_reload_only' in render
assert 'vr_manual_reload_trace(from->n,v->n,extra_radius,&component)' in render
stub=r'''
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stddef.h>
#include "port/linux/game/vr_reload_contact_math.h"
typedef float real;typedef int boolean;
typedef union real_point3d {float n[3];struct{float x,y,z;};}real_point3d;
typedef union real_vector3d {float n[3];struct{float i,j,k;};}real_vector3d;
typedef struct real_matrix4x3 {float scale;union{struct{real_vector3d forward,left,up;real_point3d position;};float n[4][3];};}real_matrix4x3;
struct collision_result{int type;float t;real_point3d point;struct{real_vector3d n;float d;}plane;long object_index;};
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define MAXIMUM_GEOMETRIES_PER_MODEL 256
#define MAXIMUM_PARTS_PER_MODEL_GEOMETRY 32
#define _rasterizer_vertex_type_model_compressed 5
#define TAG_BLOCK_GET_ELEMENT(block,index,type) (&((type*)(block)->data)[index])
enum{_game_connection_local,RELOAD_MAGAZINE=0,RELOAD_SHELL,RELOAD_TUBES,RELOAD_CANISTER,RELOAD_CRYSTALS};
enum{VR_MR_IDLE,VR_MR_OLD_HELD,VR_MR_NEED_MAG,VR_MR_NEW_HELD,VR_MR_NEED_CHAMBER,VR_MR_CHAMBER_HELD,VR_MR_SEATING};
static struct{int ready,hand;double sample_time,grip_time;int bounds_valid[2],kind;struct{int phase;}state;real_matrix4x3 socket,charge,gun,held;float chamber_travel;real_point3d bounds_min[2],bounds_max[2];}reload;
enum{VR_INTERACTION_RELOAD=1};static int owner=VR_INTERACTION_RELOAD;
static int vr_interaction_owner(int hand){(void)hand;return owner;}
static int enabled=1,active=1,network;static double now=10;
static int config_boolean(char const*k){(void)k;return enabled;}
static int vr_active(void){return active;}
static int game_connection(void){return network;}
static double vr_pose_time(void){return now;}
static void reload_refresh_held_pose(void){}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float normalize3d(real_vector3d*v){float s=sqrtf(dot_product3d(v,v));if(s>0)for(int a=0;a<3;a++)v->n[a]/=s;return s;}
static void matrix4x3_transform_vector(real_matrix4x3 const*m,real_vector3d const*v,real_vector3d*out){for(int a=0;a<3;a++)out->n[a]=m->scale*(m->forward.n[a]*v->i+m->left.n[a]*v->j+m->up.n[a]*v->k);}
static void matrix4x3_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){matrix4x3_transform_vector(m,(real_vector3d const*)p,(real_vector3d*)out);for(int a=0;a<3;a++)out->n[a]+=m->position.n[a];}
static void matrix4x3_inverse_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){real_vector3d d;for(int a=0;a<3;a++)d.n[a]=(p->n[a]-m->position.n[a])/m->scale;out->x=dot_product3d(&d,&m->forward);out->y=dot_product3d(&d,&m->left);out->z=dot_product3d(&d,&m->up);}
static real_matrix4x3 identity(void){real_matrix4x3 m={0};m.scale=1;m.forward.i=m.left.j=m.up.k=1;return m;}
struct block{int count;void*data;};
struct model_node{short parent_node_index;real_matrix4x3 runtime_default_inverse_matrix;};
struct model{struct block nodes,geometries;};
struct model_geometry{struct block parts;};
struct model_vertex_compressed{real_point3d position;unsigned char nodes[2];short node_weight;};
struct buffer{int count,type;void*data;};
struct model_geometry_part{struct buffer vertex_buffer,triangle_buffer;};
static struct model model;
static struct model*model_definition_get(long index){(void)index;return &model;}
static int rasterizer_model_buffer_data(struct buffer const*v,struct buffer const*t,void const**out,void const**indices){(void)t;*out=v->data;*indices=NULL;return 1;}
'''
code=stub+function(manual,'static boolean reload_matrix_valid(')+function(manual,'int vr_manual_reload_trace(')
code+=function(manual,'int vr_manual_reload_hand(')
code+=function(models,'boolean model_rigid_component_bounds(')+function(models,'boolean model_rigid_node_bounds(')
code+=r'''
int main(void){
 struct collision_result hit;float from[3]={-2,0,0},delta[3]={4,0,0};
 reload.ready=1;reload.sample_time=now;reload.bounds_valid[0]=1;
 reload.socket=reload.held=reload.charge=reload.gun=identity();
 for(int a=0;a<3;a++){reload.bounds_min[0].n[a]=-.5f;reload.bounds_max[0].n[a]=.5f;}
 assert(vr_manual_reload_trace(from,delta,0,&hit)&&fabsf(hit.t-.375f)<1e-6f&&hit.plane.n.i==-1&&hit.object_index==NONE);
 enabled=0;memset(&hit,0x77,sizeof hit);struct collision_result before=hit;
 assert(!vr_manual_reload_trace(from,delta,0,&hit)&&!memcmp(&hit,&before,sizeof hit));enabled=1;
 network=1;assert(!vr_manual_reload_trace(from,delta,0,&hit));network=0;
 reload.sample_time=now-.3;assert(!vr_manual_reload_trace(from,delta,0,&hit));reload.sample_time=now;
 reload.state.phase=VR_MR_NEED_MAG;assert(!vr_manual_reload_trace(from,delta,0,&hit));
 reload.state.phase=VR_MR_NEW_HELD;reload.held.position.x=4;
 assert(!vr_manual_reload_trace(from,delta,0,&hit));from[0]=2;
 assert(vr_manual_reload_trace(from,delta,0,&hit)&&fabsf(hit.t-.375f)<1e-6f);
 reload.held.scale=2;assert(vr_manual_reload_trace(from,delta,.1f,&hit)&&fabsf(hit.t-.225f)<1e-6f);
 from[0]=4;assert(vr_manual_reload_trace(from,delta,0,&hit)&&hit.t==0);
 reload.held.scale=NAN;assert(!vr_manual_reload_trace(from,delta,0,&hit));reload.held=identity();
 reload.bounds_min[0]=(real_point3d){-.5f,-.1f,-.1f};reload.bounds_max[0]=(real_point3d){.5f,.1f,.1f};
 reload.held.forward=(real_vector3d){0,1,0};reload.held.left=(real_vector3d){-1,0,0};
 from[0]=0;from[1]=-2;delta[0]=0;delta[1]=4;
 assert(vr_manual_reload_trace(from,delta,0,&hit)&&fabsf(hit.t-.375f)<1e-6f&&hit.plane.n.j==-1);
 reload.kind=RELOAD_SHELL;reload.state.phase=VR_MR_IDLE;assert(!vr_manual_reload_trace(from,delta,0,&hit));
 reload.kind=RELOAD_CRYSTALS;assert(!vr_manual_reload_trace(from,delta,0,&hit));
 reload.kind=RELOAD_MAGAZINE;reload.state.phase=VR_MR_NEW_HELD;reload.held=identity();
 float palm[3]={.8f,0,0};reload.grip_time=now;
 assert(vr_manual_reload_hand(0,palm)&&palm[0]==.8f); /* no visual snap at acquisition */
 now+=.04;assert(vr_manual_reload_hand(0,palm)&&fabsf(palm[0]-.65f)<1e-5f);
 now+=.04;assert(vr_manual_reload_hand(0,palm)&&fabsf(palm[0]-.5f)<1e-5f);
 owner=0;palm[0]=.8f;assert(!vr_manual_reload_hand(0,palm)&&palm[0]==.8f);owner=1;
 assert(!vr_manual_reload_hand(1,palm)&&palm[0]==.8f);
 struct model_node nodes[3]={{.parent_node_index=-1},{.parent_node_index=0},{.parent_node_index=1}};
 nodes[1].runtime_default_inverse_matrix=identity();nodes[1].runtime_default_inverse_matrix.position.x=-5;
 struct model_vertex_compressed vertices[4]={{{4,1,2},{3,0},32767},{{6,3,4},{6,0},32767},{{999,999,999},{0,0},32767},{{888,888,888},{3,0},16000}};
 struct model_geometry_part part={.vertex_buffer={4,5,vertices}};
 struct model_geometry geometry={{1,&part}};model.nodes=(struct block){3,nodes};model.geometries=(struct block){1,&geometry};
 real_point3d lo,hi;assert(model_rigid_node_bounds(0,1,&lo,&hi));
 assert(lo.x==-1&&hi.x==1&&lo.y==1&&hi.y==3&&lo.z==2&&hi.z==4);
 assert(model_rigid_component_bounds(0,1,1ULL<<2,&lo,&hi)&&lo.x==1&&hi.x==1);
 part.vertex_buffer.count=65536;assert(!model_rigid_node_bounds(0,1,&lo,&hi));
 part.vertex_buffer.count=4;vertices[0].position.x=NAN;assert(!model_rigid_node_bounds(0,1,&lo,&hi));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'contact.c';exe=Path(tmp)/'contact';c.write_text(code)
    subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-Wno-missing-braces','-fsanitize=address,undefined','-I',str(ROOT),str(c),'-lm','-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('reload component contact: production bounds + trace pass (ASan/UBSan)')
