# Test39 private candidate delivery

**Candidate:** Halo CE Quest VR + Android `1.0.20-test39`, Android version
code 50, OpenCE Build157/network24.
**Status:** private owner-test candidate only. Public v1.0.18 remains the
accepted/public baseline. This does not authorize publication or installation.

The exact APK filenames, byte counts, SHA-256 hashes, signing certificate,
source commit, APK/runtime source commit, source archive, package archive and
reproducible checksum list are in the generated `manifest.json` and
`SHA256SUMS.txt` alongside the APKs. The candidate is built with the established
certificate; package verification must reject any different key.

| Edition | APK | Bytes | SHA-256 |
|---|---|---:|---|
| Android / flat | `HaloCE-Android-1.0.20-test39.apk` | 32,811,714 | `dc2375e8157e3584531d2babe87c406ddd51aef329dab21302828e0376613e18` |
| Quest / VR | `HaloCE-Quest-VR-1.0.20-test39.apk` | 34,918,473 | `12c2936ef64039b46d7e33a604bf534458c762d12151702a2d8c7e6ad20baf5f` |

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
