# Test45 device acceptance checklist

Install the Quest and Android APKs over their existing installations without
uninstalling or clearing data. The Test45 source pass did not include a device
session, so use the cases below before treating the candidate as accepted.

## Quest VR: contact before Grip

- [ ] In a solo campaign, enable NPC GRAB. With Grip already held, move the
      hand onto a supported NPC. It must not acquire until Grip is released and
      pressed again while the tracked palm collider overlaps the body.
- [ ] Touch a Grunt, Jackal, Elite, Hunter and a dead body, then press Grip.
      Confirm acquisition occurs on contact, including while looking away.
- [ ] Repeat with a living Marine and crew ally. Confirm ordinary AI movement
      pauses while held and resumes after Grip release; team and orders remain
      intact. A forced immediate scripted order should remain ineligible.
- [ ] Press Grip without touching a target and point at one with the aim ray.
      Confirm no acquisition occurs. Then touch it, release Grip, and press
      again; confirm the contact-then-press sequence works.
- [ ] Hold a grabbed NPC while moving the hand quickly, turning the body,
      allowing the NPC to ragdoll, and moving the hand farther than 65 cm from
      the original limb. It must remain held while Grip stays down.
- [ ] Release Grip deliberately. Confirm throw/release occurs once, the body
      remains visible under normal game cleanup, and the log gives a reason.
- [ ] Repeat a touch-then-Grip prop grab and a two-hand grab. Verify held
      objects do not drop from a tracking sample jump or solver strain.
- [ ] Touch solid wall geometry before squeezing Grip to climb. Confirm a
      press made away from geometry does not latch.
- [ ] Confirm world contact and held weapons/fingers remain stable; no hand
      mesh snap, collision pass-through or weapon aiming change appears.

## Negotiated co-op

- [ ] With compatible Test45 peers and host permission enabled, perform a
      touch-then-Grip grab on an enemy, ally and object. The host must reject
      input sent without actual palm/model overlap.
- [ ] Keep the held interaction active while turning/moving and verify it
      remains until Grip release or a logged safety cancellation.
- [ ] Check tracking loss, disconnect and host teardown cancel safely with a
      clear log reason. Confirm ordinary PvP/co-op controls remain unchanged.

## Quest VR: whole-vehicle lifting

- [ ] In solo play, enable **LIFT VEHICLES** and contact an eligible parked
      Warthog, Ghost, Scorpion and turret before squeezing Grip. Move each held
      vehicle up/down and side-to-side; confirm it follows smoothly without
      snapping or teleporting and collides with the world.
- [ ] Use one hand to turn the vehicle by changing controller orientation, then
      grip with the second hand and move the hands apart/together and around one
      another. Confirm the vehicle rotates in response without a sudden spin.
- [ ] Release Grip while the vehicle is moving. Confirm the hand detaches, the
      vehicle continues under native gravity/collision, and its speed remains
      controlled. Repeat after a large controller tracking discontinuity.
- [ ] Confirm a destroyed vehicle, a vehicle with any filled seat, a parented
      or named/movie-star vehicle, and a network-session vehicle cannot be
      acquired or changed by the feature. Confirm boats and aircraft stay stock.
- [ ] Confirm vehicle lifting still works with WORLD GRAB disabled, since it
      has its own toggle. Test both hands and the global HAPTICS setting.

## Regression smoke checks

- [ ] In **Server Setup > Teamplay Options**, confirm voice routing, lobby
      voice, quality and proximity rows are visible and their arrows/pointer
      inputs change the displayed values. This checks menu presentation only;
      voice transmission/playback needs separate validation.
- [ ] On first launch, confirm voice transmission is Off and the app does not
      request microphone permission at startup. In VR, confirm PTT defaults to
      None and does not take over an existing button.
- [ ] With two voice-capable clients, enable lobby voice and test PTT and Open
      Mic both before a match and in-game. Confirm permission is requested when
      capture first opens, releasing PTT stops transmission, volume 0 mutes all
      incoming voice, and host route/proximity choices take effect.
- [ ] Deny microphone permission, confirm gameplay and incoming audio remain
      usable, then grant permission in Android settings, cycle voice Off and
      back on, and confirm capture retries. On flat Android, verify keyboard V
      works and note that touchscreen/gamepad PTT is not provided.
- [ ] Android boots with its existing touch layout and controller options.
- [ ] Quest enters VR with Safe Geometry enabled by default and the existing
      VR settings preserved.
- [ ] Saves, ISO/XISO selection, launcher network selector, in-game server
      browser, campaign co-op, reload, scopes, vehicles, menus and haptics remain
      available.
- [ ] Review logs for `acquisition=authored-contact-plus-fresh-grip`,
      `hold constraint started`, `hold strain`, `hand sample rebased`, and a
      final `release` or `cancel` reason for each attempted NPC interaction.
