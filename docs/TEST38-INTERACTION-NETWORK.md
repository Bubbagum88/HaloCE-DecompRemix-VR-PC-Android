# Optional campaign interaction networking

## Authority and compatibility

Server Setup adds **VR INTERACTIONS: OFF / ON**, saved as
`net.physical_interactions` (default OFF). This is host permission, not an APK
name check. Every connected machine must negotiate interaction protocol version
1 before enhanced campaign interactions are permitted. A joining old/stock peer,
an expired capability, disabled host permission or PvP immediately prevents new
authoritative interactions. The native co-op session remains available.

The extension uses the existing project-reserved distributed envelopes 37/38
with a distinct magic (`0x56494e31`) and version. Existing avatar messages keep
their original structs and magic. Older avatar decoders reject this new magic;
no native OpenCE network24 packet layout or version check changes. The host
issues nonzero per-peer nonce challenges. Offer, acknowledgement and confirmation
carry game round and random seed; leases last six seconds. Client requests are
not accepted before negotiation. Flat and VR builds share the same decoder and
host authority; local controller sampling is isolated in `vr_interaction_client.c`.

## Hand intent and host decisions

Clients may send world-space hand position/orientation, held state and enabled
interaction families. They never supply NPC palettes, object velocity or damage.
The host verifies machine/player ownership, current salted player unit, alive and
unseated state, finite transforms, a bounded two-metre reach in native world
scale, message sequence, nonce, round and seed. Native interaction modules then
perform stricter proximity, line-of-sight, object/species and ownership checks.

Host-computed grip edges prevent repeated held packets from reacquiring a
rejected/cancelled object. An explicit cancellation on lost focus/tracking/eligibility, or loss of updates
for 300 ms, cancels without inventing a throw. Reacquisition requires an observed release and new press. World and NPC
claims are exclusive per hand. The host returns the accepted family and constrained surface contact in object-local
coordinates. Both ends use the actual object world transform, not authored node 0.
The client
claims the matching local interaction owner only while its physical grip remains
valid. Native object transforms, health/damage and AI decisions remain host-owned.

NPC snapshots and client palettes are bounded to a four-body pool;
this channel does not imply unlimited simultaneous ragdolls. Mixed-client fallback
is deliberate: an unmodified client cannot display the custom articulated state,
so the session does not silently enable that state for upgraded players alone.

## NPC presentation

Only the host sends NPC joint snapshots. Clients reject player units, invalid
object indices, wrong node counts, excessive scale/position, invalid axes and
out-of-order or partial snapshots. A complete snapshot contains at most 64 nodes.
Clients interpolate host palettes after native node recomputation, before
child attachment/collider use, so visible limbs and local collision queries agree.
This updates presentation/collision node matrices, not authoritative root physics,
AI or damage decisions. Each native recomputation restores stock when the lease
expires. Normal native root replication remains authoritative.
Stale palettes blend back to stock. Pose traffic is capped at 15 Hz and paced
against an approximate aggregate 256 KiB/s budget; large peer counts reduce pose
frequency. The announced bounded cadence controls interpolation/staleness, so
reduced frequency is not mistaken for a lost connection. Native co-op already replicates scenery/machine transforms; movable scenery
uses that path, avoiding a second competing transform stream. Ordinary item
replication is also unchanged. This needs actual
network/performance testing, particularly with many clients.

## Validation and remaining device checks

`test_test38_network_interaction.py` executes the production decoder and host
tick under ASan/UBSan with counted authority callbacks. Coverage includes
challenge negotiation, all-peer gating, sender spoofing, nonce/epoch mismatch,
nonfinite/out-of-range poses, sequence replay, lease expiry, cancelled held grips,
pending grip edges across packet batches, partial/invalid joint assembly and
stale visual fallback. It also checks appended host menu labels do not renumber
PASSWORD, and the common network module has no VR-only authority branch.

`test_test38_network_input.py` additionally replays actual controller adapter
cancellation, stale result rejection, fresh-grip recovery, and scaled/rotated
object contact transforms.

Both VR and flat guest compilation pass with implicit function declarations
promoted to errors. The actual menu parser and existing OpenCE message-number
regression tests pass. These results do not establish live cross-play acceptance.
Test Quest host/Quest client, Quest host/Android client, Android host/Quest client,
late joining, disconnect while held, loss/reorder, checkpoint/map transition and
mixed stock OpenCE peers. Confirm host-approved throws/damage and remote recovery
match, with no phantom ownership or unintended state retained after fallback.

Manual reload and parkour keep their separately documented authority limits;
this NPC/world capability must not be read as permission to bypass native ammo
or movement validation on unmodified hosts.

Enhanced physical ownership permits at most four remote peers. Larger sessions
retain native co-op and disable optional interactions to avoid pose starvation
under the traffic budget. Ordinary campaign player limits are unchanged.
