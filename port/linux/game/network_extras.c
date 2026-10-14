/*
NETWORK_EXTRAS.C

HaloCE-Quest-VR: the community extras of network games, the OpenCE fork
jcompto95-tech's: the Armor choices shared (armor_sync.c), text chat
(network_chat.c) and votes to kick or ban with a reason (network_votekick.c).
They travel in distributed messages of their own (87 to 92), which OpenCE
network 28 builds without them drop as unknown kinds, so a game with those
players is the same game: no network version change, joins as before.

network.community_extras (port_config.c; the launcher's NETWORK screen) turns
them off: then this machine sends none of them and reads none it is sent.
*/

#include "cseries.h"
#include "network_extras.h"

/* port/linux/src/port_config.c */
int config_boolean(const char *name);
unsigned long config_changes(void);

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
