"""Test73b: sprint as the owner asked for it, on every build.

1. VR (the owner: "sprint button sprint is now on by default whenever people get this update ... I want the sprint
   button to have it on toggle, not hold"): Test73's update turns SLIDE on, which brings BUTTON SPRINT, with SPRINT
   TOGGLE at its old default, HOLD. SPRINT TOGGLE's default is TOGGLE now, and vr_initialize turns a config's HOLD
   into TOGGLE once (vr.test73b_sprint_toggle_applied); HOLD chosen after is kept.
2. VR, every controller: BUTTON SPRINT is the move stick's click (VR_BUTTON_SOURCE_LEFT_STICK, the one the menu frees
   for it); it read the left controller's, the turning stick's with the sticks mirrored. On the controllers that keep
   their layout (Index, Pico, Steam Frame, HP: not the Quest's remappable buttons) that click also crouched, so a
   toggled sprint slid as it stopped: with BUTTON SPRINT the click is sprint's alone and the turning stick held down
   crouches, as on the Quest (seated, the click is the horn as before). BULLET TIME, on for everyone since Test73,
   is the turning stick pushed up on every controller (the Quest's alone before).
3. Flat (the owner: "make it so on the Android port ... there's an actual button they can do for it. That shows up
   on the screen ... for flat builds, on PC too ... an actual button mapping for it. Shift maybe"): the touch screen
   shows SPRINT while the game's SPRINT is HOLD or TOGGLE (TouchControls; tools/test_test31_touch_lifecycle.py and
   tools/test_touch_layout_codec.py run it), which sends HALO_TOUCH_SPRINT, bit 16, through the host (its mask
   widened) to platform_sprint_held, beside the sprint key; the PC's key is Left Shift (controls.sprint), rebound in
   Controls Setup, and the launcher says so where SPRINT is chosen.

Each runs here with the production code, with negative controls.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8')
frame = read('port/linux/src/vr_frame.c')
config = read('port/linux/src/port_config.c')
vr_h = read('port/linux/src/vr.h')
host = read('port/android/host/host_sdl.c')
xinput = read('port/linux/src/xinput_sdl.c')
touch_h = read('port/android/include/halo_touch.h')
touch_java = read('port/android/app/src/main/java/com/halo/decomp/TouchControls.java')
layout_java = read('port/android/app/src/main/java/com/halo/decomp/TouchLayout.java')
activity = read('port/android/app/src/main/java/com/halo/decomp/HaloActivity.java')
launcher = read('port/linux/src/desktop_launcher.c')
movement_menu = read('port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.movement.xml')
profile_menu = read('port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.xml')
menus = read('port/linux/game/menu_functions.c')
for text in (frame, xinput, host, touch_java):
    assert '\r' not in text


def between(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


def block(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a) + len(end)] + '\n'


def build_and_run(name, program, extra=()):
    compiler = shutil.which('clang') or shutil.which('cc')
    assert compiler, 'a C compiler'
    with tempfile.TemporaryDirectory(prefix='test73b-sprint-') as work:
        source = Path(work, name + '.c')
        source.write_text(program)
        built = subprocess.run([compiler, '-std=gnu11', '-O1', '-Wall', '-Werror', '-Wno-unused-function',
                                '-Wno-unused-variable', '-Wno-unused-but-set-variable', '-I', str(ROOT),
                                '-I', str(ROOT / 'port/android/include'), *extra, str(source), '-pthread', '-lm',
                                '-o', str(Path(work, name))], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        result = subprocess.run([str(Path(work, name))], capture_output=True, text=True)
        return result.returncode, result.stdout


CHECKS = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
static int checks;
#define CHECK(c, what) do { checks++; if (!(c)) { printf("FAIL: %s\n", what); exit(1); } } while (0)
'''

# ---------- 1. VR: SPRINT TOGGLE's TOGGLE, by default and once for every config
assert '{ "vr.button_sprint_toggle", _config_boolean, "true",' in config
assert '{ "vr.button_sprint", _config_boolean, "false",' in config  # (SLIDE brings it: Test73's update)
assert '{ "vr.test73b_sprint_toggle_applied", _config_boolean, "false",' in config
init = function(frame, 'vr_initialize')
MIGRATION = between(init, '\t/* Test73b (the owner: "I want the sprint button to have it on toggle',
                    '\tvr_reload_settings();')
assert init.index('vr_menu_features_on();') < init.index(MIGRATION) < init.index('\tvr_reload_settings();')
MIGRATION_PROGRAM = CHECKS + r'''
static int toggle, applied, writes;
static int config_boolean(const char *key)
{
    if (!strcmp(key, "vr.button_sprint_toggle")) return toggle;
    CHECK(!strcmp(key, "vr.test73b_sprint_toggle_applied"), "only its keys");
    return applied;
}
static int config_write_boolean(const char *key, int value)
{
    writes++;
    if (!strcmp(key, "vr.button_sprint_toggle")) toggle = value;
    else { CHECK(!strcmp(key, "vr.test73b_sprint_toggle_applied"), "only its keys"); applied = value; }
    return 1;
}
static void platform_log(const char *format, ...) { (void)format; }
static void initialize(void)
{
#include "migration.inc"
}
int main(void)
{
    /* a config from before (Test73's: BUTTON SPRINT with SLIDE, SPRINT TOGGLE at its old default HOLD) */
    toggle = 0; applied = 0; initialize();
    CHECK(toggle == 1 && applied == 1, "HOLD, the old default, goes to TOGGLE");
    /* HOLD chosen in VR SETTINGS after: kept, start after start */
    toggle = 0; initialize(); initialize();
    CHECK(toggle == 0 && applied == 1, "HOLD chosen after is kept");
    /* a new config (TOGGLE, its default): left as it is, marked */
    toggle = 1; applied = 0; writes = 0; initialize();
    CHECK(toggle == 1 && applied == 1 && writes == 1, "a new config keeps TOGGLE");
    printf("ok %d\n", checks);
    return 0;
}
'''


def migration(code):
    with tempfile.TemporaryDirectory(prefix='test73b-sprint-inc-') as work:
        Path(work, 'migration.inc').write_text(code)
        return build_and_run('migration', MIGRATION_PROGRAM, ('-I', work))


status, output = migration(MIGRATION)
assert status == 0 and output.startswith('ok'), output
for code, what in [(mutated(MIGRATION, 'if (!config_boolean("vr.button_sprint_toggle"))', 'if (0)'),
                    'never changed: the update keeps HOLD'),
                   (mutated(MIGRATION, '\t\tconfig_write_boolean("vr.test73b_sprint_toggle_applied", 1);\n', ''),
                    'not once: HOLD chosen after is undone at every start')]:
    status, output = migration(code)
    assert status == 1 and output.startswith('FAIL'), (what, output)
print('PASS: SPRINT TOGGLE is TOGGLE by default and once for every config from before (HOLD, its old default); HOLD '
      'chosen after is kept (2 negative controls)')

# ---------- 2. VR: BUTTON SPRINT's click, crouch beside it, BULLET TIME on every controller
gestures = function(frame, 'update_gestures')
sprint_input = between(gestures, '\t\tint active = vr_button_sprint_input_mode(', '&vr.button_sprint_latched')
assert 'vr_button_sprint_input_mode(vr.button_sprint_enabled && vr.layout_vr,' in sprint_input
assert '(vr.frame.hand_buttons[vr.controls_mirrored ? 1 : 0] & HALO_XR_HAND_STICK) != 0,' in sprint_input
assert 'HALO_XR_BUTTON_LEFT_THUMB) != 0' not in sprint_input  # (the left controller's, whichever stick it was)
# (the menu frees the logical left stick for it: the move stick's, touch_source_down's)
assert 'case VR_BUTTON_SOURCE_LEFT_STICK: return (vr.frame.hand_buttons[1 - stick_major] & HALO_XR_HAND_STICK) != 0;' \
    in function(frame, 'touch_source_down')
assert 'int stick_major = vr.controls_mirrored ? 0 : 1;' in function(frame, 'touch_source_down')

LAYOUT = function(frame, 'layout_controls')
names = block(vr_h, 'enum\n{\n\tVR_BUTTON_ACTION_JUMP,', '};') + block(vr_h, 'enum\n{\n\tVR_BUTTON_SOURCE_NONE,', '};') + \
    ''.join(block(frame, 'static const %s' % t, '};') for t in ['char *const button_action_keys',
                                                              'char *const button_source_values',
                                                              'int button_defaults']) + \
    ''.join(function(frame, f) + '\n' for f in ['vr_button_action_key', 'vr_button_default'])
SUPPORT = function(frame, 'touch_source_hand') + '\n' + function(frame, 'touch_source_down') + '\n' + \
    function(frame, 'touch_buttons') + '\n'
LAYOUT_PROGRAM = CHECKS + r'''
#include "port/android/include/halo_android_abi.h"
enum { HAND_LOOSE, HAND_HELD, HAND_EMPTY };
''' + names + r'''
static struct { struct { uint32_t hand_buttons[2], buttons; float trigger[2], thumb[4]; int64_t predicted_display_period; } frame;
 int layout_vr, weapon_hand, touch_layout, zoom_down, view_recentred, back_pulse, heading_valid, x_hold_switched, controls_mirrored,
 buttons_mirrored, turn_stick_up, bullet_time_held, bullet_stick_up,
 grip_held[2], in_holster, hand_state, physical, button_source[VR_BUTTON_ACTIONS], recentre_source; unsigned pad_buttons; float pad_trigger[2];
 double x_held, grenade_pulse, view_held;
 int seated, turn_stick_down, reticle_hidden, reticle_press, reticle_cancelled, push_to_talk_held;
 int menus_active, menu_back_press, pointer_age, button_sprint_enabled;
 int force_render; long diag_fire_frame; long stereo_frames; } vr;
static int recentres;
static void platform_log(const char *f, ...) { (void)f; }
static int physical_weapons(void) { return vr.physical; }
static int vr_hand_empty(void) { return 0; }
static void host_xr_recenter(void) { recentres++; }
static void vr_haptic(int h, float a, float s) { (void)h; (void)a; (void)s; }
static int stick_zoom_active(void) { return 0; }
''' + '#include "support.inc"\n#include "layout.inc"\n' + r'''
#define LEFT_THUMB HALO_XR_BUTTON_LEFT_THUMB
#define MELEE HALO_XR_BUTTON_B
static void start(int touch, int sprint, int mirrored)
{
    int action;
    memset(&vr, 0, sizeof(vr));
    for (action = 0; action < VR_BUTTON_ACTIONS; action++) vr.button_source[action] = vr_button_default(action);
    vr.layout_vr = 1; vr.touch_layout = touch; vr.physical = 1; vr.button_sprint_enabled = sprint;
    vr.controls_mirrored = vr.buttons_mirrored = mirrored; vr.weapon_hand = mirrored ? 0 : 1;
    vr.frame.predicted_display_period = 13888889;
}
/* the physical left and right controllers' buttons, and the turning stick (after the sticks' swap) */
static unsigned step(unsigned left, unsigned right, float turn_x, float turn_y)
{
    vr.frame.hand_buttons[0] = left; vr.frame.hand_buttons[1] = right;
    vr.frame.thumb[2] = turn_x; vr.frame.thumb[3] = turn_y;
    layout_controls();
    return vr.pad_buttons;
}
int main(void)
{
    const unsigned K = HALO_XR_HAND_STICK;
    unsigned b;
    int seated;
    /* the controllers that keep their layout (Index, Pico, Steam Frame, HP), BUTTON SPRINT off: the move stick's
    click crouches, as ever; the turning stick held down does nothing */
    start(0, 0, 0);
    b = step(K, 0, 0, 0); CHECK(b & LEFT_THUMB, "sprint off: the click crouches");
    b = step(0, 0, 0, -0.9f); CHECK(!(b & LEFT_THUMB), "sprint off: the turning stick down is no crouch");
    /* BUTTON SPRINT on: the click is sprint's alone; the turning stick held down crouches (a slide while sprinting) */
    start(0, 1, 0);
    b = step(K, 0, 0, 0); CHECK(!(b & LEFT_THUMB), "sprint on: the click no longer crouches");
    b = step(0, 0, 0, -0.9f); CHECK(b & LEFT_THUMB, "sprint on: the turning stick held down crouches");
    b = step(0, 0, 0, -0.6f); CHECK(b & LEFT_THUMB, "held down: let go a little sooner than taken");
    b = step(0, 0, 0, 0); CHECK(!(b & LEFT_THUMB), "let go: no crouch");
    b = step(0, 0, 0.8f, -0.9f); CHECK(!(b & LEFT_THUMB), "a turn down and aside is a turn");
    b = step(0, K, 0, 0); CHECK((b & MELEE) && !(b & LEFT_THUMB), "the turning stick's click still melees");
    /* in a seat: the click is the horn (the crouch button) as before, and the stick down nothing */
    for (seated = 0; seated < 2; seated++)
    {
        start(0, 1, 0); vr.seated = 1;
        b = step(K, 0, 0, 0); CHECK(b & LEFT_THUMB, "seated: the click sounds the horn");
        b = step(0, 0, 0, -0.9f); CHECK(!(b & LEFT_THUMB), "seated: the stick down does nothing");
    }
    /* left-handed, the sticks mirrored: the move stick is the right controller's */
    start(0, 1, 1);
    b = step(0, K, 0, 0); CHECK(!(b & LEFT_THUMB) && !(b & MELEE), "mirrored: the move stick's click is sprint's");
    b = step(K, 0, 0, 0); CHECK((b & MELEE) && !(b & LEFT_THUMB), "mirrored: the turning stick's click melees");
    start(0, 0, 1);
    b = step(0, K, 0, 0); CHECK(b & LEFT_THUMB, "mirrored, sprint off: the move stick's click crouches");
    /* the Quest's remappable buttons: crouch is the turning stick held down by default, the click the reticle's */
    start(1, 1, 0);
    b = step(0, 0, 0, -0.9f); CHECK(b & LEFT_THUMB, "Quest: the turning stick held down crouches");
    /* BULLET TIME: the turning stick pushed up on every controller, in a seat too, never in the menus */
    start(0, 1, 0);
    step(0, 0, 0, 0.9f); CHECK(vr.bullet_time_held, "BULLET TIME on R UP: the other controllers");
    step(0, 0, 0, 0); CHECK(!vr.bullet_time_held, "BULLET TIME let go");
    vr.seated = 1; step(0, 0, 0, 0.9f); CHECK(vr.bullet_time_held, "BULLET TIME in a seat");
    vr.seated = 0; vr.menus_active = 1; step(0, 0, 0, 0.9f); CHECK(!vr.bullet_time_held, "no BULLET TIME in a menu");
    start(1, 1, 0);
    step(0, 0, 0, 0.9f); CHECK(vr.bullet_time_held, "BULLET TIME on R UP: the Quest's");
    vr.button_source[VR_BUTTON_ACTION_BULLET_TIME] = VR_BUTTON_SOURCE_A;
    step(0, HALO_XR_HAND_SOUTH, 0, 0); CHECK(vr.bullet_time_held, "the Quest's BUTTONS move it");
    step(0, 0, 0, 0.9f); CHECK(!vr.bullet_time_held, "moved off R UP");
    printf("ok %d\n", checks);
    return 0;
}
'''


def layout(code, support=SUPPORT):
    with tempfile.TemporaryDirectory(prefix='test73b-sprint-inc-') as work:
        Path(work, 'layout.inc').write_text(code)
        Path(work, 'support.inc').write_text(support)
        return build_and_run('layout', LAYOUT_PROGRAM, ('-I', work))


status, output = layout(LAYOUT)
assert status == 0 and output.startswith('ok'), output
for code, what in [(mutated(LAYOUT, 'if (vr.button_sprint_enabled && !vr.seated)', 'if (0)'),
                    'the click both sprints and crouches (the slide as a toggled sprint stops)'),
                   (mutated(LAYOUT, '(!vr.touch_layout ? vr.bullet_stick_up :', '(!vr.touch_layout ? 0 :'),
                    'BULLET TIME the Quest\'s alone')]:
    status, output = layout(code)
    assert status == 1 and output.startswith('FAIL'), (what, output)
print('PASS: BUTTON SPRINT is the move stick\'s click (mirrored too); with it the other controllers\' click no longer '
      'crouches and the turning stick held down does (seated, the click is the horn); BULLET TIME on R UP on every '
      'controller (2 negative controls)')

# ---------- 3. Flat: the touch screen's SPRINT and the PC's key
# (the bit, kept in step on both sides of the host/guest record)
assert '#define HALO_TOUCH_SPRINT   (1u << 16)' in touch_h and '#define HALO_TOUCH_BUTTONS  0x1ffffu' in touch_h
assert 'private static final int SPRINT=1<<16;' in touch_java
assert 'new Control("Sprint", left+w*.22f, top+h*.56f, r, SPRINT, BUTTON),' in touch_java
controls = between(touch_java, 'controls=new Control[] {', '};')
assert controls.index('"Touch"') < controls.index('"Sprint"') < controls.index('"HUD"')
assert '"touch_visibility",\n        "sprint"};' in layout_java and 'static final int SPRINT=19;' in layout_java
assert 'if(c.bit==SPRINT && (sprintMode==0 || (menus && !editing)))return false;' in touch_java
assert 'if(!menus) refreshSprint();' in touch_java
assert 'TouchControls.sprintMode(ConfigSettings.read(configRoot, "movement", "sprint", "\\"off\\"")));' in activity
# (the host passes it, bits above it masked off)
assert 'unsigned int held = (unsigned int)buttons & HALO_TOUCH_BUTTONS;' in host and '0xffffu' not in host
HOST = host[host.index('static pthread_mutex_t touch_lock'):host.index('#define HANDLE_COUNT')]
HOST_PROGRAM = CHECKS + r'''
#include <pthread.h>
#include <stdatomic.h>
#include "port/android/include/halo_touch.h"
typedef void JNIEnv; typedef void *jclass; typedef int jint; typedef int jboolean; typedef float jfloat;
typedef unsigned long long Uint64;
#define JNIEXPORT
#define JNICALL
static Uint64 SDL_GetTicks(void) { return 1; }
#include "host.inc"
int main(void)
{
    struct halo_touch_state s;
    Java_com_halo_decomp_TouchControls_nativeState(0, 0, 0, 0, 0, 0, (jint)(HALO_TOUCH_SPRINT | HALO_TOUCH_A), 0);
    host_touch_read(&s); CHECK(s.buttons == (HALO_TOUCH_SPRINT | HALO_TOUCH_A), "SPRINT reaches the game");
    Java_com_halo_decomp_TouchControls_nativeState(0, 0, 0, 0, 0, 0, 0, 0);
    host_touch_read(&s); CHECK(s.buttons == 0, "released");
    /* a tap between two polls still counts once */
    Java_com_halo_decomp_TouchControls_nativeState(0, 0, 0, 0, 0, 0, (jint)HALO_TOUCH_SPRINT, 0);
    Java_com_halo_decomp_TouchControls_nativeState(0, 0, 0, 0, 0, 0, 0, 0);
    host_touch_read(&s); CHECK(s.buttons == HALO_TOUCH_SPRINT, "a quick tap of SPRINT");
    host_touch_read(&s); CHECK(s.buttons == 0, "once");
    Java_com_halo_decomp_TouchControls_nativeState(0, 0, 0, 0, 0, 0, (jint)(1u << 17), 0);
    host_touch_read(&s); CHECK(s.buttons == 0, "no bit beyond SPRINT");
    printf("ok %d\n", checks);
    return 0;
}
'''


def host_run(code):
    with tempfile.TemporaryDirectory(prefix='test73b-sprint-inc-') as work:
        Path(work, 'host.inc').write_text('#ifndef HALO_VR\n' + code)
        return build_and_run('host', HOST_PROGRAM, ('-I', work))


status, output = host_run(HOST)
assert status == 0 and output.startswith('ok'), output
status, output = host_run(mutated(HOST, 'buttons & HALO_TOUCH_BUTTONS;', 'buttons & 0xffffu;'))
assert status == 1 and output.startswith('FAIL'), output
# (the game: SPRINT beside the key, a tap between two ticks once, a cancelled one none)
touch_state = function(xinput, 'touch_gamepad_state')
assert '    touch_sprint_held = (touch.buttons & HALO_TOUCH_SPRINT) != 0;\n' \
       '    if (touch_sprint_held) touch_sprint_pressed = 1;\n' in touch_state
assert 'touch_sprint_pressed = 0; /* (Test73b: a cancelled SPRINT is no press) */' in touch_state
assert 'pad->wButtons |= digital[index];' in touch_state and 'index < 8;' in touch_state  # (bits 6 to 13 only)
HELD = function(xinput, 'platform_sprint_held')
HELD_PROGRAM = CHECKS + r'''
#include <pthread.h>
static pthread_mutex_t mouse_lock = PTHREAD_MUTEX_INITIALIZER;
static int sprint_key_held;
#if defined(HALO_ANDROID) && !defined(HALO_VR)
static int touch_sprint_held, touch_sprint_pressed;
/* touch_gamepad_state's two lines: each poll of the touch screen */
static void poll_touch(int held) { touch_sprint_held = held; if (touch_sprint_held) touch_sprint_pressed = 1; }
#else
static void poll_touch(int held) { (void)held; }
#endif
#include "held.inc"
int main(void)
{
    sprint_key_held = 1; CHECK(platform_sprint_held(), "the key"); sprint_key_held = 0;
    CHECK(!platform_sprint_held(), "nothing held");
#if defined(HALO_ANDROID) && !defined(HALO_VR)
    poll_touch(1); CHECK(platform_sprint_held() && platform_sprint_held(), "SPRINT held, tick after tick");
    poll_touch(0); CHECK(!platform_sprint_held(), "let go between ticks after a tick saw it: no more");
    poll_touch(1); poll_touch(0); CHECK(platform_sprint_held(), "a tap between two ticks: one press");
    CHECK(!platform_sprint_held(), "once");
#endif
    printf("ok %d\n", checks);
    return 0;
}
'''


def held(code, *defines):
    with tempfile.TemporaryDirectory(prefix='test73b-sprint-inc-') as work:
        Path(work, 'held.inc').write_text(code)
        return build_and_run('held', HELD_PROGRAM, ('-I', work, *defines))


for defines in ((), ('-DHALO_ANDROID',), ('-DHALO_ANDROID', '-DHALO_VR')):
    status, output = held(HELD, *defines)
    assert status == 0 and output.startswith('ok'), (defines, output)
status, output = held(mutated(HELD, 'touched = touch_sprint_held || touch_sprint_pressed;',
                              'touched = touch_sprint_held;'), '-DHALO_ANDROID')
assert status == 1 and output.startswith('FAIL'), output
# (the PC's key, its rebinding, the flat MOVEMENT screen on every flat build, the launcher's word)
assert '{ "controls.sprint", _config_string, "\\"Left Shift\\"", "HALO_KEY_SPRINT",' in config
assert '{ "movement.sprint", _config_string, "\\"off\\"", "HALO_MOVEMENT_SPRINT",' in config
assert '{ "controls.sprint", L"SPRINT", 0 },' in menus
assert 'if (input_held(input, bindings[HALO_KEYBOARD_SPRINT][slot]))' in xinput
assert 'strings="OFF|HOLD|TOGGLE|AUTO" setting="movement.sprint" values="off|hold|toggle|auto"' in movement_menu
assert 'movement_profile_item" platform="flat"/>' in profile_menu
settings_page = function(launcher, 'page_settings')
assert '"SPRINT: HOLD sprints while Left Shift is held, TOGGLE starts and stops it with a press' in settings_page
assert settings_page.index('#ifndef HALO_VR') < settings_page.index('"SPRINT: HOLD sprints')
print('PASS: the touch screen\'s SPRINT reaches the game as the sprint key does (held, a quick tap once, nothing '
      'beyond its bit; the guest\'s VR build has no touch); Left Shift is the PC\'s, rebound in Controls Setup, and '
      'the launcher says so (2 negative controls)')
