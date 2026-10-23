"""Test73: tools/test_linux_port.py (pytest), OpenCE's checks of the Linux
tooling, menus, settings, brokers, config sections, stand-in machines, wire
format, lobby and map validator, as taken in the 242 merge and adapted to
this port (its menus' per-build variants, its built-in broker list, a
build.ninja configured on Windows), run with the suite.

The lobby check is a 32-bit program: where this machine cannot run those
(WSL1), tools/pytest_m32_not_run.py runs it under qemu-i386 and counts it as
such; without qemu it is a skip that says so, never a pass. The map
validator's tests need game maps (assets/maps, assets/custom_edition) and a
Linux build of map_validate, which this checkout does not hold: they are
skips, reported by name.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    import pytest  # noqa: F401
except ImportError:
    sys.exit('FAIL: pytest is not installed (python3 -m pip install pytest)')
env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + str(ROOT) + os.pathsep +
           os.environ.get('PYTHONPATH', ''))
result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                         '-rfEs', 'tools/test_linux_port.py'], cwd=ROOT, env=env, capture_output=True, text=True)
sys.stdout.write(result.stdout[-6000:])
sys.stderr.write(result.stderr[-3000:])
counts = {kind: int(number) for number, kind in re.findall(r"(\d+) (passed|failed|skipped|errors?)", result.stdout)}
qemu_run = re.search(r"M32-QEMU-RUN: (\d+)", result.stdout)
not_run = re.search(r"M32-NOT-RUN: (\d+)", result.stdout)
reasons = {}
for number, reason in re.findall(r"^SKIPPED \[(\d+)\] [^\n]*?:\d+: ([^\n]*)$", result.stdout, re.M):
    reasons[reason] = reasons.get(reason, 0) + int(number)
for reason, number in sorted(reasons.items(), key=lambda item: -item[1]):
    print('  skipped %d: %s' % (number, reason))
if result.returncode or counts.get('failed') or counts.get('error') or counts.get('errors') or not counts.get('passed'):
    sys.exit('FAIL: tools/test_linux_port.py (pytest exit %d)' % result.returncode)
print('PASS: tools/test_linux_port.py: %d passed (%d 32-bit programs run under qemu-i386, %d compiled but NOT RUN), '
      '%d skipped (above)' % (counts.get('passed', 0), int(qemu_run.group(1)) if qemu_run else 0,
                              int(not_run.group(1)) if not_run else 0, counts.get('skipped', 0)))
