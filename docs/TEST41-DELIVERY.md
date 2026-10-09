# Test41 private candidate delivery

Candidate: **Halo CE Quest VR + Android 1.0.22-test41 / code52**,
OpenCE Build157/network24. Private test candidate only; it is not published.
Public v1.0.18 and the previously delivered Test40 package remain unchanged.
PC/Steam Frame work remains deferred.

## Artifacts

Final package directory: `D:\HaloQuest\builds\test41-20261009-v1.0.22-test41`

| APK | Size | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-1.0.22-test41.apk` | 35,528,446 bytes | `695D2D84C1DB88033B72B17AE1804A94A11CB7486C40102BB38A943E10829DDD` |
| `HaloCE-Android-1.0.22-test41.apk` | 33,353,707 bytes | `4B9CFF71BDC63BE47259D4DEEAFB8B07F15A455FE319C21BCC7918D1F4839F41` |

Both APKs have package names `com.halo.decomp.vr` and `com.halo.decomp`,
version code 52, version name `1.0.22-test41`, ARM64 payloads, and a valid
v2 signature. Their signing certificate matches Test40's certificate
SHA-256 `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
The flat and VR builds share networking code and app classes; the OpenXR loader
is the only expected APK-entry difference.

The output also includes the matching source ZIP, build ZIP, manifest,
compatibility metadata and SHA-256 list. The package manifest identifies the
source commit and marks runtime acceptance false.

## Validation

- Quest/VR and flat Android builds both completed successfully from the same
  Test41 source. Each build ran all **87 regression suites**; both report
  `Failed suites: []`.
- Coverage includes real production NPC eligibility, NPC rescue, wall contact
  and parkour, world physics, vehicle lift, props, reload/debris, interaction
  lifecycle and haptic feedback, plus the existing networking, Android input,
  launcher and VR suites.
- Both APK signatures and package/version/ABI metadata were inspected. The
  exact APK signing certificate matches Test40. Package-time checks additionally
  verify cross-flavor networking parity, APK contents, source archive integrity,
  guide inclusion, and recorded hashes.
- The first packaging attempt rejected the incremental Quest APK because it
  contained an unindexed duplicate guest payload. The Quest Gradle outputs were
  cleaned and the VR APK was rebuilt from the same source; the corrected APK is
  smaller and must pass the orphaned-ZIP-data check before delivery.
- No APK was installed or launched on a headset. Quest action acceptance is
  pending the checklist in [TEST41-DEVICE-CHECKLIST.md](TEST41-DEVICE-CHECKLIST.md).
  Host tests and a successful compile do not prove that physical grabs,
  climbing, rescue or other controller actions work in the game.

See [TEST41-DELIVERY-STATUS.md](TEST41-DELIVERY-STATUS.md) for the evidence
from the supplied logs and [TEST41-REQUIREMENT-DISPOSITION.md](TEST41-REQUIREMENT-DISPOSITION.md)
for scope boundaries and current disposition.
