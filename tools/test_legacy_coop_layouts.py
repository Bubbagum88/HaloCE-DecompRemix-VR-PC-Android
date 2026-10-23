"""Replay pinned OpenCE campaign presentation layouts into the production receiver.

The fixture records actual upstream structs and commit IDs, not guessed protocol
numbers. This checks wire layout and receiver behavior, not headset gameplay.
"""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
fixtures = json.loads((ROOT / "tools/fixtures/legacy-coop-layouts.json").read_text())
coop = (ROOT / "port/linux/game/network_coop.c").read_text()
distributed = (ROOT / "port/linux/game/network_distributed.c").read_text()


def structure(source, name):
    return re.search(r"^struct " + name + r"\s*\n\{.*?^\};", source, re.M | re.S).group(0)


def canonical(text):
    return re.sub(r"\s+", " ", re.sub(r"/\*.*?\*/", "", text, flags=re.S)).strip()


def function(source, name):
    match = re.search(r"^(?:static )?[\w *]+\b" + name + r"\s*\([^;{]*\)\s*\{", source, re.M)
    start = source.index("{", match.start())
    end, depth = start + 1, 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


def guest_types(text):
    # Production guest ABI is 32-bit; don't let a host LP64 long change it.
    return re.sub(r"\blong\b", "int", text)


current = structure(coop, "distributed_coop_presentation")
current_input = canonical(structure(distributed, "distributed_player_input"))
out = ROOT / "build/legacy-coop-layouts"
out.mkdir(parents=True, exist_ok=True)
for version, fixture in fixtures["versions"].items():
    version = int(version)
    assert len(fixture["commit"]) == 40
    if version >= 15:
        for name, schema in fixture["schema"].items():
            # v17 puts cluster+1 in two formerly zero padding bytes. No shift.
            schema = schema.replace("byte pad[2]; real players_maximum", "short activating_cluster; real players_maximum")
            assert schema == canonical(structure(coop, name)), (version, name)
    old_input = canonical(fixture["input"])
    # v16 consumes one formerly zero padding byte, retaining every offset.
    old_input = old_input.replace("byte player_index; byte pad[3];", "byte player_index; byte structure_bsp_index; byte pad[2];")
    # v30 (OpenCE 242) consumes one more: the co-op player's friendly fire choice, 0 from older peers.
    old_input = old_input.replace("byte structure_bsp_index; byte pad[2];",
                                  "byte structure_bsp_index; byte coop_no_friendly_fire; byte pad;")
    assert old_input == current_input, version
    old = fixture["presentation"].replace("distributed_coop_presentation", "historical_presentation")
    code = r'''#include <assert.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char byte;
typedef unsigned short word;
typedef float real;
typedef int boolean;
typedef struct { real x,y,z; } real_point3d;
typedef struct { real i,j,k; } real_vector3d;
struct distributed_vector { short x,y,z; };
#define GAME_ALLEGIANCE_BITVECTOR_LONGS 4
#define PRESENTATION_BUFFER_COUNT 32
#define TRUE 1
#define FALSE 0
#define csmemcpy memcpy
#define csmemset memset
''' + guest_types(current) + "\n" + guest_types(old) + r'''
static struct {
 int heard_time, playing, played_time, heard_any, newest_time;
 struct distributed_coop_presentation buffered[32];
 int buffered_times[32];
} coop_presentation;
static int is_client = 1, host_version, legacy, allegiance_calls;
static unsigned network_game_client_joined_version(void){return host_version;}
static int config_boolean(char const *key){assert(!strcmp(key,"network.legacy_coop"));return legacy;}
static void game_allegiance_set_teams(unsigned const*a,unsigned const*b){(void)a;(void)b;allegiance_calls++;}
static int coop_client(void) { return is_client; }
static int game_time_get(void) { return 100; }
''' + guest_types(function(coop, "legacy_presentation_without_allegiance")) + '\n' + guest_types(function(coop, "client_presentation_apply_allegiance")) + '\n' + guest_types(function(coop, "network_coop_presentation_entry_size")) + "\n" + guest_types(function(coop, "network_coop_handle_presentation")) + r'''
int main(void) {
 struct historical_presentation packet = {0};
 struct distributed_coop_presentation *received = &coop_presentation.buffered[7];
 assert(offsetof(struct historical_presentation, camera_position) == offsetof(struct distributed_coop_presentation, camera_position));
 assert(offsetof(struct historical_presentation, players_maximum_body_vitality) == offsetof(struct distributed_coop_presentation, players_maximum_body_vitality));
'''
    if version < 15:
        code += r'''
 /* These hosts omit allegiance arrays: do not pass the shorter record to
    the modern receiver or silently manufacture host-owned allegiance. */
 assert(sizeof(packet) == offsetof(struct distributed_coop_presentation, ally_teams));
 assert(sizeof(packet) < network_coop_presentation_entry_size());

 host_version = VERSION_UNDER_TEST;
 network_coop_handle_presentation(&packet,7,sizeof(packet));assert(!coop_presentation.heard_any); /* OFFdefault */
 legacy=1;assert(sizeof(packet)==network_coop_presentation_entry_size());
 packet.camera_position.x=12.5f;packet.camera_field_of_view=88;packet.input_disabled=1;
 network_coop_handle_presentation(&packet,7,sizeof(packet));assert(coop_presentation.heard_any);
 assert(received->camera_position.x==12.5f&&received->camera_field_of_view==88&&received->input_disabled);
 client_presentation_apply_allegiance(received);assert(allegiance_calls==0);
 coop_presentation.heard_any=0;
 for(int size=0;size<(int)sizeof(struct distributed_coop_presentation)+4;size++) {
   if(size==(int)sizeof(packet))continue;
   network_coop_handle_presentation(&packet,8,size);assert(!coop_presentation.heard_any);
 }
 host_version=15;network_coop_handle_presentation(&packet,8,sizeof(packet));assert(!coop_presentation.heard_any);
 host_version=0;network_coop_handle_presentation(&packet,8,sizeof(packet));assert(!coop_presentation.heard_any);
'''
    else:
        code += r'''
 assert(sizeof(packet) == network_coop_presentation_entry_size());
 assert(offsetof(struct historical_presentation, ally_teams) == offsetof(struct distributed_coop_presentation, ally_teams));
 packet.camera_position.x = 12.5f;
 packet.camera_field_of_view = 88;
 packet.input_disabled = 1;
 packet.ally_teams[0] = 0xDEAD0123;
 packet.friendly_teams[3] = 0x1234ABCD;
 host_version=VERSION_UNDER_TEST;legacy=1;
 client_presentation_apply_allegiance((struct distributed_coop_presentation const*)&packet);assert(allegiance_calls==1);
 network_coop_handle_presentation(&packet, 7, sizeof(packet));
 assert(coop_presentation.heard_any && coop_presentation.newest_time == 7);
 assert(received->camera_position.x == 12.5f && received->camera_field_of_view == 88);
 assert(received->input_disabled == 1 && received->ally_teams[0] == 0xDEAD0123);
 assert(received->friendly_teams[3] == 0x1234ABCD);
 assert(received->activating_cluster == 0);
 coop_presentation.playing = 1; coop_presentation.played_time = 7;
 packet.camera_field_of_view = 45;
 network_coop_handle_presentation(&packet, 7, sizeof(packet));
 assert(received->camera_field_of_view == 88);
 coop_presentation.playing = 0; is_client = 0;
 network_coop_handle_presentation(&packet, 7, sizeof(packet));
 assert(received->camera_field_of_view == 88);
 is_client = 1;
 network_coop_handle_presentation(&packet, -1, sizeof(packet));
 assert(received->camera_field_of_view == 88);
'''
    code += '\nprintf("PASS: pinned network ' + str(version) + ' presentation and input layout\\n");\n}\n'
    cfile, binary = out / f"v{version}.c", out / f"v{version}"
    cfile.write_text(code.replace("VERSION_UNDER_TEST",str(version)))
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Wno-unused-variable", "-fsanitize=address,undefined", str(cfile), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("PASS: historical campaign wire/receiver audit; gameplay cross-play remains a device test")
