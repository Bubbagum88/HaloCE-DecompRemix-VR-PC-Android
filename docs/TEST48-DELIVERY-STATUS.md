# Test48 private candidate delivery status

Candidate target: **1.0.29-test48 / Android version code59**, on
`test39-interaction-completion`. This candidate carries Test47 and fixes the
signed-datum rejection that broke weapon grip release, dropping and holster
storage. It also fixes surface-contact haptic routing across both hands and
adds OpenXR output diagnostics. It is for owner testing only. Do not publish,
install, or launch it.

The source audit is in [TEST48-REGRESSION-AUDIT.md](TEST48-REGRESSION-AUDIT.md).
Owner retest steps are in [TEST48-DEVICE-CHECKLIST.md](TEST48-DEVICE-CHECKLIST.md).
Cumulative Test47 features, upstream scope and boundaries remain documented in
[TEST47-PLAYER-NOTES.md](TEST47-PLAYER-NOTES.md),
[TEST47-REQUIREMENT-DISPOSITION.md](TEST47-REQUIREMENT-DISPOSITION.md), and
[TEST47-OPENCE177-INTEGRATION.md](TEST47-OPENCE177-INTEGRATION.md).

## Build and host verification

The regression fixtures exercise valid negative datum handles `-431815724` and
`-431750187`, exact `-1` empty-sentinel behavior, release-to-drop/stow path
selection, holster storage/pruning/draw resolution, hand-state recovery, and
release cancellation safeguards. The complete accumulated regression suite
passed in both the Quest/VR and flat build workflows (`Failed suites: []`).
Both APKs report version name `1.0.29-test48`, version code `59`, arm64-v8a,
and the expected test signing certificate. The package gate passed APK
integrity, signing, package/version, networking parity, source archive and
build archive checks.

The Android guest was compiled with Clang 22 and the committed LLVM PGO profile
(`-fprofile-use=pgo/halo_linux.profdata`). The separate host Linux target used
the configured Clang 18 fallback; that host target is not packaged in either
APK.

Runtime source commit: `ca1f5cc40094a0ea2ab0a2b3630ad27151c3b7d0`. Final package
and matching source/build ZIPs:
`<artifacts>\test48-20261010-v1.0.29-test48-final`.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `app-vr-debug.apk` (Quest/VR) | 35,859,402 bytes | `0c9a1910898b9a61a60ebebe49d0e3f1a8a078d3a0502581ea233ccc3666a680` |
| `app-debug.apk` (flat Android) | 33,619,399 bytes | `a8c858394e6e13318536743437a63768f7f3c3b65ae961f8e24e5c2f5ab072db` |
| `HaloCE-Quest-test48-source.zip` | recorded in `SHA256SUMS.txt` | generated from the committed source |
| `HaloCE-Quest-test48-build.zip` | recorded in `SHA256SUMS.txt` | includes both APKs and candidate documentation |

The APK hashes and every package-file hash are repeated in the output folder's
`SHA256SUMS.txt` and `manifest.json`.

Host tests and compilation do not establish headset/controller behavior. The
device acceptance checklist remains pending until the owner tests both APKs,
including that physical controller motors respond to the sustained contact
haptics.
Public v1.0.18 and every prior private candidate remain preserved. PC/Steam
Frame remains deferred.
