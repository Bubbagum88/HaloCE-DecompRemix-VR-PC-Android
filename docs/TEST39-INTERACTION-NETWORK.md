# Test39 optional interaction networking

This documents only the Test39 delta from TEST38-INTERACTION-NETWORK.md.
OpenCE's native protocol, network version, campaign settings and ordinary
co-op behavior are unchanged.

## World interactions above four remote machines

The host's capability lease now accepts every connected remote machine up to
`HALO_PORT_MAXIMUM_NETWORK_MACHINES` (128), provided the host enabled
`net.physical_interactions` and every current machine/player identity has a
fresh matching lease. This is a capacity bound in the existing transport data
model, not tested evidence for a 128-player campaign or stable 128-peer VR
physics session.

Hand samples are limited to 20 Hz while pressed and 4 Hz for released-state
refresh. They still carry only controller intent; host code validates player,
unit, range, transform, ownership, epoch, sequence and lease. Host results are
sent only for a new input sequence or an ownership change, not every game tick.
Native world-object replication remains the object transform authority.

At more than four remote machines, the host still enables the bounded world
object path when all peers negotiate, while it disables NPC interaction and
articulated joint-palette synchronization. The client receives that NPC budget
in a separate additive `NI_NPC_CONFIRM` capability message. The existing
`NI_CONFIRM` message retains its Test38 protocol-v1 boolean sequence, so older
clients can still negotiate world interactions and ignore the extra NPC
budget message. Protocol version and OpenCE network version are not changed.

This is safer than advertising NPC palettes at an unbounded peer count: pose
updates multiply node count by peer count. Native co-op remains available if
the optional extension does not negotiate or its lease expires. This source
behavior still requires Quest/Android mixed-host tests and traffic measurement;
it does not certify performance or game behavior at 128 peers.

## Host sanitizer coverage

`test_test38_network_interaction.py` executes the production decoder/host tick
with a 128-machine fixture. It verifies all-peer negotiation, the preserved
boolean confirmation, additive NPC confirmation, world authority with five
and 128 remote machines, NPC rejection above four, restoration at four,
expired/missing lease denial, spoof/range/epoch/sequence rejection and joint
pose validation. `test_test38_network_input.py` verifies client pacing and
transition/cancel behavior. These deterministic tests are not live network
acceptance.
