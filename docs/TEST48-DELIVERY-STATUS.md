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
release cancellation safeguards. Results and APK hashes will be recorded after
the Test48 VR and flat builds and package gate complete.

Host tests and compilation do not establish headset/controller behavior. The
device acceptance checklist remains pending until the owner tests both APKs.
Public v1.0.18 and every prior private candidate remain preserved. PC/Steam
Frame remains deferred.
