"""Test62: production contact-damage effects and campaign fist fallbacks.

Runs actual helper/selection code under ASan+UBSan. The native damage oracle
models actual shield/body outcome; visual/runtime content acceptance is separate.
"""
from pathlib import Path
import re
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
def fn(text,name):
    m=re.search(r'^(?:static )?[\w *]+\b'+re.escape(name)+r'\s*\([^;{]*\)\s*\{',text,re.M)
    assert m,name
    start=m.start();end=text.index('{',start)+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
def run(name,text):
    with tempfile.TemporaryDirectory(prefix='test62-contact-') as tmp:
        p=Path(tmp);src=p/(name+'.c');out=p/name;src.write_text(text)
        subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function',
            '-fsanitize=address,undefined','-fno-sanitize-recover=all',str(src),'-lm','-o',str(out)],check=True)
        subprocess.run([str(out)],check=True)
damage=(ROOT/'source/objects/damage.c').read_text()
units=(ROOT/'source/units/units.c').read_text()
helper=fn(damage,'object_cause_contact_damage')
assert 'tag_load' not in helper.replace('tag_loaded',''), 'no gameplay-time asset loads'
run('contact',r"""
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
typedef float real;
typedef struct {float n[3];} real_point3d,real_vector3d;
#define NONE (-1)
#define VALID_INDEX(i,n) ((i)>=0&&(i)<(n))
#define TEST_FLAG(v,b) ((v)&(1u<<(b)))
#define PROJECTILE_DEFINITION_TAG 0x70726F6A
#define _object_type_biped 1
#define _damage_create_localized_effect_bit 2
struct reference {long index;};
struct tag_block {int count;void *address;};
#define TAG_BLOCK_GET_ELEMENT(block,index,type) (&((type *)(block)->address)[index])
struct damage_data {long definition_index;float scale;unsigned flags;short material_type;real_point3d epicenter;real_vector3d direction;};
struct object_datum {long definition_index;struct{float body_vitality,shield_vitality;int type;}object;};
struct object_definition {struct{struct reference collision_model;}object;};
struct damage_resistance_material {short material_type;};
struct collision_model {struct {struct reference localized_damage_effect;struct tag_block materials;short indirect_damage_material_index;}resistance;struct tag_block nodes;};
struct projectile_material_response_definition {struct reference default_effect;};
struct projectile_definition {struct{struct tag_block material_responses;}projectile;};
static struct object_datum victim;
static struct object_definition def;
static struct collision_model model;
static struct damage_resistance_material materials[3];
static struct projectile_material_response_definition responses[8];
static struct projectile_definition bullet;
static int exists,native_calls,effect_calls,loads,definitions,models,projectiles,logs,native_localized;
static int native_delete,invulnerable;static float body_loss,shield_loss;
static long loaded,emitted;static short effect_node,seen_material,seen_region;
static real_point3d effect_position;static real_vector3d effect_direction,effect_normal;static int got_normal;
static struct object_datum *object_try_and_get(long i){return i==20&&exists?&victim:NULL;}
static struct object_definition const *object_definition_get(long i){assert(i==3);definitions++;return &def;}
static struct collision_model const *collision_model_definition_get(long i){assert(i==4);models++;return &model;}
static long tag_loaded(long group,char const*name){assert(group==PROJECTILE_DEFINITION_TAG&&!strcmp(name,"weapons\\assault rifle\\bullet"));loads++;return loaded;}
static struct projectile_definition const*projectile_definition_get(long i){assert(i==5);projectiles++;return &bullet;}
void platform_log(char const*f,...){(void)f;logs++;}
static void damage_effect_new_at_location(long effect,long object,short node,real_point3d const*p,real_vector3d const*d,real_vector3d const*n){
 assert(object==20&&exists);assert(effect!=NONE);assert(node==NONE||VALID_INDEX(node,model.nodes.count));
 effect_calls++;emitted=effect;effect_node=node;effect_position=*p;effect_direction=*d;got_normal=n!=NULL;if(n)effect_normal=*n;
}
static void object_cause_damage(struct damage_data*d,long object,short node,short region,short material,real_vector3d const*n){
 assert(object==20&&exists);(void)node;(void)n;native_calls++;seen_material=material;seen_region=region;
 if(invulnerable)return;
 victim.object.shield_vitality-=shield_loss;victim.object.body_vitality-=body_loss;
 /* Native damage can report shield as predominant material even with some
  * body damage. The fallback must still select the body's tag material. */
 d->material_type=7;
 if(body_loss>0&&(d->flags&(1u<<_damage_create_localized_effect_bit))&&model.resistance.localized_damage_effect.index!=NONE)native_localized++;
 if(native_delete)exists=0;
}
static void reset(void){
 memset(&victim,0,sizeof victim);memset(&def,0,sizeof def);memset(&model,0,sizeof model);memset(&bullet,0,sizeof bullet);
 victim.definition_index=3;victim.object.type=_object_type_biped;victim.object.body_vitality=1;victim.object.shield_vitality=1;
 def.object.collision_model.index=4;model.resistance.localized_damage_effect.index=50;
 model.resistance.materials=(struct tag_block){3,materials};model.resistance.indirect_damage_material_index=1;model.nodes.count=5;
 materials[0].material_type=2;materials[1].material_type=3;materials[2].material_type=4;
 bullet.projectile.material_responses=(struct tag_block){8,responses};for(int i=0;i<8;i++)responses[i].default_effect.index=100+i;
 exists=1;native_calls=effect_calls=loads=definitions=models=projectiles=logs=native_localized=0;
 native_delete=invulnerable=0;body_loss=.2f;shield_loss=.1f;loaded=5;emitted=NONE;effect_node=NONE;got_normal=0;
}
"""+helper+r"""
int main(void){
 struct damage_data d={.definition_index=9,.scale=.7f,.epicenter={{1,2,3}},.direction={{.1f,.2f,.3f}}};real_vector3d normal={{0,0,1}};
 reset();body_loss=0;shield_loss=1;object_cause_contact_damage(&d,20,2,1,0,&normal);
 assert(native_calls==1&&victim.object.shield_vitality==0&&effect_calls==0&&definitions==0&&loads==0); /* native shield break only */
 reset();object_cause_contact_damage(&d,20,2,1,0,&normal);
 assert(native_calls==1&&effect_calls==1&&emitted==50&&effect_node==2&&seen_material==0&&seen_region==1&&loads==0);
 assert(!memcmp(&effect_position,&d.epicenter,sizeof effect_position)&&!memcmp(&effect_direction,&d.direction,sizeof effect_direction));
 assert(got_normal&&!memcmp(&effect_normal,&normal,sizeof normal));
 reset();model.resistance.localized_damage_effect.index=NONE;object_cause_contact_damage(&d,20,2,1,0,NULL);
 assert(effect_calls==1&&emitted==102&&d.material_type==7&&got_normal==0&&loads==1&&projectiles==1); /* BODY, not shield 107 */
 reset();model.resistance.localized_damage_effect.index=NONE;object_cause_contact_damage(&d,20,99,1,-222,NULL);
 assert(emitted==103&&effect_node==NONE); /* invalid material -> authored indirect, invalid node never attached */
 reset();model.resistance.localized_damage_effect.index=NONE;object_cause_contact_damage(&d,20,-222,1,3,NULL);
 assert(emitted==103&&effect_node==NONE); /* upper-bound material rejected too */
 reset();invulnerable=1;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==1&&effect_calls==0&&definitions==0);
 reset();body_loss=0;shield_loss=0;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==1&&effect_calls==0);
 reset();body_loss=-.2f;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==1&&effect_calls==0); /* healing */
 reset();d.flags=1u<<_damage_create_localized_effect_bit;object_cause_contact_damage(&d,20,2,1,0,NULL);
 assert(native_calls==1&&native_localized==1&&effect_calls==0);d.flags=0; /* no duplicate native effect */
 reset();native_delete=1;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==1&&effect_calls==0&&definitions==0&&logs==0);
 reset();exists=0;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==0&&effect_calls==0);
 reset();object_cause_contact_damage(&d,-1,2,1,0,NULL);object_cause_contact_damage(NULL,20,2,1,0,NULL);assert(native_calls==0&&effect_calls==0);
 reset();victim.object.type=2;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==1&&effect_calls==0&&definitions==0);
 reset();def.object.collision_model.index=NONE;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(native_calls==1&&effect_calls==0&&models==0);
 reset();model.resistance.localized_damage_effect.index=NONE;loaded=NONE;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(effect_calls==0&&projectiles==0);
 reset();model.resistance.localized_damage_effect.index=NONE;responses[2].default_effect.index=NONE;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(effect_calls==0);
 reset();model.resistance.localized_damage_effect.index=NONE;model.resistance.materials.count=0;object_cause_contact_damage(&d,20,2,1,0,NULL);assert(effect_calls==0&&projectiles==0);
 reset();model.resistance.localized_damage_effect.index=NONE;model.resistance.indirect_damage_material_index=3;object_cause_contact_damage(&d,20,2,1,-1,NULL);assert(effect_calls==0&&projectiles==0);
 for(int material=-2;material<=9;material++){
  reset();model.resistance.localized_damage_effect.index=NONE;materials[0].material_type=(short)material;
  object_cause_contact_damage(&d,20,2,1,0,NULL);assert(effect_calls==(VALID_INDEX(material,8)?1:0));
 }
 reset();model.nodes.count=0;object_cause_contact_damage(&d,20,0,1,0,NULL);assert(effect_calls==1&&effect_node==NONE);
 puts("PASS: actual contact-damage helper: native shields, real-body-only authored effects, body material fallback, deletion/invulnerability/indices/no-asset guards, no duplicate effects");
}
""")
# Execute the exact production damage-selection block, so authored melee
# priority, the optional globals fallback and its scale remain testable
# without substituting fake collision or networking for the whole game.
impact=fn(units,'unit_vr_impact_melee_apply')  # (Test72: the damage is chosen where the strike is applied)
start=impact.index('\t/* Prefer the biped')
end=impact.index('\n\tif (hit_object_index != NONE && object_get',start)
selection=impact[start:end]
assert 'if (melee_damage_effect_index == NONE && !weapon_hand && vr_combat_enabled())' in selection
run('fist_fallback',r"""
#include <assert.h>
#include <math.h>
#include <stdio.h>
#define NONE (-1)
typedef int boolean;typedef float real;
typedef struct {float n[3];} real_point3d;
typedef struct {float n[3];} real_vector3d;
struct unit_datum{struct{int current_weapon_index;long weapon_object_indices[2];}unit;};
struct unit_definition{struct{struct{long index;}melee_damage;}unit;};
struct weapon_datum{long definition_index;};
struct weapon_definition{struct{struct{long index;}melee_attack_damage,melee_attack_response;}weapon;};
static struct weapon_datum weapon={7};static struct weapon_definition weapon_def;
static long unarmed,falling;static int allowed,unarmed_calls,falling_calls,combat_calls;
static float combo=1;
static struct weapon_datum*weapon_get(long i){assert(i==6);return &weapon;}
static struct weapon_definition*weapon_definition_get(long i){assert(i==7);return &weapon_def;}
static long unit_unarmed_melee_damage(long i){assert(i==1);unarmed_calls++;return unarmed;}
static long damage_globals_impact_effect(void){falling_calls++;return falling;}
static int vr_combat_enabled(void){return allowed;}
/* Test65: the swing's direction and strength go with it (the combo's knockdowns and shoves) */
static float vr_combat_hit(long unit,long target,real_point3d const*p,real_vector3d const*d,real s,int weapon_hand){assert(unit==1&&target==2&&d&&s>0);(void)p;(void)weapon_hand;combat_calls++;return combo;}
static long result,response;static float result_scale;
static void choose(struct unit_datum*unit,struct unit_definition*unit_definition,boolean weapon_hand,real scale){
 long unit_index=1,hit_object_index=2,melee_damage_effect_index=NONE,melee_response_effect_index=NONE;
 struct {real_point3d point;}collision={0};real_vector3d direction={{1,0,0}};
"""+selection+r"""
 result=melee_damage_effect_index;response=melee_response_effect_index;result_scale=scale;
}
int main(void){
 struct unit_datum unit={.unit={.current_weapon_index=NONE,.weapon_object_indices={6,NONE}}};
 struct unit_definition def={.unit={.melee_damage={.index=NONE}}};
 unarmed=NONE;falling=80;allowed=1;choose(&unit,&def,0,1.2f);assert(result==80&&fabsf(result_scale-.3f)<1e-6f&&falling_calls==1);
 allowed=0;choose(&unit,&def,0,1.2f);assert(result==NONE&&result_scale==1.2f&&falling_calls==1); /* ordinary/pvp/remote safety gate */
 allowed=1;choose(&unit,&def,1,1.2f);assert(result==NONE&&result_scale==1.2f&&falling_calls==1); /* no globals gun blow */
 unarmed=30;choose(&unit,&def,0,1.2f);assert(result==30&&result_scale==1.2f&&falling_calls==1);
 def.unit.melee_damage.index=40;choose(&unit,&def,0,1.2f);assert(result==40&&result_scale==1.2f);
 unit.unit.current_weapon_index=0;weapon_def.weapon.melee_attack_damage.index=50;weapon_def.weapon.melee_attack_response.index=51;
 choose(&unit,&def,1,1.2f);assert(result==50&&response==51&&result_scale==1.2f);
 choose(&unit,&def,0,1.2f);assert(result==40&&response==NONE&&result_scale==1.2f); /* biped fist preferred */
 def.unit.melee_damage.index=NONE;choose(&unit,&def,0,1.2f);assert(result==50&&response==51&&result_scale==1.2f);
 unit.unit.current_weapon_index=NONE;unarmed=NONE;falling=NONE;choose(&unit,&def,0,1.2f);assert(result==NONE);
 falling=80;combo=3;choose(&unit,&def,0,1.2f);assert(result==80&&fabsf(result_scale-.9f)<1e-6f);
 puts("PASS: actual fist selection block: unit/weapon/unarmed priorities preserved, opt-in empty-fist globals fallback at quarter strength, unavailable/weapon-hand gate and combo scaling");
}
""")


# The authoritative NPC restraint uses real ownership/feature/session helpers,
# not render ownership: one hand on a living heavy body is already restrained.
npc=(ROOT/'port/linux/game/vr_npc_interaction.c').read_text()
network=(ROOT/'port/linux/game/network_interaction.c').read_text()
run('npc_restraint',r"""
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define NONE (-1)
#define TRUE 1
#define FALSE 0
#define NPC_POOL_SIZE 3
typedef int boolean;
#define _game_connection_local 0
#define _game_connection_network_client 1
#define _game_connection_network_server 2
#define HALO_PORT_MAXIMUM_NETWORK_MACHINES 128
#define NUMBEROF(a) (sizeof(a)/sizeof((a)[0]))
#define NI_LEASE 3000
static int ni_host_ready=1,ni_host_npc_ready=1;
static unsigned long ni_host_seen=100;
static unsigned long system_milliseconds(void){return 100;}
struct vec {float v[3];};
struct unit_datum{struct{unsigned control_flags;float primary_trigger;struct vec throttle;}unit;};
static struct unit_datum victim;
static struct vec zero,*global_zero_vector3d=&zero;
static struct npc_state{int active,started,held[2],is_remote,death;long index;}npc_pool[NPC_POOL_SIZE],*npc_current=&npc_pool[0];
#define npc (*npc_current)
static int enabled=1,death_enabled,physical=1,connection,peers_ready=1,eligible=1,cancels,logs;
static int config_boolean(char const*k){return !strcmp(k,"vr.npc_interaction")?enabled:!strcmp(k,"vr.death_ragdolls")?death_enabled:!strcmp(k,"net.physical_interactions")?physical:0;}
static int game_connection(void){return connection;}
static int network_interaction_host_ready(void){return connection==_game_connection_network_server&&peers_ready;}
static short distributed_client_machines(long *machines,int capacity){assert(machines&&capacity==128);return 1;}
static struct unit_datum*continuable(long i){return i==7&&eligible?&victim:NULL;}
static void log_ineligible_state(long i){assert(i==7);logs++;}
static void cancel_one_reason(char const*r){assert(r);cancels++;memset(npc_current,0,sizeof(*npc_current));}
static struct unit_datum*unit_get(long i){assert(i==7);return &victim;}
static void reset(void){memset(npc_pool,0,sizeof npc_pool);npc_current=&npc_pool[0];npc.active=1;npc.index=7;enabled=physical=eligible=peers_ready=1;connection=death_enabled=cancels=logs=0;victim.unit.control_flags=17;victim.unit.primary_trigger=1;victim.unit.throttle.v[0]=1;}
"""+fn(network,'network_interaction_npc_ready')+fn(npc,'feature_enabled')+fn(npc,'authority')+fn(npc,'owns')+fn(npc,'vr_npc_interaction_owned')+fn(npc,'vr_npc_interaction_restrained')+fn(npc,'vr_npc_interaction_controls')+r"""
int main(void){
 reset();assert(!vr_npc_interaction_restrained(7));assert(!vr_npc_interaction_restrained(8));
 npc.held[0]=1;assert(vr_npc_interaction_restrained(7)&&!vr_npc_interaction_owned(7));
 vr_npc_interaction_controls(7);assert(victim.unit.control_flags==0&&victim.unit.primary_trigger==0&&victim.unit.throttle.v[0]==0);
 npc.held[0]=0;victim.unit.control_flags=17;vr_npc_interaction_controls(7);assert(!vr_npc_interaction_restrained(7)&&victim.unit.control_flags==17); /* prelift release */
 npc.held[1]=1;assert(vr_npc_interaction_restrained(7));npc.started=1;assert(vr_npc_interaction_owned(7));
 npc.held[1]=0;assert(vr_npc_interaction_restrained(7)); /* native ragdoll recovery retains its existing control suppression */
 npc.active=0;assert(!vr_npc_interaction_restrained(7)); /* completed handoff: fully native */
 reset();npc.held[0]=1;enabled=0;assert(!vr_npc_interaction_restrained(7)&&cancels==1&&!npc.active);
 reset();npc.held[0]=1;eligible=0;assert(!vr_npc_interaction_restrained(7)&&cancels==1&&logs==1);
 reset();npc.held[0]=1;connection=1;assert(network_interaction_npc_ready());
 assert(!authority()&&!vr_npc_interaction_restrained(7)&&cancels==1); /* actual ready-client branch is for requests/host poses, never simulation */
 reset();npc.started=npc.death=1;connection=1;assert(network_interaction_npc_ready()&&!authority()&&!vr_npc_interaction_owned(7)&&cancels==1);
 reset();npc.held[0]=1;npc.is_remote=1;enabled=0;connection=2;assert(vr_npc_interaction_restrained(7)); /* flat host, remote VR grip */
 physical=0;assert(!vr_npc_interaction_restrained(7)&&cancels==1);
 reset();npc.held[0]=1;npc.is_remote=1;connection=2;peers_ready=0;assert(!vr_npc_interaction_restrained(7)&&cancels==1);
 reset();npc.started=1;npc.death=1;enabled=0;death_enabled=1;assert(vr_npc_interaction_restrained(7));
 reset();npc.held[0]=1;npc_pool[1]=npc;npc_pool[0].index=8;assert(npc_current==&npc_pool[0]);
 assert(vr_npc_interaction_restrained(7)&&npc_current==&npc_pool[0]); /* nested native query cannot redirect caller rig */
 enabled=0;assert(!vr_npc_interaction_restrained(7)&&!npc_pool[1].active&&npc_current==&npc_pool[0]);
 puts("PASS: actual NPC restraint+ownership+controls: one-hand prelift, two-hand/lift recovery, release, disabled/invalid/client cancellation, actual negotiated client readiness denied simulation, remote host authority and unchanged render ownership");
}
""")
