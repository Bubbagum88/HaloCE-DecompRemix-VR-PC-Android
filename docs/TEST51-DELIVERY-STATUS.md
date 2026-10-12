# Test51 runtime and delivery record

Test51 was released as stable **v1.0.19 / Android version code63** after the
owner confirmed on Quest that the multiplayer join crash was gone and voice
chat worked. Preserve the original Test51 APK/package record as historical
evidence; the public release has separately versioned APKs and provenance.

## Scope

The highest-priority fix removes the Test50 Quest join crash inside the host
voice-configuration diagnostic. Every voice diagnostic uses integer-only
format conversions, and the client marks host settings received before
logging. Voice protocol, routing, microphone policy and in-game controls are
unchanged. Test50 mounted reticle alignment and sprint toggle are retained.
See TEST51-CRASH-ANALYSIS.md.

## Build and regression checks

Both owner-test APK builds completed on 2026-10-10 with Android guest clang-22.
The full Quest check suite passed for VR and flat targets (Failed suites: []
for each gate). The focused voice integration check, Python compile checks and
git diff --check also passed.

The package validator confirmed the expected signing certificate, package IDs,
arm64 ABI, version name/code, ZIP structure, launcher icon and networking
parity between the APKs (only the OpenXR loader is VR-only). The owner
subsequently confirmed the join and voice behavior on Quest. This does not
certify every headset, server, map, revision or player count.

Runtime source commit: a11229c8c20128412602d7aad810845c907acac9.
Owner-test APK package: <artifacts>\test51-20261010-v1.0.32-test51-final.
Stable release hashes are recorded in RELEASE-PROVENANCE-1.0.19.md.
