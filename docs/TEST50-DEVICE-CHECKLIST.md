# Test50 device checklist

## Quest VR sprint

1. Confirm existing default behavior: Button Sprint Off has no sprint effect.
2. Enable **Locomotion → Button Sprint** and leave **Sprint Toggle → Hold**.
   Verify sprint begins only while left-stick click is held and ends on release.
3. Select **Sprint Toggle → Toggle**. Verify one click starts sprint, releasing
   the stick leaves it active, and the next click stops it.
4. Confirm both-stick recenter cancels sprint and never leaves it latched.
   Also check focus loss/re-entry, sitting, and normal forward movement.
5. Disable Button Sprint and confirm the previous left-stick binding returns.
   Confirm movement remains unchanged in network play.

## Mounted vehicle and turret reticles

1. In a solo match, fire the Ghost, Scorpion tank, Shade turret, and Warthog
   gunner weapon at a fixed distant surface. Test driver and gunner seats where
   each vehicle supports them.
2. Confirm the shot center follows the selected reticle ray with **Right Hand**,
   **Left Hand**, **Head**, and **Stick** aim modes. Repeat in third-person and
   first-person vehicle view if both are available.
3. Use several shots per weapon: random spread can move individual rounds, but
   the center direction should align with the reticle. Check logs for mounted
   role/seat, aim path, and reticle-to-shot angle.
4. Confirm ordinary handheld weapon aim assist still behaves as before and
   that passengers/remote players retain their native aim-assist path.

## Voice chat

1. Use two clients running a voice-capable build. Set the host's Server Setup
   lobby voice on and an in-game route that includes the two players.
2. Set the listener's receive volume above zero. Confirm it can hear the
   speaker with its own microphone mode Off, then test Push to Talk and Open
   Mic separately on the speaking client.
3. Repeat in a lobby and in a match. Check Android/Quest microphone permission
   and the configured PTT control as appropriate.
4. Save both client logs. Check for host configuration, a local encoded frame
   on the speaker, an accepted/relayed frame on the host, and an incoming frame
   decoded on the listener. Confirm the listener's receive volume and routing
   gain are nonzero.
5. Repeat with a non-voice-capable/older host only to confirm the diagnostic
   explains the missing voice settings; ordinary multiplayer must remain
   available.

This is an owner-run device checklist; no two-headset result is available from
the source build or the supplied Test49 log.
