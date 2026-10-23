"""Test73, item 10h (the owner, for the next release: "make it so all the vr features (manual reload, parkour, fist
combat, immersive vehicles, npc/wall grab, one hand heavies, etc.) are all enabled by default upon update. this
would be for everyone. of course, they can still go into the vr settings and change it back ... overwriting previous
settings in those areas").

Once (vr_initialize, vr.test73_features_applied, after the vehicle defaults' own migration), vr_menu_features_on
turns each VR feature on as VR SETTINGS does: its row's ON through the menu's own apply (vr_menu_apply, shared with
vr_menu_setting_change), so what each needs comes with it (IMMERSIVE VEHICLE the first-person seat, FIST COMBAT
impact melee, SLIDE a sprint, NPC GRAB its rigs and rescue...). The same features' defaults are on, for a fresh
config. Ways to play rather than features are left as they are (ARM RUN, BUTTON SPRINT's own row, SPRINT TOGGLE,
BULLET TIME MODE, GRIP GUIDE, TANK HATCH, the online switches).

Compiled and run (ASan): vr_menu.c's real settings tables, dependency resolver, vr_menu_apply and the migration, over
a stand-in config store holding a pre-update config (every feature off, the player's own third-person seat, swing
melee, 10 cm grab assist, crouch on the stick's click): every listed feature on afterwards, with its requirements;
every listed key has a row; the player's OFF after it is kept, and VR SETTINGS still turns things off as before.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_features'
menu = (ROOT / 'port/linux/game/vr_menu.c').read_text(encoding='utf-8')
config = (ROOT / 'port/linux/src/port_config.c').read_text(encoding='utf-8')
frame = (ROOT / 'port/linux/src/vr_frame.c').read_text(encoding='utf-8')
vr_h = (ROOT / 'port/linux/src/vr.h').read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


features = re.findall(r'"(vr\.[a-z_0-9]+)"', menu[menu.index('static char const *const vr_menu_update_features[] ='):
                                                    menu.index('};', menu.index('static char const *const vr_menu_update_features[] ='))])
assert len(features) == len(set(features)) and len(features) >= 45, features
# ---------- the owner's named ones are among them
for key in ('vr.manual_reload', 'vr.parkour_wallrun', 'vr.parkour_walljump', 'vr.parkour_climb', 'vr.assisted_combat',
            'vr.vehicle_handles', 'vr.npc_interaction', 'vr.world_interaction', 'vr.npc_one_hand_heavy',
            'vr.physical_grenades', 'vr.slide', 'vr.death_ragdolls',
            # (the owner, 2026-10-21: "make sure that includes mag debris as well": MAG DEBRIS)
            'vr.dropped_magazines'):
    assert key in features, key
# (MAG DEBRIS's ON brings MANUAL RELOAD, which it needs; MANUAL RELOAD's own ON comes first and leaves it alone)
assert '{ "ON", "vr.dropped_magazines=true;vr.manual_reload=true" }' in menu
assert features.index('vr.manual_reload') < features.index('vr.dropped_magazines')
# ---------- ways to play, not features: left alone
for key in ('vr.arm_run', 'vr.button_sprint', 'vr.button_sprint_toggle', 'vr.bullet_time_toggle',
            'vr.vehicle_grip_guide', 'vr.vehicle_tank_hatch', 'vr.physical_multiplayer', 'vr.melee_multiplayer'):
    assert key not in features, key
# ---------- their defaults are on (a fresh config)
for key in features:
    m = re.search(r'\{ "%s", _config_boolean, "(true|false)"' % re.escape(key), config)
    assert m and m[1] == 'true', key
assert '{ "vr.test73_features_applied", _config_boolean, "false",' in config
# ---------- once, after the vehicle defaults, before the settings are read
init = fn(frame, 'vr_initialize')
features_block = ('if (!config_boolean("vr.test73_features_applied"))\n\t{\n\t\tvr_menu_features_on();\n\t\t'
                  'config_write_boolean("vr.test73_features_applied", 1);\n\t}\n\t')
assert features_block in init
# (Test73b: SPRINT TOGGLE's one-time TOGGLE next, tools/test_test73b_sprint.py; both before the settings are read)
after_features = init[init.index(features_block) + len(features_block):]
assert after_features.startswith('/* Test73b (the owner: "I want the sprint button to have it on toggle')
assert after_features.index('vr.test73b_sprint_toggle_applied') < after_features.index('\tvr_reload_settings();')
assert init.index('config_vr_vehicle_defaults();') < init.index('vr_menu_features_on();')
assert 'void vr_menu_features_on(void);' in vr_h
# ---------- the menu's apply is the one path (a player's choice, the update's)
assert 'return vr_menu_apply(setting, value);\n}' in fn(menu, 'vr_menu_setting_change')

tables = menu[menu.index('enum\n{', menu.index('/* ---------- the settings')) if '/* ---------- the settings' in menu
              else menu.index('enum\n{'):menu.index('/* a page of settings, opened')]
pages = menu[menu.index('/* a page of settings, opened'):menu.index('#define VR_MENU_PAGE_COUNT')]
pages += '#define VR_MENU_PAGE_COUNT ((long)NUMBEROF(vr_menu_pages))\n'
apply_fn = fn(menu, 'vr_menu_apply')
migration = menu[menu.index('static char const *const vr_menu_update_features[] ='):menu.index('void vr_menu_features_on(void)')]
migration += fn(menu, 'vr_menu_features_on')

HARNESS = r'''
#include <assert.h>
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
/* the config store: a key's text */
static struct { char key[64], text[256]; } store[512];
static int stored;
static char *slot(char const *key)
{
	for (int i = 0; i < stored; i++) if (!strcmp(store[i].key, key)) return store[i].text;
	assert(stored < 512);
	snprintf(store[stored].key, sizeof(store[stored].key), "%s", key);
	store[stored].text[0] = 0;
	return store[stored++].text;
}
static void set(char const *key, char const *text) { snprintf(slot(key), 256, "%s", text); }
static int config_boolean(char const *key) { return !strcmp(slot(key), "true"); }
static double config_real(char const *key) { return atof(slot(key)); }
static long config_integer(char const *key) { return atol(slot(key)); }
static char const *config_string(char const *key) { return slot(key); }
static int config_write_boolean(char const *key, int on) { set(key, on ? "true" : "false"); return 1; }
static int config_write_real(char const *key, double value) { char t[64]; snprintf(t, sizeof(t), "%g", value); set(key, t); return 1; }
static int config_write_string(char const *key, char const *text) { set(key, text); return 1; }
static int config_write_text(char const *key, char const *text) { set(key, text); return 1; }
static int config_write(char const *key, char const *text) { set(key, text); return 1; }
static int config_matches(char const *key, char const *text)
{
	char *end1, *end2; double a = strtod(slot(key), &end1), b = strtod(text, &end2);
	if (*slot(key) && !*end1 && *text && !*end2) return fabs(a - b) < 0.001;
	return !strcmp(slot(key), text);
}
static int reloads, logs;
static void vr_reload_settings(void) { reloads++; }
static void platform_log(char const *format, ...) { (void)format; logs++; }
#include "port/linux/src/vr.h"
''' + tables + pages + r'''
static long vr_menu_value_index(struct vr_menu_setting const *s) { (void)s; return NONE; }
''' + frame[frame.index('static const char *const button_action_keys[VR_BUTTON_ACTIONS] ='):
              frame.index('void vr_set_network_game(int network)')] + \
    fn(menu, 'vr_menu_multi') + fn(menu, 'vr_menu_button_source') + fn(menu, 'vr_menu_button_sprint_set') + \
    fn(menu, 'vr_menu_button_set') + apply_fn + migration + r'''
/* a menu row chosen by hand */
static void choose(char const *key, char const *value)
{
	for (long page = 0; page < VR_MENU_PAGE_COUNT; page++)
		for (long index = 0; index < vr_menu_pages[page].count; index++)
			if (!strcmp(vr_menu_pages[page].settings[index].key, key)) { vr_menu_apply(&vr_menu_pages[page].settings[index], value); return; }
	assert(!"no row");
}
int main(void)
{
	static char const *const listed[] = { FEATURES };
	/* a config from before the update: every feature off, and the player's own choices */
	for (unsigned i = 0; i < NUMBEROF(listed); i++) set(listed[i], "false");
	set("vr.vehicle_view", "chase"); set("vr.melee", "swing"); set("vr.melee_speed", "0"); set("vr.npc_grab_assist", "0.10");
	set("vr.object_throw", "0"); set("vr.melee_requires_fist", "false"); set("vr.button_sprint", "false"); set("vr.arm_run", "false");
	set("vr.holsters", "true"); set("vr.immersion_auto", ""); set("vr.button_crouch", "left_stick");
	set("vr.vehicle_grip_guide", "false"); set("vr.vehicle_tank_hatch", "false"); set("vr.bullet_time_toggle", "false");
	vr_menu_features_on();
	/* every feature on */
	for (unsigned i = 0; i < NUMBEROF(listed); i++)
	{
		struct vr_menu_setting const *row; char const *on;
		assert(vr_menu_feature_row(listed[i], &row, &on));
		if (!config_boolean(listed[i])) { printf("off: %s\n", listed[i]); assert(0); }
	}
	/* with what they need and play best with */
	assert(config_boolean("vr.dropped_magazines") && config_boolean("vr.manual_reload")); /* MAG DEBRIS (the owner) */
	assert(!strcmp(config_string("vr.vehicle_view"), "first_person"));   /* IMMERSIVE VEHICLE */
	assert(!strcmp(config_string("vr.melee"), "impact") && config_real("vr.melee_speed") >= 2.0 - 1e-6); /* FIST COMBAT */
	assert(config_boolean("vr.melee_requires_fist"));
	assert(config_real("vr.npc_grab_assist") >= 0.30 - 1e-6 && config_real("vr.object_throw") >= 2.0 - 1e-6);
	assert(config_boolean("vr.button_sprint"));                            /* SLIDE: a sprint (no ARM RUN) */
	assert(config_boolean("vr.holsters"));
	/* ways to play left as they were */
	assert(!config_boolean("vr.arm_run") && !config_boolean("vr.vehicle_grip_guide") && !config_boolean("vr.vehicle_tank_hatch") &&
		!config_boolean("vr.bullet_time_toggle"));
	/* afterwards the player's OFF is the player's: IMMERSIVE VEHICLE off takes its first-person seat back with it,
	 * as VR SETTINGS always did; FIST COMBAT off releases impact melee and its speed */
	choose("vr.vehicle_handles", "false");
	assert(!config_boolean("vr.vehicle_handles") && !strcmp(config_string("vr.vehicle_view"), "chase"));
	choose("vr.assisted_combat", "false");
	assert(!config_boolean("vr.assisted_combat") && !strcmp(config_string("vr.melee"), "swing"));
	/* a requirement turned off by hand turns its hard feature off (MANUAL RELOAD off takes MAG DEBRIS) */
	choose("vr.manual_reload", "vr.manual_reload=false;vr.dropped_magazines=false");
	assert(!config_boolean("vr.manual_reload") && !config_boolean("vr.dropped_magazines"));
	printf("%u VR features on after the update, with their requirements; turned off after, off\n", (unsigned)NUMBEROF(listed));
	return 0;
}
'''.replace('FEATURES', ', '.join('"%s"' % key for key in features))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'features.c').write_text(HARNESS, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-DHALO_VR', '-Wall', '-Wno-unused-function', '-Wno-unused-variable',
                '-Wno-multichar', '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-I' + str(ROOT),
                '-I' + str(ROOT / 'port/linux/game'), str(OUT / 'features.c'), '-lm', '-o', str(OUT / 'features')], check=True)
print(subprocess.run([str(OUT / 'features')], check=True, capture_output=True, text=True).stdout.strip())
print('PASS: Test73 VR features on with the update, once, as VR SETTINGS turns them on; the player\'s later OFF kept')
