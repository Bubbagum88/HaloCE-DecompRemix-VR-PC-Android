"""Execute Test62 grenade/combat production state against bounded engine fixtures."""
from pathlib import Path
import re,subprocess,tempfile
R=Path(__file__).resolve().parents[1]
source=(R/'port/linux/game/vr_extra_interaction.c').read_text()
source=re.sub(r'^#include[^\n]*\n','',source,flags=re.M).replace('#ifdef HALO_VR','',1).rsplit('#endif',1)[0]
stubs=r"""
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
typedef float real;typedef int boolean;typedef unsigned short word;
typedef union {float n[3];struct{float x,y,z;};}real_point3d;
typedef union {float n[3];struct{float i,j,k;};}real_vector3d;
typedef struct {real scale;real_vector3d forward,left,up;real_point3d position;}real_matrix4x3;
typedef struct {float alpha,red,green,blue;}real_argb_color;
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
#define _pi 3.141592653589793f
#define NUMBEROF(a) ((int)(sizeof(a)/sizeof((a)[0])))
/* (the fixture's bodies are of no kind unless a test says: 0 is none) */
enum{_actor_elite=10,_actor_jackal,_actor_grunt,_actor_hunter};
typedef struct{float i,j;}real_vector2d;
enum{_game_connection_local,_game_connection_network_client,_game_connection_network_server};
enum{_object_dead_bit,_unit_suspended_bit,_biped_airborne_bit,_biped_no_collision_bit,_unit_control_weapon_primary_trigger_bit,_unit_control_throw_grenade_bit,_unit_control_use_equipment_bit,_unit_control_jump_bit};
enum{_object_type_biped=1,_object_mask_biped=2,_collision_result_object=3,_collision_test_for_projectiles_flags=4};
enum{VR_INTERACTION_NONE,VR_INTERACTION_RELOAD,VR_INTERACTION_VEHICLE,VR_INTERACTION_WORLD,VR_INTERACTION_PARKOUR,VR_INTERACTION_NPC,VR_INTERACTION_GRENADE};
struct object_fields{long parent_object_index;unsigned damage_flags;int type,owner_team_index;real_point3d position,bounding_sphere_center;real_vector3d forward;real bounding_sphere_radius,shield_vitality;struct{long size;}node_matrices;};
struct unit_fields{long actor_index,player_index;unsigned flags,control_flags;real_vector3d throttle;real primary_trigger;char melee_attack_state;};
struct unit_datum{long definition_index;struct object_fields object;struct unit_fields unit;};
struct biped_datum{long definition_index;struct object_fields object;struct unit_fields unit;struct{unsigned flags;}biped;};
static struct biped_datum bodies[4];static real widths[4]={.2f,.3f,.3f,.3f};
struct actor_datum{struct{int active,team_index,type;}meta;}actors[4];
struct player_datum{long unit_index;}player={0};
struct object_iterator{long index;};
struct collision_result{int type;long object_index;float t;struct{real_vector3d n;float d;}plane;};
struct model_node{char name[32];short parent_node_index;};
struct model{struct{int count;struct model_node*address;}nodes;};
struct object_definition{struct{struct{long index;}model;float acceleration_scale;}object;}definition={.object={.model={0},.acceleration_scale=1}};
static struct model_node nodes[3]={{"root",-1},{"spine",0},{"head",1}};
static struct model model={.nodes={3,nodes}};
#define TAG_BLOCK_GET_ELEMENT(b,i,t) ((t*)((b)->address)+(i))
static int enabled,combat,highlights=1,host_allowed,ready,network,coop,active=1,focused=1,paused,inhibited,cinematic,empty=1,grip[2],owners[2],tracking[2]={1,1},ammo[2]={2,2},obstruction,throw_count,pulses[2],draws;
static long now;static double pose_clock=1;static double vr_pose_time(void){return pose_clock;}
static int rendered_hand;static real_point3d rendered_palm;static float collision_t=.5f;static real_vector3d collision_normal={.n={-1,0,0}};
static int vr_render_palm_point(int h,long u,float p[3]){(void)h;(void)u;if(rendered_hand)memcpy(p,rendered_palm.n,12);return rendered_hand;}
static real_vector3d zero,*global_zero_vector3d=&zero,gaze={.n={1,0,0}},last_throw;
static real_point3d hands[2];
static float combat_reach_setting=2.5f,lunge_setting=0,health_setting=1;static int counters_setting=1;
static char const *melee_mode="impact";static char const*config_string(char const*k){return !strcmp(k,"vr.melee")?melee_mode:"";}
static float melee_speed=2;static float vr_melee_speed(void){return melee_speed;}
static float config_real(char const*k){if(!strcmp(k,"vr.grenade_chest_forward"))return .16f;if(!strcmp(k,"vr.grenade_chest_down"))return .30f;if(!strcmp(k,"vr.grenade_chest_spread"))return .14f;if(!strcmp(k,"vr.combat_reach"))return combat_reach_setting;if(!strcmp(k,"vr.combat_lunge_reach"))return lunge_setting;if(!strcmp(k,"vr.combat_enemy_health"))return health_setting;return 1;}
static int config_boolean(char const*k){return !strcmp(k,"vr.physical_grenades")?enabled:!strcmp(k,"vr.assisted_combat")?combat:!strcmp(k,"vr.combat_highlights")?highlights:!strcmp(k,"net.host_vr_actions")?host_allowed:!strcmp(k,"vr.combat_counters")?counters_setting:!strcmp(k,"vr.active_ragdoll")?1:0;}
static short local_player_get_next(short p){(void)p;return 0;}
static long local_player_get_player_index(short p){(void)p;return 0;}
static struct player_datum*player_get(long p){(void)p;return &player;}
static struct unit_datum*unit_try_and_get(long u){return u>=0&&u<4?(struct unit_datum*)&bodies[u]:NULL;}
static struct unit_datum*unit_get(long u){assert(u>=0&&u<4);return (struct unit_datum*)&bodies[u];}
static struct biped_datum*biped_try_and_get(long u){return u==0?&bodies[0]:NULL;}
static struct actor_datum*actor_try_and_get(long a){return a>=0&&a<4?&actors[a]:NULL;}
static void biped_get_physics_pill(long u,real_point3d*p,real*h,real*w){assert(u>=0&&u<4);*p=bodies[u].object.position;*h=1.5f;*w=widths[u];}
static int vr_active(void){return active;}static int game_connection(void){return network;}static int network_coop_active(void){return coop;}
static int network_interaction_host_ready(void){return ready;}
static int game_time_get_paused(void){return paused;}static int cinematic_in_progress(void){return cinematic;}
static int director_inhibited_input(short x){(void)x;return inhibited;}
static int vr_controller(unsigned*b,float*t,float*s){(void)b;(void)t;(void)s;return focused;}
static long game_time_get(void){return now;}static float vr_units_per_metre(void){return 1;}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return a->i*b->i+a->j*b->j+a->k*b->k;}
static float magnitude3d(real_vector3d const*v){return sqrtf(dot_product3d(v,v));}
static float normalize3d(real_vector3d*v){float n=magnitude3d(v);if(n>0)for(int k=0;k<3;k++)v->n[k]/=n;return n;}
static void scale_vector3d(real_vector3d const*v,float s,real_vector3d*out){for(int k=0;k<3;k++)out->n[k]=v->n[k]*s;}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*out){for(int k=0;k<3;k++)out->n[k]=b->n[k]-a->n[k];}
static void point_from_line3d(real_point3d const*p,real_vector3d const*v,float s,real_point3d*out){for(int k=0;k<3;k++)out->n[k]=p->n[k]+v->n[k]*s;}
static int valid_real_point3d(real_point3d const*p){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
static int valid_real_vector3d(real_vector3d const*v){return isfinite(v->i)&&isfinite(v->j)&&isfinite(v->k);}
static void cross_product3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*out){*out=(real_vector3d){.n={a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};}
static void unit_get_camera_position(long u,real_point3d*p){*p=bodies[u].object.position;p->z+=1.6f;}
static int vr_head_view(float const*p,float const*f,float*out,float*d,float*u){(void)f;memcpy(out,p,12);memcpy(d,gaze.n,12);u[0]=u[1]=0;u[2]=1;return focused;}
/* Test65: the tick runs before the frame begins: vr_head_view refused it
 * there (frame_begun 0); the recent head is the last frame's */
static int frame_begun=1;
static int vr_head_view_recent(float const*p,float const*f,float*out,float*d,float*u){(void)f;memcpy(out,p,12);memcpy(d,gaze.n,12);u[0]=u[1]=0;u[2]=1;return focused;}
static float hand_speed=3;static float vr_hand_speed(int h){(void)h;return hand_speed;}
static int shoves;static void biped_accelerate(long u,real_vector3d const*v){(void)u;(void)v;shoves++;}
static real_vector3d up_axis={.n={0,0,1}},*global_up3d=&up_axis;
static int strikes,strike_ok=1;static long struck=NONE;
static boolean unit_vr_combat_strike(long u,long t,real_vector3d const*d,real s){(void)u;(void)d;(void)s;strikes++;struck=t;return strike_ok;}
static int knocks;static long knocked=NONE;static float knock_speed;
static int vr_npc_interaction_knock(long t,real_point3d const*p,real_vector3d const*d,real speed){(void)p;(void)d;knocks++;knocked=t;knock_speed=speed;return 1;}
static int vr_hand_pose(int h,float const*c,float*p,float*f,float*u){(void)c;memcpy(p,hands[h].n,12);f[0]=1;f[1]=f[2]=0;u[0]=u[1]=0;u[2]=1;return tracking[h];}
static int vr_interaction_grip(int h,int*p,int*r){(void)p;(void)r;return grip[h];}
static int vr_interaction_owner(int h){return owners[h];}
static int vr_interaction_claim(int h,int o){if(owners[h]&&owners[h]!=o)return 0;owners[h]=o;return 1;}
static void vr_interaction_release(int h,int o){if(owners[h]==o)owners[h]=0;}
static int vr_weapon_hand(void){return 1;}static int vr_hand_empty(void){return empty;}
static int vr_physical_melee_hand_allowed(int h){return !owners[h]&&tracking[h]&&grip[h];}
static int game_team_is_enemy(int a,int b){return a!=b;}
static long owned_npc=NONE;static int vr_npc_interaction_owned(long u){return u==owned_npc;}
static long restrained_npc=NONE;static int vr_npc_interaction_restrained(long u){return u==owned_npc||u==restrained_npc;}
static int collision_test_vector(unsigned f,real_point3d const*p,real_vector3d const*v,long u,struct collision_result*r){(void)f;(void)p;(void)v;(void)u;r->type=0;r->object_index=NONE;r->t=collision_t;r->plane.n=collision_normal;return obstruction;}
static int unit_get_grenade_count(long u,short t){(void)u;assert(t>=0&&t<2);return ammo[t];}
static int unit_vr_throw_grenade(long u,short t,real_point3d const*p,real_vector3d const*v){(void)u;(void)p;if(ammo[t]<=0)return 0;--ammo[t];++throw_count;last_throw=*v;return 1;}
static void vr_haptic(int h,float a,float t){assert(h>=0&&h<2&&a>0&&t>0);pulses[h]++;}
void platform_log(char const*f,...){(void)f;}
static void object_iterator_new(struct object_iterator*i,unsigned m,int f){(void)m;(void)f;i->index=-1;}
static struct unit_datum*object_iterator_next(struct object_iterator*i){return ++i->index<4?unit_get(i->index):NULL;}
static void render_debug_polygon(real_point3d const*p,int n,real_argb_color const*c){(void)p;(void)n;(void)c;draws++;}
static void render_debug_sphere(int b,real_point3d const*p,float r,real_argb_color const*c){(void)b;(void)p;(void)r;(void)c;draws++;}
static struct object_definition*object_definition_get(long i){(void)i;return &definition;}
static struct model*model_definition_get(long i){(void)i;return &model;}
/* Test66: an enemy's bones as drawn (NULL: none, the camera point and sphere) */
static real_matrix4x3 *node_pose;static real_matrix4x3*object_get_node_matrices(long i){(void)i;return node_pose;}
static int swings;static long swinger=NONE;
static boolean unit_melee_attack_begin(long u,boolean c,real_vector2d const*a){(void)c;(void)a;swings++;swinger=u;return 1;}
static int difficulty=1,guard_sounds;
static int game_difficulty_level_get(void){return difficulty;}
static void unit_vr_guard_feedback(long unit,boolean parry){(void)unit;(void)parry;guard_sounds++;}
int vr_combat_stunned(long unit);
"""
extra_stubs=r"""
/* Test63: the chest frame (vr_frame.c's vr_torso_place): from the eyes along
 * the level gaze; x right, y up, z back. The drawn camera: none, so the tick
 * uses the unit's camera. Grenade models: none in this fixture (shells). */
static int vr_torso_place(const float o[3],const float c[3],float out[3]){
 real_vector3d f=gaze;f.k=0;if(normalize3d(&f)<.0001f)return 0;
 real_vector3d right={.n={f.j,-f.i,0}};
 for(int k=0;k<3;k++)out[k]=c[k]+right.n[k]*o[0]+(k==2?o[1]:0)-f.n[k]*o[2];
 return focused;}
static int vr_render_drawn_camera(float p[3]){(void)p;return 0;}
struct game_globals_grenade{struct{long index;}projectile;};
struct game_globals{struct{int count;struct game_globals_grenade*address;}grenades;};
static struct game_globals no_grenade_globals={.grenades={0,NULL}};
static struct game_globals*scenario_get_game_globals(void){return &no_grenade_globals;}
struct render_lighting{int unused;};
#define NUMBER_OF_OBJECT_CHANGE_COLORS 4
#define NUMBER_OF_OUTGOING_OBJECT_FUNCTIONS 4
typedef struct{float red,green,blue;}real_rgb_color;
static struct{int frustum;}render;
#define VR_RENDER_EYE() 1
static void model_get_node_matrices(struct model const*m,real_matrix4x3*out,real_point3d const*o,real_vector3d const*f,real_vector3d const*u){(void)m;(void)out;(void)o;(void)f;(void)u;}
static struct render_lighting*object_get_cached_render_lighting(long u,float d){(void)u;(void)d;return NULL;}
static float render_frustum_sphere_diameter_in_pixels(int const*f,real_point3d const*p,float r){(void)f;(void)p;return r;}
static void render_model(long m,float px,real_matrix4x3 const*n,char const*r,void const*c,float const*fv,struct render_lighting const*l,real_point3d const*ce,float ra,void const*e,long id,short perm,unsigned fl){(void)m;(void)px;(void)n;(void)r;(void)c;(void)fv;(void)l;(void)ce;(void)ra;(void)e;(void)id;(void)perm;(void)fl;draws++;}
"""
checks=r"""
static void setup(void){
 difficulty=1;guard_sounds=0;hand_speed=3;
 memset(bodies,0,sizeof bodies);memset(actors,0,sizeof actors);memset(owners,0,sizeof owners);memset(grip,0,sizeof grip);
 for(int i=0;i<4;i++){bodies[i].object.parent_object_index=NONE;bodies[i].object.type=_object_type_biped;bodies[i].unit.player_index=NONE;bodies[i].unit.actor_index=i;bodies[i].object.forward.i=1;bodies[i].object.bounding_sphere_radius=.3f;bodies[i].object.node_matrices.size=3*sizeof(real_matrix4x3);actors[i].meta.active=1;actors[i].meta.team_index=i?1:0;}
 bodies[0].unit.player_index=0;bodies[0].unit.actor_index=NONE;
 bodies[1].object.position.x=1.2f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={1.2f,0,1.2f}};
 bodies[2].object.position.x=1.3f;bodies[2].object.bounding_sphere_center=(real_point3d){.n={1.3f,0,1.2f}};
 bodies[3].object.damage_flags=FLAG(_object_dead_bit);
 network=coop=host_allowed=ready=obstruction=paused=inhibited=cinematic=0;focused=active=empty=1;tracking[0]=tracking[1]=1;
 owned_npc=restrained_npc=NONE;now=10;enabled=1;combat=0;melee_speed=2;melee_mode="impact";widths[0]=.2f;widths[1]=widths[2]=widths[3]=.3f;ammo[0]=ammo[1]=2;throw_count=0;gaze=(real_vector3d){.n={1,0,0}};
 hands[0]=(real_point3d){.n={.13f,.14f,1.3f}};hands[1]=(real_point3d){.n={.13f,-.14f,1.3f}};
 vr_extra_reset();vr_extra_tick(0);
}
static void tick(void){++now;pose_clock+=1.0/30;vr_extra_tick(0);}
int main(void){
 setup();assert(!vr_extra_feedback_active(0)&&!vr_extra_feedback_active(1));grip[0]=1;tick();
 assert(vr_extra_feedback_active(0)&&!vr_extra_feedback_active(1));
 pose_clock+=.041;assert(!vr_extra_feedback_active(0));grip[0]=0;tick();assert(vr_extra_feedback_active(0));
 pose_clock+=.066;assert(!vr_extra_feedback_active(0));
 extra_pulse(1,.7f,.06f);assert(vr_extra_feedback_active(1));pose_clock-=.1;assert(!vr_extra_feedback_active(1));
 pose_clock=NAN;assert(!vr_extra_feedback_active(0)&&!vr_extra_feedback_active(1));
 assert(!vr_extra_feedback_active(-1)&&!vr_extra_feedback_active(2));vr_extra_reset();pose_clock=1;assert(!vr_extra_feedback_active(1));
 setup();real_point3d view={.n={0,0,0}},draw;
 hands[0]=(real_point3d){.n={.97f,0,0}};assert(extra_grenade_draw_point(0,0,&view,&draw)&&fabsf(draw.x-1)<1e-6f);
 obstruction=1;collision_t=.5f;assert(extra_grenade_draw_point(0,0,&view,&draw)&&fabsf(draw.x-.475f)<1e-6f);
 collision_t=.02f;assert(extra_grenade_draw_point(0,0,&view,&draw)&&draw.x==0);
 collision_t=NAN;assert(!extra_grenade_draw_point(0,0,&view,&draw));collision_t=.5f;collision_normal.i=0;assert(!extra_grenade_draw_point(0,0,&view,&draw));
 rendered_hand=1;rendered_palm=(real_point3d){.n={.25f,.1f,.05f}};
 assert(extra_grenade_draw_point(0,1,&view,&draw)&&!memcmp(&draw,&rendered_palm,sizeof draw)); // final blended/collision-adjusted pose wins over raw tracking
 rendered_hand=0;tracking[0]=0;assert(!extra_grenade_draw_point(0,0,&view,&draw));tracking[0]=1;hands[0].x=NAN;assert(!extra_grenade_draw_point(0,0,&view,&draw));
 setup();grip[0]=1;tick();assert(extra.hand[0].held&&owners[0]==VR_INTERACTION_GRENADE&&ammo[0]==2);
 hands[0].x+=.1f;tick();hands[0].x+=.1f;grip[0]=0;tick();assert(throw_count==1&&ammo[0]==1&&fabsf(last_throw.i-.1f)<1e-5f);
 assert(vr_physical_grenade_busy()); // one release tick suppresses simultaneous native button throw
 tick();assert(throw_count==1&&!owners[0]&&!vr_physical_grenade_busy());
 setup();grip[0]=1;tick();owners[0]=VR_INTERACTION_NONE;grip[0]=0;tick(); // runtime cleared claim (menu/recenter)
 assert(!extra.hand[0].held&&!throw_count&&ammo[0]==2&&!owners[0]);
 setup();grip[0]=1;tick();owners[0]=VR_INTERACTION_NONE;tick(); // still squeezed after recenter: no automatic re-grab
 assert(!extra.hand[0].held&&!throw_count&&ammo[0]==2&&!owners[0]);
 tick();assert(!extra.hand[0].held);grip[0]=0;tick();grip[0]=1;tick();assert(extra.hand[0].held);
 setup();owners[0]=VR_INTERACTION_RELOAD;grip[0]=1;tick();assert(!extra.hand[0].held&&owners[0]==VR_INTERACTION_RELOAD);
 setup();grip[0]=1;tick();tracking[0]=0;tick();assert(!extra.hand[0].held&&ammo[0]==2&&!throw_count&&!owners[0]);
 setup();grip[0]=1;tick();cinematic=1;tick();assert(!extra.hand[0].held&&ammo[0]==2);
 setup();grip[0]=1;tick();hands[0].x+=1;grip[0]=0;tick();assert(!throw_count&&ammo[0]==2);
 setup();ammo[0]=1;hands[1]=hands[0];grip[0]=grip[1]=1;tick();assert(extra.hand[0].held&&!extra.hand[1].held);
 for(int net=1;net<=2;net++){setup();network=net;coop=1;grip[0]=1;tick();assert(!extra.hand[0].held);}
 setup();network=2;coop=host_allowed=ready=1;tick();grip[0]=1;tick();assert(extra.hand[0].held);ready=0;tick();assert(!extra.hand[0].held&&ammo[0]==2);
 setup();combat=1;enabled=0;grip[0]=1;tick();real_point3d p={.n={.3f,0,1.2f}};real_vector3d punch={.n={.2f,0,0}};
 obstruction=1;vr_combat_punch(0,0,&p,&punch);assert(extra.target==NONE);obstruction=0;
 actors[1].meta.team_index=actors[2].meta.team_index=0;vr_combat_punch(0,0,&p,&punch);assert(extra.target==NONE);
 actors[1].meta.team_index=actors[2].meta.team_index=1;vr_combat_punch(0,0,&p,&punch);assert(extra.target==1);
 bodies[2].object.bounding_sphere_center.x=.7f;vr_combat_punch(0,0,&p,&punch);assert(extra.target==1);
 real_vector3d velocity={.n={0,0,-.03f}};bodies[1].object.bounding_sphere_radius=3; // visual bounds must not keep a tall actor out of reach
 vr_combat_velocity(0,&bodies[0].object.position,&velocity);assert(velocity.i>0&&velocity.i<=10.0f/30+1e-6f&&velocity.k==-.03f); /* Test65: a dash up to 10 m/s */
 widths[1]=1.1f;velocity.i=0;vr_combat_velocity(0,&bodies[0].object.position,&velocity);assert(velocity.i==0&&extra.approach_until==0); // native collision width still keeps clearance
 widths[1]=.3f;extra.approach_until=0;vr_combat_punch(0,0,&p,&punch);widths[1]=NAN;vr_combat_velocity(0,&bodies[0].object.position,&velocity);assert(extra.approach_until==0);widths[1]=.3f;
 real_point3d hit;unit_get_camera_position(1,&hit);assert(vr_combat_hit(0,1,&hit,NULL,1.0f,0)==1&&extra.stun_until==now+27);
 /* The real predicate gates both control and native animation callbacks. */
 assert(vr_combat_stunned(1)&&!vr_combat_stunned(0)&&!vr_combat_stunned(2));
 bodies[1].unit.control_flags=~0u;bodies[1].unit.primary_trigger=1;bodies[1].unit.throttle.i=1;
 vr_combat_controls(1);assert(bodies[1].unit.throttle.i==0&&bodies[1].unit.primary_trigger==0);
 {long saved_now=now;now=extra.stun_until;assert(!vr_combat_stunned(1));now=saved_now-1;assert(!vr_combat_stunned(1));now=saved_now+2;assert(!vr_combat_stunned(1));now=saved_now;}
 owned_npc=1;assert(!vr_combat_stunned(1));owned_npc=NONE;
 restrained_npc=1;assert(!vr_npc_interaction_owned(1)&&!vr_combat_stunned(1));restrained_npc=NONE;assert(vr_combat_stunned(1)); /* prelift held actor belongs to NPC restraint, not fist stun */
 bodies[1].unit.player_index=4;assert(!vr_combat_stunned(1));bodies[1].unit.player_index=NONE;
 bodies[1].object.damage_flags=FLAG(_object_dead_bit);assert(!vr_combat_stunned(1));bodies[1].object.damage_flags=0;
 actors[1].meta.team_index=0;assert(!vr_combat_stunned(1));actors[1].meta.team_index=1;
 combat=0;assert(!vr_combat_stunned(1));combat=1;
 focused=0;assert(!vr_combat_stunned(1));focused=1;
 network=_game_connection_network_client;assert(!vr_combat_stunned(1));network=_game_connection_local;
 real_matrix4x3 stock[3]={0};for(int k=0;k<3;k++){stock[k].scale=1;stock[k].forward.i=stock[k].left.j=stock[k].up.k=1;stock[k].position.z=k*.5f;}
 real_matrix4x3 saved[3];memcpy(saved,stock,sizeof stock);real_matrix4x3 *posed=vr_combat_render(1,stock);assert(posed!=stock&&!memcmp(saved,stock,sizeof stock));
 real_vector3d gap;vector_from_points3d(&posed[1].position,&posed[2].position,&gap);assert(fabsf(magnitude3d(&gap)-.5f)<1e-5f);
 assert(vr_combat_hit(0,1,&hit,NULL,1.0f,0)==1&&vr_combat_damage_share()==6);assert(vr_combat_hit(0,0,&hit,NULL,1.0f,0)==1&&vr_combat_damage_share()==1); // behind enemy: a takedown (x6, Test66: as the multiplier); the player never valid
 now+=60;assert(vr_combat_render(1,stock)==stock);
 setup();combat=1;enabled=0;grip[0]=1;tick();vr_combat_punch(0,0,&p,&punch);gaze.i=-1;tick();assert(extra.target==NONE);
 setup();combat=1;enabled=0;grip[0]=1;tick();melee_speed=0;assert(!vr_combat_enabled());
 vr_combat_punch(0,0,&p,&punch);assert(extra.target==NONE);melee_speed=NAN;assert(!vr_combat_enabled());
 melee_speed=2;melee_mode="swing";assert(!vr_combat_enabled());vr_combat_punch(0,0,&p,&punch);assert(extra.target==NONE);
 melee_mode="off";assert(!vr_combat_enabled());melee_mode="invalid";assert(!vr_combat_enabled());
 melee_mode="impact";assert(vr_combat_enabled());vr_combat_punch(0,0,&p,&punch);assert(extra.target!=NONE);
 melee_speed=0;tick();assert(extra.target==NONE&&extra.stun_until==0&&extra.approach_until==0);
 for(int gate=0;gate<3;gate++){
  setup();combat=1;grip[0]=1;tick();assert(extra.hand[0].held);
  if(gate==0)bodies[0].biped.flags|=FLAG(_biped_no_collision_bit);
  else if(gate==1)bodies[0].unit.flags|=FLAG(_unit_suspended_bit);
  else player.unit_index=1; /* fixture permits only owner 0 as a biped */
  assert(!vr_combat_enabled());tick();assert(!extra.hand[0].held&&ammo[0]==2&&!throw_count&&extra.target==NONE);
  player.unit_index=0;
 }
 /* Test63: the grenade is taken at the palm drawn on screen, within 12 cm of
  * the slot (the owner's hand closed on the slot and never took it); a
  * squeeze 15 cm off does not take it */
 setup();rendered_hand=1;rendered_palm=(real_point3d){.n={.16f,.14f+.10f,1.3f}};hands[0]=(real_point3d){.n={5,5,5}};
 grip[0]=1;tick();assert(extra.hand[0].held&&extra.hand[0].type==0);
 setup();rendered_hand=1;rendered_palm=(real_point3d){.n={.16f,.14f+.15f,1.3f}};hands[0]=(real_point3d){.n={5,5,5}};
 grip[0]=1;tick();assert(!extra.hand[0].held&&!owners[0]);rendered_hand=0;
 /* the slots follow the chest frame: turning the gaze moves them with it
  * (the frame itself only turns past 35 degrees: vr_frame.c, test_test63) */
 setup();gaze=(real_vector3d){.n={0,1,0}};hands[0]=(real_point3d){.n={-.14f,.16f,1.3f}};grip[0]=1;tick();assert(extra.hand[0].held);
 /* Test63: a punch picks an enemy up to FIST REACH (2.5 m) away within ~45
  * degrees of the gaze and starts the step; 3 m away nothing (and the
  * reason is logged); a hook (the punch's line across the target) counts */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 bodies[1].object.position.x=2.0f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={2.0f,0,1.2f}};
 bodies[2].object.position.x=3.4f;bodies[2].object.bounding_sphere_center=(real_point3d){.n={3.4f,0,1.2f}};
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d hook={.n={0,.2f,0}};
  vr_combat_punch(0,0,&fist,&hook);assert(extra.target==1&&extra.approach_until>now&&extra.hold_until>extra.approach_until);
  /* a hand that grabs ends the step and the hold */
  owners[0]=VR_INTERACTION_NPC;tick();assert(extra.approach_until==0&&extra.hold_until==0);owners[0]=0;
  extra.target=NONE;bodies[1].object.position.x=3.2f;bodies[1].object.bounding_sphere_center.x=3.2f;
  vr_combat_punch(0,0,&fist,&hook);assert(extra.target==NONE);
  /* a punch back, away from the target, takes nothing */
  bodies[1].object.position.x=1.2f;bodies[1].object.bounding_sphere_center.x=1.2f;
  real_vector3d back={.n={-.2f,0,0}};vr_combat_punch(0,0,&fist,&back);assert(extra.target==NONE);}
 /* the target is slowed, not frozen, while the step closes */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};
  bodies[1].object.position.x=2.0f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={2.0f,0,1.2f}};
  vr_combat_punch(0,0,&fist,&jab);assert(extra.target==2); /* the nearer, more central one */
  real_vector3d walk={.n={.1f,.1f,0}};vr_combat_velocity(2,&bodies[2].object.position,&walk);
  assert(fabsf(walk.i-.035f)<1e-6f&&fabsf(walk.j-.035f)<1e-6f);}
 /* Test65: Arkham Shadow's fist combat.
  * 1. the head as the last frame tracked it: a tick before this frame's
  *    vr_aim still acquires (Test63 never did) */
 setup();combat=1;enabled=0;grip[0]=1;tick();frame_begun=0;
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};
  vr_combat_punch(0,0,&fist,&jab);assert(extra.target!=NONE);}
 frame_begun=1;
 /* 2. LUNGE: an enemy 5 m off, punched at, is dashed to; the blow lands on
  *    arrival (unit_vr_combat_strike), not before */
 setup();combat=1;enabled=0;lunge_setting=6;grip[0]=1;tick();
 bodies[2].object.position.x=9;bodies[2].object.bounding_sphere_center=(real_point3d){.n={9,0,1.2f}};
 bodies[1].object.position.x=5;bodies[1].object.bounding_sphere_center=(real_point3d){.n={5,0,1.2f}};
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};int before=strikes;
  vr_combat_punch(0,0,&fist,&jab);assert(extra.target==1&&extra.strike_pending&&extra.approach_until>now+5);
  tick();assert(strikes==before&&extra.strike_pending);
  bodies[0].object.position.x=4.3f;tick();assert(strikes==before+1&&struck==1&&!extra.strike_pending);}
 /* a lunge that never arrives gives its blow up a second on */
 setup();combat=1;enabled=0;lunge_setting=6;grip[0]=1;tick();
 bodies[1].object.position.x=5;bodies[1].object.bounding_sphere_center=(real_point3d){.n={5,0,1.2f}};
 bodies[2].object.position.x=9;bodies[2].object.bounding_sphere_center=(real_point3d){.n={9,0,1.2f}};
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};int before=strikes;
  vr_combat_punch(0,0,&fist,&jab);for(int t=0;t<32;t++)tick();assert(strikes==before&&!extra.strike_pending);}
 lunge_setting=0;
 /* 3. COUNTERS: an enemy's swing opens a window; a punch toward it counters:
  *    its swing is undone (stunned), the blow lands at once in reach */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};
 vr_combat_note_melee(1);assert(extra.counter_enemy==1&&extra.counter_until>now);
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};int before=strikes;
  bodies[1].object.position.x=.6f;bodies[1].object.bounding_sphere_center.x=.6f;
  vr_combat_punch(0,0,&fist,&jab);assert(extra.countered==1&&vr_combat_stunned(1)&&extra.strike_pending);
  tick();assert(strikes==before+1&&struck==1);}
 /* an enemy facing away, or the counters off, opens nothing */
 setup();combat=1;enabled=0;grip[0]=1;tick();bodies[1].object.forward=(real_vector3d){.n={1,0,0}};
 vr_combat_note_melee(1);assert(extra.counter_enemy==NONE);
 bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};counters_setting=0;vr_combat_note_melee(1);assert(extra.counter_enemy==NONE);counters_setting=1;
 /* 4. the combo meter: a hit in a row each, within two seconds; ENEMY
  *    HEALTH divides a fist's blow; a full meter's hard punch is a takedown
  *    (x6) and knocks the enemy down (vr_npc_interaction_knock, next tick);
  *    a hit taken breaks the meter */
 setup();combat=1;enabled=0;grip[0]=1;tick();health_setting=3;
 {real_point3d body_hit={.n={1.2f,0,.8f}};float blow;int before=knocks;
  for(int i=1;i<=7;i++){blow=vr_combat_hit(0,1,&body_hit,NULL,.9f,0);assert(extra.combo==i&&blow==1);
   blow=vr_combat_damage_share();assert(fabsf(blow-(1+.08f*(i-1))/3.0f)<1e-5f);assert(vr_combat_damage_share()==1); /* once */extra.stun_until=0;extra.hit_count=0;tick();tick();tick();}
  blow=vr_combat_hit(0,1,&body_hit,NULL,.9f,0);assert(extra.combo==8);tick();tick();tick();extra.stun_until=0;extra.hit_count=0;
  blow=vr_combat_hit(0,1,&body_hit,NULL,1.2f,0);assert(blow==1&&vr_combat_damage_share()==6&&extra.combo==0&&extra.knock_pending);
  tick();assert(knocks==before+1&&knocked==1&&knock_speed==6);
  tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.9f,0);tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.9f,0);assert(extra.combo==2);
  vr_combat_note_damage(1);assert(extra.combo==2);vr_combat_note_damage(0);assert(extra.combo==0);
  /* the meter runs out two seconds after the last hit */
  tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.9f,0);assert(extra.combo==1);for(int t=0;t<61;t++)tick();assert(extra.combo==0);}
 health_setting=1;
 /* Test66 1. ENEMY HEALTH as the damage multiplier (6X: a sixth of a blow;
  * the swing's scale untouched), and only for the tick of that blow */
 setup();combat=1;enabled=0;grip[0]=1;tick();health_setting=6;
 {real_point3d body_hit={.n={1.2f,0,.8f}};
  assert(vr_combat_hit(0,1,&body_hit,NULL,.8f,0)==1);tick();assert(vr_combat_damage_share()==1); /* a tick on: spent */
  tick();tick();extra.stun_until=0;assert(vr_combat_hit(0,1,&body_hit,NULL,.8f,0)==1);
  assert(fabsf(vr_combat_damage_share()-(1+.08f)/6.0f)<1e-5f);}
 health_setting=1;
 /* 2. kinds: a Grunt staggers in two blows, an Elite in four, a Hunter
  *    never; a Hunter's front takes 40%, its back 160%; a Jackal's shield
  *    45% in front, all of it once staggered */
 {real_point3d body_hit={.n={1.2f,0,.8f}};
  setup();combat=1;enabled=0;grip[0]=1;tick();actors[1].meta.type=_actor_grunt;
  vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(!extra.stun_until);tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(extra.stun_until>now);
  setup();combat=1;enabled=0;grip[0]=1;tick();actors[1].meta.type=_actor_elite;bodies[1].object.shield_vitality=1;
  for(int i=0;i<3;i++){vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(!extra.stun_until);for(int t=0;t<8;t++)tick();}
  vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(extra.stun_until>now);
  setup();combat=1;enabled=0;grip[0]=1;tick();actors[1].meta.type=_actor_hunter;bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};
  for(int i=0;i<6;i++){vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(!extra.stun_until&&fabsf(vr_combat_damage_share()-.40f*(1+.08f*(real)i))<1e-4f);tick();tick();tick();}
  bodies[1].object.forward=(real_vector3d){.n={1,0,0}};vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(vr_combat_damage_share()>1.5f);
  assert(!extra.knock_pending); /* never knocked down */
  setup();combat=1;enabled=0;grip[0]=1;tick();actors[1].meta.type=_actor_jackal;bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};
  vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(fabsf(vr_combat_damage_share()-.45f)<1e-4f);
  tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.8f,0);vr_combat_damage_share();assert(extra.stun_until>now);
  tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.8f,0);assert(vr_combat_damage_share()>.9f);}
 /* 3. an Elite struck twice in a second and a half answers with its own
  *    swing a fifth of a second on (native unit_melee_attack_begin) */
 setup();combat=1;enabled=0;grip[0]=1;tick();actors[1].meta.type=_actor_elite;bodies[1].object.shield_vitality=1;
 {real_point3d body_hit={.n={1.2f,0,.8f}};int before=swings;
  vr_combat_hit(0,1,&body_hit,NULL,.8f,0);tick();tick();tick();vr_combat_hit(0,1,&body_hit,NULL,.8f,0);
  for(int t=0;t<6;t++){tick();assert(swings==before);}tick();assert(swings==before+1&&swinger==1);}
 /* 4. BLOCK: an enemy's swing meets a hand held up between the face and it:
  *    most of the blow stopped, the guard tiring blow on blow, never all */
 setup();combat=1;enabled=0;grip[0]=1;tick();hand_speed=.5f;
 bodies[1].object.position.x=.6f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={.6f,0,1.2f}};bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};
 assert(vr_combat_defend(0,1)==1); /* not swinging: nothing to block */
 vr_combat_note_melee(1);bodies[1].unit.melee_attack_state=1;tick();
 assert(vr_combat_defend(0,1)==1); /* hands down: the whole blow */
 hands[0]=(real_point3d){.n={.3f,0,1.45f}};
 {float first=vr_combat_defend(0,1),second=vr_combat_defend(0,1);
  assert(fabsf(first-.35f)<1e-5f&&second>first&&second<1);
  for(int i=0;i<8;i++)second=vr_combat_defend(0,1);assert(fabsf(second-.83f)<1e-5f);}
 combat=0;assert(vr_combat_defend(0,1)==1);combat=1;
 assert(vr_combat_defend(1,0)==1); /* the enemy is never defended */
 /* 5. PARRY: a hand swiped hard while the swing comes: none of the blow,
  *    the attacker staggered and open (a rear takedown, a grab) */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 bodies[1].object.position.x=.6f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={.6f,0,1.2f}};bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};
 vr_combat_note_melee(1);bodies[1].unit.melee_attack_state=1;hands[0]=(real_point3d){.n={.4f,.1f,1.3f}};hand_speed=4;tick();
 assert(vr_combat_defend(0,1)==0&&extra.countered==1&&vr_combat_stunned(1)&&extra.target==1&&extra.stun_until>now);
 /* a swipe long before the blow is no parry */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 bodies[1].object.position.x=.6f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={.6f,0,1.2f}};bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};
 vr_combat_note_melee(1);bodies[1].unit.melee_attack_state=1;hands[0]=(real_point3d){.n={.4f,.1f,1.3f}};hand_speed=4;tick();hand_speed=.5f;
 for(int t=0;t<8;t++)tick();bodies[1].unit.melee_attack_state=1;hands[0]=(real_point3d){.n={0,.6f,.5f}};assert(vr_combat_defend(0,1)==1);
 hand_speed=3;
 /* 6. the lunge in the air rises or dives to the enemy (3 m); on the ground
  *    an enemy two metres below is out of the dash */
 for(int air=0;air<2;air++){
  setup();combat=1;enabled=0;lunge_setting=6;grip[0]=1;tick();
  bodies[2].object.position.x=9;bodies[2].object.bounding_sphere_center=(real_point3d){.n={9,0,1.2f}};
  bodies[1].object.position=(real_point3d){.n={5,0,-2}};bodies[1].object.bounding_sphere_center=(real_point3d){.n={5,0,-.8f}};
  if(air)bodies[0].biped.flags|=FLAG(_biped_airborne_bit);
  real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};vr_combat_punch(0,0,&fist,&jab);assert(extra.target==1&&extra.approach_until>now);
  real_vector3d v={.n={0,0,-.01f}};vr_combat_velocity(0,&bodies[0].object.position,&v);
  if(air)assert(v.i>0&&v.k<-.3f&&extra.approach_until>now);else assert(v.i==0&&v.k==-.01f&&extra.approach_until==0);}
 lunge_setting=0;
 /* 7. the lights sit on the bones as drawn (the chest the last spine node,
  *    the face 8 cm over the neck), not the tick's camera point */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 {real_matrix4x3 drawn[3]={0};for(int k=0;k<3;k++){drawn[k].scale=1;drawn[k].forward.i=drawn[k].left.j=drawn[k].up.k=1;}
  drawn[0].position=(real_point3d){.n={2,1,0}};drawn[1].position=(real_point3d){.n={2,1,1.2f}};drawn[2].position=(real_point3d){.n={2,1,1.5f}};
  node_pose=drawn;real_point3d head,chest;assert(combat_regions(1,&head,&chest));
  assert(fabsf(chest.x-2)<1e-5f&&fabsf(chest.z-1.2f)<1e-5f&&fabsf(head.z-1.58f)<1e-5f&&fabsf(head.y-1)<1e-5f);
  node_pose=NULL;assert(combat_regions(1,&head,&chest)&&fabsf(chest.x-1.2f)<1e-5f);}
 /* Test67: one acquisition/damage owner for a sustained fast swing, including
  * its landing tick. Rest/release rearms; the other hand can switch targets. */
 setup();combat=1;enabled=0;grip[0]=grip[1]=1;lunge_setting=8;tick();
 bodies[1].object.position.x=5;bodies[1].object.bounding_sphere_center.x=5;
 bodies[2].object.position.x=9;bodies[2].object.bounding_sphere_center.x=9;
 {real_point3d fist={.n={.3f,0,1.2f}};real_vector3d jab={.n={.2f,0,0}};int before=strikes;
  assert(vr_combat_punch(0,0,&fist,&jab)==1&&extra.strike_pending);
  bodies[0].object.position.x=4.4f;tick();assert(strikes==before+1&&!extra.strike_pending);
  for(int i=0;i<8;i++){assert(vr_combat_punch(0,0,&fist,&jab)==1&&!extra.strike_pending);tick();}
  assert(strikes==before+1);
  bodies[1].object.damage_flags=FLAG(_object_dead_bit);
  assert(vr_combat_punch(0,1,&fist,&jab)==1&&extra.target==2&&extra.strike_pending);
  hand_speed=.1f;for(int i=0;i<3;i++)tick();assert(!extra.swing_used[0]);
  hand_speed=3;assert(vr_combat_punch(0,0,&fist,&jab)==1&&extra.strike_hand==0);
  owners[0]=VR_INTERACTION_NPC;tick();assert(!extra.strike_pending&&!extra.approach_until);
 }
 lunge_setting=0;
 /* Difficulty is a fist multiplier, scoped to this owner/target/tick; native
  * bullets and armed melee retain their damage and rear-kill rules. */
 for(int d=0;d<4;d++) {
  setup();combat=1;enabled=0;grip[0]=1;difficulty=d;health_setting=3;tick();
  real_point3d body_hit={.n={1.2f,0,.8f}};float durability[]={.85f,1,1.25f,1.5f};
  assert(vr_combat_hit(0,1,&body_hit,NULL,.8f,0)==1);
  assert(fabsf(vr_combat_damage_share()-1/(3*durability[d]))<1e-5f);
  assert(vr_combat_regular_blow(0,1)&&!vr_combat_regular_blow(0,2)&&!vr_combat_regular_blow(1,1));
  vr_combat_damage_end();assert(!vr_combat_regular_blow(0,1));
  assert(vr_combat_hit(0,1,&body_hit,NULL,.8f,1)==1&&!vr_combat_regular_blow(0,1));
  assert((combat_parry_ticks()==(int[]){8,6,5,4}[d]));
 }
 health_setting=1;
 /* A parry has stronger feedback plus a short opening, a block a shorter
  * amber impact. Switching to an incompatible session clears authority. */
 setup();combat=1;enabled=0;grip[0]=1;tick();
 bodies[1].object.position.x=.6f;bodies[1].object.bounding_sphere_center=(real_point3d){.n={.6f,0,1.2f}};
 bodies[1].object.forward=(real_vector3d){.n={-1,0,0}};vr_combat_note_melee(1);
 bodies[1].unit.melee_attack_state=1;hands[0]=(real_point3d){.n={.4f,.1f,1.3f}};hand_speed=4;tick();
 assert(vr_combat_defend(0,1)==0&&guard_sounds==1&&extra.defence_parry&&extra.defence_until==now+8);
 network=1;assert(vr_combat_defend(0,1)==1);network=0;
 setup();combat=1;enabled=0;grip[0]=1;hand_speed=.1f;tick();
 bodies[1].object.position.x=.6f;bodies[1].unit.melee_attack_state=1;hands[0]=(real_point3d){.n={.3f,0,1.45f}};
 assert(vr_combat_defend(0,1)<1&&guard_sounds==1&&!extra.defence_parry&&extra.defence_until==now+4);
 puts("PASS: Test67 stroke ownership/rearm/opposite-hand switching, four difficulties, scoped melee durability and block/parry feedback/authority");
 puts("PASS: Test66 fist combat: ENEMY HEALTH divides the blow (the multiplier, once), Grunts/Jackals/Elites/Hunters fight their own ways, an Elite answers a flurry, BLOCK (tiring) and PARRY (the swing undone, an opening), the lunge rises and dives in the air, lights on the drawn bones");
 setup();real_point3d camera;unit_get_camera_position(0,&camera);assert(vr_extra_render(camera.n)&&draws>0);enabled=0;assert(!vr_extra_render(camera.n));
 puts("PASS: production Test62 grenade ownership/ammo/release/tracking/network gates; enemy acquisition, lock, collision velocity, stun, rear takedown and pose invariants");
 puts("PASS: Test65 fist combat: the last frame's head acquires in a tick; a lunge carries the blow to its landing (given up after a second); counters undo the swing; a combo meter (ENEMY HEALTH, broken by a hit, out after 2 s) and a takedown that knocks down");
 puts("PASS: Test63 grenades taken at the drawn palm within 12 cm, slots in the chest frame; punches acquire within 2.5 m and 45 degrees (hooks too, not punches away), a 5 m/s step, the target slowed not frozen, a grab ends the assist");
}
"""
with tempfile.TemporaryDirectory(prefix='test62-extra-') as d:
 p=Path(d);(p/'check.c').write_text(stubs+extra_stubs+source+checks)
 subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'check.c'),'-lm','-o',str(p/'check')],check=True)
 subprocess.run([str(p/'check')],check=True)

# Execute the actual grenade creation/ammo transaction separately, including
# spawn failure and invalid BSP recovery. No live map or device is needed.
def function(text,name):
 a=text.index(name);b=text.index('{',a);depth=1;c=b+1
 while depth:
  depth+=(text[c]=='{')-(text[c]=='}');c+=1
 return text[a:c]
un=(R/'source/units/units.c').read_text()
native=function(un,'boolean unit_vr_throw_grenade(')
ns=stubs
ns=re.sub(r'static int unit_vr_throw_grenade\([^\n]*\n','',ns)
ns=ns.replace('real bounding_sphere_radius,shield_vitality;','real bounding_sphere_radius,shield_vitality;real_vector3d translational_velocity;')
ns=ns.replace('real primary_trigger;','real primary_trigger;real_vector3d aiming_vector;int grenade_throw_state;char grenade_counts[2];')
ns=ns.replace('r->type=0;r->object_index=NONE;','r->type=0;r->object_index=NONE;r->t=.5f;')
ns+=r"""
#define SET_FLAG(v,b,on) ((v)=(on)?((v)|FLAG(b)):((v)&~FLAG(b)))
#define NUMBER_OF_UNIT_GRENADE_TYPES 2
#define _unit_grenade_throw_idle 0
#define _new_object_never_automatically_delete_bit 0
struct game_globals_grenade{struct{long index;}projectile;};
struct game_globals{struct{int count;struct game_globals_grenade*address;}grenades;};
static struct game_globals_grenade grenade_tags[2]={{{5}},{{6}}};
static struct game_globals globals={.grenades={2,grenade_tags}};
static struct{int infinite_ammo;}cheat;
struct object_placement_data{unsigned flags;real_point3d position;real_vector3d forward,up;};
static int spawn_ok=1,bsp_ok=1,infinite,created,deleted,noted,unzoomed;static long spawn_owner;static struct object_placement_data spawned;
static struct game_globals*scenario_get_game_globals(void){return &globals;}
static real_vector3d*perpendicular3d(real_vector3d const*p,real_vector3d*out){(void)p;*out=(real_vector3d){.n={0,0,1}};return out;}
static void object_placement_data_new(struct object_placement_data*p,long tag,long owner){assert(tag==5||tag==6);memset(p,0,sizeof *p);spawn_owner=owner;}
static long object_new(struct object_placement_data const*p){spawned=*p;++created;return spawn_ok?3:NONE;}
static int object_force_inside_bsp(long i,real_point3d const*p){assert(i==3);(void)p;return bsp_ok;}
static void object_delete(long i){assert(i==3);deleted++;}
static struct unit_datum*object_get(long i){return unit_get(i);}
static void subtract_vectors3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*out){for(int k=0;k<3;k++)out->n[k]=a->n[k]-b->n[k];}
static void projectile_accelerate(long i,real_vector3d const*v){assert(i==3);for(int k=0;k<3;k++)bodies[i].object.translational_velocity.n[k]+=v->n[k];}
static int game_engine_infinite_grenades(long i){assert(i==0);return infinite;}
static void network_damage_note_grenade(long i,short t){assert(i==0&&t>=0&&t<2);noted++;}
static void player_control_unzoom(long i){assert(i==0);unzoomed++;}
"""
# Use the live fixture's inventory for the native transaction count getter.
ns=ns.replace('return ammo[t];','return bodies[u].unit.grenade_counts[t];')
native_checks=r"""
int main(void){
 struct unit_datum*u=unit_get(0);u->unit.player_index=0;u->object.parent_object_index=NONE;u->unit.aiming_vector.i=1;
 u->unit.grenade_counts[0]=2;u->unit.grenade_counts[1]=2;
 real_point3d p={.n={.4f,0,1.3f}};real_vector3d v={.n={.12f,.03f,.1f}};
 assert(unit_vr_throw_grenade(0,0,&p,&v)&&u->unit.grenade_counts[0]==1&&noted==1&&unzoomed==1&&spawn_owner==0);
 assert(!memcmp(&bodies[3].object.translational_velocity,&v,sizeof v));
 spawn_ok=0;assert(!unit_vr_throw_grenade(0,0,&p,&v)&&u->unit.grenade_counts[0]==1);
 spawn_ok=1;bsp_ok=0;assert(!unit_vr_throw_grenade(0,0,&p,&v)&&u->unit.grenade_counts[0]==1&&deleted==1);bsp_ok=1;
 obstruction=1;assert(unit_vr_throw_grenade(0,1,&p,&v)&&spawned.position.x<p.x&&u->unit.grenade_counts[1]==1);obstruction=0;
 cheat.infinite_ammo=1;assert(unit_vr_throw_grenade(0,1,&p,&v)&&u->unit.grenade_counts[1]==1);cheat.infinite_ammo=0;
 for(int t=-1;t<=2;t+=3)assert(!unit_vr_throw_grenade(0,(short)t,&p,&v));
 u->unit.grenade_counts[0]=0;assert(!unit_vr_throw_grenade(0,0,&p,&v));u->unit.grenade_counts[0]=1;
 network=1;assert(!unit_vr_throw_grenade(0,0,&p,&v));network=2;coop=1;ready=0;assert(!unit_vr_throw_grenade(0,0,&p,&v));
 ready=1;assert(unit_vr_throw_grenade(0,0,&p,&v));network=0;
 u->unit.grenade_counts[0]=1;p.x=NAN;assert(!unit_vr_throw_grenade(0,0,&p,&v));p.x=.4f;v.i=NAN;assert(!unit_vr_throw_grenade(0,0,&p,&v));v.i=.1f;
 u->unit.grenade_throw_state=1;assert(!unit_vr_throw_grenade(0,0,&p,&v));u->unit.grenade_throw_state=0;
 u->object.damage_flags=FLAG(_object_dead_bit);assert(!unit_vr_throw_grenade(0,0,&p,&v));
 puts("PASS: actual native grenade spawn/owner/velocity/ammo transaction; failed creation/BSP, walls, infinite ammo, counts, invalid values and online gates");
}
"""
with tempfile.TemporaryDirectory(prefix='test62-grenade-') as d:
 p=Path(d);(p/'native.c').write_text(ns+native+native_checks)
 subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'native.c'),'-lm','-o',str(p/'native')],check=True)
 subprocess.run([str(p/'native')],check=True)

# The caller itself retains a positive finite threshold before any sweep or
# scale division, even if another optional feature enables impact entry.
render=(R/'port/linux/game/vr_render.c').read_text()
melee=function(render,'void vr_render_impact_melee(')
assert '!isfinite(melee_threshold) || melee_threshold <= 0.0f' in melee
assert 'real scale = speed / (2.0f * melee_threshold)' in melee
assert melee.index('!isfinite(melee_threshold)') < melee.index('unit_get_camera_position')

# Compile the actual host-side gate with the real fist predicate. Direct
# config loading does not run the VR menu dependency resolver.
frame=(R/'port/linux/src/vr_frame.c').read_text()
fist_gate=function(frame,'int vr_physical_melee_hand_allowed(')
fist_fixture=r"""
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "port/linux/game/vr_sprint_melee_math.h"
#define VR_INTERACTION_NONE 0
static struct {int active,melee_requires_fist,weapon_hand;struct{unsigned hand_valid[2];float squeeze[2],trigger[2];}frame;}vr;
static int assistance,empty=1,owner[2];
static int config_boolean(char const*k){return !strcmp(k,"vr.assisted_combat")?assistance:0;}
static int vr_interaction_owner(int h){return owner[h];}
static int vr_hand_empty(void){return empty;}
"""
fist_checks=r"""
int main(void){
 vr.active=1;vr.weapon_hand=1;vr.frame.hand_valid[0]=vr.frame.hand_valid[1]=1;
 assert(vr_physical_melee_hand_allowed(0)); // original open-hand mode unaffected when assistance is off
 assistance=1;assert(!vr_physical_melee_hand_allowed(0));
 vr.frame.squeeze[0]=1;assert(!vr_physical_melee_hand_allowed(0));
 vr.frame.trigger[0]=1;assert(vr_physical_melee_hand_allowed(0));
 owner[0]=6;assert(!vr_physical_melee_hand_allowed(0));owner[0]=0;
 vr.frame.hand_valid[0]=0;assert(!vr_physical_melee_hand_allowed(0));
 empty=0;assert(vr_physical_melee_hand_allowed(1)); // the held weapon still strikes
 assistance=0;empty=1;assert(vr_physical_melee_hand_allowed(1));
 puts("PASS: actual shared melee hand gate enforces assisted fist from direct config; ordinary melee, weapon and owned-hand behavior preserved");
}
"""
with tempfile.TemporaryDirectory(prefix='test62-fist-gate-') as d:
 p=Path(d);(p/'fist.c').write_text(fist_fixture+fist_gate+fist_checks)
 subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-I',str(R),str(p/'fist.c'),'-lm','-o',str(p/'fist')],check=True)
 subprocess.run([str(p/'fist')],check=True)



# Run actual native ingress guards plus their VR/flat authority composition.
# Continuation oracles represent the unchanged native body after each guard.
guarded={}
for name,sig in [('begin','boolean unit_melee_attack_begin('),('hit','void unit_cause_melee_damage('),
                 ('continuous','static void unit_cause_continuous_melee_damage('),('impact','void unit_impact_melee_damage(')]:
    match=re.search(r'^'+re.escape(sig)+r'[^;]*?\)\s*\{',un,re.M)
    assert match,sig
    body=function(un[match.start():],sig)
    block=body.split('struct unit_datum *unit = unit_get(unit_index);',1)[1].split('struct unit_definition',1)[0]
    assert 'unit_interaction_melee_restrained(unit_index)' in block
    assert body.index('unit_interaction_melee_restrained')<body.index('unit_definition_get'),name
    guarded[name]=block
fixture=r"""
#include <assert.h>
#include <stdio.h>
#define FALSE 0
#define TRUE 1
typedef int boolean;
struct unit_datum {struct {int melee_attack_state,timer,animation_state,attached;}unit;};
static struct unit_datum actors[3];static int stun=1,restrained=1,native_calls[4];
static int vr_combat_stunned(long unit){return unit==1&&stun;}
static int vr_npc_interaction_restrained(long unit){return unit==1&&restrained;}
static struct unit_datum*unit_get(long unit){assert(unit>=0&&unit<3);return &actors[unit];}
"""+function(un,'static boolean unit_interaction_melee_restrained(')
fixture+='static int begin(long unit_index){struct unit_datum*unit=unit_get(unit_index);'+guarded['begin']+'native_calls[0]++;unit->unit.melee_attack_state=1;return 1;}\n'
fixture+='static void hit(long unit_index){struct unit_datum*unit=unit_get(unit_index);'+guarded['hit']+'native_calls[1]++;unit->unit.melee_attack_state=0;}\n'
fixture+='static void continuous(long unit_index){struct unit_datum*unit=unit_get(unit_index);'+guarded['continuous']+'native_calls[2]++;unit->unit.timer--;}\n'
fixture+='static void impact(long unit_index){struct unit_datum*unit=unit_get(unit_index);'+guarded['impact']+'native_calls[3]++;unit->unit.attached=1;}\n'
fixture+=r"""
int main(void){
 actors[1].unit.melee_attack_state=1;actors[1].unit.animation_state=44;actors[1].unit.timer=7;
 assert(!begin(1)&&native_calls[0]==0&&actors[1].unit.melee_attack_state==1);
 hit(1);assert(native_calls[1]==0&&actors[1].unit.melee_attack_state==0&&actors[1].unit.animation_state==44);
 actors[1].unit.melee_attack_state=4;continuous(1);assert(native_calls[2]==0&&actors[1].unit.melee_attack_state==4&&actors[1].unit.timer==7);
 impact(1);assert(native_calls[3]==0&&!actors[1].unit.attached);
 assert(begin(0));hit(0);continuous(0);impact(0);for(int n=0;n<4;n++)assert(native_calls[n]==1);
 restrained=0;
#ifdef HALO_VR
 assert(unit_interaction_melee_restrained(1)); /* independent opt-in VR stun */
#else
 assert(!unit_interaction_melee_restrained(1)); /* no VR stun implementation in flat */
#endif
 stun=0;assert(begin(1));hit(1);continuous(1);impact(1);
 for(int n=0;n<4;n++)assert(native_calls[n]==2);
 assert(actors[1].unit.melee_attack_state==0&&actors[1].unit.timer==6&&actors[1].unit.attached&&actors[1].unit.animation_state==44);
 puts("PASS: native VR/flat restraint+stun guards: new/pending/continuous/contact melee, state consumption, animation/timer recovery and unrelated actors preserved");
}
"""
for vr in (False,True):
    with tempfile.TemporaryDirectory(prefix='test62-stun-') as d:
        p=Path(d);(p/'stun.c').write_text(('#define HALO_VR 1\n' if vr else '')+fixture)
        subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined',
            '-fno-sanitize-recover=all',str(p/'stun.c'),'-o',str(p/'stun')],check=True)
        subprocess.run([str(p/'stun')],check=True)

# Execute the actual final-palm publisher/getter; stale hand samples must never
# cross frames, maps, unit identity changes, invalid tracking time or hand sides.
render=(R/'port/linux/game/vr_render.c').read_text()
palm_struct=render[render.index('static struct { real_point3d position, elbow, palm;'):render.index('/* The final wrist')]
palm_stub=stubs
palm_stub=re.sub(r'static int vr_render_palm_point[^\n]*\n','',palm_stub)
palm_code=palm_stub+'\nstatic unsigned long vr_contact_epoch;\n'+palm_struct
palm_code+=function(render,'static void vr_avatar_palm_note(')+'\n'+function(render,'int vr_render_palm_point(')
palm_code+=r"""
int main(void){
 real_point3d wrist={.n={-.105f,0,0}},knuckle={.n={-.05f,0,0}},out;
 vr_avatar_hands[0].valid=1;vr_avatar_hands[0].unit=7;vr_avatar_hands[0].time=pose_clock;
 vr_avatar_palm_note(0,&wrist,&knuckle);assert(vr_render_palm_point(0,7,out.n));
 assert(fabsf(out.x)<1e-6f&&out.y==0&&out.z==0); // origin is a valid palm, not an invalid sentinel
 assert(!vr_render_palm_point(1,7,out.n)&&!vr_render_palm_point(0,8,out.n));
 pose_clock+=.001;assert(!vr_render_palm_point(0,7,out.n));pose_clock-=.002;assert(!vr_render_palm_point(0,7,out.n));
 pose_clock=1;++vr_contact_epoch;assert(!vr_render_palm_point(0,7,out.n));vr_avatar_palm_note(0,&wrist,&knuckle);assert(vr_render_palm_point(0,7,out.n));
 pose_clock=NAN;assert(!vr_render_palm_point(0,7,out.n));pose_clock=1;
 vr_avatar_hands[1].valid=1;vr_avatar_hands[1].unit=7;vr_avatar_hands[1].time=pose_clock;
 wrist=(real_point3d){.n={0,.105f,0}};knuckle=(real_point3d){.n={0,.05f,0}};
 vr_avatar_palm_note(1,&wrist,&knuckle);assert(vr_render_palm_point(1,7,out.n)&&fabsf(out.y)<1e-6f);
 vr_avatar_hands[1].valid=0;assert(!vr_render_palm_point(1,7,out.n));vr_avatar_hands[1].valid=1;
 vr_avatar_palm_note(1,&wrist,&wrist);assert(!vr_render_palm_point(1,7,out.n));
 knuckle.x=NAN;vr_avatar_palm_note(1,&wrist,&knuckle);assert(!vr_render_palm_point(1,7,out.n));
 vr_avatar_palm_note(1,&wrist,NULL);assert(!vr_render_palm_point(1,7,out.n));
 assert(!vr_render_palm_point(-1,7,out.n)&&!vr_render_palm_point(2,7,out.n)&&!vr_render_palm_point(0,NONE,out.n));
 puts("PASS: production final-palm position/direction, both hands, world origin, hidden/stale/unit/epoch/time/malformed skeleton guards");
}
"""
with tempfile.TemporaryDirectory(prefix='test62-palm-') as d:
 p=Path(d);(p/'palm.c').write_text(palm_code)
 subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'palm.c'),'-lm','-o',str(p/'palm')],check=True)
 subprocess.run([str(p/'palm')],check=True)
ik=function(render,'void vr_render_first_person_ik(')
assert ik.index('vr_blend_action_arm(graph, matrices, authored') < ik.index('vr_avatar_palm_note(controller')
assert 'side ? "r " : "l "' in ik and 'side ? vr_weapon_hand() : 1 - vr_weapon_hand()' in ik
assert 'vr_manual_reload_feedback_active(hand) || vr_extra_feedback_active(hand)' in render
assert '!vr_manual_reload_feedback_active(controller) && !vr_extra_feedback_active(controller)' in render
render_order=(R/'source/render/render.c').read_text()
assert render_order.index('first_person_weapon_render_update();') < render_order.index('render_objects();') < render_order.index('vr_render_vehicle_controls()', render_order.index('render_objects();'))
