"""Test72: a phone on mobile data through a VPN (its public address Google's)
reached the FOOZY host's tunnel - its pings answered - but each join timed
out 5 s after the game's connection was made ("timeout in
network_connection_idle"), in a 10-13 player lobby. The game's connection
is a stream carried over the tunnel (KCP), whose 1200-byte pieces came to
1280 bytes on the wire over IPv6 - the very limit, with no room for a VPN's
own wrapping - while the pings are a few bytes (the likely cause, not
proven: the host's side was not seen). So:
- the tunnel's datagrams are sent without "don't fragment"
  (posix_socket_allow_fragments): a narrower path fragments, not drops;
- this side's stream pieces are 1000 bytes (a KCP receiver takes any size:
  the protocol, network 29, is unchanged);
- pieces unanswered for 3 s while the peer answers pings, and a datagram the
  system refuses, are said once each.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
p2p = read("port/linux/src/p2p.c")
posix_h = read("port/linux/src/posix.h")
posix_net = read("port/linux/src/posix_net.c")
win32_net = read("port/windows/src/win32_net.c")

def constant(name):
    return int(re.search(r"\b%s = (\d+)," % name, p2p).group(1))

kcp_mtu = constant("KCP_MTU")
assert kcp_mtu == 1000
assert "ikcp_setmtu(stream->kcp, KCP_MTU);" in p2p
# a piece on the wire: the tunnel's magic, identifier and counter, the inner
# type byte, the KCP segment, the seal's tag; UDP and IPv6 headers
identifier = int(re.search(r"P2P_IDENTIFIER_SIZE = (\d+)", read("port/linux/src/p2p_internal.h")).group(1))
tag = int(re.search(r"P2P_TAG_SIZE = (\d+)", read("port/linux/src/p2p_internal.h")).group(1))
on_wire = (1 + identifier + 8) + 1 + kcp_mtu + tag + 8 + 40
assert on_wire <= 1280 - 100, on_wire  # under a VPN's 1280 with room for its own wrapping
assert (1 + identifier + 8) + 1 + 1200 + tag + 8 + 40 >= 1280  # the old size: at the limit, no room for a VPN's wrapping

assert "void posix_socket_allow_fragments(int socket);" in posix_h
linux = posix_net[posix_net.index("void posix_socket_allow_fragments(int socket)"):]
linux = linux[:linux.index("\n}\n")]
assert "int value = IP_PMTUDISC_DONT;" in linux and "setsockopt(socket, IPPROTO_IP, IP_MTU_DISCOVER," in linux
windows = win32_net[win32_net.index("void posix_socket_allow_fragments(int socket)"):]
windows = windows[:windows.index("\n}\n")]
assert "IP_DONTFRAGMENT" in windows and "DWORD value = FALSE;" in windows
setup = p2p[p2p.index("p2p.tunnel_socket = open_socket(SOCK_DGRAM, 0,"):]
assert setup.index("posix_socket_allow_fragments(p2p.tunnel_socket);") < setup.index("stun_setup();")

send = p2p[p2p.index("static void peer_send_to(struct peer *peer,"):]
send = send[:send.index("\n}\n")]
assert "if (!said && error != WSAEWOULDBLOCK)" in send and "could not be sent (error %d)" in send

update = p2p[p2p.index("static void stream_update(struct stream *stream)"):]
update = update[:update.index("\n}\n")]
assert "if (!stream->stall_time || stream->stall_una != stream->kcp->snd_una)" in update
assert "!elapsed(peer->heard_time, STREAM_STALL_TIME))" in update  # the peer still answers
assert "large packets may be lost on this network (a VPN?)" in update
assert constant("STREAM_STALL_TIME") == 3000
# the protocol untouched
assert re.search(r"\b29\b", read("port/linux/src/port_config.c"))
print("PASS: Test72 tunnel: stream pieces %d bytes on the wire (under a VPN's 1280), datagrams may fragment, "
      "stalls and refused sends said; network 29 unchanged" % on_wire)
