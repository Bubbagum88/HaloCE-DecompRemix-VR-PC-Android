# Test44 device acceptance checklist

Install each APK over its previous installation without uninstalling or
clearing app data.

## Contact-driven VR interactions

- [ ] Solo VR, NPC GRAB on: touch an eligible enemy and press Grip. Confirm it only acquires on collision overlap, does not depend on aim direction, and misses when Grip is pressed without contact.
- [ ] WORLD GRAB on: press Grip while the hand volume physically overlaps a weapon/equipment/prop collision model; pointing at a nearby untouched object must not select it.
- [ ] PARKOUR CLIMB on: touch a solid vertical wall with a free hand, then squeeze Grip to latch and pull. Touch alone must not latch; Grip away from a wall must miss.
- [ ] Repeat while looking away to confirm contact interactions do not require aiming.
- [ ] Two-headset co-op host/client: touch an eligible enemy with the client's
      hand and press Grip. Confirm the host accepts only hand-volume/collision-
      model overlap plus a fresh Grip edge; pressing before contact must not
      acquire it. Release and repeat while looking away.
- [ ] Two-headset co-op world item: repeat touch-then-Grip with an eligible
      object. Pointing at it from outside contact must not select it. Confirm
      release, tracking loss or stale network input cancels the hold safely.
- [ ] Manual reload: touch the magazine/pouch with the free hand before the
      selected Grip/Trigger press; insertion commits only when magazine bounds
      touch the socket within the documented seating tolerance.

## Android and Quest game-data explanation

- [ ] First-run text says only supported maps are copied and directs users to
      Android Files to delete the source ISO/XISO.
- [ ] Main launcher repeats that picker-selected images are not retained or
      deleted by the app, and distinguishes deletable inbox copies.
- [ ] In **Game files & versions**, verify the disabled **Currently selected:
      Existing game data** row is clearly explained as protected status when it
      is the only set. Confirm imports, selection and all prior safe-delete
      behavior remain intact.
- [ ] Select an image from Downloads, complete import, and confirm the source
      still exists in Downloads. Delete it manually in Android Files if desired.
- [ ] Copy an image into the inbox and verify only that copy can be removed by
      the manager after confirmation.

## A10 tutorial calibration

- [ ] Start the first Halo CE mission and reach its look-at-light calibration.
- [ ] With hand aiming selected, keep the headset still and point the actual
      reticle at each target. Confirm the corresponding check responds.
- [ ] Keep the reticle off a target while turning the head toward it; verify a
      fresh hand reticle remains authoritative during this calibration.
- [ ] Confirm reticle movement does not cause a false directional event when
      entering the calibration or when recentering.
- [ ] Briefly point away while the reticle ray is unavailable/stale and confirm
      head motion alone does not complete a hand-aim calibration check; confirm
      progress resumes once the rendered reticle ray is valid again.
- [ ] Switch to head-aim mode and confirm the existing head-based behavior is
      available. Complete calibration and verify normal gameplay/aiming.
- [ ] Enter another mission and confirm script look checks retain their prior
      behavior.

## Regression smoke checks

- [ ] Flat Android launches with its original touch UI and gamepad options.
- [ ] Quest launches immersive with Safe Geometry and the accepted VR settings.
- [ ] Existing saves, settings, network browser and co-op remain available.
- [ ] Logs show no new VR startup, script, or game-data errors.
