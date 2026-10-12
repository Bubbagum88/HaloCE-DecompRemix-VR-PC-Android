"""Test38/Test55 virtual cockpit control replay: real steering function and geometry.

Test55 (IMMERSIVE VEHICLES): a hand takes the Warthog's own wheel anywhere on
its rim, or a handle along its outer half, within the palm contact radius plus
4 cm (10 cm away still misses). While the controls are shown they own the
steering (controller aim no longer fights them) and self-centre when let go;
the Banshee yoke's push/pull sets the pitch.

Test56: turning the controls right steers right (Test55 had every control
inverted: the owner's Ghost turned the wrong way); the Ghost's handlebar also
twists and the Scorpion's sticks steer as a tank's; 1.5 degrees of dead zone;
self-centring by time; the Warthog's rim takes a hand 2 cm further (12 cm
misses); haptics as the controls turn, at full lock and on release.

Test57: each vehicle its own controls: the Warthog a drawn wheel in front of
its own, taken 4 cm further (14 cm misses); the Scorpion (and a Wraith) one
drive stick tilted the way to go; the Banshee's flight bar also slides across
to turn (12 cm is full lock); a soft tick crossing the centre (the Ghost's
too); the Ghost's handlebar reach and steering unchanged. CONTROL GLOW,
STEER HAPTICS and BANSH SLIDE turn the highlight, the steering haptics and
the Banshee's slide off.
"""
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
#define PIN(x,l,h) ((x)<(l)?(l):((x)>(h)?(h):(x)))
static struct {long unit;int kind,valid,log_pending,down[2],steering_logged;real_matrix4x3 root;real_point3d center,target[2];float radius,angle,pitch,grip_phase[2],push_start[2];struct vr_wheel_grip grip[2];
 float anchor[3],scale;double steered;int at_limit[2];float felt[2];real_vector3d normal,plane_left,plane_up,simulated_forward,steer;int steer_valid;
 float side_start[2];int near[2],side[2],wheel_front,glow,steer_haptics,slide,far,far_logged,drive;float throttle;}vr_wheel;
static double clock_now;static double vr_pose_time(void){return clock_now+=1.0/72.0;}
static void vr_wheel_drawn_refresh(void){}
static struct {real_point3d game_camera_position;}vr_render;
static const char *vr_wheel_keys[]={"warthog","ghost","scorpion","banshee"};
#define platform_log(...) ((void)0)
static int input_valid=1;
static float config_real(char const*k){assert(!strcmp(k,"vr.interaction_reach"));return .04f;}
static int eligible=1,held[2],pressed[2],released[2],tracked[2]={1,1},owner[2],buzz;static real_point3d pose[2];
static int vr_controller(unsigned int*b,float*t,float*s){(void)b;(void)t;(void)s;return input_valid;}
static void vr_vehicle_handles_clear(void){for(int h=0;h<2;h++){vr_wheel.down[h]=1;vr_wheel.grip[h].held=0;owner[h]=0;}}
static int vr_vehicle_handles_prepare(long u){(void)u;return eligible;}
static int vr_interaction_grip(int h,int*p,int*r){*p=pressed[h];*r=released[h];return held[h];}
static int vr_hand_world(int h,float*a,float*b,float*c,float*d){(void)a;(void)c;(void)d;memcpy(b,pose[h].n,12);return tracked[h];}
static int vr_interaction_owner(int h){return owner[h];}
static int vr_interaction_claim(int h,int o){if(owner[h]&&owner[h]!=o)return 0;owner[h]=o;return 1;}
static void vr_interaction_release(int h,int o){if(owner[h]==o)owner[h]=0;}
static float last_amplitude;static void vr_haptic(int h,float a,float b){(void)h;(void)b;last_amplitude=a;buzz++;}
static float vr_units_per_metre(void){return 1;}
static void vector_from_points3d(const real_point3d*a,const real_point3d*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static float dot_product3d(const real_vector3d*a,const real_vector3d*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(const real_vector3d*v){return sqrtf(dot_product3d(v,v));}
static float vr_yaw(const real_vector3d*v){return atan2f(v->j,v->i);}
static real_point3d vr_wheel_point(real x,real y,real z){real_point3d p=vr_wheel.center;for(int i=0;i<3;i++)p.n[i]+=vr_wheel.root.forward.n[i]*x+vr_wheel.plane_left.n[i]*y+vr_wheel.plane_up.n[i]*z;return p;}
/* the heading the controls give for a turn (+ right): the yaw falls, past the dead zone */
static float steered(float a){float m=fabsf(a)<=VR_WHEEL_DEAD_ZONE?0:(a-copysignf(VR_WHEEL_DEAD_ZONE,a))*VR_WHEEL_LOCK/(VR_WHEEL_LOCK-VR_WHEEL_DEAD_ZONE);return -m;}
'''+re.search(r'static struct \{char const \*control;.*?\};\n',s,re.S)[0]+re.search(r'#define VR_STICK_LENGTH.*\n#define VR_BAR_SLIDE.*\n',s)[0]+fn('vr_wheel_grip_distance')+fn('vr_vehicle_handles_update')+fn('vr_vehicle_handles_hand')+r'''
static void hands(float angle){for(int h=0;h<2;h++){float sign=h?-1:1;pose[h]=(real_point3d){{0,sign*.2f*cosf(angle),sign*.2f*sinf(angle)}};}}
int main(void){
 vr_wheel.steer_haptics=vr_wheel.slide=vr_wheel.glow=1;
 struct vr_wheel_grip g;float p[2]={-1,.001f},q[2]={-1,-.001f};vr_wheel_grip_start(&g,p,0);assert(fabsf(vr_wheel_grip_angle(&g,q))<.003f);
 q[0]=NAN;assert(vr_wheel_grip_angle(&g,q)==g.base);p[0]=p[1]=0;vr_wheel_grip_start(&g,p,0);assert(!g.held);
 vr_wheel.root.forward=(real_vector3d){{1,0,0}};vr_wheel.root.left=(real_vector3d){{0,1,0}};vr_wheel.root.up=(real_vector3d){{0,0,1}};
 vr_wheel.plane_left=vr_wheel.root.left;vr_wheel.plane_up=vr_wheel.root.up;vr_wheel.normal=(real_vector3d){{-1,0,0}};vr_wheel.simulated_forward=vr_wheel.root.forward;vr_wheel.scale=1;
 vr_wheel.target[0]=(real_point3d){{0,.2f,0}};vr_wheel.target[1]=(real_point3d){{0,-.2f,0}};vr_wheel.valid=1;
 /* prepared controls own the steering even untouched (no controller steering) */
 real_vector3d f={{0,1,0}};hands(0);assert(vr_vehicle_handles_update(1,&f));assert(fabsf(f.j)<1e-6&&f.i>.99f);
 /* A Grip press 14 cm off the rim is not contact. Release, move onto the rim,
  * and squeeze again before the wheel can be acquired. */
 pose[0].x=.14f;held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(!owner[0]&&!vr_wheel.grip[0].held);
 held[0]=pressed[0]=0;vr_vehicle_handles_update(1,&f);pose[0].x=.11f; /* 11 cm off the rim: within 4+4+4 cm */
 held[0]=held[1]=pressed[0]=pressed[1]=1;assert(vr_vehicle_handles_update(1,&f));assert(buzz==2&&vr_wheel.grip[0].held&&vr_wheel.grip[1].held&&fabsf(f.j)<1e-6);
 pose[0].x=0;
 /* the Warthog rim is grabbed anywhere, not only at the authored targets */
 { float point[3];assert(vr_vehicle_handles_hand(0,point)&&fabsf(point[1]-.2f)<1e-5); }
 /* the wheel turned right (the left hand rising) steers right */
 pressed[0]=pressed[1]=0;hands(.4f);assert(vr_vehicle_handles_update(1,&f));assert(fabsf(atan2f(f.j,f.i)-steered(.4f))<1e-5&&atan2f(f.j,f.i)<-.35f);
 assert(vr_wheel.steer_valid&&fabsf(vr_wheel.steer.j-f.j)<1e-6);
 { float point[3];assert(vr_vehicle_handles_hand(0,point)&&fabsf(atan2f(point[2],point[1])-.4f)<1e-4); }
 held[1]=0;released[1]=1;hands(.6f);assert(vr_vehicle_handles_update(1,&f));assert(!owner[1]&&owner[0]==2);assert(fabsf(atan2f(f.j,f.i)-steered(.6f))<1e-5);
 /* ownership lost: the grip ends and the controls come back toward centre */
 owner[0]=0;assert(vr_vehicle_handles_update(1,&f));assert(!vr_wheel.grip[0].held);assert(fabsf(vr_wheel.angle-.6f*expf(-(1.0f/72.0f)/0.17f))<1e-4);
 for(int i=0;i<200;i++)vr_vehicle_handles_update(1,&f);assert(fabsf(vr_wheel.angle)<1e-3&&fabsf(atan2f(f.j,f.i))<1e-3);
 hands(0);vr_wheel.down[0]=0;pressed[0]=1;held[0]=1;vr_wheel.angle=0;vr_vehicle_handles_update(1,&f);assert(owner[0]==2);
 pressed[0]=0;tracked[0]=0;vr_vehicle_handles_update(1,&f);assert(!owner[0]);
 tracked[0]=1;vr_vehicle_handles_update(1,&f);assert(!owner[0]); /* held through tracking return must not relatch */
 held[0]=0;vr_vehicle_handles_update(1,&f);held[0]=1;hands(0);vr_vehicle_handles_update(1,&f);assert(owner[0]==2);
 input_valid=0;assert(!vr_vehicle_handles_update(1,&f));input_valid=1;vr_vehicle_handles_update(1,&f);assert(!owner[0]);
 held[0]=0;vr_vehicle_handles_update(1,&f);held[0]=1;vr_vehicle_handles_update(1,&f);assert(owner[0]==2);
 vr_wheel.grip[0].held=0;vr_wheel.down[0]=0;owner[0]=1;pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(owner[0]==1&&!vr_wheel.grip[0].held);owner[0]=0;
 hands(0);vr_wheel.down[0]=0;vr_wheel.angle=0;vr_vehicle_handles_update(1,&f);pressed[0]=0;hands(2.0f);vr_vehicle_handles_update(1,&f);assert(fabsf(vr_wheel.angle-1.04719755f)<1e-6);
 /* handles (Ghost/Scorpion/Banshee): along the outer half of each handle */
 held[0]=held[1]=0;vr_vehicle_handles_update(1,&f);vr_wheel.kind=3;vr_wheel.angle=0;hands(0);
 pose[0].y=.12f;held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(owner[0]==2); /* on the horn's outer half */
 held[0]=pressed[0]=0;vr_vehicle_handles_update(1,&f);
 pose[0].y=0;pose[0].z=.10f;held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(!owner[0]); /* 10 cm above the centre */
 held[0]=pressed[0]=0;vr_vehicle_handles_update(1,&f);hands(0);
 /* Banshee yoke: pushed 12 cm forward dives, pulled back climbs, let go levels */
 held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);pressed[0]=0;assert(owner[0]==2);
 pose[0].x=.12f;vr_vehicle_handles_update(1,&f);assert(f.k<-.6f);
 pose[0].x=-.12f;vr_vehicle_handles_update(1,&f);assert(f.k>.6f);
 held[0]=0;for(int i=0;i<200;i++)vr_vehicle_handles_update(1,&f);assert(fabsf(f.k)<1e-3);
 /* Ghost: the handlebar twisted (left hand forward, right back) turns right */
 vr_wheel.kind=1;vr_wheel.angle=0;vr_wheel.radius=.2f;hands(0);held[0]=pressed[0]=held[1]=pressed[1]=1;
 vr_vehicle_handles_update(1,&f);assert(owner[0]==2&&owner[1]==2);pressed[0]=pressed[1]=0;
 pose[0].x=.05f;pose[1].x=-.05f;vr_vehicle_handles_update(1,&f);assert(atan2f(f.j,f.i)<-.2f);
 pose[0].x=-.05f;pose[1].x=.05f;vr_vehicle_handles_update(1,&f);assert(atan2f(f.j,f.i)>.2f);
 held[0]=held[1]=0;for(int i=0;i<200;i++)vr_vehicle_handles_update(1,&f);
 /* Banshee flight bar: slid 6 cm to the right (both hands) turns right, as
  * far left turns left; a push alone does not turn */
 vr_wheel.kind=3;vr_wheel.angle=0;hands(0);held[0]=pressed[0]=held[1]=pressed[1]=1;
 vr_vehicle_handles_update(1,&f);pressed[0]=pressed[1]=0;assert(owner[0]==2&&owner[1]==2);
 pose[0].y-=.06f;pose[1].y-=.06f;vr_vehicle_handles_update(1,&f);assert(atan2f(f.j,f.i)<-.3f);
 pose[0].y+=.12f;pose[1].y+=.12f;vr_vehicle_handles_update(1,&f);assert(atan2f(f.j,f.i)>.3f);
 pose[0].y-=.06f;pose[1].y-=.06f;pose[0].x=pose[1].x=.05f;vr_vehicle_handles_update(1,&f);assert(fabsf(vr_wheel.angle)<1e-5);
 /* BANSH SLIDE off: sliding the bar does not turn (rolling still does) */
 vr_wheel.slide=0;pose[0].x=pose[1].x=0;pose[0].y-=.06f;pose[1].y-=.06f;vr_vehicle_handles_update(1,&f);assert(fabsf(vr_wheel.angle)<1e-5);
 pose[0].y+=.06f;pose[1].y+=.06f;vr_wheel.slide=1;
 held[0]=held[1]=0;for(int i=0;i<200;i++)vr_vehicle_handles_update(1,&f);
 /* Scorpion (and Wraith): one drive stick, its knob at the controls' centre;
  * a hand 5 cm to the right tilts it right and turns right, to the left
  * turns left; a hand 12 cm off the knob does not take it */
 vr_wheel.kind=2;vr_wheel.angle=0;vr_wheel.target[0]=vr_wheel.target[1]=vr_wheel.center;
 pose[0]=pose[1]=(real_point3d){{0,0,.12f}};held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(!owner[0]);
 held[0]=pressed[0]=0;vr_vehicle_handles_update(1,&f);
 pose[0]=(real_point3d){{0,0,.02f}};held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);pressed[0]=0;assert(owner[0]==2&&vr_wheel.grip[0].held);
 pose[0].y=-.05f;vr_vehicle_handles_update(1,&f);assert(atan2f(f.j,f.i)<-.2f&&fabsf(vr_wheel.angle-atan2f(.05f,.16f))<1e-4);
 pose[0].y=.05f;vr_vehicle_handles_update(1,&f);assert(atan2f(f.j,f.i)>.2f);
 /* Test59: TANK DRIVE: pushed 10 cm drives on full, pulled 6 cm reverses,
  * 1 cm is nothing; off, the stick only steers */
 vr_wheel.drive=1;pose[0].y=0;
 pose[0].x=.10f;vr_vehicle_handles_update(1,&f);assert(fabsf(vr_wheel.throttle-1.0f)<1e-4f);
 pose[0].x=-.06f;vr_vehicle_handles_update(1,&f);assert(vr_wheel.throttle<-.4f&&vr_wheel.throttle>-.6f);
 pose[0].x=.01f;vr_vehicle_handles_update(1,&f);assert(vr_wheel.throttle==0.0f);
 vr_wheel.drive=0;pose[0].x=.10f;vr_vehicle_handles_update(1,&f);assert(vr_wheel.throttle==0.0f);
 pose[0].x=0;
 /* haptics: a firm buzz at full lock, a light one on release */
 /* STEER HAPTICS off: no turning ticks or full-lock buzz */
 {int before=buzz;vr_wheel.steer_haptics=0;pose[0].y=-.4f;vr_vehicle_handles_update(1,&f);assert(buzz==before);pose[0].y=.05f;vr_vehicle_handles_update(1,&f);vr_wheel.steer_haptics=1;}
 {int before=buzz;pose[0].y=-.4f;vr_vehicle_handles_update(1,&f);assert(buzz>before&&fabsf(vr_wheel.angle-VR_WHEEL_LOCK)<1e-5);
  before=buzz;held[0]=0;vr_vehicle_handles_update(1,&f);assert(buzz>before&&!owner[0]);}
 for(int i=0;i<200;i++)vr_vehicle_handles_update(1,&f);
 /* a soft tick crossing the centre (the wheel and the Ghost's handlebar) */
 vr_wheel.kind=0;vr_wheel.angle=0;vr_wheel.target[0]=(real_point3d){{0,.2f,0}};vr_wheel.target[1]=(real_point3d){{0,-.2f,0}};
 /* Test57: the wheel's face takes a hand (a spoke, 10 cm out and 5 cm in
  * front); its hub's middle does not */
 pose[0]=(real_point3d){{.05f,.10f,0}};held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(owner[0]==2);
 held[0]=pressed[0]=0;vr_vehicle_handles_update(1,&f);assert(!owner[0]);
 pose[0]=(real_point3d){{0,.02f,0}};held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);assert(!owner[0]);
 held[0]=pressed[0]=0;vr_vehicle_handles_update(1,&f);
 hands(0);held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);pressed[0]=0;assert(owner[0]==2);
 hands(.3f);vr_vehicle_handles_update(1,&f);
 {int before=buzz;hands(-.3f);vr_vehicle_handles_update(1,&f);assert(buzz>before);}
 held[0]=0;vr_vehicle_handles_update(1,&f);for(int i=0;i<200;i++)vr_vehicle_handles_update(1,&f);
 vr_wheel.kind=1;hands(0);held[0]=pressed[0]=1;vr_vehicle_handles_update(1,&f);pressed[0]=0;assert(owner[0]==2);
 hands(.3f);vr_vehicle_handles_update(1,&f);
 {int before=buzz;hands(-.3f);vr_vehicle_handles_update(1,&f);
  assert(buzz>before);}
 held[0]=0;vr_vehicle_handles_update(1,&f);
 vr_wheel.kind=0;
 eligible=0;assert(!vr_vehicle_handles_update(1,&f));
 puts("PASS: immersive vehicle controls: rim/handle contact (8 cm, 10 cm misses), controls own steering and self-centre, Banshee yoke pitch, exclusive claims, two hands/release, tracking/recenter reset, 60-degree clamp and eligibility fallback; Test56: right is right, Ghost twist, dead zone, timed self-centring, steering haptics; Test57: Warthog wheel reach 12 cm, drive stick, flight bar slide, centre tick, STEER HAPTICS and BANSH SLIDE off");}
'''
# Replay actual closed prism mesh; every perimeter edge must belong to two faces.
mesh=r'''
typedef struct {float alpha,red,green,blue;}real_argb_color;
static real_point3d faces_seen[6][4];static int faces_count;
static void cross_product3d(const real_vector3d*a,const real_vector3d*b,real_vector3d*c){*c=(real_vector3d){{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};}
static float normalize3d(real_vector3d*v){float n=magnitude3d(v);if(n>0)for(int i=0;i<3;i++)v->n[i]/=n;return n;}
static void render_debug_polygon(const real_point3d*p,int n,const real_argb_color*c){(void)c;assert(n==4&&faces_count<6);memcpy(faces_seen[faces_count++],p,sizeof(real_point3d)*4);for(int i=0;i<4;i++)for(int a=0;a<3;a++)assert(isfinite(p[i].n[a]));}
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
 /* a column along the vehicle's forward axis is still a closed box */
 faces_count=0;vr_wheel_bar((real_point3d){{0,0,0}},(real_point3d){{1,0,0}},.02f,(real_argb_color){1,1,1,1});assert(faces_count==6);
 eligible=0;''')
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(code);subprocess.run(['clang','-std=gnu11','-fsanitize=address,undefined','-I',str(ROOT),str(p/'t.c'),'-lm','-o',str(p/'t')],check=True);subprocess.run([str(p/'t')],check=True)
controls=fn('vr_render_vehicle_controls')
assert 'VR_RENDER_EYE()' in controls and 'vr.vehicle_wheel_visible' in controls
assert 'saved_debug' in controls and 'rasterizer_debug_draw();' in controls
assert 'config_boolean("vr.vehicle_wheel_visible");' in controls and 'vr_wheel.kind!=0;' not in controls, 'Test57: the Warthog draws its wheel'
assert 'Warthog: a rubber rim, three metal spokes' in controls and 'one drive stick on a base plate' in controls
assert 'Scorpion: two control sticks' not in controls
assert '&& vr_wheel.glow' in controls
assert '{"wraith",2}' in s and '{"steering wheel",0.08f},{"handlebar",0.06f}' in s
assert 'accent' not in controls, 'no cyan accent block'
assert 'vr.vehicle_wheel_visible' not in fn('vr_vehicle_handles_update')
assert 'vr_first_person_vehicles()' in fn('vr_vehicle_handles_enabled') and 'vr_render.seat.driver' in fn('vr_vehicle_handles_enabled')
assert 'vr_interaction_release(h,VR_INTERACTION_VEHICLE)' in fn('vr_vehicle_handles_clear')
assert 'config_real("vr.interaction_reach")' in fn('vr_vehicle_handles_update')
assert 'distance<=contact_radius' in fn('vr_vehicle_handles_update')
render=(ROOT/'port/linux/game/vr_render.c').read_text()
assert 'if (vr_render_vehicle_first_person_hands())\n\t\treturn FALSE;' in render
assert 'vr_vehicle_handles_hand(controller, hand.n);' in render
assert 'owner == VR_INTERACTION_RELOAD || owner == VR_INTERACTION_VEHICLE' in render
assert '"IMMERSIVE VEHICLE", "vr.vehicle_handles"' in (ROOT/'port/linux/game/vr_menu.c').read_text()
print('PASS: first-person-driver eligibility, Warthog draws its wheel (Test57), drive stick, Ghost/Scorpion/Banshee meshes, first-person hands on the controls, IMMERSIVE VEHICLES row')
