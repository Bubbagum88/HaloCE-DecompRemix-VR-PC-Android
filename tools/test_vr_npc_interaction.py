"""Compile production NPC ownership/root drive in isolation; verify hook order."""
from pathlib import Path
import subprocess
import re
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'port/linux/game/vr_npc_interaction.c').read_text()
header=(ROOT/'port/linux/game/vr_npc_interaction.h').read_text()
pool_match=re.search(r'^#define\s+VR_NPC_INTERACTION_POOL_SIZE\s+(\d+)\s*$',header,re.M)
assert pool_match, 'the production NPC rig pool must have a compile-time bound'
POOL_SIZE=int(pool_match.group(1))
assert POOL_SIZE==8, f'expected the requested raised pool, got {POOL_SIZE}'
def function(signature):
    match=re.search(re.escape(signature)+r'[^;{]*\{',source)
    assert match,signature
    start=match.start(); brace=source.index('{',start); depth=1; end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
out=ROOT/'build/npc-tests';out.mkdir(parents=True,exist_ok=True)
c=r'''
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#include "vr_world_math.h"
#include "vr_interaction_hold_math.h"
#include "vr_articulated.h"
#define VR_NPC_INTERACTION_POOL_SIZE {POOL_SIZE}
#define NONE -1
#define TRUE 1
#define FALSE 0
#define _game_team_player 1
#define VR_INTERACTION_NPC 5
#define _object_mask_biped 1
#define _object_dead_bit 2
#define _object_connected_to_map_bit 11
#define _object_outside_of_map_bit 21
#define _object_movie_star_bit 22
#define _object_no_collisions_bit 24
#define _unit_possessed_by_recording_bit 0
#define _unit_grenade_throw_idle 0
#define _unit_state_idle 0
#define _unit_state_land_hard 22
#define _unit_state_resurrect_front 34
#define _unit_state_resurrect_back 35
#define _weapon_state_idle 0
#define _trigger_idle 0
#define _magazine_idle 0
#define PIN(v,a,b) ((v)<(a)?(a):((v)>(b)?(b):(v)))
#define NUMBEROF(a) ((int)(sizeof(a)/sizeof(*(a))))
#define TEST_FLAG(a,b) (!!((a)&(1u<<(b))))
enum {NPC_POOL_SIZE=VR_NPC_INTERACTION_POOL_SIZE,NPC_REMOTE_PLAYERS=128};
typedef float real;
typedef union {float n[3];struct{float x,y,z;};} real_vector3d;
typedef union {float n[3];struct{float x,y,z;};} real_point3d;
typedef struct {float values[13];} real_matrix4x3;
#define MAX(a,b) ((a)>(b)?(a):(b))
static int valid_real_point3d(real_point3d const *p){return p&&isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
enum {_actor_elite,_actor_jackal,_actor_grunt,_actor_hunter,_actor_engineer,_actor_assassin,_actor_player,_actor_marine,_actor_crew,_actor_combat_form,_actor_infection_form,_actor_carrier_form,_actor_monitor,_actor_sentinel,_actor_none,_actor_mounted_weapon,NUMBER_OF_ACTOR_TYPES};
enum {_race_player=1,_race_human=2,_race_covenant=4,_race_floodcombat=8,_race_floodcarrier=16,_race_floodinfection=32,_race_sentinel=64};
enum {_actor_definition_flying_bit=21,_actor_definition_swarm_actor_bit=26,_biped_flying_bit=2};
enum {_game_connection_local=0};static int connection;static int game_connection(void){return connection;}
static struct npc_state {int active,recovery,settling,minimum_hands,started,is_remote,getting_up,species_type;float mobility;long index,tick,player;int held[2],edge[2],node[2],strain_logged[2];real_vector3d target[2],offset[2],root_anchor[2],velocity[2];struct{struct vr_articulated_body body;real_matrix4x3 captured[64];}rig;} npc_pool[NPC_POOL_SIZE],*npc_current=&npc_pool[0];
#define npc (*npc_current)
static struct remote_state {long player,candidate[2];int valid,held[2],seen[2],edge[2];real_vector3d point[2];} remote_pool[128];
static struct {long definition;short type;int valid;} species_cache[64];
static struct {long definition;int valid;} custom_rig_graph_cache[64];
static int local_edges[2]={1,1};
static struct unit_datum {long definition_index;struct{real_vector3d position,translational_velocity;unsigned long flags;unsigned short damage_flags;long parent_object_index;short name_index;}object;struct{long actor_index,player_index;unsigned long flags;int grenade_throw_state;struct{int state;}animation;short current_weapon_index;}unit;} unit;
struct actor_datum {struct{short type;int active,swarm;long definition_index;short team_index;}meta;struct{long command_list_index;int command_list_immediate;}state;};static struct actor_datum actor;
static struct actor_datum *actor_try_and_get(long index){return index==7?&actor:0;}
static int game_team_is_enemy(short our,short other){return !(our==_game_team_player&&other==2);}
static int custom_rigs,swarm_types[32],actor_races[32];
static void platform_log(char const *format,...){(void)format;}
static int config_boolean(char const *name){assert(!strcmp(name,"vr.custom_npc_rigs"));return custom_rigs;}
static short actor_type_get_race(short type){return type>=0&&type<32?actor_races[type]:0;}
static int actor_type_get_swarm(short type){return type>=0&&type<32?swarm_types[type]:1;}
struct actor_definition {unsigned long flags;short type;};static struct actor_definition actors[8];
struct biped_definition {struct{unsigned long flags;float collision_height_standing,collision_radius;short runtime_pelvis_node_index,runtime_head_node_index;}biped;};static struct biped_definition biped;
struct vr_articulated_native {struct vr_articulated_body body;};
static int graph_capture_ok=1,graph_nodes=8,graph_parent[64],graph_capture_count;
static struct biped_definition *biped_definition_get(long index){(void)index;return &biped;}
static int vr_articulated_native_capture(long index,struct vr_articulated_native *rig){(void)index;++graph_capture_count;if(!graph_capture_ok)return 0;rig->body.count=graph_nodes;for(int n=0;n<graph_nodes&&n<64;++n)rig->body.nodes[n].parent=graph_parent[n];return 1;}
struct actor_variant_definition {struct{long index;}actor_reference,unit_reference;};static struct actor_variant_definition variants[2];
struct tag_iterator {int index;};static int variant_count,tag_scans;
#define ACTOR_VARIANT_DEFINITION_TAG 1
static void tag_iterator_new(struct tag_iterator *it,long group){(void)group;it->index=0;++tag_scans;}
static long tag_iterator_next(struct tag_iterator *it){return it->index<variant_count?it->index++:NONE;}
static struct actor_variant_definition *actor_variant_definition_get(long index){return &variants[index];}
static struct actor_definition *actor_definition_get(long index){return index>=0&&index<NUMBEROF(actors)?&actors[index]:NULL;}
struct weapon_datum {struct{int state;struct{int state;}triggers[2],magazines[2];}weapon;};
static struct weapon_datum weapon;
static int weapon_valid=1,custom_animation,owner[2],lookups,recomputes,valid=1;
static void vr_interaction_release(int hand,int which){if(owner[hand]==which)owner[hand]=0;}
static void *object_try_and_get_and_verify_type(long index,int mask){(void)index;(void)mask;++lookups;return valid?&unit:0;}
static int unit_is_playing_custom_animation(long index){(void)index;return custom_animation;}
static long unit_inventory_get_weapon(long index,short slot){(void)index;(void)slot;return weapon_valid?9:NONE;}
static struct weapon_datum *weapon_try_and_get(long index){return weapon_valid&&index==9?&weapon:0;}
static void object_compute_node_matrices(long index){(void)index;++recomputes;}
static int owns(long index){return npc.active&&index==npc.index;}
static struct unit_datum *unit_get(long index){(void)index;return &unit;}
static void surface_offset(int hand,real_vector3d *offset){*offset=npc.offset[hand];}
static float interaction_units(void){return 1;}
static float global_gravity=.003f;
static int maximum=8;
static long config_integer(char const *name){(void)name;return maximum;}
static void cancel_one(void);
'''
c=c.replace('#define VR_NPC_INTERACTION_POOL_SIZE {POOL_SIZE}',
            f'#define VR_NPC_INTERACTION_POOL_SIZE {POOL_SIZE}')
for sig in ['static int species(', 'static int custom_rig_graph_valid(', 'static int custom_humanoid_rig(', 'static int interaction_profile(', 'static int npc_contact_node(', 'static struct npc_state *free_state(', 'static struct npc_state *state_for_object(', 'static int select_owner(', 'static short unit_species(', 'static struct unit_datum *eligible(', 'static void reset_one(', 'static void cancel_one(', 'void vr_npc_interaction_reset(', 'void vr_npc_interaction_cancel(', 'static void release(', 'void vr_npc_interaction_velocity(', 'int vr_npc_interaction_snapshot(', 'int vr_npc_interaction_remote_contact(']:
    c+=function(sig)+'\n'
c+=r'''
int main(void){
 assert(vr_world_hand_contact_radius(.02f,1.f)==.02f);
 assert(vr_world_hand_contact_radius(.08f,1.f)==.08f);
 assert(vr_world_hand_contact_radius(.99f,1.f)==.08f);
 assert(vr_world_authority(1,0,0));
 int hands;float mobility;
 assert(species(_actor_grunt,&hands,&mobility)&&hands==1&&mobility==.5f);
 assert(species(_actor_elite,&hands,&mobility)&&hands==2&&mobility==.25f);
 assert(species(_actor_hunter,&hands,&mobility)&&hands==2&&mobility==.12f);
 assert(species(_actor_marine,&hands,&mobility)&&hands==1);
 assert(species(_actor_crew,&hands,&mobility)&&hands==1);
 assert(!species(_actor_sentinel,&hands,&mobility)&&!species(_actor_infection_form,&hands,&mobility));
 /* A broad root/NONE collision result can still attach to a real articulated
    joint. The other hand may never pin the same joint. */
 struct vr_articulated_native contact_rig={0};contact_rig.body.count=4;
 contact_rig.body.nodes[1].position[0]=0;contact_rig.body.nodes[1].position[1]=0;contact_rig.body.nodes[1].radius=.03f;
 contact_rig.body.nodes[2].position[0]=.10f;contact_rig.body.nodes[2].position[1]=0;contact_rig.body.nodes[2].radius=.03f;
 contact_rig.body.nodes[3].position[0]=0;contact_rig.body.nodes[3].position[1]=.20f;contact_rig.body.nodes[3].radius=.03f;
 real_point3d contact={.n={.09f,.01f,0}};int mapped=0;
 assert(npc_contact_node(&contact_rig,0,&contact,1,NONE,&mapped)==2&&mapped);
 assert(npc_contact_node(&contact_rig,NONE,&contact,1,2,&mapped)==1&&mapped);
 assert(npc_contact_node(&contact_rig,3,&contact,1,NONE,&mapped)==3&&!mapped);
 assert(npc_contact_node(&contact_rig,3,&contact,1,3,&mapped)==2&&mapped);
 contact.n[0]=.6f;contact.n[1]=.6f;assert(npc_contact_node(&contact_rig,0,&contact,1,NONE,&mapped)==NONE&&!mapped);
 assert(npc_contact_node(&contact_rig,-2,&contact,1,NONE,&mapped)==NONE);
 assert(npc_contact_node(&contact_rig,99,&contact,1,NONE,&mapped)==NONE);
 actor_races[_actor_engineer]=_race_covenant;actor_races[_actor_assassin]=_race_covenant;
 actor_races[_actor_monitor]=_race_sentinel;actor_races[_actor_sentinel]=_race_sentinel;
 assert(!species(_actor_engineer,&hands,&mobility));custom_rigs=1;
 assert(!species(_actor_engineer,&hands,&mobility));
 assert(species(_actor_assassin,&hands,&mobility)&&hands==2&&mobility==.25f);
 assert(!species(_actor_monitor,&hands,&mobility));swarm_types[_actor_engineer]=1;
 assert(!species(_actor_engineer,&hands,&mobility));swarm_types[_actor_assassin]=1;
 assert(!species(_actor_assassin,&hands,&mobility));custom_rigs=0;
 /* Generic admission is separate from the preserved species table. */
 unit.definition_index=900;unit.unit.actor_index=7;actor.meta.active=1;actor.meta.swarm=0;actor.meta.definition_index=1;
 actors[1].flags=0;actor_races[_actor_none]=_race_covenant;swarm_types[_actor_none]=0;
 graph_capture_ok=1;graph_nodes=8;memset(graph_parent,0,sizeof graph_parent);
 graph_parent[0]=-1;graph_parent[1]=0;graph_parent[2]=1;graph_parent[3]=1;graph_parent[4]=1;graph_parent[5]=2;graph_parent[6]=3;graph_parent[7]=4;
 biped.biped.runtime_pelvis_node_index=1;biped.biped.runtime_head_node_index=5;
 biped.biped.collision_height_standing=1.4f;biped.biped.collision_radius=.25f;biped.biped.flags=0;
 assert(!interaction_profile(_actor_none,&unit,1,&hands,&mobility)); /* default OFF */
 custom_rigs=1;
 assert(interaction_profile(_actor_none,&unit,1,&hands,&mobility)&&hands==2&&mobility==.25f);
 connection=1;assert(!interaction_profile(_actor_none,&unit,1,&hands,&mobility));connection=0;
 int captures=graph_capture_count;
 assert(interaction_profile(_actor_none,&unit,1,&hands,&mobility)&&graph_capture_count==captures); /* definition cache */
 for(int i=0;i<3;i++) {
   actor_races[_actor_none]=(short[]){_race_human,_race_covenant,_race_floodcombat}[i];
   unit.definition_index++;memset(custom_rig_graph_cache,0,sizeof custom_rig_graph_cache);
   assert(interaction_profile(_actor_none,&unit,1,&hands,&mobility));
 }
 for(int type=0;type<NUMBER_OF_ACTOR_TYPES;type++) if(type!=_actor_none&&type!=_actor_engineer)
   assert(!custom_humanoid_rig((short)type,&unit,1,&hands,&mobility));
 assert(!custom_humanoid_rig(NUMBER_OF_ACTOR_TYPES,&unit,1,&hands,&mobility)); /* invalid enum is not clamped to _actor_none */
 actor_races[_actor_none]=_race_player;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));
 actor_races[_actor_none]=_race_sentinel;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));
 actor_races[_actor_none]=_race_floodcarrier;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));
 actor_races[_actor_none]=_race_covenant;
 actor.meta.swarm=1;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));actor.meta.swarm=0;
 swarm_types[_actor_none]=1;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));swarm_types[_actor_none]=0;
 actors[1].flags=1u<<_actor_definition_flying_bit;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));
 actors[1].flags=1u<<_actor_definition_swarm_actor_bit;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));actors[1].flags=0;
 actor.meta.active=0;assert(custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));actor.meta.active=1; /* inactive corpse profile; eligible still gates live actors */
 actor.meta.definition_index=NONE;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));actor.meta.definition_index=1;
 unit.unit.actor_index=NONE;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));unit.unit.actor_index=7;
 graph_capture_ok=0;unit.definition_index++;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));graph_capture_ok=1;
 graph_nodes=3;unit.definition_index++;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));graph_nodes=8;
 biped.biped.runtime_pelvis_node_index=8;unit.definition_index++;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));biped.biped.runtime_pelvis_node_index=1;
 graph_parent[2]=0;graph_parent[3]=0;graph_parent[4]=0;unit.definition_index++;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility)); /* no split below pelvis */
 graph_parent[2]=1;graph_parent[3]=1;graph_parent[4]=1;graph_parent[7]=99;unit.definition_index++;assert(!custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility)); /* malformed parent */
 graph_parent[7]=4;unit.definition_index++;assert(custom_humanoid_rig(_actor_none,&unit,1,&hands,&mobility));
 /* The graph proof uses authored head/pelvis markers and native biped
    flight/capsule metadata, and admits a grounded custom Engineer layout. */
 actor_races[_actor_engineer]=_race_covenant;swarm_types[_actor_engineer]=0;
 assert(custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility)&&hands==2&&mobility==.25f);
 biped.biped.runtime_head_node_index=8;unit.definition_index++;
 assert(!custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility));biped.biped.runtime_head_node_index=5;
 swarm_types[_actor_engineer]=1;unit.definition_index++;
 assert(!custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility));swarm_types[_actor_engineer]=0;
 biped.biped.flags=1u<<_biped_flying_bit;unit.definition_index++;
 assert(!custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility));biped.biped.flags=0;
 biped.biped.runtime_head_node_index=7;graph_parent[7]=0;unit.definition_index++;
 assert(!custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility)); /* head outside pelvis subtree */
 graph_parent[7]=4;biped.biped.runtime_head_node_index=5;
 biped.biped.collision_height_standing=.4f;unit.definition_index++;
 assert(!custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility)); /* invalid authored capsule */
 biped.biped.collision_height_standing=1.4f;
 actors[1].flags=1u<<_actor_definition_flying_bit;unit.definition_index++;
 assert(!custom_humanoid_rig(_actor_engineer,&unit,1,&hands,&mobility));actors[1].flags=0;
 /* Exercise the production eligibility gate itself. The prior fixture
    replaced this function with `return valid ? &unit : NULL`, which could
    pass while every live NPC was rejected. A normal connected-map Grunt
    with a live actor, idle weapon, and no script/control conflict must pass. */
 custom_rigs=0;unit.definition_index=900;unit.object.damage_flags=0;
 unit.object.parent_object_index=NONE;unit.object.name_index=NONE;
 unit.object.flags=1u<<_object_connected_to_map_bit;
 unit.unit.actor_index=7;unit.unit.player_index=NONE;unit.unit.flags=0;
 unit.unit.grenade_throw_state=_unit_grenade_throw_idle;
 unit.unit.animation.state=_unit_state_idle;unit.unit.current_weapon_index=0;
 actor.meta.type=_actor_grunt;actor.meta.active=1;actor.meta.swarm=0;
 actor.meta.definition_index=1;actor.meta.team_index=3;actor.state.command_list_index=NONE;
 actor.state.command_list_immediate=0;actors[1].flags=0;
 weapon.weapon.state=_weapon_state_idle;
 for(int n=0;n<2;n++){weapon.weapon.triggers[n].state=_trigger_idle;weapon.weapon.magazines[n].state=_magazine_idle;}
 valid=1;weapon_valid=1;custom_animation=0;
 assert(eligible(7)==&unit);
 /* Allied Marines and crew use the same contact/Grip acquisition path.
    Ordinary AI orders are preserved while their transient controls are held;
    forced immediate orders and scripted enemies remain ineligible. */
 actor.meta.type=_actor_marine;actor.meta.team_index=2;
 actor.state.command_list_index=4;assert(eligible(7)==&unit);
 actor.meta.type=_actor_crew;assert(eligible(7)==&unit);
 actor.state.command_list_immediate=1;assert(!eligible(7));
 actor.state.command_list_immediate=0;actor.meta.team_index=3;assert(!eligible(7));
 actor.state.command_list_index=NONE;actor.meta.type=_actor_grunt;actor.meta.team_index=3;
 unit.unit.player_index=3;assert(!eligible(7));unit.unit.player_index=NONE;
 unit.object.parent_object_index=55;assert(!eligible(7));unit.object.parent_object_index=NONE;
 unit.object.name_index=1;assert(!eligible(7));unit.object.name_index=NONE;
 unit.object.flags|=1u<<_object_movie_star_bit;assert(!eligible(7));unit.object.flags&=~(1u<<_object_movie_star_bit);
 unit.object.flags|=1u<<_object_no_collisions_bit;assert(!eligible(7));unit.object.flags&=~(1u<<_object_no_collisions_bit);
 unit.object.flags&=~(1u<<_object_connected_to_map_bit);assert(!eligible(7));unit.object.flags|=1u<<_object_connected_to_map_bit;
 unit.object.flags|=1u<<_object_outside_of_map_bit;assert(!eligible(7));unit.object.flags&=~(1u<<_object_outside_of_map_bit);
 unit.unit.flags|=1u<<_unit_possessed_by_recording_bit;assert(!eligible(7));unit.unit.flags&=~(1u<<_unit_possessed_by_recording_bit);
 custom_animation=1;assert(!eligible(7));custom_animation=0;
 unit.unit.grenade_throw_state=1;assert(!eligible(7));unit.unit.grenade_throw_state=_unit_grenade_throw_idle;
 unit.unit.animation.state=29;assert(!eligible(7));unit.unit.animation.state=_unit_state_idle;
 actor.meta.active=0;assert(!eligible(7));actor.meta.active=1;
 actor.state.command_list_index=0;assert(!eligible(7));actor.state.command_list_index=NONE;
 actor.state.command_list_immediate=1;assert(!eligible(7));actor.state.command_list_immediate=0;
 weapon.weapon.state=1;assert(!eligible(7));weapon.weapon.state=_weapon_state_idle;
 weapon.weapon.triggers[1].state=1;assert(!eligible(7));weapon.weapon.triggers[1].state=_trigger_idle;
 weapon.weapon.magazines[0].state=1;assert(!eligible(7));weapon.weapon.magazines[0].state=_magazine_idle;
 unit.unit.actor_index=NONE;assert(!eligible(7));unit.unit.actor_index=7;
 actor.meta.type=_actor_none;actor_races[_actor_none]=_race_covenant;custom_rigs=0;
 assert(!eligible(7));custom_rigs=1;assert(eligible(7)==&unit);custom_rigs=0;
 valid=0;assert(!eligible(7));valid=1;
 /* Keep the legacy release/throw fixture on a production-eligible live unit. */
 actor.meta.type=_actor_grunt;actor.meta.active=1;actor.state.command_list_index=NONE;
 unit.unit.actor_index=7;unit.unit.player_index=NONE;unit.unit.animation.state=_unit_state_idle;
 unit.object.parent_object_index=NONE;unit.object.name_index=NONE;
 unit.object.flags=1u<<_object_connected_to_map_bit;
 npc.active=1;npc.index=7;npc.held[0]=npc.held[1]=1;owner[0]=5;owner[1]=3;lookups=0;
 vr_npc_interaction_reset();assert(!npc.active&&owner[0]==0&&owner[1]==3&&lookups==0);
 for(int n=0;n<NUMBEROF(custom_rig_graph_cache);++n)assert(!custom_rig_graph_cache[n].valid); /* map reset clears graph proofs */
 assert(npc.edge[0]&&npc.edge[1]&&npc.index==-1);
 npc.active=1;npc.index=7;vr_npc_interaction_cancel();assert(lookups==1&&recomputes==1&&!npc.active);
 npc.active=1;npc.index=7;valid=0;vr_npc_interaction_cancel();assert(recomputes==1);valid=1;
 npc.active=1;npc.index=7;npc.started=1;npc.minimum_hands=1;npc.mobility=.5f;npc.held[0]=npc.held[1]=1;owner[0]=owner[1]=5;
 release(0,0,"test-release");assert(npc.held[1]&&!npc.recovery&&owner[0]==0&&owner[1]==5);
 release(1,0,"test-release");assert(npc.settling==1&&owner[1]==0);
 npc.held[0]=npc.held[1]=1;npc.minimum_hands=2;npc.settling=0;
 release(0,0,"test-support-release");assert(!npc.held[0]&&!npc.held[1]&&npc.settling==1);
 npc.minimum_hands=1;npc.held[0]=1;npc.rig.body.count=1;npc.velocity[0].n[0]=20;
 release(0,1,"test-grip-release");assert(unit.object.translational_velocity.n[0]>.23f&&unit.object.translational_velocity.n[0]<.25f);
 assert(npc.rig.body.nodes[0].previous[0]<-.23f);
 npc.recovery=0;npc.held[0]=1;npc.root_anchor[0].n[2]=1;npc.offset[0].n[2]=.1f;
 npc.target[0].n[2]=1.6f;unit.object.position.n[2]=0;
 float v[3]={0};vr_npc_interaction_velocity(7,v);assert(v[2]>0&&v[2]<=.2f);
 /* Moving the physical capsule to the target removes spring error; an
    already pinned visual limb does not eliminate the independent anchor. */
 float lift=v[2];unit.object.position.n[2]=.5f;memset(v,0,sizeof v);
 vr_npc_interaction_velocity(7,v);assert(v[2]<lift);
 npc.recovery=2;float before[3]={.1f,.2f,.3f};memcpy(v,before,sizeof v);
 vr_npc_interaction_velocity(7,v);assert(!memcmp(v,before,sizeof v));
 npc.recovery=0;vr_npc_interaction_velocity(8,v);assert(!memcmp(v,before,sizeof v));
 vr_npc_interaction_reset();
 for(int i=0;i<NPC_POOL_SIZE;i++){npc_pool[i].active=1;npc_pool[i].started=1;npc_pool[i].index=100+i;npc_pool[i].player=10+i;npc_pool[i].is_remote=1;npc_pool[i].held[0]=1;npc_pool[i].minimum_hands=1;npc_pool[i].rig.body.count=1;}
 assert(!select_owner(99,1,0));assert(select_owner(12,1,0)&&npc.index==102);
 assert(state_for_object(103)==&npc_pool[3]);assert(!state_for_object(999));
 npc_pool[0].held[0]=0;assert(!select_owner(99,1,0)); /* settling body remains owned */
 long id;int count;real_matrix4x3 matrices[64];int seen=0;
 for(int i=0;i<NPC_POOL_SIZE;i++){assert(vr_npc_interaction_snapshot(&id,&count,matrices,64));assert(count==1);seen|=1<<(id-100);}
 assert(seen==((1u<<NPC_POOL_SIZE)-1));assert(!vr_npc_interaction_snapshot(&id,&count,matrices,0));
 float point[3];assert(vr_npc_interaction_remote_contact(12,0,&id,point)&&id==102);
 assert(!vr_npc_interaction_remote_contact(12,1,&id,point));
 vr_npc_interaction_reset();maximum=1;assert(select_owner(99,1,0));npc.active=1;npc.player=99;npc.is_remote=1;npc.held[0]=1;
 assert(!select_owner(98,1,0));maximum=8;assert(select_owner(98,1,0));
 vr_npc_interaction_reset();unit.unit.actor_index=7;actor.meta.type=_actor_grunt;
 assert(unit_species(&unit,555)==_actor_grunt);
 unit.unit.actor_index=NONE;unit.definition_index=101;variant_count=1;
 variants[0].unit_reference.index=101;variants[0].actor_reference.index=0;actors[0].type=_actor_hunter;
 assert(unit_species(&unit,555)==_actor_hunter&&tag_scans==1);
 assert(unit_species(&unit,555)==_actor_hunter&&tag_scans==1); /* cached tag proof */
 unit.definition_index=102;variant_count=2;variants[0].unit_reference.index=variants[1].unit_reference.index=102;
 variants[1].actor_reference.index=1;actors[1].type=_actor_grunt;
 assert(unit_species(&unit,555)==NONE); /* ambiguous custom tag, never guess */
 npc.active=1;npc.index=555;npc.species_type=_actor_elite;
 assert(unit_species(&unit,555)==_actor_elite); /* alive-to-dead retains proven type */
 puts("PASS: actual NPC cancellation/stale-ID reset/exclusive claims/two-hand release/recovery/native-root anchor drive");
}
'''
path=out/'npc.c';path.write_text(c)
binary=out/'npc'
subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(ROOT/'port/linux/game'),str(path),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)

objects=(ROOT/'source/objects/objects.c').read_text()
update=objects[objects.index('boolean object_update('):objects.index('void object_compute_node_matrices_recursive(')]
assert update.index('object_compute_node_matrices(object_index)')<update.index('vr_npc_interaction_palette(object_index)')<update.index('object_update(object->object.first_child_object_index)')
units=(ROOT/'source/units/units.c').read_text()
update=units[units.index('boolean unit_update('):]
assert update.index('persistent_control_timer>0')<update.index('vr_npc_interaction_controls(unit_index)')<update.index('if (cheat.jetpack')
bipeds=(ROOT/'source/units/bipeds.c').read_text()
assert bipeds.index('vr_npc_interaction_velocity(physics->biped_index')<bipeds.index('collision_count = collision_move_pill(')
assert 'vr_controller(&buttons,triggers,thumbs)' in source
assert 'network_interaction_npc_ready()' in source
assert 'interaction_profile(unit_species(u,index)' in source
palette=function('void vr_npc_interaction_palette(')
assert '!npc.is_remote && npc.started && !npc.recovery' in palette
assert 'vr_world_interaction_weight_feedback(h,npc.mobility' in palette
assert 'node->position[k]-node->previous[k]' in palette
assert 'magnitude3d(&strain)/units' in palette
assert 'collision_model_test_pill(&model,&point,&stationary,contact_radius,&model_hit)' in source
assert 'collision_test_vector(_collision_test_for_line_of_sight_flags' in source # occlusion only, after overlap
local_tick=function('static void tick_player(')
assert 'if(!pressed || npc.held[h] || npc.recovery' in local_tick
assert local_tick.index('if(!pressed || npc.held[h]') < local_tick.index('collision_model_test_pill(')
assert 'vr_interaction_hold_target_step(npc.target[h].n,point.n,.45f*units,&limited)' in local_tick
assert 'if(magnitude3d(&delta)>0.45f*units) {release' not in local_tick
assert 'if(magnitude3d(&delta)>.65f*units) {release' not in local_tick
assert 'reason=minimum-hands-not-met' in source and '"grip-released"' in source
assert 'vr_interaction_hold_target_step' in source
helper=r'''
int main(void){float target[3]={0,0,0},desired[3]={1,0,0};int limited=0;
 assert(vr_interaction_hold_target_step(target,desired,.15f,&limited)&&limited);
 assert(fabsf(target[0]-.15f)<.00001f&&target[1]==0&&target[2]==0);
 assert(vr_interaction_hold_target_step(target,desired,.15f,&limited)&&limited);
 assert(fabsf(target[0]-.30f)<.00001f);
 desired[0]=.35f;assert(vr_interaction_hold_target_step(target,desired,.15f,&limited)&&!limited);
 assert(fabsf(target[0]-.35f)<.00001f);
 desired[0]=NAN;assert(!vr_interaction_hold_target_step(target,desired,.15f,&limited));
 puts("PASS: held contact targets follow normally and rate-limit discontinuities without detach");return 0;}
'''
hold_path=out/'hold-target.c'
hold_path.write_text('#include <assert.h>\n#include <math.h>\n#include <stdio.h>\n#include "vr_interaction_hold_math.h"\n'+helper)
hold_binary=out/'hold-target'
subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(ROOT/'port/linux/game'),str(hold_path),'-lm','-o',str(hold_binary)],check=True)
subprocess.run([str(hold_binary)],check=True)
assert '!vr_aiming()' not in source
assert 'actor_set_active(' not in source and 'meta.frozen' not in source
assert 'unit_port_resurrect(' not in source
assert 'biped_start_limp_body_physics(index)' in source
assert 'unit_interaction_recover(index,body_forward.k<0)' in source
eligible_source=function('static struct unit_datum *eligible(')
for marker in ['u->unit.player_index!=NONE','u->object.parent_object_index!=NONE','u->object.name_index!=NONE',
               '_object_movie_star_bit','_unit_possessed_by_recording_bit','unit_is_playing_custom_animation(index)',
               'u->unit.grenade_throw_state!=_unit_grenade_throw_idle','a->state.command_list_index!=NONE&&!friendly',
               'a->state.command_list_immediate']:
    assert marker in eligible_source,marker
assert 'game_team_is_enemy(_game_team_player,a->meta.team_index)' in eligible_source
custom_source=function('static int custom_humanoid_rig(')
for marker in ['_actor_none','_actor_engineer','type!=_actor_engineer',
               '_actor_definition_flying_bit','_actor_definition_swarm_actor_bit','actor->meta.swarm',
               'game_connection()!=_game_connection_local']:
    assert marker in custom_source,marker
graph_source=function('static int custom_rig_graph_valid(')
for marker in ['runtime_head_node_index','runtime_pelvis_node_index','_biped_flying_bit',
               'collision_height_standing','collision_radius','head_reaches_pelvis']:
    assert marker in graph_source,marker
remote_probe=source[source.index('static long probe_remote(real_point3d const *point,real_point3d const *camera,long player_unit,long required,int hand)\n{'):source.index('static void reset_one(')]
assert 'collision_model_test_pill(&model,point,&stationary,contact_radius,&model_hit)' in remote_probe
assert remote_probe.index('collision_model_test_pill(') < remote_probe.index('collision_test_vector(')
remote_submit=source[source.index('int vr_npc_interaction_remote(long player_index'):source.index('void vr_npc_interaction_remote_cancel(')]
assert 'probe_remote(&point,&camera,player->unit_index,required,hand)' in remote_submit
assert 'remote.candidate[hand]=selected' in remote_submit
npc_tick=function('static void tick_player(')
assert '(use_remote&&remote.candidate[h]!=it.index)' in npc_tick
network=(ROOT/'port/linux/game/network_interaction.c').read_text()
assert 'else if(r->pressed||!r->held)' in network
assert 'vr_npc_interaction_remote(r->player,hand,r->held,r->position.n)' in network
print('PASS: NPC native palette/action/capsule hook order, offline/type/focus/BSP-ID guards, no destructive AI toggle')
