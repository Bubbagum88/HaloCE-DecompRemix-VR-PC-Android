# Test49 haptics and weapon-action regression audit

## Findings from the supplied Test48 Quest log

- The log identifies a Quest 3 on Android 14 and build `1.0.29-test48` / code
  `59`. OpenXR reports the haptic output action ready and later reports a
  successful `xrApplyHapticFeedback` call. The vibration action/runtime was
  available; the log does not record individual haptic amplitudes or which
  source requested them.
- The contact diagnostics show zero finger-contact hands in most intervals,
  with one interval reporting contacts. This diagnostic does not track the
  separate palm sampler, so it cannot by itself prove whether an individual
  vibration came from palm contact.
- The source comparison found Test48 newly sampled a head-to-hand collision
  path independently of arm pose ownership, then renewed pressure/finger
  haptics on each render update. That path can report an obstruction along the
  arm while the tracked palm is not pressing the surface. Repeated requests to
  the same OpenXR haptic action can mask short weapon-recoil pulses. Test49
  removes that added feedback path and restores the v1.0.18 direct collision
  and arm-ownership gates.
- `vr_weapon_buzz` and `vr_render_weapon_fired` are byte-for-byte identical to
  their `v1.0.18` implementations. Their per-weapon amplitude/duration table,
  shot de-duplication, local-player filter, and two-hand output are unchanged.
- The log contains repeated `weapons switched at the ... holster` and
  subsequent `holding PLASMA RIFLE` / other weapon entries. It does not contain
  an emitted melee-action record. Source constants distinguish melee (`0x1`)
  from weapon switch (`0x8`); the default inputs are right-stick click and Y,
  respectively. Test49 adds event-level action-mask and swing diagnostics;
  it does not change the controls or animation handoff.

## Changes in Test49

- Restore v1.0.18 contact haptic gating: sustained palm pressure follows the
  actual hand collision while that arm is IK-owned; fingertip feedback remains
  tied to actual finger collision and the same ownership gate.
- Remove the independent head-to-hand haptic sampler that could refresh
  vibration when a hand was not pressing a surface.
- Preserve the v1.0.18 weapon-fire haptic implementation exactly.
- Log physical melee gesture speed and emitted melee/weapon-switch action
  bits. This makes a retest able to show whether a perceived melee animation
  corresponds to a melee input or only the native weapon-switch animation.
- Keep Test48 signed-datum release/drop/holster behavior and all other
  accumulated changes.

## Verification boundary

Host tests compare the firing haptic functions with `v1.0.18`, exercise the
collision feedback wiring and assert the action-bit separation. Quest runtime
acceptance is still required to verify vibration feel and whether the reported
animation appears during an actual weapon switch. The supplied Test48 log
alone does not show an emitted melee action, so no speculative animation or
binding change is included.
