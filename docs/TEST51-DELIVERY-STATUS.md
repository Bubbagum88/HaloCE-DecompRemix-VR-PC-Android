# Test51 private candidate delivery status

Candidate: **1.0.32-test51 / Android code62**. This is a private owner-test
candidate. Preserve Test50, older test artifacts and public v1.0.18. Do not
publish, install or launch.

## Scope

The highest-priority fix removes the Test50 Quest join crash inside the host
voice-configuration diagnostic. Every voice diagnostic now uses integer-only
format conversions, and the client marks the host settings received before
logging. Voice protocol, routing, microphone policy and in-game controls are
unchanged. Test50 mounted reticle alignment, sprint toggle and prior changes are
retained. See TEST51-CRASH-ANALYSIS.md.

## Build and regression checks

Both APK builds completed successfully on 2026-10-10 with Android guest
clang-22. The full Quest check suite passed for both VR and flat targets
(Failed suites: [] for each gate). The focused voice integration check,
Python compile checks and git diff --check also passed.

The package validator confirmed the expected signing certificate, package IDs,
arm64 ABI, version name/code, ZIP structure, launcher icon and networking
parity between the APKs (only the OpenXR loader is VR-only). The shared guest
and app native libraries were built from the same source commit. Runtime and
voice acceptance still require the device checks below.

Runtime source commit: a11229c8c20128412602d7aad810845c907acac9.
Documentation/package record commit: recorded in the package manifest.

| APK | Size | SHA-256 |
| --- | ---: | --- |
| HaloCE-Quest-VR-test51.apk | 35,861,254 bytes | c00e1bf181607a082b63c6210c1994622a923ab23152d6b01ede6408e4afa1e1 |
| HaloCE-Android-test51.apk | 33,621,499 bytes | 57320e84337a1356c951f207d2c6e53e9fb5ce40237bfde33be5c4fa90f66f7d |

Host-side checks cannot establish Quest multiplayer stability or two-client
voice playback; these remain in TEST51-DEVICE-CHECKLIST.md.

## Artifacts

Final output: D:\HaloQuest\builds\test51-20261010-v1.0.32-test51-final.
The directory contains the APK pair, matching source and build ZIPs, manifest,
compatibility record and SHA-256 list. This remains a private test candidate;
it has not been installed or published.
