"""Test73 (2026-10-20 session): what the item 3 verification and the owner's notes changed.

- game.unlock_all_levels is true by default (OpenCE's 329d311c1 made it false): every release of this port opened
  every campaign level to a new profile, and the owner keeps it so. A new profile is made by player_profile_new, which
  finishes every level on every difficulty when the setting is true.
- debug.fixed_step plays the same every time, frame for frame, as its help says (the shadow A/B of universal's
  5f2e048eb needed it): the local random seed is fixed (random_math.c), a cache read is done before the game goes on
  (cache_files_windows.c: its own completion flag, read as volatile, as cache_requests_flush reads one, since the I/O
  thread sets it), and the desktop visibility batches are waited for (d3d8_gl.c; test_test73_visibility runs that).
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_session'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?(?:inline )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


# every level open to a new profile by default
config = read('port/linux/src/port_config.c')
entry = re.search(r'\{ "game\.unlock_all_levels", _config_boolean, "(\w+)", "HALO_UNLOCK_ALL_LEVELS"', config)
assert entry and entry.group(1) == 'true', entry
profile = read('source/saved games/player_profile.c')
new = fn(profile, 'player_profile_new')
assert 'if (config_boolean("game.unlock_all_levels"))' in new
assert 'profile->single_player_map_flags[level] |= FLAG(difficulty);' in new
assert '| `game.unlock_all_levels` | `true` |' in read('port/linux/README.md')

# fixed step: the local random seed, compiled with the clock and rand() made to differ every call
seed = fn(read('source/math/random_math.c'), 'get_number_suitable_for_initializing_random_seed')
assert 'if (halo_fixed_step())' in seed
OUT.mkdir(parents=True, exist_ok=True)
harness = r'''
#include <assert.h>
#include <stdio.h>
static int fixed, calls;
static int halo_fixed_step(void) { return fixed; }
static unsigned long system_seconds(void) { return 1000 + calls++; }
static unsigned long system_milliseconds(void) { return 7 * calls++; }
static int rand(void) { return 3 * calls++; }
''' + seed + r'''
int main(void)
{
	unsigned long first, second;

	fixed = 1;
	first = get_number_suitable_for_initializing_random_seed();
	second = get_number_suitable_for_initializing_random_seed();
	assert(first == second && first == 0x5EED5EEDUL);
	fixed = 0;
	first = get_number_suitable_for_initializing_random_seed();
	second = get_number_suitable_for_initializing_random_seed();
	assert(first != second);
	printf("PASS: fixed step: one local random seed every run; otherwise the clock's\n");
	return 0;
}
'''
source = OUT / 'seed.c'
source.write_text(harness, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Wno-unused-function', '-fsanitize=address,undefined',
                '-fno-sanitize-recover=undefined', str(source), '-o', str(OUT / 'seed')], check=True)
subprocess.run([str(OUT / 'seed')], check=True)

# fixed step: a cache read finished before the game goes on, waiting on its own flag as volatile
read_fn = fn(read('source/cache/cache_files_windows.c'), 'cache_file_read')
wait = read_fn[read_fn.index('cache_file_windows_thread_wake();'):]
assert re.search(r'if \(halo_fixed_step\(\)\)\s*\{\s*while \(!\*\(volatile boolean \*\)completion_flag_reference\)\s*'
                 r'SleepEx\(0, TRUE\);\s*\}', wait), wait[:400]
# (the MCC and Custom Edition reads return before: they complete at once)
assert read_fn.index('mcc_cache_read') < read_fn.index('halo_fixed_step')
assert read_fn.index('custom_edition_cache_read') < read_fn.index('halo_fixed_step')

# fixed step: the desktop visibility readback waits (its behaviour is test_test73_visibility's)
batch = fn(read('port/linux/src/d3d8_gl.c'), 'visibility_read_batch')
assert 'BOOL wait = halo_fixed_step() != 0;' in batch
# (OpenCE a0f22cbba: read after the swap, the fence always flushed; the fixed step waits up to a second)
assert 'glClientWaitSync(batch->fence, GL_SYNC_FLUSH_COMMANDS_BIT, wait ? 1000000000ULL : 0);' in batch
assert 'if (!available && !wait)' in batch
assert 'int halo_fixed_step(void);' in read('port/linux/src/port_config.h')

# item 4 (map sharing), found by the two-instance test with a real Custom Edition map: debug.network_test's host named
# custom_maps\<name> levels\test\custom_maps\<name>\custom_maps\<name> (version 0), which no client took for a Custom
# Edition map, so none asked for it; a map with a path is now that level, as the file's own comment says
test = read('port/linux/game/network_test.c')
naming = (r"""if (strchr(network_test.map_name, '\\'))""" + '\n'
          r"""					snprintf(path, sizeof(path), "%s", network_test.map_name);""" + '\n'
          r"""				else""" + '\n'
          r"""					snprintf(path, sizeof(path), "levels\\test\\%s\\%s", network_test.map_name, """
          r"""network_test.map_name);""")
assert naming in test, naming
# the menus' own choice passes the list's name as it is (custom_maps\<name>)
handlers = read('source/interface/ui_widget_event_handler_functions.c')
assert 'map_name = levels[level_index];' in handlers and 'network_game_server_change_map_name(server, map_name);' in handlers
# why a missing map is not asked for, and what the host named, are logged
share = fn(read('port/linux/game/map_share.c'), 'map_share_download_begin')
for reason in ('network.map_download is off', 'this machine hosts', 'no network client',
               'no Custom Edition tag cache (game.custom_edition)', 'no file wanted',
               'its name is not a safe file name', 'the host named no version of it'):
    assert reason in share, reason
assert share.count('"map sharing: not asking the host for %s: %s"') == 2
assert 'platform_log("map missing: %s (the host\'s \'%.127s\', version %08lx)", message, map_name, version);' in \
    read('source/cache/cache_files.c')

# item 6: ARMS FROM (vr.character_arms): the played character's own arms with the first-person gloves' fingers
entry = re.search(r'\{ "vr\.character_arms", _config_string, "\\"(\w+)\\"", "HALO_VR_CHARACTER_ARMS"', config)
assert entry and entry.group(1) == 'auto', entry
assert '{ "vr.character_arms", { "auto", "on", "off", NULL }, NULL },' in config
menu = read('port/linux/game/vr_menu.c')
assert ('{ "ARMS FROM", "vr.character_arms", _vr_setting_string, 3, { { "AUTO", "auto" }, { "CHARACTER", "on" }, '
        '{ "FIRST PERSON", "off" } } },') in menu
render = read('port/linux/game/vr_render.c')
wanted = fn(render, 'vr_character_arms_wanted')
assert 'else if (mode == 2 && name && !_strnicmp(name, "characters\\\\cyborg", 17)) why = "the game\'s own Spartan";' \
    in wanted, wanted
for why in ('"ARMS FROM first person"', '"hands only"', '"arms not reached by IK"', '"not aiming by hand"'):
    assert why in wanted, why
body = fn(render, 'vr_render_body_matrices')
assert body.index('cached_time == vr_pose_time()) return matrices;') < body.index('vr_character_arms_frame.on = FALSE;'), \
    "the other eye's cached palette keeps the frame's choice"
assert 'own_arms = vr_character_arms_wanted(object_index);' in body
assert body.index('vr_body_arms_to_hands(object_index, graph, matrices, count, forward);') < \
    body.index('vr_publish_body(object_index, graph, matrices, count, forward, own_arms);')
assert 'roots[1] = vr_find_node(graph, " l ", own_arms ? "hand" : "clavicle");' in body
assert 'roots[2] = vr_find_node(graph, " r ", own_arms ? "hand" : "clavicle");' in body
assert '!(own_arms && ((upper[0] >= 0 && vr_node_under(graph, i, upper[0])) ||' in body
publish = fn(render, 'vr_publish_body')
assert 'if (!arms_solved)\n        vr_body_arms_to_hands(unit, graph, m, count, heading);' in publish
recent = fn(render, 'vr_render_character_arms')
assert 'return vr_character_arms_frame.on && age >= 0.0 && age < 0.1;' in recent

# the PC build's maps folder check: an installed custom campaign's levels are not strays (the owner saw SPV1 warned of)
launcher = read('port/linux/src/desktop_launcher.c')
mod_map = fn(launcher, 'desktop_launcher_mod_map')
assert 'if (!mod_installed(root, &launcher_mods[mod]))' in mod_map and '!SDL_strcasecmp(name, file_name)' in mod_map
assert 'int desktop_launcher_mod_map(const char *root, const char *file_name) { (void)root; (void)file_name; return 0; }' \
    in launcher
strays = fn(read('port/linux/src/xbox_files.c'), 'pc_maps_in_maps')
assert strays.index('if (!map_version_is_pc(map_file_version(path)))') < \
    strays.index('if (desktop_launcher_mod_map(platform_data_root(), name))')

# item 7: the screen's render targets of a width no longer drawn are freed (OpenCE 7124534a4, this port's way): the
# real render_targets_evict, render_target_delete and the framebuffer helpers, with counting GL stand-ins
gl = read('port/linux/src/d3d8_gl.c')
xgpu = read('port/linux/src/xgpu.h')
struct = lambda text, name: text[text.index('struct %s\n{' % name):text.index('};', text.index('struct %s\n{' % name)) + 2]
commit = fn(gl, 'halo_screen_commit')
assert commit.index('screen_width = width;') < commit.index('render_targets_evict();')
evict_harness = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int BOOL;
typedef unsigned int GLuint;
typedef unsigned int GLenum;
#define TRUE 1
#define FALSE 0
#define SCREEN_HEIGHT 480
''' + struct(xgpu, 'xgpu_render_target') + '\n' + struct(gl, 'render_target_entry') + '\n' + \
    struct(gl, 'framebuffer_entry') + r'''
#define RENDER_TARGET_BUCKET_COUNT 256
static struct render_target_entry *render_target_buckets[RENDER_TARGET_BUCKET_COUNT];
static struct render_target_entry *render_targets;
static struct framebuffer_entry *framebuffers;
static long screen = 640;
static int textures_deleted, renderbuffers_deleted, framebuffers_deleted, invalidated, logged;
static long halo_screen_width(void) { return screen; }
static void glDeleteTextures(int n, const GLuint *t) { (void)t; textures_deleted += n; }
static void glDeleteRenderbuffers(int n, const GLuint *t) { (void)t; renderbuffers_deleted += n; }
static void glDeleteFramebuffers(int n, const GLuint *t) { (void)t; framebuffers_deleted += n; }
static void xgpu_gl_state_invalidate(void) { invalidated++; }
static void platform_log(const char *format, ...) { (void)format; logged++; }
/* (OpenCE a3277d94d's: the bound framebuffer's shadow, and a deleted texture forgotten by the binding shadows) */
static struct { GLuint framebuffer; } gl_state;
static int textures_forgotten;
static void xgpu_gl_texture_deleted(unsigned int texture) { (void)texture; textures_forgotten++; }
''' + fn(gl, 'render_target_bucket') + fn(gl, 'framebuffer_forget_renderbuffer') + fn(gl, 'framebuffer_forget_texture') + \
    fn(gl, 'render_target_delete') + fn(gl, 'render_targets_evict') + r'''
static GLuint names = 1;
static struct render_target_entry *add(unsigned long data, unsigned long width, unsigned long height, BOOL multisampled)
{
	struct render_target_entry *entry = calloc(1, sizeof(*entry));
	struct framebuffer_entry *framebuffer = calloc(1, sizeof(*framebuffer));
	entry->target.data = data; entry->target.width = width; entry->target.height = height;
	entry->target.texture = names++;
	entry->target.multisample = multisampled ? names++ : 0;
	entry->next = render_targets; render_targets = entry;
	entry->next_in_bucket = *render_target_bucket(data); *render_target_bucket(data) = entry;
	framebuffer->color = entry->target.texture; framebuffer->framebuffer = names++;
	framebuffer->next = framebuffers; framebuffers = framebuffer;
	if (multisampled)
	{
		framebuffer = calloc(1, sizeof(*framebuffer));
		framebuffer->color = entry->target.multisample; framebuffer->renderbuffers = TRUE; framebuffer->framebuffer = names++;
		framebuffer->next = framebuffers; framebuffers = framebuffer;
	}
	return entry;
}
static int count_targets(void) { int n = 0; for (struct render_target_entry *e = render_targets; e; e = e->next) n++; return n; }
static int count_framebuffers(void) { int n = 0; for (struct framebuffer_entry *f = framebuffers; f; f = f->next) n++; return n; }
static int in_bucket(struct render_target_entry *wanted)
{
	for (struct render_target_entry *e = *render_target_bucket(wanted->target.data); e; e = e->next_in_bucket)
		if (e == wanted) return 1;
	return 0;
}
int main(void)
{
	/* the back buffer and its depth at the old width 852 (one multisampled), a game surface of the
	same address bucket at 640 (kept), a shadow map 128 high, a 1024 texture target */
	struct render_target_entry *old_back = add(0x01000000, 852, 480, TRUE);
	struct render_target_entry *old_depth = add(0x01100000, 852, 480, FALSE);
	struct render_target_entry *keep_640 = add(0x01000000, 640, 480, FALSE);
	struct render_target_entry *shadow = add(0x02000000, 128, 128, FALSE);
	struct render_target_entry *big = add(0x03000000, 1024, 512, FALSE);
	(void)old_back; (void)old_depth;
	assert(count_targets() == 5 && count_framebuffers() == 6);
	screen = 640;
	render_targets_evict();
	assert(count_targets() == 3 && in_bucket(keep_640) && in_bucket(shadow) && in_bucket(big));
	assert(textures_deleted == 2 && renderbuffers_deleted == 1 && framebuffers_deleted == 3 && count_framebuffers() == 3);
	/* (each deleted target's texture forgotten by the binding shadows first: OpenCE a3277d94d) */
	assert(textures_forgotten == textures_deleted);
	assert(logged == 1 && invalidated >= 1);
	/* nothing stale: nothing freed, nothing logged */
	render_targets_evict();
	assert(count_targets() == 3 && textures_deleted == 2 && logged == 1);
	printf("PASS: a screen width change frees the old width's targets with their framebuffers; others kept\n");
	return 0;
}
'''
(OUT / 'evict.c').write_text(evict_harness, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Wno-unused-function', '-fsanitize=address,undefined',
                '-fno-sanitize-recover=undefined', str(OUT / 'evict.c'), '-o', str(OUT / 'evict')], check=True)
subprocess.run([str(OUT / 'evict')], check=True)

# item 7: OpenCE b449c43e2, the vertex constant serials 64-bit
assert 'static unsigned long long constant_serials[XGPU_VERTEX_CONSTANT_COUNT];' in gl
assert 'static unsigned long long constants_serial;' in gl
assert 'unsigned long long constants_serial;\n\t/* draw_uniforms_serial' in gl
assert 'unsigned long serial;' not in fn(gl, 'prepare_draw')

# item 7, 244 gap (b): the desktop builds' icons are this port's (the launcher's artwork, tools/desktop_icon.py), the
# window's embedded and the executables' compiled from port/windows/halo.rc, as OpenCE 244 does with its own
embed = read('tools/embed_assets.py')
assert 'WINDOW_ICON = Path("port/assets/icon/haloce-quest-vr-256.png")' in embed and 'opence-icon' not in embed
assert (ROOT / 'port/assets/icon/haloce-quest-vr-256.png').read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
icon = (ROOT / 'port/windows/haloce-quest-vr.ico').read_bytes()
assert icon[:4] == b'\x00\x00\x01\x00' and int.from_bytes(icon[4:6], 'little') == 9, 'nine sizes, 16 to 256'
assert '1 ICON "haloce-quest-vr.ico"' in read('port/windows/halo.rc')
windows = read('tools/windows_build.py')
assert 'command="$windows_rc /no-preprocess /FO $out $in"' in windows
assert 'n.build(outputs=resources, rule="windows_rc", inputs=PORT_DIR / "halo.rc",' in windows
assert 'inputs=objects + extra_objects + [resources],' in windows, 'both executables link the icon'

# item 7, 244 gap (f): online co-op's own FRIENDLY FIRE, which the flat campaign pause menu has, is on the headset's
# VR menu (GAMEPLAY): its campaign pause menu is VR's own (menu_tags.c leaves it unpatched under HALO_VR)
vr_menu = read('port/linux/game/vr_menu.c')
assert re.search(r'static struct vr_menu_setting const vr_menu_vr\[\] =\s*\{[\s\S]*?\{ "FRIENDLY FIRE", '
                 r'"network\.coop_own_friendly_fire", _vr_setting_boolean, 2, \{ \{ "OFF", "false" \}, \{ "ON", "true" \} \} \},'
                 r'\s*\};', vr_menu)
assert 'return config_boolean("network.coop_own_friendly_fire") != 0;' in read('port/linux/game/network_coop.c'), \
    'read as it changes'
print('PASS: unlock_all_levels true by default; fixed step: seed, cache reads and visibility waits; '
      'network test hosts a Custom Edition map by its own name; map sharing says why it does not ask; '
      'ARMS FROM the character; an installed campaign\'s levels are not warned of')
