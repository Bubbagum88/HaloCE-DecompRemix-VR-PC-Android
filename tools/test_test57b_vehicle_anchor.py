"""Test57b: the immersive controls sit on the vehicle, wherever it is.

Owner's Test57 session (2026-10-11 21:03 and 21:04 logs): every Warthog grip
missed by about 540 m and every Scorpion grip by about 2 m. The Warthog's
wheel was placed from object_marker.node_matrix, which is the marker's
few-centimetre offset from its node, not the node in the world, so the wheel
sat at the map's origin (Test56 and Test57); the Scorpion's stick sat between
its driver's hands, inside the hull. This replays the real
vr_vehicle_handles_prepare / vr_wheel_place (extracted from the header) with
engine-shaped markers (node_matrix local, matrix in the world) built from the
stock Warthog's wheel node and grip markers (USA Xbox Blood Gulch), for every
control kind, at many places, headings and tilts: the controls must be where
the vehicle's own frame says, a hand there must take them, and they must move
with the vehicle.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
s = (ROOT / 'port/linux/game/vr_vehicle_handles.h').read_text()


def fn(name):
    m = re.search(r'^(?:static )?[\w *]+\b' + name + r'\s*\([^;{}]*\)\s*\{', s, re.M)
    assert m, name
    e = m.end()
    d = 1
    while d:
        d += (s[e] == '{') - (s[e] == '}')
        e += 1
    return s[m.start():e] + '\n'


state = s[s.index('static struct {\n    long unit, vehicle;'):s.index('} vr_wheel;') + len('} vr_wheel;')] + '\n'
tables = s[s.index('static char const *const vr_wheel_keys'):s.index('#define VR_BAR_SLIDE 0.12f') + len('#define VR_BAR_SLIDE 0.12f')] + '\n'
# Test59: the chest place and COMFORT REACH distances
tables += s[s.index('#define VR_CHEST_AHEAD'):s.index('#define VR_COMFORT_REACH 0.55f') + len('#define VR_COMFORT_REACH 0.55f')] + '\n'
# Test61: a marker gone wrong past 1.5 m
tables += s[s.index('#define VR_FAR_REACH'):s.index('#define VR_FAR_REACH 1.5f') + len('#define VR_FAR_REACH 1.5f')] + '\n'

code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "port/linux/game/vr_vehicle_controls_math.h"
typedef float real;
typedef union {struct {float x,y,z;};float n[3];} real_point3d;
typedef union {struct {float i,j,k;};float n[3];} real_vector3d;
typedef struct {real_vector3d forward,left,up;real_point3d position;} real_matrix4x3;
struct object_marker {short node_index;real_matrix4x3 node_matrix,matrix;};
struct unit_datum {struct {unsigned long damage_flags;} object;};
struct object_datum {struct {struct {long size;} node_matrices;} object;long definition_index;};
#define NONE (-1)
#define TEST_FLAG(f,b) (((f)>>(b))&1u)
#define _object_dead_bit 0
#define PIN(x,l,h) ((x)<(l)?(l):((x)>(h)?(h):(x)))
#define VR_INTERACTION_VEHICLE 2
#define platform_log(...) (printf("  log: "),printf(__VA_ARGS__),printf("\n"))
static const float UNITS=0.32808399f; /* world units a metre (the engine's) */
static float vr_units_per_metre(void){return UNITS;}
static float dot_product3d(const real_vector3d*a,const real_vector3d*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(const real_vector3d*v){return sqrtf(dot_product3d(v,v));}
static void vector_from_points3d(const real_point3d*a,const real_point3d*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static void cross_product3d(const real_vector3d*a,const real_vector3d*b,real_vector3d*c){real_vector3d r={{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};*c=r;}
static float normalize3d(real_vector3d*v){float m=magnitude3d(v);if(m>0)for(int i=0;i<3;i++)v->n[i]/=m;return m;}
static int valid_real_point3d(const real_point3d*p){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
static void vr_interaction_release(int h,int o){(void)h;(void)o;}
static struct {struct {long vehicle_index;short seat_index;} seat;real_point3d game_camera_position;} vr_render;
static int vr_settings_generation(void){return 1;}
static double clock_now;static double vr_pose_time(void){return clock_now;}
static int vr_vehicle_handles_enabled(long u){(void)u;return 1;}
static float cfg_all[3],cfg_vehicle[3];
static float config_real(char const*k){if(strstr(k,"vr.handle_")&&!strstr(k,"_size")){int i=strstr(k,"_forward")?0:strstr(k,"_left")?1:2;return strstr(k,"_all_")?cfg_all[i]:cfg_vehicle[i];}if(!strcmp(k,"vr.interaction_reach"))return .04f;if(strstr(k,"_size"))return 1;return 0;}
static int cfg_comfort=1,cfg_visible=1;
static int config_boolean(char const*k){if(!strcmp(k,"vr.vehicle_comfort_reach"))return cfg_comfort;if(!strcmp(k,"vr.vehicle_wheel_visible"))return cfg_visible;return 1;}
static real_matrix4x3 *render_interpolation_object_node_matrices(long o){(void)o;return NULL;}
/* Test63: no calibration rows on screen; the fixture's vehicle has no wheel bone */
static int vr_calibration_shown(int m){(void)m;return 0;}
struct object_definition {struct {struct {long index;} model;} object;};
static struct object_definition vehicle_definition={{{NONE}}};
static struct object_definition *object_definition_get(long i){(void)i;return &vehicle_definition;}
static short model_find_node(long m,char const*n){(void)m;(void)n;return NONE;}
/* Test61: the hands' heading in a seat is the seat's (the vehicle's yaw) */
static const real_matrix4x3 *heading_source;
static int vr_heading_forward(float f[3]){float h=atan2f(heading_source->forward.j,heading_source->forward.i);f[0]=cosf(h);f[1]=sinf(h);f[2]=0;return 1;}
/* the world: the player's unit (1) in a vehicle (2) */
static struct unit_datum unit;static struct object_datum vehicle;
static char const *vehicle_name;
static real_matrix4x3 nodes[8];
static struct unit_datum *unit_try_and_get(long i){return i==1?&unit:NULL;}
static struct object_datum *object_try_and_get(long i){return i==2?&vehicle:NULL;}
static real_matrix4x3 *object_get_node_matrices(long i){return i==2?nodes:NULL;}
static char const *tag_get_name(long d){(void)d;return vehicle_name;}
/* marker stand-ins as the engine makes them: node_matrix is the marker's
 * offset in its node, matrix the marker in the world (node x offset) */
static struct {char const *name;long object;short node;real_point3d local;} markers_defined[4];static int marker_count;
static void transform_point(const real_matrix4x3*m,const real_point3d*p,real_point3d*o){for(int k=0;k<3;k++)o->n[k]=m->position.n[k]+m->forward.n[k]*p->x+m->left.n[k]*p->y+m->up.n[k]*p->z;}
static short object_get_marker_by_name(long object,char const*name,struct object_marker*out,short count){
 (void)count;
 for(int m=0;m<marker_count;m++)if(markers_defined[m].object==object&&!strcmp(markers_defined[m].name,name)){
  real_matrix4x3 local={{{1,0,0}},{{0,1,0}},{{0,0,1}},markers_defined[m].local};
  out->node_index=markers_defined[m].node;out->node_matrix=local;
  out->matrix=local;transform_point(object==2?&nodes[out->node_index]:&nodes[7],&markers_defined[m].local,&out->matrix.position);
  if(object==2)out->matrix.forward=nodes[out->node_index].forward,out->matrix.left=nodes[out->node_index].left,out->matrix.up=nodes[out->node_index].up;
  return 1;}
 return 0;}
'''+state+tables+fn('vr_vehicle_handles_clear')+fn('vr_wheel_point')+fn('vr_wheel_valid_frame')+fn('vr_wheel_hand_frame')+fn('vr_wheel_place')+fn('vr_wheel_read_user')+fn('vr_vehicle_handles_prepare')+fn('vr_wheel_grip_distance')+r'''
/* a vehicle frame: yaw, then pitch (nose up), then roll, at a place */
static real_matrix4x3 frame(float x,float y,float z,float yaw,float pitch,float roll){
 real_matrix4x3 m;float cy=cosf(yaw),sy=sinf(yaw),cp=cosf(pitch),sp=sinf(pitch),cr=cosf(roll),sr=sinf(roll);
 real_vector3d f={{cy*cp,sy*cp,sp}},l0={{-sy,cy,0}},u0;cross_product3d(&f,&l0,&u0);
 for(int k=0;k<3;k++){m.left.n[k]=l0.n[k]*cr+u0.n[k]*sr;m.up.n[k]=u0.n[k]*cr-l0.n[k]*sr;}
 m.forward=f;m.position=(real_point3d){{x,y,z}};return m;}
/* the stock Warthog (vehicles\warthog\warthog, model space, world units):
 * hull node at (0,0,.42); "frame steering wheel" node 6 at (.147,.170,.541),
 * forward (.17,0,.98), up (-.98,0,.17); grips "left/right hand wheel grip" on
 * node 6 at (.154,.213,.544) and (.142,.127,.509); "camera driver" (.007,.168,.626) */
static real_point3d to_model(const real_matrix4x3*vehicle_frame,real_point3d p){real_point3d o;transform_point(vehicle_frame,&p,&o);return o;}
static void node_from_model(const real_matrix4x3*v,int node,real_point3d pos,real_vector3d fwd,real_vector3d up){
 real_matrix4x3 n;n.position=to_model(v,pos);
 for(int k=0;k<3;k++){n.forward.n[k]=v->forward.n[k]*fwd.i+v->left.n[k]*fwd.j+v->up.n[k]*fwd.k;n.up.n[k]=v->forward.n[k]*up.i+v->left.n[k]*up.j+v->up.n[k]*up.k;}
 normalize3d(&n.forward);normalize3d(&n.up);cross_product3d(&n.up,&n.forward,&n.left);nodes[node]=n;}
static void local_in_node(int node,real_point3d world,real_point3d*local){real_vector3d d;vector_from_points3d(&nodes[node].position,&world,&d);
 local->x=dot_product3d(&d,&nodes[node].forward);local->y=dot_product3d(&d,&nodes[node].left);local->z=dot_product3d(&d,&nodes[node].up);}
static float cm(real_point3d a,real_point3d b){real_vector3d d;vector_from_points3d(&a,&b,&d);return magnitude3d(&d)/UNITS*100;}
static int failures;
static void enter(int kind,const real_matrix4x3*v){
 memset(&vr_wheel,0,sizeof vr_wheel);vr_vehicle_handles_clear();clock_now=10;
 vehicle_name=kind==0?"vehicles\\warthog\\warthog":kind==1?"vehicles\\ghost\\ghost_mp":kind==2?"vehicles\\scorpion\\scorpion_mp":"vehicles\\banshee\\banshee";
 vehicle.object.node_matrices.size=8*sizeof(real_matrix4x3);
 node_from_model(v,0,(real_point3d){{0,0,.42f}},(real_vector3d){{1,0,0}},(real_vector3d){{0,0,1}});
 node_from_model(v,6,(real_point3d){{.147f,.170f,.541f}},(real_vector3d){{.17f,0,.98f}},(real_vector3d){{-.98f,0,.17f}});
 node_from_model(v,7,(real_point3d){{0,0,0}},(real_vector3d){{1,0,0}},(real_vector3d){{0,0,1}}); /* the driver unit's root */
 vr_render.seat.vehicle_index=2;vr_render.seat.seat_index=0;heading_source=&nodes[0];
 vr_render.game_camera_position=to_model(v,(real_point3d){{.007f,.168f,.626f}});
 marker_count=0;
 {real_point3d l,r;local_in_node(6,to_model(v,(real_point3d){{.154f,.213f,.544f}}),&l);local_in_node(6,to_model(v,(real_point3d){{.142f,.127f,.509f}}),&r);
  markers_defined[marker_count++]=(typeof(markers_defined[0])){"left hand wheel grip",2,6,l};
  markers_defined[marker_count++]=(typeof(markers_defined[0])){"right hand wheel grip",2,6,r};}
 /* the driver's hands: on the Ghost's bars (in reach), inside the
  * Scorpion's and Banshee's hulls (about 2 m off, as in the owner's log) */
 {real_point3d l=kind==1?(real_point3d){{.20f,.15f,.48f}}:(real_point3d){{.55f,.20f,-.05f}},r=l;r.y=-r.y;
  markers_defined[marker_count++]=(typeof(markers_defined[0])){"left hand",1,0,l};
  markers_defined[marker_count++]=(typeof(markers_defined[0])){"right hand",1,0,r};
  node_from_model(v,7,(real_point3d){{0,0,0}},(real_vector3d){{1,0,0}},(real_vector3d){{0,0,1}});}
 assert(!vr_vehicle_handles_prepare(1)); /* the entry animation's half second */
 clock_now+=1;assert(vr_vehicle_handles_prepare(1)&&vr_wheel.valid);
}
static void check(char const*what,int ok){if(!ok){printf("FAIL: %s\n",what);failures++;}}
int main(void){
 real_matrix4x3 places[]={frame(0,0,0,0,0,0),frame(98.493f,-157.639f,1.705f,1.328f,0,0),frame(-512,833,41,3.5f,.25f,.1f),
  frame(300,300,-20,-2.2f,-.3f,-.15f),frame(.5f,-.7f,3,.9f,.6f,.3f)};
 for(int p=0;p<(int)(sizeof places/sizeof places[0]);p++)for(int kind=0;kind<4;kind++){
  real_matrix4x3 *v=&places[p];enter(kind,v);
  real_point3d head=vr_render.game_camera_position;float gap=cm(head,vr_wheel.center);
  printf("place %d %-8s center %5.1f cm from the eyes (%s)\n",p,vr_wheel_keys[kind],gap,vr_wheel.anchored);
  check("controls within a metre of the eyes",gap<100);
  if(kind==0){
   /* the wheel: on the stock wheel node, 2.5 cm toward the driver */
   real_point3d expected=nodes[6].position;for(int k=0;k<3;k++)expected.n[k]+=nodes[6].up.n[k]*.025f*UNITS;
   check("Warthog wheel on its wheel node",cm(expected,vr_wheel.center)<0.5f);
   check("Warthog wheel faces the driver",dot_product3d(&vr_wheel.normal,&nodes[6].up)>.99f);
   check("Warthog wheel radius ~15 cm",fabsf(vr_wheel.radius/UNITS-.15f)<.03f);
  }
  if(kind==1){
   /* the Ghost: between the driver's hands on its bars; Test59: this
    * fixture's 90 cm comes in to 55 cm from the eyes on the same line
    * (COMFORT REACH) */
   real_point3d l,r,mid,expected;transform_point(&nodes[7],&markers_defined[2].local,&l);transform_point(&nodes[7],&markers_defined[3].local,&r);
   for(int k=0;k<3;k++)mid.n[k]=(l.n[k]+r.n[k])/2;
   {real_vector3d to;vector_from_points3d(&head,&mid,&to);float g=magnitude3d(&to);
    for(int k=0;k<3;k++)expected.n[k]=head.n[k]+to.n[k]*(g>.55f*UNITS?.55f*UNITS/g:1.0f);}
   check("Ghost bar on the line to its hand contacts, within comfort reach",cm(expected,vr_wheel.center)<0.5f&&gap<55.5f);
  }
  if(kind>=2){
   /* stick and bar: 35 cm ahead of and 40 cm below the eyes (Test61: in
    * the hands' level frame, turned to the vehicle's heading) */
   real_point3d expected=head;real_vector3d level=nodes[0].forward;level.k=0;normalize3d(&level);
   for(int k=0;k<3;k++)expected.n[k]+=level.n[k]*.35f*UNITS-(k==2?.40f*UNITS:0);
   check("stick/bar in front of the chest",cm(expected,vr_wheel.center)<0.5f);
  }
  /* a hand on each control takes it */
  for(int h=0;h<2;h++){
   real_point3d hand=vr_wheel.target[h];
   float d=vr_wheel_grip_distance(h,&hand)/UNITS*100;check("a hand on the control is in reach",d<=1.0f);
   if(kind==0){ /* anywhere on the rim, and on a spoke */
    for(int a=0;a<8;a++){real ang=a*.785f,r=vr_wheel.radius;real_point3d rim=vr_wheel_point(0,r*cosf(ang),r*sinf(ang));
     check("Warthog rim in reach",vr_wheel_grip_distance(h,&rim)/UNITS*100<=1.0f);}
    real_point3d spoke=vr_wheel_point(0,vr_wheel.radius*.6f,0);check("Warthog spoke in reach",vr_wheel_grip_distance(h,&spoke)/UNITS*100<=1.0f);
   }
  }
  /* the vehicle drives on 40 m, turns and pitches: the controls go with
   * it, in the same place from the eyes in the hands' frame (Test61: its
   * heading, not its pitch and roll, which the hands do not follow) */
  {real_vector3d before;vector_from_points3d(&vr_wheel.root.position,&vr_wheel.center,&before);
   float bf=dot_product3d(&before,&vr_wheel.root.forward),bl=dot_product3d(&before,&vr_wheel.root.left),bu=dot_product3d(&before,&vr_wheel.root.up);
   real_matrix4x3 moved=frame(v->position.x+13,v->position.y-6,v->position.z+1,1.1f,.1f,0);
   real_matrix4x3 root=moved;root.position=to_model(&moved,(real_point3d){{0,0,.42f}});
   vr_render.game_camera_position=to_model(&moved,(real_point3d){{.007f,.168f,.626f}}); /* the eyes ride along */
   heading_source=&root;
   vr_wheel_place(&root);
   real_vector3d after;vector_from_points3d(&vr_render.game_camera_position,&vr_wheel.center,&after);
   check("controls move with the vehicle's place and heading",fabsf(dot_product3d(&after,&vr_wheel.root.forward)-bf)<1e-4f&&fabsf(dot_product3d(&after,&vr_wheel.root.left)-bl)<1e-4f&&fabsf(dot_product3d(&after,&vr_wheel.root.up)-bu)<1e-4f);
   check("the hands' frame is level, turned to the vehicle",vr_wheel.root.up.k==1.0f&&fabsf(atan2f(vr_wheel.root.forward.j,vr_wheel.root.forward.i)-1.1f)<1e-4f);
   heading_source=&nodes[0];}
 }
 /* Test59: the Scorpion's boarding animation: the eyes end 2 m from where
  * they were half a second in (the owner's log: every squeeze 2.2 m off);
  * the stick follows the eyes, in reach, and takes a hand */
 for(int kind=2;kind<4;kind++){real_matrix4x3 v=frame(98.493f,-157.639f,1.705f,1.328f,0,0);enter(kind,&v);
  real_matrix4x3 root=nodes[0];
  for(int k=0;k<3;k++)vr_render.game_camera_position.n[k]+=root.left.n[k]*2.0f*UNITS-root.up.n[k]*.6f*UNITS;
  vr_wheel_place(&root);
  check("stick/bar follows the eyes after boarding",fabsf(cm(vr_render.game_camera_position,vr_wheel.center)-53.15f)<1.0f);
  {real_point3d hand=vr_wheel.target[0];check("stick/bar after boarding takes a hand",vr_wheel_grip_distance(0,&hand)/UNITS*100<=1.0f);}}
 /* Test59: a Warthog wheel 97 cm from the eyes (the owner's log) comes in
  * to 55 cm along the same line; hidden (VIRTUAL WHEEL), it stays on the
  * model's wheel; COMFORT REACH off, it stays on the vehicle's place */
 {real_matrix4x3 v=frame(98.493f,-157.639f,1.705f,1.328f,0,0);enter(0,&v);
  real_matrix4x3 root=nodes[0];real_point3d model_wheel;
  for(int k=0;k<3;k++)vr_render.game_camera_position.n[k]+=-root.forward.n[k]*.42f*UNITS+root.up.n[k]*.12f*UNITS;
  /* Test61: measured from the eyes on boarding: board with them there */
  vr_wheel.valid=0;vr_wheel.settle_sampled=0;clock_now+=1;assert(!vr_vehicle_handles_prepare(1));
  clock_now+=.36;assert(vr_vehicle_handles_prepare(1));
  model_wheel=nodes[6].position;for(int k=0;k<3;k++)model_wheel.n[k]+=nodes[6].up.n[k]*.025f*UNITS;
  {float far_gap=cm(vr_render.game_camera_position,model_wheel);
   printf("Warthog wheel %.0f cm from the eyes: comes in to %.1f cm\n",far_gap,cm(vr_render.game_camera_position,vr_wheel.center));
   check("Warthog wheel past 55 cm (test setup)",far_gap>80&&far_gap<100);}
  check("Warthog wheel comes in to 55 cm",fabsf(cm(vr_render.game_camera_position,vr_wheel.center)-55)<0.5f);
  {real_vector3d a,b;vector_from_points3d(&vr_render.game_camera_position,&model_wheel,&a);vector_from_points3d(&vr_render.game_camera_position,&vr_wheel.center,&b);
   normalize3d(&a);normalize3d(&b);check("on the same line from the eyes",dot_product3d(&a,&b)>.9999f);}
  {real_point3d hand=vr_wheel.target[0];check("the near wheel takes a hand",vr_wheel_grip_distance(0,&hand)/UNITS*100<=1.0f);}
  cfg_visible=0;assert(vr_vehicle_handles_prepare(1));vr_wheel_place(&root);
  check("hidden wheel stays on the model's wheel",cm(nodes[6].position,vr_wheel.center)<0.5f);
  cfg_visible=1;cfg_comfort=0;assert(vr_vehicle_handles_prepare(1));vr_wheel_place(&root);
  check("COMFORT REACH off: the vehicle's place",cm(model_wheel,vr_wheel.center)<0.5f);
  cfg_comfort=1;}
 /* a control whose authored place is wrong is put in front of the chest */
 {real_matrix4x3 v=frame(98.493f,-157.639f,1.705f,1.328f,0,0);enter(1,&v);
  markers_defined[2].local=(real_point3d){{-400,500,10}};markers_defined[3].local=(real_point3d){{-400,500,10}};
  memset(&vr_wheel,0,sizeof vr_wheel);vr_vehicle_handles_clear();clock_now=10;assert(!vr_vehicle_handles_prepare(1));clock_now+=1;assert(vr_vehicle_handles_prepare(1));
  check("a far authored place falls back in reach",cm(vr_render.game_camera_position,vr_wheel.center)<100);}
 /* a vehicle (or driver) without the markers still gets its controls, in reach */
 for(int kind=0;kind<4;kind+=3){real_matrix4x3 v=frame(-512,833,41,3.5f,.25f,.1f);enter(kind,&v);
  marker_count=0;memset(&vr_wheel,0,sizeof vr_wheel);vr_vehicle_handles_clear();clock_now=10;assert(!vr_vehicle_handles_prepare(1));clock_now+=1;
  check("no markers: controls still placed",vr_vehicle_handles_prepare(1)&&vr_wheel.valid);
  check("no markers: controls in reach",cm(vr_render.game_camera_position,vr_wheel.center)<100);
  {real_point3d hand=vr_wheel.target[0];check("no markers: a hand there takes them",vr_wheel_grip_distance(0,&hand)/UNITS*100<=1.0f);}}
 /* the head not yet placed in the vehicle (no frame drawn): wait */
 {real_matrix4x3 v=frame(98.493f,-157.639f,1.705f,1.328f,0,0);enter(0,&v);
  memset(&vr_wheel,0,sizeof vr_wheel);vr_vehicle_handles_clear();vr_render.game_camera_position=(real_point3d){{0,0,0}};clock_now=10;assert(!vr_vehicle_handles_prepare(1));clock_now+=1;
  check("no controls placed from a head outside the vehicle",!vr_vehicle_handles_prepare(1)&&!vr_wheel.valid);}
 /* Test62: moving boarding eyes cannot lock early; moving the entire
  * vehicle with the eyes does not restart settling. */
 {real_matrix4x3 v=frame(0,0,0,0,0,0);enter(0,&v);
  vr_vehicle_handles_clear();clock_now=20;assert(!vr_vehicle_handles_prepare(1));
  for(int t=1;t<=9;t++){clock_now=20+t*.2;vr_render.game_camera_position.z+=.02f*UNITS;assert(!vr_vehicle_handles_prepare(1));}
  clock_now=22.0;nodes[0].position.x+=1;vr_render.game_camera_position.x+=1;assert(!vr_vehicle_handles_prepare(1));
  clock_now=22.16;assert(vr_vehicle_handles_prepare(1)&&vr_wheel.valid);}
 /* Persistent idle motion still gets controls at the 3 second cap. */
 {real_matrix4x3 v=frame(0,0,0,0,0,0);enter(2,&v);
  vr_vehicle_handles_clear();clock_now=30;assert(!vr_vehicle_handles_prepare(1));
  for(int t=1;t<15;t++){clock_now=30+t*.2;vr_render.game_camera_position.z+=.016f*UNITS;assert(!vr_vehicle_handles_prepare(1));}
  clock_now=33;vr_render.game_camera_position.z+=.016f*UNITS;assert(vr_vehicle_handles_prepare(1));}
 /* All-control offsets combine with each vehicle's own offsets; zero is
  * unchanged, and corrupt/nonfinite settings cannot move controls to NaN. */
 for(int kind=0;kind<4;kind++){real_matrix4x3 v=frame(0,0,0,0,0,0);enter(kind,&v);
  cfg_all[0]=.1f;cfg_vehicle[0]=.05f;cfg_all[1]=.45f;cfg_vehicle[1]=.4f;cfg_all[2]=NAN;cfg_vehicle[2]=.02f;
  assert(vr_vehicle_handles_prepare(1));assert(fabsf(vr_wheel.user[0]/UNITS-.15f)<1e-5f);
  assert(fabsf(vr_wheel.user[1]/UNITS-.5f)<1e-5f&&fabsf(vr_wheel.user[2]/UNITS-.02f)<1e-5f);
  memset(cfg_all,0,sizeof cfg_all);memset(cfg_vehicle,0,sizeof cfg_vehicle);}
 if(failures){printf("%d failures\n",failures);return 1;}
 puts("PASS: Test57b immersive controls on the vehicle (stock Warthog wheel node, Ghost contacts, Scorpion/Banshee in front of the chest) at 5 places/headings/tilts, every control in reach, rim and spokes taken, moving with the vehicle's place and heading (Test61: in the hands' level frame), far places falling back, never placed from a head outside the vehicle; Test59: stick/bar from the eyes each frame (boarding), comfort reach 55 cm, hidden wheel on the model, comfort off");
 return 0;}
'''
with tempfile.TemporaryDirectory(prefix='test57b-') as d:
    p = Path(d)
    (p / 't.c').write_text(code)
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wno-unused-function', '-Wno-unused-variable', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', '-I', str(ROOT), str(p / 't.c'), '-lm', '-o', str(p / 't')], check=True)
    subprocess.run([str(p / 't')], check=True)
