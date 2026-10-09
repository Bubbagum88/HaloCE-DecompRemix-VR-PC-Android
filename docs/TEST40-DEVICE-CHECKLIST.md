# Test40 device acceptance checklist

Status: **not yet run**. Automated tests and a successful build are not device
acceptance. Record device, OS/runtime, ISO revision, APK hash, settings, map and
log for every result. Keep all new options OFF for the baseline checks first.

## Baseline regression checks

- [ ] Flat Android starts, touch controls remain visible/usable, gamepad input works.
- [ ] Quest enters VR with Safe geometry and the existing VR settings/menu.
- [ ] Campaign save/continue, map transition, scope, reload, body/hand tracking,
      vehicles, server browser and campaign co-op still behave as in the tested baseline.
- [ ] Confirm all four new settings default OFF after install and preserve a
      user's existing config on update.

## New features

- [ ] With manual reload enabled, eject a supported rifle magazine and verify
      it falls, collides with the world, stays still on the floor, renders with
      world depth/occlusion in both eyes, and does not change ammo accounting.
- [ ] Repeat with supported pistol and sniper profiles, both weapon hands.
- [ ] Fill the 32-item pool; confirm the oldest visual is recycled and frame
      time remains acceptable. Confirm a map/checkpoint reload clears debris.
- [ ] With WORLD GRAB plus LIFT VEHICLES, lift an unoccupied Warthog, Ghost,
      Scorpion and turret. Confirm vertical response is bounded and native
      gravity/collision work; release and verify no fling, stuck velocity or
      rotation. Confirm named, occupied, unsupported and online vehicles stay
      native. Test grab and sustained lift feedback with WEIGHT HAPTICS OFF
      and ON; confirm the acquisition pulse remains and the opt-in load pulse
      is comfortable, capped and present on both controller hands.
- [ ] Enable CUSTOM NPC RIGS in a solo map containing a known compatible
      unclassified humanoid graph. Verify arm/hand selection and release. Try
      an invalid/non-humanoid graph and verify it is refused without crash.
- [ ] Enable NPC RESCUE; verify no action during ordinary jumps, AI movement,
      scripted orders, combat, cutscenes, vehicle occupancy or multiplayer.
- [ ] Strand an eligible encounter NPC unsupported for less than ten seconds
      and then land it; confirm the timer resets. Leave one falling for more
      than ten seconds; confirm it returns only to a clear previous grounded
      capsule and resumes its existing AI/mission state.
- [ ] Verify rescue on map transition, checkpoint save/load, actor deletion,
      and invalid/blocked recovery positions without stale IDs or repeated
      teleport loops.
- [ ] Hold an eligible NPC with each hand and both hands. Confirm the grab
      pulse and opt-in bounded load feedback feel natural; remote-owned NPCs
      must not vibrate the local controllers.
- [ ] Press fingers/palm against safe world surfaces and a held weapon. Confirm
      the existing contact haptics pulse on contact without buzzing every frame;
      verify the global HAPTICS strength slider still scales it, and reload,
      parkour and ordinary grab event pulses still fire.

## Acceptance record

Owner results and logs: pending. Do not change `runtime_accepted` or the
accepted public pointer until the exact APK pair has explicit owner acceptance.
