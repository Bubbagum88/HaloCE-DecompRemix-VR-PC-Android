"""Test38 virtual cockpit control replay: real steering function and geometry."""
from pathlib import Path
import re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'port/linux/game/vr_vehicle_handles.h').read_text()
def fn(n):
 m=re.search(r'^(?:static )?[\w *]+\b'+n+r'\s*\([^;{}]*\)\s*\{',s,re.M);assert m,n
 e=m.end();d=1
 while d:d+=(s[e]=='{')-(s[e]=='}');e+=1
 return s[m.start():e]+'\n'
code=r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "port/linux/game/vr_vehicle_controls_math.h"
typedef float real;typedef int boolean;
typedef union {struct {float x,y,z;};float n[3];} real_point3d;
typedef union {struct {float i,j,k;};float n[3];} real_vector3d;
typedef struct {real_vector3d forward,left,up;real_point3d position;}real_matrix4x3;
#define VR_INTERACTION_VEHICLE 2
static struct {long unit;int kind,valid,log_pending,down[2];real_matrix4x3 root;real_point3d center,target[2];float radius,angle;struct vr_wheel_grip grip[2];}vr_wheel;
static struct {real_point3d game_camera_position;}vr_render;
static const char *vr_wheel_keys[]={"warthog","ghost","scorpion","banshee"};
#define platform_log(...) ((void)0)
static int input_valid=1;
static int eligible=1,held[2],pressed[2],released[2],tracked[2]={1,1},owner[2],buzz;static real_point3d pose[2];
static int vr_controller(unsigned int*b,float*t,float*s){return input_valid;}
static void vr_vehicle_handles_clear(void){for(int h=0;h<2;h++){vr_wheel.down[h]=1;vr_wheel.grip[h].held=0;owner[h]=0;}}
static int vr_vehicle_handles_prepare(long u){return eligible;}
static int vr_interaction_grip(int h,int*p,int*r){*p=pressed[h];*r=released[h];return held[h];}
static int vr_hand_world(int h,float*a,float*b,float*c,float*d){memcpy(b,pose[h].n,12);return tracked[h];}
static int vr_interaction_owner(int h){return owner[h];}
static int vr_interaction_claim(int h,int o){if(owner[h]&&owner[h]!=o)return 0;owner[h]=o;return 1;}
static void vr_interaction_release(int h,int o){if(owner[h]==o)owner[h]=0;}
static void vr_haptic(int h,float a,float b){buzz++;}
static float vr_units_per_metre(void){return 1;}
static void vector_from_points3d(const real_point3d*a,const real_point3d*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static float dot_product3d(const real_vector3d*a,const real_vector3d*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(const real_vector3d*v){return sqrtf(dot_product3d(v,v));}
static float vr_yaw(const real_vector3d*v){return atan2f(v->j,v->i);}
'''+fn('vr_vehicle_handles_update')+r'''
static void hands(float angle){for(int h=0;h<2;h++){float sign=h?-1:1;pose[h]=(real_point3d){{0,sign*.2f*cosf(angle),sign*.2f*sinf(angle)}};}}
int main(void){
 struct vr_wheel_grip g;float p[2]={-1,.001f},q[2]={-1,-.001f};vr_wheel_grip_start(&g,p,0);assert(fabsf(vr_wheel_grip_angle(&g,q))<.003f);
 q[0]=NAN;assert(vr_wheel_grip_angle(&g,q)==g.base);p[0]=p[1]=0;vr_wheel_grip_start(&g,p,0);assert(!g.held);
 vr_wheel.root.forward=(real_vector3d){{1,0,0}};vr_wheel.root.left=(real_vector3d){{0,1,0}};vr_wheel.root.up=(real_vector3d){{0,0,1}};
 vr_wheel.target[0]=(real_point3d){{0,.2f,0}};vr_wheel.target[1]=(real_point3d){{0,-.2f,0}};
 real_vector3d f={{1,0,0}};hands(0);assert(!vr_vehicle_handles_update(1,&f));
 held[0]=held[1]=pressed[0]=pressed[1]=1;assert(vr_vehicle_handles_update(1,&f));assert(buzz==2&&fabsf(f.j)<1e-6);
 pressed[0]=pressed[1]=0;hands(.4f);assert(vr_vehicle_handles_update(1,&f));assert(fabsf(atan2f(f.j,f.i)-.4f)<1e-5);
 held[1]=0;released[1]=1;hands(.6f);assert(vr_vehicle_handles_update(1,&f));assert(!owner[1]&&owner[0]==2);assert(fabsf(atan2f(f.j,f.i)-.6f)<1e-5);
 owner[0]=0;assert(!vr_vehicle_handles_update(1,&f));assert(!vr_wheel.grip[0].held); /* recenter/ownership reset */
 hands(0);vr_wheel.down[0]=0;pressed[0]=1;held[0]=1;vr_wheel.angle=0;assert(vr_vehicle_handles_update(1,&f));pressed[0]=0;tracked[0]=0;assert(!vr_vehicle_handles_update(1,&f)&&!owner[0]);
 tracked[0]=1;assert(!vr_vehicle_handles_update(1,&f)); /* held through tracking return must not relatch */
 held[0]=0;assert(!vr_vehicle_handles_update(1,&f));held[0]=1;hands(0);assert(vr_vehicle_handles_update(1,&f));
 input_valid=0;assert(!vr_vehicle_handles_update(1,&f));input_valid=1;assert(!vr_vehicle_handles_update(1,&f));
 held[0]=0;assert(!vr_vehicle_handles_update(1,&f));held[0]=1;assert(vr_vehicle_handles_update(1,&f));
 vr_wheel.grip[0].held=0;vr_wheel.down[0]=0;owner[0]=1;pressed[0]=1;assert(!vr_vehicle_handles_update(1,&f));owner[0]=0;
 hands(0);vr_wheel.down[0]=0;vr_wheel.angle=0;assert(vr_vehicle_handles_update(1,&f));pressed[0]=0;hands(2.0f);assert(vr_vehicle_handles_update(1,&f));assert(fabsf(vr_wheel.angle-1.04719755f)<1e-6);
 eligible=0;assert(!vr_vehicle_handles_update(1,&f));
 puts("PASS: real vehicle control: wheel wrap, finite/zero guards, exclusive claims, two hands/release, tracking/recenter reset, 60-degree clamp and eligibility fallback");}
'''
# Replay actual closed prism mesh; every perimeter edge must belong to two faces.
mesh=r'''
typedef struct {float alpha,red,green,blue;}real_argb_color;
static real_point3d faces_seen[6][4];static int faces_count;
static void cross_product3d(const real_vector3d*a,const real_vector3d*b,real_vector3d*c){*c=(real_vector3d){{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};}
static float normalize3d(real_vector3d*v){float n=magnitude3d(v);if(n>0)for(int i=0;i<3;i++)v->n[i]/=n;return n;}
static void render_debug_polygon(const real_point3d*p,int n,const real_argb_color*c){assert(n==4&&faces_count<6);memcpy(faces_seen[faces_count++],p,sizeof(real_point3d)*4);for(int i=0;i<4;i++)for(int a=0;a<3;a++)assert(isfinite(p[i].n[a]));}
'''+fn('vr_wheel_bar')
code=code.replace('int main(void){',mesh+'\nint main(void){')
code=code.replace(' eligible=0;',r'''
 vr_wheel_bar((real_point3d){{0,0,0}},(real_point3d){{0,1,0}},.02f,(real_argb_color){1,1,1,1});assert(faces_count==6);
 for(int face=0;face<6;face++)for(int edge=0;edge<4;edge++){
  real_point3d a=faces_seen[face][edge],b=faces_seen[face][(edge+1)%4];int found=0;
  for(int f2=0;f2<6;f2++)for(int e2=0;e2<4;e2++){
   real_point3d c=faces_seen[f2][e2],d=faces_seen[f2][(e2+1)%4];
   if((!memcmp(&a,&c,sizeof(a))&&!memcmp(&b,&d,sizeof(b)))||(!memcmp(&a,&d,sizeof(a))&&!memcmp(&b,&c,sizeof(b))))found++;
  } assert(found==2);
 }
 eligible=0;''')
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(code);subprocess.run(['clang','-std=gnu11','-fsanitize=address,undefined','-I',str(ROOT),str(p/'t.c'),'-lm','-o',str(p/'t')],check=True);subprocess.run([str(p/'t')],check=True)
assert 'VR_RENDER_EYE()' in fn('vr_render_vehicle_controls') and 'vr.vehicle_wheel_visible' in fn('vr_render_vehicle_controls')
assert 'saved_debug' in fn('vr_render_vehicle_controls') and 'rasterizer_debug_draw();' in fn('vr_render_vehicle_controls')
assert 'vr.vehicle_wheel_visible' not in fn('vr_vehicle_handles_update')
assert 'vr_first_person_vehicles()' in fn('vr_vehicle_handles_enabled') and 'vr_render.seat.driver' in fn('vr_vehicle_handles_enabled')
assert 'vr_interaction_release(h,VR_INTERACTION_VEHICLE)' in fn('vr_vehicle_handles_clear')
print('PASS: first-person-driver eligibility, independent hidden wheel/control option, eye-only native mesh and restored render flag')
