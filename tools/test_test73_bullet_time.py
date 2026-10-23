"""Test73: BULLET TIME's slow motion is never kept by a checkpoint.

A player's report (test70): "I hit a checkpoint when in slo motion, and when i
died and the checkpoint reloaded i was stuck in slow motion. Hitting the
bullet time button again only causes the slo motion to double up lol. Turning
off the bullet time setting doesn't fix it." Test70 to Test72's BULLET TIME
set the game's own speed, which is the game state's (game_time_globals,
game_state_malloc): a checkpoint kept the slow motion, the revert brought it
back with BULLET TIME off, its button slowed it again, and the setting gave
nothing back.

Run here with the real code (clang, ASan/UBSan): game_time.c's speed functions
and vr_bullet_time.c, with the input, settings and clock as stand-ins.
1. The report's sequence (toggle and hold), today's code against Test72's
   (f77f6a11, the code of the report; HEAD's until Test73 was committed):
   Test72's reproduces every symptom (the negative control); today's keeps the
   checkpoint at the game's own speed, starts the revert at full speed, never
   slows twice, and the setting gives the speed back.
2. A checkpoint an earlier build saved slowed is healed after it is taken, but
   only where it can only be that (a local game, a map whose scripts never call
   game_speed, a speed in BULLET TIME's range); a map's script's speed is kept,
   and BULLET TIME slows it and gives it back as it was.
3. hs.c's scan (hs_syntax_node_calls_function) finds game_speed's calls only.
4. The wiring: every saved game taken resets BULLET TIME and heals; the
   readers that put the speed back or give it to a script read the game's own.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8', errors='replace')
# (the code before the fix: Test72's; Test73b: not HEAD's, which has had the fix since Test73 was committed)
BEFORE = 'f77f6a11'
head = lambda path: subprocess.run(['git', 'show', BEFORE + ':' + path], cwd=ROOT, capture_output=True, text=True,
                                   check=True).stdout
OUT = ROOT / 'build/test73-bullet-time'
OUT.mkdir(parents=True, exist_ok=True)


def function(text, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\(\s*\n?[^;{}]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.end() - 1)
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


def game_time_part(text, new):
    struct = text[text.index('struct game_time_globals_struct\n{'):]
    struct = struct[:struct.index('};') + 2] + '\n'
    part = struct + 'static struct game_time_globals_struct *game_time_globals;\n'
    names = ['game_time_get_tick_fraction', 'game_time_get_speed', 'game_time_set_speed']
    if new:
        assert 'static real game_time_local_scale = 1.0f;' in text
        part += 'static real game_time_local_scale = 1.0f;\n'
        names += ['game_time_get_own_speed', 'game_time_set_local_scale', 'game_time_get_local_scale',
                  'game_time_after_load']
        assert '#define GAME_TIME_BULLET_TIME_LEAST_SPEED 0.2f\n' in text
        part += '#define GAME_TIME_BULLET_TIME_LEAST_SPEED 0.2f\n'
    return part + ''.join(function(text, name) for name in names)


def bullet_part(text):
    body = text[text.index('#ifdef HALO_VR\n') + len('#ifdef HALO_VR\n'):text.index('\n#else\n')]
    return '\n'.join(line for line in body.splitlines() if not line.startswith('#include')) + '\n'


PRELUDE = r'''#include <assert.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
typedef float real;
typedef int boolean;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define TICKS_PER_SECOND 30
#define PIN(x, lo, hi) ((x) < (lo) ? (lo) : ((x) > (hi) ? (hi) : (x)))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define match_assert(file, line, condition) assert(condition)
enum { _error_silent = 2 };
enum { _game_connection_local = 0, _game_connection_network_server = 1, _game_connection_network_client = 2 };
static int connection = _game_connection_local, map_sets_speed, errors_logged;
static int setting_on = 1, toggle_mode = 1, held, coop, in_cinematic, paused_flag;
static unsigned long now_ms = 1000;
static boolean network_game_distributed_client(void) { return connection == _game_connection_network_client; }
static real mcc_game_speed_client(real original) { return original; }
static short game_connection(void) { return (short)connection; }
boolean hs_scenario_may_set_game_speed(void) { return map_sets_speed; }
static void error(int kind, char const *format, ...) { (void)kind; (void)format; errors_logged++; }
static short local_player_get_next(short index) { return index == NONE ? 0 : NONE; }
static boolean network_coop_active(void) { return coop; }
static boolean cinematic_in_progress(void) { return in_cinematic; }
static boolean director_inhibited_input(short player) { (void)player; return FALSE; }
static int vr_active(void) { return 1; }
static int vr_aiming(void) { return 1; }
static int vr_bullet_time_held(void) { return held; }
static void vr_haptic(int hand, float amplitude, float seconds) { (void)hand; (void)amplitude; (void)seconds; }
static int config_boolean(char const *name)
{
	if (!strcmp(name, "vr.bullet_time")) return setting_on;
	assert(!strcmp(name, "vr.bullet_time_toggle"));
	return toggle_mode;
}
static double config_real(char const *name) { assert(!strcmp(name, "vr.bullet_time_scale")); return 0.4; }
'''


def program(new):
    game_time = read('source/game/game_time.c') if new else head('source/game/game_time.c')
    bullet = read('port/linux/game/vr_bullet_time.c') if new else head('port/linux/game/vr_bullet_time.c')
    paused = 'boolean game_time_get_paused(void) { return paused_flag; }\n'
    log = ('void platform_log(char const *format, ...) { (void)format; }\n'
           'unsigned long system_milliseconds(void) { return now_ms; }\n')
    return PRELUDE + '#define NEW %d\n' % int(new) + paused + log + game_time_part(game_time, new) + \
        'void vr_bullet_time_frame(void);\nvoid vr_bullet_time_reset(void);\n' + bullet_part(bullet) + DRIVER


DRIVER = r'''
static struct game_time_globals_struct storage;
static void frames(int count) { while (count-- > 0) { now_ms += 14; vr_bullet_time_frame(); } }
static void press(void) { held = 1; frames(1); held = 0; frames(1); }
static real effective(void) { return game_time_get_speed(); }
static int near(real a, real b) { return fabsf(a - b) < 0.002f; }
/* what a saved game taken does about BULLET TIME: before Test73, nothing */
static void after_load(void)
{
#if NEW
	vr_bullet_time_reset();
	game_time_after_load();
#endif
}
static void start(void)
{
	memset(&storage, 0, sizeof(storage));
	storage.initialized = TRUE;
	storage.active = TRUE;
	storage.speed = 1.0f;
	game_time_globals = &storage;
	connection = _game_connection_local;
	setting_on = 1; held = 0; coop = 0; in_cinematic = 0; paused_flag = 0; map_sets_speed = 0;
	vr_bullet_time_reset();
	frames(2);
}
int main(void)
{
	struct game_time_globals_struct checkpoint;
	int mode;

	for (mode = 0; mode < 2; mode++)
	{
		start();
		toggle_mode = mode;
		/* BULLET TIME on, fully slowed */
		if (toggle_mode) press(); else held = 1;
		frames(30);
		printf("mode %d slowed %.3f own %.3f\n", mode, effective(), storage.speed);
		assert(near(effective(), 0.4f));
		/* the checkpoint saved now */
		checkpoint = storage;
		printf("mode %d checkpoint keeps %.3f\n", mode, checkpoint.speed);
		/* BULLET TIME off */
		if (toggle_mode) press(); else held = 0;
		frames(30);
		assert(near(effective(), 1.0f));
		/* a death: the checkpoint reverted */
		storage = checkpoint;
		after_load();
		frames(5);
		printf("mode %d after the revert %.3f\n", mode, effective());
		/* its button again */
		if (toggle_mode) press(); else held = 1;
		frames(30);
		printf("mode %d button again %.3f\n", mode, effective());
		if (toggle_mode) press(); else held = 0;
		frames(30);
		printf("mode %d button off %.3f\n", mode, effective());
		/* the setting turned off */
		setting_on = 0;
		frames(3);
		printf("mode %d setting off %.3f\n", mode, effective());
	}
#if NEW
	/* 2. an earlier build's slowed checkpoint healed after it is taken, only
	where it can only be that */
	start();
	storage.speed = 0.4f; errors_logged = 0; after_load();
	assert(near(storage.speed, 1.0f) && errors_logged == 1);
	storage.speed = 0.2f; after_load();
	assert(near(storage.speed, 1.0f));
	storage.speed = 0.4f; map_sets_speed = 1; errors_logged = 0; after_load();
	assert(near(storage.speed, 0.4f) && errors_logged == 0);
	map_sets_speed = 0; connection = _game_connection_network_server; after_load();
	assert(near(storage.speed, 0.4f));
	connection = _game_connection_local;
	storage.speed = 0.1f; after_load(); assert(near(storage.speed, 0.1f));
	storage.speed = 1.5f; after_load(); assert(near(storage.speed, 1.5f));
	storage.speed = 1.0f; errors_logged = 0; after_load(); assert(errors_logged == 0);
	storage.initialized = FALSE; storage.speed = 0.4f; after_load(); assert(near(storage.speed, 0.4f));
	/* a map's script's speed: BULLET TIME slows it, never writes it, gives it back */
	start();
	toggle_mode = 0;
	game_time_set_speed(0.5f);
	held = 1; frames(30);
	assert(near(effective(), 0.2f) && near(game_time_get_own_speed(), 0.5f) && near(storage.speed, 0.5f));
	held = 0; frames(30);
	assert(near(effective(), 0.5f) && near(game_time_get_local_scale(), 1.0f));
	/* not here: a network game, co-op, a cinematic, paused */
	start(); toggle_mode = 0; held = 1;
	connection = _game_connection_network_server; frames(30); assert(near(effective(), 1.0f));
	connection = _game_connection_local; coop = 1; frames(30); assert(near(effective(), 1.0f));
	coop = 0; in_cinematic = 1; frames(30); assert(near(effective(), 1.0f));
	in_cinematic = 0; frames(30); assert(near(effective(), 0.4f));
	/* the scale's bounds */
	game_time_set_local_scale(NAN); assert(game_time_get_local_scale() == 1.0f);
	game_time_set_local_scale(0.0f); assert(game_time_get_local_scale() == 1.0f);
	game_time_set_local_scale(1.5f); assert(game_time_get_local_scale() == 1.0f);
	game_time_set_local_scale(0.3f); assert(near(game_time_get_local_scale(), 0.3f));
	/* the frames between ticks follow the slowed clock */
	storage.leftover_dt = 0.01f; storage.speed = 1.0f; game_time_set_local_scale(0.5f);
	assert(near(game_time_get_tick_fraction(), 0.15f));
	puts("PASS ran");
#endif
	return 0;
}
'''

results = {}
for new in (False, True):
    name = 'new' if new else 'head'
    source = OUT / (name + '.c')
    source.write_text(program(new), encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-function',
                    '-fsanitize=address,undefined', '-fno-sanitize-recover=all', str(source), '-lm',
                    '-o', str(OUT / name)], check=True)
    run = subprocess.run([str(OUT / name)], capture_output=True, text=True, check=True)
    results[name] = dict(re.findall(r'^(mode \d [a-z ]+?) (-?[\d.]+)', run.stdout, re.M))
    results[name]['ran'] = 'PASS ran' in run.stdout
old, now = results['head'], results['new']
for mode in ('0', '1'):
    key = lambda what: 'mode %s %s' % (mode, what)
    # Test72's reproduces the report: the checkpoint keeps the slow motion, the
    # revert brings it back, the button doubles it, the setting gives nothing
    assert abs(float(old[key('checkpoint keeps')]) - 0.4) < 0.01, old
    assert abs(float(old[key('after the revert')]) - 0.4) < 0.01, old
    assert abs(float(old[key('button again')]) - 0.16) < 0.01, old
    assert abs(float(old[key('setting off')]) - 0.4) < 0.01, old
    # today's: none of it
    assert abs(float(now[key('checkpoint keeps')]) - 1.0) < 0.001, now
    assert abs(float(now[key('after the revert')]) - 1.0) < 0.001, now
    assert abs(float(now[key('button again')]) - 0.4) < 0.01, now
    assert abs(float(now[key('button off')]) - 1.0) < 0.001, now
    assert abs(float(now[key('setting off')]) - 1.0) < 0.001, now
assert now['ran']
print('PASS: the report reproduced with Test72\'s code (checkpoint keeps 0.4, the revert stuck at 0.4, the button '
      'doubles it to 0.16, the setting gives nothing back; toggle and hold); today\'s keeps the checkpoint at 1, '
      'starts the revert at 1, slows to 0.4 once and gives 1 back, and the setting gives 1 back')
print('PASS: an earlier build\'s slowed checkpoint healed only in a local game, on a map that never calls '
      'game_speed, in BULLET TIME\'s range; a script\'s speed slowed and given back unchanged; not in network, '
      'co-op or cinematics; the scale bounded; frames between ticks follow it')

# 3. hs.c's scan
hs = read('source/hs/hs.c')
scan = function(hs, 'hs_syntax_node_calls_function')
probe = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int boolean;
#define TRUE 1
#define FALSE 0
#define TEST_FLAG(flags, bit) (((flags) >> (bit)) & 1)
#define NUMBEROF(a) ((short)(sizeof(a) / sizeof((a)[0])))
#define csstrcmp strcmp
enum { _hs_syntax_node_primitive_bit = 0, _hs_syntax_node_script_bit, _hs_syntax_node_variable_bit,
	_hs_syntax_node_permanent_bit };
enum { _hs_type_void = 4, NUMBER_OF_HS_TYPES = 40 };
#define hs_type_valid(type) ((type) >= _hs_type_void && (type) < NUMBER_OF_HS_TYPES)
struct hs_syntax_node { short datum_header; short function_index; short type; short flags; };
struct hs_function_definition { char const *name; };
static struct hs_function_definition functions[] = { { "begin" }, { "game_speed" }, { "sleep" } };
boolean const hs_function_allowed_in_maps[3] = { TRUE, TRUE, TRUE };
static struct hs_function_definition *hs_function_get(short index) { return &functions[index]; }
struct hs_function_definition *mcc_script_function(short index) { return index == 200 ? &functions[1] : NULL; }
struct hs_function_definition *custom_edition_script_function(short index) { (void)index; return NULL; }
''' + scan + r'''
int main(void)
{
	short permanent = 1 << _hs_syntax_node_permanent_bit;
	struct hs_syntax_node call = { 0, 1, 4, 0 };
	call.flags = permanent;
	assert(hs_syntax_node_calls_function(&call, "game_speed"));
	assert(!hs_syntax_node_calls_function(&call, "sleep"));
	call.function_index = 2; assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.function_index = 1; call.flags = permanent | (1 << _hs_syntax_node_primitive_bit);
	assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.flags = permanent | (1 << _hs_syntax_node_script_bit); assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.flags = 0; assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.flags = permanent; call.type = 99; assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.type = 4; call.function_index = 200; assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.function_index = 3; assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	call.function_index = -1; assert(!hs_syntax_node_calls_function(&call, "game_speed"));
	assert(!hs_syntax_node_calls_function(NULL, "game_speed"));
	puts("PASS scan");
	return 0;
}
'''
(OUT / 'scan.c').write_text(probe, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-fsanitize=address,undefined',
                '-fno-sanitize-recover=all', str(OUT / 'scan.c'), '-o', str(OUT / 'scan')], check=True)
assert 'PASS scan' in subprocess.run([str(OUT / 'scan')], capture_output=True, text=True, check=True).stdout
check = function(hs, 'hs_scenario_functions_check')
assert check.index('hs_scenario_calls_game_speed = TRUE;') < check.index('mcc_syntax_functions_check(')
assert 'if (hs_syntax_node_calls_function(expression, "game_speed"))' in check
assert check.index('hs_scenario_calls_game_speed = calls_game_speed;') < check.index('if (!refused && !linked_twice)')
assert re.search(r'hs_scenario_calls_game_speed = TRUE;\n\tif \(!recompile && hs_compile_postprocess', hs)
print('PASS: hs.c finds game_speed\'s calls only (not primitives, scripts, console nodes, other functions, MCC or '
      'OpenSauce indices, bad indices or types); MCC maps and maps not looked at count as setting the speed')

# 4. the wiring
state = read('source/saved games/game_state.c')
after = function(state, 'game_state_call_after_load_procs')
assert after.index('vr_bullet_time_reset();') < after.index('game_time_after_load();') < after.index('(*proc)();')
assert '#include "vr_bullet_time.h"' in state
game_time = read('source/game/game_time.c')
assert 'game_time_globals->speed*game_time_local_scale*TICKS_PER_SECOND' in function(game_time, 'game_time_update')
assert 'game_time_set_speed' not in read('port/linux/game/vr_bullet_time.c')
assert 'real saved_speed = game_time_get_own_speed();' in function(read('source/main/main.c'), 'main_skip_private')
assert 'value.number=game_time_get_own_speed();' in read('port/linux/game/mcc_script_runtime.inl')
print('PASS: every saved game taken resets BULLET TIME then heals; ticks follow the scale; BULLET TIME never sets '
      'the game\'s speed; the cinematic skip and MCC\'s game_speed_value read the game\'s own')
