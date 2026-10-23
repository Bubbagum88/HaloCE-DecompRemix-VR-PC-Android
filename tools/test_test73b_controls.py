"""Test73b: the launchers' CONTROLS (the owner: "a controls section, one where you can click, it'll give you the actual
proper mappings. For each controller type ... with the different options enabled, what can change certain mappings
... You can select like what controller type you're using").

One file, port/android/app/src/main/assets/controls/controllers.txt, a page per controller and what every page of its
kind shows; the Android launcher shows it (ControlsText.java parses it, ControlsGuide.java draws it as What's New is,
this device's controller first) and the PC launcher embeds and shows it (desktop_launcher.c page_controls, its own
parser). Checked here:
1. the file's form (its headers, the pages each launcher lists, What's New's line kinds, a font's characters);
2. what it says against the code it describes: the Quest's default buttons (vr_frame.c button_defaults), the other
   controllers' fixed layout (layout_controls), each controller's bindings (halo_xr_bindings.h), the keyboard's
   defaults (port_config.c), the gamepad's (xinput_sdl.c), the touch screen's circles (TouchControls.java), MOVEMENT;
3. ControlsText run with javac, the PC launcher's parser compiled and run on the real file, with negative controls;
4. the wiring: the launchers' buttons, the PC page, the file embedded for the PC.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8')
CONTROLS = 'port/android/app/src/main/assets/controls/controllers.txt'
text = read(CONTROLS)
frame = read('port/linux/src/vr_frame.c')
bindings = read('port/android/include/halo_xr_bindings.h')
config = read('port/linux/src/port_config.c')
xinput = read('port/linux/src/xinput_sdl.c')
touch = read('port/android/app/src/main/java/com/halo/decomp/TouchControls.java')
launcher = read('port/linux/src/desktop_launcher.c')
activity = read('port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java')
guide = read('port/android/app/src/main/java/com/halo/decomp/ControlsGuide.java')
embed = read('tools/embed_assets.py')
movement = read('port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.movement.xml')
JAVA = ROOT / 'port/android/app/src/main/java/com/halo/decomp'

# ---------- 1. the file's form
assert '\r' not in text and '\t' not in text
for character in set(text):
    assert ord(character) < 128 or character == '•', repr(character)  # (the launchers' fonts: ASCII and the bullet)
pages = []  # (label, kind, places, body lines)
for line in text.split('\n'):
    if line.startswith('#'):
        continue
    if line.startswith('== '):
        fields = [field.strip() for field in line[3:].split('|')]
        assert len(fields) == 3, line
        assert fields[1] in ('vr', 'flat') and set(fields[2].split()) <= {'quest', 'phone', 'pc'}, line
        pages.append((fields[0], fields[1], fields[2].split(), []))
        continue
    assert pages or not line.strip(), line
    if pages:
        pages[-1][3].append(line)


def listed(where):
    return [label for label, kind, places, body in pages if where in places and label != '*']


assert listed('quest') == ['QUEST (TOUCH)', 'PICO', 'STEAM FRAME'], listed('quest')
assert listed('phone') == ['TOUCH SCREEN', 'GAMEPAD', 'KEYBOARD + MOUSE'], listed('phone')
assert listed('pc') == ['QUEST (TOUCH)', 'PICO', 'STEAM FRAME', 'VALVE INDEX', 'HP REVERB G2', 'OTHER PC VR', 'GAMEPAD',
                        'KEYBOARD + MOUSE'], listed('pc')  # (the PC page's two rows of four)
for label, kind, places, body in pages:
    assert len(label) <= 18, label  # (the PC page's buttons)
    if label == '*':
        continue
    for where in places:  # (each kind's shared page, where its pages are)
        assert [p for p in pages if p[0] == '*' and p[1] == kind and where in p[2]], (label, where)
shared = {kind: [p for p in pages if p[0] == '*' and p[1] == kind] for kind in ('vr', 'flat')}
assert len(shared['vr']) == 1 and len(shared['flat']) == 1
page = {label: '\n'.join(body) for label, kind, places, body in pages if label != '*'}
vr_all = '\n'.join(shared['vr'][0][3])
flat_all = '\n'.join(shared['flat'][0][3])
for label, kind, places, body in pages:
    lines = [line for line in body if line.strip()]
    assert lines, label
    if label != '*':
        assert not re.search('[a-z]', lines[0]), (label, lines[0])  # (its title)
    else:
        assert not re.search('[a-z]', lines[0]) and not lines[0].startswith('•')  # (a heading under the page)
    for line in lines:
        assert not line.startswith(('-', '*', ' ')), (label, line)
        if '•' in line:
            assert line.startswith('• ') and line.count('•') == 1, (label, line)

# ---------- 2. what it says, against the code
# the Quest's remappable defaults (button_defaults: jump, action, melee, crouch, switch weapon, grenade, switch
# grenade, reticle, push to talk, bullet time)
assert ('VR_BUTTON_SOURCE_A, VR_BUTTON_SOURCE_B, VR_BUTTON_SOURCE_RIGHT_STICK, VR_BUTTON_SOURCE_RIGHT_STICK_DOWN,\n'
        '\tVR_BUTTON_SOURCE_Y, VR_BUTTON_SOURCE_X, VR_BUTTON_SOURCE_HOLD, VR_BUTTON_SOURCE_LEFT_STICK,\n'
        '\tVR_BUTTON_SOURCE_NONE, VR_BUTTON_SOURCE_RIGHT_STICK_UP') in frame
quest = page['QUEST (TOUCH)']
for words in ('A (right, lower): JUMP.', 'B (right, upper): USE / RELOAD', 'X (left, lower): GRENADE: a tap throws one, '
              'a hold of half a second switches grenades.', 'Y (left, upper): NEXT WEAPON.', 'Held down: CROUCH.',
              'Pushed up: BULLET TIME (offline).', 'Menu (left): pause.', 'Both stick clicks together: recentre',
              "Right stick's click: ZOOM while your hands do the melee", 'VR SETTINGS > BUTTONS'):
    assert words in quest, words
assert 'vr.touch_layout = strstr(vr.info.system, "Quest") != NULL;' in frame  # (the Quest's layout: a Quest's alone)
assert 'if (!vr.touch_layout || vr.seated || !physical_melee_allowed())' in frame  # (the stick's zoom, seated not)
assert 'buttons |= touch_buttons(right, left, seconds, &grenade_down);\n\t\tleft &= ~HALO_XR_HAND_EAST;' in frame
assert 'recentre' not in quest.split('Y (left, upper)')[1].split('\n')[0]  # (the Quest's Y never recentres)
# the other controllers' fixed layout
layout = function(frame, 'layout_controls')
for line in ('if (right & HALO_XR_HAND_SOUTH) buttons |= HALO_XR_BUTTON_A;           /* jump */',
             'if (right & HALO_XR_HAND_EAST) buttons |= HALO_XR_BUTTON_X;            /* action, reload */',
             'if (right & HALO_XR_HAND_WEST) buttons |= HALO_XR_BUTTON_BLACK;        /* switch grenades */',
             'if (right & HALO_XR_HAND_NORTH) buttons |= HALO_XR_BUTTON_Y;           /* switch weapons */',
             'buttons |= HALO_XR_BUTTON_B;                                        /* melee (and the swing) */',
             'if ((left & (HALO_XR_HAND_VIEW | HALO_XR_HAND_EAST)))', 'if (vr.view_held >= 1.0 && !vr.view_recentred)',
             'buttons |= HALO_XR_BUTTON_WHITE;                                    /* flashlight, the off hand\'s */',
             'vr.pad_trigger[0] = (vr.frame.hand_buttons[vr.weapon_hand] & HALO_XR_HAND_BUMPER) ? 1.0f : 0.0f;',
             'if (vr.button_sprint_enabled && !vr.seated)', 'vr.push_to_talk_held = vr.touch_layout &&',
             '(!vr.touch_layout ? vr.bullet_stick_up :'):
    assert line in layout, line
assert 'vr_button_sprint_input_mode(vr.button_sprint_enabled && vr.layout_vr,' in frame
for label in ('PICO', 'VALVE INDEX', 'HP REVERB G2'):
    body = page[label]
    for words in ('(right, lower): JUMP.', '(right, upper): USE / RELOAD.', 'GRENADE: a tap throws one, a hold of half a '
                  'second switches grenades. With WEAPONS: LOCKED it switches grenades.', 'a press is BACK',
                  'Held a second, it recentres.', 'NEXT WEAPON: draw another from a holster',
                  "CROUCH, while BUTTON SPRINT has the left stick's click", 'Pushed up: BULLET TIME (offline).',
                  "The other hand's trigger: ZOOM."):
        assert words in body, (label, words)
frame_page = page['STEAM FRAME']
for words in ('A: JUMP.', 'B: USE / RELOAD.', 'X: NEXT GRENADE.', 'Y: NEXT WEAPON.', "Right bumper (the gun hand's): "
              'throw a GRENADE.', "Left bumper (the other hand's): FLASHLIGHT.", 'View (left): a press is BACK',
              'Menu (right): pause.', 'The d-pad does nothing in this layout', 'MIRROR CONTROLS: OFF and MIRROR '
              'BUTTONS: OFF'):
    assert words in frame_page, words
assert 'HALO_XR_HAND_DPAD' not in frame  # (the VR layout leaves the Frame's d-pad alone)
assert 'vr.buttons_mirrored = vr.controls_mirrored ||' in frame
# each controller's bindings, as the pages name the buttons
def table(name):
    return bindings[bindings.index('static const struct binding %s[] =' % name):].split('};')[0]


for name, expected in (('halo_xr_bindings_touch', ('_action_hand_menu, "/user/hand/left/input/menu/click"',
                                                   '_action_hand_east, "/user/hand/left/input/y/click"')),
                       ('halo_xr_bindings_pico', ('_action_hand_menu, "/user/hand/left/input/menu/click"',
                                                  '_action_hand_south, "/user/hand/left/input/x/click"')),
                       ('halo_xr_bindings_hp', ('_action_hand_menu, "/user/hand/left/input/menu/click"',
                                                '_action_hand_east, "/user/hand/left/input/y/click"')),
                       ('halo_xr_bindings_index', ('_action_hand_menu, "/user/hand/left/input/system/click"',
                                                   '_action_hand_south, "/user/hand/left/input/a/click"',
                                                   '_action_hand_east, "/user/hand/left/input/b/click"',
                                                   '_action_x, "/user/hand/left/input/a/click"',
                                                   '_action_y, "/user/hand/left/input/b/click"')),
                       ('halo_xr_bindings_frame', ('_action_hand_west, "/user/hand/right/input/x/click"',
                                                   '_action_hand_north, "/user/hand/right/input/y/click"',
                                                   '_action_hand_menu, "/user/hand/right/input/menu/click"',
                                                   '_action_hand_view, "/user/hand/left/input/view/click"',
                                                   '_action_back, "/user/hand/left/input/view/click"',
                                                   '_action_white, "/user/hand/left/input/bumper/click"',
                                                   '_action_black, "/user/hand/right/input/bumper/click"'))):
    for binding in expected:
        assert binding in table(name), (name, binding)
assert '_action_back' not in table('halo_xr_bindings_touch') + table('halo_xr_bindings_index') + \
    table('halo_xr_bindings_pico') + table('halo_xr_bindings_hp')  # (XBOX's View: the Frame's alone)
for words in ('CONTROLS: XBOX', "the Index's left A and B are X and Y", "Steam Frame's bumpers are the flashlight and "
              'next grenade, its View back', "BUTTON SPRINT is the VR layout's only", 'TOGGLE (the default since Test73b',
              "the Quest's BUTTONS page gives it; with the other controllers, use OPEN MIC"):
    assert words in vr_all, words
assert '{ "vr.button_sprint_toggle", _config_boolean, "true",' in config
# the keyboard's defaults
keys = dict(re.findall(r'\{ "controls\.(\w+)", _config_string, "\\"([^"\\]*)\\""', config))
expected_keys = {
    'move_forward': ('W', 'W, A, S, D: move.'), 'move_backward': ('S', 'W, A, S, D: move.'),
    'strafe_left': ('A', 'W, A, S, D: move.'), 'strafe_right': ('D', 'W, A, S, D: move.'),
    'jump': ('Space', 'Space: JUMP.'), 'crouch': ('Left Ctrl, C', 'Left Ctrl or C: CROUCH.'),
    'fire': ('Mouse Left', 'Left mouse: FIRE.'), 'throw_grenade': ('Mouse Right, G', 'Right mouse or G: throw a GRENADE.'),
    'melee': ('F, Mouse 4', 'F or mouse 4: MELEE.'), 'reload': ('R', 'R: RELOAD.'),
    'zoom': ('Z, Mouse Middle', 'Z or the middle mouse: ZOOM.'), 'switch_weapon': ('Wheel, 1', 'Wheel or 1: NEXT WEAPON.'),
    'switch_grenade': ('X', 'X: NEXT GRENADE.'), 'action': ('E', 'E: USE (pick up, get in).'),
    'flashlight': ('Q', 'Q: FLASHLIGHT.'), 'scoreboard': ('Tab', 'Tab: the scoreboard.'), 'pause': ('Escape', 'Escape: pause.'),
    'screenshot': ('F10', 'F10: a screenshot.'), 'push_to_talk': ('V', 'V: push to talk.'),
    'third_person': ('Keypad Enter', 'Keypad Enter: the third-person camera'),
    'free_look': ('Left Alt, Right Alt', 'hold Alt to look around it'), 'chat': ('T', 'T: chat.'),
    'team_chat': ('Y', 'Y: team chat.'), 'sprint': ('Left Shift', 'Left Shift: SPRINT'),
}
assert set(keys) == set(expected_keys), set(keys) ^ set(expected_keys)
keyboard = page['KEYBOARD + MOUSE']
for key, (default, words) in expected_keys.items():
    assert keys[key] == default, (key, keys[key])
    assert words in keyboard, words
# the gamepad's (the Xbox pad the game reads: input_abstraction.c's)
for line in ('merge_button(pad, XINPUT_GAMEPAD_A, SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_SOUTH));',
             'merge_button(pad, XINPUT_GAMEPAD_WHITE, SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_LEFT_SHOULDER));',
             'merge_button(pad, XINPUT_GAMEPAD_BLACK, SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER));',
             '{ SDL_GAMEPAD_BUTTON_LEFT_STICK, XINPUT_GAMEPAD_LEFT_THUMB },'):
    assert line in xinput, line
assert ('buttons do (input_abstraction.c): A jump, B melee, X action and reload,\nY switch weapons, white flashlight, '
        'black switch grenades, left trigger\ngrenade, right trigger fire, left stick crouch, right stick zoom') in frame
gamepad = page['GAMEPAD']
for words in ('A: JUMP. B: MELEE. X: reload; hold to use, pick up or get in. Y: NEXT WEAPON.',
              'Left bumper: FLASHLIGHT. Right bumper: NEXT GRENADE.', 'Left trigger: throw a GRENADE. Right trigger: FIRE.',
              "Left stick: move; its click: CROUCH. Right stick: look; its click: ZOOM.", 'choose AUTO'):
    assert words in gamepad, words
# the touch screen's circles
screen = page['TOUCH SCREEN']
circles = re.findall(r'new Control\("([^"]+)"', touch)
assert {'^', 'v', '<', '>'} <= set(circles) and 'The arrows: the d-pad.' in screen
for label in circles:
    if label not in ('^', 'v', '<', '>'):
        assert label in screen, label
assert 'shown while SPRINT is HOLD or TOGGLE' in screen
# MOVEMENT (the flat builds')
for setting, words in (('movement.sprint', 'SPRINT: OFF (default), HOLD, TOGGLE or AUTO.'),
                       ('movement.sprint_speed', 'SPRINT SPEED'), ('movement.slide', 'SLIDE'),
                       ('movement.parkour_wallrun', 'WALL RUN'), ('movement.parkour_walljump', 'WALL JUMP')):
    assert 'setting="%s"' % setting in movement and words in flat_all, setting

# ---------- 3a. ControlsText (javac)
JAVA_CHECK = r'''package com.halo.decomp;
import java.nio.file.*;
import java.util.*;
public final class ControlsCheck {
 static int checks;
 static void check(boolean ok, String message) { checks++; if (!ok) throw new AssertionError(message); }
 static List<String> labels(ControlsText text) { List<String> out = new ArrayList<>(); for (ControlsText.Page page : text.pages()) out.add(page.label); return out; }
 public static void main(String[] args) throws Exception {
  String file = new String(Files.readAllBytes(Paths.get(args[0])), "UTF-8");
  ControlsText quest = new ControlsText(file, "quest"), phone = new ControlsText(file, "phone"), pc = new ControlsText(file, "pc");
  check(labels(quest).equals(Arrays.asList("QUEST (TOUCH)", "PICO", "STEAM FRAME")), "the VR app's: " + labels(quest));
  check(labels(phone).equals(Arrays.asList("TOUCH SCREEN", "GAMEPAD", "KEYBOARD + MOUSE")), "the phone's: " + labels(phone));
  check(labels(pc).size() == 8 && labels(pc).get(3).equals("VALVE INDEX"), "the PC's: " + labels(pc));
  for (int index = 0; index < quest.pages().size(); index++) {
   String text = quest.text(index);
   check(text.startsWith(quest.pages().get(index).text) && text.contains("\n\nEVERY VR CONTROLLER: HANDS AND GESTURES\n"), "the VR pages' shared block");
   check(!text.contains("\n#") && !text.startsWith("#") && !text.contains("== ") && !text.endsWith("\n"), "no notes, headers or trailing lines");
  }
  check(phone.text(0).contains("\n\nMOVEMENT SETTINGS") && !phone.text(0).contains("EVERY VR CONTROLLER"), "the flat pages' shared block");
  check(quest.text(-1).isEmpty() && quest.text(99).isEmpty(), "no such page");
  // this device's first
  check(quest.pages().get(ControlsText.first(quest.pages(), true, false, "Oculus")).label.equals("QUEST (TOUCH)"), "a Quest");
  check(quest.pages().get(ControlsText.first(quest.pages(), true, false, "PICO")).label.equals("PICO"), "a PICO");
  check(quest.pages().get(ControlsText.first(quest.pages(), true, true, "Valve")).label.equals("STEAM FRAME"), "the Frame");
  check(phone.pages().get(ControlsText.first(phone.pages(), false, false, "Samsung")).label.equals("TOUCH SCREEN"), "a phone");
  check(ControlsText.first(new ArrayList<>(), true, false, null) == 0, "none");
  // a file read with Windows line ends, an unreadable one, a header short of its fields
  check(labels(new ControlsText(file.replace("\n", "\r\n"), "quest")).equals(labels(quest)), "CRLF");
  check(new ControlsText("", "quest").pages().isEmpty() && new ControlsText(null, "pc").pages().isEmpty(), "nothing read");
  check(new ControlsText("== BROKEN\nTEXT\n== OK | vr | pc\nOK PAGE\n", "pc").pages().size() == 1, "a broken header skipped");
  System.out.println("ok " + checks);
 }
}
'''

javac = shutil.which('javac')
assert javac, 'javac'
with tempfile.TemporaryDirectory(prefix='test73b-controls-java-') as work:
    package = Path(work, 'com/halo/decomp')
    package.mkdir(parents=True)
    (package / 'ControlsCheck.java').write_text(JAVA_CHECK, encoding='utf-8')
    subprocess.run([javac, '-d', work, str(JAVA / 'ControlsText.java'), str(package / 'ControlsCheck.java')], check=True)
    run = subprocess.run(['java', '-cp', work, 'com.halo.decomp.ControlsCheck', str(ROOT / CONTROLS)],
                         capture_output=True, text=True)
    assert run.returncode == 0 and run.stdout.startswith('ok'), run.stdout + run.stderr

# ---------- 3b. the PC launcher's parser, compiled
PARSER = '\n'.join(function(launcher, name) for name in ('controls_field', 'controls_pages', 'controls_compose'))
assert '#define CONTROLS_PAGES 16' in launcher
STRUCT = launcher[launcher.index('struct controls_page\n{'):launcher.index('};', launcher.index('struct controls_page\n{')) + 2]
C_CHECK = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CONTROLS_PAGES 16
''' + STRUCT + '\n#include "parser.inc"\n' + r'''
int main(int argc, char **argv)
{
    static char file[1 << 20];
    struct controls_page pages[CONTROLS_PAGES], common[2];
    FILE *in = fopen(argv[1], "rb");
    size_t size = fread(file, 1, sizeof(file) - 1, in);
    int count, index;
    file[size] = 0;
    fclose(in);
    count = controls_pages(file, argv[2], pages, CONTROLS_PAGES, common);
    for (index = 0; index < count; index++)
        printf("PAGE %s|%d\n", pages[index].label, pages[index].vr);
    for (index = 0; index < count; index++)
    {
        char *text = controls_compose(&pages[index], common);
        printf("TEXT %d\n%s\nEND\n", index, text);
        free(text);
    }
    return 0;
}
'''


def parse(parser, where):
    compiler = shutil.which('clang') or shutil.which('cc')
    with tempfile.TemporaryDirectory(prefix='test73b-controls-c-') as work:
        Path(work, 'parser.inc').write_text(parser)
        Path(work, 'controls.c').write_text(C_CHECK)
        built = subprocess.run([compiler, '-std=gnu11', '-Wall', '-Werror', '-Wno-unused-function', '-fsanitize=address,undefined',
                                '-I', work, str(Path(work, 'controls.c')), '-o', str(Path(work, 'controls'))],
                               capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        result = subprocess.run([str(Path(work, 'controls')), str(ROOT / CONTROLS), where], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        labels = re.findall(r'^PAGE (.*)\|(\d)$', result.stdout, re.M)
        texts = re.findall(r'^TEXT \d+\n(.*?)\nEND$', result.stdout, re.M | re.S)
        return labels, texts


labels, texts = parse(PARSER, 'pc')
assert [label for label, vr in labels] == listed('pc'), labels
assert [vr for label, vr in labels] == ['1'] * 6 + ['0'] * 2
for (label, vr), composed in zip(labels, texts):
    assert composed.startswith('\n'.join(line for line in page[label].split('\n')).rstrip('\n') + '\n\n'), label
    assert composed.rstrip('\n').endswith((vr_all if vr == '1' else flat_all).rstrip('\n')), label
    assert '\n#' not in composed and '== ' not in composed and not composed.endswith('\n\n\n'), label
labels, texts = parse(PARSER, 'phone')
assert [label for label, vr in labels] == listed('phone')
# (negative controls: every page listed whatever its places; no shared page after it)
labels, texts = parse(mutated(PARSER, 'if (word && word == strlen(where) && !strncmp(places, where, word))',
                              'if (word)'), 'pc')
assert 'TOUCH SCREEN' in [label for label, vr in labels]
labels, texts = parse(mutated(PARSER, 'open = &common[vr];', 'open = NULL;'), 'pc')
assert 'EVERY VR CONTROLLER: HANDS AND GESTURES' not in texts[0] and 'EVERY VR CONTROLLER: HANDS AND GESTURES' in vr_all

# ---------- 4. the wiring
assert 'PAGE_CONTROLS };' in launcher and 'case PAGE_CONTROLS: page_controls(); break;' in launcher
assert 'if (button(840.0f, y, 360.0f, 56.0f, "CONTROLS", 1)) { ui.page = PAGE_CONTROLS; ui.focus = 0; ui.scroll = 0.0f; }' \
    in function(launcher, 'page_home')
controls_page = function(launcher, 'page_controls')
assert 'launcher_file_text("controls/controllers.txt")' in controls_page and 'controls_pages(file, "pc",' in controls_page
assert 'news_layout(text, top - ui.scroll, 1, top, bottom);' in controls_page
assert '"campaigns/altheros.properties", "controls/controllers.txt")' in embed
assert activity.count('menuButton(layout, "Controls: every button, for your controller").setOnClickListener(v -> '
                      'ControlsGuide.show(this));') == 2
assert 'activity.getAssets().open("controls/controllers.txt")' in guide and 'WhatsNew.styled(controls.text(chosen[0])' in guide
assert 'ControlsText.first(pages, where().equals("quest"), Lepton.running(), Build.MANUFACTURER)' in guide
print('PASS: CONTROLS: %d pages (the VR app %d, the phone %d, the PC %d) checked against the code they describe '
      '(the Quest\'s defaults, the other controllers\' layout, every binding, the keyboard\'s %d defaults, the gamepad, '
      'the touch screen\'s circles, MOVEMENT); the Android parser (javac) and the PC launcher\'s (clang, ASan) on the real '
      'file, 2 negative controls; the launchers\' buttons and the PC page wired' % (
          len(page), len(listed('quest')), len(listed('phone')), len(listed('pc')), len(expected_keys)))
