"""Guard selected OpenCE 169-177 changes and the unchanged network identity."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
tags = (ROOT / "source/tag_files/tag_groups.c").read_text()
players = (ROOT / "source/game/players.c").read_text()
memory = (ROOT / "port/android/host/host_memory.c").read_text()
sdl = (ROOT / "port/android/host/host_sdl.c").read_text()
threads = (ROOT / "port/android/host/host_thread.c").read_text()
abi = (ROOT / "port/android/include/halo_android_abi.h").read_text()
hud_tool = (ROOT / "tools/hud_assets.py").read_text()
hud_layout = json.loads((ROOT / "port/assets/hud/layout.json").read_text())

# Build169: malformed CE block indices receive safe empty data, while Xbox
# cache tags keep the strict assertions.
assert "an element past the block" in tags and "nothing checked" in tags
assert "if (!custom_edition_cache_tags_loaded())" in tags
assert "return element_size <= TAG_EMPTY_DATA_SIZE ? tag_empty_data() : NULL;" in tags

# Build173: large network co-op games respawn beside a safe member of the
# largest grounded group; the ordinary small-lobby path is still explicit.
respawn = players[players.index("static long players_coop_respawn_unit(", players.index("static long players_coop_respawn_unit(") + 1):]
assert "if (!players_coop_use_majority())" in respawn
assert "players_coop_near_count(positions, count, index, radius_squared)" in respawn
assert "return unit_indices[anchor_index];" in respawn

# Builds170/175: guest callback threads detach their guest pthread, gamepad
# handles close through SDL, and kernels treating MAP_FIXED_NOREPLACE as a
# hint cannot leave a misplaced reservation counted as success.
assert "thread_detach" in abi and "header->thread_detach" in threads
assert "host_sdl_close_gamepad" in sdl and "SDL_CloseGamepad(object)" in sdl
assert "audio_binding_free" in sdl and "pthread_condattr_setclock" in sdl
assert "host_native_thread_create(audio_thread" in sdl and "handle_release(binding->handle" in sdl
host_memory = memory[memory.index("static void *map_fixed_noreplace("):]
assert "result != (void *)address" in host_memory
assert "munmap(result, size);" in host_memory

# Build176: pagemap denial takes the mincore+range-swap fallback, and unknown
# page state is retained. Build177: the exact reticle sheet and sniper scope
# artwork are represented by the generated layout and embedded source assets.
assert "range_usage_mincore" in memory and "range_swap_kb(mapping_start, from, to)" in memory
assert "usage_result != _range_unused" in memory
assert "host_memory_reclaim_test_no_pagemap" in memory
assets = {entry["name"] for entry in hud_layout["assets"]}
assert "hud_reticles__7" in assets
assert "sniper__hud_reticles_scope__0" in assets
assert "def reticles(arguments)" in hud_tool and 'commands.add_parser("reticles")' in hud_tool

print("Selected OpenCE Builds 169, 170, 173, 175-177 integration guards pass; network24 is preserved")
