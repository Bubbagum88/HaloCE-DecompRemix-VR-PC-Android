"""Test67: OpenCE's own harness tests for what Test67 took from its testing
branch (52e33a39, "Harden map sharing and Custom Edition map loading"): map
sharing's names and trust, and the Custom Edition geometry size cap.

They compile the real sources with narrow host stubs (tools/harness). Run
here 64-bit (HALO_HARNESS_NATIVE=1: these units have no 32-bit layouts),
and once more as written (-m32), where a machine that cannot run 32-bit
programs counts them as compiled but not run (tools/pytest_m32_not_run.py).
"""
from pathlib import Path
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = ['tools/harness/tests/test_map_share_names.py', 'tools/harness/tests/test_map_share_trust.py',
         'tools/harness/tests/test_map_share_restart.py',
         'tools/harness/tests/test_geometry_bytes.py']
# single tests left out natively, each with its reason
DESELECTED_NATIVE = {
    'tools/harness/tests/test_geometry_bytes.py::test_negative_control[no-count-check]':
        "the fault it plants (no count check) shows only with 32-bit longs: a 64-bit product does not wrap, and "
        "the size check after it refuses the same counts; the -m32 run below keeps it",
}

env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + os.environ.get('PYTHONPATH', ''))
deselect = [arg for test in DESELECTED_NATIVE for arg in ('--deselect', test)]
native = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-rfE', *deselect, *TESTS],
                        cwd=ROOT, env=dict(env, HALO_HARNESS_NATIVE='1'), capture_output=True, text=True)
sys.stdout.write(native.stdout[-3000:])
if native.returncode:
    sys.exit('FAIL: OpenCE harness tests, 64-bit (pytest exit %d)' % native.returncode)
m32 = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                      '-rfE', *TESTS], cwd=ROOT, env=env, capture_output=True, text=True)
sys.stdout.write(m32.stdout[-2000:])
if m32.returncode:
    sys.exit('FAIL: OpenCE harness tests, -m32 (pytest exit %d)' % m32.returncode)
passed = re.search(r'(\d+) passed', native.stdout)
not_run = re.search(r'M32-NOT-RUN: (\d+)', m32.stdout)
qemu_run = re.search(r'M32-QEMU-RUN: (\d+)', m32.stdout)
m32_passed = re.search(r'(\d+) passed', m32.stdout)
print('PASS: OpenCE harness tests: %s passed 64-bit (%d left out: %s); -m32: %s passed (%s of them run under '
      'qemu-i386), %s compiled but NOT RUN here'
      % (passed.group(1) if passed else '0', len(DESELECTED_NATIVE), '; '.join(DESELECTED_NATIVE.values()),
         m32_passed.group(1) if m32_passed else '0', qemu_run.group(1) if qemu_run else '0',
         not_run.group(1) if not_run else '0'))
