"""Test73: OpenCE's own harness tests (tools/harness) that no runner here ran, and OpenCE Build 249 to 256's and its
testing branch's. The Build 256 audit found 19 of tools/harness/tests run by nothing (aim_assist, biped_discard,
bots_lobby, button_presets, coop_monitor, coop_pickups, coop_scaling_menu, coop_vehicles, elevator_carry,
elevator_correction, latency_meter, lobby_countdown, model_detail, queue_reset, screen_effect_passes, sound_orphan,
structure_culling, texture_idle, unicode_line_breaks; `_scratch/t72/harness_coverage.py` lists them). With them, the
ones the Build 249 to 256 port took: coop_gate (cdce33647, the co-op Pillar of Autumn softlock), visibility_readback
(a0f22cbba), coop_ally_friendly_fire (1d38b3f93, network 33) and static_target (the fix-scenery-shields-network
branch, 5744d2d17 to 4ab042e14, network 34). And the two Android pytest files of 3975480a3 (Custom Edition texture
residency), tools/test_android_ce_texture_cache.py and tools/test_android_mirror_uploads.py.

Taken as upstream has them, then adapted where this port's code differs on purpose, each marked "HaloCE-Quest-VR":
biped_discard (this port's biped_port_may_discard: a body held in VR is never erased, and a client notes once that
the host's fallen biped is the host's to erase), static_target (this port's static_target_shields: a client of a
host before 34 keeps that host's static targets), coop_scaling_menu (this port's VR INTERACTIONS, the ninth CO-OP
OPTIONS row, laid out on the same line) and visibility_readback (this port's debug.fixed_step wait, and a fixed step's
batch not waited for).

Run here 64-bit (HALO_HARNESS_NATIVE=1) less the cases that assert the game's 32-bit layout (DESELECTED_NATIVE), and
once more as written (-m32), where a machine that cannot run 32-bit programs counts them as compiled but not run
(tools/pytest_m32_not_run.py), as the 232 and 244 suites do. The Android files build -m32 themselves, so they run in
the second pass only.
"""
from pathlib import Path
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['aim_assist', 'biped_discard', 'bots_lobby', 'button_presets', 'coop_monitor', 'coop_pickups',
         'coop_scaling_menu', 'coop_vehicles', 'elevator_carry', 'elevator_correction', 'latency_meter',
         'lobby_countdown', 'model_detail', 'queue_reset', 'screen_effect_passes', 'sound_orphan', 'structure_culling',
         'texture_idle', 'unicode_line_breaks',
         'coop_gate', 'visibility_readback', 'coop_ally_friendly_fire', 'static_target']
TESTS = ['tools/harness/tests/test_%s.py' % name for name in NAMES]
ANDROID = ['tools/test_android_ce_texture_cache.py', 'tools/test_android_mirror_uploads.py']

# cases left out natively, each with its reason (the -m32 run below keeps them)
DESELECTED_NATIVE = {
    'tools/harness/tests/test_coop_gate.py::test_gate':
        "it checks the checkpoint's 32-bit layout first (sizeof(struct object_list_header_datum) == 12), which "
        "64-bit pointers change",
    'tools/harness/tests/test_aim_assist.py::test_case':
        "the host's aim assist policy (message 90) is checked as its 12-byte wire layout, 32-bit longs'",
    'tools/harness/tests/test_latency_meter.py::test_case[since-tick-bounds]':
        "the meter's tick clock is checked across a 32-bit wrap, which a 64-bit long does not take",
    'tools/harness/tests/test_structure_culling.py::test_case[load-small-group-scratch]':
        "the scratch's byte count (956) is the 32-bit structures'",
    'tools/harness/tests/test_structure_culling.py::test_case[compact-allocation-failure]':
        "the compact allocation's offsets are the 32-bit structures'",
}

env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + os.environ.get('PYTHONPATH', ''))
deselect = [arg for test in DESELECTED_NATIVE for arg in ('--deselect', test)]
native = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-rfE', *deselect, *TESTS],
                        cwd=ROOT, env=dict(env, HALO_HARNESS_NATIVE='1'), capture_output=True, text=True)
sys.stdout.write(native.stdout[-4000:])
if native.returncode:
    sys.exit('FAIL: OpenCE 256 harness tests, 64-bit (pytest exit %d)' % native.returncode)
m32 = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                      '-rfE', *TESTS, *ANDROID], cwd=ROOT, env=env, capture_output=True, text=True)
sys.stdout.write(m32.stdout[-2500:])
if m32.returncode:
    sys.exit('FAIL: OpenCE 256 harness and Android tests, -m32 (pytest exit %d)' % m32.returncode)
passed = re.search(r'(\d+) passed', native.stdout)
deselected = re.search(r'(\d+) deselected', native.stdout)
not_run = re.search(r'M32-NOT-RUN: (\d+)', m32.stdout)
qemu_run = re.search(r'M32-QEMU-RUN: (\d+)', m32.stdout)
m32_passed = re.search(r'(\d+) passed', m32.stdout)
print('PASS: OpenCE 256 harness tests (%d files) and its 2 Android files: %s passed 64-bit (%s deselected: %s); '
      '-m32: %s passed (%s of them run under qemu-i386), %s compiled but NOT RUN here'
      % (len(TESTS), passed.group(1) if passed else '?', deselected.group(1) if deselected else '0',
         '; '.join(DESELECTED_NATIVE.values()), m32_passed.group(1) if m32_passed else '?',
         qemu_run.group(1) if qemu_run else '?', not_run.group(1) if not_run else '?'))
