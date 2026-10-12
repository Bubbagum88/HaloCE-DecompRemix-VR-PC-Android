# Test48 Quest and Android device checklist

Test48 is a private regression candidate. Do not publish it until the owner
accepts the test result.

## Priority: physical weapon release and holsters

Use the same profile and controller bindings as the Test47 report. Enable
physical weapons and holsters. Verify the selected holster locations and
holster haptics settings.

1. Grip a weapon, move clear of every holster, then release Grip. The weapon
   should leave the hand and the game should drop it exactly once.
2. Pick it up again, release while inside a configured holster, then confirm
   the hand empties and the weapon is stowed instead of dropped.
3. Grip at that holster. Confirm the stored weapon is selected and returns to
   the hand. Repeat for each enabled shoulder/hip position and handedness.
4. Carry both weapons, assign each to separate holsters, then draw each exact
   stored weapon. Check that slot pruning does not erase a weapon still in the
   inventory and removes it after the weapon is truly dropped or removed.
5. Repeat while a world/NPC interaction temporarily owns the hand. Verify a
   deferred release resolves once after ownership clears, while re-gripping,
   tracking loss, focus loss, recentering, or a weapon switch cancels it.
6. Confirm the initial weapon still stays supported until its first deliberate
   grip and two-handed transfer still gives the weapon to the other gripped
   hand without dropping it.

The supplied log's valid handle values are `-431815724` and `-431750187`.
Confirm Test48 no longer leaves the weapon in the same fixed state. Save the
new `halo_log_*.txt` from Downloads if any step fails.

## Surface-contact haptics

Set the global **HAPTICS** option above zero. Test both controllers against a
wall, floor/solid scenery, a movable object, a held weapon, and a live NPC or
ally. Repeat with the weapon hand, off hand, two-handed grip, and while a
reload/native hand animation is playing; also test with the arm display hidden
or animated. Palm pressure should produce a sustained buzz that follows the
press and stops after release; deeper pressure and finger contact should be
clearer. Turning **HAPTICS** to zero should mute these
contact pulses together with the other controller vibration. In the log,
check for `[openxr] haptic output action ready` and
`[openxr] controller haptic output accepted by runtime`; report any
`xrApplyHapticFeedback failed` lines or a missing action-ready marker.

## Regression checks carried from Test47

- Verify arms do not stretch, fingers still contact surfaces, reload/grenade
  native animation handoff remains smooth, and scopes remain aligned with one
  and two hands.
- Confirm surface-contact haptics on both hands and the OpenXR output log
  markers above; source tests cannot establish physical controller vibration.
- Verify manual reload only begins after actual palm contact and its mapped
  input; it remains solo-only.
- Verify the local solo multiplayer-map spawn and body-retention behavior.
- Verify Safe Geometry remains the default in both APKs; confirm the Android
  touch layout, XInput controls, launcher game-data management and network
  selector still work.
- Verify multiplayer join/co-op and voice chat are unaffected. The network
  protocol remains network24; do not infer universal server compatibility.

## Capture with any report

Include headset model, Quest OS, APK version, left/right handedness, physical
weapon/holster settings, selected game image/revision, mode (solo/PvP/co-op),
and a log captured immediately after the failed action.
