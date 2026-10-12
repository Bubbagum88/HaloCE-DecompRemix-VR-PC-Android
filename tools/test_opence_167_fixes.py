"""Compile focused tests from production helpers for OpenCE 166/167 fixes."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def extract_function(path, signature):
    source = (ROOT / path).read_text(encoding="utf-8")
    starts = [match.start() for match in re.finditer(re.escape(signature), source)]
    start = None
    opening = None
    for candidate in starts:
        brace = source.find("{", candidate)
        semicolon = source.find(";", candidate)
        if brace >= 0 and (semicolon < 0 or brace < semicolon):
            start, opening = candidate, brace
            break
    if start is None:
        raise AssertionError("production function definition not found: " + signature)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError("unterminated production helper: " + signature)


def main():
    compiler = next((shutil.which(name) for name in ("clang", "cc", "gcc") if shutil.which(name)), None)
    if not compiler:
        raise SystemExit("no C compiler")

    chunk = extract_function("port/linux/src/posix_update.c", "static int update_chunk_size_parse(")
    map_name = extract_function("source/networking/network_client_manager.c",
                                "static boolean network_game_client_map_name_is_valid(")
    saved_name = extract_function("source/saved games/saved_game_files.c",
                                  "static void saved_game_file_copy_multiplayer_map_name(")
    clear_grenades = extract_function("port/linux/game/network_objects.c",
                                      "static void distributed_client_clear_unit_grenades(")
    teleporter = extract_function("port/linux/game/network_distributed.c",
                                  "static void distributed_note_host_teleporter_correction(")
    explosion = extract_function("port/linux/game/network_damage.c",
                                 "static boolean distributed_explosion_this_tick(")
    pvs = extract_function("source/objects/objects.c", "void objects_port_set_activating_cluster(")

    body = extract_function("port/linux/src/posix_update.c", "static int read_body(")
    assert "remaining > MAXIMUM_DOWNLOAD_SIZE - download->received" in body
    assert "distributed_client_clear_unit_grenades(object_index);" in (
        ROOT / "port/linux/game/network_objects.c").read_text(encoding="utf-8")
    create = extract_function("port/linux/game/network_objects.c", "static void distributed_client_create(")
    assert create.index("objects_client_has[absolute_index] = object_index") < create.index(
        "distributed_client_clear_unit_grenades(object_index)") < create.index(
        "distributed_client_apply_change(object_index, change)")
    assert "distributed_source_deals(grenade->projectile.index" in explosion
    assert "player->teleporter_index = find_netgame_flag" in teleporter
    assert "cluster_index < 0" in pvs

    c = r'''#include <assert.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <stdint.h>
#include <stdlib.h>
#define TRUE 1
#define FALSE 0
#define NONE -1
#define NUMBEROF(x) (sizeof(x) / sizeof((x)[0]))
#define MAXIMUM_FILENAME_LENGTH 32
#define _strnicmp strncasecmp
typedef int boolean;
typedef unsigned char byte;
typedef struct { float x,y,z; } real_point3d;
struct damage_reach { float distance,ticks,carried_ticks; };
typedef struct damage_reach damage_reach;
''' + chunk + r'''
''' + map_name + r'''
static int test_map_name(const char *s) { return network_game_client_map_name_is_valid(s,(long)strlen(s)+1); }
static void csmemset(void *d, int c, size_t n) { memset(d,c,n); }
static void csstrncpy(char *d, const char *s, size_t n) { strncpy(d,s,n); }
''' + saved_name + r'''
struct object_datum { struct { long type; } object; };
struct unit_datum { struct { unsigned char grenade_counts[2]; } unit; };
static struct object_datum object_fixture;
static struct unit_datum unit_fixture;
static struct object_datum *object_get(long index) { (void)index; return &object_fixture; }
static struct unit_datum *unit_get(long index) { (void)index; return &unit_fixture; }
#define _object_mask_unit 1
#define TEST_FLAG(mask,value) (((mask) & (value)) != 0)
''' + clear_grenades + r'''
struct player_datum { long teleporter_index; };
struct object_position { real_point3d position; };
struct object_position_datum { struct object_position object; };
static struct object_position_datum object_position_fixture;
static struct object_position_datum *object_get_position(long index) { (void)index; return &object_position_fixture; }
#define object_get(i) object_get_position(i)
static long flag_result = 17;
static long find_netgame_flag(real_point3d const *p, float r, float z, int source, long none)
{ (void)p; (void)r; (void)z; (void)source; (void)none; return flag_result; }
#define _netgame_flag_teleporter_source 1
static float distance_squared3d(real_point3d const *a, real_point3d const *b)
{ float x=a->x-b->x,y=a->y-b->y,z=a->z-b->z; return x*x+y*y+z*z; }
''' + teleporter + r'''
struct game_globals_grenade { struct { long index; } projectile; };
struct tag_block { struct game_globals_grenade items[4]; };
struct globals { struct tag_block grenades; };
static struct globals globals_fixture;
static struct globals *scenario_get_game_globals(void) { return &globals_fixture; }
#define TAG_BLOCK_GET_ELEMENT(block,index,type) (&(block)->items[(index)])
struct damage_effect { long definition_index; real_point3d epicenter; };
struct damage_tick { long time; short count; struct damage_effect explosions[4]; };
static struct damage_tick damage_explosions[2];
static long game_tick;
static long game_time_get(void) { return game_tick; }
static float distributed_source_deals(long source, long damage, boolean grenade, byte *kinds, damage_reach *reach)
{ (void)kinds; (void)reach; return source == 7 && grenade && damage == 21 ? 1.0f : 0.0f; }
''' + explosion + r'''
enum { _pvs_activation_normal=0, _pvs_activation_cluster=1 };
struct cluster_block { short count; };
struct structure_bsp { struct cluster_block clusters; };
struct pvs_globals { short pvs_activation_type; struct { short cluster_index; } pvs_activation; };
static struct structure_bsp bsp_fixture;
static struct pvs_globals globals_pvs;
static struct pvs_globals *object_globals=&globals_pvs;
static struct structure_bsp *global_structure_bsp_get(void) { return &bsp_fixture; }
''' + pvs + r'''
int main(void)
{
 unsigned long long n=999;
 char name[33];
 struct player_datum player={3};
 real_point3d before={0,0,0};
 assert(update_chunk_size_parse("0",&n) && n==0);
 assert(update_chunk_size_parse("a",&n) && n==10);
 assert(update_chunk_size_parse("A;foo=bar",&n) && n==10);
 assert(update_chunk_size_parse("5 \t",&n) && n==5);
 assert(!update_chunk_size_parse("",&n));
 assert(!update_chunk_size_parse("-1",&n));
 assert(!update_chunk_size_parse("+1",&n));
 assert(!update_chunk_size_parse(" 1",&n));
 assert(!update_chunk_size_parse("0x10",&n));
 assert(!update_chunk_size_parse("10000000000000000",&n));
 assert(!update_chunk_size_parse("1;bad\001",&n));
 assert(test_map_name("[H2]_Lockout"));
 assert(test_map_name("maps\\Lockout (CE)+"));
 assert(!test_map_name("../Lockout"));
 assert(!test_map_name("maps\\CON.map"));
 assert(!test_map_name("maps\\com1.map"));
 assert(!test_map_name("maps\\LPT9.map"));
 assert(!test_map_name("maps\\bad/name"));
 memset(name,0x7f,sizeof(name));
 saved_game_file_copy_multiplayer_map_name(name,"short");
 assert(!strcmp(name,"short") && name[32]==0);
 object_fixture.object.type=1; unit_fixture.unit.grenade_counts[0]=3; unit_fixture.unit.grenade_counts[1]=2;
 distributed_client_clear_unit_grenades(4);
 assert(unit_fixture.unit.grenade_counts[0]==0 && unit_fixture.unit.grenade_counts[1]==0);
 object_fixture.object.type=2; unit_fixture.unit.grenade_counts[0]=4;
 distributed_client_clear_unit_grenades(4);
 assert(unit_fixture.unit.grenade_counts[0]==4);
 object_position_fixture.object.position.x=2.0f; player.teleporter_index=3; flag_result=17;
 distributed_note_host_teleporter_correction(&player,1,&before);
 assert(player.teleporter_index==17);
 player.teleporter_index=3; object_position_fixture.object.position.x=0.5f;
 distributed_note_host_teleporter_correction(&player,1,&before);
 assert(player.teleporter_index==3);
 globals_fixture.grenades.items[0].projectile.index=7;
 damage_explosions[0].time=9; damage_explosions[0].count=2; game_tick=9;
 damage_explosions[0].explosions[0].definition_index=22;
 damage_explosions[0].explosions[1].definition_index=21;
 assert(distributed_explosion_this_tick(0,0,NULL));
 assert(distributed_explosion_this_tick(0,0,&(real_point3d){0,0,0}));
 assert(!distributed_explosion_this_tick(0,1,NULL));
 assert(!distributed_explosion_this_tick(0,0,&(real_point3d){1,0,0}));
 damage_explosions[0].time=8;
 assert(!distributed_explosion_this_tick(0,0,NULL));
 bsp_fixture.clusters.count=8;
 objects_port_set_activating_cluster(-5);
 assert(globals_pvs.pvs_activation_type==_pvs_activation_normal);
 objects_port_set_activating_cluster(8);
 assert(globals_pvs.pvs_activation_type==_pvs_activation_normal);
 objects_port_set_activating_cluster(4);
 assert(globals_pvs.pvs_activation_type==_pvs_activation_cluster && globals_pvs.pvs_activation.cluster_index==4);
 puts("OpenCE focused fixtures passed");
 return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="opence-167-") as directory:
        source = Path(directory) / "opence_167_test.c"
        binary = Path(directory) / "opence_167_test"
        source.write_text(c, encoding="utf-8")
        subprocess.run([compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-O1",
                        str(source), "-o", str(binary)], check=True)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
        print(result.stdout.strip())


if __name__ == "__main__":
    main()
