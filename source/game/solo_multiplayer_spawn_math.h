#ifndef SOLO_MULTIPLAYER_SPAWN_MATH_H
#define SOLO_MULTIPLAYER_SPAWN_MATH_H

/* The New Game flow can load a multiplayer scenario without a network
 * connection or a running game engine. It must never inherit the campaign
 * continuation unit, even if the local-player slot still contains one. */
static int players_solo_mp_spawn_enabled(int multiplayer_scenario,
	int local_connection, int campaign_active)
{
	return multiplayer_scenario && local_connection && !campaign_active;
}

static int players_solo_mp_reuse_saved_unit(int local_mp_map, int engine_running)
{
	return !local_mp_map && !engine_running;
}

static int players_solo_mp_accept_native_start(int local_mp_map,
	int engine_running, int native_start_valid)
{
	return local_mp_map && engine_running && native_start_valid;
}

/* Candidate priority for the local New Game free-roam path. Network player
 * spawns continue to use the engine's game-type/team start selection. */
static int players_solo_mp_spawn_priority(int is_player_start, int flag_type,
	int team_index)
{
	if (is_player_start)
		return team_index == 0 ? 5 : 4;
	if (flag_type == 0) /* CTF flag */
		return team_index == 0 ? 3 : 2;
	if (flag_type < 0 || flag_type >= 9 || flag_type == 6 || flag_type == 7)
		return 0; /* invalid, teleporter source or target */
	return 1; /* another authored non-teleporter netgame location */
}

#endif
