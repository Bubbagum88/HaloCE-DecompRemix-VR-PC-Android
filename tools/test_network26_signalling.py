"""Internet-play signalling with OpenCE Build184 (network 26) and older hosts.

OpenCE network 26 made JOIN/ACCEPT message version 4: after the address list
each machine says its WebRTC (none, a native build's DTLS certificate hash,
or a browser's ICE credentials and mDNS names), and a version-4 host reads
nothing else. Network 24/25 hosts read version 3 only. This build has no
WebRTC: it says none, asks in both versions until a host answers in one,
then keeps to that one, and as a host answers each request in its own
version, turning browsers away (they reach a host over WebRTC alone).

The production get_addresses/put_addresses are extracted from
port/linux/src/p2p_signal.c and run against byte layouts written as a
Build184 machine writes them (p2p_signal.c: put_addresses).
"""
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "port/linux/src/p2p_signal.c").read_text(encoding="utf-8")
limits = (ROOT / "port/linux/include/halo_port_limits.h").read_text(encoding="utf-8")


def function(name):
    start = source.index(name)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        depth += {"{": 1, "}": -1}.get(source[index], 0)
        if depth == 0:
            return source[start:index + 1]
    raise AssertionError(name)


# Test59: hosting moves to OpenCE network 28 (27: map sharing, 28: its rules); 26's signalling is unchanged
assert "#define HALO_PORT_NETWORK_VERSION 28" in limits
assert "#define HALO_PORT_NETWORK_VERSION_MAXIMUM 28" in limits
assert "MESSAGE_VERSION_LEGACY = 3," in source and "MESSAGE_VERSION = 4," in source
send = function("static void send_join(void)")
assert "send_join_version(MESSAGE_VERSION);" in send and "send_join_version(MESSAGE_VERSION_LEGACY);" in send
assert "!signalling.join_version ||" in send
accept = function("static void accept_received(")
assert "signalling.join_version = version;" in accept
assert "if (signalling.join_version && version != signalling.join_version)" in accept
assert "!= \n\t\tsize - TAG_SIZE - fixed" in accept or "!=\n\t\tsize - TAG_SIZE - fixed" in accept
join = function("static void join_received(")
assert "webrtc_kind == SIGNAL_WEBRTC_BROWSER" in join and "proven = size - fixed - read;" in join
assert join.count(", version);") == 3, "every accept answers in the request's own version"
dispatch = source[source.index("if (signalling.hosting && !strcmp(topic, signalling.host_topic))"):]
dispatch = dispatch[:dispatch.index("/* a CONNACK")]
assert dispatch.count("message[1] == MESSAGE_VERSION || message[1] == MESSAGE_VERSION_LEGACY") == 2
assert "signalling.join_version = 0;" in function("void p2p_signal_join(")

enum = source[source.index("MESSAGE_VERSION_LEGACY = 3,"):]
enum = enum[:enum.index("};")]
harness = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define P2P_MAXIMUM_CANDIDATES 8
struct p2p_candidate { unsigned int address; unsigned short port; };
enum { _message_join = 'J', _message_accept = 'A',
''' + enum + r'''};
static int p2p_local_candidates(struct p2p_candidate *c, int maximum)
{ (void)maximum; c[0].address = 0x0100007f; c[0].port = 0x3412; c[1].address = 0x0a0a0a0a; c[1].port = 0x7856; return 2; }
''' + function("static int put_candidates(unsigned char *message)") + "\n" + \
    "static int get_candidates(const unsigned char *message, int size, struct p2p_candidate *candidates);\n" + \
    function("static int put_addresses(unsigned char *message, int version)") + "\n" + \
    function("static int skip_ice_text(") + "\n" + function("static int get_addresses(") + "\n" + \
    function("static int get_candidates(const unsigned char *message, int size, struct p2p_candidate *candidates)\n{") + r'''
static int parse(const unsigned char *m, int n, int version, int *count, int *kind)
{ struct p2p_candidate c[P2P_MAXIMUM_CANDIDATES]; return get_addresses(m, n, version, c, count, kind); }
int main(int argc, char **argv)
{
	unsigned char own[256];
	int count, kind, size;
	/* this build: version 3 is the bare list; version 4 adds "no WebRTC" */
	size = put_addresses(own, MESSAGE_VERSION_LEGACY);
	assert(size == 13 && parse(own, size, MESSAGE_VERSION_LEGACY, &count, &kind) == 13 && count == 2 && kind == 0);
	size = put_addresses(own, MESSAGE_VERSION);
	assert(size == 14 && own[13] == SIGNAL_WEBRTC_NONE);
	assert(parse(own, size, MESSAGE_VERSION, &count, &kind) == 14 && count == 2 && kind == SIGNAL_WEBRTC_NONE);
	/* a version-4 list cut before its WebRTC kind is not one */
	assert(parse(own, 13, MESSAGE_VERSION, &count, &kind) == -1);
	/* Build184 layouts from the Python side: each must be read to its exact end */
	for (int i = 1; i + 2 < argc; i += 3)
	{
		unsigned char bytes[512];
		int length = 0, expected = atoi(argv[i + 1]), expected_kind = atoi(argv[i + 2]);
		for (const char *hex = argv[i]; hex[0] && hex[1]; hex += 2)
			sscanf(hex, "%2hhx", &bytes[length++]);
		int read = parse(bytes, length, MESSAGE_VERSION, &count, &kind);
		if (read != expected || (read >= 0 && kind != expected_kind))
		{
			printf("case %d: read %d (expected %d) kind %d (expected %d)\n", i / 3, read, expected, kind, expected_kind);
			return 1;
		}
	}
	puts("ok");
	return 0;
}
'''


def addresses(candidates):
    out = bytes([len(candidates)])
    for address, port in candidates:
        out += struct.pack("<IH", address, port)
    return out


def webrtc(kind, ufrag=b"", password=b"", names=()):
    out = bytes([kind]) + bytes(range(32)) + bytes([len(ufrag)]) + ufrag + bytes([len(password)]) + password
    out += bytes([len(names)])
    for name, port in names:
        out += bytes([len(name)]) + name + struct.pack("<H", port)
    return out


cases = []
native = addresses([(0x0100007F, 0x1234), (0x0A000001, 0x2222)]) + webrtc(1)
cases.append((native, len(native), 1))
browser = addresses([]) + webrtc(2, b"Ab+/", b"abcdefghijklmnopqrstuv", [(b"0f3a-11.local", 5000)])
cases.append((browser, len(browser), 2))
cases.append((addresses([]) + bytes([0]), 2, 0))
# malformed: unknown kind, ufrag without password, bad mDNS name, cut short, too many names
cases.append((addresses([]) + webrtc(3), -1, 0))
cases.append((addresses([]) + webrtc(2, b"Ab+/", b""), -1, 0))
cases.append((addresses([]) + webrtc(2, b"Ab+/", b"abcdefghijklmnopqrstuv", [(b"bad_name.local", 5000)]), -1, 0))
cases.append((native[:-1], -1, 0))
cases.append((addresses([]) + webrtc(2, b"Ab+/", b"abcdefghijklmnopqrstuv",
                                     [(b"a.local", 1), (b"b.local", 2), (b"c.local", 3)]), -1, 0))

clang = shutil.which("clang")
if clang:
    with tempfile.TemporaryDirectory() as temp:
        c = Path(temp) / "signal.c"
        c.write_text("#include <stdlib.h>\n" + harness, encoding="utf-8")
        exe = Path(temp) / "signal"
        subprocess.run([clang, "-std=gnu11", "-Wall", "-Werror", "-Wno-unused-function",
                        "-fsanitize=address,undefined", str(c), "-o", str(exe)], check=True)
        arguments = []
        for data, expected, kind in cases:
            arguments += [data.hex(), str(expected), str(kind)]
        result = subprocess.run([str(exe), *arguments], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    print("PASS: signalling reads Build184 native/browser WebRTC descriptions to their exact end, rejects malformed ones, "
          "and writes version 3 or 4 (none) itself")
# network 25 (OpenCE 767a4edb): the host's object states carry a unit's
# integrated light, with a bit saying it was sent (older hosts send zeros,
# which are not "off"); a client applies it except to what its player drives
objects = (ROOT / "port/linux/game/network_objects.c").read_text(encoding="utf-8")
flags = objects[objects.index("_distributed_object_carried_bit = 0,"):]
flags = flags[:flags.index("};")]
assert re.findall(r"(_distributed_object_\w+_bit)", flags) == [
    "_distributed_object_carried_bit", "_distributed_object_at_rest_bit", "_distributed_object_dead_bit",
    "_distributed_object_predicted_bit", "_distributed_object_light_sent_bit", "_distributed_object_light_on_bit"], \
    "state flag bits must keep OpenCE's order"
assert "SET_FLAG(state->flags, _distributed_object_light_sent_bit, TRUE);" in objects
assert "TEST_FLAG(state->flags, _distributed_object_light_sent_bit) &&" in objects
assert "!distributed_unit_driven_here(state->object_index)" in objects
print("PASS: network 25 integrated-light state bits sent by this host and applied from 25/26 hosts")
print("PASS: joins ask in versions 4 and 3 until answered, then keep the host's; hosts answer in the request's version "
      "and turn browsers away; hosting is network 28 with clients 11-28")
