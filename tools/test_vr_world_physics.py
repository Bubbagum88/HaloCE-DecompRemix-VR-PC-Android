"""Exercise bounded item spring and articulated solver with real compiled code."""
from pathlib import Path
import subprocess
import re

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/world-physics-tests'
out.mkdir(parents=True,exist_ok=True)
source=r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "vr_world_math.h"
#include "vr_articulated.h"
static int sweeps;
static int floor_sweep(void *unused,float const old[3],float radius,float next[3]) {
 (void)unused;(void)old;++sweeps;if(next[2]<radius)next[2]=radius;return 1;
}
static int failed_sweep(void *unused,float const old[3],float radius,float next[3]) {
 (void)unused;(void)old;(void)radius;next[0]=NAN;return 1;
}
int main(void){
 for(int local=0;local<2;++local)for(int server=0;server<2;++server)for(int campaign=0;campaign<2;++campaign)
   assert(vr_world_authority(local,server,campaign)==(local||(server&&campaign)));
 float error[3]={1,0,0},current[3]={0,0,0},light[3],heavy[3],two[3];
 assert(vr_world_spring(error,current,2,1,1,0,light));
 assert(vr_world_spring(error,current,.25f,1,1,0,heavy));
 assert(vr_world_spring(error,current,.25f,2,1,0,two));
 assert(light[0]>heavy[0] && two[0]>heavy[0]);
 for(int i=0;i<300;++i){
   assert(vr_world_spring(error,current,1,1,1,.003f,current));
   assert(sqrtf(current[0]*current[0]+current[1]*current[1]+current[2]*current[2])<=.201f);
 }
 error[0]=NAN;assert(!vr_world_spring(error,current,1,1,1,0,light));error[0]=1;
 assert(!vr_world_spring(error,current,1,1,0,0,light));
 float throw_velocity[3]={20,-20,20};assert(vr_world_limit(throw_velocity,.24f));
 assert(throw_velocity[0]>0 && throw_velocity[1]<0 && throw_velocity[2]>0);
 assert(fabsf(sqrtf(throw_velocity[0]*throw_velocity[0]+throw_velocity[1]*throw_velocity[1]+throw_velocity[2]*throw_velocity[2])-.24f)<.0001f);

 struct vr_articulated_body b={0},before;
 b.count=3;
 for(int i=0;i<3;++i){b.nodes[i].parent=i-1;b.nodes[i].length=i?1:0;b.nodes[i].inverse_mass=1;b.nodes[i].radius=.05f;b.nodes[i].max_bend=3.141592f;b.nodes[i].position[2]=b.nodes[i].previous[2]=3-i;}
 struct vr_articulated_pin pin={0,{0,0,3}};
 for(int tick=0;tick<600;++tick){
   assert(vr_articulated_step(&b,1.0f/60,9.81f,&pin,1,floor_sweep,0));
   assert(b.nodes[0].position[2]==3);
   for(int i=1;i<3;++i){float d=0;for(int n=0;n<3;++n){float v=b.nodes[i].position[n]-b.nodes[i-1].position[n];d+=v*v;}assert(fabsf(sqrtf(d)-1)<.005f);}
 }
 before=b;pin.position[0]=10;
 assert(!vr_articulated_step(&b,1.0f/60,9.81f,&pin,1,floor_sweep,0));assert(!memcmp(&b,&before,sizeof b));
 pin.position[0]=0;
 assert(!vr_articulated_step(&b,1.0f/60,9.81f,&pin,1,failed_sweep,0));assert(!memcmp(&b,&before,sizeof b));
 assert(!vr_articulated_step(&b,1,9.81f,&pin,1,floor_sweep,0));
 for(int tick=0;tick<600;++tick){assert(vr_articulated_step(&b,1.0f/60,9.81f,0,0,floor_sweep,0));for(int i=0;i<3;++i)assert(b.nodes[i].position[2]>=.04999f);}
 float target[3][3]={{0,0,2.2f},{0,0,1.2f},{0,0,.2f}};
 for(int tick=0;tick<120;++tick)assert(vr_articulated_recovery(&b,target,.1f,floor_sweep,0));
 assert(fabsf(b.nodes[0].position[2]-2.2f)<.001f);
 before=b;target[1][0]=NAN;assert(!vr_articulated_recovery(&b,target,.1f,floor_sweep,0));assert(!memcmp(&b,&before,sizeof b));
 b.nodes[1].parent=2;assert(!vr_articulated_step(&b,1.0f/60,9.81f,0,0,floor_sweep,0));
 memset(&b,0,sizeof b);b.count=64;b.self_collision=1;
 for(int i=0;i<64;++i){b.nodes[i].parent=i-1;b.nodes[i].length=i?.02f:0;b.nodes[i].inverse_mass=1;b.nodes[i].radius=.004f;b.nodes[i].max_bend=3.141592f;b.nodes[i].position[2]=b.nodes[i].previous[2]=2-i*.02f;}
 for(int tick=0;tick<300;++tick){sweeps=0;assert(vr_articulated_step(&b,1.f/30,3.f,0,0,floor_sweep,0));assert(sweeps==64);}
 memset(&b,0,sizeof b);b.count=4;b.self_collision=1;
 for(int i=0;i<4;++i){b.nodes[i].parent=-1;b.nodes[i].inverse_mass=1;b.nodes[i].radius=.05f;b.nodes[i].max_bend=3.141592f;b.nodes[i].position[2]=b.nodes[i].previous[2]=1;}
 assert(vr_articulated_step(&b,1.f/30,0,0,0,floor_sweep,0));
 for(int i=0;i<4;++i)for(int j=i+1;j<4;++j){float d=0;for(int k=0;k<3;++k){float v=b.nodes[i].position[k]-b.nodes[j].position[k];d+=v*v;}assert(sqrtf(d)>.098f);}
 puts("PASS: item force/mobility/two-hand bounds, finite guards, throw clamp, articulated constraints/gravity/collision/recovery, invalid-state atomic rejection");
}
'''
c=out/'world.c';c.write_text(source)
binary=out/'world'
subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(ROOT/'port/linux/game'),str(c),str(ROOT/'port/linux/game/vr_articulated.c'),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)

# Exercise actual ownership release/reset code: tracking loss must not create
# a throw, nor may releasing one of two hands fling the shared item.
world=(ROOT/'port/linux/game/vr_world_interaction.c').read_text()
def function(name):
    m=re.search(r'^(?:static )?[\w *]+\b'+name+r'\s*\([^;{]*\)\s*\{',world,re.M)
    start=world.index('{',m.start());end=start+1;depth=1
    while depth:
        depth+=(world[end]=='{')-(world[end]=='}');end+=1
    return world[m.start():end]
state=re.search(r'static struct world_hand \{.*?\} hands\[2\];',world,re.S).group(0)
lifecycle=r'''
#include <assert.h>
#include <string.h>
#include <math.h>
#include "vr_world_math.h"
typedef int boolean;
typedef union {struct {float i,j,k;};float n[3];} real_vector3d;
typedef real_vector3d real_point3d;
typedef float real;
#define NONE (-1)
#define VR_INTERACTION_WORLD 3
enum {_object_type_none,_object_type_vehicle};
struct object_datum {struct {real_vector3d angular_velocity;int type;} object;};
static struct object_datum item;
static int probes,throws,releases;
static real_vector3d applied;
static struct object_datum *grabbable(long id){++probes;return id==42?&item:0;}
static void vr_world_object_velocity(long id,real_vector3d const *linear,real_vector3d const *angular){assert(id==42);(void)angular;++throws;applied=*linear;}
static void vr_interaction_release(int hand,int owner){assert(hand>=0&&hand<2&&owner==3);++releases;}
#define platform_log(...) ((void)0)
static long last_tick,last_unit;
static int previous_grip[2];
static unsigned long weight_haptic_at[2]={10,20};
''' + state + '\n' + function('release_hand') + '\n' + function('vr_world_interaction_reset') + r'''
int main(void){
 hands[0].active=1;hands[0].index=42;hands[0].velocity.i=100;
 release_hand(0,0,1);assert(throws==0&&!hands[0].active&&releases==1);
 hands[0].active=hands[1].active=1;hands[0].index=hands[1].index=42;
 release_hand(0,1,1);assert(throws==0&&hands[1].active);
 hands[1].velocity.i=100;release_hand(1,1,1);assert(throws==1&&fabsf(applied.i-.24f)<.00001f);
 hands[0].active=1;hands[0].index=42;hands[0].velocity.i=100;item.object.type=_object_type_vehicle;
 release_hand(0,1,1);assert(throws==1&&!hands[0].active);item.object.type=_object_type_none;
 hands[0].active=1;hands[0].index=42;hands[0].velocity.i=NAN;
 release_hand(0,1,1);assert(throws==1);
 hands[0].active=1;hands[0].index=999;int old=probes;
 vr_world_interaction_reset();assert(probes==old&&throws==1&&!hands[0].active&&last_tick==NONE&&last_unit==NONE);
 assert(weight_haptic_at[0]==0&&weight_haptic_at[1]==0);
 assert(previous_grip[0]&&previous_grip[1]);
}
'''
c=out/'lifecycle.c';c.write_text(lifecycle);binary=out/'lifecycle'
subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Wno-unused-function','-fsanitize=address,undefined','-I'+str(ROOT/'port/linux/game'),str(c),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
print('PASS: actual release/reset code: tracking loss, shared two-hand release, throw cap, NaN rejection, stale-ID-safe map reset')
