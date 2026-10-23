"""Test73, item 8: the Steam Frame plan (Lepton, SteamOS's Android container; Valve's Steamworks Steam Frame pages,
and ringfall-mjolnir-vr's field findings, CC0). The same VR APK as for the Quest and PICO; everything chosen at run
time, inside Lepton only. Not run on a Frame: no device acceptance.

Pinned in the source:
- the launcher, the game and the logs in /home/<user>/Documents/HaloCEQuestVR (Lepton.java, host_main.c);
- a Steam launch (headless) starts the game, unpacks a disc image it finds, or leaves a note;
- the VR game in the main process there (HaloFrameActivity); no self-update; missing pickers reported;
- the fdm_injection pass-through OpenXR layer, in the VR APK only (and the package check knowing it);
- the Frame's and the Index's finger touches, suggested with their profile's bindings or, refused, without them;
- a controller that never reports a touch shows a hand at rest, never the "L" (middle finger) after a second's grip;
- uniform locations asked of GL once; on SteamVR in Lepton the swapchain images released as the frame ends, the
  frames' thread on the fast cores;
- deploy.sh and the docs on the new folder.

Compiled and run (clang, AddressSanitizer): the release state machine (deferred and not, a scripted frame and
200,000 random calls, against a runtime that allows one image out per swapchain), the paired suggestion and its
fallback, the resting hand without touch sensors, lepton_data_root's user names against Lepton.hostUser's
expression, host_lepton_running, and (with the OpenXR headers configure.py fetches) the layer itself: negotiated,
then passing creation and lookups on to the next.
"""
from pathlib import Path
import random
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_frame'


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


def build(name, source, extra=()):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (name + '.c')
    path.write_text(source, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-variable',
                    '-Wno-unused-function', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                    *extra, str(path), '-lm', '-ldl', '-o', str(OUT / name)], check=True)
    return OUT / name


def run(binary, stdin=None):
    result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, input=stdin)
    return result.stdout


lepton = read('port/android/app/src/main/java/com/halo/decomp/Lepton.java')
launcher = read('port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java')
frame_activity = read('port/android/app/src/main/java/com/halo/decomp/HaloFrameActivity.java')
halo_activity = read('port/android/app/src/main/java/com/halo/decomp/HaloActivity.java')
updater = read('port/android/app/src/main/java/com/halo/decomp/Updater.java')
runlog = read('port/android/app/src/main/java/com/halo/decomp/RunLog.java')
data_manager = read('port/android/app/src/main/java/com/halo/decomp/GameDataManager.java')
manifest = read('port/android/app/src/vr/AndroidManifest.xml')
host_main = read('port/android/host/host_main.c')
host_h = read('port/android/host/host.h')
host = read('port/android/host/host_xr.c')
bindings = read('port/android/include/halo_xr_bindings.h')
abi = read('port/android/include/halo_android_abi.h')
frame = read('port/linux/src/vr_frame.c')
android_build = read('tools/android_build.py')
package = read('tools/package-quest.py')
deploy = read('tools/steam_frame/deploy.sh')
layer = read('port/android/xr_layer/fdm_injection_stub.c')
architecture = read('docs/VR_ARCHITECTURE.md')

# ---------- the launcher (Java)
assert 'static final String FOLDER = "HaloCEQuestVR";' in lepton
# (Test73: and Lepton 3's app container flag and model; its maker is "Valve" now, compat_tool/liblepton/properties.sh)
assert ('return !property("lepton.app_id").isEmpty() || !property("waydroid.host.user").isEmpty()\n'
        '            || "true".equals(property("ro.steam.running_in_app_container"))\n'
        '            || "Lepton".equalsIgnoreCase(Build.MODEL) || "Lepton".equalsIgnoreCase(Build.MANUFACTURER);') in lepton
assert 'return "true".equals(property("lepton.headless"));' in lepton
HOST_USER = re.search(r'return user\.matches\("([^"]+)"\) \? user : "steamos";', lepton)[1].replace('\\\\', '\\')
assert HOST_USER == '[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}', HOST_USER
assert 'File root = new File("/home/" + hostUser() + "/Documents/" + FOLDER);' in lepton
assert 'return root.isDirectory() && root.canWrite() ? root : null;' in lepton
assert 'if (Lepton.running() && (Lepton.headless() || haveData())) {' in launcher
assert ('Intent game = new Intent(this, BuildConfig.APPLICATION_ID.endsWith(".vr") && Lepton.running()\n'
        '            ? HaloFrameActivity.class : HaloActivity.class);') in launcher
assert 'File image = Lepton.findDiscImage();' in launcher and 'STEAM-FRAME-README.txt' in launcher
assert 'File lepton = Lepton.dataRoot();' in launcher
# every picker through openPicker (none left to throw ActivityNotFoundException), the data manager's guarded
picker = fn(launcher, 'openPicker')
assert 'catch (ActivityNotFoundException' in picker or 'catch (android.content.ActivityNotFoundException' in picker
outside = launcher.replace(picker, '')
assert launcher.count('openPicker(') >= 7
# (the one other: the app's own mod download page, always there)
assert re.findall(r'startActivityForResult\(([^)]*)\)', outside) == ['intent, MOD_WEB_DOWNLOAD'], \
    re.findall(r'startActivityForResult\(([^)]*)\)', outside)
assert data_manager.count('catch(android.content.ActivityNotFoundException e)') == 2
assert 'public class HaloFrameActivity extends HaloActivity {' in frame_activity
assert 'if (Lepton.running() && Lepton.dataRoot() != null) gameRoot = Lepton.dataRoot();' in halo_activity
assert updater.count('if(Lepton.running()){') == 2
assert 'File lepton = Lepton.running() ? Lepton.dataRoot() : null;' in runlog
entry = manifest[manifest.index('android:name=".HaloFrameActivity"'):]
entry = entry[:entry.index('</activity>')]
assert 'android:exported="false"' in entry and 'android:launchMode="singleTask"' in entry
assert '<intent-filter' not in entry and 'android:process' not in entry
game_entry = manifest[manifest.rindex('<activity', 0, manifest.index('android:name=".HaloActivity"')):]
game_entry = game_entry[:game_entry.index('</activity>')]
assert 'android:process=":halo_game"' in game_entry
# (the rest of HaloActivity's entry is the main manifest's, merged: the same configuration changes kept)
main_manifest = read('port/android/app/src/main/AndroidManifest.xml')
main_entry = main_manifest[main_manifest.index('android:name=".HaloActivity"'):]
main_entry = main_entry[:main_entry.index('</activity>')]
changes = re.search(r'android:configChanges="([^"]+)"', entry)[1]
assert changes == re.search(r'android:configChanges="([^"]+)"', main_entry)[1]
assert 'android:screenOrientation="sensorLandscape"' in entry and 'android:screenOrientation="sensorLandscape"' in main_entry

# ---------- the host (native)
assert 'int host_lepton_running(void);' in host_h
assert 'if (host_lepton_running())\n\t{\n\t\tconst char *lepton = lepton_data_root();' in host_main
assert host_main.index('if (directory_has_maps(SHARED_DATA_ROOT))') < host_main.index('if (host_lepton_running())\n\t{')
# the fast cores, and the deferred releases, chosen in Lepton under SteamVR only
assert '\t\tif (host_lepton_running() && !getenv("HALO_XR_ANY_CORE"))\n\t\t\txr_fast_cores();' in host
assert 'xr.defer_releases = choice && *choice ? atoi(choice) != 0 : xr.steamvr && lepton;' in host
assert '#ifndef _WIN32\n\t\tint lepton = host_lepton_running();\n#else\n\t\tint lepton = 0;\n#endif' in host
assert 'xr.steamvr = strstr(properties.runtimeName, "SteamVR") != NULL;' in host
assert '\t/* (a new swapchain has no image of its own held: Test73) */\n\tswapchain->held = 0;' in fn(host, 'create_swapchain')

# ---------- bindings: the fingers' touches, paired
for table in ('halo_xr_bindings_frame_fingers', 'halo_xr_bindings_index_fingers'):
    body = bindings[bindings.index('static const struct binding %s[] =' % table):]
    body = body[:body.index('};')]
    actions = set(re.findall(r'\{ (_action_\w+), "', body))
    assert actions == {'_action_hand_thumb_touch', '_action_hand_index_touch'}, (table, actions)
    assert '"/user/hand/left/input/trigger/touch"' in body and '"/user/hand/right/input/trigger/touch"' in body
assert ('if (xr.frame_controller)\n\t\tsuggest_pair("/interaction_profiles/valve/frame_controller_valve", '
        'halo_xr_bindings_frame,') in host
assert 'suggest_pair("/interaction_profiles/valve/index_controller", halo_xr_bindings_index,' in host
# the Quest's Touch keeps its one table, its touches in it, as before
assert 'suggest("/interaction_profiles/oculus/touch_controller", halo_xr_bindings_touch,' in host

# ---------- the guest: resting hands without touch sensors, uniforms looked up once
assert ('\t\tif (touch & (HALO_XR_HAND_THUMB_TOUCH | HALO_XR_HAND_INDEX_TOUCH))\n\t\t\tvr.touch_seen[hand] = 1;\n'
        '\t\telse if (!vr.touch_seen[hand])\n\t\t\ttouch |= HALO_XR_HAND_THUMB_TOUCH | HALO_XR_HAND_INDEX_TOUCH;') in frame
assert len(re.findall(r'glUniform\w+\(uniform_location\(', frame)) == 15
assert frame.count('glGetUniformLocation(') == 2  # (only in uniform_location)
assert all('glGetUniformLocation' not in line for line in frame.splitlines() if 'glUniform' in line)

# ---------- the layer, its build and the package check
assert 'XRAPI_ATTR XrResult XRAPI_CALL xrNegotiateLoaderApiLayerInterface(' in layer
assert 'github.com/Cesarus85/ringfall-mjolnir-vr' in layer and 'CC0 1.0' in layer
assert 'staged_fdm_stub = BUILD / "jniLibs-vr" / "arm64-v8a" / "libVkLayer_VALVE_fdm_injection.so"' in android_build
assert android_build.index('if vr:\n        # beside, not among') < android_build.index('staged_fdm_stub = ')
assert '-fvisibility=hidden' in android_build and 'staged.append(staged_fdm_stub)' in android_build
assert 'STEAM_FRAME_LAYER = "lib/arm64-v8a/libVkLayer_VALVE_fdm_injection.so"' in package
assert 'if candidate_at_least(args.label, 73) and (STEAM_FRAME_LAYER in names) != vr:' in package
assert 'VR_ONLY_ENTRIES = {"lib/arm64-v8a/libopenxr_loader.so"}' in package

# ---------- deploy.sh and the docs
assert 'Documents/HaloCE/' not in deploy and "ssh \"$frame_host\" 'mkdir -p ~/Documents/HaloCEQuestVR/maps'" in deploy
assert "chmod -R a+rwX ~/Documents/HaloCEQuestVR" in deploy
assert '## Test73: the Steam Frame plan (item 8, 2026-10-20)' in architecture
assert '**not been run on a Frame**' in architecture

# ---------- compiled: the swapchain releases (host_xr.c's own functions, against a fake runtime)
count = int(re.search(r'#define HALO_XR_SWAPCHAIN_COUNT (\d+)', abi)[1])
right = int(re.search(r'#define HALO_XR_SWAPCHAIN_RIGHT (\d+)', abi)[1])
swapchain_struct = re.search(r'struct swapchain\n\{.*?\n\};', host, re.S)[0]
end_start = host.index('\tfor (which = 0; which < HALO_XR_SWAPCHAIN_COUNT; which++)\n\t\thost_xr_release((uint32_t)which);')
end_stop = host.index('release_image(&xr.swapchains[which]);\n\t}\n', end_start) + len('release_image(&xr.swapchains[which]);\n\t}\n')
releases = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define HALO_XR_SWAPCHAIN_COUNT %d
#define HALO_XR_SWAPCHAIN_RIGHT %d
#define HALO_XR_MAXIMUM_IMAGES 4
typedef int XrResult;
typedef uintptr_t XrSwapchain;
typedef struct { int type; } XrSwapchainImageAcquireInfo, XrSwapchainImageReleaseInfo;
typedef struct { int type; long long timeout; } XrSwapchainImageWaitInfo;
#define XR_TYPE_SWAPCHAIN_IMAGE_ACQUIRE_INFO 1
#define XR_TYPE_SWAPCHAIN_IMAGE_WAIT_INFO 2
#define XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO 3
#define XR_INFINITE_DURATION 0x7fffffffffffffffLL
%s
static struct { int frame_begun, defer_releases; struct swapchain swapchains[HALO_XR_SWAPCHAIN_COUNT]; } xr;
/* the runtime: one image out per swapchain at a time; every call in order */
static int out[HALO_XR_SWAPCHAIN_COUNT], errors, acquires, released, flushes;
static XrResult xrAcquireSwapchainImage(XrSwapchain s, const XrSwapchainImageAcquireInfo *i, uint32_t *index)
{ (void)i; if (out[s - 1]++) errors++; acquires++; *index = 0; return 0; }
static XrResult xrWaitSwapchainImage(XrSwapchain s, const XrSwapchainImageWaitInfo *i) { (void)s; (void)i; return 0; }
static XrResult xrReleaseSwapchainImage(XrSwapchain s, const XrSwapchainImageReleaseInfo *i)
{ (void)i; if (!out[s - 1]) errors++; else out[s - 1]--; released++; return 0; }
static void glFlush(void) { flushes++; }
static int check(XrResult r, const char *what) { (void)what; return r >= 0; }
%s%s%s
static void end_frame(void)
{
	int which;

%s}

static void reset(int defer)
{
	int which;

	memset(&xr, 0, sizeof(xr));
	memset(out, 0, sizeof(out));
	errors = acquires = released = flushes = 0;
	xr.frame_begun = 1;
	xr.defer_releases = defer;
	for (which = 0; which < HALO_XR_SWAPCHAIN_COUNT; which++)
		xr.swapchains[which].handle = (XrSwapchain)(which + 1);
}

static void none_out(void)
{
	int which;

	for (which = 0; which < HALO_XR_SWAPCHAIN_COUNT; which++)
		assert(!out[which] && !xr.swapchains[which].held && !xr.swapchains[which].acquired);
}

int main(void)
{
	int defer, frames;
	unsigned int state = 12345;

	for (defer = 0; defer < 2; defer++)
	{
		/* a frame as the game draws it: the eyes, the HUD drawn twice, a swapchain the guest never released */
		reset(defer);
		for (frames = 0; frames < 3; frames++)
		{
			int during;

			assert(host_xr_acquire(0) == 0); host_xr_release(0);
			assert(host_xr_acquire(1) == 0); host_xr_release(1);
			assert(host_xr_acquire(2) == 0); host_xr_release(2);
			assert(host_xr_acquire(2) == 0); host_xr_release(2);
			assert(host_xr_acquire(4) == 0);
			assert(host_xr_acquire(4) == -1); /* (acquired, not released: as before) */
			during = released;
			end_frame();
			none_out();
			/* deferred: only the HUD's first image let go in the frame (drawn again); else each as drawn */
			assert(during == frames * 5 + (defer ? 1 : 4));
			assert(released == (frames + 1) * 5 && acquires == (frames + 1) * 5);
			assert(flushes == (defer ? frames + 1 : 0));
		}
		assert(!errors);
		/* 200,000 calls at random, a frame ended now and then */
		reset(defer);
		for (frames = 0; frames < 200000; frames++)
		{
			unsigned int which, op;

			state ^= state << 13; state ^= state >> 17; state ^= state << 5;
			which = (state >> 8) %% HALO_XR_SWAPCHAIN_COUNT;
			op = state %% 16;
			if (op < 7)
				host_xr_acquire(which);
			else if (op < 14)
				host_xr_release(which);
			else
			{
				end_frame();
				none_out();
			}
			assert(!errors);
			if (!defer)
				assert(!xr.swapchains[which].held);
		}
		end_frame();
		none_out();
		assert(!errors);
		printf("releases %%s: scripted frames and 200000 random calls in order, none left out\n",
			defer ? "deferred" : "one by one");
	}
	return 0;
}
''' % (count, right, swapchain_struct, fn(host, 'release_image'), fn(host, 'host_xr_acquire'),
       fn(host, 'host_xr_release'), host[end_start:end_stop])
print(run(build('releases', releases)).strip())

# ---------- compiled: the paired suggestion and its fallback
action_enum = bindings[bindings.index('enum\n{'):bindings.index('};', bindings.index('enum\n{')) + 2]
suggest_source = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int XrResult;
typedef uintptr_t XrAction, XrPath, XrInstance;
#define XR_SUCCEEDED(r) ((r) >= 0)
#define XR_ERROR_VALIDATION_FAILURE -1
#define XR_ERROR_PATH_UNSUPPORTED -19
#define XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING 51
#define HOST_LOG_INFO 4
typedef struct { XrAction action; XrPath binding; } XrActionSuggestedBinding;
typedef struct { int type; const void *next; XrPath interactionProfile; uint32_t countSuggestedBindings;
	const XrActionSuggestedBinding *suggestedBindings; } XrInteractionProfileSuggestedBinding;
%s
struct binding { int action; const char *path; };
static struct { XrInstance instance; XrAction actions[NUMBER_OF_ACTIONS]; } xr;
static const char *paths[512];
static int path_count, refuse_over, calls, counts[4], lines;
static XrPath path(const char *text)
{
	assert(path_count < 512);
	paths[path_count] = text;
	return (XrPath)++path_count;
}
static const char *result_name(XrResult r) { return r == XR_ERROR_PATH_UNSUPPORTED ? "XR_ERROR_PATH_UNSUPPORTED" : "?"; }
static void host_logf(int priority, const char *format, ...) { (void)priority; (void)format; lines++; }
static const struct binding *expect_a, *expect_b;
static int expect_a_count;
static XrResult xrSuggestInteractionProfileBindings(XrInstance instance, const XrInteractionProfileSuggestedBinding *info)
{
	uint32_t index;

	(void)instance;
	assert(calls < 4);
	counts[calls++] = (int)info->countSuggestedBindings;
	assert(!strcmp(paths[info->interactionProfile - 1], "/interaction_profiles/test"));
	for (index = 0; index < info->countSuggestedBindings; index++)
	{
		const struct binding *b = (int)index < expect_a_count ? &expect_a[index] : &expect_b[index - expect_a_count];

		assert(!strcmp(paths[info->suggestedBindings[index].binding - 1], b->path));
		assert(info->suggestedBindings[index].action == xr.actions[b->action]);
	}
	return refuse_over && (int)info->countSuggestedBindings > refuse_over ? XR_ERROR_PATH_UNSUPPORTED : 0;
}
#define POSES(hand) \
	{ _action_grip_pose, "/user/hand/" hand "/input/grip/pose" }, \
	{ _action_aim_pose, "/user/hand/" hand "/input/aim/pose" }, \
	{ _action_haptic, "/user/hand/" hand "/output/haptic" }
%s%s%s%s%s%s
static void pair(const struct binding *a, int na, const struct binding *b, int nb, int refuse)
{
	calls = 0;
	refuse_over = refuse;
	expect_a = a; expect_a_count = na; expect_b = b;
	suggest_pair("/interaction_profiles/test", a, na, b, nb);
	if (!refuse)
		assert(calls == 1 && counts[0] == na + nb);
	else
	{
		assert(calls == 2 && counts[0] == na + nb && counts[1] == na);
	}
}

int main(void)
{
	int index;

	for (index = 0; index < NUMBER_OF_ACTIONS; index++)
		xr.actions[index] = (XrAction)(1000 + index);
#define N(t) (int)(sizeof(t) / sizeof(t[0]))
	pair(halo_xr_bindings_frame, N(halo_xr_bindings_frame), halo_xr_bindings_frame_fingers, N(halo_xr_bindings_frame_fingers), 0);
	pair(halo_xr_bindings_frame, N(halo_xr_bindings_frame), halo_xr_bindings_frame_fingers, N(halo_xr_bindings_frame_fingers),
		N(halo_xr_bindings_frame));
	pair(halo_xr_bindings_index, N(halo_xr_bindings_index), halo_xr_bindings_index_fingers, N(halo_xr_bindings_index_fingers), 0);
	pair(halo_xr_bindings_index, N(halo_xr_bindings_index), halo_xr_bindings_index_fingers, N(halo_xr_bindings_index_fingers),
		N(halo_xr_bindings_index));
	/* (the pair fits the suggestion's array: else the table alone, at once) */
	assert(N(halo_xr_bindings_frame) + N(halo_xr_bindings_frame_fingers) <= SUGGESTED_MAX);
	assert(N(halo_xr_bindings_index) + N(halo_xr_bindings_index_fingers) <= SUGGESTED_MAX);
	printf("suggest_pair: the Frame's %%d+%%d and the Index's %%d+%%d bindings together, or refused, the table alone\n",
		N(halo_xr_bindings_frame), N(halo_xr_bindings_frame_fingers), N(halo_xr_bindings_index), N(halo_xr_bindings_index_fingers));
	return 0;
}
'''


def table(name):
    start = bindings.index('static const struct binding %s[] =' % name)
    return bindings[start:bindings.index('\n};', start) + 3] + '\n'


suggest_source = suggest_source % (
    action_enum, '#define SUGGESTED_MAX (NUMBER_OF_ACTIONS * 2)\n', fn(host, 'suggest'), fn(host, 'suggest_pair'),
    table('halo_xr_bindings_frame') + table('halo_xr_bindings_frame_fingers'),
    table('halo_xr_bindings_index') + table('halo_xr_bindings_index_fingers'), '')
assert '#define SUGGESTED_MAX (NUMBER_OF_ACTIONS * 2)\n' in host
print(run(build('suggest', suggest_source)).strip())

# ---------- compiled: the fingers' targets (vr_frame.c's own lines)
finger_start = frame.index('\tif (vr.touch_profile != vr.frame.controller_profile)')
finger_stop = frame.index('\t\tfor (finger = 0; finger < 4; finger++)', finger_start)
fingers_source = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#define HALO_XR_HAND_THUMB_TOUCH %s
#define HALO_XR_HAND_INDEX_TOUCH %s
static struct
{
	struct { unsigned int hand_buttons[2], controller_profile; float trigger[2], squeeze[2]; } frame;
	unsigned char touch_seen[2];
	unsigned int touch_profile;
	float l_pose_held[2];
} vr;
static float targets[2][4];

static void step(float seconds)
{
	int hand;

%s		targets[hand][0] = target[0]; targets[hand][1] = target[1];
		targets[hand][2] = target[2]; targets[hand][3] = target[3];
	}
}

int main(void)
{
	int tick;

	/* no touch sensors (HP Reverb G2, or touches refused): a full grip for three seconds, the hand at rest on it */
	vr.frame.controller_profile = 6;
	vr.frame.squeeze[0] = vr.frame.squeeze[1] = 1.0f;
	for (tick = 0; tick < 300; tick++)
	{
		step(0.01f);
		assert(targets[0][0] == 0.75f && targets[0][1] == 0.22f && targets[0][2] == 1.0f && vr.l_pose_held[0] == 0.0f);
	}
	/* the trigger still curls the index finger */
	vr.frame.trigger[1] = 0.9f;
	step(0.01f);
	assert(targets[1][1] == 0.9f);
	/* Touch: a touch seen, then none with the grip held: the "L" after a second, as before */
	vr.frame.controller_profile = 1;
	vr.frame.hand_buttons[0] = HALO_XR_HAND_THUMB_TOUCH;
	step(0.01f);
	assert(vr.touch_seen[0] && !vr.touch_seen[1]);
	vr.frame.hand_buttons[0] = 0;
	for (tick = 0; tick < 99; tick++)
		step(0.01f);
	assert(targets[0][0] == 0.0f && vr.l_pose_held[0] < 1.0f);
	for (tick = 0; tick < 3; tick++)
		step(0.01f);
	assert(vr.l_pose_held[0] >= 1.0f && targets[0][0] == 0.8f && targets[0][1] == 1.0f && targets[0][2] == 0.0f);
	/* the other hand, never touched, at rest */
	assert(targets[1][0] == 0.75f && vr.l_pose_held[1] == 0.0f);
	/* other controllers: seen again from the start */
	vr.frame.controller_profile = 2;
	step(0.01f);
	assert(!vr.touch_seen[0] && targets[0][0] == 0.75f && vr.l_pose_held[0] == 0.0f);
	printf("fingers: without touch sensors a hand at rest, never the L; with them as before\n");
	return 0;
}
''' % (re.search(r'#define HALO_XR_HAND_THUMB_TOUCH (\w+)', abi)[1], re.search(r'#define HALO_XR_HAND_INDEX_TOUCH (\w+)', abi)[1],
       frame[finger_start:finger_stop])
print(run(build('fingers', fingers_source)).strip())

# ---------- compiled: lepton_data_root's user names (C) against Lepton.hostUser's expression (Java), and detection
lepton_source = r'''
#include <stdio.h>
#include <string.h>
#include <strings.h>
#define PROP_VALUE_MAX 92
#define W_OK 2
static char property_user[PROP_VALUE_MAX], property_app[PROP_VALUE_MAX], property_maker[PROP_VALUE_MAX],
	property_model[PROP_VALUE_MAX], property_container[PROP_VALUE_MAX];
static int __system_property_get(const char *name, char *value)
{
	const char *from = !strcmp(name, "waydroid.host.user") ? property_user : !strcmp(name, "lepton.app_id") ?
		property_app : !strcmp(name, "ro.product.manufacturer") ? property_maker :
		!strcmp(name, "ro.product.model") ? property_model :
		!strcmp(name, "ro.steam.running_in_app_container") ? property_container : "";

	snprintf(value, PROP_VALUE_MAX, "%%s", from);
	return (int)strlen(value);
}
static int fake_mkdir(const char *path) { (void)path; return 0; }
#define mkdir(path, mode) fake_mkdir(path)
#define access(path, mode) 0
%s%s
int main(void)
{
	char line[256];

	/* detection: each of the three alone */
	if (host_lepton_running()) return 1;
	snprintf(property_app, sizeof(property_app), "4290000001");
	if (!host_lepton_running()) return 2;
	property_app[0] = 0;
	snprintf(property_maker, sizeof(property_maker), "lEpToN");
	if (!host_lepton_running()) return 3;
	snprintf(property_maker, sizeof(property_maker), "Oculus");
	if (host_lepton_running()) return 4;
	/* (Test73: Lepton 3's, each alone: its maker "Valve" is not Lepton on its own) */
	snprintf(property_maker, sizeof(property_maker), "Valve");
	if (host_lepton_running()) return 6;
	snprintf(property_model, sizeof(property_model), "Lepton");
	if (!host_lepton_running()) return 7;
	property_model[0] = 0;
	snprintf(property_container, sizeof(property_container), "true");
	if (!host_lepton_running()) return 8;
	snprintf(property_container, sizeof(property_container), "false");
	if (host_lepton_running()) return 9;
	property_container[0] = 0;
	snprintf(property_user, sizeof(property_user), "steamos");
	if (!host_lepton_running()) return 5;
	/* the user names, one a line */
	while (fgets(line, sizeof(line), stdin))
	{
		line[strcspn(line, "\n")] = 0;
		snprintf(property_user, sizeof(property_user), "%%s", line);
		printf("%%s\n", lepton_data_root());
	}
	return 0;
}
''' % (fn(host_main, 'host_lepton_running'), fn(host_main, 'lepton_data_root'))
rng = random.Random(73)
alphabet = 'abcXYZ019_.-/ \\$~'
users = ['', 'steamos', 'deck', 'a' * 32, 'a' * 33, '.hidden', '-x', 'x.y-z_1', '../etc', 'a/b', 'café', '_', '9',
         'user name', 'x' * 31 + '.', 'root\\x']
users += [''.join(rng.choice(alphabet) for _ in range(rng.randint(1, 40))) for _ in range(20000)]
binary = build('lepton', lepton_source)
roots = run(binary, '\n'.join(users) + '\n').splitlines()
assert len(roots) == len(users)
for user, root in zip(users, roots):
    # (the C reads the property's bytes; Java the same name's characters: a non-ASCII one is refused by both)
    expected = user if user and re.fullmatch(HOST_USER, user) and user.isascii() else 'steamos'
    assert root == '/home/%s/Documents/HaloCEQuestVR' % expected, (user, root)
print('lepton_data_root: %d user names chosen as Lepton.hostUser chooses them; detection by each property' % len(users))

# ---------- compiled: the layer, negotiated and passing everything on (needs configure.py's OpenXR headers)
headers = sorted(ROOT.glob('build/*/third_party/openxr-*/include/openxr/openxr_loader_negotiation.h'))
if headers:
    include = headers[0].parents[1]
    OUT.mkdir(parents=True, exist_ok=True)
    library = OUT / 'libVkLayer_VALVE_fdm_injection.so'
    subprocess.run(['clang', '-O2', '-fPIC', '-shared', '-fvisibility=hidden', '-Wall', '-Werror', '-I' + str(include),
                    str(ROOT / 'port/android/xr_layer/fdm_injection_stub.c'), '-o', str(library)], check=True)
    exported = subprocess.run(['nm', '-D', '--defined-only', str(library)], check=True, capture_output=True,
                              text=True).stdout.split()
    assert [s for s in exported if s.startswith('xr')] == ['xrNegotiateLoaderApiLayerInterface'], exported
    layer_test = r'''
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <openxr/openxr.h>
#include <openxr/openxr_loader_negotiation.h>
static int created, looked_up;
static XrInstance made = (XrInstance)(uintptr_t)0x1234;
static XRAPI_ATTR XrResult XRAPI_CALL next_lookup(XrInstance instance, const char *name, PFN_xrVoidFunction *function)
{
	looked_up++;
	assert(instance == made && !strcmp(name, "xrCreateSession"));
	*function = (PFN_xrVoidFunction)next_lookup;
	return XR_SUCCESS;
}
static XRAPI_ATTR XrResult XRAPI_CALL next_create(const XrInstanceCreateInfo *info, const XrApiLayerCreateInfo *layer,
	XrInstance *instance)
{
	created++;
	assert(info && layer && layer->nextInfo == NULL);
	*instance = made;
	return XR_SUCCESS;
}
int main(int argc, char **argv)
{
	void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
	PFN_xrNegotiateLoaderApiLayerInterface negotiate;
	XrNegotiateLoaderInfo loader = { XR_LOADER_INTERFACE_STRUCT_LOADER_INFO, XR_LOADER_INFO_STRUCT_VERSION,
		sizeof(XrNegotiateLoaderInfo), 1, XR_CURRENT_LOADER_API_LAYER_VERSION, XR_MAKE_VERSION(1, 0, 0),
		XR_MAKE_VERSION(1, 0, 0) };
	XrNegotiateApiLayerRequest request = { XR_LOADER_INTERFACE_STRUCT_API_LAYER_REQUEST,
		XR_API_LAYER_INFO_STRUCT_VERSION, sizeof(XrNegotiateApiLayerRequest) };
	XrApiLayerNextInfo next = { XR_LOADER_INTERFACE_STRUCT_API_LAYER_NEXT_INFO, XR_API_LAYER_NEXT_INFO_STRUCT_VERSION,
		sizeof(XrApiLayerNextInfo), "XR_APILAYER_VALVE_fdm_injection", next_lookup, next_create, NULL };
	XrApiLayerCreateInfo layer_info = { XR_LOADER_INTERFACE_STRUCT_API_LAYER_CREATE_INFO,
		XR_API_LAYER_CREATE_INFO_STRUCT_VERSION, sizeof(XrApiLayerCreateInfo), NULL, { 0 }, &next };
	XrInstanceCreateInfo create = { XR_TYPE_INSTANCE_CREATE_INFO };
	XrInstance instance = XR_NULL_HANDLE;
	PFN_xrVoidFunction function = NULL;
	XrNegotiateLoaderInfo too_new = loader;

	(void)argc;
	assert(library);
	negotiate = (PFN_xrNegotiateLoaderApiLayerInterface)dlsym(library, "xrNegotiateLoaderApiLayerInterface");
	assert(negotiate);
	too_new.minInterfaceVersion = XR_CURRENT_LOADER_API_LAYER_VERSION + 1;
	too_new.maxInterfaceVersion = XR_CURRENT_LOADER_API_LAYER_VERSION + 1;
	assert(negotiate(&too_new, "XR_APILAYER_VALVE_fdm_injection", &request) == XR_ERROR_INITIALIZATION_FAILED);
	assert(negotiate(&loader, "XR_APILAYER_VALVE_fdm_injection", &request) == XR_SUCCESS);
	assert(request.layerInterfaceVersion == XR_CURRENT_LOADER_API_LAYER_VERSION);
	assert(request.layerApiVersion == XR_MAKE_VERSION(1, 0, 0));
	/* before an instance: nothing to hand on to */
	assert(request.getInstanceProcAddr(XR_NULL_HANDLE, "xrCreateSession", &function) == XR_ERROR_HANDLE_INVALID);
	assert(request.createApiLayerInstance(&create, &layer_info, &instance) == XR_SUCCESS && instance == made);
	assert(request.getInstanceProcAddr(instance, "xrCreateSession", &function) == XR_SUCCESS);
	assert(function == (PFN_xrVoidFunction)next_lookup && created == 1 && looked_up == 1);
	printf("fdm_injection stub: negotiated, creation and lookups handed on to the next layer\n");
	return 0;
}
'''
    path = OUT / 'layer_test.c'
    path.write_text(layer_test, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Werror', '-I' + str(include), str(path), '-ldl', '-o',
                    str(OUT / 'layer_test')], check=True)
    print(subprocess.run([str(OUT / 'layer_test'), str(library)], check=True, capture_output=True,
                         text=True).stdout.strip())
else:
    print('fdm_injection stub harness: not run (no OpenXR headers yet: configure.py --vr fetches them)')

print('PASS: Test73 Steam Frame: Lepton data folder, headless start, main-process game, fdm layer, paired finger '
      'touches, resting hands without sensors, uniforms once, deferred releases')
