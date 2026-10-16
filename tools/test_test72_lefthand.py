"""Test72: the Discord reports the owner passed on.

- LEFT-HAND MODE: the BUTTONS rows named the gun hand's buttons A/B, which
  left-handed are the left controller's X/Y ("changing B changes Y, changing
  A changes X"). The rows show and choose the physical letter; the binding
  saved is the logical one it always was (nothing of a player's changes).
- The menus' back stays the right controller's B with LEFT-HAND MODE (its
  mirrored face buttons had made it Y).
- BULLET TIME on R UP in a vehicle or turret: on before a seat it stayed on
  there, and could not be turned on there (the stick up is never a button in
  a seat), while on the stick's click it worked. R UP is BULLET TIME's
  button in a seat too; the stick's other actions keep "never in a seat".
- The magazine in hand: held as the reload animation holds it, it follows
  the drawn wrist every frame (the fingers are posed round it there).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
frame = read("port/linux/src/vr_frame.c")
menu = read("port/linux/game/vr_menu.c")
vr_h = read("port/linux/src/vr.h")
bullet = read("port/linux/game/vr_bullet_time.c")
reload = read("port/linux/game/vr_manual_reload.c")

# ---- the BUTTONS rows' letters, left-handed
assert "int vr_buttons_mirrored(void);" in vr_h
assert "int vr_buttons_mirrored(void)\n{\n\treturn vr.buttons_mirrored;\n}" in frame
label = menu[menu.index("static char const *vr_menu_value_label("):]
label = label[:label.index("\n}\n")]
assert "setting->type != _vr_setting_button || !vr_buttons_mirrored()" in label
for logical, physical in (("a", "X"), ("b", "Y"), ("x", "A"), ("y", "B")):
    assert 'if (!strcmp(value, "%s")) return "%s";' % (logical, physical) in label
# every place a button row names its choice goes through it
for use in ("vr_menu_value_label(setting, vr_remap.value)", "vr_menu_value_label(setting, vr_menu_button_value(setting, source))"):
    assert use in menu, use
assert "setting->values[vr_remap.value].label" not in menu
assert "candidate = vr_menu_value_label(setting, vr_remap.value);" in menu
# the binding saved is unchanged: the rows' values are still the logical sources
assert '{ "JUMP", "vr.button_jump", _vr_setting_button, 10, { { "A", "a" }, { "B", "b" }, { "X", "x" }, { "Y", "y" },' in menu

# ---- back is the right controller's B
assert "back_down = (vr.frame.hand_buttons[1] & HALO_XR_HAND_EAST) != 0;" in frame
assert "unsigned int back = HALO_XR_BUTTON_B;" in frame
assert "vr.buttons_mirrored ? HALO_XR_BUTTON_Y : HALO_XR_BUTTON_B" not in frame
assert "hand_buttons[vr.buttons_mirrored ? 0 : 1] & HALO_XR_HAND_EAST" not in frame

# ---- BULLET TIME's R UP in a seat
assert "vr.turn_stick_up = !vr.seated &&" in frame  # its other actions: never in a seat
held = frame[frame.index("int source = vr.button_source[VR_BUTTON_ACTION_BULLET_TIME];"):]
held = held[:held.index("}")]
assert "vr.bullet_stick_up = fabsf(vr.frame.thumb[2]) < 0.6f &&" in held and "seated" not in held
assert "source == VR_BUTTON_SOURCE_RIGHT_STICK_UP ? vr.bullet_stick_up : touch_source_down(source, right, left)" in held
assert "int bullet_stick_up;" in frame
# the feature itself is unchanged (allowed, toggled, eased as before)
assert "static boolean vr_bullet_time_allowed(void)" in bullet and "seated" not in bullet.split("vr_bullet_time_allowed(void)")[1].split("}")[0]
assert "bullet.toggled = !bullet.toggled;" in bullet and "PIN(scale, 0.2f, 0.8f)" in bullet

# ---- the magazine in hand
hold = reload[reload.index("static void reload_hold(real_matrix4x3 const *hand_matrix)"):]
hold = hold[:hold.index("\n}\n")]
assert "reload.held_authored && reload.state.phase == VR_MR_NEW_HELD && vr_render_reload_grip(0, &authored)" in hold
assert "matrix4x3_multiply(hand_matrix, &reload.attachment, &reload.held);" in hold
assert reload.count("reload_hold(") == 4  # its definition and the three places a held magazine is posed
assert reload.count("reload.held_authored = TRUE;") == 2 and reload.count("reload.held_authored = FALSE;") == 2

print("PASS: Test72 left hand: BUTTONS rows by the physical letter (bindings unchanged), back on B, "
      "BULLET TIME's R UP in seats, the held magazine on the drawn wrist")
