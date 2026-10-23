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

import network_expected as netv  # noqa: E402 (tools/: the versions this build hosts and joins)
ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")

limits = read("port/linux/include/halo_port_limits.h")
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION %d$" % netv.CURRENT, limits, re.M)
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION_MINIMUM %d$" % netv.MINIMUM, limits, re.M)
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION_MAXIMUM %d$" % netv.MAXIMUM, limits, re.M)

# the launcher: every network 11..28 selectable, 27 included; All compatible the default
profile = read("port/android/app/src/main/java/com/halo/decomp/NetworkProfile.java")
assert "static final int DEFAULT = 0;" in profile and "static final int CURRENT = %d;" % netv.CURRENT in profile
supported = re.search(r"SUPPORTED = \{([^}]*)\}", profile).group(1)
assert [int(v) for v in supported.split(",")] == netv.SUPPORTED, supported
assert 'return version == 0 ? "All compatible networks"' in profile
config = read("port/linux/src/port_config.c")
assert '{ "network.protocol_version", _config_integer, "0",' in config
browser = read("port/android/app/src/main/java/com/halo/decomp/ServerBrowser.java")
assert '"All compatible networks (%s) · "' % netv.range_text() in browser and "for (int version : NetworkProfile.SUPPORTED)" in browser
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
# (OpenCE Build 201: a lobby message's reliability goes with it when it came over no stream)
assert "map_share_handle_message(machine_index, message, size, machine_index != NONE ?" in handle
assert "distributed_handling_stream_message : !network_connection_last_read_was_unreliable());" in handle
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


# Test66: map sharing itself (OpenCE Build 201's map_share.c, the owner's
# "include EVERYTHING from opence ... INCLUDING map sharing") replaced the
# stand-in that answered every request "not shared": the messages are the
# same four (network 28 carries them; no protocol change), handled by the real
# sharer; its own harness (tools/harness/tests/test_map_share_names.py, from
# upstream) checks the names it accepts and sends.
share_source = read("port/linux/game/map_share.c")
assert "void map_share_handle_message(" in share_source and "boolean map_share_handles_message(" in share_source
import os
names = subprocess.run(["python3", "-m", "pytest", "-q", str(ROOT / "tools/harness/tests/test_map_share_names.py")],
                       capture_output=True, text=True, env=dict(os.environ, HALO_HARNESS_NATIVE="1"))
assert names.returncode == 0, names.stdout + names.stderr
print("PASS: map sharing's names, upstream harness:", names.stdout.strip().splitlines()[-1])

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
# (OpenCE 242: the rule in a function of its own, for the flash and the sound)
assert "return !(last_shield_vitality > 1.0f && last_shield_vitality - shield_vitality <= 0.02f);" in hud
assert hud.count("hud_shield_drop_is_hit(") >= 3
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
print("PASS: Test59 network rules (Test68: hosts 29, joins 11..29 incl. 27 and 28, All compatible default), Build201 map sharing integrated, "
      "28's BSP / lights / second-weapon rules, overshield drain, client bodies (VR-posed ones left alone), renderer limits")
