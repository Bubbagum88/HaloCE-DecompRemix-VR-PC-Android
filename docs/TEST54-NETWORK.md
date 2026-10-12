# Test54: VR immersion features online

The owner asked that VR immersion features be shared between same-build VR
players, without breaking OpenCE compatibility, Android players or
host authority, and without forcing risky networking. This is what Test54
does, what already existed, and what remains.

## What is shared today

The existing optional extension (`port/linux/game/network_interaction.c`,
since Test38) is used unchanged; Test54 adds no packets and does not change
the network version.

| Area | How it works online | Who sees it |
|---|---|---|
| Capability / version negotiation | Host offers (`NI_OFFER`, nonce, game seed, round) every 2 s; a compatible client acknowledges; the host confirms world (`NI_CONFIRM`) and NPC (`NI_NPC_CONFIRM`) readiness. Distinct magic/version inside the reserved avatar envelopes, which stock decoders discard. | Only peers that answer take part. Stock OpenCE and Android clients ignore it. |
| Host feature policy | `net.physical_interactions` on the host (consent). The host must be in co-op and every connected client must have acknowledged; NPC pose sync also needs at most four remote machines. | Advertised to clients by the confirmations; a client's features follow the host's answer. |
| Grabbing world objects | Client sends hand intent at 20 Hz (`NI_HAND`: position, orientation, grip); the host repeats the touch test, owns the object, simulates it and sends the result (`NI_RESULT`); native object sync moves the object for everyone. | Everyone, including Android and stock clients (native object state). |
| Grabbing NPCs and bodies | Same intent path; the host runs the articulated rig and streams the rig's joint poses (`NI_JOINT`, up to 15 Hz, capped near 256 KiB/s) to compatible clients. The native root moves through normal sync. | Compatible VR clients see the limbs. Others see the native body moved by its root. |
| Throws | Released on the host from its samples of the client's hand intent, with the host's THROW STRENGTH (a remote holder's hold strength is fixed at SPARTAN). | Everyone (native velocity). |
| Death ragdolls (Test54) | On a co-op host they are rigs in the same pool, so their poses go out on the existing `NI_JOINT` stream. A client never simulates one. | Compatible clients see the ragdoll; others see native death and the body where the root lands (the root follows the body: Test54). |
| Physical melee | `vr.melee_multiplayer` ("+ ONLINE"): impact melee uses native melee damage requests, which the host validates. | Everyone. |
| Authority / ownership | One owner per hand per object; a request is ignored while another player holds it; the host cancels on lease timeout (300 ms of missing intent), owner change or player death. No snapping between owners: the host's result is what all clients show. | |

## What remains (deliberately not forced)

- **Parkour as a client** (wall run, wall jump, grip climb). The OpenCE host
  validates client movement (no hovering, slow falls or rises past a jump)
  and would pull the player back. A safe version needs a host-side
  allowance for negotiated clients' parkour states, plus anti-cheat limits
  for PvP. It stays solo and co-op-host only.
- **Manual reload as a client.** Ammo is host-authoritative; a client-side
  commit would desync. A network-safe version would end the physical gesture
  with the native reload request (so the host does the ammo), but the native
  reload animation would then replay. Left solo-only rather than ship that.
- **Client-simulated ragdolls on stock hosts** are impossible to share (a stock
  host has no rig). Clients of stock servers keep native deaths.
- **More than four remote peers**: NPC pose streaming is disabled above four by
  bandwidth policy; world-object grabs still work.
- **A client's own THROW STRENGTH / NPC HOLD / NPC GRAB ASSIST** are not sent
  to the host; the host's settings apply to every holder in its game. Sending
  them needs a new field in `NI_HAND` (a protocol version bump).

Online behaviour still needs device testing with two VR headsets and a phone;
see [TEST54-DEVICE-CHECKLIST.md](TEST54-DEVICE-CHECKLIST.md).
