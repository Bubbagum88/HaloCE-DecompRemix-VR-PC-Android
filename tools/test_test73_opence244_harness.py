"""Test73: OpenCE build 244's own harness tests (tools/harness) that this repository did not have (item 7's parity
audit found 12): limp bodies the host moves (limp_body_moves), the object bounds cache (object_bounds_cache), the
sound manager's lifecycle and transitions (sound_lifecycle, sound_transition), a stream's cancellation
(sound_stream_flush), damage from a player no longer there (stale_player_damage), transparent enclosures and the
order of transparent planes (transparent_enclosure, transparent_plane_order), voice routing (voice_route), vote kick
counts (votekick_count) and the widget pool (widget_pool). And build 246's one new harness test, taken as it is:
the co-op scripts' player0 and followers in hs_players' reverse datum order (coop_script_players; its fix,
9d7436bd6 + 9044950d7, is ported in coop_scripts.c).

Taken as build-244 has them, then adapted where this port's code differs on purpose, each marked "HaloCE-Quest-VR":
limp_body_moves (a stand-in for the VR hands' ownership of a body; its "living" control planted in this port's
line), object_bounds_cache (the update's type argument and the vector test's sphere test, halo-ce-universal
b9ac6b855; its invalidation control named in the sphere test), voice_route (the one-byte wire length's cap), and
tools/harness/audio.py (no sinc history in this port's resampler). Two found real gaps, now fixed:
sound_stream_flush (a cancelled stream's finished head was reported SUCCESS, so the game's callback refilled the
stream being stopped: dsound_sdl.c now reports FLUSHED and resets its resampler, as OpenCE does) and
transparent_enclosure (a part with no triangles was skipped, which only the VR body's trimmed parts need:
models.c).

Not here: test_mixer.py, kept in tools/harness/tests: it measures OpenCE's windowed-sinc resampler (zero crossings,
filter table, stretch, its mode reader), which this port deliberately does not have (its own Catmull-Rom curve as
"sinc" and a linear one, audio.resampler, since Test66: the sinc filter is too heavy for the Quest); this port's
resampler is tested by test_test31_audio.

Run here 64-bit (HALO_HARNESS_NATIVE=1), and once more as written (-m32), where a machine that cannot run 32-bit
programs counts them as compiled but not run (tools/pytest_m32_not_run.py), as the 232 suite does.
"""
from pathlib import Path
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['limp_body_moves', 'object_bounds_cache', 'sound_lifecycle', 'sound_stream_flush', 'sound_transition',
         'stale_player_damage', 'transparent_enclosure', 'transparent_plane_order', 'voice_route', 'votekick_count',
         'widget_pool', 'coop_script_players']
TESTS = ['tools/harness/tests/test_%s.py' % name for name in NAMES]

env = dict(os.environ, PYTHONPATH=str(ROOT / 'tools') + os.pathsep + os.environ.get('PYTHONPATH', ''))
native = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-rfE', *TESTS],
                        cwd=ROOT, env=dict(env, HALO_HARNESS_NATIVE='1'), capture_output=True, text=True)
sys.stdout.write(native.stdout[-4000:])
if native.returncode:
    sys.exit('FAIL: OpenCE 244 and 246 harness tests, 64-bit (pytest exit %d)' % native.returncode)
m32 = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'pytest_m32_not_run',
                      '-rfE', *TESTS], cwd=ROOT, env=env, capture_output=True, text=True)
sys.stdout.write(m32.stdout[-2500:])
if m32.returncode:
    sys.exit('FAIL: OpenCE 244 and 246 harness tests, -m32 (pytest exit %d)' % m32.returncode)
passed = re.search(r'(\d+) passed', native.stdout)
not_run = re.search(r'M32-NOT-RUN: (\d+)', m32.stdout)
qemu_run = re.search(r'M32-QEMU-RUN: (\d+)', m32.stdout)
m32_passed = re.search(r'(\d+) passed', m32.stdout)
print('PASS: OpenCE 244 and 246 harness tests (%d files): %s passed 64-bit; -m32: %s passed (%s of them run under qemu-i386), '
      '%s compiled but NOT RUN here' % (len(TESTS), passed.group(1) if passed else '?',
                                        m32_passed.group(1) if m32_passed else '?',
                                        qemu_run.group(1) if qemu_run else '?', not_run.group(1) if not_run else '?'))
