"""Test67: GulchCE's own Halo 1 MCC regression tests (pytest), as taken.

The MCC loader, renderer bridges, scripts, saves and menus come from GulchCE
(CC0, on OpenCE build 201). Its tests compile the real sources with narrow
host stubs (tools/harness). This port plays MCC maps solo only
(port/linux/game/mcc_offline.h), so the tests of GulchCE's online MCC games
are adapted where this port deliberately differs; see EXCLUDED.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# (filled in from the first run: each exclusion names its reason)
EXCLUDED = {
}

tests = sorted(str(p) for p in (ROOT / 'tools').glob('test_mcc_*.py') if p.name not in EXCLUDED)
tests.append(str(ROOT / 'tools/test_viewmodel_shield.py'))
result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *tests],
                        cwd=ROOT)
if result.returncode:
    sys.exit('FAIL: GulchCE MCC tests (pytest exit %d)' % result.returncode)
print('PASS: GulchCE MCC tests: %d files (%d adapted out: %s)' % (len(tests), len(EXCLUDED), ', '.join(sorted(EXCLUDED)) or 'none'))
