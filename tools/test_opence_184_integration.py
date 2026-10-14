"""OpenCE Build184 (network 26) integration for Test53.

Ported from https://github.com/OpenCommunityEdition/OpenCE (tag build-184,
19f1bd9f). The engine base remains Build157 with selected compatible changes;
this is not a full Build184 rebase. The protocol work (network 25's
integrated light, network 26's signalling) is checked by
test_network26_signalling.py; this suite guards the other selected fixes.

Ported: co-op stale player handles (6ea142ce + #250 fb97e526), co-op elevator
riding (8dad0c75), a connection made is open (ab3c388c), telnet HTTP drop
(0fb9b576), respawned vehicles keep their teleporter name (af7ad15d), vehicle
homes (21db5f90), HUD digits on their own bitmaps (a3c139ec, adapted), Custom
Edition map listing through its own handle (a845bbf5, adapted to the managed
data set), Settings with no profile asks for a name (3dcacc95).

Reviewed, not ported: browser/WebRTC hosting and the web build (this build
has no WebRTC: browsers cannot join its hosts); display.first_person_legs,
display.shield_color/shield_glow/viewmodel_shield (new display features built
on OpenCE's video-settings screens, which this port's menus do not have; the
VR body already shows the player's legs); campaign pause row spacing (art and
menu-generator change); banned-join rejection reason (message text only, on
server code this port does not share); profiling build.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


distributed = read("port/linux/game/network_distributed.c")
assert "static boolean distributed_riding_moving_elevator(" in distributed
assert "if (distributed_riding_moving_elevator(unit_index))\n\t\tposition.z = object->object.position.z;" in distributed

connection = read("source/networking/network_connection.c")
assert "SET_FLAG(connection->flags, _connection_closed_bit, FALSE);" in connection

damage = read("source/objects/damage.c")
assert "static void damage_data_validate_owner(" in damage
assert damage.count("damage_data_validate_owner(damage);") >= 2
game_manager = read("source/networking/network_game_manager.c")
assert "static void network_game_player_forget(" in game_manager
assert "network_game_player_forget(quitter_index);" in game_manager
assert "void player_delete(long player_index);" in game_manager  # the guest ABI's declaration (Test52)

telnet = read("source/networking/telnet_console.c")
assert "HTTP" in telnet or "http" in telnet

engine = read("source/game/game_engine.c")
assert "static boolean game_engine_vehicle_empty(" in engine
assert "static long game_engine_vehicle_home_on_pad(" in engine

hud = read("source/interface/hud_draw.c")
assert "static boolean hud_digits_share_bitmap(" in hud
assert hud.count("!digits_on_one_bitmap || source_bitmap==number_bitmap);") == 5
assert hud.count("if (number_bitmap)\n") == 5

maps = read("port/linux/game/custom_edition_maps.c")
look_for = maps[maps.index("static void custom_edition_maps_look_for("):]
look_for = look_for[:look_for.index("static void custom_edition_maps_ensure_current(")]
assert "FindFirstFileA(pattern, &data)" in look_for and "FindNextFileA(find, &data)" in look_for
look_for_code = re.sub(r"/\*.*?\*/", "", look_for, flags=re.S)
assert "find_files_start" not in look_for_code and "find_files_next" not in look_for_code, \
    "the shared find_files_* listing can race the menus' folder cleanup and delete the maps"
assert "CloseHandle(find);" in look_for

menu_functions = read("port/linux/game/menu_functions.c")
assert "static boolean profile_edit_begin(" in menu_functions
assert "static boolean new_profile_decision(" in menu_functions
assert 'return profile_edit_begin(widget, event, widget_deleted);' in menu_functions
tags = read("port/linux/game/menu_tags.c")
functions = tags[tags.index("port_function_names[] ="):]
functions = functions[:functions.index("};")]
assert '"new campaign decision",' in functions, "dispatched by name: it must be one of the port's functions"

limits = read("port/linux/include/halo_port_limits.h")
assert "#define HALO_PORT_NETWORK_VERSION 29" in limits and "OpenCE\nBuild206" in limits  # Test68: network 29
print("PASS: selected OpenCE Build184 fixes integrated (co-op stale handles and elevators, joining, vehicles, "
      "HUD digits, CE map listing, profile-less Settings); network 28 hosting (Test59)")
