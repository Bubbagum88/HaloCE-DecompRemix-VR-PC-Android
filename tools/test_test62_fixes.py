"""Test62: real fallback-damage lookup and event-feedback delivery boundaries."""
from pathlib import Path
import subprocess
import tempfile
R=Path(__file__).resolve().parents[1]
def fn(text,name):
    start=text.index(name);brace=text.index('{',start);end=brace+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
reload=(R/'port/linux/game/vr_manual_reload.c').read_text()
damage=(R/'source/objects/damage.c').read_text()
render=(R/'port/linux/game/vr_render.c').read_text()
extras=(R/'port/linux/game/vr_extra_interaction.c').read_text()
code=r'''
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#include "vr_manual_reload_math.h"
#define NONE (-1)
typedef float real;
struct game_globals_falling_damage {struct{long index;}falling_damage,vehicle_collision_damage;};
static struct game_globals_falling_damage effects;
static struct globals {struct{int count;}falling_damage;} globals;
static int have_globals=1;
static struct globals *scenario_get_game_globals(void){return have_globals?&globals:0;}
#define TAG_BLOCK_GET_ELEMENT(block,index,type) (&effects)
static double clock_now=10;static int weapon_hand,pulses[2];static float amplitude[2],duration[2];
static double vr_pose_time(void){return clock_now;}
static int vr_weapon_hand(void){return weapon_hand;}
static void vr_haptic(int hand,float a,float s){assert(hand>=0&&hand<2);++pulses[hand];amplitude[hand]=a;duration[hand]=s;}
static double reload_feedback_start[2],reload_feedback_until[2];
static double extra_feedback_start[2],extra_feedback_until[2];
'''
code+=fn(damage,'long damage_globals_impact_effect(')
for sig in ('static void reload_pulse(', 'int vr_manual_reload_feedback_active(', 'static void reload_event_haptic('):code+='\n'+fn(reload,sig)
for sig in ('static void extra_pulse(', 'int vr_extra_feedback_active('):code+='\n'+fn(extras,sig)
code+='\n'+fn(render,'static void vr_pressure_buzz(\n')
code+=r'''
int main(void){
 have_globals=0;assert(damage_globals_impact_effect()==NONE);have_globals=1;
 globals.falling_damage.count=0;assert(damage_globals_impact_effect()==NONE);
 globals.falling_damage.count=1;effects.falling_damage.index=12;effects.vehicle_collision_damage.index=13;
 assert(damage_globals_impact_effect()==12);effects.falling_damage.index=NONE;assert(damage_globals_impact_effect()==13);
 effects.vehicle_collision_damage.index=NONE;assert(damage_globals_impact_effect()==NONE);
 for(weapon_hand=0;weapon_hand<2;++weapon_hand){int free_hand=1-weapon_hand;
  for(int i=0;i<4;++i){int events[]={VR_MR_INSERT,VR_MR_SEATED,VR_MR_RACKED,VR_MR_COMMIT};
   clock_now+=1;memset(pulses,0,sizeof pulses);reload_event_haptic(events[i],free_hand);
   assert(pulses[0]==1&&pulses[1]==1&&amplitude[0]>0&&amplitude[1]>0);
   assert(vr_manual_reload_feedback_active(0)&&vr_manual_reload_feedback_active(1));
   clock_now+=.01;assert(vr_manual_reload_feedback_active(0)&&vr_manual_reload_feedback_active(1));
   vr_pressure_buzz(0,.08f);vr_pressure_buzz(1,.08f);
   assert(pulses[0]==1&&pulses[1]==1); /* gun-wall and hand-wall buzz cannot replace insert/rack */
   clock_now+=.1;assert(!vr_manual_reload_feedback_active(0)&&!vr_manual_reload_feedback_active(1));
   assert(pulses[0]==1&&pulses[1]==1); /* polling never adds a buzz */
   vr_pressure_buzz(0,.08f);vr_pressure_buzz(1,.08f);
   assert(pulses[0]==2&&pulses[1]==2); /* normal surface feedback resumes immediately */
  }
  memset(pulses,0,sizeof pulses);reload_event_haptic(VR_MR_CHARGE,free_hand);
  assert(pulses[free_hand]==1&&pulses[weapon_hand]==0);
  clock_now-=5;assert(!vr_manual_reload_feedback_active(free_hand));clock_now+=10;
  memset(pulses,0,sizeof pulses);reload_event_haptic(VR_MR_NONE,free_hand);assert(pulses[0]==0&&pulses[1]==0);
 }
 assert(!vr_manual_reload_feedback_active(-1)&&!vr_manual_reload_feedback_active(2));
 clock_now+=1;memset(pulses,0,sizeof pulses);extra_pulse(0,.7f,.065f);
 vr_pressure_buzz(0,.08f);assert(pulses[0]==1&&vr_extra_feedback_active(0));
 vr_pressure_buzz(1,.08f);assert(pulses[1]==1); /* independent hand remains responsive */
 clock_now+=.066;vr_pressure_buzz(0,.08f);assert(pulses[0]==2&&!vr_extra_feedback_active(0));
 clock_now=NAN;assert(!vr_manual_reload_feedback_active(0)&&!vr_extra_feedback_active(0));
 puts("PASS: Test62 actual globals fallback, both-handed reload pulse dispatch and bounded contact priority; idle/time-reset guards");
}
'''
with tempfile.TemporaryDirectory(prefix='test62-') as temp:
    p=Path(temp);(p/'check.c').write_text(code)
    subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I',str(R/'port/linux/game'),str(p/'check.c'),'-lm','-o',str(p/'check')],check=True)
    subprocess.run([str(p/'check')],check=True)
# Protect the connection from the event to the renderer and adjusted palm.
render=(R/'port/linux/game/vr_render.c').read_text()
assert 'if (!vr_manual_reload_feedback_active(controller) && !vr_extra_feedback_active(controller)) {' in render
assert '!vr_hand_pose(hand_index, camera.n, hand.n, forward.n, up.n)' in reload
assert 'if(vr_hand_pose(reload.hand,reload.camera.n,hand.n,forward.n,up.n))' in reload
assert 'reload_event_haptic(event, hand_index);' in reload

# Category ranges must cover exactly their rows; a new row must not move the
# next category's controls or hide its last setting.
import re
menu=(R/'port/linux/game/vr_menu.c').read_text()
rows=menu.split('vr_menu_immersion[] =',1)[1].split('};',1)[0]
sections=menu.split('vr_menu_immersion_sections[] =',1)[1].split('};',1)[0]
for name,count in re.findall(r'\{ "([^"]+)", (\d+) \}',sections):
    part=rows.split('/* '+name+' */',1)[1].split('/*',1)[0]
    assert len(re.findall(r'^\s*VR_IMMERSION_\w+,',part,re.M))==int(count),name
print('PASS: Test62 every immersion category covers exactly its settings')
