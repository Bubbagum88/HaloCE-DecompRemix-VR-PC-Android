"""Test59: OpenCE network 28 (Build 201), with 27 and 28 joinable.

The owner asked for the latest OpenCE network, with every network selectable
(27 too) and All compatible networks still the launcher's default. This app
now hosts and advertises network 28 and joins 11..28:

- 27 (OpenCE Build 189) adds map sharing's messages 83-86. A network 27 or
  newer OpenCE client joining a game on a Custom Edition map it lacks asks the
  host for it; this app shares no maps, so its host answers as an OpenCE host
  with network.map_share off does (the client then says "The host does not
  share its maps." instead of waiting). Its client never asks and drops the
  messages. This replays the real responder (extracted from
  network_distributed.c) with valid and forged requests.
- 28 (Build 201) changes rules every machine must agree on: a multiplayer
  map's first scripted BSP is kept (hs.c), dynamic lights and the flashlight
  stay on past the Xbox player and vehicle limits (game_engine.c), and a
  second weapon picked up while firing is readied (units.c,
  network_objects.c); its host also holds a downloading machine's players,
  which this app's never are.

Also taken from Builds 189-201 without a wire change: the overshield drain is
not a shield hit on clients (hud_unit.c), bodies the host moves are not left
floating on clients (network_objects.c, never a body this app's VR hands or
DEATH RAGDOLLS pose), and the renderer's transparent groups (2048) and debug
vertices (static).
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")

limits = read("port/linux/include/halo_port_limits.h")
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION 28$", limits, re.M)
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION_MINIMUM 11$", limits, re.M)
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION_MAXIMUM 28$", limits, re.M)

# the launcher: every network 11..28 selectable, 27 included; All compatible the default
profile = read("port/android/app/src/main/java/com/halo/decomp/NetworkProfile.java")
assert "static final int DEFAULT = 0;" in profile and "static final int CURRENT = 28;" in profile
supported = re.search(r"SUPPORTED = \{([^}]*)\}", profile).group(1)
assert [int(v) for v in supported.split(",")] == list(range(28, 10, -1)), supported
assert 'return version == 0 ? "All compatible networks"' in profile
config = read("port/linux/src/port_config.c")
assert '{ "network.protocol_version", _config_integer, "0",' in config
browser = read("port/android/app/src/main/java/com/halo/decomp/ServerBrowser.java")
assert '"All compatible networks (11–28) · "' in browser and "for (int version : NetworkProfile.SUPPORTED)" in browser
for name in ("ServerBrowser", "InGameNetworkGuide", "Updater", "NetworkProfile"):
    text = read("port/android/app/src/main/java/com/halo/decomp/%s.java" % name)
    assert "network 26" not in text and "11–26" not in text and "15–26" not in text, name

# 27: map sharing's messages, numbered as OpenCE's, and the host's answer in both paths
header = read("port/linux/game/network_distributed.h")
for name, number in (("request", 83), ("offer", 84), ("sources", 85), ("progress", 86)):
    assert "_distributed_message_map_share_%s = %d," % (name, number) in header
distributed = read("port/linux/game/network_distributed.c")
handle = distributed[distributed.index("void network_distributed_handle_message(\n"):]
assert handle.index("map_share_handles_message(message, size)") < handle.index("if (size < sizeof(header) || !game_in_progress())")
assert "map_share_handle_message(machine_index, message, size, distributed_handling_stream_message);" in handle
server = read("source/networking/network_server_message_handler.c")
stream = server[server.index("network_voice_handle_message(machine_index, message, message_buffer_size);"):]
stream = stream[:stream.index("network_distributed_handle_stream_message(machine_index, message, message_buffer_size);")]
assert "if (map_share_handles_message(message, message_buffer_size))" in stream
assert "map_share_handle_message(machine_index, message, message_buffer_size, TRUE);" in stream
assert "network_game_server_client_machine_is_joined_to_game(server, machine)" in stream


def function(text, name):
    start = re.search(r"^[\w ]+\b" + name + r"\(\n", text, re.M)
    assert start, name
    end = text.index("\n}\n", start.start()) + 3
    return text[start.start():end]


share = distributed[distributed.index("#define MAP_SHARE_LEVEL_NAME_BYTES 64"):distributed.index("boolean map_share_handles_message(")]
share = share.replace("unsigned long version;", "unsigned int version;")
harness = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char byte;
typedef unsigned short word;
typedef int boolean;
typedef unsigned short message_header;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define FLAG(b) (1u << (b))
#define HALO_PORT_MAXIMUM_NETWORK_MACHINES 128
#define csmemcpy memcpy
#define csmemset memset
enum { _distributed_message_map_share_request = 83, _distributed_message_map_share_offer,
	_distributed_message_map_share_sources, _distributed_message_map_share_progress };
enum { _error_silent };
struct distributed_message_header { message_header header; byte type; byte count; int game_time; };
static int server, in_game, sends, sent_machine, logs;
static byte sent[512];
static word sent_size;
static void *global_network_game_server_get(void) { return server ? &server : NULL; }
static boolean game_in_progress(void) { return in_game; }
static int game_time_get(void) { return 1234; }
static void build_message_header(message_header *h, word size, int a, int b) { *h = (message_header)(size | 0x8000); (void)a; (void)b; }
static boolean network_distributed_server_send_to_machine_reliably(long machine, void *message, word size)
{ sends++; sent_machine = (int)machine; sent_size = size; memcpy(sent, message, size); return TRUE; }
static void error(int kind, char const *format, ...) { (void)kind; (void)format; logs++; }
''' + share + function(distributed, "map_share_handles_message") + function(distributed, "map_share_handle_message") + r'''
static word request(byte *buffer, byte type, char const *name, int terminate, int extra)
{
	struct distributed_message_header h = { 0, type, 1, 0 };
	struct distributed_map_share_request r;
	memset(&r, 'x', sizeof(r));
	if (terminate) { memset(r.level_name, 0, sizeof(r.level_name)); strcpy(r.level_name, name); }
	r.version = 0x1234; r.wanted = 1;
	memcpy(buffer, &h, sizeof(h)); memcpy(buffer + sizeof(h), &r, sizeof(r));
	return (word)(sizeof(h) + sizeof(r) + extra);
}
int main(void)
{
	byte buffer[256];
	word size;
	struct distributed_message_header h;
	struct distributed_map_share_offer offer;
	int type;

	assert(sizeof(struct distributed_message_header) == 8);
	/* a joined machine's request over its connection: answered "not shared" */
	server = 1; in_game = 0;
	size = request(buffer, 83, "custom_maps\\hugeass_1a2b3c4d", 1, 0);
	assert(map_share_handles_message((word const *)buffer, size));
	map_share_handle_message(5, (word const *)buffer, size, TRUE);
	assert(sends == 1 && sent_machine == 5 && sent_size == 8 + 68);
	memcpy(&h, sent, 8); memcpy(&offer, sent + 8, sizeof(offer));
	assert(h.type == 84 && h.count == 1 && h.game_time == 0 && h.header == (message_header)(76 | 0x8000));
	assert(!strcmp(offer.level_name, "custom_maps\\hugeass_1a2b3c4d") && offer.result == 1 && offer.file_count == 0 && offer.flags == 0);
	/* during a game: the in-progress flag and the game time */
	in_game = 1;
	map_share_handle_message(7, (word const *)buffer, size, TRUE);
	assert(sends == 2 && sent_machine == 7);
	memcpy(&h, sent, 8); memcpy(&offer, sent + 8, sizeof(offer));
	assert(h.game_time == 1234 && offer.flags == 1 && offer.result == 1);
	/* dropped: a datagram (anyone can send one as from anyone), a client (no
	server), no machine, a bad size, a name without its end, the other three
	kinds */
	map_share_handle_message(5, (word const *)buffer, size, FALSE);
	server = 0; map_share_handle_message(5, (word const *)buffer, size, TRUE); server = 1;
	map_share_handle_message(NONE, (word const *)buffer, size, TRUE);
	map_share_handle_message(128, (word const *)buffer, size, TRUE);
	map_share_handle_message(5, (word const *)buffer, (word)(size + 4), TRUE);
	map_share_handle_message(5, (word const *)buffer, (word)(size - 1), TRUE);
	size = request(buffer, 83, "", 0, 0);
	map_share_handle_message(5, (word const *)buffer, size, TRUE);
	size = request(buffer, 83, "", 1, 0);
	map_share_handle_message(5, (word const *)buffer, size, TRUE);
	for (type = 84; type <= 86; type++) {
		size = request(buffer, (byte)type, "custom_maps\\a", 1, 0);
		assert(map_share_handles_message((word const *)buffer, size));
		map_share_handle_message(5, (word const *)buffer, size, TRUE);
		map_share_handle_message(NONE, (word const *)buffer, size, TRUE);
	}
	assert(sends == 2);
	/* not map sharing's: voice 82, 87, a short message */
	size = request(buffer, 82, "x", 1, 0); assert(!map_share_handles_message((word const *)buffer, size));
	size = request(buffer, 87, "x", 1, 0); assert(!map_share_handles_message((word const *)buffer, size));
	assert(!map_share_handles_message((word const *)buffer, 7));
	puts("PASS: map sharing's request answered once per valid request (machine, 76 bytes, offer 84, not shared, level name, in-progress flag, game time); datagrams, clients, bad machines, sizes and names and the other kinds dropped");
	return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "t.c").write_text(harness, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wno-unused-function", "-fsanitize=address,undefined",
                    str(path / "t.c"), "-o", str(path / "t")], check=True)
    subprocess.run([str(path / "t")], check=True)

# 28: a multiplayer map's first scripted BSP kept, later switches ignored
hs = read("source/hs/hs.c")
bsp = hs[hs.index("static short scripted_multiplayer_bsp = NONE;"):]
assert "scripted_multiplayer_bsp = NONE;" in hs[hs.index("void hs_initialize_for_new_map("):][:2000]
assert "switch_bsp from a script is ignored after the multiplayer game has chosen its bsp" in hs
# 28: dynamic lights and the flashlight past the Xbox limits
engine = read("source/game/game_engine.c")
lighting = engine[engine.index("static void game_engine_build_lighting(\n\tvoid)\n{"):]
lighting = lighting[:lighting.index("\n}\n")]
assert "_game_engine_disable_dynamic_light_bit" not in lighting and "_game_engine_disable_integrated_lights_bit" not in lighting
assert "The beam is a dynamic light" in lighting and "_game_engine_5_or_more_players_bit" in lighting
# 28: a second weapon picked up while firing readied, on the host and a client
units = read("source/units/units.c")
starting = units[units.index("case _unit_add_weapon_starting:"):units.index("case _unit_add_weapon_replace:")]
assert "if (holding_another ||" in starting and "slot != inventory_index &&" in starting
objects = read("port/linux/game/network_objects.c")
ready = objects[objects.index("static void distributed_client_ready_picked_up_weapons("):]
ready = ready[:ready.index("\n}\n")]
assert "weapon_slot != current_slot &&" in ready and "if (!TEST_FLAG(unit->unit.control_flags, _unit_control_weapon_primary_trigger_bit))" not in ready
# Build 201 without a wire change: the overshield's drain on a client
hud = read("source/interface/hud_unit.c")
assert "if (hud_state->last_shield_vitality > 1.0f && shield_drop <= 0.02f)" in hud
# e791cf9a: bodies the host moves, never one this app's VR code poses
body = objects[objects.index("static struct biped_datum *distributed_body_get("):]
body = body[:body.index("\n}\n")]
assert "!vr_npc_interaction_owned(object_index)" in body and "_object_dead_bit" in body
move = objects[objects.index("static void distributed_object_move("):]
move = move[:move.index("\n}\n")]
assert move.index("distributed_body_unfix_pose(object_index);") < move.index("object_set_position(object_index, position, forward, up);")
assert "distributed_body_set_at_rest(state->object_index, at_rest);" in objects
# the renderer's (no wire change)
assert "#define HALO_PORT_MAXIMUM_TRANSPARENT_GEOMETRY_GROUPS 2048" in read("port/linux/include/halo_port_capacity.h")
assert "RASTERIZER_MAXIMUM_TRANSPARENT_GEOMETRY_GROUPS = HALO_PORT_MAXIMUM_TRANSPARENT_GEOMETRY_GROUPS," in read("source/rasterizer/rasterizer.h")
assert "static struct rasterizer_debug_model_vertex debug_vertices[" in read("source/rasterizer/rasterizer.c")
print("PASS: Test59 network 28 (hosts 28, joins 11..28 incl. 27, All compatible default), map sharing answered as not shared, "
      "28's BSP / lights / second-weapon rules, overshield drain, client bodies (VR-posed ones left alone), renderer limits")
