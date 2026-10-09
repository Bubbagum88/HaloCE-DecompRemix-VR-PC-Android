# Test42 delivery status

## Candidate

Private candidate `1.0.23-test42`, Android version code 53, on branch
`test39-interaction-completion`. Public v1.0.18 and prior candidate packages
remain unchanged. PC/Steam Frame remains deferred. No publication, installation
or game launch is authorized.

## Scope carried forward

This candidate deliberately includes the entire post-v1.0.18 project delta:
Test38 manual reload/scope/vehicle and physical-interaction additions; Test39
shake cooling and expanded interaction safeguards; Test40 bounded custom rigs,
magazine debris, vehicle lift and NPC rescue; Test41 reach, rig-slot, unified
haptics, holster mute and session diagnostics; the Test39 user's app icon; and
the generated candidate guide. It also includes selected OpenCE Build167
compatibility fixes while keeping the engine base at Build157/network24.

See `TEST42-REQUIREMENT-DISPOSITION.md` for the complete feature ledger and
restrictions, `TEST42-OPENCE167-INTEGRATION.md` for upstream boundaries, and
`TEST42-DEVICE-CHECKLIST.md` for the required owner test.

## Validation state

- Focused OpenCE, Android native-bridge hash, holster-haptics and all previously
  failing migration/config suites pass.
- Final clean-candidate source run: `tools/run-quest-checks.py` passed all 92
  registered suites, including the production touch editor lifecycle, layout
  codec, NPC interaction/ragdoll lifecycle and selected Build167 fixtures.
- Focused touch checks: 132 codec checks and 312 HUD lifecycle checks passed.
- Vehicle reticle preview no longer applies head-camera convergence while
  mounted; a production-source fixture checks that mounted aiming follows the
  weapon ray, on-foot geometric convergence is preserved, and native projectile
  autoaim/target bookkeeping remains intact.
- Refresh-rate **Auto** now sends OpenXR's specified `0.0` no-preference request
  when returning from a fixed rate. A production-source fixture covers the
  fixed-rate choices, reset, duplicate suppression and unsupported-runtime path.
- Manual reload continues to reacquire authored contact bounds after a transient
  state reset, but reports each weapon/model profile once instead of flooding
  logs on repeated reacquisition. The reload sequence, cancellation and native
  ammo conservation fixtures still exercise the production transaction math.
- This is source/host validation only. The SAF document provider, touch display,
  controller haptics, articulated NPC motion and live networking still require
  Quest/Android owner testing.
- The supplied USA Original/Rev1/Rev2 XISOs were read-only verified against the
  existing image hashes and map inventory. A newly found Android managed-map
  filename restriction was widened to the same safe Custom Edition characters
  accepted by the native Build167 validator; desktop-reserved names and paths
  remain rejected.
- The Android touch-layout codec and production HUD editor lifecycle fixtures
  pass; import remains a preview until the user presses Save.
- Native corpse-ragdoll source audit is complete: no fixed simultaneous corpse
  count cap was found. The native 20-iteration value controls each body's
  settling duration; `NPC RIG SLOTS` caps only the mod's interaction rigs.
  General object/memory pressure cleanup remains unchanged.
- The bundled touch guide documents export/import, per-control hide/restore,
  legacy-visible defaults and the Save/Cancel flow. The Android device checklist
  includes document-picker and app-restart tests.
- Full `tools/run-quest-checks.py` result: 92 passed, no failed suites.
- VR and flat APK builds, certificate/version/parity/icon checks and package
  hashes: pending.
- Quest/Android action tests and live network/co-op tests: pending owner.

Do not describe the candidate as headset verified or as a full OpenCE Build167
source update.
