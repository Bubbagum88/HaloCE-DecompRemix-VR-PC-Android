"""Compile the production impact transaction with a deterministic native oracle."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'build/interaction-impact-tests'
out.mkdir(parents=True, exist_ok=True)
production = (ROOT/'port/linux/game/vr_interaction_impact.c').read_text()
production = re.sub(r'^#include.*$', '', production, flags=re.M)
stub = r'''
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#include "vr_interaction_impact_math.h"
typedef int boolean;
typedef union { struct {float i,j,k;}; float n[3]; } real_vector3d;
typedef real_vector3d real_point3d;
struct location {int leaf;};
struct collision_result {int type;long object_index;real_point3d point;struct {real_vector3d n;} plane;struct location location;short material_type,node_index,region_index,material_index;};
struct object_datum {long definition_index;struct {int type,damage_flags;} object;};
struct unit_datum {long definition_index;struct {int owner_team_index;} object;struct {long player_index;} unit;};
struct unit_definition {struct {struct {long index;} melee_damage;} unit;};
struct damage_data {long owner_object_index,owner_player_index;int owner_team_index;struct location location;real_point3d origin,epicenter;real_vector3d direction;float scale;};
enum {FALSE,TRUE};
enum {_game_connection_local,_game_connection_network_server,_game_connection_network_client};
enum {_collision_result_object=1,_collision_result_structure=2};
enum {_object_type_biped=1,_object_dead_bit=0};
#define NONE (-1)
#define TEST_FLAG(v,b) ((v)&(1u<<(b)))
static int tick,connection,campaign,enabled=1,damage_calls;
static float threshold=2,cap=1,damage_scale;
static long damaged,damage_owner;
static struct object_datum objects[5];
static struct unit_datum owner={0,{2},{10}};
static struct unit_definition definition={{{7}}};
static struct object_datum* object_try_and_get(long i){return i>=0&&i<5?&objects[i]:0;}
static struct unit_datum* unit_try_and_get(long i){return i==0?&owner:0;}
static struct unit_definition* unit_definition_get(long i){(void)i;return &definition;}
static int game_connection(void){return connection;}
static int network_coop_active(void){return campaign;}
static int network_interaction_host_ready(void){return campaign;}
static long game_time_get(void){return tick;}
static int config_boolean(char const*k){(void)k;return enabled;}
static float config_real(char const*k){return !strcmp(k,"vr.impact_threshold")?threshold:cap;}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static void normalize3d(real_vector3d*v){float l=sqrtf(dot_product3d(v,v));if(l>0)for(int i=0;i<3;++i)v->n[i]/=l;}
static void damage_data_new(struct damage_data*d,long i){(void)i;memset(d,0,sizeof(*d));}
static void object_cause_damage(struct damage_data*d,long target,int node,int region,int material,real_vector3d const*n){(void)n;assert(node>=-1&&region>=-1&&material>=-1);damage_calls++;damaged=target;damage_owner=d->owner_object_index;damage_scale=d->scale;}
void platform_log(char const*f,...){(void)f;}
'''
tests = r'''
int main(void) {
 real_vector3d velocity={{0,0,-.2f}};
 struct collision_result hit={0};hit.type=_collision_result_object;hit.object_index=2;hit.plane.n.k=1;
 assert(vr_interaction_impact_scale(.01f,1,1,2,1)==0);
 assert(vr_interaction_impact_scale(.2f,1,.25f,2,1)==1);
 assert(vr_interaction_impact_scale(.1f,1,2,2,1)<vr_interaction_impact_scale(.1f,1,.5f,2,1));
 assert(vr_interaction_impact_scale(NAN,1,1,2,1)==0);
 assert(vr_interaction_impact_scale(.2f,0,1,2,1)==0);
 assert(vr_interaction_impact_scale(-.2f,1,1,2,1)==0);
 vr_interaction_impact_track(1,0,1,1);vr_interaction_impact_collision(1,&hit,&velocity);
 assert(damage_calls==0);vr_interaction_impact_flush();assert(damage_calls==1&&damaged==2&&damage_owner==0&&damage_scale<=cap);
 vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==1);
 tick=10;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==2);
 tick=100;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==2);
 vr_interaction_impact_track(1,0,1,1);hit.object_index=0;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==2);
 hit.object_index=2;objects[2].object.damage_flags=1;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==2);objects[2].object.damage_flags=0;
 connection=_game_connection_network_client;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==2);
 connection=_game_connection_network_server;campaign=0;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==2);
 campaign=1;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==3);
 tick+=10;hit.type=_collision_result_structure;hit.node_index=hit.region_index=hit.material_index=-222;
 vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==3);
 objects[1].object.type=_object_type_biped;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_flush();assert(damage_calls==4&&damaged==1);
 tick+=10;vr_interaction_impact_collision(1,&hit,&velocity);vr_interaction_impact_reset();vr_interaction_impact_flush();assert(damage_calls==4);
 enabled=0;vr_interaction_impact_track(1,0,1,1);assert(!entries[0].active);
 puts("PASS: production impact authority, deferred collision damage, native attribution, kinetic weights/cap, expiry/debounce, world/self hits, reset and finite guards");
}
'''
c=out/'impact.c'; c.write_text(stub+production+tests)
binary=out/'impact'
subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
               '-I'+str(ROOT/'port/linux/game'),str(c),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
