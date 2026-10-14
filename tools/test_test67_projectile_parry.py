"""Compile the complete production parry module, its real authority gate and
native pre-collision movement splice against deterministic engine fixtures.
No copied parry algorithm. ASan/UBSan cover malformed and lifecycle inputs.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def function(source, name):
    match = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) +
                      r'\s*\([^;{]*\)\s*\{', source, re.M)
    assert match, name
    start = match.start()
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


fixture = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;
typedef int boolean;
typedef union {real n[3];struct {real x,y,z;};struct {real i,j,k;};} real_point3d,real_vector3d;
#define NONE (-1)
#define TRUE 1
#define FALSE 0
#define HALO_VR 1
#define TICKS_PER_SECOND 30
#define MAXIMUM_OBJECTS_PER_MAP 16
#define MAXIMUM_WEAPONS_PER_UNIT 4
#define FLAG(b) (1u<<(b))
#define TEST_FLAG(v,b) (((v)&FLAG(b))!=0)
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define PIN(a,l,h) MIN(MAX(a,l),h)
enum {_object_type_projectile=5,_object_type_weapon=6,_object_at_rest_bit=0,_object_dead_bit=1,
      _biped_no_collision_bit=2,_unit_suspended_bit=3};
enum {_game_connection_local=0,_game_connection_network_server=1,_game_connection_network_client=2};
enum {VR_INTERACTION_NONE,VR_INTERACTION_RELOAD,VR_INTERACTION_VEHICLE,VR_INTERACTION_WORLD,
      VR_INTERACTION_PARKOUR,VR_INTERACTION_NPC,VR_INTERACTION_GRENADE,VR_INTERACTION_COUNT};
struct object_fields {int type;unsigned flags,damage_flags;long parent_object_index;
    long owner_object_index,owner_player_index;short owner_team_index;
    real_point3d position;real_vector3d translational_velocity,forward,up;};
struct object_datum {long definition_index;struct object_fields object;};
struct unit_fields {long player_index;unsigned flags;short current_weapon_index;long weapons[4];};
struct unit_datum {long definition_index;struct object_fields object;struct unit_fields unit;};
struct biped_datum {long definition_index;struct object_fields object;struct unit_fields unit;struct {unsigned flags;}biped;};
struct projectile_datum {long definition_index;struct object_fields object;
 struct {unsigned flags;short action;long ignore_object_index,target_object_index;
 real detonation_timer,detonation_timer_delta,arming_time,arming_time_delta,odometer;
 real deceleration_timer,deceleration_timer_delta,maximum_damage_distance;}projectile;};
struct projectile_definition {struct {real collision_radius;}projectile;};
static struct projectile_datum shot;
static struct projectile_definition definition;
static struct biped_datum body;
static struct object_datum guns[2];
static struct {long unit_index;}player_data;
static long live_index,tick;
static double pose_time;
static int enabled,connection,coop,host_permission,peers,active,paused,inhibited,controller,cinematic;
static int tracking[2],grip[2],trigger[2],busy[2],weapon_hand,empty,two_handed,palm_valid;
static int feedback,feedback_hand,object_deleted,target_updates;
static real speed[2],units,palm_radius;
static real_point3d palms[2],camera,feedback_point;
static real_vector3d up={.n={0,0,1}};
static int config_boolean(char const *key){
 if(!strcmp(key,"vr.projectile_parry"))return enabled;
 if(!strcmp(key,"net.host_vr_actions"))return host_permission;
 return 0;
}
static double config_real(char const *key){assert(!strcmp(key,"vr.interaction_reach"));return palm_radius;}
static short local_player_get_next(short previous){(void)previous;return 0;}
static long local_player_get_player_index(short local){(void)local;return 3;}
#define player_get(index) ((void)(index),&player_data)
static struct biped_datum *biped_try_and_get(long index){return index==0?&body:NULL;}
static struct unit_datum *unit_try_and_get(long index){return (struct unit_datum *)biped_try_and_get(index);}
static struct object_datum *object_try_and_get(long index){
 if(index==4||index==5)return &guns[index-4];
 return !object_deleted&&index==live_index?(struct object_datum *)&shot:NULL;
}
static long unit_inventory_get_weapon(long unit,short index){assert(unit==0&&index>=0&&index<4);return body.unit.weapons[index];}
static struct projectile_definition *projectile_definition_get(long index){(void)index;return &definition;}
static int vr_active(void){return active;}
static int game_connection(void){return connection;}
static int network_coop_active(void){return coop;}
static int network_interaction_host_ready(void){return peers;}
static int cinematic_in_progress(void){return cinematic;}
static int game_time_get_paused(void){return paused;}
static int director_inhibited_input(short local){(void)local;return inhibited;}
static int vr_controller(unsigned *buttons,float triggers[2],float thumbs[4]){(void)buttons;(void)triggers;(void)thumbs;return controller;}
static long game_time_get(void){return tick;}
static double vr_pose_time(void){return pose_time;}
static real vr_units_per_metre(void){return units;}
static int vr_render_drawn_camera(float *out){memcpy(out,camera.n,sizeof camera.n);return 1;}
static void unit_get_camera_position(long index,real_point3d *out){assert(index==0);*out=camera;}
static int valid_real_point3d(real_point3d const *p){return isfinite(p->n[0])&&isfinite(p->n[1])&&isfinite(p->n[2]);}
static int valid_real_vector3d(real_vector3d const *v){return valid_real_point3d(v);}
static real dot_product3d(real_vector3d const *a,real_vector3d const *b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static real magnitude3d(real_vector3d const *v){return sqrtf(dot_product3d(v,v));}
static real normalize3d(real_vector3d *v){real n=magnitude3d(v);if(n>0)for(int k=0;k<3;k++)v->n[k]/=n;return n;}
static void vector_from_points3d(real_point3d const *a,real_point3d const *b,real_vector3d *out){for(int k=0;k<3;k++)out->n[k]=b->n[k]-a->n[k];}
static void point_from_line3d(real_point3d const *p,real_vector3d const *v,real s,real_point3d *out){for(int k=0;k<3;k++)out->n[k]=p->n[k]+s*v->n[k];}
static void scale_vector3d(real_vector3d const *v,real s,real_vector3d *out){for(int k=0;k<3;k++)out->n[k]=s*v->n[k];}
static real_vector3d *cross_product3d(real_vector3d const *a,real_vector3d const *b,real_vector3d *out){
 real_vector3d temp={.n={a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};*out=temp;return out;
}
static real_vector3d *perpendicular3d(real_vector3d const *a,real_vector3d *out){
 real_vector3d axis=fabsf(a->i)<.8f?(real_vector3d){.n={1,0,0}}:up;return cross_product3d(a,&axis,out);
}
static int vr_interaction_owner(int hand){return busy[hand];}
static int vr_weapon_hand(void){return weapon_hand;}
static int vr_hand_empty(void){return empty;}
static int vr_two_handed(void){return two_handed;}
static int vr_hand_pose(int hand,float const *anchor,float *point,float *forward,float *out_up){
 (void)anchor;if(!tracking[hand])return 0;memcpy(point,palms[hand].n,sizeof palms[hand].n);
 memcpy(forward,((real_vector3d){.n={1,0,0}}).n,sizeof palms[hand].n);memcpy(out_up,up.n,sizeof up.n);return 1;
}
static int vr_render_palm_point(int hand,long unit,float *point){assert(unit==0);if(palm_valid)memcpy(point,palms[hand].n,sizeof palms[hand].n);return palm_valid;}
static real vr_hand_speed(int hand){return speed[hand];}
static int vr_interaction_grip(int hand,int *pressed,int *released){(void)pressed;(void)released;return grip[hand];}
static int vr_interaction_trigger(int hand){return trigger[hand];}
static void projectile_set_target_object_index(long index,long target){assert(index==live_index);shot.projectile.target_object_index=target;target_updates++;}
static void vr_extra_projectile_feedback(int hand,real_point3d const *point){feedback++;feedback_hand=hand;feedback_point=*point;}
'''

checks = r'''
static void reset(void){
 memset(&shot,0,sizeof shot);memset(&body,0,sizeof body);memset(&definition,0,sizeof definition);
 live_index=0x10001;tick=100;pose_time=10;enabled=active=controller=empty=palm_valid=1;
 connection=coop=host_permission=peers=paused=inhibited=cinematic=0;
 body.object.parent_object_index=NONE;body.object.owner_team_index=4;body.unit.player_index=3;player_data.unit_index=0;
 body.unit.current_weapon_index=0;body.unit.weapons[0]=4;
 guns[0].object.type=guns[1].object.type=_object_type_weapon;
 shot.object.parent_object_index=NONE;shot.object.type=_object_type_projectile;shot.object.owner_object_index=8;
 shot.object.owner_player_index=9;shot.object.owner_team_index=2;shot.object.up=up;
 shot.object.position=(real_point3d){.n={-10,0,1}};
 shot.object.translational_velocity=(real_vector3d){.n={20,0,0}};
 shot.projectile.target_object_index=0;shot.projectile.ignore_object_index=8;
 shot.projectile.detonation_timer=.45f;shot.projectile.arming_time=.7f;shot.projectile.odometer=7;
 shot.projectile.detonation_timer_delta=.01f;shot.projectile.arming_time_delta=.02f;
 shot.projectile.deceleration_timer=.3f;shot.projectile.deceleration_timer_delta=.04f;shot.projectile.maximum_damage_distance=100;
 for(int h=0;h<2;h++){tracking[h]=grip[h]=trigger[h]=1;busy[h]=0;speed[h]=3;palms[h]=(real_point3d){.n={.1f,(real)h*2,1}};}
 camera=(real_point3d){.n={0,0,1.6f}};weapon_hand=1;two_handed=0;units=1;palm_radius=.04f;
 feedback=object_deleted=target_updates=0;feedback_hand=-1;vr_projectile_parry_new_map();
}
static void stroke(int hand){
 vr_projectile_parry_tick(0);tick++;pose_time+=1.0/30.0;palms[hand].x-=.1f;vr_projectile_parry_tick(0);
}
static int attempt(real solid){
 real fraction=-1;real_point3d end={.n={10,0,1}};real_vector3d velocity=shot.object.translational_velocity;
 int result=vr_projectile_parry_try(live_index,&end,&velocity,solid,1,&fraction);
 if(result)assert(fraction>=0&&fraction<solid);
 return result;
}
static void unchanged(void){
 assert(!feedback&&!target_updates&&shot.object.owner_object_index==8&&shot.projectile.target_object_index==0);
 assert(shot.projectile.detonation_timer==.45f&&shot.projectile.arming_time==.7f&&shot.projectile.odometer==7);
}
static void lifetime(void){
 assert(shot.projectile.detonation_timer==.45f&&shot.projectile.arming_time==.7f&&shot.projectile.odometer==7);
 assert(shot.projectile.detonation_timer_delta==.01f&&shot.projectile.arming_time_delta==.02f);
 assert(shot.projectile.deceleration_timer==.3f&&shot.projectile.deceleration_timer_delta==.04f&&shot.projectile.maximum_damage_distance==100);
}
int main(void){
 /* Bullet crossing both endpoints, ownership, homing, timing and haptic side. */
 reset();stroke(0);assert(attempt(1));assert(feedback==1&&feedback_hand==0&&target_updates==1);
 assert(shot.object.owner_object_index==0&&shot.object.owner_player_index==3&&shot.object.owner_team_index==4);
 assert(shot.projectile.ignore_object_index==0&&shot.projectile.target_object_index==NONE);
 assert(fabsf(shot.object.translational_velocity.i+20)<.001f);lifetime();
 assert(!attempt(1));vr_projectile_parry_reset();stroke(0);assert(!attempt(1));assert(feedback==1);
 vr_projectile_parry_forget(live_index);assert(attempt(1));
 /* Every title/projectile tag uses the same movement; a native radius counts
  * for Wraith/Banshee-sized shots, with no unbounded proximity shield. */
 reset();shot.definition_index=77;definition.projectile.collision_radius=.12f;palms[0].y=.15f;stroke(0);assert(attempt(1));lifetime();
 reset();definition.projectile.collision_radius=100;palms[0].y=.25f;stroke(0);assert(!attempt(1));unchanged();
 /* Either actual hand, handed weapon, off hand and busy arbitration. */
 reset();palms[1].y=0;palms[0].y=2;weapon_hand=0;empty=0;stroke(1);assert(attempt(1)&&feedback_hand==1);
 for(int h=0;h<2;h++)for(int owner=1;owner<VR_INTERACTION_COUNT;owner++){
  reset();palms[h].y=0;palms[1-h].y=2;stroke(h);busy[h]=owner;assert(!attempt(1));unchanged();
 }
 /* A held gun itself qualifies the deliberate gesture. Neither firing nor
  * Grip is required, so fixed and physical held-gun modes share the path. */
 for(int h=0;h<2;h++)for(int firing=0;firing<2;firing++){
  reset();palms[h].y=0;palms[1-h].y=2;weapon_hand=h;empty=0;grip[h]=0;trigger[h]=firing;
  stroke(h);assert(attempt(1)&&feedback_hand==h);
  reset();palms[h].y=0;palms[1-h].y=2;weapon_hand=h;empty=0;grip[h]=0;trigger[h]=firing;
  vr_projectile_parry_tick(0);tick++;pose_time+=1.0/30.0;vr_projectile_parry_tick(0);
  assert(!attempt(1));unchanged(); /* aim/fire with no deliberate swipe */
  reset();palms[h].y=0;palms[1-h].y=2;weapon_hand=h;empty=0;stroke(h);busy[h]=VR_INTERACTION_RELOAD;
  assert(!attempt(1));unchanged();
 }
 reset();weapon_hand=0;empty=0;two_handed=1;stroke(0);assert(attempt(1));
 reset();weapon_hand=1;empty=0;two_handed=1;stroke(0);assert(!attempt(1));unchanged();
 reset();weapon_hand=0;empty=0;stroke(0);empty=1;assert(!attempt(1));unchanged(); /* ownership changed */
 reset();weapon_hand=0;empty=0;stroke(0);body.unit.weapons[0]=5;assert(!attempt(1));unchanged(); /* gun switched */
 reset();weapon_hand=0;empty=0;stroke(0);body.unit.current_weapon_index=NONE;assert(!attempt(1));unchanged(); /* native holster */
 reset();weapon_hand=0;empty=0;stroke(0);body.unit.weapons[0]=NONE;assert(!attempt(1));unchanged(); /* native drop */
 reset();weapon_hand=0;empty=0;stroke(0);weapon_hand=1;assert(!attempt(1));unchanged(); /* hand transfer */
 for(int slot=-1;slot<5;slot+=5){
  reset();weapon_hand=0;empty=0;grip[0]=trigger[0]=0;body.unit.current_weapon_index=(short)slot;
  stroke(0);assert(!attempt(1));unchanged(); /* fixed mode but no actual gun */
 }
 /* Real production authority: standalone local and explicitly compatible
  * co-op host; no guests, PvP or unconsented hosts. */
 for(int mode=0;mode<3;mode++)for(int bits=0;bits<8;bits++){
  reset();connection=mode;coop=!!(bits&1);host_permission=!!(bits&2);peers=!!(bits&4);stroke(0);
  int allowed=mode==0||(mode==1&&bits==7);assert(attempt(1)==allowed);if(!allowed)unchanged();
 }
 for(int disabled=0;disabled<10;disabled++){
  reset();stroke(0);
  switch(disabled){case 0:enabled=0;break;case 1:paused=1;break;case 2:inhibited=1;break;case 3:controller=0;break;
  case 4:active=0;break;case 5:cinematic=1;break;case 6:body.object.damage_flags=FLAG(_object_dead_bit);break;
  case 7:body.object.parent_object_index=9;break;case 8:body.unit.flags=FLAG(_unit_suspended_bit);break;
  case 9:body.biped.flags=FLAG(_biped_no_collision_bit);break;}
  assert(!attempt(1));unchanged();
 }
 /* The hand must actually move as a fist; no standing shield or remote aim. */
 reset();vr_projectile_parry_tick(0);assert(!attempt(1));unchanged();
 reset();grip[0]=0;stroke(0);assert(!attempt(1));unchanged();
 reset();trigger[0]=0;stroke(0);assert(!attempt(1));unchanged();
 reset();speed[0]=.5f;stroke(0);assert(!attempt(1));unchanged();
 reset();tracking[0]=0;stroke(0);assert(!attempt(1));unchanged();
 reset();palms[0].y=.2f;stroke(0);assert(!attempt(1));unchanged();
 reset();stroke(0);assert(!attempt(.4f));unchanged(); /* wall is before palm */
 /* Recenter, pause gap, backwards game tick and tracking discontinuity. */
 reset();stroke(0);vr_projectile_parry_reset();assert(!attempt(1));unchanged();
 reset();vr_projectile_parry_tick(0);pose_time+=2;tick++;palms[0].x-=.1f;assert(!attempt(1));unchanged();
 reset();vr_projectile_parry_tick(0);pose_time+=.033;tick--;palms[0].x-=.1f;assert(!attempt(1));unchanged();
 reset();vr_projectile_parry_tick(0);pose_time+=.033;tick++;palms[0].x-=2;assert(!attempt(1));unchanged();
 reset();vr_projectile_parry_tick(0);pose_time+=.033;tick++;palms[0].x-=.1f;camera.x-=.1f;assert(!attempt(1));unchanged();
 /* Airborne frag/plasma fuse remains; settled, stuck, exploding and deleted
  * projectiles retain native behavior. A slow airborne throw gets fist speed. */
 reset();stroke(0);shot.object.position=(real_point3d){.n={-.02f,0,1}};
 shot.object.translational_velocity=(real_vector3d){.n={.01f,0,0}};
 assert(attempt(1));assert(fabsf(shot.object.translational_velocity.i+.1f)<.001f);lifetime();
 for(int bit=0;bit<8;bit++)if(bit==_projectile_attached_bit||bit==_projectile_stopped_after_collision_bit||
     bit==_projectile_already_super_exploded_bit||bit==_projectile_will_super_explode_bit){
  reset();stroke(0);shot.projectile.flags=FLAG(bit);assert(!attempt(1));unchanged();
 }
 reset();stroke(0);shot.object.flags=FLAG(_object_at_rest_bit);assert(!attempt(1));unchanged();
 reset();stroke(0);shot.object.parent_object_index=6;assert(!attempt(1));unchanged();
 reset();stroke(0);shot.projectile.action=_projectile_action_detonate;assert(!attempt(1));unchanged();
 reset();stroke(0);object_deleted=1;assert(!attempt(1));unchanged();
 reset();stroke(0);shot.object.type=0;assert(!attempt(1));unchanged();
 reset();stroke(0);shot.projectile.detonation_timer=1;assert(!attempt(1));assert(!feedback);
 /* NaN/Inf/bounds cannot change native state or reach feedback. */
 for(int bad=0;bad<9;bad++){
  reset();stroke(0);
  switch(bad){case 0:shot.object.position.x=NAN;break;case 1:shot.object.translational_velocity.x=INFINITY;break;
   case 2:shot.projectile.detonation_timer=NAN;break;case 3:definition.projectile.collision_radius=NAN;break;
   case 4:palm_radius=NAN;break;case 5:units=NAN;break;case 6:shot.object.up.z=NAN;break;
   case 7:pose_time=NAN;break;case 8:shot.projectile.arming_time=NAN;break;}
  assert(!attempt(1));assert(!feedback&&!target_updates&&shot.object.owner_object_index==8);
 }
 reset();stroke(0);assert(!attempt(NAN));unchanged();
 reset();stroke(0);live_index=0x100ff;assert(!attempt(1));unchanged();
 /* Slot reuse with a new salted handle does not inherit another projectile. */
 reset();stroke(0);assert(attempt(1));live_index=0x20001;shot.object.translational_velocity.i=20;assert(attempt(1));
 puts("PASS: production projectile parry authority, swept contact, both hands, ownership/homing, fuse, lifecycle, malformed inputs");
}
'''

projectiles = read('source/items/projectiles.c')
header = read('source/items/projectiles.h')
enums = ''.join(re.search(r'enum ' + name + r'\s*\{.*?\};', header, re.S)[0] + '\n'
                for name in ('projectile_datum_flags', 'projectile_action'))
module = re.sub(r'^#include .*\n', '', read('port/linux/game/vr_projectile_parry.c'), flags=re.M)
extra = read('port/linux/game/vr_extra_interaction.c')
source = fixture + enums + function(extra, 'extra_player') + '\n'
source += function(extra, 'vr_extra_action_owner') + '\n' + module + checks

with tempfile.TemporaryDirectory(prefix='test67-projectiles-') as directory:
    path = Path(directory)
    (path / 'check.c').write_text(source, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-function', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', str(path / 'check.c'), '-lm',
                    '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)

# Lifecycle and native insertion contract; the compiled movement fixture below
# runs the actual splice, including disabled-query ordering and leftover travel.
assert 'vr_projectile_parry_forget' in function(projectiles, 'projectile_new')
assert 'vr_projectile_parry_forget' in function(projectiles, 'projectile_delete')
assert 'vr_projectile_parry_new_map' in function(projectiles, 'projectiles_initialize_for_new_map')
assert 'vr_projectile_parry_new_map' in function(projectiles, 'projectiles_dispose_from_old_map')
update = function(projectiles, 'projectile_update')
start = update.index('\t\thit = collision_count')
stop = update.index('\n\t\tif (hit)', start)
splice = update[start:stop]
movement = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;typedef int boolean;
typedef union {real n[3];struct{real x,y,z;};}real_point3d,real_vector3d;
#define HALO_VR 1
#define TRUE 1
#define FALSE 0
#define MAXIMUM_PROJECTILE_COLLISIONS_PER_UPDATE 3
enum{_projectile_action_disappear=2};
struct {struct{real_point3d position;}object;struct{int action;real odometer;}projectile;}shot;
static int global_current_collision_user_depth,query_count,parry_calls,reflect,obstruction,translations;
static real observed_limit;
static void vector_from_points3d(real_point3d const *a,real_point3d const *b,real_vector3d *v){for(int k=0;k<3;k++)v->n[k]=b->n[k]-a->n[k];}
static void point_from_line3d(real_point3d const *p,real_vector3d const *v,real s,real_point3d *out){for(int k=0;k<3;k++)out->n[k]=p->n[k]+s*v->n[k];}
static real magnitude3d(real_vector3d const *v){return sqrtf(v->n[0]*v->n[0]+v->n[1]*v->n[1]+v->n[2]*v->n[2]);}
struct collision{real t;};
static int projectile_collision_test_line(long id,real_point3d const *end,struct collision *c){(void)id;(void)end;query_count++;c->t=.25f;return obstruction;}
static int vr_projectile_parry_try(long id,real_point3d const *p,real_vector3d const *v,real limit,real remaining,real *at){
 (void)id;(void)p;(void)v;assert(remaining==1);parry_calls++;observed_limit=limit;*at=.5f;return reflect&&limit>.5f;
}
static void object_translate(long id,real_point3d const *p,void const *location){(void)id;assert(!location);shot.object.position=*p;translations++;}
static void run(int limit,int action){
 typeof(shot)*projectile=&shot;long projectile_index=1;int collision_count=limit,moved=0,hit=0,vr_parried=0;
 real time_remaining=1;real_point3d new_position={.n={20,0,0}};real_vector3d new_velocity={.n={20,0,0}};struct collision collision;
 shot.projectile.action=action;
 int iterations=0;
 while(iterations++==0){
''' + splice + r'''
 }
 if(reflect&&!obstruction&&limit<3&&action!=2){
  assert(vr_parried&&translations==1&&shot.object.position.x==10&&shot.projectile.odometer==10);
  assert(time_remaining==.5f&&collision_count==limit+1&&global_current_collision_user_depth==1);
 }else{assert(!vr_parried&&!translations&&time_remaining==1&&global_current_collision_user_depth==2);}
 assert(query_count==(limit<3&&action!=2));
 assert(hit==(query_count&&obstruction));assert(moved==query_count);
 assert(parry_calls==(limit<3&&action!=2));
 if(query_count)assert(observed_limit==(obstruction?.25f:1));
}
int main(void){
 for(int enabled=0;enabled<2;enabled++)for(int blocked=0;blocked<2;blocked++)for(int limit=0;limit<4;limit++)for(int action=0;action<3;action+=2){
  memset(&shot,0,sizeof shot);query_count=parry_calls=translations=0;global_current_collision_user_depth=2;
  reflect=enabled;obstruction=blocked;run(limit,action);
 }
 puts("PASS: production native movement splice preserves disabled collision path, nearest obstruction, contact travel, remaining tick and collision stack");
}
'''
with tempfile.TemporaryDirectory(prefix='test67-projectile-movement-') as directory:
    path = Path(directory)
    (path / 'check.c').write_text(movement, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                    str(path / 'check.c'), '-lm', '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)

# The same native splice with HALO_VR absent is the flat Android path. Its
# collision query/order and translation results must equal the old branch.
flat_movement = movement.replace('#define HALO_VR 1', '')
flat_movement = flat_movement.replace('if(reflect&&!obstruction&&limit<3&&action!=2)', 'if(0)')
flat_movement = flat_movement.replace('assert(parry_calls==(limit<3&&action!=2));', 'assert(parry_calls==0);')
flat_movement = flat_movement.replace('if(query_count)assert(observed_limit==(obstruction?.25f:1));', '')
flat_movement = flat_movement.replace('PASS: production native movement splice preserves disabled collision path, nearest obstruction, contact travel, remaining tick and collision stack', 'PASS: flat Android native collision splice retains its original path')
with tempfile.TemporaryDirectory(prefix='test67-projectile-flat-') as directory:
    path = Path(directory)
    (path / 'check.c').write_text(flat_movement, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-function', '-Wno-unused-variable',
                    '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                    str(path / 'check.c'), '-lm', '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)

