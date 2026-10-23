"""Test73b: B goes back in the menus on every controller (the owner, relaying a Steam Frame player: "the b button didnt
seem to work in menus").

Before, only the Quest's menus took the face buttons by their letters (vr.touch_layout); every other controller kept
its game layout there, where the right controller's B is the game's X (use and reload), and on every headset B went
back only through the pointer, while it was on the menus. Now every controller's menus take the letters (the Steam
Frame's X and Y are its right controller's; the left's upper button stays back, View, where the layout makes it so),
and a B press goes back once whether the menus are pointed at or not: begun with the pointer on them, it is the
pointer's back (vr_ui_pointer's right click); begun off them, the game's B (vr.menu_back_press latches which for the
whole press, so the ray crossing onto or off the menus mid-press never goes back twice).

The production block (layout_controls) and the pointer's back (vr_ui_pointer) run here frame by frame, in both
orders, with negative controls.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]
frame = (ROOT / 'port/linux/src/vr_frame.c').read_text(encoding='utf-8')
assert '\r' not in frame


def between(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


layout = function(frame, 'layout_controls')
BLOCK = between(layout, '\t/* test30: in the menus', '\t/* the off hand\'s trigger zooms */')
pointer = function(frame, 'vr_ui_pointer')
POINTER = between(pointer, '\tback_down = (vr.frame.hand_buttons[1] & HALO_XR_HAND_EAST) != 0;',
                  '\tif (!vr.pointer_age || pointer->left_clicks || pointer->right_clicks)')
assert 'if (vr.menus_active)\n\t{' in BLOCK and 'vr.menu_back_press = vr.pointer_age ? 1 : 2;' in BLOCK
assert 'if (back_down && !vr.pointer_back && vr.menu_back_press == 1)' in POINTER

PROGRAM = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "halo_android_abi.h"
static struct { struct halo_xr_frame frame; int menus_active, touch_layout, controls_mirrored, buttons_mirrored,
    x_hold_switched; double grenade_pulse, x_held; int menu_back_press, pointer_age, pointer_back; } vr;
static int logs;
static void platform_log(const char *format, ...) { (void)format; logs++; }
struct pointer_state { int right_clicks; };
static unsigned int buttons_frame(unsigned int right, unsigned int left)
{
    int grenade_down = 0;
    unsigned int buttons = 0;
    (void)right; (void)left; /* (the frame's buttons: step) */
#include "block.inc"
    (void)grenade_down;
    return buttons;
}
static int pointer_frame(int on_menus)
{
    struct pointer_state state = { 0 }, *pointer = &state;
    int back_down;
    if (!on_menus) { vr.pointer_age = 0; return 0; }
#include "pointer.inc"
    vr.pointer_back = back_down;
    vr.pointer_age = 1;
    return state.right_clicks;
}
static int backs;
/* a frame: the pointer and the buttons in either order; counts the backs (the
pointer's click, or the game's B going down) */
static unsigned int last_b;
static unsigned int step(unsigned int right, unsigned int left, int on_menus, int pointer_first)
{
    unsigned int buttons;
    /* (the frame's buttons, as the frame has them for both) */
    vr.frame.hand_buttons[1] = right; vr.frame.hand_buttons[0] = left;
    if (pointer_first) { backs += pointer_frame(on_menus); buttons = buttons_frame(right, left); }
    else { buttons = buttons_frame(right, left); backs += pointer_frame(on_menus); }
    if ((buttons & HALO_XR_BUTTON_B) && !last_b) backs++;
    last_b = buttons & HALO_XR_BUTTON_B;
    return buttons;
}
#define CHECK(x, what) do { if (!(x)) { printf("FAIL %s (order %d)\n", what, order); return 1; } } while (0)
int main(void)
{
    const unsigned int S = HALO_XR_HAND_SOUTH, E = HALO_XR_HAND_EAST, W = HALO_XR_HAND_WEST, N = HALO_XR_HAND_NORTH;
    int order, i;
    for (order = 0; order < 2; order++) {
        memset(&vr, 0, sizeof(vr)); vr.menus_active = 1; vr.touch_layout = 0; /* the Steam Frame's */
        /* B held, the menus not pointed at: the game's B, one back */
        backs = 0; last_b = 0;
        for (i = 0; i < 4; i++) step(E, 0, 0, order);
        step(0, 0, 0, order);
        CHECK(backs == 1, "B off the menus goes back once");
        /* B pressed on the menus: the pointer's back, once */
        backs = 0; last_b = 0; step(0, 0, 1, order);
        for (i = 0; i < 4; i++) CHECK(!(step(E, 0, 1, order) & HALO_XR_BUTTON_B), "no game B with the pointer's back");
        step(0, 0, 1, order);
        CHECK(backs == 1, "B on the menus goes back once");
        /* begun off the menus, the ray onto them mid-press: still one back */
        backs = 0; last_b = 0; step(0, 0, 0, order);
        step(E, 0, 0, order); step(E, 0, 1, order); step(E, 0, 1, order); step(0, 0, 1, order);
        CHECK(backs == 1, "the ray onto the menus mid-press: one back");
        /* begun on the menus, the ray off them mid-press: still one back */
        backs = 0; last_b = 0; step(0, 0, 1, order);
        step(E, 0, 1, order); step(E, 0, 0, order); step(E, 0, 0, order); step(0, 0, 0, order);
        CHECK(backs == 1, "the ray off the menus mid-press: one back");
        /* the Frame's letters: A, X and Y on its right controller; its left has no Y (View is back) */
        CHECK(step(S, 0, 1, order) == HALO_XR_BUTTON_A, "A");
        CHECK(step(W, 0, 1, order) == HALO_XR_BUTTON_X, "the Frame's X");
        CHECK(step(N, 0, 1, order) == HALO_XR_BUTTON_Y, "the Frame's Y");
        CHECK(step(0, S, 1, order) == HALO_XR_BUTTON_X, "a left lower button's X (Index, Pico)");
        CHECK(step(0, E, 1, order) == 0, "a left upper button is View's back, not Y (Index, Pico)");
        /* the Quest's: its left upper button is Y */
        vr.touch_layout = 1;
        CHECK(step(0, E, 1, order) == HALO_XR_BUTTON_Y, "the Quest's Y");
    }
    printf("ok %d\n", logs);
    return 0;
}
'''


def run(block, pointer_code):
    compiler = shutil.which('clang') or shutil.which('cc')
    assert compiler, 'a C compiler'
    with tempfile.TemporaryDirectory() as work:
        Path(work, 'block.inc').write_text(block)
        Path(work, 'pointer.inc').write_text(pointer_code)
        Path(work, 'menu_back.c').write_text(PROGRAM)
        build = subprocess.run([compiler, '-std=gnu99', '-Wall', '-Werror', '-Wno-unused-function',
                                '-Wno-unused-variable', '-I', work, '-I', str(ROOT / 'port/android/include'),
                                str(Path(work, 'menu_back.c')), '-o', str(Path(work, 'menu_back'))],
                               capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        result = subprocess.run([str(Path(work, 'menu_back'))], capture_output=True, text=True)
        return result.returncode, result.stdout


status, output = run(BLOCK, POINTER)
assert status == 0 and output.startswith('ok'), output
for block, pointer_code, what in [
        (mutated(BLOCK, 'if (vr.menus_active)\n\t{', 'if (vr.menus_active && vr.touch_layout)\n\t{'), POINTER,
         'the Quest alone (the report)'),
        (mutated(BLOCK, 'vr.menu_back_press = vr.pointer_age ? 1 : 2;', 'vr.menu_back_press = 1;'), POINTER,
         'B only through the pointer'),
        (BLOCK, mutated(POINTER, 'if (back_down && !vr.pointer_back && vr.menu_back_press == 1)',
                        'if (back_down && !vr.pointer_back)'), 'no latch: two backs'),
        (mutated(BLOCK, '\t\tif (physical_right & HALO_XR_HAND_WEST) buttons |= HALO_XR_BUTTON_X;\n', ''), POINTER,
         'no Frame X')]:
    status, output = run(block, pointer_code)
    assert status == 1 and output.startswith('FAIL'), (what, output)
print('PASS: B goes back in the menus on every controller, pointed at or not, once a press (the ray crossing mid-'
      'press too, either order); the Steam Frame\'s A, X and Y by their letters on its right controller; Index and '
      'Pico keep the left upper as back, the Quest\'s is Y (4 negative controls)')
