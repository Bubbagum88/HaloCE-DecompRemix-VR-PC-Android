# Test49 private candidate delivery status

Candidate: **1.0.30-test49 / Android code60** on
`test39-interaction-completion`. This is an owner test build. Public v1.0.18
and the prior Test48 files remain preserved. Do not publish, install, or launch
from the packaging workflow.

The source correction restores the v1.0.18 hand-contact and arm-ownership gate
for surface haptics. The weapon-fire haptic functions are byte-for-byte equal
to the v1.0.18 versions. The build also logs emitted melee/switch action bits
for the reported weapon-animation concern. Evidence and limitations are in
[TEST49-REGRESSION-AUDIT.md](TEST49-REGRESSION-AUDIT.md); owner test steps are
in [TEST49-DEVICE-CHECKLIST.md](TEST49-DEVICE-CHECKLIST.md).

## Build and package checks

Completed for both editions on 2026-10-10:

- The full `tools/run-quest-checks.py` regression suite passed for the Quest/VR
  build and again for the flat Android build (`Failed suites: []`). This
  includes the haptics, holster, hand-compliance, reload, multiplayer/co-op,
  Android input and retained-feature checks.
- Both Android native/Gradle builds completed with the Android guest compiler
  set to Clang 22 and the committed LLVM 22 profile selected. The shared guide
  generator preserved the full cumulative candidate guide.
- Package parity checks passed. The game/network entries match; the expected
  OpenXR loader is the edition-specific difference.
- `aapt` confirms version `1.0.30-test49`, code `60`, min SDK `28`, with
  `com.halo.decomp.vr` and `com.halo.decomp` package IDs. `apksigner verify`
  passes for both APKs. Their signing certificate matches Test48, allowing an
  in-place update from that candidate without uninstalling it.
- Final candidate package directory:
  `<artifacts>\test49-20261010-v1.0.30-test49-verified`
- VR APK SHA-256:
  `8838c235290238b62483d560d18b6f4d58c586cdb88571725dc8ded55851c32a`
- Flat APK SHA-256:
  `16d3851421de7a5d286452b8ed8e3ad6860a675a54636bd61fac7f32dc846e76`

No APK was installed or launched. Automated and source-level checks cannot
establish the physical haptic feel or confirm the reported animation in the
headset; owner device acceptance remains pending.

## Artifacts

The verified package contains both APKs plus matching build and source ZIPs.
Test48 and older outputs remain unchanged. PC/Steam Frame remains deferred.
