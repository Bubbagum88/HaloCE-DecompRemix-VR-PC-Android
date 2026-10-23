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

## Test73: one co-op VR toggle for every player

The owner's request: one host setting that lets the host and every player use
the VR mechanics (fists, physical grenades, manual reload, parkour and slides).
`net.physical_interactions` (Server Setup > CO-OP OPTIONS > VR INTERACTIONS)
is that setting now, **on by default** (the owner); a config saved before
Test73 is switched on once (`config_vr_interactions_default`, from
`game_initialize`, flag `net.vr_interactions_applied`), and stays off if the
host turns it off afterwards. `net.host_vr_actions` (HOST VR ACTIONS) is no
longer read, and its row is gone. The extension's version stays 1: older peers
drop kinds they do not know, so a mixed session keeps the buttons for these.
OpenCE's native protocol is unchanged; the network version is OpenCE's (34
since its fix-scenery-shields-network branch; 33 was ALLY FRIENDLY FIRE).

- **Negotiation.** After each acknowledgement the host sends `NI_FEATURES`
  (kind 10): what VR INTERACTIONS allows (all of `NETWORK_VR_RELOAD`,
  `_GRENADES`, `_MOVEMENT` and `_MELEE`; none while it is off or any client
  has not negotiated). After each offer a client sends `NI_CLIENT_FEATURES`
  (kind 11): what its player uses (melee always; reload, grenades and movement
  as its settings have them; a flat build none). Each is taken only with the
  current nonce (on the host, while the machine still has the player it
  negotiated for). A client's allowance follows the host's confirmation and
  lease: none before FEATURES, after the lease or after a new host's offer.
- **Actions.** A client's manual reload, physical grenade and fist blows reach
  the host as `NI_ACTION` (kind 12, in a hand message's wire), three copies of
  one sequence.
  The host takes a sequence once, from the machine that has that player, for
  its living, unseated unit, and only a kind the client said it uses. A reload
  is committed on the weapon the unit holds when it is the weapon tag the
  client reloaded (`weapon_vr_reload_commit`, as the local reload), at most
  every 500 ms; a grenade within 1.2 m of the unit's eyes, at most 15 m/s, of
  a known type, at most every 250 ms (`unit_vr_throw_player_grenade`, as a
  local throw: count, state and collision checked there).
- **Host side.** The host's copy of a hand-reloading client's weapon is not
  reloaded on its own when empty (`network_interaction_unit_manual_reload`).
  The on-foot bound gives a player that uses VR movement or fist combat at
  least 12 m/s and no rise ceiling (`distributed_on_foot_bound`), so climbs,
  wall runs, slides and fist-combat lunges are not pulled back.
- **Fists** (the owner: "make it so everyone can do advanced fist combat").
  A client runs its own fist combat (punches, FIST COMBAT's assist, lunges,
  combos, counters, takedowns, haptics) and each blow it lands is an
  `NI_ACTION` of kind 3 (`network_interaction_client_strike`, sent from
  `unit_vr_impact_melee_apply` instead of dealing it): the body struck, where,
  along what, its strength, its fist combat's share (combo, ENEMY HEALTH,
  armour; a takedown's x6) and the shove. The host deals it
  (`unit_vr_remote_strike`, every build) when it meets another body within
  2.5 m of the striker's eyes and 0.6 m of the body's sphere, strength at most
  2.5, share at most 6, shove at most 6.5 m/s, at most every 60 ms. A
  client's knockdown is a shove on the host; its stuns are its own (the host's
  AI is not stunned by them); BLOCK and PARRY guard only the host's and local
  players (a client's damage is dealt on the host). Shot deflection stays the
  host's and local games' (projectiles are the host's).
- **Not online:** sprint's speed boost, BULLET TIME, SHAKE COOLING, LIFT
  VEHICLES and CLOSE CONTACT.

`tools/test_test73_network_vr.py` compiles `network_interaction.c` itself (host,
VR client, flat client) and Test72's version (an older host and client), with
23 negative controls (`_scratch/t72/negative_network_vr.sh`). A two-instance run
(a flat host, a PC VR client) is due with the build pass.
