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

Pending. Record the full Quest/VR and flat Android regression-suite results,
version/package/signature checks, source/build archive checks, and exact hashes
here after packaging. Host validation cannot establish physical haptic output
or headset animation behavior; headset acceptance remains pending.

## Artifacts

Pending final package path and SHA-256 hashes. Keep Test48 and older outputs
unchanged. PC/Steam Frame remains deferred.
