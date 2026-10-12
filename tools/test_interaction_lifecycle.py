"""Compile the actual shared grip-owner API and exercise cross-feature lifecycle."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'port/linux/src/vr_frame.c').read_text()
start = source.index('int vr_interaction_owner(')
end = source.index('static void update_gestures', start)
api = source[start:end]
fixture = r'''
#include <assert.h>
#include <stddef.h>
#include <string.h>
enum { VR_INTERACTION_NONE, VR_INTERACTION_RELOAD, VR_INTERACTION_VEHICLE,
 VR_INTERACTION_WORLD, VR_INTERACTION_PARKOUR, VR_INTERACTION_NPC, VR_INTERACTION_COUNT };
enum { HALO_XR_FRAME_FOCUSED=1, HALO_XR_FRAME_RECENTRED=2 };
enum { HALO_XR_BUTTON_X=4 };
enum { VR_ACTION_SWITCH_WEAPON=1, VR_ACTION_DROP_WEAPON=2, VR_ACTION_GRAB_WEAPON=4 };
static struct { int active,menus_active,grip_pressed[2],grip_released[2],grip_held[2];
 struct { int flags,hand_valid[2]; } frame;
 int two_hand_held,two_handed,support_near,weapon_hand,actions; unsigned pad_buttons; float support_dwell;
 int reload_held_from_menu;
} vr;
static int interaction_owner[2];
static int interaction_trigger_held[2];
'''
cases = r'''
int main(void) {
 vr.active=1;vr.frame.flags=HALO_XR_FRAME_FOCUSED;
 vr.frame.hand_valid[0]=vr.frame.hand_valid[1]=1;
 vr.grip_held[0]=vr.grip_held[1]=1;vr.weapon_hand=0;
 for(int owner=1;owner<VR_INTERACTION_COUNT;owner++) {
  vr.two_hand_held=vr.two_handed=vr.support_near=1;vr.support_dwell=1;
  vr.actions=7;
  assert(vr_interaction_claim(0,owner));
  assert(!vr.two_handed&&!vr.two_hand_held&&!vr.support_near&&!vr.support_dwell&&!vr.actions);
  for(int other=1;other<VR_INTERACTION_COUNT;other++) {
   if(other==owner) continue;
   assert(!vr_interaction_claim(0,other));
   vr_interaction_release(0,other);assert(vr_interaction_owner(0)==owner);
  }
  /* Checkpoint cancellation: each feature releases only its own ownership. */
  for(int reset=1;reset<VR_INTERACTION_COUNT;reset++) vr_interaction_release(0,reset);
  assert(vr_interaction_owner(0)==VR_INTERACTION_NONE);
  assert(vr_interaction_claim(0,owner));
  vr.frame.flags=0;
  int down=9,up=9;assert(!vr_interaction_grip(0,&down,&up)&&!down&&!up);
  assert(vr_interaction_owner(0)==VR_INTERACTION_NONE);
  vr.frame.flags=HALO_XR_FRAME_FOCUSED;
  assert(vr_interaction_claim(0,owner));vr.frame.hand_valid[0]=0;
  assert(vr_interaction_owner(0)==VR_INTERACTION_NONE);
  vr.frame.hand_valid[0]=1;
  assert(vr_interaction_claim(0,owner));vr.menus_active=1;
  assert(vr_interaction_owner(0)==VR_INTERACTION_NONE&&!vr_interaction_claim(0,owner));
  vr.menus_active=0;
  assert(vr_interaction_claim(0,owner));vr.frame.flags|=HALO_XR_FRAME_RECENTRED;
  assert(vr_interaction_owner(0)==VR_INTERACTION_NONE&&!vr_interaction_claim(0,owner));
  vr.frame.flags=HALO_XR_FRAME_FOCUSED;
 }
 assert(!vr_interaction_claim(-1,1)&&!vr_interaction_claim(2,1));
 assert(!vr_interaction_claim(0,0)&&!vr_interaction_claim(0,VR_INTERACTION_COUNT));
 /* Alternate manual-reload input shares the same exclusive owner slot while
  * ordinary features still require grip through the legacy wrapper. */
 vr.grip_held[0]=0;interaction_trigger_held[0]=1;
 assert(vr_interaction_trigger(0));
 assert(vr_interaction_claim_input(0,VR_INTERACTION_RELOAD,vr_interaction_trigger(0)));
 assert(!vr_interaction_claim_input(0,VR_INTERACTION_WORLD,vr_interaction_trigger(0)));
 vr_interaction_release(0,VR_INTERACTION_RELOAD);
 interaction_trigger_held[0]=0;assert(!vr_interaction_trigger(0));
 assert(!vr_interaction_claim_input(0,VR_INTERACTION_RELOAD,vr_interaction_trigger(0)));
 vr.pad_buttons=HALO_XR_BUTTON_X;assert(vr_manual_reload_action_down());
 vr.menus_active=1;assert(!vr_manual_reload_action_down());vr.menus_active=0;
 vr.frame.flags|=HALO_XR_FRAME_RECENTRED;assert(!vr_manual_reload_action_down());
 vr.frame.flags=HALO_XR_FRAME_FOCUSED;assert(vr_manual_reload_action_down());
 vr.frame.flags=0;assert(!vr_manual_reload_action_down());
 vr.frame.flags=HALO_XR_FRAME_FOCUSED;
 /* Test61: X still held from a menu (vr_ui_pointer latched it) is no reload
  * until let go; the next press is */
 vr.reload_held_from_menu=1;assert(!vr_manual_reload_action_down());assert(vr.reload_held_from_menu);
 vr.pad_buttons=0;assert(!vr_manual_reload_action_down());assert(!vr.reload_held_from_menu);
 vr.pad_buttons=HALO_XR_BUTTON_X;assert(vr_manual_reload_action_down());
 vr.pad_buttons=0;
 vr.grip_held[0]=1;
 vr.active=0;assert(!vr_interaction_claim(0,1));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp)/'lifecycle.c'
    exe = Path(tmp)/'lifecycle'
    c.write_text(fixture+api+cases)
    subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('shared interaction lifecycle: passed (production API, ASan/UBSan)')
