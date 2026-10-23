/*
NETWORK_EXTRAS.C

HaloCE-Quest-VR: the community extras of network games, the OpenCE fork
jcompto95-tech's: the Armor choices shared (armor_sync.c) and votes to kick
or ban with a reason (network_votekick.c). They travel in distributed
messages of their own (Test73: 91 to 94), which OpenCE builds without them
drop as unknown kinds, so a game with those players is the same game: no
network version change, joins as before.

network.community_extras (port_config.c; the launcher's NETWORK screen) turns
them off: then this machine sends none of them and reads none it is sent.

Test73: OpenCE 232's text chat (network_chat.c, its kinds 87 to 89) took the
fork's chat's place, OpenCE 244's aim assist policy took 90
(network_aim_assist.c), and the extras moved after them (votes 91 and 92, the
Armor choices 93 and 94). Test67-72 builds, which host network 28 or 29 and
join no host past 29, still give the kinds from 87 their old meanings (votes
87 and 88, the fork's chat 89 and 90, the Armor choices 91 and 92). So:

- a client of a host of network 30 or later reads these kinds as they are
  now: no Test67-72 build hosts such a game;
- a client of a host of network 29 or before never sends it the extras (91
  to 94: OpenCE's builds of those networks have none, Test67-72's number them
  otherwise), only OpenCE's text chat; and no OpenCE build of those networks
  sends a kind past 89, so a host that sends one (a Test67-72 host: its chat
  lines, 90, and its Armor table, 92, which it sends to each machine that
  joins) runs a Test67-72 build, as does one that sends 88 the size of its
  vote's details rather than a chat line (in this build both are 68 bytes,
  so 88 alone shows nothing: the table, at the join, does). From then on no
  message from 87 is read from that host or sent to it, and the players
  here are told once;
- a host (whose players' builds join it only at its own network) takes these
  kinds only the way each goes, from the clients to the host or the host to
  the clients: a client sending one the wrong way is treated as above.
*/

#include "cseries.h"
#include "cseries/errors.h"
#include "game/game.h"
#include "bungie_net/common/message_header.h"
#include "networking/network_game_globals.h"
#include "networking/network_game_manager.h"
#include "networking/network_client_manager.h"
#include "network_distributed.h"
#include "network_extras.h"
#include "network_chat.h"

#include <stdio.h>

/* port/linux/src/port_config.c */
int config_boolean(const char *name);
unsigned long config_changes(void);

enum
{
	EXTRAS_MACHINES = HALO_PORT_MAXIMUM_NETWORK_MACHINES,
	/* the latest network a Test67-72 build hosts (Test67 28, Test68-72 29) */
	EXTRAS_LAST_OLD_NETWORK_VERSION = 29,
};

/* the host: the clients found sending these kinds the wrong way; a client:
whether its host runs a Test67-72 build */
static boolean extras_old_machines[EXTRAS_MACHINES];
static boolean extras_old_host;
/* the notice of the latest found, shown once a game is under way (the lobby
draws no chat) */
static char extras_notice[160];

boolean network_extras_enabled(
	void)
{
	static unsigned long read_at = (unsigned long)-1;
	static boolean enabled = TRUE;

	if (read_at != config_changes())
	{
		read_at = config_changes();
		enabled = config_boolean("network.community_extras") != 0;
	}
	return enabled;
}

boolean network_extras_kind(
	byte type)
{
	return type >= _distributed_message_chat_up && type <= _distributed_message_armors;
}

/* the kinds only the host sends (the others of them, only clients) */
static boolean extras_kind_from_host(
	byte type)
{
	return type == _distributed_message_chat_down || type == _distributed_message_chat_config ||
		type == _distributed_message_aim_assist_policy || type == _distributed_message_vote_details ||
		type == _distributed_message_armors;
}

/* a client: whether the host it joined may run a Test67-72 build (a host of
network 29 or before; 0 is this machine's own host or none) */
static boolean extras_host_may_be_old(
	void)
{
	unsigned int version = network_game_client_joined_version();

	return version != 0 && version <= EXTRAS_LAST_OLD_NETWORK_VERSION;
}

/* a machine's name, as the host has it, in ASCII (others '?') */
static void extras_machine_name(
	long machine_index,
	char *name,
	short size)
{
	struct network_game *game = network_game_get_game();
	short index = 0;

	if (game && machine_index >= 0 && machine_index < EXTRAS_MACHINES &&
		game->machines[machine_index].machine_index == machine_index)
	{
		wchar_t const *wide = game->machines[machine_index].name;

		for (; index < size - 1 && index < (short)NUMBEROF(game->machines[machine_index].name) && wide[index]; index++)
			name[index] = wide[index] >= ' ' && wide[index] < 0x7F ? (char)wide[index] : '?';
	}
	if (!index)
	{
		csstrncpy(name, "A player", size - 1);
		name[size - 1] = 0;
		return;
	}
	name[index] = 0;
}

boolean network_extras_receive(
	long machine_index,
	word const *message,
	word size)
{
	struct distributed_message_header header;

	if (size < sizeof(header))
		return TRUE;
	csmemcpy(&header, message, sizeof(header));
	if (!network_extras_kind(header.type))
		return TRUE;
	if (machine_index != NONE)
	{
		/* (the host: a client's) */
		if (machine_index < 0 || machine_index >= EXTRAS_MACHINES)
			return TRUE;
		if (extras_old_machines[machine_index])
			return FALSE;
		if (!extras_kind_from_host(header.type))
			return TRUE;
		extras_old_machines[machine_index] = TRUE;
		{
			char name[40];

			extras_machine_name(machine_index, name, (short)sizeof(name));
			snprintf(extras_notice, sizeof(extras_notice), "%s has an older version of this port: text chat, "
				"votes and armor are off with them until they update", name);
		}
		error(_error_silent, "community extras: machine %ld sent kind %d the host's way: another build",
			machine_index, header.type);
		return FALSE;
	}
	/* (a client: the host's) */
	if (!extras_host_may_be_old())
		return TRUE;
	if (extras_old_host)
		return FALSE;
	if (header.type < _distributed_message_aim_assist_policy &&
		!(header.type == _distributed_message_chat_down &&
			size == sizeof(header) + network_votekick_details_entry_size() &&
			network_votekick_details_entry_size() != network_chat_line_entry_size()))
	{
		return TRUE;
	}
	extras_old_host = TRUE;
	snprintf(extras_notice, sizeof(extras_notice), "The host has an older version of this port: text chat, votes "
		"and armor are off in this game until it updates");
	error(_error_silent, "community extras: the host (network %u) sent kind %d (%d bytes): a Test67-72 build",
		network_game_client_joined_version(), header.type, size);
	return FALSE;
}

boolean network_extras_blocked(
	long machine_index,
	byte type)
{
	if (!network_extras_kind(type))
		return FALSE;
	if (machine_index == NONE)
	{
		/* (to the host: none to a Test67-72 one; the extras to none of
		network 29 or before) */
		return extras_old_host || (type >= _distributed_message_vote_choice && extras_host_may_be_old());
	}
	return machine_index >= 0 && machine_index < EXTRAS_MACHINES && extras_old_machines[machine_index];
}

boolean network_extras_old_clients(
	void)
{
	long machine_index;

	for (machine_index = 0; machine_index < EXTRAS_MACHINES; machine_index++)
	{
		if (extras_old_machines[machine_index])
			return TRUE;
	}
	return FALSE;
}

void network_extras_update(
	void)
{
	struct network_game_client *client = global_network_game_client_get();
	struct network_game *game = client ? network_game_client_get_game(client) : NULL;
	long machine_index;

	if (extras_notice[0] && game_in_progress())
	{
		network_chat_local_notice(extras_notice);
		extras_notice[0] = 0;
	}
	if (global_network_game_server_get())
	{
		/* (the host's own copy of the game, as armor_sync.c reads it) */
		struct network_game *hosted = network_game_get_game();

		if (hosted)
			game = hosted;
		/* (a slot left, or taken by another machine since: forgotten) */
		for (machine_index = 0; machine_index < EXTRAS_MACHINES; machine_index++)
		{
			if (extras_old_machines[machine_index] &&
				(!game || game->machines[machine_index].machine_index != machine_index))
			{
				extras_old_machines[machine_index] = FALSE;
			}
		}
		extras_old_host = FALSE;
		return;
	}
	csmemset(extras_old_machines, 0, sizeof(extras_old_machines));
	if (!game)
		extras_old_host = FALSE;
}
