"""Test73: the mixed-build guard (port/linux/game/network_extras.c). OpenCE 232's text chat took the distributed
kinds 87-89, OpenCE 244's host aim assist policy 90, and the community extras moved after them, to 91-94 (votes 91-92,
the Armor choices 93-94); Test67-72 builds, which host network 28 or 29 and join no host past 29, still send and read
87-92 with their old meanings (votes 87-88, the fork's chat 89-90, the Armor choices 91-92). The real
network_extras.c, compiled against stand-ins and the build's own message enum, is played against:

- as a host, clients of this build and of OpenCE 244 (no extras): each client's kind read, nothing flagged; a client
  sending one of the host's kinds is flagged at once, then nothing from 87 is read from it or sent to it, its
  players are told once, in game, by name, and a machine that leaves is forgotten (no Test67-72 build joins this
  build's network 32, so only a misbehaving machine does this);
- as a client of a host of network 30 or later (this build, OpenCE 242/244): every host's kind read, 90 too;
- as a client of an OpenCE network 29 host: its chat read (88 the size of a chat line, 89), never flagged, and the
  extras (91-94) never sent to it;
- as a client of a Test67-72 host (network 29): its Armor table (old 92), its chat lines (old 90), or its vote's
  details (old 88, their size) flag it at once; then nothing from 87 is read from it or sent to it, told once; a
  new host forgets it.

The wiring is checked too: the receive guard first in network_distributed_handle_message, every send path of these
kinds filtered (the batches, the reliable broadcast per machine, the host's and a machine's sends, the Armor
choices' own sends), the update each frame in main.c."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73-mixed-builds'
OUT.mkdir(parents=True, exist_ok=True)
read = lambda path: (ROOT / path).read_text(encoding='utf-8')

header = read('port/linux/game/network_distributed.h')
enum = re.search(r'enum\n\{\n\t[^}]*?_distributed_message_player_prediction = 1,.*?NUMBER_OF_DISTRIBUTED_MESSAGES\n\};',
                 header, re.S).group(0)
kinds = dict((name, int(value)) for name, value in re.findall(r'_distributed_message_(\w+) = (\d+),', header))
assert [kinds[k] for k in ('chat_up', 'chat_down', 'chat_config', 'aim_assist_policy', 'vote_choice', 'vote_details',
                           'armor', 'armors')] == [87, 88, 89, 90, 91, 92, 93, 94]
extras = read('port/linux/game/network_extras.c')
body = extras[extras.index('/* port/linux/src/port_config.c */'):]

source = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
typedef int boolean; typedef unsigned char byte; typedef unsigned short word; typedef unsigned short wchar16;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define NUMBEROF(a) ((long)(sizeof(a)/sizeof((a)[0])))
#define csmemcpy memcpy
#define csmemset memset
#define csstrncpy strncpy
#define HALO_PORT_MAXIMUM_NETWORK_MACHINES 128
enum { _error_silent };
static int errors;
static void error(int kind, const char *format, ...) { (void)kind; (void)format; errors++; }
typedef unsigned long message_header;
''' + enum + r'''
struct distributed_message_header { message_header header; byte type; byte count; long game_time; };
struct network_machine { wchar16 name[32]; char machine_index; byte padding[3]; };
struct network_game { struct network_machine machines[HALO_PORT_MAXIMUM_NETWORK_MACHINES]; };
struct network_game_client { int unused; };
struct network_game_server { int unused; };
static struct network_game the_game;
static struct network_game_client the_client;
static struct network_game_server the_server;
static int hosting, joined, in_game, notices;
static unsigned int joined_version;
static long votekick_details_size = 40, chat_line_size = 136;
static char last_notice[200];
#define wchar_t wchar16
static struct network_game *network_game_get_game(void) { return joined ? &the_game : NULL; }
static struct network_game_client *global_network_game_client_get(void) { return joined ? &the_client : NULL; }
static struct network_game *network_game_client_get_game(struct network_game_client *c) { return c ? &the_game : NULL; }
static struct network_game_server *global_network_game_server_get(void) { return hosting ? &the_server : NULL; }
static unsigned int network_game_client_joined_version(void) { return hosting ? 0 : joined_version; }
static long network_votekick_details_entry_size(void) { return votekick_details_size; }
static long network_chat_line_entry_size(void) { return chat_line_size; }
static boolean game_in_progress(void) { return in_game; }
static void network_chat_local_notice(char const *text) { notices++; snprintf(last_notice, sizeof(last_notice), "%s", text); }
''' + body.replace('wchar_t const *wide', 'wchar16 const *wide') + r'''
#undef wchar_t
static int config_value = 1;
static unsigned long changes;
int config_boolean(const char *name) { assert(!strcmp(name, "network.community_extras")); return config_value; }
unsigned long config_changes(void) { return changes; }

/* a message of the kind with so many bytes after its header */
static boolean receive_sized(long machine, byte type, long payload)
{
	static unsigned char buffer[512];
	struct distributed_message_header message = { 0, type, 1, 0 };
	memset(buffer, 0, sizeof(buffer));
	memcpy(buffer, &message, sizeof(message));
	return network_extras_receive(machine, (word const *)buffer, (word)(sizeof(message) + payload));
}
static boolean receive(long machine, byte type) { return receive_sized(machine, type, 0); }
static void join(long machine, const char *name)
{
	int i;
	the_game.machines[machine].machine_index = (char)machine;
	for (i = 0; name[i]; i++) the_game.machines[machine].name[i] = (wchar16)name[i];
	the_game.machines[machine].name[i] = 0;
}
static void leave(long machine) { memset(&the_game.machines[machine], 0, sizeof(the_game.machines[machine])); the_game.machines[machine].machine_index = -1; }
static void leave_all(void) { long m; for (m = 0; m < HALO_PORT_MAXIMUM_NETWORK_MACHINES; m++) leave(m); }

/* this build's ways: 1 sent by clients, 2 by the host */
static const int way[] = { [87] = 1 /* chat_up */, [88] = 2 /* chat_down */, [89] = 2 /* chat_config */,
	[90] = 2 /* aim_assist_policy */, [91] = 1 /* vote_choice */, [92] = 2 /* vote_details */, [93] = 1 /* armor */,
	[94] = 2 /* armors */ };

/* a client joined to a host of this network, nothing found yet */
static void client_of(unsigned int version) { joined = 0; network_extras_update(); joined = 1; joined_version = version; }

int main(void)
{
	unsigned int version;
	byte type;

	leave_all();
	/* the kinds: from chat_up to armors, nothing else */
	for (type = 0; type < NUMBER_OF_DISTRIBUTED_MESSAGES; type++)
		assert(network_extras_kind(type) == (type >= 87 && type <= 94));
	assert(!network_extras_kind(_distributed_message_votekick) && !network_extras_kind(_distributed_message_map_share_progress));
	/* ---- the host, with clients of this build (1) and OpenCE 244's (2), and one sending the host's kinds (3) */
	hosting = joined = in_game = 1;
	join(0, "host"); join(1, "new"); join(2, "opence"); join(3, "Odd One");
	for (type = 87; type <= 94; type++)
		if (way[type] == 1) assert(receive(1, type));
	assert(receive(2, _distributed_message_chat_up));
	assert(!network_extras_old_clients() && !errors);
	for (type = 87; type <= 94; type++) { assert(!network_extras_blocked(1, type)); assert(!network_extras_blocked(2, type)); }
	/* the host's kinds the wrong way flag it at once: an Armor table (94) */
	assert(!receive(3, _distributed_message_armors) && errors == 1);
	assert(network_extras_old_clients());
	for (type = 87; type <= 94; type++) { assert(!receive(3, type)); assert(network_extras_blocked(3, type)); }
	assert(!network_extras_blocked(3, _distributed_message_votekick) && !network_extras_blocked(3, _distributed_message_notice));
	assert(!network_extras_blocked(3, 0) && receive(3, _distributed_message_votekick));
	for (type = 87; type <= 94; type++) { assert(!network_extras_blocked(1, type)); assert(!network_extras_blocked(2, type)); }
	/* told once, in game, by name */
	assert(!notices); network_extras_update(); assert(notices == 1 && strstr(last_notice, "Odd One has an older version"));
	network_extras_update(); assert(notices == 1);
	/* it leaves: forgotten; a new machine in its slot is not blocked */
	leave(3); network_extras_update(); assert(!network_extras_old_clients() && !network_extras_blocked(3, 88));
	join(3, "next"); assert(receive(3, _distributed_message_armor));
	/* one whose name is not ASCII, found in the lobby: told when the game is under way */
	in_game = 0; join(4, ""); the_game.machines[4].name[0] = 0x263A; the_game.machines[4].name[1] = 0;
	assert(!receive(4, _distributed_message_aim_assist_policy));
	network_extras_update(); assert(notices == 1);
	in_game = 1; network_extras_update(); assert(notices == 2 && strstr(last_notice, "? has an older version"));
	/* each of the host's kinds flags a client; each client's kind does not */
	for (type = 87; type <= 94; type++)
	{
		join(5, "other"); network_extras_update();
		if (way[type] == 2) { assert(!receive(5, type)); assert(network_extras_blocked(5, 87)); }
		else { assert(receive(5, type)); assert(!network_extras_blocked(5, 87)); }
		leave(5); network_extras_update(); assert(!network_extras_blocked(5, 87));
	}
	/* ---- a client */
	hosting = 0; in_game = 1; notices = 0; errors = 0; leave_all();
	/* a host of network 30 or later: every host's kind read, the extras sent */
	for (version = 30; version <= 32; version++)
	{
		client_of(version);
		for (type = 87; type <= 94; type++)
			if (way[type] == 2) assert(receive(NONE, type));
		assert(receive_sized(NONE, _distributed_message_chat_down, votekick_details_size));
		for (type = 87; type <= 94; type++) assert(!network_extras_blocked(NONE, type));
	}
	assert(!errors && !notices);
	/* OpenCE's own host of network 29: its chat read, never flagged; the extras not sent to it */
	client_of(29);
	assert(receive_sized(NONE, _distributed_message_chat_down, chat_line_size) && receive(NONE, _distributed_message_chat_config));
	assert(!network_extras_blocked(NONE, _distributed_message_chat_up));
	for (type = 91; type <= 94; type++) assert(network_extras_blocked(NONE, type));
	assert(!errors);
	/* a Test67-72 host (network 29): its Armor table, old 92, sent to each newcomer */
	assert(!receive(NONE, 92) && errors == 1);
	for (type = 87; type <= 94; type++) { assert(!receive(NONE, type)); assert(network_extras_blocked(NONE, type)); }
	assert(!network_extras_blocked(NONE, _distributed_message_votekick) && receive(NONE, _distributed_message_notice));
	network_extras_update(); assert(notices == 1 && strstr(last_notice, "The host has an older version"));
	/* still with that host between games; forgotten when this machine leaves it */
	in_game = 0; network_extras_update(); assert(network_extras_blocked(NONE, 87));
	in_game = 1; client_of(29); assert(!network_extras_blocked(NONE, 87));
	/* its chat lines, old 90, show it too */
	assert(!receive(NONE, 90) && network_extras_blocked(NONE, 88));
	/* its vote's details, old 88, by their size (not a chat line's) */
	client_of(29); assert(receive_sized(NONE, 88, chat_line_size) && !network_extras_blocked(NONE, 87));
	assert(!receive_sized(NONE, 88, votekick_details_size) && network_extras_blocked(NONE, 87));
	/* where the two sizes are one, 88 tells nothing (the other kinds still do) */
	votekick_details_size = chat_line_size;
	client_of(29); assert(receive_sized(NONE, 88, chat_line_size) && !network_extras_blocked(NONE, 87));
	assert(!receive(NONE, 92) && network_extras_blocked(NONE, 87));
	votekick_details_size = 40;
	/* every Test67-72 host's kind past OpenCE's 29 flags it: old 90 (chat) and 92 (armors) */
	for (type = 90; type <= 94; type++)
	{
		client_of(29);
		assert(!receive(NONE, type)); assert(network_extras_blocked(NONE, 87));
	}
	client_of(0); assert(!network_extras_blocked(NONE, 87));
	/* a message too short to have a header is the netcode's to refuse */
	{ word tiny = 0; assert(network_extras_receive(NONE, &tiny, 1)); }
	/* network.community_extras still reads as before */
	assert(network_extras_enabled()); config_value = 0; changes++; assert(!network_extras_enabled());
	puts("PASS: the guard: this build's and OpenCE's peers read and never flagged (hosts of 30-32 whole, OpenCE 29 "
		"hosts' chat, and no extras sent to them); a Test67-72 host (29) by its table (old 92), chat (old 90) or "
		"vote details (old 88's size) at once, and a client sending the host's kinds; then nothing from 87 read from "
		"or sent to it; told once in game, by name (non-ASCII as ?); forgotten as it leaves");
	return 0;
}
'''
(OUT / 'mixed.c').write_text(source)
subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Wno-unused-function', '-fsanitize=address,undefined',
                '-fno-sanitize-recover=all', str(OUT / 'mixed.c'), '-o', str(OUT / 'mixed')], check=True)
subprocess.run([str(OUT / 'mixed')], check=True)

# ---- the wiring
distributed = read('port/linux/game/network_distributed.c')
handle = distributed[distributed.index('void network_distributed_handle_message('):]
assert handle.index('if (!network_extras_receive(machine_index, message, size))\n\t\treturn;') < \
    handle.index('network_voice_handles_message(message, size)') < handle.index('armor_sync_handles_message(message, size)')
send = distributed[distributed.index('void distributed_send(\n'):distributed.index('/* a packer\'s messages of the type')]
assert send.count('network_extras_blocked(') == 6, send.count('network_extras_blocked(')
assert 'if (network_extras_kind(type) && network_extras_old_clients())' in send
assert 'network_distributed_server_send_to_machine_reliably(machine_indices[index], message, size);' in send
armor = read('port/linux/game/armor_sync.c')
assert 'network_extras_blocked(machine_index, _distributed_message_armors)' in armor
assert 'network_extras_blocked(NONE, _distributed_message_armor)' in armor
main = read('source/main/main.c')
assert main.index('network_chat_update();') < main.index('network_extras_update();') < \
    main.index('profile_scope_enter(main_network_start_frame_section)')
chat_h = read('port/linux/game/network_chat.h')
assert 'void network_chat_local_notice(char const *text);' in chat_h
# every send of these kinds goes through the filtered paths: no direct low-level send of them elsewhere
for path in ('port/linux/game/network_chat.c', 'port/linux/game/network_votekick.c'):
    text = read(path)
    assert 'network_distributed_server_send_to_all_reliably' not in text and \
        'network_distributed_client_send_reliably' not in text, path
print('PASS: wiring: the guard before every handler, six filtered send paths and the reliable broadcast per machine, '
      'the Armor choices\' own sends, the update after the chat\'s each frame; chat and votes only through them')
