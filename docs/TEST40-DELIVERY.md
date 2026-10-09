# Test40 private candidate delivery

Candidate: **1.0.21-test40 / Android code51 / OpenCE Build157/network24**.
This is not a public release. Public v1.0.18 remains unchanged. No device
acceptance is implied.

## Artifacts

The private candidate package is written to
`D:\HaloQuest\builds\test40-20261008-v1.0.21-test40-delivery` and contains:

- `HaloCE-Android-1.0.21-test40.apk` — 33,350,171 bytes; SHA-256
  `566254a00d4bd4d0a0fa4a1da7fad4a101250497dd24a00a7d28e27ca2621acc`.
- `HaloCE-Quest-VR-1.0.21-test40.apk` — 35,458,718 bytes; SHA-256
  `b705cfcdb6715733643523a14e3d72735a4221b578e49bef27165838b83898fc`.
- `HaloCE-Quest-test40-source.zip` and `HaloCE-Quest-test40-build.zip`, plus
  `manifest.json`, `compatibility.json` and `SHA256SUMS.txt`.

Both APKs use package version code **51**, version name **1.0.21-test40**,
ARM64 native code, minimum SDK 28, and the established Android debug signing
certificate SHA-256
`53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
Both were built from runtime commit `a0bf36c8b065b20a74a1072c44f38b35aef42386`.
The package manifest records the exact documentation/source archive commit.

## Verification

- The Quest/flat source regression runner passed all **87 suites** with no
  failures, including the four new feature suites and haptics routing checks.
- Cache-format pytest: **127 passed, 4 skipped** because optional extracted map
  fixtures are not present in this workspace.
- Focused ASan/UBSan checks passed for vehicle lift bounds, NPC interaction and
  rescue, magazine debris lifecycle, reload collision bounds, and hand-contact
  haptic pulse behavior.
- Both flat and Quest builds passed all 87 regression suites. APK metadata,
  ARM64 ABI, OpenXR declaration (Quest), signing identity and network parity
  were checked. The flat APK was cleanly reassembled after a mode-switch left
  stale ZIP payload in an incremental artifact; its final archive is compact.
- Cache-format pytest: **127 passed, 4 skipped** for absent optional extracted
  map fixtures. The local clang 18 toolchain does not match the clang 22 PGO
  profiles, so this candidate was built without profile-guided optimization.
- The package gate creates and validates the matching source/build ZIPs and
  writes final checksums and exact source identity to the included manifest.
- The exact device/runtime acceptance status remains pending owner testing.
