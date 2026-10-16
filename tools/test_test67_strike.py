"""Execute carried fist strikes and ordinary impacts through production collision
and damage routing. Engine fixtures supply collision results; the actual wrappers,
target resolution, effect selection and side-effect ordering are compiled intact.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
units = (ROOT / 'source/units/units.c').read_text(encoding='utf-8')


def function(name):
    match = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) +
                      r'\s*\([^;{]*\)\s*\{', units, re.M)
    assert match, name
    start = match.start()
    end = units.index('{', start) + 1
    depth = 1
    while depth:
        depth += (units[end] == '{') - (units[end] == '}')
        end += 1
    return units[start:end]


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
#define FLAG(b) (1u << (b))
#define TEST_FLAG(v,b) (((v) & FLAG(b)) != 0)
#define SET_FLAG(v,b,on) ((v) = (on) ? (v) | FLAG(b) : (v) & ~FLAG(b))
#define MAXIMUM_COLLISION_USER_STACK_DEPTH 8
enum {_collision_test_for_projectiles_flags=1,_collision_result_structure=2,_collision_result_object=3};
enum {_object_type_biped=1,_object_type_weapon=2,_object_type_vehicle=3,_object_type_machine=4,_object_type_scenery=5};
enum {_collision_result_breakable_surface_bit=0,_damage_from_weapon_bit=1};
struct object_fields {real bounding_sphere_radius;real_point3d bounding_sphere_center,position;int type;long parent_object_index;int location,owner_team_index;};
struct object_datum {long definition_index;struct object_fields object;};
struct unit_datum {long definition_index;struct object_fields object;struct {int current_weapon_index;long weapon_object_indices[2],player_index;} unit;};
struct unit_definition {struct {struct {long index;} melee_damage;} unit;};
struct weapon_datum {long definition_index;};
struct weapon_definition {struct {struct {long index;} melee_attack_damage,melee_attack_response;} weapon;};
struct object_definition {struct {real acceleration_scale;} object;};
struct collision_result {int type;long object_index;real t;unsigned flags;short material_type,breakable_surface_index,node_index,region_index,material_index;long surface_index;real_point3d point;struct {real_vector3d n;} plane;};
struct damage_data {int location;long owner_object_index,owner_team_index,owner_player_index;real_point3d origin,epicenter;real_vector3d direction;short material_type;real scale,multiplier;unsigned flags;};
static struct unit_datum bodies[8];
static struct unit_definition biped_definition;
static struct weapon_datum weapon;
static struct weapon_definition weapon_definition;
static struct object_definition object_definition;
static int global_current_collision_user_depth,global_current_collision_users[MAXIMUM_COLLISION_USER_STACK_DEPTH];
static int hit_type,obstruction_type,contacts,combat_hits,sounds,vehicle_pushes,breaks,machines,responses,shares,ends;
static long hit_index,obstruction_index,last_contact;
static real units_per_metre=1;
static real_point3d eye={.n={0,0,1.6f}};
static struct unit_datum *unit_get(long id){assert(id>=0&&id<8);return &bodies[id];}
static struct object_datum *object_get(long id){return (struct object_datum *)unit_get(id);}
static struct object_datum *object_try_and_get(long id){return id>=0&&id<8?object_get(id):NULL;}
static struct unit_definition *unit_definition_get(long id){(void)id;return &biped_definition;}
static struct weapon_datum *weapon_get(long id){(void)id;return &weapon;}
static struct weapon_definition *weapon_definition_get(long id){(void)id;return &weapon_definition;}
static struct object_definition *object_definition_get(long id){(void)id;return &object_definition;}
static real vr_render_units_per_metre(void){return units_per_metre;}
static void unit_get_camera_position(long id,real_point3d *out){assert(id==0);*out=eye;}
static void vector_from_points3d(real_point3d const *a,real_point3d const *b,real_vector3d *out){for(int k=0;k<3;k++)out->n[k]=b->n[k]-a->n[k];}
static void point_from_line3d(real_point3d const *p,real_vector3d const *v,real s,real_point3d *out){for(int k=0;k<3;k++)out->n[k]=p->n[k]+s*v->n[k];}
static void scale_vector3d(real_vector3d const *v,real s,real_vector3d *out){for(int k=0;k<3;k++)out->n[k]=s*v->n[k];}
static real dot_product3d(real_vector3d const *a,real_vector3d const *b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static real normalize3d(real_vector3d *v){real n=sqrtf(v->i*v->i+v->j*v->j+v->k*v->k);if(n>0)for(int k=0;k<3;k++)v->n[k]/=n;return n;}
static int collision_test_vector(unsigned flags,real_point3d const *from,real_vector3d const *v,long owner,struct collision_result *out){
 (void)flags;(void)v;assert(owner==0);int sight=!memcmp(from,&eye,sizeof eye);
 int type=sight?obstruction_type:hit_type;if(!type)return 0;
 memset(out,0,sizeof *out);out->type=type;out->object_index=sight?obstruction_index:hit_index;
 out->t=.5f;out->point=(real_point3d){.n={.8f,0,1}};out->material_type=7;
 out->flags=FLAG(_collision_result_breakable_surface_bit);out->breakable_surface_index=3;
 return 1;
}
static long unit_unarmed_melee_damage(long unit){(void)unit;return 7;}
static long damage_globals_impact_effect(void){return 8;}
static int vr_combat_enabled(void){return 1;}
static real vr_combat_hit(long unit,long target,real_point3d const *p,real_vector3d const *d,real scale,boolean armed){assert(unit==0&&target>=0&&p&&d&&scale>0);(void)armed;combat_hits++;return 1;}
static real vr_combat_damage_share(void){shares++;return 1;}
static void vr_combat_damage_end(void){ends++;}
static void vehicle_accelerate(long target,real_vector3d const *a){(void)target;(void)a;vehicle_pushes++;}
static void damage_data_new(struct damage_data *out,long effect){assert(effect!=NONE);memset(out,0,sizeof *out);}
static void breakable_surface_damage(short surface,struct damage_data const *damage,long seed){(void)surface;(void)damage;(void)seed;breaks++;}
static void machine_try_to_open_with_damage(long target){(void)target;machines++;}
static void object_cause_contact_damage(struct damage_data *damage,long target,short node,short region,short material,real_vector3d const *normal){assert(damage->owner_object_index==0);(void)node;(void)region;(void)material;(void)normal;contacts++;last_contact=target;}
static void unit_melee_sound(long unit,short material,long effect){(void)unit;(void)material;(void)effect;sounds++;}
static void object_cause_damage(struct damage_data *damage,long unit,short node,short region,short material,real_vector3d const *normal){(void)damage;(void)unit;(void)node;(void)region;(void)material;(void)normal;responses++;}
static void reset(void){
 memset(bodies,0,sizeof bodies);for(int i=0;i<8;i++){bodies[i].object.parent_object_index=NONE;bodies[i].object.type=_object_type_biped;bodies[i].object.bounding_sphere_radius=.3f;bodies[i].object.bounding_sphere_center=(real_point3d){.n={1,0,1}};bodies[i].unit.current_weapon_index=NONE;}
 biped_definition.unit.melee_damage.index=7;object_definition.object.acceleration_scale=1;
 contacts=combat_hits=sounds=vehicle_pushes=breaks=machines=responses=shares=ends=0;
 hit_type=_collision_result_object;hit_index=1;obstruction_type=0;obstruction_index=NONE;last_contact=NONE;
 global_current_collision_user_depth=1;units_per_metre=1;
}
static void untouched(void){assert(!contacts&&!combat_hits&&!sounds&&!vehicle_pushes&&!breaks&&!machines&&!responses&&!shares&&!ends);assert(global_current_collision_user_depth==1);}
'''

checks = r'''
int main(void){
 real_vector3d direction={.n={1,0,0}},sweep={.n={.8f,0,0}};real_point3d from={.n={.2f,0,1}};
 reset();assert(unit_vr_combat_strike(0,1,&direction,1));assert(contacts==1&&last_contact==1&&combat_hits==1&&shares==1&&ends==1&&sounds==1);
 /* Another enemy, ally, player, vehicle, machine, held weapon and world
  * geometry all stop a carried blow. None acquires its damage or feedback. */
 for(int object=2;object<8;object++){
  reset();hit_index=object;bodies[object].object.type=object==4?_object_type_vehicle:object==5?_object_type_machine:object==6?_object_type_weapon:_object_type_biped;
  assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
  reset();obstruction_type=_collision_result_object;obstruction_index=object;
  assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 }
 reset();hit_type=_collision_result_structure;assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 reset();obstruction_type=_collision_result_structure;assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 reset();hit_type=0;assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 /* Parent resolution accepts an actual piece of the intended enemy, while
  * a child of another actor and another actor's weapon cannot redirect it. */
 /* (Test72: a piece is a part, not a biped: an attached biped is a rider,
  * who takes its own blow) */
 reset();hit_index=7;bodies[7].object.parent_object_index=1;bodies[7].object.type=_object_type_scenery;assert(unit_vr_combat_strike(0,1,&direction,1));assert(contacts==1&&last_contact==1);
 /* Test72: a rider (a Shade's gunner) struck through its seat is the one aimed at */
 reset();hit_index=3;bodies[3].object.type=_object_type_vehicle;bodies[7].object.parent_object_index=3;assert(unit_vr_combat_strike(0,7,&direction,1));assert(contacts==1&&last_contact==7&&!vehicle_pushes);
 reset();hit_index=7;bodies[7].object.parent_object_index=3;assert(unit_vr_combat_strike(0,7,&direction,1));assert(last_contact==7); /* hit itself: its own */
 reset();hit_index=7;bodies[7].object.parent_object_index=2;bodies[7].object.type=_object_type_scenery;assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 reset();hit_index=7;bodies[7].object.parent_object_index=1;bodies[7].object.type=_object_type_weapon;assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 reset();obstruction_type=_collision_result_object;obstruction_index=1;assert(unit_vr_combat_strike(0,1,&direction,1));assert(last_contact==1&&contacts==1);
 /* Public physical/weapon entry retains ordinary collision ownership. */
 for(int armed=0;armed<2;armed++){
  reset();hit_index=2;assert(unit_vr_impact_melee(0,&from,&sweep,1,armed,.035f));assert(last_contact==2&&contacts==1);
  reset();obstruction_type=_collision_result_object;obstruction_index=2;assert(unit_vr_impact_melee(0,&from,&sweep,1,armed,.035f));assert(last_contact==2&&contacts==1);
  reset();hit_index=3;bodies[3].object.type=_object_type_vehicle;assert(unit_vr_impact_melee(0,&from,&sweep,1,armed,.035f));assert(vehicle_pushes==1&&last_contact==3);
  reset();hit_type=_collision_result_structure;assert(unit_vr_impact_melee(0,&from,&sweep,1,armed,.035f));assert(breaks==1&&contacts==0);
 }
 reset();assert(!unit_vr_combat_strike(0,NONE,&direction,1));untouched();
 reset();assert(!unit_vr_combat_strike(0,1,NULL,1));untouched();
 reset();direction=(real_vector3d){0};assert(!unit_vr_combat_strike(0,1,&direction,1));untouched();
 puts("PASS: production carried strike targets only its acquired enemy; obstruction, parent, bystander, vehicle, wall and ordinary fist/weapon regressions");
}
'''

# (Test72: the strike split into its probes and where it is applied)
source = fixture + function('unit_vr_impact_melee_apply') + '\n' + function('unit_vr_impact_melee_target') + '\n'
source += function('unit_vr_impact_melee') + '\n'
source += function('unit_vr_combat_strike') + '\n' + checks
with tempfile.TemporaryDirectory(prefix='test67-strike-') as directory:
    path = Path(directory)
    (path / 'check.c').write_text(source, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-function', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', str(path / 'check.c'), '-lm',
                    '-o', str(path / 'check')], check=True)
    subprocess.run([str(path / 'check')], check=True)
