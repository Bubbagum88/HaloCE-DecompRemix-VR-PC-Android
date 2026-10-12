# Test41 device acceptance checklist

Status: **pending owner testing**. A build or host test cannot establish Quest
runtime behavior. Keep the Test40 APK pair and its directory untouched for
comparison. Install Test41 over the existing app; do not clear app data.

## First confirm the session classification

- [ ] Launch directly into a solo saved campaign with no invite pending. In the
      generated log, verify `VR interactions: session=local(0)` while in the map.
- [ ] Repeat while an invite is pending but do not accept/join it. Verify the
      session remains local. If accepted and the network join completes, verify
      the log changes to `network-client` or `network-server`.
- [ ] Quit the network game and load a solo campaign. Verify the log returns to
      `local(0)` and local-only features are no longer suppressed.
- [ ] Confirm settings and session lines are emitted only on state changes,
      rather than every frame.
- [ ] Set the single HAPTICS slider to 0% and confirm shots, contact,
      reload, movement and interaction feedback all stop. Raise it to 50% and
      confirm each effect returns at reduced strength. Then set HOLSTER HAPTICS
      Off: holster entry/draw/stow buzz should stop while weapon switching still
      works. Manual reload pouch detection and reload haptics on the free hand
      must remain independent and still follow the master HAPTICS value.

## Physical grab reach and NPC pool

- [ ] In a solo map, enable WORLD GRAB and set GRAB REACH to 30 cm. Try a
      supported movable item at 12-30 cm, then test each hand and two hands.
      After enabling or resetting a feature, fully release grip and squeeze
      again; grabs require a fresh grip press.
- [ ] Confirm a wall still blocks the reach, unsupported/scripted objects are
      refused, contact/load haptics follow the master HAPTICS strength, and
      release leaves native gravity/collision active.
- [ ] Enable NPC GRAB and test supported Grunt, Elite and Hunter behavior at
      the selected distance. Heavy actors should honor their two-hand minimum;
      unsafe/custom/special graphs should remain refused unless the validated
      CUSTOM NPC RIGS path applies.
- [ ] Exercise more than four eligible NPC interaction states, then verify up
      to the configured slot count works and excess requests fail safely. Watch
      frame time and log for pool capacity. This does not test Halo's native
      corpse-ragdoll cap.

## Existing toggles that were reported as ineffective

- [ ] Manual reload: use a supported profiled gun with rounds in reserve; test
      shoulder and hip pouches, magazine removal/insertion, chamber action where
      applicable, cancel and ammo synchronization. Look for a `VR manual reload`
      `event=` entry; the old log only showed authored bounds.
- [ ] Dropped magazine debris: enable both required options, complete a
      supported magazine ejection, verify visual collision/lifetime and confirm
      native ammo totals are unchanged. Fill the 32-object pool, confirm the
      oldest visual is replaced safely, then change maps and confirm stale
      objects are released without changing reserve ammo.
- [ ] Parkour: test wallrun while sprinting/jumping toward a valid wall, wall
      jump, and two-hand wall climb/release. Look for `VR parkour` events.
- [ ] Vehicle lift: enable LIFT VEHICLES by itself; test only an eligible,
      unoccupied supported vehicle (Warthog, Ghost, Scorpion or turret). Check
      bounded vertical movement, collision, release and haptics. Repeat with
      occupied, parented, scripted and unsupported vehicles; they must remain
      unaffected. WORLD GRAB is not a prerequisite.
- [ ] NPC rescue: enable it in a solo encounter; verify ordinary AI/cutscene
      behavior stays native, then test a live eligible NPC falling unsupported
      for under and over ten seconds. Check the rescue log and AI continuation.
      Verify recovery does not place the NPC into a blocked capsule, and repeat
      across checkpoint load, map transition and actor deletion/reset.
- [ ] Custom NPC rigs: enabling it should also enable NPC GRAB. Test only a
      compatible unknown humanoid graph; verify a malformed/special rig fails
      closed without a crash. Repeat after changing maps so cached graph
      validation does not leak across actors or tag sets.
- [ ] Load feedback: with global HAPTICS above zero, test sustained movement or
      strain while holding supported objects/NPC limbs/vehicle lift. A static
      light hold is not expected to pulse continuously. HAPTICS at 0% must
      suppress it along with every other controller vibration.
- [ ] NPC RIG SLOTS: vary the setting from 1 to 8 and test the same number of
      simultaneously held/settling/recovering physical NPC rigs. This counts
      this mod's interaction rigs; it does not raise Halo's native corpse limit.

For every failure, retain the full new log and include device/headset, Quest OS,
selected ISO/revision, map/checkpoint, exact settings, which hand/buttons were
used, target type/distance, and whether a network invite was merely pending or
the game actually joined. Public v1.0.18 remains the accepted release until the
owner accepts this candidate.
