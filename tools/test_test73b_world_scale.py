"""Test73b: WORLD SCALE in the VR menu (a request the owner relayed: "a world scale slider/option in the menu. make it
proper and work accordingly like most other world scale options in vr games").

VR SETTINGS > COMFORT > WORLD SCALE (vr.world_size, 70% to 150%, 100% the world's true size): the game units a metre of
the eyes' separation and of the head's and hands' movement make are vr.world_scale's (the game's 10-foot unit, 0.328084
a metre, the advanced setting kept) divided by it, so at 120% the world is a fifth bigger around the player (the
player a fifth smaller) and at 80% smaller, as other games' world scales work: stereo depth, motion and reach scale
together. It takes effect at once (vr_reload_settings, which every VR menu change runs), and everything in metres
takes it through vr_units_per_metre (reach, holsters, melee speed); the compositor's panels (menus, HUD) keep their
size.

Run here: vr_reload_settings' block (production) against stand-in settings, with negative controls; the menu row,
the setting, and the path from the eyes' poses to the view.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8')
frame = read('port/linux/src/vr_frame.c')
config = read('port/linux/src/port_config.c')
menu = read('port/linux/game/vr_menu.c')
remote = read('port/linux/game/vr_world_remote.c')

# ---------- the setting and its row
assert '{ "vr.world_scale", _config_real, "0.328084", "HALO_VR_WORLD_SCALE",' in config
assert '{ "vr.world_size", _config_real, "1.0", "HALO_VR_WORLD_SIZE", _environment_value, _platform_vr,' in config
comfort = menu[menu.index('static struct vr_menu_setting const vr_menu_comfort[] ='):]
comfort = comfort[:comfort.index('};')]
row = next(line for line in comfort.splitlines() if '"WORLD SCALE"' in line)
assert '{ "WORLD SCALE", "vr.world_size", _vr_setting_real, 12, {' in row
pairs = re.findall(r'\{ "(\d+)%", "([\d.]+)" \}', row)
assert len(pairs) == 12 and ('100', '1.0') in pairs, pairs
for percent, value in pairs:
    assert abs(int(percent) / 100.0 - float(value)) < 1e-9, (percent, value)
values = [float(value) for percent, value in pairs]
assert values == sorted(values) and values[0] >= 0.5 and values[-1] <= 2.0
rows = re.findall(r'^\t(?:\{ "[A-Z]|VR_[A-Z_]+,)', comfort, re.M)
assert len(rows) == 7, rows  # (one COMFORT screen: VR_MENU_SETTINGS_PER_SCREEN rows at most)
assert '#define VR_MENU_SETTINGS_PER_SCREEN 8' in menu and '#define VR_MENU_MAXIMUM_VALUES 12' in menu

# ---------- at once: vr_reload_settings (every VR menu change runs it, vr_menu_apply)
reload = function(frame, 'vr_reload_settings')
BLOCK = reload[reload.index('\t{\n\t\tdouble base = config_real("vr.world_scale"), size = config_real("vr.world_size");'):]
BLOCK = BLOCK[:BLOCK.index('\t\tvr.units_per_metre = units;\n\t}\n') + len('\t\tvr.units_per_metre = units;\n\t}\n')]
assert reload.index(BLOCK) < reload.index('static const char *const sides[]')
apply = function(menu, 'vr_menu_apply')
assert apply.count('vr_reload_settings();') >= 1
init = function(frame, 'vr_initialize')
assert init.index('vr.units_per_metre = (float)config_real("vr.world_scale");') < init.index('\tvr_reload_settings();')
PROGRAM = r'''
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int checks;
#define CHECK(c, what) do { checks++; if (!(c)) { printf("FAIL: %s\n", what); exit(1); } } while (0)
static struct { float units_per_metre; } vr;
static double base_value = 0.328084, size_value = 1.0;
static double config_real(const char *key)
{
    if (!strcmp(key, "vr.world_scale")) return base_value;
    CHECK(!strcmp(key, "vr.world_size"), "only its keys");
    return size_value;
}
static void platform_log(const char *format, ...) { (void)format; }
static void reload(void)
{
#include "block.inc"
}
static int near(float a, double b) { return fabs(a - b) < 1e-6 * fabs(b); }
int main(void)
{
    reload(); CHECK(near(vr.units_per_metre, 0.328084), "100%: the game's unit, 10 feet");
    size_value = 1.2; reload(); CHECK(near(vr.units_per_metre, 0.328084 / 1.2), "120%: the world a fifth bigger");
    size_value = 0.8; reload(); CHECK(near(vr.units_per_metre, 0.328084 / 0.8), "80%: smaller");
    size_value = 0.1; reload(); CHECK(near(vr.units_per_metre, 0.328084 / 0.5), "at least 50%");
    size_value = 9.0; reload(); CHECK(near(vr.units_per_metre, 0.328084 / 2.0), "at most 200%");
    size_value = NAN; reload(); CHECK(near(vr.units_per_metre, 0.328084), "an unreadable size: 100%");
    size_value = -1.0; reload(); CHECK(near(vr.units_per_metre, 0.328084), "a negative size: 100%");
    size_value = 1.0; base_value = 0.0; reload(); CHECK(near(vr.units_per_metre, 1.0 / 3.048), "no base: 10 feet");
    base_value = 0.5; size_value = 1.25; reload(); CHECK(near(vr.units_per_metre, 0.4), "a base of one's own, scaled");
    printf("ok %d\n", checks);
    return 0;
}
'''


def run(block):
    compiler = shutil.which('clang') or shutil.which('cc')
    assert compiler, 'a C compiler'
    with tempfile.TemporaryDirectory(prefix='test73b-world-scale-') as work:
        Path(work, 'block.inc').write_text(block)
        Path(work, 'scale.c').write_text(PROGRAM)
        built = subprocess.run([compiler, '-std=gnu11', '-Wall', '-Werror', '-I', work, str(Path(work, 'scale.c')),
                                '-lm', '-o', str(Path(work, 'scale'))], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        result = subprocess.run([str(Path(work, 'scale'))], capture_output=True, text=True)
        return result.returncode, result.stdout


status, output = run(BLOCK)
assert status == 0 and output.startswith('ok'), output
for code, what in [(mutated(BLOCK, 'units = (float)(base / size);', 'units = (float)(base * size);'),
                    'the other way round (120% a smaller world)'),
                   (mutated(BLOCK, 'size = size < 0.5 ? 0.5 : size > 2.0 ? 2.0 : size;\n', ''), 'unbounded')]:
    status, output = run(code)
    assert status == 1 and output.startswith('FAIL'), (what, output)

# ---------- what takes it: the eyes (their separation), the head, the hands, through one scale
view = function(frame, 'view')
assert 'out_position[0] = position[0] + halo[0] * vr.units_per_metre;' in view
eye = function(frame, 'vr_eye_view')
assert 'offset[axis] += pose->position[axis] - vr.frame.head.position[axis];' in eye and \
    'view(offset, pose->orientation, position, forward, out_position, out_forward, out_up);' in eye
assert 'float vr_units_per_metre(void)\n{\n\treturn vr.units_per_metre;\n}' in frame
# (no VR code reads the base apart but the co-op host's grip for a remote player's palm, whose own scale it cannot
# know: the true unit, as before)
for path in sorted((ROOT / 'port/linux').rglob('*.c')):
    text = path.read_text(encoding='utf-8', errors='replace')
    if 'config_real("vr.world_scale")' in text:
        assert path.name in ('vr_frame.c', 'vr_world_remote.c'), path
assert 'real u=config_real("vr.world_scale");' in remote
print('PASS: WORLD SCALE (COMFORT, 70% to 150%) divides the game units a metre makes, at once: the eyes\' separation, '
      'the head\'s and hands\' movement; bounded 50% to 200%, an unreadable value 100% (2 negative controls)')
