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
- Final clean-candidate source run passed all 92 registered suites in both
  serial edition builds, including the production touch editor lifecycle,
  layout codec, NPC interaction/ragdoll lifecycle and selected Build167
  fixtures. Neither run reported a failed suite.
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
- Final VR and flat APK builds completed serially from the same source tree.
  The package gate verified the established signing certificate, app IDs,
  ARM64 ABI, version code/name, icon assets, bundled current guide, managed
  data, privacy checks and networking parity. Both APKs passed ZIP integrity
  and signature verification. Network entries, networking strings and app
  classes match between editions; the OpenXR loader is the expected VR-only
  entry.
- The compaction step removed Gradle's obsolete incremental ZIP records. It
  confirmed that every non-signature APK entry retained its exact hash and
  that the signing certificate did not change.

| Edition | APK | Bytes | SHA-256 |
|---|---|---:|---|
| Quest / VR | `HaloCE-Quest-VR-1.0.23-test42.apk` | 35,527,934 | `eb956b4cafd4f66a3e2302de9e3fc478f773d03c422b35380e8f22298e3184c0` |
| Android / flat | `HaloCE-Android-1.0.23-test42.apk` | 33,361,071 | `3f4c769a98ae065617abc540b6a2913d3cab200cbd3ba860bb6e46846163547d` |

- The installed compiler is clang 18 while the optional PGO profiles were
  produced with clang 22, so the builds completed without PGO. This affects
  profile-guided optimization only; all registered checks and both builds
  completed.
- Quest/Android action tests and live network/co-op tests: pending owner.

Do not describe the candidate as headset verified or as a full OpenCE Build167
source update.
