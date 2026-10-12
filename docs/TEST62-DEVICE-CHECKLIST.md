# Test62 device checks

Install both APKs as updates; do not uninstall first. Keep the prior APKs.
The build/test tools do not install or launch them for you. These checks are
still pending, even if the automated suite and packaging checks pass.

## 1. Baseline and settings

- Check Test62 / 1.0.29-test62 in the generated log. Confirm profiles, saves,
  imported data and selected revision remain present.
- With new options OFF, check normal aiming/reticles, native reload/throw,
  firing haptics, two-hand grip, holsters, grip-release drop and menu navigation.
- Confirm master HAPTICS 0 stops feedback, restored intensity resumes it,
  and HOLSTER HAPTICS alone still controls its existing exception.
- Check the familiar flat touch/controller layout, pause/resume, controller
  reconnect and normal menu navigation. No new VR gesture should affect it.

## 2. Immersive vehicles

- Enable IMMERSIVE VEHICLE; confirm it brings FIRST PERSON. Enter/re-enter
  Warthog, Ghost, Scorpion and Banshee. Controls wait up to three seconds
  while boarding, then stay reachable through bumps and turns.
- Check drawn/hidden wheel, COMFORT REACH, all three CTRL offsets and each
  vehicle's own offsets, while ungripped. Verify saved settings after restart.
- Recheck third-person right-hand control, turret/scope reticles, seat changes,
  exit/recenter and controller tracking loss. Turning the immersive option
  OFF should restore the usual driving path.

## 3. NPC grabs, slams and ragdolls

- Set GRAB ASSIST to 5 CM if TOUCH was preserved. Grab allies, Grunts, living
  Elites/Hunters and corpses from either hand. Confirm actual body contact,
  not acquisition through a wall or across a room.
- First hand restrains a living heavy actor; a second distinct contact lifts.
  Release one/both hands, kill it while first-hand-held, then lift the corpse.
  Check native world collision and living AI recovery within one second.
  Catch an NPC during a melee wind-up/contact attack and verify it cannot
  continue hurting you while restrained; after release normal attacks resume.
- Enable IMPACT DAMAGE. At the same IMPACT SPEED, compare deliberate floor,
  wall and body-to-body slams with slow contact and glancing movement. Repeat
  on multiple campaign maps, species and shield states. Verify real shield
  depletion/break and native damage/material effects instead of a flash on
  every contact. Check shield-only hits, actual shield depletion, unshielded
  flesh and missing optional art. Keep matching VR impact/VR contact damage
  log lines with before/after shield/body vitality.
- Enable DEATH RAGDOLLS. Test burst/explosion deaths nearby and around 50 m,
  compare 40/60 m range and a busy 24-slot scene. Watch for jitter, stretched
  bones, stuck live NPCs and frame loss. Checkpoint/load afterward.

## 4. Manual reload and hand ownership

- Eject and reseat the original magazine; then pouch replacement, tactical
  reload, empty-weapon charge and cancel/recover. Feel insert/rack/ready
  clicks in each hand and with nondefault HAND ANGLE, including while the
  hand touches a wall so contact feedback cannot hide the reload pulse.
- Test shoulder and hip pouches alongside holsters, NPC contact and walls.
  A hand already holding something must not also acquire a magazine/grenade.
- Recheck armed physical melee, native animation handoff, ammo counts and
  weapon switching. Verify no new persistent idle/contact vibration.

## 5. Parkour and assisted fist combat

- Set CLIMB GRAB to 14 CM and WALL TIME to 2 S if older choices remain.
  Check climb contact, a hand slightly versus deeply behind a wall,
  release/launch, automatic wallrun, wall jump, corners,
  low ceilings and missing tracking. Check collision and escape controls.
- Enable FIST COMBAT: verify required FIST REQUIRED/impact MELEE and suggested
  NPC GRAB/CLOSE CONTACT. Start with MELEE SPEED OFF and confirm
  enabling combat sets a positive threshold, while a saved positive threshold
  stays unchanged. Set MELEE SPEED OFF afterward and confirm FIST COMBAT
  visibly turns off and its lock releases. Open hands must not acquire combat
  targets, including when assistance is enabled through config rather than the menu.
  Switch MELEE to SWING and confirm FIST COMBAT visibly turns off.
  A direct-config SWING/assist combination must not emit assisted impacts.
- Look and punch toward an enemy at each FIST REACH; compare an ally/player,
  a second enemy, an occluded target and targets on another elevation.
- Verify approach stops outside the enemy and respects walls. Backward input,
  strafe, jumping, climbing and looking away must allow disengaging. Repeated
  punches keep one target; inactivity releases it.
- Verify cyan head/chest highlights, amber brief stun, hit flash and subtle
  hit/stun reaction. Stun an enemy during a melee wind-up and continuous/
  contact attack: damage must pause only during the stun. Check a rear hit
  during stun, then grabbing/slamming.
  Observe native hurt sounds and protected campaign actors. Check Hunters,
  Flood and other skeletons for bent joints or hidden/misplaced highlights.
- Turn the feature off and verify normal movement, AI, melee and settings.
  Report any involuntary movement or discomfort rather than accepting it.

## 6. Physical chest grenades

- Enable PHYS GRENADES; adjust CHEST FWD/DOWN/SPACING in multiple body modes.
  Frag should be left, plasma right; unavailable ammo should hide that slot.
- Check that a held grenade stays in the visible palm while the hand touches
  a wall or native animation blends. Repeat with hands hidden/unsupported:
  its fallback should not draw through a wall or retain a stale pose.
- Touch/Grip with an empty hand, then release to throw. Test overarm, underarm,
  slow drop and throwing while moving. Try THROW POWER 0.5X/1X/2X and each hand.
  Feel pickup/release pulses near a contacting wall, separately on each hand;
  master HAPTICS 0 must still silence them.
- Verify native fuse/explosion/sticking, intended direction and count changes.
  Compare normal grenade buttons with no held chest grenade; buttons must not
  spend another grenade while one is held or on the same tick it is released.
- Hold a grenade, then pause, die, load a checkpoint, lose tracking or turn the
  feature off. Also recenter or invalidate hand ownership. Cancelling must
  not lose ammo or spawn a surprise grenade; picking up again needs a fresh
  Grip press. Test near a wall and with one grenade/reservations in two hands.
  Change/exit the map while holding one or locked onto an enemy; neither state
  should carry into the next map or menu.

## 7. Scope and shared aim

- Compare AIM STEADY OFF with LIGHT/MEDIUM/STRONG/MAX. OFF retains the older
  scope behavior; higher levels should filter angular micro-movement without
  separating the gun/reticle/projectile direction.
- Scope each supported gun/profile one-handed and two-handed, both handedness
  choices, roomscale motion, hand angle, gun offsets and close-wall pullback.
  Include zero gun-offset/anchor movement. Recenter and pause/resume.
  Check both eyes for drift, delayed catch-up, clipping and comfort. Preserve
  per-gun settings unless adjusting deliberately.

## 8. Co-op and multiplayer

- Run normal PvP, normal co-op and existing voice as regression checks.
- In co-op Server Setup test HOST VR ACTIONS OFF, ON without VR INTERACTIONS,
  then ON with VR INTERACTIONS and negotiated compatible peers. The host's
  fist/chest features should activate only in the permitted case.
- Verify remote clients retain native controls, a mixed/older client disables
  the gated actions, and losing readiness cancels held actions cleanly.
- With a fully negotiated ready client, grab an NPC and verify grip requests
  reach the server and replicated poses appear on the client. The client must
  not independently restrain, simulate or damage the NPC; check release and
  loss of permission as well. Readiness alone is not physics authority.
- Compare host/client enemy health, grenade counts/projectiles and AI recovery.
  NPC pose sync retains the existing four-remote-machine budget; check the
  expected fallback beyond it without treating that as normal co-op capacity.

For a failure send the generated log plus a short clip, device/Quest OS,
game image/map, host/client role, connected peers and relevant settings.
These private candidates are not an accepted release until device results
confirm them.
