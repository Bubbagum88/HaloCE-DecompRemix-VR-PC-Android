# Test40 progress — 1.0.21-test40

## Scope

Finish the four previously deferred interaction requests without changing the
public v1.0.18 release: custom NPC rig fallback, persistent discarded magazine
visuals, whole-vehicle lifting, and automatic mission-NPC rescue. Package a
private flat Android and Quest VR candidate. Keep PC/Steam Frame deferred.

## Work completed in source

- Added default-off custom humanoid graph fallback for eligible unclassified
  actors; local-only, with the previous species paths preserved.
- Added default-off, map-session discarded magazine visuals with swept sphere
  collision, 32-slot oldest-first recycling, and map/save lifecycle resets.
- Added default-off vertical lifting for a validated subset of unoccupied
  native vehicles through bounded vehicle acceleration; WORLD GRAB required.
- Added default-off local NPC recovery with a ten-second falling dwell, saved
  grounded pose, full-capsule clearance, and AI/mission-state preservation.
- Completed the haptic pass: sustained load feedback now also covers validated
  vehicle lifts and locally held articulated NPC limbs through the existing
  WEIGHT HAPTICS toggle. Acquisition/reload/parkour pulses and one-shot finger
  collision contact haptics remain intact; device comfort checks are listed.
- Added focused ASan/UBSan harnesses and registered them in the normal Quest
  regression runner.
- Added user notes, status, requirement disposition and device acceptance docs.

## Current validation state

- Focused harnesses: passed for rescue, magazine debris, vehicle lifting,
  NPC custom-rig admission, NPC/vehicle weight-feedback routing and retained
  collision-contact haptics.
- Full Quest/flat regression runner: 87 suites passed, no failures. Cache-format
  pytest: 127 passed, four optional map-fixture skips. Flat and Quest APK
  builds plus package/signature verification remain pending.
- Quest/Android device and co-op acceptance: pending owner testing.

## Explicit limits

This candidate does not claim universal custom skeleton mapping, saved or
networked magazines, full 6-DoF vehicle manipulation, NPC resurrection, or
automatic recovery of actively script-owned actors. See
[TEST40-REQUIREMENT-DISPOSITION.md](TEST40-REQUIREMENT-DISPOSITION.md).
