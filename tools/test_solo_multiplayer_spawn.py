"""Bound and scope the local New Game multiplayer-map spawn fallback."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "source/game/players.c").read_text()
header = ROOT / "source/game/solo_multiplayer_spawn_math.h"

fixture = r'''
#include <assert.h>
#include "source/game/solo_multiplayer_spawn_math.h"
int main(void) {
    assert(players_solo_mp_spawn_enabled(1, 1, 0));
    assert(!players_solo_mp_spawn_enabled(1, 0, 0)); /* network peers stay native */
    assert(!players_solo_mp_spawn_enabled(1, 1, 1)); /* campaign co-op stays native */
    assert(!players_solo_mp_spawn_enabled(0, 1, 0)); /* campaign scenarios stay native */
    assert(!players_solo_mp_reuse_saved_unit(1, 0));
    assert(!players_solo_mp_reuse_saved_unit(1, 1));
    assert(players_solo_mp_reuse_saved_unit(0, 0));
    assert(!players_solo_mp_reuse_saved_unit(0, 1));
    assert(players_solo_mp_accept_native_start(1, 1, 1));
    assert(!players_solo_mp_accept_native_start(1, 0, 1));
    assert(!players_solo_mp_accept_native_start(1, 1, 0));
    assert(!players_solo_mp_accept_native_start(0, 1, 1));
    assert(players_solo_mp_spawn_priority(1, -1, 0) == 5);
    assert(players_solo_mp_spawn_priority(1, -1, 1) == 4);
    assert(players_solo_mp_spawn_priority(0, 0, 0) == 3); /* CTF team 0 */
    assert(players_solo_mp_spawn_priority(0, 0, 1) == 2); /* another CTF flag */
    assert(players_solo_mp_spawn_priority(0, 2, 0) == 1); /* oddball/other point */
    assert(players_solo_mp_spawn_priority(0, 6, 0) == 0); /* teleporter source */
    assert(players_solo_mp_spawn_priority(0, 7, 0) == 0); /* teleporter target */
    assert(players_solo_mp_spawn_priority(0, 9, 0) == 0); /* invalid type */
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="solo-mp-spawn-") as temp:
    path = Path(temp)
    (path / "fixture.c").write_text(fixture)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-I", str(ROOT), str(path / "fixture.c"), "-o", str(path / "fixture")], check=True)
    subprocess.run([str(path / "fixture")], check=True)

spawn = source[source.index("static void player_spawn("):source.index("/* the distributed netcode", source.index("static void player_spawn("))]
assert "scenario->type == _scenario_type_multiplayer" in spawn
assert "players_solo_mp_spawn_enabled(" in spawn
assert "solo_mp_free_roam = local_mp_map && !game_engine_running();" in spawn
assert "players_solo_mp_reuse_saved_unit(solo_mp_free_roam, game_engine_running())" in spawn
assert "bypassing saved campaign unit" in spawn
assert "players_solo_mp_accept_native_start(local_mp_map," in spawn
assert "native game-type start" in spawn
assert "game_connection() == _game_connection_local" in spawn
assert "network_campaign_playing()" in spawn
assert "players_solo_mp_spawn_location(scenario" in spawn
assert "scenario_leaf_index_from_point(position) != NONE" in source
assert "scenario->netgame_flags" in source
assert "multiplayer_information->unit.index" in spawn
assert "player_information->player_unit.index" in spawn
assert "local multiplayer map spawn failed" in spawn
print("PASS: local MP maps bypass stale campaign units and choose a valid native/fallback in-BSP start; network and campaign paths remain scoped")
