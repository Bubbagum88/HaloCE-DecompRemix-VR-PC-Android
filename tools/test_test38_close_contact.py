"""Production radius policy and occupied-space expansion state; no headset claim."""
from pathlib import Path
import re
import subprocess
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test38-close-contact'
OUT.mkdir(parents=True, exist_ok=True)

def fn(s, name):
    m = re.search(r'^(?:static )?[\w *]+\b'+name+r'\s*\([^;{}]*\)\s*\{', s, re.M)
    assert m, name
    i = m.end(); depth = 1
    while depth:
        depth += (s[i] == '{') - (s[i] == '}'); i += 1
    return s[m.start():i]+'\n'

s = (ROOT/'port/linux/game/vr_close_contact.c').read_text()
code = r'''
#include <assert.h>
#include <string.h>
#include "port/linux/game/vr_close_contact_math.h"
typedef float real; typedef int boolean;
#define TRUE 1
#define MIN(a,b) ((a)<(b)?(a):(b))
enum {_game_connection_local};
static struct {long unit,tick;real radius;boolean active;} clearance;
static int active=1,network=0,world=0,free_space=1,queries;
static long tick;
static char const *mode="auto";
static float metres=.25f;
static char const *config_string(char const *key){return mode;}
static int config_boolean(char const *key){return world;}
static float config_real(char const *key){return metres;}
static float vr_units_per_metre(void){return 1.f;}
static int vr_active(void){return active;}
static int game_connection(void){return network;}
static long game_time_get(void){return tick;}
static int clearance_can_expand(long unit,real radius){queries++;return free_space;}
'''
code += fn(s, 'vr_close_contact_reset')+fn(s, 'vr_grab_contact_radius')
code += r'''
int main(void){
 assert(vr_close_radius_target(.5,.45,.01,1,1)==.18f);
 assert(vr_close_radius_target(.5,.45,2,1,1)==.5f);
 assert(vr_close_radius_target(.5,.45,NAN,1,1)==.25f);
 assert(vr_close_radius_target(.5,.45,.25,0,1)==.45f);
 assert(vr_grab_contact_radius(2,.45,.5)==.45f && queries==0);
 world=1;tick++;
 assert(vr_grab_contact_radius(2,.45,.5)==.25f && queries==0);
 mode="off";tick++;free_space=0;
 assert(vr_grab_contact_radius(2,.45,.5)==.25f && queries==1);
 assert(vr_grab_contact_radius(2,.45,.5)==.25f && queries==1); /* same tick */
 tick++;free_space=1;
 assert(fabsf(vr_grab_contact_radius(2,.45,.5)-.26f)<.00001f);
 for(int i=0;i<25;i++){tick++;vr_grab_contact_radius(2,.45,.5);}
 assert(vr_grab_contact_radius(2,.45,.5)==.45f);
 mode="on";world=0;tick++;
 assert(vr_grab_contact_radius(2,.45,.5)==.25f);
 network=1;assert(vr_grab_contact_radius(2,.45,.5)==.45f);
 network=0;active=0;free_space=0;tick++;
 assert(vr_grab_contact_radius(2,.45,.5)==.25f); /* XR loss cannot expand through a wall */
 free_space=1;tick++;
 assert(fabsf(vr_grab_contact_radius(2,.45,.5)-.26f)<.00001f);
 active=1;vr_close_contact_reset();assert(!clearance.active);
 mode="off";assert(vr_grab_contact_radius(3,.45,.5)==.45f);
 return 0;
}
'''
p = OUT/'radius.c'; p.write_text(code)
subprocess.run(['clang','-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-parameter',
                '-fsanitize=address,undefined','-I',str(ROOT),str(p),'-lm','-o',str(OUT/'radius')],check=True)
subprocess.run([str(OUT/'radius')],check=True)
expand = fn(s,'clearance_can_expand')
assert 'collision_get_features_in_sphere(_collision_test_for_bipeds_living_flags' in expand
assert 'collision_features_test_point(&features, &base' in expand
assert 'MAXIMUM_COLLISION_FEATURES_PER_TEST' in expand
render = (ROOT/'port/linux/game/vr_render.c').read_text()
radius = fn(render,'vr_player_collision_radius')
assert 'game_connection() != _game_connection_local' in radius
assert 'player_get(player)->unit_index != unit_index' in radius
assert 'object.parent_object_index != NONE' in radius
print('PASS adjustable contact radius, auto/override policy, bounded expansion, blocked expansion, lifecycle and stock-network guard')
