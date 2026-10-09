"""Run the production parkour state/guards against bounded collision fixtures."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
production = (ROOT / "port/linux/game/vr_parkour.c").read_text()
production = re.sub(r'^#include[^\n]*\n', '', production, flags=re.M)
production = production.replace('#ifdef HALO_VR\n', '', 1)
production = production.rsplit('#endif', 1)[0]
stubs = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "port/linux/game/vr_parkour_math.h"
typedef float real;typedef int boolean;
typedef union real_point3d {float n[3];struct{float x,y,z;};} real_point3d;
typedef union real_vector3d {float n[3];struct{float i,j,k;};} real_vector3d;
typedef struct {real_vector3d n;float d;} real_plane3d;
#define NONE (-1)
#define TRUE 1
#define FALSE 0
#define TICKS_PER_SECOND 30
#define FLAG(b) (1u<<(b))
#define TEST_FLAG(v,b) (!!((v)&FLAG(b)))
enum{_collision_test_structure_bit,_collision_test_objects_bit,_collision_test_objects_scenery_bit};
enum{_collision_result_structure=1,_collision_result_object=2};
enum{_object_dead_bit,_biped_no_collision_bit,_unit_suspended_bit,_unit_control_jump_bit,_biped_airborne_bit};
enum{VR_INTERACTION_NONE,VR_INTERACTION_RELOAD,VR_INTERACTION_VEHICLE,VR_INTERACTION_WORLD,VR_INTERACTION_PARKOUR};
enum{_game_connection_local,_object_mask_scenery=8};
struct collision_result{int type;float t;real_point3d point;real_plane3d plane;long object_index;};
struct object_fields{long parent_object_index;unsigned damage_flags;real_point3d position;real_vector3d forward;};
struct object_datum{struct object_fields object;};
struct biped_datum{long definition_index;struct object_fields object;
 struct{unsigned control_flags,flags;real_vector3d throttle;}unit;struct{unsigned flags;}biped;} body;
struct biped_definition{struct{float jump_velocity;}biped;}definition={.biped={.jump_velocity=.2f}};
struct player_datum{long unit_index;}player={42};
static real_vector3d zero,*global_zero_vector3d=&zero;
static int enabled[3],network,focused=1,paused,inhibited,cinematic,grip[2],owner[2],tracked[2]={1,1},empty;
static int queries,lookups,logs;static long now;
static real_point3d hands[2]={{.n={.20f,0,1}},{.n={.20f,0,1}}};
static real_vector3d gaze={.n={0,1,0}};
static real_vector3d wall_normal={.n={1,0,0}};static float wall_offset;
static int config_boolean(char const*k){return !strcmp(k,"vr.parkour_wallrun")?enabled[0]:!strcmp(k,"vr.parkour_walljump")?enabled[1]:enabled[2];}
static float config_real(char const*k){return !strcmp(k,"vr.wallrun_duration")?1.5f:!strcmp(k,"vr.wallrun_speed")?1.25f:!strcmp(k,"vr.interaction_reach")?.25f:1;}
static float vr_world_interaction_reach(float metres,float units){if(metres<.12f)metres=.12f;if(metres>.40f)metres=.40f;return metres*units;}
static short local_player_get_next(short x){(void)x;return 0;}
static long local_player_get_player_index(short x){(void)x;return 0;}
static struct player_datum *player_get(long x){(void)x;return &player;}
static struct biped_datum *biped_try_and_get(long x){return x==42?&body:NULL;}
static struct biped_datum *biped_get(long x){assert(x==42);return &body;}
static struct biped_definition *biped_definition_get(long x){(void)x;return &definition;}
static int vr_active(void){return 1;}static int vr_aiming(void){return 1;}
static int vr_controller(unsigned*b,float*t,float*s){(void)b;(void)t;(void)s;return focused;}
static int game_connection(void){return network;}static int game_time_get_paused(void){return paused;}
static long game_time_get(void){return now;}static int cinematic_in_progress(void){return cinematic;}
static int director_inhibited_input(short x){(void)x;return inhibited;}
static float vr_units_per_metre(void){return 1;}
static void unit_get_camera_position(long x,real_point3d*p){(void)x;*p=body.object.position;p->z+=1.6f;}
static int vr_head_view(float const*p,float const*f,float*out,float*d,float*u){(void)f;memcpy(out,p,12);memcpy(d,gaze.n,12);u[0]=u[1]=0;u[2]=1;return focused;}
static int vr_hand_world(int h,float const*c,float*p,float*f,float*u){(void)c;memcpy(p,hands[h].n,12);f[0]=1;f[1]=f[2]=0;u[0]=u[1]=0;u[2]=1;return tracked[h];}
static int vr_interaction_grip(int h,int*p,int*r){(void)p;(void)r;return focused&&tracked[h]?grip[h]:0;}
static int vr_interaction_owner(int h){return owner[h];}
static int vr_interaction_claim(int h,int o){if(owner[h]&&owner[h]!=o)return 0;owner[h]=o;return 1;}
static void vr_interaction_release(int h,int o){if(owner[h]==o)owner[h]=0;}
static int vr_weapon_hand(void){return 1;}static int vr_hand_empty(void){return empty;}
static void vr_haptic(int h,float a,float t){(void)h;(void)a;(void)t;}
void platform_log(char const*f,...){(void)f;logs++;}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(real_vector3d const*v){return sqrtf(dot_product3d(v,v));}
static float normalize3d(real_vector3d*v){float n=magnitude3d(v);if(n>0)for(int i=0;i<3;i++)v->n[i]/=n;return n;}
static void scale_vector3d(real_vector3d const*v,float s,real_vector3d*out){for(int i=0;i<3;i++)out->n[i]=v->n[i]*s;}
static void add_vectors3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*out){for(int i=0;i<3;i++)out->n[i]=a->n[i]+b->n[i];}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*out){for(int i=0;i<3;i++)out->n[i]=b->n[i]-a->n[i];}
static int collision_test_vector(unsigned flags,real_point3d const*p,real_vector3d const*v,long ignore,struct collision_result*r){
 (void)flags;(void)ignore;queries++;
 float denominator=wall_normal.i*v->i+wall_normal.j*v->j+wall_normal.k*v->k;
 float distance=wall_normal.i*p->x+wall_normal.j*p->y+wall_normal.k*p->z-wall_offset;
 if(denominator>=-.000001f)return 0;
 r->t=-distance/denominator;if(r->t<0||r->t>1)return 0;
 r->type=_collision_result_structure;
 for(int i=0;i<3;i++)r->point.n[i]=p->n[i]+r->t*v->n[i];
 r->plane.n=wall_normal;
 r->object_index=0x12345678; /* poison: production BSP collision does not set this */
 return 1;
}
static struct object_datum*object_try_and_get_and_verify_type(long x,int mask){(void)x;(void)mask;lookups++;return NULL;}
'''
checks = r'''
static real_vector3d tick(float x,float y,float z){
 now++;real_vector3d velocity={.n={x,y,z}};
 vr_parkour_velocity(42,&body.object.position,1.2f,.2f,&velocity);return velocity;
}
int main(void){
 body.object.parent_object_index=NONE;body.object.position.x=.22f;body.object.forward.i=1;
 vr_parkour_reset();
 /* At the full 25 cm reach, a wall 22.5 degrees between the old world-axis
    probes is outside each cardinal ray but inside the diagonal contact ray. */
 wall_normal=(real_vector3d){.n={.9238795f,.3826834f,0}};
 real_point3d oblique_hand={.n={.25f*.9238795f,.25f*.3826834f,1}};
 struct collision_result oblique_hit;
 assert(parkour_grab_surface(42,&oblique_hand,1,&oblique_hit));
 assert(fabsf(oblique_hit.t-1.0f)<.001f);
 wall_normal=(real_vector3d){.n={1,0,0}};wall_offset=0;queries=0;
 real_vector3d v=tick(.1f,.2f,.3f);assert(v.i==.1f&&v.j==.2f&&v.k==.3f&&queries==0);
 enabled[2]=1;network=1;v=tick(.1f,.2f,.3f);assert(v.k==.3f&&queries==0);network=0;
 tick(0,0,0);grip[0]=1;v=tick(0,0,0);
 assert(parkour.hand[0].active&&owner[0]==VR_INTERACTION_PARKOUR&&lookups==0);
 assert(v.i<0&&magnitude3d(&v)<=4.0f/30.0f+.0001f);
 float anchor[3];assert(vr_parkour_hand(0,anchor)&&anchor[0]==0);
 hands[0].z-=.2f;v=tick(0,0,0);assert(v.k>0);
 grip[0]=0;v=tick(0,0,0);assert(v.k>0&&owner[0]==0&&!parkour.hand[0].active);
 tick(0,0,0);grip[0]=1;tick(0,0,0);assert(parkour.hand[0].active);
 focused=0;v=tick(.1f,.2f,.3f);assert(!parkour.hand[0].active&&owner[0]==0&&v.k==.3f);
 focused=1;tick(0,0,0);assert(!parkour.hand[0].active); /* held grip cannot re-acquire after focus loss */
 grip[0]=0;tick(0,0,0);grip[0]=1;tick(0,0,0);assert(parkour.hand[0].active);
 tracked[0]=0;v=tick(.1f,.2f,.3f);assert(!parkour.hand[0].active&&owner[0]==0&&v.k==.3f);
 tracked[0]=1;tick(0,0,0);assert(!parkour.hand[0].active); /* tracking restored while still held */
 grip[0]=0;tick(0,0,0);grip[1]=1;tick(0,0,0);assert(!parkour.hand[1].active); /* held weapon hand */
 grip[0]=1;owner[0]=VR_INTERACTION_RELOAD;tick(0,0,0);assert(!parkour.hand[0].active&&owner[0]==VR_INTERACTION_RELOAD);owner[0]=0;
 enabled[2]=0;enabled[0]=enabled[1]=1;grip[0]=grip[1]=0;vr_parkour_reset();
 body.unit.throttle.j=1;body.unit.control_flags=0;tick(0,.15f,0);
 body.unit.control_flags=FLAG(_unit_control_jump_bit);tick(0,.15f,0);
 body.biped.flags=FLAG(_biped_airborne_bit);v=tick(0,.15f,0);
 assert(parkour.running&&v.j>0); /* left strafe sign remains left */
 float initial_speed=parkour.run_speed;
 for(int i=0;i<50;i++)v=tick(0,.15f,0);
 assert(parkour.run_ticks==45&&!parkour.running&&parkour.run_speed==initial_speed);
 body.unit.control_flags=0;tick(0,.15f,0);
 body.unit.control_flags=FLAG(_unit_control_jump_bit);v=tick(0,.15f,0);
 assert(parkour.jumped_wall&&v.i>0&&v.k>0); /* bounded outward/head-directed jump */
 v=tick(0,.15f,-.01f);assert(v.k==-.01f); /* held jump cannot repeat */
 body.unit.control_flags=0;tick(0,.15f,0);body.unit.control_flags=FLAG(_unit_control_jump_bit);
 v=tick(0,.15f,-.01f);assert(v.k==-.01f); /* fresh press still exhausted on same wall */
 struct collision_result poisoned={.type=_collision_result_structure,.object_index=0x55555555};
 assert(parkour_hit_object(&poisoned)==NONE);poisoned.type=_collision_result_object;assert(parkour_hit_object(&poisoned)==0x55555555);
 assert(vr_pk_bound(NAN,1,0,2)==1);float bad[3]={INFINITY,0,0};vr_pk_cap(bad,1);assert(bad[0]==0);
 float floor[3]={0,0,1};assert(!vr_pk_vertical(floor));
 float into[3]={-1,0,0},normal[3]={1,0,0},out[3];vr_pk_leap(into,normal,1,.4f,out);assert(out[0]>0&&out[2]>=.4f);
 puts("PASS: production parkour off/network isolation, poisoned BSP objects, grip/focus ownership, climb, bounded run and jump exhaustion");
}
'''
with tempfile.TemporaryDirectory(prefix="vr-parkour-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(stubs + production + checks)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
                    "-I", str(ROOT), str(path / "check.c"), "-lm", "-o", str(path / "check")], check=True)
    subprocess.run([str(path / "check")], check=True)
