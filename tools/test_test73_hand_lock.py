"""Test73, item 10 (a tester's request relayed by the owner: "Any chance we could get the hands locked onto the
steering wheels? When holding grip"): HAND LOCK (vr.vehicle_hand_lock, VEHICLES and IMMERSION > VEHICLE OPTIONS, on
by default, turned on with IMMERSIVE VEHICLE). While a hand holds grip on an immersive control, it is drawn where it
took hold (vr_vehicle_handles_hand: on the Warthog's rim at its phase, turning with the wheel; on the handlebar's,
bar's or stick's grip) with no pull back toward the controller (before: at most 10 cm from it), and turned as it was
when it took hold, in the control's own axes (vr_vehicle_handles_hand_turn): it turns with the wheel, rolls with the
handlebar and the flight bar, leans with the stick. Off: as before. The local player's hands only (no protocol).

Compiled and run (clang, AddressSanitizer) on the header's own functions (vr_wheel_place, vr_vehicle_handles_hand,
vr_wheel_control_axes, vr_vehicle_handles_hand_turn), every control kind, checked against the geometry the controls
are drawn with, not against the lock's own formula: on the wheel, the hand keeps its angles to the rim at its grip
point (radial, tangent, axis) as the wheel turns; on the stick, its angles to the stick's own axis and across; on the
handlebar and the bar, to the bar between its ends; back at the start the hand is exactly as it took hold; unit and
at right angles through 20,000 random turns; a new grip measured anew; off or not held, the controller's.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_hand_lock'
s = (ROOT / 'port/linux/game/vr_vehicle_handles.h').read_text(encoding='utf-8')
render = (ROOT / 'port/linux/game/vr_render.c').read_text(encoding='utf-8')
menu = (ROOT / 'port/linux/game/vr_menu.c').read_text(encoding='utf-8')
config = (ROOT / 'port/linux/src/port_config.c').read_text(encoding='utf-8')


def fn(name):
    m = re.search(r'^(?:static )?[\w *]+\b' + name + r'\s*\([^;{}]*\)\s*\{', s, re.M)
    assert m, name
    e = m.end()
    d = 1
    while d:
        d += (s[e] == '{') - (s[e] == '}')
        e += 1
    return s[m.start():e] + '\n'


# ---------- wiring
assert '{ "vr.vehicle_hand_lock", _config_boolean, "true", "HALO_VR_VEHICLE_HAND_LOCK"' in config
assert ('#define VR_IMMERSION_HAND_LOCK { "HAND LOCK", "vr.vehicle_hand_lock", _vr_setting_boolean, 2, '
        '{ { "OFF", "false" }, { "ON", "true" } } }') in menu
assert menu.count('VR_IMMERSION_HAND_LOCK,') == 2  # (VEHICLES' DRIVING and IMMERSION's VEHICLE OPTIONS)
assert '{ "vr.vehicle_hand_lock", "vr.vehicle_handles", TRUE },' in menu
assert 'vr_wheel.hand_lock=config_boolean("vr.vehicle_hand_lock");' in fn('vr_wheel_read_user')
assert 'vr_wheel.grips[h]++; /* Test73: HAND LOCK measures this grip anew */' in fn('vr_vehicle_handles_update')
assert 'boolean vehicle_locked = vehicle_grip && vr_vehicle_handles_hand_turn(controller, &f, &u);' in render
assert 'if (world_grip || climbing_grip || npc_grip || reload_grip || (vehicle_grip && !vehicle_locked))' in render
# (the locked f goes on to the wrist and the hand's turn: target from f, then vr_orient_hand with f and u)
locked_at = render.index('boolean vehicle_locked = ')
assert render.index('target.x = hand.x - f.i * 0.075f * units;', locked_at) < render.index(
    'vr_orient_hand(graph, matrices, chain[_vr_arm_hand], joints, &f, &u);', locked_at)

state = s[s.index('static struct {\n    long unit, vehicle;'):s.index('} vr_wheel;') + len('} vr_wheel;')] + '\n'
tables = s[s.index('static char const *const vr_wheel_keys'):s.index('#define VR_BAR_SLIDE 0.12f') + len('#define VR_BAR_SLIDE 0.12f')] + '\n'
tables += s[s.index('#define VR_CHEST_AHEAD'):s.index('#define VR_COMFORT_REACH 0.55f') + len('#define VR_COMFORT_REACH 0.55f')] + '\n'
tables += s[s.index('#define VR_FAR_REACH'):s.index('#define VR_FAR_REACH 1.5f') + len('#define VR_FAR_REACH 1.5f')] + '\n'

CODE = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "port/linux/game/vr_vehicle_controls_math.h"
typedef float real;
typedef union {struct {float x,y,z;};float n[3];} real_point3d;
typedef union {struct {float i,j,k;};float n[3];} real_vector3d;
typedef struct {real_vector3d forward,left,up;real_point3d position;} real_matrix4x3;
#define NONE (-1)
#define PIN(x,l,h) ((x)<(l)?(l):((x)>(h)?(h):(x)))
static const float UNITS=0.32808399f;
static float vr_units_per_metre(void){return UNITS;}
static float dot_product3d(const real_vector3d*a,const real_vector3d*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(const real_vector3d*v){return sqrtf(dot_product3d(v,v));}
static void vector_from_points3d(const real_point3d*a,const real_point3d*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static void cross_product3d(const real_vector3d*a,const real_vector3d*b,real_vector3d*c){real_vector3d r={{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};*c=r;}
static float normalize3d(real_vector3d*v){float m=magnitude3d(v);if(m>0)for(int i=0;i<3;i++)v->n[i]/=m;return m;}
static int valid_real_point3d(const real_point3d*p){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
static struct {struct {long vehicle_index;short seat_index;int driver;float offset;} seat;real_point3d game_camera_position;} vr_render;
static int vr_cockpit_frame(float f[3],float l[3],float u[3]){(void)f;(void)l;(void)u;return 0;}
static int config_boolean(char const*k){(void)k;return 0;}
static const real_matrix4x3 *heading_source;
static int vr_heading_forward(float f[3]){float h=atan2f(heading_source->forward.j,heading_source->forward.i);f[0]=cosf(h);f[1]=sinf(h);f[2]=0;return 1;}
static int refreshed;
'''

HARNESS = CODE + state + tables + fn('vr_wheel_point') + fn('vr_wheel_hand_frame') + fn('vr_wheel_place') + r'''
/* (the controls stay where vr_wheel_place put them: the drawn vehicle is the harness's) */
static void vr_wheel_drawn_refresh(void){refreshed++;}
''' + fn('vr_vehicle_handles_hand') + fn('vr_wheel_control_axes') + fn('vr_vehicle_handles_hand_turn') + r'''
static real_matrix4x3 root;
static unsigned int seed=73;
static float random_unit(void){seed=seed*1103515245u+12345u;return (float)((seed>>8)&0xFFFF)/65535.0f*2.0f-1.0f;}
static void random_hand(real_vector3d*f,real_vector3d*u){
 do{for(int i=0;i<3;i++)f->n[i]=random_unit();}while(normalize3d(f)<0.2f);
 do{for(int i=0;i<3;i++)u->n[i]=random_unit();float d=dot_product3d(f,u);for(int i=0;i<3;i++)u->n[i]-=f->n[i]*d;}while(normalize3d(u)<0.2f);}
static void place(int kind,float angle,float throttle){
 vr_wheel.kind=kind;vr_wheel.angle=angle;vr_wheel.throttle=throttle;vr_wheel_place(&root);}
static void setup(int kind){
 memset(&vr_wheel,0,sizeof vr_wheel);
 vr_wheel.valid=1;vr_wheel.hand_lock=1;vr_wheel.kind=kind;vr_wheel.scale=1;vr_wheel.radius=0.18f*UNITS;
 /* the controls 40 cm ahead of and 30 cm below the eyes, their axis toward the driver, leaning back */
 vr_wheel.local[0]=0.40f*UNITS;vr_wheel.local[1]=0;vr_wheel.local[2]=-0.30f*UNITS;
 vr_wheel.axis[0]=-0.98f;vr_wheel.axis[1]=0;vr_wheel.axis[2]=0.17f;
 root.forward=(real_vector3d){{cosf(.6f),sinf(.6f),0}};root.left=(real_vector3d){{-sinf(.6f),cosf(.6f),0}};root.up=(real_vector3d){{0,0,1}};
 root.position=(real_point3d){{3,-2,1}};heading_source=&root;
 vr_render.game_camera_position=(real_point3d){{3.1f,-2.2f,1.5f}};
 place(kind,0,0);}
/* the frame the control is drawn with, from its geometry: the wheel's at the grip point (radial out, along the rim,
 * the axis); the stick's (along it from the pivot, across, the third); a bar's (between its ends, up, the axis) */
static int drawn_frame(int kind,int hand,real_vector3d e[3]){
 if(kind==0){real_point3d at;real_vector3d r;if(!vr_vehicle_handles_hand(hand,at.n))return 0;vector_from_points3d(&vr_wheel.center,&at,&r);
  normalize3d(&r);e[0]=r;e[2]=vr_wheel.normal;cross_product3d(&e[2],&e[0],&e[1]);return 1;}
 if(kind==2){float length=VR_STICK_LENGTH*UNITS;real_point3d pivot=vr_wheel_point(0,0,-length);real_vector3d s;
  vector_from_points3d(&pivot,&vr_wheel.target[0],&s);normalize3d(&s);e[0]=s;
  float a=dot_product3d(&vr_wheel.plane_left,&s);for(int i=0;i<3;i++)e[1].n[i]=vr_wheel.plane_left.n[i]-s.n[i]*a;normalize3d(&e[1]);
  cross_product3d(&e[0],&e[1],&e[2]);return 1;}
 {real_vector3d bar;vector_from_points3d(&vr_wheel.target[1],&vr_wheel.target[0],&bar);normalize3d(&bar);e[0]=bar;e[2]=vr_wheel.normal;
  cross_product3d(&e[2],&e[0],&e[1]);return 1;}}
static float worst;
static void same_in(const real_vector3d e[3],const real_vector3d*a,const real_vector3d*b){
 for(int k=0;k<3;k++){float d=fabsf(dot_product3d(a,&e[k])-dot_product3d(b,&e[k]));if(d>worst)worst=d;assert(d<5e-4f);}}
int main(void){
 for(int kind=0;kind<4;kind++){
  for(int trial=0;trial<200;trial++){
   real_vector3d f0,u0,f,u,e0[3],e[3];
   setup(kind);
   int hand=trial&1;
   vr_wheel.grip[hand].held=1;vr_wheel.grips[hand]=1;vr_wheel.grip_phase[hand]=random_unit()*3.1f;
   random_hand(&f0,&u0);f=f0;u=u0;
   /* the grip's first frame: as the controller is */
   assert(vr_vehicle_handles_hand_turn(hand,&f,&u));
   for(int i=0;i<3;i++){assert(fabsf(f.n[i]-f0.n[i])<1e-5f);assert(fabsf(u.n[i]-u0.n[i])<1e-5f);}
   assert(drawn_frame(kind,hand,e0));
   real_vector3d fl[1],ul[1];
   for(int step=0;step<100;step++){
    float angle=random_unit()*1.6f,throttle=kind==2?random_unit():0;
    place(kind,angle,throttle);
    random_hand(&f,&u); /* the controller anywhere: ignored */
    assert(vr_vehicle_handles_hand_turn(hand,&f,&u));
    assert(fabsf(magnitude3d(&f)-1)<1e-4f&&fabsf(magnitude3d(&u)-1)<1e-4f&&fabsf(dot_product3d(&f,&u))<1e-4f);
    assert(drawn_frame(kind,hand,e));
    /* the hand's angles to the control as drawn: as when it took hold */
    {real_vector3d a,b;for(int k=0;k<3;k++){a.n[k]=dot_product3d(&f0,&e0[k]);b.n[k]=dot_product3d(&u0,&e0[k]);}
     real_vector3d expect_f={{0}},expect_u={{0}};
     for(int k=0;k<3;k++)for(int i=0;i<3;i++){expect_f.n[i]+=e[k].n[i]*a.n[k];expect_u.n[i]+=e[k].n[i]*b.n[k];}
     same_in(e,&f,&expect_f);same_in(e,&u,&expect_u);}
    fl[0]=f;ul[0]=u;
   }
   /* back at the start: exactly as it took hold */
   place(kind,0,0);random_hand(&f,&u);
   assert(vr_vehicle_handles_hand_turn(hand,&f,&u));
   for(int i=0;i<3;i++){assert(fabsf(f.n[i]-f0.n[i])<2e-4f);assert(fabsf(u.n[i]-u0.n[i])<2e-4f);}
   /* a new grip: measured anew, the controller's again */
   vr_wheel.grips[hand]++;random_hand(&f0,&u0);f=f0;u=u0;place(kind,0.7f,0);
   assert(vr_vehicle_handles_hand_turn(hand,&f,&u));
   for(int i=0;i<3;i++)assert(fabsf(f.n[i]-f0.n[i])<1e-5f);
   /* off, or let go, or the other hand (not holding): the controller's, untouched */
   vr_wheel.hand_lock=0;f=f0;assert(!vr_vehicle_handles_hand_turn(hand,&f,&u));assert(!memcmp(&f,&f0,sizeof f));
   vr_wheel.hand_lock=1;vr_wheel.grip[hand].held=0;assert(!vr_vehicle_handles_hand_turn(hand,&f,&u));
   assert(!vr_vehicle_handles_hand_turn(!hand,&f,&u));
   vr_wheel.valid=0;vr_wheel.grip[hand].held=1;assert(!vr_vehicle_handles_hand_turn(hand,&f,&u));
   (void)fl;(void)ul;
  }
  printf("kind %d: the locked hand keeps its angles to the control as drawn (worst %.1e)\n",kind,(double)worst);
 }
 /* the wheel's rim point turns with the wheel by its angle (the place the lock keeps) */
 {setup(0);vr_wheel.grip[0].held=1;vr_wheel.grip_phase[0]=0.3f;real_point3d a,b;
  assert(vr_vehicle_handles_hand(0,a.n));place(0,0.5f,0);assert(vr_vehicle_handles_hand(0,b.n));
  real_vector3d ra,rb;vector_from_points3d(&vr_wheel.center,&a,&ra);vector_from_points3d(&vr_wheel.center,&b,&rb);
  float ca=dot_product3d(&ra,&rb)/(magnitude3d(&ra)*magnitude3d(&rb));assert(fabsf(acosf(fminf(1,ca))-0.5f)<1e-3f);}
 printf("hand lock: %d draws refreshed the controls\n",refreshed);
 return 0;}
'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'hand_lock.c').write_text(HARNESS, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-function', '-Wno-unused-variable',
                '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-I' + str(ROOT), str(OUT / 'hand_lock.c'),
                '-lm', '-o', str(OUT / 'hand_lock')], check=True)
result = subprocess.run([str(OUT / 'hand_lock')], check=True, capture_output=True, text=True)
print(result.stdout.strip())
print('PASS: Test73 HAND LOCK: a hand holding the wheel, handlebar, stick or flight bar is drawn where it took hold, '
      'turned with the control; off, as before; menu rows, default and dependency in place')
