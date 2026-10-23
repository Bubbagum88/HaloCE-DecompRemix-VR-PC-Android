"""Test72: the VR menus' organisation (the owner's 2026-10-15 requests).

- BULLET TIME was on GAMEPLAY, whose first row is HAPTICS ("Gameplay >
  Haptics"): its rows (on/off, time scale, hold or toggle) are on
  LOCOMOTION with sprint, slide and the parkour rows (Locomotion / Parkour),
  and on IMMERSION's new LOCOMOTION topics. Its button stays on BUTTONS with
  the others' remapping (conflicts, NONE, the saved binding). Keys, values
  and the feature itself are unchanged.
- IMMERSION gains the toggles that were missing (BUTTON SPRINT, SPRINT
  TOGGLE, SLIDE and its options, BULLET TIME, TWO HANDS, SCOPE, the vehicles'
  VIEW); MOVEMENT is PARKOUR; BODY keeps the body's rows.
- SCOPES: one topic a weapon, named in full; rows FORWARD / UP / RIGHT /
  SIZE; each topic screen titled "PAGE: TOPIC" (wider than a row).
- MENU POSITION: head-locked (as before, the default), world or follow;
  distance, size and height; the same panel and pointer, placed as a menu
  opens and again on a stick click or a recentre.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
menu = read("port/linux/game/vr_menu.c")
frame = read("port/linux/src/vr_frame.c")
config = read("port/linux/src/port_config.c")


def page(name):
    text = menu[menu.index("static struct vr_menu_setting const %s[] =" % name):]
    return text[:text.index("};")]


macros = dict(re.findall(r"^#define (VR_IMMERSION_\w+) (\{.*\})$", menu, re.M))
gameplay, locomotion, immersion, hud, scopes = (page(n) for n in
    ("vr_menu_vr", "vr_menu_locomotion", "vr_menu_immersion", "vr_menu_hud", "vr_menu_scopes"))

# ---- BULLET TIME: out of GAMEPLAY, into LOCOMOTION and IMMERSION; its button on BUTTONS
for key in ("vr.bullet_time", "vr.bullet_time_scale", "vr.bullet_time_toggle"):
    assert key not in gameplay, key
    macro = next(name for name, row in macros.items() if '"%s"' % key in row)
    assert macro + "," in locomotion and macro + "," in immersion, key
assert macros["VR_IMMERSION_BULLET_TIME"] == '{ "BULLET TIME", "vr.bullet_time", _vr_setting_boolean, 2, { { "OFF", "false" }, { "ON", "true" } } }'
assert macros["VR_IMMERSION_BULLET_SCALE"] == '{ "TIME SCALE", "vr.bullet_time_scale", _vr_setting_real, 4, { { "25%", "0.25" }, { "40%", "0.4" }, { "50%", "0.5" }, { "65%", "0.65" } } }'
assert macros["VR_IMMERSION_BULLET_MODE"] == '{ "BULLET TIME MODE", "vr.bullet_time_toggle", _vr_setting_boolean, 2, { { "HOLD", "false" }, { "TOGGLE", "true" } } }'
buttons = page("vr_menu_buttons")
assert '{ "BULLET TIME", "vr.button_bullet_time", _vr_setting_button, 10,' in buttons
assert "vr.button_bullet_time" not in locomotion and "vr.button_bullet_time" not in immersion
for key, default in (("vr.bullet_time", '"true"'), ("vr.bullet_time_scale", '"0.4"'), ("vr.bullet_time_toggle", '"false"'),
                     ("vr.button_bullet_time", '"\\"right_stick_up\\""')):
    assert '{ "%s", _config_' % key in config and re.search(r'\{ "%s", _config_\w+, %s,' % (re.escape(key), re.escape(default)), config), key
# parkour on LOCOMOTION, not GAMEPLAY
for macro in ("VR_IMMERSION_WALLRUN", "VR_IMMERSION_WALLJUMP", "VR_IMMERSION_GRIP_CLIMB", "VR_IMMERSION_CLIMB_GRAB"):
    assert macro + "," in locomotion and macro + "," not in gameplay, macro
assert "VR_IMMERSION_HAPTICS," in gameplay

# ---- IMMERSION's topics and the missing toggles
sections = re.findall(r'\{ "([A-Z +]+)", (\d+) \}', menu[menu.index("vr_menu_immersion_sections[] ="):].split("};")[0])
labels = [label for label, _ in sections]
assert labels[labels.index("HOLSTER PLACES") + 1:labels.index("GRAB + NPCS")] == ["LOCOMOTION", "LOCOMOTION OPTIONS", "PARKOUR", "BODY"]
assert ("WEAPONS", "8") in sections and ("VEHICLE OPTIONS", "8") in sections and ("BODY", "4") in sections  # (Test73: + HAND LOCK)
for macro in ("VR_IMMERSION_BUTTON_SPRINT", "VR_IMMERSION_SPRINT_TOGGLE", "VR_IMMERSION_SLIDE", "VR_IMMERSION_BULLET_TIME",
              "VR_IMMERSION_TWO_HANDS", "VR_IMMERSION_SCOPE", "VR_IMMERSION_VEHICLE_VIEW", "VR_IMMERSION_JUMP_CANCELS"):
    assert immersion.count(macro + ",") == 1, macro
    rest = menu.replace(immersion, "")
    assert len(re.findall(r"\b%s," % macro, rest)) == 1, macro  # and once on its usual page

# ---- SCOPES: a topic a weapon, titled screens
assert '{ "FORWARD", "vr.scope_" #key "_forward"' in scopes and '{ "SIZE", "vr.scope_" #key "_scale"' in scopes
assert ' FWD"' not in scopes and ' RGT"' not in scopes
sections_scopes = menu[menu.index("vr_menu_scopes_sections[] ="):].split("};")[0]
names = re.findall(r'\{ "([A-Z ]+)", (\d+) \}', sections_scopes)
assert [n for n, _ in names] == ["PISTOL", "SNIPER RIFLE", "ROCKET LAUNCHER", "OTHER WEAPONS", "PLASMA PISTOL", "ASSAULT RIFLE",
                                 "PLASMA RIFLE", "SHOTGUN", "NEEDLER", "FUEL ROD GUN", "FLAMETHROWER", "RESET"], names
profiles = read("port/linux/src/vr_scope_profiles.h")
order = re.findall(r"X\((\w+),", profiles)
assert order == ["pistol", "sniper", "rocket_launcher", "other", "plasma_pistol", "assault_rifle", "plasma_rifle",
                 "shotgun", "needler", "fuel_rod", "flamethrower"], order  # the names above follow this order
assert "NUMBEROF(vr_menu_scopes_sections) == VR_SCOPE_PROFILE_COUNT + 1" in menu
assert '{ "SCOPES", vr_menu_scopes, NUMBEROF(vr_menu_scopes),\n\t\tvr_menu_scopes_sections, NUMBEROF(vr_menu_scopes_sections) },' in menu
assert 'vr_menu.navigation[slot].jump = 4;' in menu and '"%s: %s"' in menu
assert "vr_menu_widget_get(title)->bounds.x1 = 512;" in menu
assert "if (vr_menu_pages[page].sections && vr_menu_pages[page].section_count > 0)\n            vr_menu.navigation_capacity += screens;" in menu
assert menu.count("vr_menu.screen_title_tag_index = NONE;") >= 3  # unload, load, after each screen

# ---- MENU POSITION
assert '{ "vr.menu_anchor", _config_string, "\\"head\\""' in config
for key, default in (("vr.menu_distance", "1.6"), ("vr.menu_scale", "1.0"), ("vr.menu_height", "0.0")):
    assert '{ "%s", _config_real, "%s"' % (key, default) in config, key
assert '{ "MENU POSITION", "vr.menu_anchor", _vr_setting_string, 3, { { "HEAD", "head" }, { "WORLD", "world" }, { "FOLLOW", "follow" } } },' in hud
pose = frame[frame.index("static int menu_world_pose(void)\n{"):]  # (the definition, not its prototype)
pose = pose[:pose.index("\n}\n")]
assert "(vr.frame.flags & HALO_XR_FRAME_RECENTRED)" in pose and "HALO_XR_HAND_STICK" in pose
assert "if (!vr.menus_active || vr.mode != VR_MODE_STEREO || !anchor)" in pose
assert "now - vr.menu_away_since >= 750.0" in pose
assert "if (vr.mode == VR_MODE_STEREO && menu_world_pose())" in frame and "screen = vr.menu_pose;" in frame
assert "layers.quad_pose = vr.menu_pose;" in frame
assert "vr.menu_placed = 0; /* Test72: the next menu is put in front anew */" in frame
# head-locked stays as it was
assert "layers.flags |= HALO_XR_LAYER_QUAD | HALO_XR_LAYER_QUAD_HEAD_LOCKED | HALO_XR_LAYER_QUAD_ALPHA;" in frame

print("PASS: Test72 menus: BULLET TIME on LOCOMOTION and IMMERSION (its button on BUTTONS), parkour on LOCOMOTION, "
      "IMMERSION's missing toggles, SCOPES a weapon a topic with titled screens, MENU POSITION head/world/follow")
