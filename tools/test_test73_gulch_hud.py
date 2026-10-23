"""Test73: GulchCE's own tests of its HUD and pause work (to 2026-10-16), which OpenCE 232/235 took and this port
has with them: the scripted HUD timer's digits (f0804e1e), HUD upscaling and ammunition thresholds (9240763d), the
three high-resolution button styles (e8f36b8a, 5f66c519, f6bb6fe4, ac5b303b, ce6cf746, c21ec87e), live high-res
HUD/text settings (ddeb650d, e5513afa), the pause art (a0c20572, c76a3a59, 95489685) and MCC solo Settings pausing
(90b9b8e2). GulchCE's MCC tests run in test_test67_mcc_upstream.

Some read the shipped art with numpy and Pillow, which GulchCE's CI installs (3384f31d). Where either is missing
here those are left out and said so, never counted as passed."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = ['tools/test_hud_timer.py', 'tools/test_hud_upscale.py', 'tools/test_hires_live_settings.py',
         'tools/test_pause_campaign_context.py', 'tools/test_hud_button_style.py', 'tools/test_pause_art.py']
# whole files that import numpy/Pillow at the top, and single tests that import them inside
IMAGE_FILES = ['tools/test_pause_art.py']
# Test73: test_hud_ammo_thresholds.py is a script (no pytest function: pytest collected nothing from it, so it never
# ran here). It compiles the real nv2a_psh.c and draws the meters in a hidden GL context; run as a script below. It
# failed to compile before the renderer half of OpenCE c40d7b22f (key.point_threshold) was ported.
THRESHOLDS = 'tools/test_hud_ammo_thresholds.py'
IMAGE_TESTS = ['tools/test_hud_button_style.py::test_supplied_gems_preserve_transparency_and_fit_existing_bounds',
               'tools/test_hud_button_style.py::test_visible_face_bounds_match_xbox_and_keep_black_white',
               'tools/test_hud_button_style.py::test_supplied_controls_and_animation',
               'tools/test_hud_button_style.py::test_control_visible_bounds_and_animation_slots']
try:
    import numpy  # noqa: F401
    import PIL  # noqa: F401
    image_libraries = True
except ImportError:
    image_libraries = False

tests = [t for t in TESTS if image_libraries or t not in IMAGE_FILES]
deselect = [] if image_libraries else [arg for test in IMAGE_TESTS for arg in ('--deselect', test)]
env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + os.environ.get('PYTHONPATH', ''))
# (Test73: LLVM's clang where the installer puts it, which is not on every PATH: 23 tests skipped as "clang
# required" on this PC although it is installed)
if sys.platform == 'win32' and not shutil.which('clang') and Path(r'C:\Program Files\LLVM\bin\clang.exe').exists():
    env['PATH'] = r'C:\Program Files\LLVM\bin' + os.pathsep + env.get('PATH', '')
result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                         '-rfEs', *deselect, *tests], cwd=ROOT, env=env, capture_output=True, text=True)
sys.stdout.write(result.stdout[-4000:])
sys.stderr.write(result.stderr[-2000:])
counts = {kind: int(number) for number, kind in re.findall(r"(\d+) (passed|failed|skipped|errors?)", result.stdout)}
if not image_libraries:
    print('  NOT RUN (numpy and Pillow are not installed here): %s; %s'
          % (', '.join(IMAGE_FILES), ', '.join(t.split('::')[1] for t in IMAGE_TESTS)))
if result.returncode or counts.get('failed') or counts.get('error') or counts.get('errors'):
    sys.exit('FAIL: GulchCE HUD/pause tests (pytest exit %d)' % result.returncode)

# the ammunition thresholds: numpy/Pillow, clang, and SDL3 (Windows: the windows build's x86 SDL3)
missing = []
if not image_libraries:
    missing.append('numpy/Pillow')
if not shutil.which('clang') and not Path(r'C:\Program Files\LLVM\bin\clang.exe').exists():
    missing.append('clang')
if sys.platform == 'win32' and not list((ROOT / 'build/windows/third_party').glob('SDL3-*/lib/x86/SDL3.lib')):
    missing.append('the windows build\'s SDL3')
if sys.platform != 'win32':
    if not shutil.which('pkg-config') or subprocess.run(['pkg-config', '--exists', 'sdl3']).returncode:
        missing.append('SDL3 (pkg-config sdl3)')
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        missing.append('a display for its hidden GL window')
if missing:
    thresholds = 'NOT RUN (%s missing): %s' % (', '.join(missing), THRESHOLDS)
    print('  ' + thresholds)
else:
    run_env = dict(env)
    if sys.platform == 'win32':
        run_env['PATH'] = r'C:\Program Files\LLVM\bin' + os.pathsep + run_env.get('PATH', '')
    run = subprocess.run([sys.executable, THRESHOLDS], cwd=ROOT, env=run_env, capture_output=True, text=True,
                         timeout=900)
    sys.stdout.write(run.stdout[-1500:])
    sys.stderr.write(run.stderr[-2000:])
    if run.returncode or 'PASS:' not in run.stdout:
        sys.exit('FAIL: %s (exit %d)' % (THRESHOLDS, run.returncode))
    thresholds = 'ammunition thresholds rendered and passed'
print('PASS: GulchCE HUD/pause tests: %d files, %d passed, %d skipped; %s%s'
      % (len(tests), counts.get('passed', 0), counts.get('skipped', 0), thresholds,
         '' if image_libraries else '; %d files and %d tests NOT RUN (no numpy/Pillow)' %
         (len(IMAGE_FILES), len(IMAGE_TESTS))))
