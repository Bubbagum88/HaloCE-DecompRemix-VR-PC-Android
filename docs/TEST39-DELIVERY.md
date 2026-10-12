# Test39 private candidate delivery

**Candidate:** Halo CE Quest VR + Android `1.0.20-test39`, Android version
code 50, OpenCE Build157/network24.
**Status:** private owner-test candidate only. Public v1.0.18 remains the
accepted/public baseline. This does not authorize publication or installation.

The final logo-updated APKs and matching archives are in
`<artifacts>\test39-20261008-v1.0.20-test39-logo-verified`.
The generated `manifest.json` and `SHA256SUMS.txt` record the exact source
commit, APK/runtime source commit, signing certificate, archive hashes and
file sizes. Both APKs use the established signing certificate.

| Edition | APK | Bytes | SHA-256 |
|---|---|---:|---|
| Android / flat | `HaloCE-Android-1.0.20-test39.apk` | 33,350,243 | `79674d4431293c9459658171b5cdfe47cfaf477cf8f7aed8ca98abeae585c197` |
| Quest / VR | `HaloCE-Quest-VR-1.0.20-test39.apk` | 35,456,998 | `9e7684b1553e61db0459e7927f4c313204e79bb588b4b2846520895e4e93b893` |

The Quest and Android adaptive launcher icons now use the supplied Halo CE
Combat Evolved VR / Open CE Port logo artwork.

Both APKs use package IDs `com.halo.decomp` / `com.halo.decomp.vr`, version
code 50, minimum API 28 and the existing signing certificate. The package gate
confirmed networking parity and that the only expected APK entry difference
is the Quest OpenXR loader.

The work and current known boundaries are in
[TEST39-DELIVERY-STATUS.md](TEST39-DELIVERY-STATUS.md). The end-user feature
summary is [TEST39-PLAYER-NOTES.md](TEST39-PLAYER-NOTES.md); device acceptance
steps are [TEST39-DEVICE-CHECKLIST.md](TEST39-DEVICE-CHECKLIST.md).

This source and build delivery is not a public GitHub release. Device/runtime
acceptance remains pending. Preserve the previous public release and do not
advance accepted state until the owner reports testing.
