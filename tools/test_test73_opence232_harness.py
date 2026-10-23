"""Test73: OpenCE's own harness tests (tools/harness) for what came with OpenCE build 232 and what no other suite
of this port ran: the text chat's rules (chat_logic), mod files (mod_files), streamer mode's filter (text_filter),
and the older cinematic titles (cinematic_titles) and server teardown (server_teardown).

They compile the real sources with narrow host stubs. Run here 64-bit (HALO_HARNESS_NATIVE=1), and once more as
written (-m32), where a machine that cannot run 32-bit programs counts them as compiled but not run
(tools/pytest_m32_not_run.py), as tools/test_test67_upstream_harness.py does for Test67's.
"""
from pathlib import Path
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# (and streamer mode's word table against its review, tools/test_text_filter_terms.py: the maps' strings where
# assets/maps has them, else skipped. Not here: tools/test_mods.py, which plays mods in the Linux x86 build under
# xvfb, a build this port does not make: mods' file handling is mod_files' here)
# (and the host's taking of a co-op client's player on an elevator, test_elevator_prediction: OpenCE's since
# before 232, taken with 242's network 31 bound)
# (and the profile keyboard's lifetime, its Enter and the names it keeps bannable: test_profile_keyboard, which
# found this port's virtual_keyboard.c without Build 201's player_name_clean and computer-keyboard typing; Test73
# restores both, the port's server-field keyboard and VR pointer kept)
TESTS = ['tools/harness/tests/test_chat_logic.py', 'tools/harness/tests/test_mod_files.py',
         'tools/harness/tests/test_text_filter.py', 'tools/harness/tests/test_cinematic_titles.py',
         'tools/harness/tests/test_server_teardown.py', 'tools/harness/tests/test_profile_keyboard.py',
         'tools/harness/tests/test_elevator_prediction.py', 'tools/test_text_filter_terms.py']

# single tests left out natively, each with its reason (the -m32 run below keeps them)
DESELECTED_NATIVE = {
    'tools/harness/tests/test_chat_logic.py::test_negative_control[mute-wrap-broken]':
        "the fault it plants (no wrap of the mute's clock) shows only with 32-bit longs: a 64-bit clock does not "
        "wrap at 0xFFFFFFFF",
    'tools/harness/tests/test_mod_files.py::test_negative_control[adds-offset-and-size]':
        "the fault it plants (offset + size, which can overflow) shows only with 32-bit longs: a 64-bit sum does not "
        "overflow",
}

env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + os.environ.get('PYTHONPATH', ''))
deselect = [arg for test in DESELECTED_NATIVE for arg in ('--deselect', test)]
native = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-rfE', *deselect, *TESTS],
                        cwd=ROOT, env=dict(env, HALO_HARNESS_NATIVE='1'), capture_output=True, text=True)
sys.stdout.write(native.stdout[-4000:])
if native.returncode:
    sys.exit('FAIL: OpenCE 232 harness tests, 64-bit (pytest exit %d)' % native.returncode)
# (the filter terms' own --check builds its helper -m32 and runs it itself, not through the harness's qemu-i386,
# so a machine without 32-bit execution cannot run it there: it is the native run's)
m32 = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                      '-rfE', *[test for test in TESTS if 'text_filter_terms' not in test]], cwd=ROOT, env=env,
                     capture_output=True, text=True)
sys.stdout.write(m32.stdout[-2500:])
if m32.returncode:
    sys.exit('FAIL: OpenCE 232 harness tests, -m32 (pytest exit %d)' % m32.returncode)
passed = re.search(r'(\d+) passed', native.stdout)
not_run = re.search(r'M32-NOT-RUN: (\d+)', m32.stdout)
qemu_run = re.search(r'M32-QEMU-RUN: (\d+)', m32.stdout)
m32_passed = re.search(r'(\d+) passed', m32.stdout)
print('PASS: OpenCE 232 harness tests (chat logic, mod files, text filter, cinematic titles, server teardown, filter '
      'terms): %s passed 64-bit (%d left out: %s); -m32: %s passed (%s of them run under qemu-i386), %s compiled but '
      'NOT RUN here'
      % (passed.group(1) if passed else '0', len(DESELECTED_NATIVE), '; '.join(DESELECTED_NATIVE.values()),
         m32_passed.group(1) if m32_passed else '0', qemu_run.group(1) if qemu_run else '0',
         not_run.group(1) if not_run else '0'))
