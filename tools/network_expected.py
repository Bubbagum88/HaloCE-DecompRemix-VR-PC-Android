"""The network versions this build is meant to host and join, recorded on their own: the suites that pin them
(test_test27, test_test59_network28, test_test68_network29 and the others) read them here, so that a change of
port/linux/include/halo_port_limits.h or the launcher's NetworkProfile.java that is not also made here fails
them, and an upstream version bump is one line here (Test73: OpenCE Build 256 and its newer branches, network 34:
the map's scenery shields and tripmines shared (fix-scenery-shields-network); 33 co-op's ALLY FRIENDLY FIRE; 32 the
host's aim assist policy, message 90; 30 the co-op player's own friendly fire
byte, 31 the elevator bound).

Historical facts stay in their suites (network 29's Custom Edition map identity, 23 for Custom Edition maps)."""

CURRENT = 34  # HALO_PORT_NETWORK_VERSION, what this build hosts and advertises
MINIMUM = 11  # HALO_PORT_NETWORK_VERSION_MINIMUM, the oldest host it joins
MAXIMUM = 34  # HALO_PORT_NETWORK_VERSION_MAXIMUM, the newest
UPSTREAM_BUILD = 256  # the newest OpenCE build merged (CURRENT is its newer branches' network)

SUPPORTED = list(range(MAXIMUM, MINIMUM - 1, -1))  # the launcher's choices, newest first (NetworkProfile.SUPPORTED)


def range_text(low=MINIMUM, dash="–"):
    """the join range as the launcher and guides write it: '11–32'"""
    return "%d%s%d" % (low, dash, MAXIMUM)
