# Test40 private candidate delivery

Candidate: **1.0.21-test40 / Android code51 / OpenCE Build157/network24**.
This is not a public release. Public v1.0.18 remains unchanged. No device
acceptance is implied.

## Artifacts

Final APKs, matching source/build ZIPs, manifest, checksums, sizes and hashes
will be recorded here after the candidate package gate passes.

## Verification

- The Quest/flat source regression runner passed all **87 suites** with no
  failures, including the four new feature suites and haptics routing checks.
- Cache-format pytest: **127 passed, 4 skipped** because optional extracted map
  fixtures are not present in this workspace.
- Focused ASan/UBSan checks passed for vehicle lift bounds, NPC interaction and
  rescue, magazine debris lifecycle, reload collision bounds, and hand-contact
  haptic pulse behavior.
- Flat/VR APK builds, signing certificate, APK contents, hashes, and final
  package checks remain pending; this section will be completed after packaging.
- The exact device/runtime acceptance status remains pending owner testing.
