"""Execute production optional move state against native-event fixtures.
No game assets, game launch, native animation rewrite or generated damage.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
production = (ROOT / 'port/linux/game/vr_combat_moves.c').read_text()
production = re.sub(r'^#include[^\n]*\n', '', production, flags=re.M)
production = production.replace('#ifdef HALO_VR', '', 1).rsplit('#endif', 1)[0]
header = (ROOT / 'port/linux/game/vr_combat_moves.h').read_text()
events = header[header.index('enum vr_combat_move_event_type'):header.index('#ifdef HALO_VR')]

fixture = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef float real;typedef int boolean;
typedef union {float n[3];struct {float x,y,z;};struct {float i,j,k;};}real_point3d,real_vector3d;
typedef struct {float scale;union {float n[4][3];struct {real_vector3d forward,left,up;real_point3d position;};};}real_matrix4x3;
#define NONE (-1)
#define TRUE 1
#define FALSE 0
#define TICKS_PER_SECOND 30
#define MAXIMUM_NODES_PER_MODEL 64
#define FLAG(b) (1u<<(b))
#define TEST_FLAG(v,b) (((v)&FLAG(b))!=0)
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define PIN(v,a,b) MIN(MAX(v,a),b)
enum {_actor_elite,_actor_jackal,_actor_grunt,_actor_hunter,_actor_unknown};
enum {_object_type_biped=1,_object_dead_bit=0,_unit_suspended_bit=1,_biped_airborne_bit=2};
enum {_unit_state_melee_attack=1,_unit_state_melee_airborne,_unit_state_leap_melee};
enum {_collision_test_for_projectiles_flags=1,_collision_result_object=2};
enum {VR_INTERACTION_NONE,VR_INTERACTION_NPC,VR_INTERACTION_WORLD};
struct object_fields {int type,owner_team_index;unsigned damage_flags;long parent_object_index;real_point3d position,bounding_sphere_center;real_vector3d forward,translational_velocity;real shield_vitality;struct {long size;}node_matrices;struct {long animation_graph_index;struct {short index,frame_index;}state;}animation;};
struct unit_fields {long actor_index,player_index;unsigned flags;int melee_attack_state;struct {int state;}animation;};
struct unit_datum {long definition_index;struct object_fields object;struct unit_fields unit;};
struct biped_datum {long definition_index;struct object_fields object;struct unit_fields unit;struct {unsigned flags;}biped;};
struct actor_datum {struct {int active,team_index,type;}meta;};
struct model_node {char name[32];short next_sibling_node_index,first_child_node_index,parent_node_index,pad;};
struct model {struct {int count;struct model_node *address;}nodes;};
struct object_definition {struct {struct {long index;}model;}object;};
struct animation {short frame_count,private_key_frame_index,private_second_key_frame_index;};
struct animation_graph {struct {int count;struct animation *address;}animations;};
struct collision_result {int type;long object_index;};
struct player_datum {long unit_index;};
#define TAG_BLOCK_GET_ELEMENT(b,n,t) ((t*)((b)->address)+(n))
#include "port/linux/game/vr_combat_pose.h"
static struct biped_datum bodies[40];static struct actor_datum actors[40];static struct player_datum player;
static struct model_node nodes[6];static struct model model={.nodes={6,nodes}};
static struct object_definition definition={.object={.model={0}}};
static struct animation clip={20,8,-1};static struct animation_graph graph={.animations={1,&clip}};
static long now,held[2];static short held_node[2];static real_point3d held_contact[2],hand[2],tracked_head;
static int allowed,moves_on,npc_on,empty,tracking,obstructed,owners[2],closed[2],grip[2],hand_valid[2],stun[40],rig_owned[40];
static float hand_speed[2],units=1;
static real_vector3d up={.n={0,0,1}},*global_up3d=&up;
static long game_time_get(void){return now;}
static short local_player_get_next(short last){(void)last;return 0;}
static long local_player_get_player_index(short local){(void)local;return 0;}
static struct player_datum *player_get(long p){assert(p==0);return &player;}
static int config_boolean(char const *key){if(!strcmp(key,"vr.npc_interaction"))return npc_on;assert(!strcmp(key,"vr.combat_moves"));return moves_on;}
static int vr_combat_enabled(void){return allowed;}
static int vr_hand_empty(void){return empty;}
static float vr_units_per_metre(void){return units;}
static struct unit_datum *unit_try_and_get(long id){return id>=0&&id<40?(struct unit_datum *)&bodies[id]:NULL;}
static struct unit_datum *unit_get(long id){assert(id>=0&&id<40);return unit_try_and_get(id);}
static struct biped_datum *biped_try_and_get(long id){return id>=0&&id<40?&bodies[id]:NULL;}
static struct actor_datum *actor_try_and_get(long id){return id>=0&&id<40?&actors[id]:NULL;}
static int game_team_is_enemy(int a,int b){return a!=b;}
static int valid_real_point3d(real_point3d const *p){return p&&isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
static int valid_real_vector3d(real_vector3d const *p){return valid_real_point3d(p);}
static float dot_product3d(real_vector3d const *a,real_vector3d const *b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(real_vector3d const *v){return sqrtf(dot_product3d(v,v));}
static float normalize3d(real_vector3d *v){float length=magnitude3d(v);if(length>0)for(int k=0;k<3;k++)v->n[k]/=length;return length;}
static void vector_from_points3d(real_point3d const *a,real_point3d const *b,real_vector3d *out){for(int k=0;k<3;k++)out->n[k]=b->n[k]-a->n[k];}
static void cross_product3d(real_vector3d const *a,real_vector3d const *b,real_vector3d *out){*out=(real_vector3d){.n={a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};}
static void unit_get_camera_position(long owner,real_point3d *out){*out=unit_get(owner)->object.position;out->z+=1.6f;}
static int vr_head_view_recent(float const *p,float const *f,float *head,float *g,float *u){(void)p;(void)f;memcpy(head,tracked_head.n,12);g[0]=1;g[1]=g[2]=u[0]=u[1]=0;u[2]=1;return tracking;}
static int collision_test_vector(int flags,real_point3d const *p,real_vector3d const *v,long owner,struct collision_result *hit){(void)flags;(void)p;(void)v;(void)owner;hit->type=0;hit->object_index=NONE;return obstructed;}
static struct animation_graph *animation_graph_definition_get(long id){assert(id==0);return &graph;}
static struct object_definition *object_definition_get(long id){(void)id;return &definition;}
static struct model *model_definition_get(long id){assert(id==0);return &model;}
static int vr_combat_control_opening(long target){return stun[target];}
static int vr_npc_interaction_owned(long target){return rig_owned[target];}
static int vr_npc_interaction_contact(int h,long *object,short *node,float *out){if(held[h]==NONE)return 0;*object=held[h];*node=held_node[h];memcpy(out,held_contact[h].n,12);return 1;}
static int vr_interaction_owner(int h){return owners[h];}
static int vr_interaction_grip(int h,int *pressed,int *released){if(pressed)*pressed=0;if(released)*released=0;return grip[h];}
static int vr_physical_melee_hand_allowed(int h){return closed[h]&&!owners[h]&&tracking;}
static float vr_hand_speed(int h){return hand_speed[h];}
static float vr_melee_speed(void){return 2;}
static int vr_hand_pose(int h,float const *camera,float *p,float *f,float *u){(void)camera;memcpy(p,hand[h].n,12);f[0]=u[2]=1;f[1]=f[2]=u[0]=u[1]=0;return tracking&&hand_valid[h];}
'''

checks = r'''
static void setup(void){
 memset(bodies,0,sizeof bodies);memset(actors,0,sizeof actors);memset(stun,0,sizeof stun);memset(rig_owned,0,sizeof rig_owned);
 for(int i=0;i<40;i++){
  bodies[i].object.type=_object_type_biped;bodies[i].object.owner_team_index=i?1:0;bodies[i].object.parent_object_index=NONE;
  bodies[i].object.position.x=i?1:0;bodies[i].object.bounding_sphere_center=(real_point3d){.n={i?1:0,0,1}};
  bodies[i].object.forward.i=i?-1:1;bodies[i].unit.player_index=i?NONE:0;bodies[i].unit.actor_index=i?i:NONE;
  bodies[i].unit.animation.state=_unit_state_melee_attack;bodies[i].unit.melee_attack_state=1;
  bodies[i].object.node_matrices.size=6*sizeof(real_matrix4x3);actors[i].meta.active=1;actors[i].meta.team_index=i?1:0;actors[i].meta.type=_actor_grunt;
 }
 memset(nodes,0,sizeof nodes);strcpy(nodes[0].name,"bip01 pelvis");nodes[0].parent_node_index=NONE;
 strcpy(nodes[1].name,"bip01 spine");nodes[1].parent_node_index=0;
 strcpy(nodes[2].name,"bip01 l upperarm");nodes[2].parent_node_index=1;
 strcpy(nodes[3].name,"bip01 l forearm");nodes[3].parent_node_index=2;
 strcpy(nodes[4].name,"bip01 l hand");nodes[4].parent_node_index=3;
 strcpy(nodes[5].name,"bip01 l thigh");nodes[5].parent_node_index=0;
 for(int h=0;h<2;h++){held[h]=NONE;held_node[h]=3;owners[h]=0;closed[h]=grip[h]=hand_valid[h]=1;hand_speed[h]=3;held_contact[h]=hand[h]=(real_point3d){.n={.8f,.1f,1}};}
 clip=(struct animation){20,8,-1};model.nodes.count=6;allowed=moves_on=npc_on=empty=tracking=1;obstructed=0;units=1;
 now=10;player.unit_index=0;tracked_head=(real_point3d){.n={0,0,1.6f}};
 vr_combat_moves_reset();vr_combat_moves_tick(0);
}
static void tick(void){++now;vr_combat_moves_tick(0);}
static void attack(int kind){
 struct combat_move_state *s=move_slot(1,TRUE);s->attacks=kind;
 vr_combat_moves_note_melee(0,1);assert(s->attack_until>now);
 bodies[1].object.animation.state.frame_index=8;
}
static void arm_hold(void){held[0]=1;owners[0]=VR_INTERACTION_NPC;}
static void punch(void){real_vector3d down={.n={0,0,-1}};vr_combat_moves_note_hit(0,1,&hand[1],&down,1);}
int main(void){
 struct vr_combat_move_event event;struct vr_combat_pose_request pose;
 /* The overlay follows the exact native clip and hit keyframe. */
 setup();attack(0);assert(vr_combat_moves_poll_event(&event)&&event.type==VR_COMBAT_MOVE_ATTACK_SWEEP);
 assert(vr_combat_moves_cue(1)==VR_COMBAT_MOVE_ATTACK_SWEEP);
 int cues=0;for(int i=0;i<VR_COMBAT_MOVE_TARGETS;i++)if(vr_combat_moves_cue_target(i)==1)cues++;
 assert(cues==1&&vr_combat_moves_cue_target(-1)==NONE&&vr_combat_moves_cue_target(VR_COMBAT_MOVE_TARGETS)==NONE);
 assert(vr_combat_moves_pose(1,&pose)&&pose.mode==VR_COMBAT_POSE_SWEEP&&fabsf(pose.phase-.65f)<1e-6f);
 assert(vr_combat_moves_defend(0,1)==1);tracked_head.z-=.21f;
 assert(vr_combat_moves_defend(0,1)==0&&vr_combat_moves_opening(1));assert(vr_combat_moves_defend(0,1)==0);
 assert(vr_combat_moves_cue(1)==VR_COMBAT_MOVE_DUCK);
 assert(vr_combat_moves_poll_event(&event)&&event.type==VR_COMBAT_MOVE_DUCK);
 assert(!vr_combat_moves_poll_event(&event));bodies[1].object.animation.state.frame_index=12;assert(vr_combat_moves_defend(0,1)==1);
 setup();attack(0);tracked_head.z-=.25f;bodies[0].object.position.z-=.25f;assert(vr_combat_moves_defend(0,1)==1); /* lower floor is not a duck */
 setup();attack(0);tracked_head.z-=.25f;bodies[1].object.animation.state.frame_index=3;assert(vr_combat_moves_defend(0,1)==1);
 bodies[1].object.animation.state.frame_index=8;empty=0;assert(vr_combat_moves_defend(0,1)==1);empty=1;owners[0]=VR_INTERACTION_NPC;assert(vr_combat_moves_defend(0,1)==1);
 setup();actors[1].meta.type=_actor_elite;attack(1);tracked_head.z-=.3f;assert(vr_combat_moves_defend(0,1)==1);tracked_head.y=.23f;assert(vr_combat_moves_defend(0,1)==0);
 setup();attack(2);tracked_head.y=.23f;assert(vr_combat_moves_defend(0,1)==0);
 setup();obstructed=1;vr_combat_moves_note_melee(0,1);assert(!move_slot(1,FALSE));
 setup();clip.private_key_frame_index=30;vr_combat_moves_note_melee(0,1);assert(!move_slot(1,FALSE));
 setup();attack(0);bodies[1].object.animation.state.index=1;tracked_head.z-=.3f;assert(vr_combat_moves_defend(0,1)==1&&!vr_combat_moves_pose(1,&pose));
 /* Only a real held arm plus second fist contact creates arm control. */
 setup();arm_hold();struct biped_datum snapshot=bodies[1];punch();
 assert(!memcmp(&snapshot,&bodies[1],sizeof snapshot));assert(move_slot(1,FALSE)->arm_pending_until>now&&!vr_combat_moves_opening(1));
 assert(vr_combat_moves_poll_event(&event)&&event.type==VR_COMBAT_MOVE_ARM_OPENING);
 assert(vr_combat_moves_cue(1)==VR_COMBAT_MOVE_ARM_OPENING);
 assert(vr_combat_moves_pose(1,&pose)&&pose.mode==VR_COMBAT_POSE_CLUTCH_KNEEL&&pose.has_control_target);
 rig_owned[1]=1;assert(!vr_combat_moves_pose(1,&pose)); /* accepted physical rig has priority */
 held[0]=NONE;owners[0]=0;grip[0]=0;tick();assert(vr_combat_moves_opening(1));long ends=move_slot(1,FALSE)->opening_until;
 for(int i=0;i<30;i++)tick();assert(now==ends&&!vr_combat_moves_opening(1));
 for(int node=0;node<6;node+=5){setup();arm_hold();held_node[0]=node;punch();assert(!move_slot(1,FALSE)->arm_pending_until);}
 setup();arm_hold();hand[1].x+=.4f;punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();closed[1]=0;punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();hand_valid[0]=0;punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();owners[0]=0;punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();grip[0]=0;punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();nodes[2].parent_node_index=3;punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();memset(nodes[3].name,'x',sizeof nodes[3].name);punch();assert(!move_slot(1,FALSE)->arm_pending_until);
 setup();arm_hold();punch();tick();punch();assert(moves.events==1); /* a hold cannot repeat the gesture */
 setup();arm_hold();punch();for(int i=0;i<62;i++)tick();assert(!move_slot(1,FALSE)->arm_pending_until&&!vr_combat_moves_opening(1));
 /* Both gameplay orders accept a real tracked release. Cancellation never
  * turns loss of tracking, contact, feature, owner or node into an opening. */
 setup();arm_hold();punch();grip[0]=0;tick();assert(vr_combat_moves_opening(1));
 for(int reason=0;reason<7;reason++){
  setup();arm_hold();punch();
  if(reason==0){held[0]=NONE;owners[0]=0;}
  if(reason==1){held[0]=NONE;owners[0]=0;hand_valid[0]=0;grip[0]=0;}
  if(reason==2){held[0]=NONE;owners[0]=0;npc_on=0;grip[0]=0;}
  if(reason==3){owners[0]=VR_INTERACTION_WORLD;grip[0]=0;}
  if(reason==4){held_node[0]=4;grip[0]=0;}
  if(reason==5){hand[0].x=NAN;grip[0]=0;}
  if(reason==6){empty=0;grip[0]=0;}
  tick();assert(!move_slot(1,FALSE)->arm_pending_until&&!vr_combat_moves_opening(1));
  held[0]=NONE;owners[0]=0;hand_valid[0]=npc_on=empty=1;hand[0].x=.8f;grip[0]=0;
  tick();assert(!vr_combat_moves_opening(1)); /* later release cannot revive it */
 }
 /* Species matrix: Grunt yes; shielded Elite requires an existing opening;
  * Jackal front requires an opening; Hunters/unknown never arm/pummel. */
 for(int species=0;species<=_actor_unknown;species++){
  setup();actors[1].meta.type=species;bodies[1].object.shield_vitality=1;arm_hold();punch();
  assert((move_slot(1,FALSE)!=NULL&&move_slot(1,FALSE)->arm_pending_until>now)==(species==_actor_grunt));
 }
 setup();actors[1].meta.type=_actor_elite;stun[1]=1;bodies[1].object.shield_vitality=1;arm_hold();punch();assert(move_slot(1,FALSE)->arm_pending_until>now);
 setup();actors[1].meta.type=_actor_jackal;bodies[1].object.forward.i=1;arm_hold();punch();assert(move_slot(1,FALSE)->arm_pending_until>now);
 /* Native jump, native collision contact: no synthetic move or damage. */
 setup();bodies[0].biped.flags=FLAG(_biped_airborne_bit);bodies[0].object.position.z=.4f;bodies[0].object.translational_velocity.k=-.1f;tick();
 snapshot=bodies[0];punch();assert(!memcmp(&snapshot,&bodies[0],sizeof snapshot));assert(vr_combat_moves_opening(1)&&move_slot(1,FALSE)->pummelling);
 assert(vr_combat_moves_cue(1)==VR_COMBAT_MOVE_PUMMEL_OPENING);
 assert(vr_combat_moves_poll_event(&event)&&event.type==VR_COMBAT_MOVE_PUMMEL_OPENING);
 bodies[0].biped.flags=0;tick();punch();assert(vr_combat_moves_poll_event(&event)&&event.type==VR_COMBAT_MOVE_PUMMEL_HIT);
 setup();punch();assert(!vr_combat_moves_opening(1));
 setup();bodies[0].biped.flags=FLAG(_biped_airborne_bit);bodies[0].object.position.z=.4f;bodies[0].object.translational_velocity.k=.1f;tick();punch();assert(!vr_combat_moves_opening(1));
 /* Config, owner, authority, timeline, death and tracking cancel safely. */
 setup();attack(0);tracked_head.z-=.3f;allowed=0;assert(vr_combat_moves_defend(0,1)==1&&!vr_combat_moves_opening(1));vr_combat_moves_tick(0);assert(moves.owner==NONE);
 setup();attack(0);moves_on=0;vr_combat_moves_tick(0);assert(moves.owner==NONE);
 assert(!vr_combat_moves_cue(1));
 setup();attack(0);player.unit_index=2;assert(vr_combat_moves_defend(0,1)==1);vr_combat_moves_tick(2);assert(moves.owner==2&&!move_slot(1,FALSE));
 setup();attack(0);tracked_head.z=NAN;assert(vr_combat_moves_defend(0,1)==1);tracking=0;assert(vr_combat_moves_defend(0,1)==1);
 setup();arm_hold();punch();bodies[1].object.damage_flags=FLAG(_object_dead_bit);tick();assert(!move_slot(1,FALSE));
 setup();attack(0);now-=2;vr_combat_moves_tick(0);assert(!move_slot(1,FALSE));
 setup();attack(0);now+=3;vr_combat_moves_tick(0);assert(!move_slot(1,FALSE));
 /* Pool pressure drops the optional new action, preserving active owners. */
 setup();for(int i=1;i<=MOVE_SLOTS;i++){struct combat_move_state *s=move_slot(i,TRUE);assert(s);s->opening_until=now+30;}
 assert(!move_slot(17,TRUE));for(int i=1;i<=MOVE_SLOTS;i++)assert(vr_combat_moves_opening(i));
 puts("PASS: production combat move native clip/timing, duck/sidestep, exact held-arm contact, species, release bounds, jump/contact pummel, ownership and cancellation");
}
'''

with tempfile.TemporaryDirectory(prefix='test67-moves-') as directory:
    path = Path(directory)
    (path / 'check.c').write_text(fixture + events + production + checks)
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-function', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', '-I', str(ROOT),
                    str(path / 'check.c'), '-lm', '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)

# Real NPC query bodies must leave an in-progress caller's rig selected.
npc_source = (ROOT / 'port/linux/game/vr_npc_interaction.c').read_text()


def npc_function(name):
    match = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) +
                      r'\s*\([^;{]*\)\s*\{', npc_source, re.M)
    assert match, name
    start = match.start()
    end = npc_source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (npc_source[end] == '{') - (npc_source[end] == '}')
        end += 1
    return npc_source[start:end]


npc_fixture = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef union {float n[3];struct {float x,y,z;};}real_point3d,real_vector3d;
#define FALSE 0
#define TRUE 1
#define NPC_POOL_SIZE 3
#define VR_ARTICULATED_NODES 4
struct npc_state {int active,is_remote,held[2],node[2],started;long index;struct {struct {int count;struct {float position[3];}nodes[4];}body;}rig;};
static struct npc_state npc_pool[NPC_POOL_SIZE],*npc_current=&npc_pool[0];
#define npc (*npc_current)
static int allowed=1,enabled=1,valid=1;
static int authority(void){return allowed;}
static int feature_enabled(void){return enabled;}
static int continuable(long index){(void)index;return valid;}
static int owns(long index){npc_current=&npc_pool[1];return index==npc.index&&allowed&&enabled&&valid;}
static void surface_offset(int hand,real_vector3d *out){(void)hand;assert(npc_current==&npc_pool[1]);*out=(real_vector3d){.n={.1f,0,0}};}
static int valid_real_point3d(real_point3d const *p){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
'''
npc_checks = r'''
int main(void){
 long object=-1;short node=-1;float point[3]={0};
 npc_pool[1].active=npc_pool[1].started=npc_pool[1].held[0]=1;npc_pool[1].index=42;
 npc_pool[1].rig.body.count=3;npc_pool[1].node[0]=2;npc_pool[1].rig.body.nodes[2].position[2]=1;
 assert(vr_npc_interaction_owned(42)&&npc_current==&npc_pool[0]);
 assert(!vr_npc_interaction_owned(77)&&npc_current==&npc_pool[0]);
 struct npc_state before[NPC_POOL_SIZE];memcpy(before,npc_pool,sizeof before);
 assert(vr_npc_interaction_contact(0,&object,&node,point)&&object==42&&node==2&&point[0]==.1f&&point[2]==1);
 assert(npc_current==&npc_pool[0]&&!memcmp(before,npc_pool,sizeof before));
 npc_pool[1].is_remote=1;assert(!vr_npc_interaction_contact(0,&object,&node,point));npc_pool[1].is_remote=0;
 npc_pool[1].node[0]=3;assert(!vr_npc_interaction_contact(0,&object,&node,point));npc_pool[1].node[0]=2;
 npc_pool[1].rig.body.nodes[2].position[0]=NAN;assert(!vr_npc_interaction_contact(0,&object,&node,point));
 npc_pool[1].rig.body.nodes[2].position[0]=0;valid=0;assert(!vr_npc_interaction_contact(0,&object,&node,point));valid=1;
 allowed=0;assert(!vr_npc_interaction_contact(0,&object,&node,point));allowed=1;enabled=0;assert(!vr_npc_interaction_contact(0,&object,&node,point));enabled=1;
 assert(!vr_npc_interaction_contact(-1,&object,&node,point)&&!vr_npc_interaction_contact(2,&object,&node,point));
 assert(!vr_npc_interaction_contact(0,NULL,&node,point)&&!vr_npc_interaction_contact(0,&object,NULL,point)&&!vr_npc_interaction_contact(0,&object,&node,NULL));
 assert(npc_current==&npc_pool[0]);
 puts("PASS: production NPC ownership/contact accessors preserve active rig, exact acquired node, local authority, finite bounds and no hold mutation");
}
'''
with tempfile.TemporaryDirectory(prefix='test67-move-contact-') as directory:
    path = Path(directory)
    (path / 'check.c').write_text(npc_fixture + npc_function('vr_npc_interaction_owned') + '\n' +
                                npc_function('vr_npc_interaction_contact') + npc_checks)
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                    str(path / 'check.c'), '-lm', '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)
