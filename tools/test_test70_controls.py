"""Test70: control remapping that never surprises the player, and left-hand
face buttons on the gun hand.

The owner's report: USE / RELOAD put on A, and JUMP (on A) was moved to
another button without a word (test23's vr_menu_button_set). Now a button
row is edited in place (A or left/right chooses, A sets); a button another
action has asks: CANCEL, SWAP, CLEAR the other, or USE BOTH. NONE stays a
choice for every gameplay button; RESET CONTROLS TO DEFAULT heads and ends
the page. Rows say when a binding does nothing now (Button Sprint's left
stick, HOLD with the grenade on the grip, the grip with physical weapons).

Left-hand mode: vr.mirror_buttons "auto" puts the face buttons (A/B: jump,
use/reload, the magazine release) on the gun hand even when the sticks stay
standard (vr.mirror_controls "off", the reporter's config); bindings are
never rewritten by handedness, so custom mappings stay.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

menu = read("port/linux/game/vr_menu.c")
frame = read("port/linux/src/vr_frame.c")
config = read("port/linux/src/port_config.c")
header = read("port/linux/include/halo_vr.h")
events = read("source/interface/ui_widget_event_handler_functions.c")

# A is its own function; button rows go through the in-place chooser
assert "#define VR_MENU_CONFIRM_FUNCTION 104" in header
assert "function_index == VR_MENU_CONFIRM_FUNCTION" in events
assert "handlers[0].function = VR_MENU_CONFIRM_FUNCTION;" in menu
assert "handlers[1].function = VR_MENU_NEXT_FUNCTION;" in menu
row = menu[menu.index("    if(setting->type == _vr_setting_button) {"):]
row = row[:row.index("return TRUE;\n    }") + 20]
assert "vr_menu_button_row_change(setting, action, step);" in row and "vr_menu_button_set(" not in row
assert menu.count('{ "RESET CONTROLS", "buttons", _vr_setting_reset_buttons') == 2
assert '{ "NONE", "none" } } },' in menu
# (rows fit their width, test_test25: a mark there, the words on the hints line)
for note in ('"%s: L STICK*"', '"*: OFF FOR NOW  "', '"+: SHARED  "', '"A: SWAP WITH %s"', '"A: TAKE %s, %s GETS NONE"',
             '" (DEFAULT)"', '"%s IS %s\'S. A: ASK  < >: CHANGE"', '"%s: %s?"'):
    assert note in menu, note
# other rows: A still steps on, and ends a button row's choosing
assert "if (!step)\n\t\t\tstep = 1;" in menu

# MIRROR BUTTONS
assert '{ "vr.mirror_buttons", _config_string, "\\"auto\\""' in config
assert '"MIRROR BUTTONS", "vr.mirror_buttons"' in menu
assert "vr.buttons_mirrored = vr.controls_mirrored ||" in frame
assert "int major = vr.buttons_mirrored ? 0 : 1;\n\tunsigned int right = vr.frame.hand_buttons[major]" in frame
assert "case VR_BUTTON_SOURCE_RIGHT_STICK: return (vr.frame.hand_buttons[stick_major] & HALO_XR_HAND_STICK) != 0;" in frame
assert "back_down = (vr.frame.hand_buttons[vr.buttons_mirrored ? 0 : 1] & HALO_XR_HAND_EAST) != 0;" in frame

check = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "vr_button_remap.h"
enum { NONE_SRC, A, B, X, Y, RS, LS, GRIP, RDOWN, HOLD };
enum { JUMP, ACTION, MELEE, CROUCH, SWITCH_WEAPON, GRENADE, SWITCH_GRENADE, RETICLE, PTT, COUNT };
static const int defaults[COUNT] = { A, B, RS, RDOWN, Y, X, HOLD, LS, NONE_SRC };
static void reset(int *s) { memcpy(s, defaults, sizeof(defaults)); }
int main(void) {
    int s[COUNT], other;
    /* the report: USE / RELOAD to A, which JUMP has */
    reset(s);
    other = vr_remap_conflict(s, COUNT, ACTION, A, NONE_SRC, HOLD);
    assert(other == JUMP);
    assert(!vr_remap_apply(s, COUNT, ACTION, A, other, VR_REMAP_CANCEL, NONE_SRC, HOLD));
    assert(!memcmp(s, defaults, sizeof(defaults)));                      /* cancel: nothing moved */
    assert(vr_remap_apply(s, COUNT, ACTION, A, other, VR_REMAP_SWAP, NONE_SRC, HOLD));
    assert(s[ACTION] == A && s[JUMP] == B);                               /* swap: the two trade */
    for (int i = 0; i < COUNT; i++) if (i != ACTION && i != JUMP) assert(s[i] == defaults[i]);
    reset(s);
    vr_remap_apply(s, COUNT, ACTION, A, JUMP, VR_REMAP_CLEAR, NONE_SRC, HOLD);
    assert(s[ACTION] == A && s[JUMP] == NONE_SRC);                        /* clear: jump unbound */
    reset(s);
    vr_remap_apply(s, COUNT, ACTION, A, JUMP, VR_REMAP_SHARE, NONE_SRC, HOLD);
    assert(s[ACTION] == A && s[JUMP] == A);                               /* both on A */
    /* no button is no conflict; NONE for every gameplay action */
    reset(s);
    assert(vr_remap_conflict(s, COUNT, JUMP, NONE_SRC, NONE_SRC, HOLD) == -1);
    assert(vr_remap_conflict(s, COUNT, JUMP, HOLD, NONE_SRC, HOLD) == -1);
    vr_remap_apply(s, COUNT, JUMP, NONE_SRC, -1, VR_REMAP_SWAP, NONE_SRC, HOLD);
    assert(s[JUMP] == NONE_SRC && s[ACTION] == B);
    /* a swap from "hold" leaves the other with no button, never "hold" */
    reset(s);
    other = vr_remap_conflict(s, COUNT, SWITCH_GRENADE, Y, NONE_SRC, HOLD);
    assert(other == SWITCH_WEAPON);
    vr_remap_apply(s, COUNT, SWITCH_GRENADE, Y, other, VR_REMAP_SWAP, NONE_SRC, HOLD);
    assert(s[SWITCH_GRENADE] == Y && s[SWITCH_WEAPON] == NONE_SRC);
    /* the row's values step around, past Button Sprint's left stick */
    assert(vr_remap_step(4, 1, 9, 5) == 6 && vr_remap_step(6, -1, 9, 5) == 4);
    assert(vr_remap_step(8, 1, 9, -1) == 0 && vr_remap_step(0, -1, 9, -1) == 8);
    assert(vr_remap_step(-1, 1, 9, -1) == 1);
    puts("PASS: Test70 remap rules: cancel/swap/clear/share, only the two actions change, hold never given, sprint's stick skipped");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test70-controls-") as temp:
    out = Path(temp)
    (out / "check.c").write_text(check, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Werror", "-Wno-unused-function", "-fsanitize=address,undefined",
                    "-I", str(ROOT / "port/linux/game"), str(out / "check.c"), "-o", str(out / "check")], check=True)
    subprocess.run([str(out / "check")], check=True)
print("PASS: Test70 controls: A sets a button row's choice, conflicts asked (never moved), NONE and reset rows, contextual notes, MIRROR BUTTONS on the gun hand")
