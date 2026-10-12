# Test48 regression audit

## Finding

The Test47 log reports live weapon handles `-431815724` and `-431750187`.
These are valid signed datum handles. The engine reserves the exact value
`NONE == -1` for an empty reference; the sign alone does not indicate validity.

Three Test47 paths used a sign test and rejected those valid handles:

- `vr_weapon_release_latch_step` cleared the release edge for every negative
  weapon, so neither release-to-drop nor release-to-holster could fire.
- Holster storage, forgetting, inventory membership, and pruning discarded
  negative weapon handles, so a stowed weapon could not be remembered/retrieved.
- Pending-release recovery treated a negative active weapon as absent and could
  not restore the held state after a native drop/stow request failed.

Test48 changes these checks to compare with the exact empty sentinel. The
`vr_note_weapon` unit validity checks use the same rule. The source's existing
weapon action branch still chooses stow inside a holster, transfer to a gripped
off-hand, or drop elsewhere; no gameplay rules or action bindings changed.

## Audit of adjacent handle paths

Reviewed VR weapon/holster state, vehicle-seat identity, manual reload, NPC
rescue/interaction, world interaction, loose props, and network object paths
for sign-based rejection of datum handles. The inspected paths use `NONE`
equality or exact `-1` equality for datum sentinels. The remaining negative
checks in the scanned VR files validate array slots, collision indices, render
swapchain indices, actor squad indexes, or other bounded integer indexes; they
are not datum-handle validity tests. No additional matching signed-handle bug
was found in that audit.

## Surface-contact haptics regression

The reported missing wall/surface/NPC haptics was reproduced by tracing the
call gates: the old feedback callback only ran inside the visible free-hand
pose branch, and its touching condition also required the native arm blend to
be exactly zero. The dominant weapon hand, a two-handed support hand, fully
native hand animations, and hidden/native arm display modes could therefore
skip palm contact feedback even while the collision path was active. Finger
feedback also depended on finger tracking being enabled.

Compared with the released `v1.0.18` source, the old palm path used a 30 ms
pressure buzz that refreshed while the hand remained pressed. The newer path
replaced it with one weaker 25 ms entry pulse. Test48 restores the sustained
pressure buzz, samples tracked palm collision before the native-arm ownership
gate for both controller hands, and also routes fingertip-only contact while
it remains. Contact strength is bounded and still passes through the single
global HAPTICS setting. The Android OpenXR host checks the result of
`xrApplyHapticFeedback`, logs the haptic action's availability, confirms the
first accepted output, and rate-limits failures. These code-path checks do not
prove that a physical controller vibrated; verify that on Quest with the
device checklist and use the new log markers to distinguish a runtime output
failure from a collision-routing failure.

## Regression coverage

The tests use the two negative weapon values from the supplied log and a
negative unit handle. They cover release-to-drop readiness, holster storage,
duplicate movement, inventory pruning, exact draw-slot resolution, hand-state
timeout recovery, and the `-1` empty sentinel. The release latch tests retain
exactly-once delivery and cancel on re-grip, invalid tracking/focus, recenter,
weapon change, and deferred interaction ownership.

Host tests and APK compilation can verify these state transitions, but only
Quest testing can confirm controller events reach this code, native drop/stow
actions take effect, and the runtime physically vibrates both controllers.
See `TEST48-DEVICE-CHECKLIST.md`.
