# Test52 device checklist

Install over the existing app (do not uninstall). Record pass/fail and keep the
newest log from Download/HaloCE for anything that fails.

## Voice (the Test51/v1.0.19 crash)

1. Join a server whose host has voice enabled. Set Audio → Voice Chat to Push
   to Talk or Open Mic and receive volume above zero.
2. Speak normally, then loudly, for at least 30 seconds in the lobby and in a
   match. The game must not close.
3. Check the log: `voice chat: host configuration received` now shows sane
   values (lobby 0/1, kbps 8–64, proximity in tenths), and the ten-second
   `diagnostic` lines show encoded/received/decoded frame counts that grow.
4. With a second player: confirm they hear you and you hear them.
5. Host a game yourself and repeat 2–4 with a client.

## Retained behavior (quick regression pass)

- Join and host PvP and co-op; server browser; LAN.
- Weapon pickup/drop/holster, reload, melee, sprint (Hold/Toggle), haptics.
- Vehicles: driver and gunner reticle alignment.
- Scoreboard (hold Back/Select): text should now be the intended size.
- Android flat: touch controls, gamepad, multiplayer join.

## Not in this candidate

Parkour, wall grabs, ragdoll/body retention and NPC grabbing are still being
reworked for the next candidate; leave those options off for this test.
