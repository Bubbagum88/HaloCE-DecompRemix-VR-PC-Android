"""Test73b: map sharing's upload limits at their most by default (the owner: "also raise the download limit to max
(i think 10mb) by default so custom map downloads via the server are faster").

A machine sends maps no faster than its limit (map_share.c's upload_limit): the host network.map_share_upload, at most
20480 KB/s (20 MB/s), a player helping it network.map_seed_upload, at most 10240 KB/s (10 MB/s); OpenCE's defaults
were 1024 and 256, and a download comes from them all at once. Both defaults are now their most. Every config is
written whole at the first start, so one saved before holds the old defaults: network.map_share_revision raises a
limit saved at its old default once and keeps a value chosen otherwise (and every choice after).

The production config loader (port_config.c with tomlc17; tools/test_test32_geometry.py's file fixtures) runs on every
edition, with 2 negative controls.
"""
from pathlib import Path
import ast
import os
import re
import subprocess
import tempfile

from harness import mutated

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73b-map-share'
OUT.mkdir(parents=True, exist_ok=True)
config = (ROOT / 'port/linux/src/port_config.c').read_text()
share = (ROOT / 'port/linux/game/map_share.c').read_text()
menus = (ROOT / 'port/linux/game/menu_functions.c').read_text()
settings = (ROOT / 'tools/port_settings.py').read_text()

# the defaults are the limits' most, and the menus offer them
assert '{ "network.map_share_upload", _config_integer, "20480",' in config
assert '{ "network.map_seed_upload", _config_integer, "10240",' in config
assert '{ "network.map_share_revision", _config_integer, "1",' in config
assert 'MAXIMUM_HOST_UPLOAD_KILOBYTES = 20480,' in share and 'MAXIMUM_SEED_UPLOAD_KILOBYTES = 10240,' in share
assert '{ "256", "512", "1024", "2048", "4096", "8192", "16384", "20480" } },' in menus  # Server Setup's
assert 'SEED_UPLOADS = (64, 128, 256, 512, 1024, 2048, 4096, 8192, 10240)' in settings  # Network Setup's

# the production loader, as test32's runs it (its file fixtures taken from it)
geometry = ast.parse((ROOT / 'tools/test_test32_geometry.py').read_text())
boundaries = next(ast.literal_eval(node.value) for node in geometry.body if isinstance(node, ast.Assign)
                  and getattr(node.targets[0], 'id', None) == 'boundaries')
PRODUCTION = config.replace('#include "platform.h"', 'static void platform_log(const char *s,...) {(void)s;}').replace(
    '#include "halo_port_limits.h"', '#define HALO_PORT_NETWORK_VERSION 24\n#define HALO_PORT_NETWORK_VERSION_MINIMUM 11\n'
    '#define HALO_PORT_NETWORK_VERSION_MAXIMUM 24').replace('#include <SDL3/SDL.h>', '')
MAIN = r'''
int main(void)
{
    printf("%ld %ld\n", config_integer("network.map_share_upload"), config_integer("network.map_seed_upload"));
    return 0;
}
'''
EDITIONS = (('flat', '#define HALO_ANDROID 1\n'), ('vr', '#define HALO_ANDROID 1\n#define HALO_VR 1\n'), ('desktop', ''))


def build(edition, defines, production):
    source, exe = OUT / (edition + '.c'), OUT / edition
    source.write_text(defines + boundaries + production + MAIN)
    subprocess.run(['clang', '-std=gnu11', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                    '-I' + str(ROOT / 'port/linux/src'), '-I' + str(ROOT / 'port/third_party/tomlc17'), str(source),
                    str(ROOT / 'port/third_party/tomlc17/tomlc17.c'), '-pthread', '-lm', '-o', str(exe)], check=True)
    return exe


def limits(exe, folder):
    env = dict(os.environ, HALO_DATA_ROOT=str(folder), TEST_CONFIG_BASE=str(folder) + '/')
    for key in ('HALO_NET_MAP_SHARE_UPLOAD', 'HALO_NET_MAP_SEED_UPLOAD', 'HALO_NET_MAP_SHARE_REVISION'):
        env.pop(key, None)
    result = subprocess.run([str(exe)], env=env, check=True, capture_output=True, text=True)
    return tuple(int(value) for value in result.stdout.split())


def saved(folder, key):
    match = re.search(r'^' + key + r'\s*=\s*(\d+)', (Path(folder) / 'config.toml').read_text(), re.M)
    return int(match.group(1)) if match else None


def check(exe):
    # a new config: the most, and its revision written
    with tempfile.TemporaryDirectory(dir=OUT) as folder:
        assert limits(exe, folder) == (20480, 10240)
        assert saved(folder, 'map_share_upload') == 20480 and saved(folder, 'map_seed_upload') == 10240
        assert saved(folder, 'map_share_revision') == 1
    # one saved before at the old defaults: raised once, the rest of the file kept
    with tempfile.TemporaryDirectory(dir=OUT) as folder:
        (Path(folder) / 'config.toml').write_text('# mine\n[network]\nmap_share_upload = 1024\nonline = false\n'
                                                  'map_seed_upload = 256\n')
        assert limits(exe, folder) == (20480, 10240), 'the old defaults raised'
        text = (Path(folder) / 'config.toml').read_text()
        assert '# mine\n' in text and re.search(r'^online = false$', text, re.M)
        assert saved(folder, 'map_share_upload') == 20480 and saved(folder, 'map_seed_upload') == 10240
        assert saved(folder, 'map_share_revision') == 1
        assert limits(exe, folder) == (20480, 10240)
        # a choice after: kept (the old default's value too)
        path = Path(folder) / 'config.toml'
        path.write_text(path.read_text().replace('map_share_upload = 20480', 'map_share_upload = 1024'))
        assert limits(exe, folder) == (1024, 10240), 'a choice after the revision kept'
    # values chosen before: kept; one at its default and one not: that one alone raised
    for share_upload, seed_upload, expected in ((512, 2048, (512, 2048)), (1024, 4096, (20480, 4096)),
                                                (16384, 256, (16384, 10240))):
        with tempfile.TemporaryDirectory(dir=OUT) as folder:
            (Path(folder) / 'config.toml').write_text(
                f'[network]\nmap_share_upload = {share_upload}\nmap_seed_upload = {seed_upload}\n')
            assert limits(exe, folder) == expected, (share_upload, seed_upload, 'a chosen value kept')
            assert saved(folder, 'map_share_revision') == 1
    # an old config without the settings at all: the new defaults added
    with tempfile.TemporaryDirectory(dir=OUT) as folder:
        (Path(folder) / 'config.toml').write_text('[network]\nonline = false\n')
        assert limits(exe, folder) == (20480, 10240)


for edition, defines in EDITIONS:
    check(build(edition, defines, PRODUCTION))
    print('ok ' + edition, flush=True)
for production, what in [
        (mutated(PRODUCTION, 'if (share_revision.type != TOML_INT64 || share_revision.u.int64 < 1)', 'if (0)'),
         'no migration: the old defaults stay'),
        (mutated(PRODUCTION, 'if (saved.type != TOML_INT64 || saved.u.int64 != limits[limit].before)',
                 'if (saved.type != TOML_INT64)'), 'every saved value raised')]:
    try:
        check(build('negative', '', production))
    except AssertionError:
        continue
    raise SystemExit('negative control passed: ' + what)
print('PASS: map sharing sends at its most by default (hosting 20 MB/s, helping 10 MB/s; the menus offer both); a '
      'config saved at the old defaults (1024, 256) raised once, chosen values and later choices kept, on the flat, '
      'VR and desktop editions (2 negative controls)')
