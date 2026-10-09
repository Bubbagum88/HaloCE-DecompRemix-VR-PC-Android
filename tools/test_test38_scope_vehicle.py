"""Execute actual mounted preview and shot paths: preview excludes target attraction.
Scope persistence/menu/profile coverage complements test_test22's pose replay.
"""
from pathlib import Path
import re, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
def fn(s,n):
 m=re.search(r'^(?:static )?[\w *]+\b'+n+r'\s*\([^;{}]*\)\s*\{',s,re.M);assert m,n
 e=m.end();d=1
 while d:d+=(s[e]=='{')-(s[e]=='}');e+=1
 return s[m.start():e]+'\n'
s=(ROOT/'source/game/aim_assist.c').read_text()
code=r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
typedef int boolean;typedef float real;typedef struct {float x,y,z;} real_point3d;typedef struct {float i,j,k;} real_vector3d;
#define NONE -1
#define TRUE 1
#define FALSE 0
#define MAXIMUM_COLLISION_USER_STACK_DEPTH 8
#define _collision_user_aim_assist 1
struct player_datum {long unit_index,team_index,aim_assist_unit_index,aim_assist_timestamp;};
struct unit_datum {struct {long parent_object_index;} object;};
struct aim_assist_parameters {float deviation_angle;};struct aim_assist_target {real_point3d position;float autoaim_level;long object_index;};
static struct player_datum p={1,2,77,88};static struct unit_datum player_unit={{42}};static int global_current_collision_user_depth=1,global_current_collision_users[8],target_calls,convergence_calls;
static struct player_datum *player_get(long i){return &p;}
static struct unit_datum *unit_try_and_get(long i){assert(i==1);return &player_unit;}
static long unit_get_aiming_unit_index(long i){return i;}
static int unit_get_zoom_level(long i){return 0;}
static int unit_get_aim_assist_parameters(long i,int z,struct aim_assist_parameters *a){a->deviation_angle=1;return 1;}
static void match_assert_valid_real_normal3d(const char*a,int b,real_vector3d*c){}
static void match_assert(const char*a,int b,int ok){assert(ok);}
static void director_camera_deterministic(long i,real_point3d *p,real_vector3d *v){*p=(real_point3d){0,0,0};*v=(real_vector3d){1,0,0};}
static int aim_assist(struct aim_assist_parameters*a,real_point3d*b,real_vector3d*c,long d,long e,struct aim_assist_target*t){target_calls++;t->position=(real_point3d){0,1,0};t->autoaim_level=1;t->object_index=9;return 1;}
static void vector_from_points3d(const real_point3d*a,const real_point3d*b,real_vector3d*v){*v=(real_vector3d){b->x-a->x,b->y-a->y,b->z-a->z};}
static float normalize3d(real_vector3d*v){return 1;}
static void aim_assist_collision_direction(long a,long b,real_point3d c,real_vector3d d,const real_point3d*e,const real_vector3d*f,real_vector3d*g){convergence_calls++;*g=d;}
static void fast_normals_interpolate(const real_vector3d*a,const real_vector3d*b,float t,real_vector3d*r){r->i=a->i*(1-t)+b->i*t;r->j=a->j*(1-t)+b->j*t;r->k=0;}
static void pin_normal_to_cone3d(const real_vector3d*a,const real_vector3d*b,float c,float d,real_vector3d*r){*r=*a;}
#define sine sinf
#define cosine cosf
static int game_time_get(void){return 123;}
'''
code+=fn(s,'player_aim_projectile_internal')+fn(s,'player_aim_projectile')+fn(s,'vr_aim_assist_converge')+fn(s,'vr_preview_player_projectile')
code+=r'''
int main(void){real_point3d origin={0,0,0};real_vector3d preview={1,0,0},shot=preview;
vr_preview_player_projectile(0,&origin,&preview);
assert(convergence_calls==0 && preview.i==1 && preview.j==0);assert(p.aim_assist_unit_index==77 && p.aim_assist_timestamp==88);
player_unit.object.parent_object_index=NONE;preview=(real_vector3d){1,0,0};
vr_preview_player_projectile(0,&origin,&preview);
assert(convergence_calls==1 && target_calls==0 && preview.i==1 && preview.j==0);
player_unit.object.parent_object_index=42;
assert(player_aim_projectile(0,&origin,&shot)==9);assert(target_calls==1 && shot.i==0 && shot.j==1);
assert(p.aim_assist_unit_index==9 && p.aim_assist_timestamp==123);assert(global_current_collision_user_depth==1);
puts("PASS: mounted VR preview stays on the selected muzzle ray; unmounted geometric convergence remains; native projectile retains autoaim and target bookkeeping");}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(code)
 subprocess.run(['clang','-std=gnu11','-fsanitize=address,undefined',str(p/'t.c'),'-lm','-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
profiles=(ROOT/'port/linux/src/vr_scope_profiles.h').read_text();config=(ROOT/'port/linux/src/port_config.c').read_text();menu=(ROOT/'port/linux/game/vr_menu.c').read_text();frame=(ROOT/'port/linux/src/vr_frame.c').read_text()
keys=re.findall(r' X\((\w+),',profiles);assert len(keys)==11 and 'rocket_launcher' in keys
for key in keys:
 for part,default in [('forward','0.0'),('up','0.0'),('right','0.0'),('scale','1.0')]:
  assert f'"vr.scope_{key}_{part}", _config_real, "{default}"' in config
assert 'VR_SCOPE_PROFILES(SCOPE_MENU)' in menu and 'VR_SCOPE_PROFILES(SCOPE_KEY)' in menu and 'VR_SCOPE_PROFILES(SCOPE_KEY)' in frame
assert 'VR_SCOPE_PROFILES(SCOPE_CLASS)' in fn(frame,'place_scope')
print('PASS: all 11 scope profiles have persistent config, shared menu/reset/load coverage; legacy keys preserved')

# Replay exclusive hand arbitration against the production helpers.
code=r'''
#include <assert.h>
#include <stdio.h>
#define HALO_XR_FRAME_FOCUSED 1
#define HALO_XR_FRAME_RECENTRED 2
#define VR_ACTION_SWITCH_WEAPON 8
#define VR_ACTION_DROP_WEAPON 32
#define VR_ACTION_GRAB_WEAPON 64
enum { VR_INTERACTION_NONE, VR_INTERACTION_RELOAD, VR_INTERACTION_VEHICLE, VR_INTERACTION_WORLD, VR_INTERACTION_PARKOUR, VR_INTERACTION_NPC, VR_INTERACTION_COUNT };
static int interaction_owner[2];
static struct {int active,menus_active,grip_held[2],grip_pressed[2],grip_released[2],weapon_hand,two_hand_held,two_handed,support_near;float support_dwell;unsigned actions;struct {unsigned flags,hand_valid[2];}frame;}vr;
'''
for name in ('vr_interaction_owner','vr_interaction_grip','vr_interaction_claim_input','vr_interaction_claim','vr_interaction_release'):code+=fn(frame,name)
code+=r'''
int main(void){int p,r;vr.active=1;vr.frame.flags=1;vr.frame.hand_valid[0]=vr.frame.hand_valid[1]=1;vr.grip_held[0]=vr.grip_held[1]=1;vr.grip_pressed[0]=1;vr.weapon_hand=1;
assert(vr_interaction_grip(0,&p,&r)&&p&&!r);assert(!vr_interaction_claim(-1,1));assert(!vr_interaction_claim(2,1));
assert(vr_interaction_claim(0,VR_INTERACTION_NPC));
assert(!vr_interaction_claim(0,VR_INTERACTION_WORLD));
vr_interaction_release(0,VR_INTERACTION_WORLD);assert(vr_interaction_owner(0)==VR_INTERACTION_NPC);
vr_interaction_release(0,VR_INTERACTION_NPC);
assert(vr_interaction_claim(0,VR_INTERACTION_RELOAD));assert(!vr_interaction_claim(0,VR_INTERACTION_WORLD));
vr_interaction_release(0,VR_INTERACTION_WORLD);assert(vr_interaction_owner(0)==VR_INTERACTION_RELOAD);
vr_interaction_release(0,VR_INTERACTION_RELOAD);assert(!vr_interaction_owner(0));
vr.actions=127;vr.two_hand_held=vr.two_handed=vr.support_near=1;
assert(vr_interaction_claim(1,VR_INTERACTION_VEHICLE));assert(!vr.two_hand_held&&!vr.two_handed&&!vr.support_near);assert(vr.actions==(127&~(8|32|64)));
vr.frame.hand_valid[1]=0;assert(!vr_interaction_owner(1));vr.frame.hand_valid[1]=1;
assert(vr_interaction_claim(1,VR_INTERACTION_WORLD));vr.frame.flags|=2;assert(!vr_interaction_owner(1));
vr.frame.flags=1;assert(vr_interaction_claim(1,VR_INTERACTION_WORLD));vr.frame.flags=0;assert(!vr_interaction_owner(1));assert(!vr_interaction_grip(1,&p,&r)&&!p&&!r);
puts("PASS: grip ownership bounds, exclusion, owner-only release, tracking/focus/recenter reset and grip action cancellation");}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(code)
 subprocess.run(['clang','-std=gnu11','-fsanitize=address,undefined',str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)

assert '{ "vr.npc_interaction", _config_boolean, "false"' in (ROOT / "port/linux/src/port_config.c").read_text()
