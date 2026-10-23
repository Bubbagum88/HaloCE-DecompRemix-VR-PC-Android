"""Test73, item 11 (the owner: "be sure the inputs/controls section in the launcher makes it clear in terms of ALL
controls/gestures/ like manual reload, flashlight, different controls that change based on different settings,
etc."): docs/CONTROLS-AND-OPTIONS.md, the launcher's Field guide > VR controls & settings (controls.txt), rewritten
as a reference of every control and gesture, sourced from the code, and shown as clean as What's New.

- Every row of the control pages (BUTTONS, LOCOMOTION, HEAD GESTURES, BODY, COMFORT, VOICE CHAT, the vehicles'
  DRIVING, VEHICLE OPTIONS and TURRET AIM, and CONTROLS' controls) is named, read from vr_menu.c's real tables
  compiled; the few tuning rows left to their pages are listed here, each with its reason. Nothing named is a row
  that does not exist.
- The default buttons are vr_frame.c's button_defaults and the PC keys port_config.c's controls.* defaults; the
  conditional rules (zoom with physical melee, L STICK CLICK, BUTTON SPRINT, MIRROR CONTROLS/BUTTONS, seated) are
  stated.
- generate-field-guide.py's launcher_text turns it into the launcher's notes form (title, headings in capitals,
  "• " points, no Markdown marks), every line of a kind WhatsNew.kind knows, and LauncherHelp shows it styled.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73-controls-guide'
OUT.mkdir(parents=True, exist_ok=True)
doc = (ROOT / 'docs/CONTROLS-AND-OPTIONS.md').read_text(encoding='utf-8')
menu = (ROOT / 'port/linux/game/vr_menu.c').read_text(encoding='utf-8')
frame = (ROOT / 'port/linux/src/vr_frame.c').read_text(encoding='utf-8')
config = (ROOT / 'port/linux/src/port_config.c').read_text(encoding='utf-8')
generator = (ROOT / 'tools/generate-field-guide.py').read_text(encoding='utf-8')
help_java = (ROOT / 'port/android/app/src/main/java/com/halo/decomp/LauncherHelp.java').read_text(encoding='utf-8')
assert '\r' not in doc and doc.startswith('# Controls and gestures (Test73)\n')

# ---------- the menu's rows, from its real tables (as tools/test_test73_features.py compiles them)
tables = menu[menu.index('enum\n{'):menu.index('/* a page of settings, opened')]
pages = menu[menu.index('/* a page of settings, opened'):menu.index('#define VR_MENU_PAGE_COUNT')]
pages += '#define VR_MENU_PAGE_COUNT ((long)NUMBEROF(vr_menu_pages))\n'
harness = r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef float real;
typedef int boolean;
typedef unsigned char byte;
typedef unsigned short word;
#define TRUE 1
#define FALSE 0
#define NONE (-1L)
#define NUMBEROF(a) (sizeof(a) / sizeof((a)[0]))
#include "port/linux/src/vr_scope_profiles.h"
static int config_boolean(char const *key) { (void)key; return 0; }
static double config_real(char const *key) { (void)key; return 0; }
static long config_integer(char const *key) { (void)key; return 0; }
static char const *config_string(char const *key) { (void)key; return ""; }
static int config_matches(char const *key, char const *text) { (void)key; (void)text; return 0; }
static int config_write_text(char const *key, char const *text) { (void)key; (void)text; return 1; }
static int config_write_boolean(char const *key, int on) { (void)key; (void)on; return 1; }
static int config_write_string(char const *key, char const *text) { (void)key; (void)text; return 1; }
static void vr_reload_settings(void) { }
static void platform_log(char const *format, ...) { (void)format; }
#include "port/linux/src/vr.h"
''' + tables + pages + r'''
int main(void)
{
	for (long page = 0; page < VR_MENU_PAGE_COUNT; page++)
	{
		long row = 0, sections = vr_menu_pages[page].sections ? vr_menu_pages[page].section_count : 1;
		for (long section = 0; section < sections; section++)
		{
			long count = vr_menu_pages[page].sections ? vr_menu_pages[page].sections[section].count : vr_menu_pages[page].count;
			for (long index = 0; index < count && row < vr_menu_pages[page].count; index++, row++)
				printf("%s\t%s\t%s\n", vr_menu_pages[page].label,
					vr_menu_pages[page].sections ? vr_menu_pages[page].sections[section].label : "",
					vr_menu_pages[page].settings[row].label);
		}
	}
	return 0;
}
'''
(OUT / 'rows.c').write_text(harness, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-DHALO_VR', '-w', '-fsanitize=address,undefined', '-I' + str(ROOT),
                '-I' + str(ROOT / 'port/linux/game'), str(OUT / 'rows.c'), '-lm', '-o', str(OUT / 'rows')], check=True)
rows = [line.split('\t') for line in subprocess.run([str(OUT / 'rows')], check=True, capture_output=True,
                                                    text=True).stdout.splitlines()]
labels = {label for _, _, label in rows}
# every row of these pages (or sections) is a control the guide names
WHOLE = {('BUTTONS', ''), ('LOCOMOTION', ''), ('HEAD GESTURES', ''), ('COMFORT', ''), ('VOICE CHAT', ''),
         ('VEHICLES', 'DRIVING'), ('VEHICLE OPTIONS', None)}
# the rows the guide leaves to their pages, each with its reason
LEFT = {
    # tuning numbers, not controls: the page shows them next to what they tune
    'NPC RIG SLOTS', 'BODY RETENTION', 'DEATH PHYSICS', 'DEATH FORCE', 'RAGDOLL RANGE', 'NPC RECOVERY',
    'IMPACT SPEED', 'IMPACT CAP', 'HAND CONTACT', 'POUCH SIZE', 'VOICE VOLUME', 'CONTACT VOLUMES', 'CONTACT LOG',
    'BODY', 'HANDS',
    # each pouch's and holster's place (out, up, back): moved where they sit, not how they are used
    'MAG HIP OUT', 'MAG HIP UP', 'MAG HIP BACK', 'MAG SHD OUT', 'MAG SHD UP', 'MAG SHD BACK',
    'GUN HIP OUT', 'GUN HIP UP', 'GUN HIP BACK', 'GUN SHD OUT', 'GUN SHD UP', 'GUN SHD BACK',
    'RESET CONTROLS',  # (named: "RESET CONTROLS is the first and the last row")
    'SMOOTH SPEED', 'SNAP ANGLE', 'VIGNETTE ON',  # (named under TURNING / COMFORT)
}
required = set()
for page, section, label in rows:
    if (page, section) in WHOLE or (page == 'VEHICLES' and section == 'VEHICLE OPTIONS') or page == 'CONTROLS':
        if label not in LEFT:
            required.add(label)
required |= {'ARMS FROM', 'FINGERS', 'ROOM-SCALE', 'CROUCH DEPTH', 'MELEE', 'MELEE SPEED', 'FIST REQUIRED',
             'THIRD PERSON', 'SCOPE', 'CUTSCENES', 'MENU POSITION', 'MENU DISTANCE', 'MENU SIZE', 'MENU HEIGHT',
             'AIM STEADY', 'HUD', 'HEAD TAP', 'CROSSHAIR', 'CROSSHAIR SIZE', 'OPACITY', 'WRIST HUD', 'TURRET AIM',
             'TURNING', 'VIGNETTE', 'MICROPHONE', 'PUSH TO TALK'}
assert required <= labels, sorted(required - labels)
missing = sorted(label for label in required if label not in doc)
assert not missing, missing
# a row the guide names in capitals is a row (or a page, section, or a button's name)
EXTRA = {'VR SETTINGS', 'MENU', 'A', 'B', 'X', 'Y', 'R UP', 'R DOWN', 'R STICK', 'L STICK', 'GRIP', 'NONE', 'OFF', 'ON',
         'AUTO', 'HOLD', 'TOGGLE', 'PHYSICAL', 'LOCKED', 'PHYSICAL + MP', 'AUTO LOCK', 'SQUEEZE', 'GRIP', 'TRIGGER',
         'LEFT', 'RIGHT', 'BOTH', 'IMPACT', 'SWING', '+ ONLINE', 'CANCEL', 'SWAP', 'CLEAR', 'BOTH', 'RESET CONTROLS',
         '(DEFAULT)', 'SMOOTH', 'SNAP', 'HEAD', 'LEFT HAND', 'RIGHT HAND', 'STICK', 'WORLD', 'FOLLOW',
         'FIRST PERSON', 'THIRD PERSON', 'LEVEL', 'HALF', 'VEHICLE', 'IMMERSIVE', '3D SCREEN', 'FLAT', 'VR', 'XBOX',
         'RETICLE', 'CROUCH', 'OPEN MIC', 'PC VR', 'TEST73', 'NPC', 'NPCS', 'HUD + RETICLE', 'MOVEMENT', 'PC', 'GAMEPLAY',
         'BODY', 'COMFORT', 'BUTTONS', 'LOCOMOTION', 'VOICE CHAT', 'CO-OP OPTIONS', 'VR INTERACTIONS', 'SCOPES',
         'SPRINT', 'SLIDE', 'WALL RUN', 'WALL JUMP', 'FUEL', 'MP', 'MAG', 'AMD', 'PVP', 'IMMERSIVE VEHICLE',
         'FORWARD', 'UP', 'SIZE', 'REACH', 'VIEW UP', 'FWD', 'HEIGHT', 'NEXT GRENADE', 'GRENADE', 'USE',
         'RELOAD', 'JUMP', 'NEXT WEAPON', 'BULLET TIME', 'MELEE SPEED OFF', 'CONTROLS', 'VIEW', 'DISTANCE'}
EXTRA |= {'CHARACTER', 'DEFAULT', 'ONLINE', 'SCREEN', 'HEAD GESTURES', 'F10', 'CONTROLS-HISTORY', 'AS SET'}
# (and every page's and section's name, from the same tables)
EXTRA |= {page for page, _, _ in rows} | {section for _, section, _ in rows if section}


def known(name):
    # (a row named with its value or its number: "CROUCH DEPTH 35", "WEAPONS PHYSICAL")
    name = re.sub(r'( \d+)+$', '', name)
    return (name in EXTRA or name in labels or any(name in label for label in labels) or
            any(name.startswith(label + ' ') and known(name[len(label) + 1:]) for label in labels))


unknown = sorted(name for name in set(re.findall(r'\b[A-Z][A-Z0-9+-]*(?: [A-Z0-9+-]+)*\b', doc))
                 if len(name) >= 2 and not known(name))
assert not unknown, 'the guide names these, which are no VR SETTINGS rows: %r' % unknown

# ---------- the default buttons, as vr_frame.c has them, and the rules that move them
defaults = frame[frame.index('static const int button_defaults[VR_BUTTON_ACTIONS] ='):]
defaults = re.findall(r'VR_BUTTON_SOURCE_\w+', defaults[:defaults.index('};')])
assert defaults == ['VR_BUTTON_SOURCE_A', 'VR_BUTTON_SOURCE_B', 'VR_BUTTON_SOURCE_RIGHT_STICK',
                    'VR_BUTTON_SOURCE_RIGHT_STICK_DOWN', 'VR_BUTTON_SOURCE_Y', 'VR_BUTTON_SOURCE_X',
                    'VR_BUTTON_SOURCE_HOLD', 'VR_BUTTON_SOURCE_LEFT_STICK', 'VR_BUTTON_SOURCE_NONE',
                    'VR_BUTTON_SOURCE_RIGHT_STICK_UP'], defaults  # (jump, use, melee, crouch, weapon, grenade, ...)
buttons = doc[doc.index('## Buttons (defaults)'):doc.index('## Changing a button')]
for said in ('A: jump', 'B: use and reload', 'X: a tap throws a grenade, a hold switches grenades', 'Y: next weapon',
             'Its click: the reticle on or off', 'Held down: crouch', 'Pushed up: BULLET TIME',
             'PUSH TO TALK has no button', 'Zoom: the right stick\'s click', 'Menu button: pause',
             'Recentre: both stick clicks together, or hold the left controller\'s upper face button', 'the stick clicks sound the horn'):
    assert said in buttons, said
# (zoom moves to the right stick's click with physical melee, nothing else on it: stick_zoom_active)
zoom = frame[frame.index('static int stick_zoom_active(void)'):]
zoom = zoom[:zoom.index('\n}\n')]
assert '!vr.touch_layout || vr.seated || !physical_melee_allowed()' in zoom
assert 'MELEE SPEED OFF moves zoom back to the other hand\'s trigger' in doc
for rule in ('MIRROR CONTROLS (AUTO)', 'MIRROR BUTTONS (AUTO)', 'L STICK CLICK: RETICLE (default) or CROUCH',
             'BUTTON SPRINT takes the left stick\'s click', 'GRENADE on GRIP: NEXT GRENADE cannot be HOLD',
             'WEAPONS PHYSICAL: the grip holds the gun'):
    assert rule in doc, rule
# the owner's examples: manual reload's steps and the flashlight
for step in ('B drops the magazine', 'HIP POUCH', 'SHOULDER POUCH', 'magazine well', 'charge the gun',
             'Shotgun: shells one by one', 'Needler: shake it to reload', 'MAG DEBRIS',
             'bring the other hand to the middle of your head', 'FLASHLIGHT: 20 cm'):
    assert step in doc, step
for key, metres in (('vr.flashlight_distance', '0.2'), ('vr.hud_tap_distance', '0.1'), ('vr.crouch_height', '0.35'),
                    ('vr.grenade_chest_down', '0.60'), ('vr.grenade_throw_scale', '1.5'), ('vr.melee_speed', '2.0'),
                    ('vr.combat_lunge_reach', '12.0'), ('vr.npc_grab_assist', '0.30'), ('vr.weapon_pull_reach', '3.0'),
                    ('vr.sprint_speed', '1.5')):
    assert re.search(r'\{ "%s", _config_real, "%s"' % (re.escape(key), re.escape(metres)), config), key
assert 'up to ±30 cm' in doc  # (test_test34_opence)

# ---------- the PC keys, as port_config.c's controls.* defaults
pc = doc[doc.index('## PC (flat): keyboard and mouse'):doc.index('## Android (flat)')]
WORDS = {'Mouse Left': 'left mouse', 'Mouse Right': 'right mouse', 'Mouse Middle': 'middle mouse', 'Wheel': 'wheel',
         'Left Alt': 'Alt', 'Right Alt': 'Alt'}
for action in ('move_forward', 'move_backward', 'strafe_left', 'strafe_right', 'jump', 'crouch', 'fire',
               'throw_grenade', 'melee', 'reload', 'zoom', 'switch_weapon', 'switch_grenade', 'action', 'flashlight',
               'scoreboard', 'pause', 'screenshot', 'push_to_talk', 'third_person', 'free_look', 'chat', 'team_chat',
               'sprint'):
    m = re.search(r'\{ "controls\.%s", _config_\w+, "\\"([^"\\]*)\\""' % action, config)
    assert m, action
    for key in m.group(1).split(', '):
        assert WORDS.get(key, key) in pc, (action, key)

# ---------- the launcher's form, and its page
# (the generator's function alone: the generator itself writes every guide when run)
start = generator.index('def launcher_text(markdown):')
body = generator.index('\n', start) + 1
end = re.search(r'^\S', generator[body:], re.M).start() + body
scope = {}
exec(generator[start:end], scope)
text = scope['launcher_text'](doc)
assert "if target=='controls.txt': text=launcher_text(text)" in generator
# (package-quest.py's checks of the bundled controls.txt: Test34's zoom input, Test41's holster haptics)
for marker in ('left trigger for right-handed play', 'reload and other haptics still follow the global'):
    assert marker in text, marker
    assert ('b"%s"' % marker) in (ROOT / 'tools/package-quest.py').read_text(encoding='utf-8'), marker
assert '**' not in text and '`' not in text and '\n## ' not in text and '\n- ' not in text
lines = text.split('\n')
assert lines[0] == 'Controls and gestures (Test73)'
headings = [l for l in lines[1:] if l and not l.startswith('• ') and not re.search('[a-z]', l)]
assert headings == [h[3:].upper() for h in re.findall(r'^## .*$', doc, re.M)], headings
points = [l for l in lines if l.startswith('• ')]
assert len(points) == len(re.findall(r'^- ', doc, re.M)) and len(points) >= 90
for point in points:
    assert '  ' not in point and len(point) <= 420, point
show = help_java[help_java.index('static void show(Activity activity) {'):]
assert 'if(files[index].equals("controls.txt")) page(activity,"VR controls & settings",content,true);' in show
assert 'text.setText(styled?WhatsNew.styled(content,(int)Math.ceil(text.getPaint().measureText("\\u2022 "))):content);' in help_java
print('PASS: the controls guide names all %d control rows of VR SETTINGS (%d left to their pages, each with its '
      'reason), the default buttons and PC keys as the code has them, the rules that move them, and reads as %d '
      'headings and %d points in the launcher' % (len(required), len(LEFT), len(headings), len(points)))
