"""Test72: the flat builds' movement extras (Android, Windows, Linux).

The owner: "for the flat/android ports see about adding the parkour features
to them alongside slide, sprint with toggle options ... those seem to not need
to be VR exclusive", and "wall grab wouldnt really be there of course".

- port/linux/game/flat_movement.c, flat builds only: SPRINT (off, hold,
  toggle, auto), SLIDE, WALL RUN, WALL JUMP; the VR build's own modules are
  untouched and keep their vr.* settings.
- Only movement.* settings, scoped to the flat builds (_platform_flat), every
  move off by default; nothing that needs tracked hands.
- Hooks: the #else side of the VR hooks in bipeds.c and game_state.c.
- Input: a SPRINT key (controls.sprint, Left Shift) on flat Controls Setup;
  AUTO for gamepads and touch sticks.
- Settings: Player profile > MOVEMENT, flat builds only, the last item.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
flat = read("port/linux/game/flat_movement.c")
header = read("port/linux/game/flat_movement.h")
config = read("port/linux/src/port_config.c")
bipeds = read("source/units/bipeds.c")
state = read("source/saved games/game_state.c")
keyboard = read("port/linux/include/halo_keyboard.h")
xinput = read("port/linux/src/xinput_sdl.c")
menus = read("port/linux/game/menu_functions.c")
menu_files = read("port/linux/src/menu_files.c")
vr_slide = read("port/linux/game/vr_slide.c")
vr_parkour = read("port/linux/game/vr_parkour.c")

# --- flat builds only, its own settings, all of them declared and off by default
assert flat.lstrip().startswith("/*") and "\n#ifndef HALO_VR\n" in flat and flat.rstrip().endswith("#endif")
assert "#ifndef HALO_VR" in header
keys = set(re.findall(r'config_(?:boolean|real|string|integer)\("([a-z_.]+)"\)', flat))
assert keys and all(key.startswith("movement.") for key in keys), keys
declared = {}
for match in re.finditer(r'\{ "((?:movement|controls)\.[a-z_]+)", _config_(\w+), "((?:\\.|[^"\\])*)", "(\w+)", _environment_value,\s*(_platform_\w+)', config):
    declared[match.group(1)] = (match.group(2), match.group(3), match.group(5))
for key in keys:
    assert key in declared and declared[key][2] == "_platform_flat", key
for key in ("movement.slide", "movement.parkour_wallrun", "movement.parkour_walljump"):
    assert declared[key] == ("boolean", "false", "_platform_flat"), key
assert declared["movement.sprint"] == ("string", '\\"off\\"', "_platform_flat")
assert declared["controls.sprint"] == ("string", '\\"Left Shift\\"', "_platform_flat")
# the same tuning as the VR build's defaults
for flat_key, vr_key in (("movement.sprint_speed", "vr.sprint_speed"), ("movement.slide_momentum", "vr.slide_momentum"),
                         ("movement.slide_friction", "vr.slide_friction"), ("movement.slide_damage", "vr.slide_damage"),
                         ("movement.wallrun_speed", "vr.wallrun_speed"), ("movement.wallrun_duration", "vr.wallrun_duration"),
                         ("movement.walljump_scale", "vr.walljump_scale")):
    vr_default = re.search(r'\{ "%s", _config_real, "([^"]+)"' % re.escape(vr_key), config).group(1)
    assert float(declared[flat_key][1]) == float(vr_default), (flat_key, vr_key)
# the flat scope: every build without a headset, never the VR build
assert "_platform_flat = 16," in config
platforms = config[config.index("#if defined(HALO_ANDROID) && defined(HALO_VR)"):]
platforms = platforms[:platforms.index("#endif") + 6]
assert "#define CONFIG_PLATFORM (_platform_android | _platform_vr)\n" in platforms
for line in ("(_platform_android | _platform_flat)", "(_platform_desktop | _platform_web | _platform_flat)",
             "(_platform_windows | _platform_flat)", "(_platform_linux | _platform_flat)"):
    assert "#define CONFIG_PLATFORM " + line in platforms, line

# --- nothing that needs tracked hands, nothing on the network
for absent in ("vr_hand", "vr_interaction", "climb", "grip", "vr_head_view", "vr_active", "network_send"):
    assert absent not in flat, absent
assert "game_connection() != _game_connection_local" in flat  # sprint and slide: offline
assert "connection == _game_connection_network_server && network_coop_active()" in flat  # wall moves: a co-op host
assert "flat_local(" in flat and "player_get(player)->unit_index != unit_index" in flat  # the local player's own body

# --- the same kinematics as the VR build's
for shared in ("vr_slide_math.h", "vr_parkour_math.h", "vr_sprint_melee_math.h"):
    assert '#include "%s"' % shared in flat
for call in ("vr_slide_entry_speed(", "vr_slide_duration(", "vr_slide_step(", "vr_slide_impact_scale(",
             "vr_pk_runnable(", "vr_pk_blend_normal(", "vr_pk_wall_leap(", "vr_pk_bound(",
             "vr_sprint_scale_for_effort(", "vr_button_sprint_input_mode("):
    assert call in flat, call
assert '!strcmp(mode, "toggle")' in flat and '!strcmp(mode, "hold")' in flat and '!strcmp(mode, "auto")' in flat
assert "biped->unit.aiming_vector" in flat  # a wall jump goes the way the camera looks

# --- the VR build's modules are as they were (their own settings, no flat code)
for vr_source in (vr_slide, vr_parkour):
    assert '"movement.' not in vr_source and "flat_movement" not in vr_source
assert 'config_boolean("vr.slide")' in vr_slide and 'config_boolean("vr.parkour_wallrun")' in vr_parkour

# --- the hooks: VR's as before, flat's on the other side
for vr_call, flat_call in (("vr_parkour_velocity(physics->biped_index", "flat_movement_parkour_velocity(physics->biped_index"),
                           ("real sprint = vr_player_sprint_scale(biped_index);", "real sprint = flat_movement_sprint_scale(biped_index);"),
                           ("vr_slide_update(biped_index, &physics.forward", "flat_movement_slide_update(biped_index, &physics.forward")):
    at = bipeds.index(vr_call)
    between = bipeds[at:bipeds.index(flat_call)]
    assert "#else" in between and "#endif" not in between, vr_call
assert '#include "flat_movement.h"' in bipeds and '#include "flat_movement.h"' in state
assert state.count("flat_movement_reset();") == 2

# --- the SPRINT key and its row
# (Test73: OpenCE 232's CHAT and TEAM CHAT keys in the fork's TEXT CHAT's place, the camera's after them)
assert keyboard.index("HALO_KEYBOARD_TEAM_CHAT,") < keyboard.index("HALO_KEYBOARD_SPRINT,") < keyboard.index("NUMBER_OF_HALO_KEYBOARD_ACTIONS")
assert "HALO_KEYBOARD_TEXT_CHAT" not in keyboard
assert '"controls.chat", "controls.team_chat", "controls.third_person", "controls.free_look", "controls.sprint",' in xinput
assert "int platform_sprint_held(void)" in xinput and "bindings[HALO_KEYBOARD_SPRINT][slot]" in xinput
row = menus.index('{ "controls.sprint", L"SPRINT", 0 },')
assert menus.rfind("#ifndef HALO_VR", 0, row) > menus.rfind("#endif", 0, row)

# --- menus: flat/vr names; the MOVEMENT screen and its item
assert '#define MENU_HEADSET "flat"' in menu_files and '#define MENU_HEADSET "vr"' in menu_files
assert "names one that is not desktop, android, web, flat or vr" in menu_files
ce = ROOT / "port/assets/menus/ce"
screen = ET.parse(ce / "main_menu.settings_select.player_setup.player_profile_edit.movement.xml").getroot()
spinners = [w for w in screen if w.get("type") == "spinner"]
assert {w.get("setting") for w in spinners} == {k for k in declared if k.startswith("movement.")} - {"movement.slide_jump_cancel"}
for spinner in spinners:
    assert len(spinner.get("strings").split("|")) == len(spinner.get("values").split("|")), spinner.get("setting")
labels = [s.get("text") for s in screen.find("strings[@name='main_menu/settings_select/player_setup/player_profile_edit/movement/labels']")]
helps = [s.get("text") for s in screen.find("strings[@name='main_menu/settings_select/player_setup/player_profile_edit/movement/help_strings']")]
assert len(labels) == len(spinners) == 11 and len(helps) == 12 and helps[0] == ""
assert "ce/main_menu.settings_select.player_setup.player_profile_edit.movement.xml" in read("port/assets/menus/menus.json")
profile = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.xml")
assert ('<child widget="main_menu/settings_select/player_setup/player_profile_edit/about_item"/>\n'
        '\t\t<child widget="main_menu/settings_select/player_setup/player_profile_edit/movement_profile_item" platform="flat"/>') in profile
strings = read("port/assets/menus/ce/strings.xml")
# (Test73: OpenCE 244's lists name their map list after the name)
options = strings[strings.index('profile_edit/profile_edit_options"'):]
options = options[options.index('>') + 1:options.index("</strings>")]
assert options.count("<string ") == 11 and options.rstrip().endswith('<string text="MOVEMENT"/>')
print("PASS: Test72 flat movement: sprint/slide/wall run/wall jump on flat builds only, movement.* settings off by "
      "default (VR's tuning), VR modules untouched, SPRINT key, MOVEMENT screen")
