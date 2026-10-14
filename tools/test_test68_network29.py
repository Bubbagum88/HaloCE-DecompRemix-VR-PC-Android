"""Test68: OpenCE Build 206's network 29, as this port takes it.

1. This build hosts and advertises network 29 and joins 11..29 (All compatible
   by default); the launcher lists 29; the community extras keep their own
   kinds 87-92, which Build 206 still drops as unknown.
2. Network 29's Custom Edition map identity: a host's level name is the map's
   own and its game record's map version the map's hash's first 32 bits
   (map_share_level_name_choose, cache_files_map_version). A host before 29
   (28 named a map for its hash and sent its header checksum) is still
   joinable: this port's client of one finds the map by its name
   (custom_edition_map_named) and checks the header checksum, never the hash
   version lookup. Run here: the real custom_edition_map_path and
   custom_edition_map_version_is_checksum, with the client's joined host
   version, the game's map version and the lookups as stand-ins.
3. The checksum refusal for such a host, and the hash version lookup for 29,
   in custom_edition_cache_present.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8', errors='replace')


def function(text, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.end() - 1)
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


# 1. the versions
limits = read('port/linux/include/halo_port_limits.h')
for name, value in (('HALO_PORT_NETWORK_VERSION', 29), ('HALO_PORT_NETWORK_VERSION_MINIMUM', 11),
                    ('HALO_PORT_NETWORK_VERSION_MAXIMUM', 29), ('HALO_PORT_CUSTOM_EDITION_NETWORK_VERSION_MINIMUM', 23),
                    ('HALO_PORT_MAP_HASH_VERSION_NETWORK_VERSION', 29)):
    assert re.search(r'^#define %s %d$' % (name, value), limits, re.M), name
assert 'version 29\n' in read('port/linux/network_format.txt')
profile = read('port/android/app/src/main/java/com/halo/decomp/NetworkProfile.java')
assert 'static final int CURRENT = 29;' in profile and 'SUPPORTED = {29, 28, 27,' in profile
header = read('port/linux/game/network_distributed.h')
kinds = dict((name, int(value)) for name, value in re.findall(r'_distributed_message_(\w+) = (\d+),', header))
assert kinds['map_share_progress'] == 86 and max(kinds.values()) == 92
print('PASS: hosts network 29 (OpenCE Build206), joins 11..29, launcher lists 29; extras still on kinds 87-92')

# 2. the map identity
server = read('source/networking/network_server_manager.c')
assert server.count('map_share_level_name_choose(server->game.map.name') == 3 and 'map_share_level_name_hash(' not in server
cache_files = read('source/cache/cache_files.c')
version_function = function(cache_files, 'cache_files_map_version')
assert 'custom_edition_map_version(map_name)' in version_function and 'mcc_cache_checksum(map_name)' in version_function
cache = read('port/linux/game/custom_edition_cache.c')
helper = function(cache, 'custom_edition_map_version_is_checksum')
path_function = function(cache, 'custom_edition_map_path')
lookup = cache[cache.index('static struct\n{\n\tchar name[MAP_PATH_SIZE];\n\tunsigned long version;'):]
lookup = lookup[:lookup.index('} custom_edition_version_lookup;') + len('} custom_edition_version_lookup;')] + '\n'
program = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
typedef int boolean;
#define TRUE 1
#define FALSE 0
#define MAP_PATH_SIZE 256
#define HALO_PORT_MAP_HASH_VERSION_NETWORK_VERSION 29
#define csstrcasecmp strcasecmp
static unsigned int joined;      /* the host version this machine joined; 0 when not a client */
static unsigned long game_version; /* the network game's map version; 0 when none */
static int by_version, by_name;
static unsigned long now = 1000;
unsigned int network_game_client_joined_version(void) { return joined; }
static unsigned long GetTickCount(void) { return now; }
static char const *tag_name_strip_path(char const *name) { char const *s = strrchr(name, '\\'); return s ? s + 1 : name; }
static boolean map_share_game_map_version(char const *level_name, unsigned long *version)
{ (void)level_name; if (!game_version) return FALSE; *version = game_version; return TRUE; }
static boolean custom_edition_map_find_version(char const *level_name, unsigned long version, char *path)
{ by_version++; sprintf(path, "custom_maps/%s_%08lx.map", tag_name_strip_path(level_name), version); return TRUE; }
static boolean custom_edition_map_named(char const *map_name, char *path)
{ by_name++; sprintf(path, "custom_maps/%s.map", tag_name_strip_path(map_name)); return TRUE; }
''' + lookup + helper + path_function + r'''
int main(void)
{
	char path[MAP_PATH_SIZE];
	/* not a client (hosting, or a local game): the game's version is the hash's */
	joined = 0; game_version = 0x0e2b3ee4;
	assert(!custom_edition_map_version_is_checksum());
	assert(custom_edition_map_path("custom_maps\\hugeass", path) && by_version == 1 && by_name == 0);
	assert(!strcmp(path, "custom_maps/hugeass_0e2b3ee4.map"));
	/* a client of a network 29 host: the hash version's file */
	joined = 29; now += 2000;
	assert(!custom_edition_map_version_is_checksum());
	assert(custom_edition_map_path("custom_maps\\hugeass", path) && by_version == 2 && by_name == 0);
	/* a client of a host before 29: the version is a header checksum; by name */
	for (joined = 11; joined < 29; joined++) {
		assert(custom_edition_map_version_is_checksum());
		now += 2000;
		assert(custom_edition_map_path("custom_maps\\hugeass_0e2b3ee4", path) && by_version == 2);
	}
	assert(by_name == 18 && !strcmp(path, "custom_maps/hugeass_0e2b3ee4.map"));
	/* no network game: by name */
	joined = 0; game_version = 0;
	assert(custom_edition_map_path("custom_maps\\plain", path) && by_name == 19 && by_version == 2);
	puts("PASS ran");
	return 0;
}
'''
out = ROOT / 'build/test68-network29'
out.mkdir(parents=True, exist_ok=True)
(out / 'identity.c').write_text(program, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Werror', '-Wno-unused-function', '-fsanitize=address,undefined',
                str(out / 'identity.c'), '-o', str(out / 'identity')], check=True)
result = subprocess.run([str(out / 'identity')], capture_output=True, text=True, check=True)
assert 'PASS ran' in result.stdout
print('PASS: network 29 map identity: a host names its map and versions it by hash; a client of a 29 host finds the '
      'hash version\'s file, of a host before 29 the map by its name (11..28), run with the real lookups')

# 3. custom_edition_cache_present
present = function(cache, 'custom_edition_cache_present')
assert 'boolean legacy = custom_edition_map_version_is_checksum();' in present
assert 'if (version && !legacy ? !custom_edition_map_find_version(level_name, version, path) :' in present
assert 'if (legacy && version && identity.checksum != version)' in present
assert 'if (version && !legacy && custom_edition_map_named(level_name, path))' in present
assert 'custom_maps.' not in present and present.count('the active game set maps folder') >= 3
print('PASS: a client of a host before 29 has its header checksum checked; of 29, the hash version\'s file; '
      'messages name the active game set maps folder')
