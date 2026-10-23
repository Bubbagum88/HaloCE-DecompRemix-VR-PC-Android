"""Test73, the Steam Frame: what the other Halo CE Frame ports found and this port now does too (astromaddie's HaloCE-VR,
CC0, our VR work's upstream after our fork; ringfall-mjolnir-vr / Mjolnir VR by Stefan Maier (Cesarus85), AGPL-3.0 or
later; and Valve's Lepton 3.0.8 source). Not run on a Frame: no device acceptance.

Compiled and run (clang, AddressSanitizer):
- host_xr_init (host_xr.c), against a scripted runtime: in Lepton, an instance SteamVR refuses (not running yet, or
  asleep with the headset) is asked for again each second for a minute, a half-made one given back first; with none
  after the minute, and on any later failure, the game ends with its reason logged and no message box (Lepton shows
  the app no window to fall back on); elsewhere (Quest, PICO) the first failure returns, the flat screen kept
  (HaloCE-VR e92d54fa);
- vr_frame_seconds (vr_frame.c): the game clock's step from the frames' display times, none without a runtime frame,
  for a pass that presented nothing, or before a first frame (HaloCE-VR 02887521).
Pinned in the source:
- create_instance lists the runtime's extensions on its first attempt only;
- the fall back to 72 Hz said once when the runtime has no such rate (HaloCE-VR 82b6d12e);
- no restart from the package-replaced receiver in Lepton (HaloCE-VR 6be73ed4);
- the game's quit leaves quit_requested.txt beside its data on Android (ringfall's);
- main.c steps by the display times before a movie's or debug.fixed_step's own steps;
- the Steam library launcher and installer (tools/steam_frame: ringfall's, adapted): bash's syntax check, a container
  of their own, the watcher that ends the container when Steam ends the game, the starts tried again within 30 s
  unless the game was quit, the names the game and the launcher share (Lepton.FOLDER, the APK's), the desktop file's
  Exec free of what it would need escaped, and the bundle (bundle.py) with its scripts executable.
"""
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_frame_ports'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


def build_and_run(name, source):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (name + '.c')
    path.write_text(source, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-function',
                    '-fsanitize=address,undefined', '-fno-sanitize-recover=all', str(path), '-o', str(OUT / name)],
                   check=True)
    return subprocess.run([str(OUT / name)], check=True, capture_output=True, text=True).stdout


host = read('port/android/host/host_xr.c')
frame = read('port/linux/src/vr_frame.c')

# ---------- compiled: host_xr_init against a scripted runtime
xr_init = fn(host, 'xr_unavailable') + fn(host, 'host_xr_init')
assert 'SDL_ShowSimpleMessageBox' not in xr_init and 'host_fatal' not in xr_init
# (the loader, the session and format, the views, the eyes' swapchains, the layers' swapchains)
assert xr_init.count('return xr_unavailable();') == 5
init_source = r'''
#include <assert.h>
#include <setjmp.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
typedef uint64_t XrInstance, XrSystemId, XrAction;
typedef int XrResult;
#define XR_NULL_HANDLE 0
enum { XR_TYPE_VIEW = 7, XR_TYPE_VIEW_CONFIGURATION_VIEW = 41, XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO = 2 };
typedef struct { int type; void *next; uint32_t recommendedImageRectWidth, maxImageRectWidth,
	recommendedImageRectHeight, maxImageRectHeight, recommendedSwapchainSampleCount, maxSwapchainSampleCount; }
	XrViewConfigurationView;
enum { HALO_XR_SWAPCHAIN_LEFT, HALO_XR_SWAPCHAIN_RIGHT, HALO_XR_SWAPCHAIN_QUAD, HALO_XR_SWAPCHAIN_RETICLE,
	HALO_XR_SWAPCHAIN_FADE, HALO_XR_SWAPCHAIN_SCOPE, HALO_XR_SWAPCHAIN_WRIST, HALO_XR_SWAPCHAIN_COUNT };
struct halo_xr_info { char runtime[64], system[64]; long long color_format;
	uint32_t width[HALO_XR_SWAPCHAIN_COUNT], height[HALO_XR_SWAPCHAIN_COUNT], image_count[HALO_XR_SWAPCHAIN_COUNT];
	uint32_t images[HALO_XR_SWAPCHAIN_COUNT][4]; };
enum { _action_haptic = 3, NUMBER_OF_ACTIONS = 8 };
enum { HOST_LOG_INFO, HOST_LOG_WARN, HOST_LOG_ERROR };
static struct { int initialized, failed; XrInstance instance; XrSystemId system; long long color_format;
	int frame_controller, actions_ready, recentre_pending; uint32_t eye_max_width, eye_max_height;
	XrAction actions[NUMBER_OF_ACTIONS]; struct { int type; } views[2]; struct timespec stats_start;
	struct { uint32_t width, height, count, images[4]; } swapchains[HALO_XR_SWAPCHAIN_COUNT]; } xr;
/* the script */
static int lepton, fail_instances, half_made, session_fails, swapchain_fails;
static int instance_calls, destroyed, sleeps, warnings, errors, exit_code;
static char last_error[512];
static jmp_buf exited;
static void host_logf(int level, const char *format, ...)
{
	va_list arguments;
	char line[512];

	va_start(arguments, format);
	vsnprintf(line, sizeof(line), format, arguments);
	va_end(arguments);
	if (level == HOST_LOG_WARN) warnings++;
	if (level == HOST_LOG_ERROR) { errors++; snprintf(last_error, sizeof(last_error), "%s", line); }
}
static int host_lepton_running(void) { return lepton; }
static int initialize_loader(void) { return 1; }
static int create_instance(struct halo_xr_info *out)
{
	assert(xr.instance == XR_NULL_HANDLE); /* (a half-made one given back first) */
	if (++instance_calls <= fail_instances)
	{
		if (half_made) xr.instance = 99;
		return 0;
	}
	xr.instance = 7;
	snprintf(out->runtime, sizeof(out->runtime), "SteamVR/OpenXR 2.17");
	snprintf(out->system, sizeof(out->system), "Steam Frame");
	return 1;
}
static void xrDestroyInstance(XrInstance instance) { assert(instance == 99); destroyed++; }
static int create_session(void) { return !session_fails; }
static int choose_format(void) { xr.color_format = 0x8C43; return 1; }
static XrResult xrEnumerateViewConfigurationViews(XrInstance i, XrSystemId s, int type, uint32_t capacity,
	uint32_t *count, XrViewConfigurationView *views)
{
	(void)i; (void)s; assert(type == XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO && capacity == 2);
	*count = 2;
	for (int eye = 0; eye < 2; eye++)
	{
		views[eye].recommendedImageRectWidth = views[eye].recommendedImageRectHeight = 1728;
		views[eye].maxImageRectWidth = views[eye].maxImageRectHeight = 4096;
	}
	return 0;
}
static int check(XrResult result, const char *name) { (void)name; return result == 0; }
static int create_swapchain(int which, uint32_t width, uint32_t height)
{
	if (swapchain_fails) return 0;
	xr.swapchains[which].width = width; xr.swapchains[which].height = height; xr.swapchains[which].count = 3;
	return 1;
}
static int create_actions(void) { xr.actions[_action_haptic] = 5; return 1; }
static void host_gl_quiet_trace_markers(void) { }
static int fake_sleep(const struct timespec *wanted, struct timespec *left)
{
	(void)left; assert(wanted->tv_sec == 1 && wanted->tv_nsec == 0); sleeps++; return 0;
}
__attribute__((noreturn)) static void fake_exit(int code) { exit_code = code; longjmp(exited, 1); }
#define nanosleep(wanted, left) fake_sleep(wanted, left)
#define _exit(code) fake_exit(code)
''' + xr_init + r'''
#undef _exit
static int attempt(int in_lepton, int failures, int half, int session, int swapchain)
{
	struct halo_xr_info info;
	volatile int result = 12345;

	memset(&xr, 0, sizeof(xr));
	lepton = in_lepton; fail_instances = failures; half_made = half; session_fails = session; swapchain_fails = swapchain;
	instance_calls = destroyed = sleeps = warnings = errors = 0; exit_code = -1; last_error[0] = 0;
	if (!setjmp(exited))
		result = host_xr_init(&info, 1280, 960);
	return result;
}
int main(void)
{
	/* the Quest and PICO: the first failure returns, the flat screen kept; nothing waited for */
	assert(attempt(0, 1, 0, 0, 0) == -1 && instance_calls == 1 && sleeps == 0 && exit_code == -1);
	assert(attempt(0, 0, 0, 1, 0) == -1 && exit_code == -1);
	assert(attempt(0, 0, 0, 0, 1) == -1 && exit_code == -1);
	assert(attempt(0, 0, 0, 0, 0) == 0 && xr.initialized && !xr.failed);
	/* the Frame: SteamVR asleep for three seconds, a half-made instance each time, given back */
	assert(attempt(1, 3, 1, 0, 0) == 0 && instance_calls == 4 && sleeps == 3 && destroyed == 3 && exit_code == -1);
	assert(warnings == 1 && xr.initialized); /* (said once, not each second) */
	/* no runtime at all: a minute, then the game ends with its reason */
	assert(attempt(1, 1000, 0, 0, 0) == 12345 && exit_code == 1 && instance_calls == 61 && sleeps == 60);
	assert(strstr(last_error, "no OpenXR runtime after a minute") && warnings == 6);
	/* the runtime there but a later step failing: ends at once, saying so */
	assert(attempt(1, 0, 0, 1, 0) == 12345 && exit_code == 1 && sleeps == 0 &&
		strstr(last_error, "OpenXR could not be started"));
	assert(attempt(1, 0, 0, 0, 1) == 12345 && exit_code == 1);
	/* once failed (elsewhere), asked again: no second try */
	assert(attempt(0, 1, 0, 0, 0) == -1);
	{
		struct halo_xr_info info;

		assert(host_xr_init(&info, 1280, 960) == -1 && instance_calls == 1);
	}
	puts("ok");
	return 0;
}
'''
assert build_and_run('xr_init', init_source).strip() == 'ok'


def fails(name, source, before, after):
    """a negative control: the fault planted, the checks above must catch it"""
    assert source.count(before) == 1, before
    try:
        build_and_run(name, source.replace(before, after))
    except subprocess.CalledProcessError:
        return
    raise AssertionError('a negative control passed: ' + name)


# (the Quest waiting a minute too; a half-made instance not given back)
fails('xr_init_any', init_source, '\t\tif (!host_lepton_running())\n\t\t\treturn -1;\n', '')
fails('xr_init_kept', init_source, '\t\t\t\txrDestroyInstance(xr.instance);\n', '')

# ---------- compiled: the game clock's step from the display times
seconds = fn(frame, 'vr_frame_seconds')
clock_source = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
static struct { int active; long long clock_display_time; struct { long long predicted_display_time; } frame; } vr;
static int runtime_frame = 1, begun;
static int frame_begin(void) { begun++; return runtime_frame; }
''' + seconds + r'''
int main(void)
{
	double step = -1.0;
	const long long period = 13888889; /* 72 Hz */

	/* no headset: the loop's own measure */
	assert(!vr_frame_seconds(&step) && step == -1.0 && !begun);
	vr.active = 1;
	vr.frame.predicted_display_time = 1000000000LL;
	assert(!vr_frame_seconds(&step) && begun == 1); /* the first: nothing to step from */
	vr.frame.predicted_display_time += period;
	assert(vr_frame_seconds(&step) && fabs(step - period * 1e-9) < 1e-12);
	/* a pass that presented nothing: the same frame, no step */
	step = -1.0;
	assert(!vr_frame_seconds(&step) && step == -1.0);
	/* a frame missed: two periods */
	vr.frame.predicted_display_time += 2 * period;
	assert(vr_frame_seconds(&step) && fabs(step - 2 * period * 1e-9) < 1e-12);
	/* no runtime frame (the session not running): the measure, and the next frame starts again */
	runtime_frame = 0;
	assert(!vr_frame_seconds(&step) && vr.clock_display_time == 0);
	runtime_frame = 1;
	vr.frame.predicted_display_time += period;
	assert(!vr_frame_seconds(&step));
	vr.frame.predicted_display_time += period;
	assert(vr_frame_seconds(&step));
	puts("ok");
	return 0;
}
'''
assert build_and_run('frame_seconds', clock_source).strip() == 'ok'
# (a pass that presented nothing stepping the clock by nothing, which it then counts as a frame)
fails('frame_seconds_same', clock_source, 'vr.clock_display_time <= previous', 'vr.clock_display_time < previous')
main_c = read('source/main/main.c')
unthrottled = fn(main_c, 'main_update_time_unthrottled')
assert unthrottled.index('if (vr_frame_seconds(&display_seconds))') < unthrottled.index('if (main_globals.movie)') < \
    unthrottled.index('else if (halo_fixed_step() && main_globals.connection == _game_connection_local)')
assert 'int vr_frame_seconds(double *seconds);' in read('port/linux/include/halo_vr.h')

# ---------- pinned: the runtime's extensions listed once; the 72 Hz fall back said once
create = fn(host, 'create_instance')
assert 'static int attempts;\n\tint quiet = attempts++ > 0;' in create
assert create.count('if (!quiet)') == 2 and 'for (index = 0; index < count && !quiet; index++)' in create
assert 'int refresh_fallback_failed;' in host
statistics = fn(host, 'log_statistics')
assert 'if (++xr.refresh_misses >= 2 && !xr.refresh_fallback_failed)' in statistics
assert 'if (host_xr_set_refresh_rate(72.0f) <= 0.0f || xr.refresh_rate > 72.5f)' in statistics
assert 'xr.refresh_fallback_failed = 1;' in statistics

# ---------- pinned: no restart from the reinstall in Lepton; the quit said beside the data
receiver = read('port/android/app/src/main/java/com/halo/decomp/UpdateReceiver.java')
assert receiver.index('if (Lepton.running())\n            return;') < receiver.index('context.startActivity(start);')
platform = read('port/linux/src/sdl_platform.c')
quit_block = platform[platform.index('\tif (platform_quit_requested)\n'):]
quit_block = quit_block[:quit_block.index('exit(EXIT_SUCCESS);')]
assert '#ifdef HALO_ANDROID' in quit_block and '"%s/quit_requested.txt", platform_data_root()' in quit_block

# ---------- the Steam library's launcher and installer (tools/steam_frame)
launch = read('tools/steam_frame/launch.sh')
install = read('tools/steam_frame/install.sh')
desktop = read('tools/steam_frame/Install HaloCE Quest VR.desktop')
for script in ('tools/steam_frame/launch.sh', 'tools/steam_frame/install.sh'):
    assert (ROOT / script).read_bytes().startswith(b'#!/bin/bash\n') and b'\r' not in (ROOT / script).read_bytes()
    subprocess.run(['bash', '-n', str(ROOT / script)], check=True)
# (and ShellCheck, where it is installed: _scratch/t72/install_shellcheck.sh puts it in ~/.local/bin)
shellcheck = shutil.which('shellcheck') or str(Path.home() / '.local/bin/shellcheck')
if Path(shellcheck).exists():
    subprocess.run([shellcheck, '-S', 'warning', str(ROOT / 'tools/steam_frame/launch.sh'),
                    str(ROOT / 'tools/steam_frame/install.sh')], check=True)
    print('shellcheck: no warnings')
else:
    print('shellcheck: not installed here, skipped')
folder = re.search(r'static final String FOLDER = "([^"]+)";',
                   read('port/android/app/src/main/java/com/halo/decomp/Lepton.java'))[1]
assert 'DATA="$HOME/Documents/%s"' % folder in launch and 'GAME_DIR="$HOME/Documents/%s"' % folder in install
assert 'snprintf(root, sizeof(root), "/home/%%s/Documents/%s", user);' % folder in read('port/android/host/host_main.c')
assert 'APK="$DATA/HaloCEQuestVR.apk"' in launch and 'APK_NAME="HaloCEQuestVR.apk"' in install
# (a container of its own: not the Steam shortcut's, not ringfall's)
app_id = re.search(r'export SteamAppId="\$\{HALO_LEPTON_APP_ID:-(\d+)\}"', launch)[1]
assert app_id != '4290000001' and int(app_id) > 4290000000
assert 'export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/$SteamAppId"' in launch
assert 'mkdir -p "$STEAM_COMPAT_DATA_PATH/internal" "$STEAM_COMPAT_SHADER_PATH"' in launch
# (Steam's Exit game ends the script: its watcher ends the container)
assert '"\'"$LEPTON"\'" kill "\'"$CONTEXT"\'"' in launch and 'CONTEXT="steamlaunch-$SteamAppId"' in launch
assert '"$LEPTON" waitforexitandrun -- "$APK" &' in launch
# (tried again within 30 s, up to three times, unless quit: the game's marker, by its name)
assert 'for attempt in 1 2 3; do' in launch
assert 'if (( stopping || SECONDS - started >= 30 )) || [ -e "$QUIT" ]; then' in launch
assert 'QUIT="$DATA/quit_requested.txt"' in launch
# (the installer: the launcher under the name its shortcut runs; the APK replaced so Lepton installs it anew)
assert 'LAUNCHER="halo-ce-quest-vr.sh"' in install and 'cp "$BUNDLE/launch.sh" "$GAME_DIR/$LAUNCHER.tmp"' in install
assert 'mv -f "$GAME_DIR/$APK_NAME.tmp" "$GAME_DIR/$APK_NAME" && touch "$GAME_DIR/$APK_NAME"' in install
assert 'steam://addnonsteamgame/' in install and 'python3 -I -c' in install
exec_line = re.search(r'^Exec=(.*)$', desktop, re.M)[1]
assert not re.search(r'[$\\%`]', exec_line), exec_line
assert '~/Downloads/HaloCEQuestVR-SteamFrame/install.sh' in exec_line
# (the bundle: one folder, the APK as the launcher names it, the scripts executable)
OUT.mkdir(parents=True, exist_ok=True)
fake = OUT / 'app-vr-release.apk'
fake.write_bytes(b'PK\x03\x04 not a real APK')
bundle_dir = OUT / 'bundle'
shutil.rmtree(bundle_dir, ignore_errors=True)
subprocess.run(['python3', '-I', str(ROOT / 'tools/steam_frame/bundle.py'), str(fake), str(bundle_dir)], check=True,
               capture_output=True)
with zipfile.ZipFile(bundle_dir / 'HaloCEQuestVR-SteamFrame.zip') as archive:
    entries = {info.filename: info for info in archive.infolist()}
    assert set(entries) == {'HaloCEQuestVR-SteamFrame/' + name for name in (
        'HaloCEQuestVR.apk', 'install.sh', 'launch.sh', 'Install HaloCE Quest VR.desktop', 'README.txt')}
    for name, mode in (('install.sh', 0o755), ('launch.sh', 0o755), ('Install HaloCE Quest VR.desktop', 0o755),
                       ('HaloCEQuestVR.apk', 0o644)):
        assert (entries['HaloCEQuestVR-SteamFrame/' + name].external_attr >> 16) & 0o777 == mode, name
    assert archive.read('HaloCEQuestVR-SteamFrame/HaloCEQuestVR.apk') == fake.read_bytes()
    assert archive.read('HaloCEQuestVR-SteamFrame/launch.sh') == (ROOT / 'tools/steam_frame/launch.sh').read_bytes()
shutil.rmtree(bundle_dir)
fake.unlink()
print('PASS: the Steam Frame ports: the runtime waited for in Lepton (a minute, then the game ends saying why; the '
      'flat screen elsewhere), the clock stepped by display times, extensions listed once, the 72 Hz fall back said '
      'once, no restart on reinstall in Lepton, the quit marker, and the Steam library launcher, installer and bundle')
