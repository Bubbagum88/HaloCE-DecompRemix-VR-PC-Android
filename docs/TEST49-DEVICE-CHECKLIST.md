# Test49 device checklist

Test49 is a private candidate; public v1.0.18 remains unchanged.

## Haptics and recoil

1. Set **HAPTICS** to 100%. Walk in open space with hands relaxed and away from
   walls, objects, and holsters. Neither controller should buzz continuously.
2. Fire each gun, including the plasma rifle, pistol, assault rifle, shotgun,
   sniper rifle, and rocket launcher. Confirm recoil strength and duration are
   distinct as in v1.0.18. Test a two-handed weapon and confirm both hands
   receive the recoil.
3. Press each tracked palm into a wall and then touch with fingers only. Palm
   pressure should track the press; finger contact should register while that
   arm is under VR IK. Release and confirm the feedback stops.
4. Repeat near scenery and while walking, then test a hand animation such as
   reload or grenade throw. Surface feedback should not sustain from an
   obstruction that the palm is not pressing.
5. Set **HAPTICS** to zero and verify shots, contact, holsters, reload, and
   interaction feedback are all muted.

## Weapon switch versus melee

1. Switch to and from the plasma rifle using the usual holster/controller
   inputs. Confirm the intended native draw/swap animation and no unintended
   melee action.
2. If a melee animation still appears, preserve the new log. Look for
   `gameplay action mask` and `physical melee gesture emitted`. A switch-only
   mask indicates the native switch animation path; a melee bit or swing line
   identifies an actual melee input/gesture.
3. Confirm right-stick melee and Y weapon switch still work independently.

## Carried-forward regression checks

- Grip release, drop, holster stow/draw and two-hand transfer.
- Reload/grenade handoff, weapon alignment, scope alignment and arm reach.
- Multiplayer join/co-op, voice, Android touch/gamepad and launcher game-data
  management.

Include headset model, Quest OS, handedness, selected body/weapon settings,
game mode, game revision and the complete launch log with any report. APK
installation or headset acceptance has not been performed by this build step.
