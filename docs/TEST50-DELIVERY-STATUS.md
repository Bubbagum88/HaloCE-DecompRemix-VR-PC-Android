# Test50 private candidate delivery status

Candidate: **1.0.31-test50 / Android code61** on
`test39-interaction-completion`. This is an owner test build. Public v1.0.18
and all earlier candidate artifacts remain preserved. Do not publish, install,
or launch from the packaging workflow.

Test50 adds an optional hold/toggle mode for Button Sprint, low-rate voice-path
diagnostics, and a source-backed mounted shot alignment correction. The Test49
Ghost and Scorpion shots show 2.28° and 2.61° reticle-to-shot deviation; the
source mismatch was a raw-muzzle reticle versus native game-camera aim assist
on the projectile. The local VR driver/gunner now fires along the selected
muzzle/reticle ray, avoiding target snapping. On-foot, passenger, remote-player
and flat Android aim assist remain unchanged; no protocol changed. Hold remains
the sprint default. The voice review found that the Test49 log confirms microphone opening
but cannot prove speech transmission or remote playback; no audio-routing
change was made. The new logs record host settings and packet/decode progress
without recording audio or player names. OpenCE Build177 remains the latest
release checked; its reticle artwork was already present, and network24 is
unchanged.

## Build and package checks

- VR and flat Android APK builds both completed successfully from runtime source
  commit `0353820e2f4e9ea26be0766e401b4c0bd79953ef` using
  `HALO_ANDROID_GUEST_CC=clang-22` and `HALO_VERSION_NAME=1.0.31-test50`.
- Both build-script runs completed the full `tools/run-quest-checks.py` gate:
  `Failed suites: []`.
- Generated Ninja commands confirm that the packaged Android game guest uses
  Clang 22 and `-fprofile-use=pgo/halo_linux.profdata`. The build also emitted a
  separate warning that the native Linux compiler resolves to Clang 18 and
  cannot consume that profile; this warning does not apply to the Android guest
  compilation used in either APK.
- Gradle produced `app-vr-debug.apk` and `app-debug.apk`. `aapt` reports
  `com.halo.decomp.vr` and `com.halo.decomp`, both version name
  `1.0.31-test50`, version code `61`. `apksigner` verified both APKs; both use
  certificate SHA-256
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
- Test APKs are 35,860,942 bytes (VR) and 33,621,171 bytes (flat). SHA-256:
  - VR: `6877f9dd6669be423337778d7b76b9f7e1baedcdfb8dee8412ad40a198a11843`
  - Flat: `87adc13581be580c0afcf23b47bfc368702c29e4e0313742e2ed571687e83ab2`
- OpenCE Build177 is the latest official release checked for this candidate;
  the repository includes selected fixes through Build177, while retaining the
  Build157/network24 base. No full upstream rebase or network protocol change
  was made in Test50.

## Artifacts

The private candidate package is pending final source/archive manifest
validation. Device acceptance remains pending: the supplied Test49 log does not
prove voice transmission or remote playback, and the owner still needs to
confirm vehicle shot-center alignment and sprint feel in headset. The mounted
aim correction has source and automated regression coverage, but no claim of
live in-game vehicle firing verification is made.
