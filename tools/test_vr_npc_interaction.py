"""Compile production NPC ownership/root drive in isolation; verify hook order."""
from pathlib import Path
import subprocess
import re
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'port/linux/game/vr_npc_interaction.c').read_text()
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
#include "vr_articulated.h"
#define NONE -1
#define TRUE 1
#define FALSE 0
#define VR_INTERACTION_NPC 5
#define _object_mask_biped 1
#define PIN(v,a,b) ((v)<(a)?(a):((v)>(b)?(b):(v)))
enum {NPC_POOL_SIZE=4,NPC_REMOTE_PLAYERS=128};
typedef float real;
typedef union {float n[3];struct{float x,y,z;};} real_vector3d;
typedef struct {float values[13];} real_matrix4x3;
enum {_actor_elite,_actor_jackal,_actor_grunt,_actor_hunter,_actor_engineer,_actor_assassin,_actor_player,_actor_marine,_actor_crew,_actor_combat_form,_actor_infection_form,_actor_carrier_form,_actor_monitor,_actor_sentinel,_actor_none};
enum {_race_player=1,_race_human=2,_race_covenant=4,_race_floodcombat=8,_race_sentinel=64};
static struct npc_state {int active,recovery,settling,minimum_hands,started,is_remote,species_type;float mobility;long index,tick,player;int held[2],edge[2],node[2];real_vector3d target[2],offset[2],root_anchor[2],velocity[2];struct{struct vr_articulated_body body;real_matrix4x3 captured[64];}rig;} npc_pool[4],*npc_current=&npc_pool[0];
#define npc (*npc_current)
static struct remote_state {long player,candidate[2];int valid,held[2],seen[2],edge[2];real_vector3d point[2];} remote_pool[128];
static struct {long definition;short type;int valid;} species_cache[64];
static int local_edges[2]={1,1};
static struct unit_datum {long definition_index;struct{real_vector3d position,translational_velocity;}object;struct{long actor_index;}unit;} unit;
struct actor_datum {struct{short type;}meta;};static struct actor_datum actor;
static struct actor_datum *actor_try_and_get(long index){return index==7?&actor:0;}
static int custom_rigs,swarm_types[32],actor_races[32];
static int config_boolean(char const *name){assert(!strcmp(name,"vr.custom_npc_rigs"));return custom_rigs;}
static short actor_type_get_race(short type){return type>=0&&type<32?actor_races[type]:0;}
static int actor_type_get_swarm(short type){return type>=0&&type<32?swarm_types[type]:1;}
struct actor_definition {short type;};static struct actor_definition actors[2];
struct actor_variant_definition {struct{long index;}actor_reference,unit_reference;};static struct actor_variant_definition variants[2];
struct tag_iterator {int index;};static int variant_count,tag_scans;
#define ACTOR_VARIANT_DEFINITION_TAG 1
static void tag_iterator_new(struct tag_iterator *it,long group){(void)group;it->index=0;++tag_scans;}
static long tag_iterator_next(struct tag_iterator *it){return it->index<variant_count?it->index++:NONE;}
static struct actor_variant_definition *actor_variant_definition_get(long index){return &variants[index];}
static struct actor_definition *actor_definition_get(long index){return &actors[index];}
static int owner[2],lookups,recomputes,valid=1;
static void vr_interaction_release(int hand,int which){if(owner[hand]==which)owner[hand]=0;}
static void *object_try_and_get_and_verify_type(long index,int mask){(void)index;(void)mask;++lookups;return valid?&unit:0;}
static void object_compute_node_matrices(long index){(void)index;++recomputes;}
static int owns(long index){return npc.active&&index==npc.index;}
static struct unit_datum *unit_get(long index){(void)index;return &unit;}
static struct unit_datum *eligible(long index){(void)index;return valid?&unit:0;}
static void surface_offset(int hand,real_vector3d *offset){*offset=npc.offset[hand];}
static float interaction_units(void){return 1;}
static float global_gravity=.003f;
static int maximum=4;
static long config_integer(char const *name){(void)name;return maximum;}
static void cancel_one(void);
'''
for sig in ['static int species(', 'static struct npc_state *free_state(', 'static struct npc_state *state_for_object(', 'static int select_owner(', 'static short unit_species(', 'static void reset_one(', 'static void cancel_one(', 'void vr_npc_interaction_reset(', 'void vr_npc_interaction_cancel(', 'static void release(', 'void vr_npc_interaction_velocity(', 'int vr_npc_interaction_snapshot(', 'int vr_npc_interaction_remote_contact(']:
    c+=function(sig)+'\n'
c+=r'''
int main(void){
 assert(vr_world_authority(1,0,0));
 int hands;float mobility;
 assert(species(_actor_grunt,&hands,&mobility)&&hands==1&&mobility==.5f);
 assert(species(_actor_elite,&hands,&mobility)&&hands==2&&mobility==.25f);
 assert(species(_actor_hunter,&hands,&mobility)&&hands==2&&mobility==.12f);
 assert(species(_actor_marine,&hands,&mobility)&&hands==1);
 assert(!species(_actor_sentinel,&hands,&mobility)&&!species(_actor_infection_form,&hands,&mobility));
 actor_races[_actor_engineer]=_race_covenant;actor_races[_actor_assassin]=_race_covenant;
 actor_races[_actor_monitor]=_race_sentinel;actor_races[_actor_sentinel]=_race_sentinel;
 assert(!species(_actor_engineer,&hands,&mobility));custom_rigs=1;
 assert(!species(_actor_engineer,&hands,&mobility));
 assert(species(_actor_assassin,&hands,&mobility)&&hands==2&&mobility==.25f);
 assert(!species(_actor_monitor,&hands,&mobility));swarm_types[_actor_engineer]=1;
 assert(!species(_actor_engineer,&hands,&mobility));swarm_types[_actor_assassin]=1;
 assert(!species(_actor_assassin,&hands,&mobility));custom_rigs=0;
 npc.active=1;npc.index=7;npc.held[0]=npc.held[1]=1;owner[0]=5;owner[1]=3;lookups=0;
 vr_npc_interaction_reset();assert(!npc.active&&owner[0]==0&&owner[1]==3&&lookups==0);
 assert(npc.edge[0]&&npc.edge[1]&&npc.index==-1);
 npc.active=1;npc.index=7;vr_npc_interaction_cancel();assert(lookups==1&&recomputes==1&&!npc.active);
 npc.active=1;npc.index=7;valid=0;vr_npc_interaction_cancel();assert(recomputes==1);valid=1;
 npc.active=1;npc.index=7;npc.started=1;npc.minimum_hands=1;npc.mobility=.5f;npc.held[0]=npc.held[1]=1;owner[0]=owner[1]=5;
 release(0,0);assert(npc.held[1]&&!npc.recovery&&owner[0]==0&&owner[1]==5);
 release(1,0);assert(npc.settling==1&&owner[1]==0);
 npc.held[0]=npc.held[1]=1;npc.minimum_hands=2;npc.settling=0;
 release(0,0);assert(!npc.held[0]&&!npc.held[1]&&npc.settling==1);
 npc.minimum_hands=1;npc.held[0]=1;npc.rig.body.count=1;npc.velocity[0].n[0]=20;
 release(0,1);assert(unit.object.translational_velocity.n[0]>.23f&&unit.object.translational_velocity.n[0]<.25f);
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
 for(int i=0;i<4;i++){npc_pool[i].active=1;npc_pool[i].started=1;npc_pool[i].index=100+i;npc_pool[i].player=10+i;npc_pool[i].is_remote=1;npc_pool[i].held[0]=1;npc_pool[i].minimum_hands=1;npc_pool[i].rig.body.count=1;}
 assert(!select_owner(99,1,0));assert(select_owner(12,1,0)&&npc.index==102);
 assert(state_for_object(103)==&npc_pool[3]);assert(!state_for_object(999));
 npc_pool[0].held[0]=0;assert(!select_owner(99,1,0)); /* settling body remains owned */
 long id;int count;real_matrix4x3 matrices[64];int seen=0;
 for(int i=0;i<4;i++){assert(vr_npc_interaction_snapshot(&id,&count,matrices,64));assert(count==1);seen|=1<<(id-100);}
 assert(seen==15);assert(!vr_npc_interaction_snapshot(&id,&count,matrices,0));
 float point[3];assert(vr_npc_interaction_remote_contact(12,0,&id,point)&&id==102);
 assert(!vr_npc_interaction_remote_contact(12,1,&id,point));
 vr_npc_interaction_reset();maximum=1;assert(select_owner(99,1,0));npc.active=1;npc.player=99;npc.is_remote=1;npc.held[0]=1;
 assert(!select_owner(98,1,0));maximum=4;assert(select_owner(98,1,0));
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
assert 'species(unit_species(u,index)' in source
assert 'hit.type!=_collision_result_object || hit.object_index!=it.index' in source
assert 'actor_set_active(' not in source and 'meta.frozen' not in source
assert 'unit_port_resurrect(' not in source
assert 'biped_start_limp_body_physics(index)' in source
assert 'unit_interaction_recover(index,body_forward.k<0)' in source
print('PASS: NPC native palette/action/capsule hook order, offline/type/focus/BSP-ID guards, no destructive AI toggle')
