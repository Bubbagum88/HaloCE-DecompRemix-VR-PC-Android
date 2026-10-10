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
retained. See [TEST51-CRASH-ANALYSIS.md](TEST51-CRASH-ANALYSIS.md).

## Build and regression checks

Pending completion of the Test51 VR and flat Android builds and package checks.
Host-side checks cannot establish Quest multiplayer stability or two-client
voice playback; these remain in [TEST51-DEVICE-CHECKLIST.md](TEST51-DEVICE-CHECKLIST.md).

## Artifacts

Pending. Planned output: `D:\HaloQuest\builds\test51-20261010-v1.0.32-test51`.
