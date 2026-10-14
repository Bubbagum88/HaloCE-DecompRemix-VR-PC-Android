"""Test67: GulchCE's own Halo 1 MCC regression tests (pytest), as taken.

The MCC loader, renderer bridges, scripts, saves and menus come from GulchCE
(CC0, on OpenCE build 201). Its tests compile the real sources with narrow
host stubs (tools/harness). This port plays MCC maps solo only
(port/linux/game/mcc_offline.h), so the tests of GulchCE's online MCC games
are left out where this port deliberately differs; each names its reason
below (and in TEST67-EVIDENCE.md).

Many of GulchCE's tests compile with -m32 -Werror (long and pointers 4 bytes,
as in the game). A machine that cannot run 32-bit programs (WSL1) cannot
start them: tools/pytest_m32_not_run.py then runs exactly those under qemu-i386
(as test_test31_menu_startup does) and counts them (M32-QEMU-RUN); without
qemu-i386 it skips them and this summary reports them apart, as compiled but
not run, never as passed. The other skips are listed by their reasons.
"""
from pathlib import Path
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# whole files left out, each with its reason
EXCLUDED = {
    "test_mcc_network.py": "GulchCE's online MCC (network 42 messages, MCC_DISTRIBUTED_SEND, speed packet); "
                           "this port plays MCC maps solo only on network 28 (online MCC deferred by the owner)",
    "test_mcc_ui_teams.py": "the MCC in-game team request is GulchCE's network_server_message_handler.c hook "
                            "(an online MCC game's); this port keeps its own handler, MCC solo only",
}
# single tests left out, each with its reason
DESELECTED = {
    "tools/test_mcc_identity.py::test_session_resolution_and_validation":
        "an MCC session is refused by design here (mcc_identity_accept: MCC solo only)",
    "tools/test_mcc_seats.py::test_mcc_seats[replication]":
        "MCC biped seats replicated to network clients (GulchCE's network_objects.c hook, online MCC only)",
    "tools/test_viewmodel_shield.py::test_plasma_first_person_displacement[None]":
        "fails identically against GulchCE's own unchanged rasterizer_xbox_plasma_energy.c in a 64-bit build "
        "(the test targets 32-bit Windows; our draw function is Build 201's, unchanged); its three negative "
        "controls run",
}

tests = sorted(str(p) for p in (ROOT / 'tools').glob('test_mcc_*.py') if p.name not in EXCLUDED)
tests.append(str(ROOT / 'tools/test_viewmodel_shield.py'))
deselect = [arg for test in DESELECTED for arg in ('--deselect', test)]
env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + os.environ.get('PYTHONPATH', ''))
result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                         '-rfEs', *deselect, *tests], cwd=ROOT, env=env, capture_output=True, text=True)
sys.stdout.write(result.stdout[-6000:])
sys.stderr.write(result.stderr[-3000:])
counts = {kind: int(number) for number, kind in re.findall(r"(\d+) (passed|failed|skipped|errors?|deselected)", result.stdout)}
not_run = re.search(r"M32-NOT-RUN: (\d+)", result.stdout)
not_run = int(not_run.group(1)) if not_run else 0
qemu_run = re.search(r"M32-QEMU-RUN: (\d+)", result.stdout)
qemu_run = int(qemu_run.group(1)) if qemu_run else 0
reasons = {}
for number, reason in re.findall(r"^SKIPPED \[(\d+)\] [^\n]*?:\d+: ([^\n]*)$", result.stdout, re.M):
    reasons[reason] = reasons.get(reason, 0) + int(number)
for reason, number in sorted(reasons.items(), key=lambda item: -item[1]):
    print('  skipped %d: %s' % (number, reason))
if result.returncode or counts.get('failed') or counts.get('error') or counts.get('errors'):
    sys.exit('FAIL: GulchCE MCC tests (pytest exit %d)' % result.returncode)
print('PASS: GulchCE MCC tests: %d files, %d passed (%d of them 32-bit programs run under qemu-i386); '
      '%d compiled with -m32 but NOT RUN (no 32-bit execution here); '
      '%d other skips; %d files and %d tests left out for this port (MCC solo only): %s'
      % (len(tests), counts.get('passed', 0), qemu_run, not_run, counts.get('skipped', 0) - not_run,
         len(EXCLUDED), len(DESELECTED), ', '.join(sorted(EXCLUDED)) + '; ' + ', '.join(DESELECTED)))
