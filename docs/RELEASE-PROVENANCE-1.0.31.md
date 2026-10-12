# Release 1.0.31 provenance

Owner authorized public promotion of the supplied Test64 APKs on 2026-10-12.
Earlier local-only/publication holds in historical candidate records are superseded
for this publication. Previous public releases are preserved. About metadata is unchanged.

Runtime source: `d1a61e06d08b5ed044a941c447e8872661aea0fa`.
Internal version: `1.0.31-test64`, code76, ARM64/API28.
Public tag: `v1.0.31`; release filenames follow the existing UpdatePolicy contract.
APKs are copied byte-for-byte from the Test64 delivery, not rebuilt or resigned.
The public source tag adds only publication documentation and compatibility metadata
to the runtime source tree. GitHub's source archives are therefore appropriate;
no duplicate source ZIP is required.

| Public APK | SHA-256 |
| --- | --- |
| HaloCE-Android-1.0.31.apk | debcca425b2e467729ebeca991f5c0607bb986e42b93ec2c5c2dcfeef21de4a9 |
| HaloCE-Quest-1.0.31.apk | 45119f2e246e68d9818e82c6874274945c69801a1a263540d501c4fadd19de90 |

Signing certificate SHA-256:
`53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
This matches the established v1.0.18 signer; package IDs stay unchanged.

The release includes compatibility.json (schema1, exact tag, APK filenames,
bytes, hashes and code76). Saves/config policy is preserve, minimum app code15.
The existing v1.0.18 updater accepts stable v1.0.31 and selects the expected
edition filenames; a v1.0.31-test64 tag would be rejected. Version-code comparison
correctly upgrades code48 to76 and does not offer code76 to an existing code76 install.
The normal Android installer approval is still required. No device installation
or launch is part of this publication task.

Recorded package gates: full regression suites, both native builds, guest ABI lint,
version/signature/package checks (see TEST64-DELIVERY-STATUS.md). Device checklist
remains pending; publication is intended to collect user tests and logs, not to
claim universal runtime acceptance. Release-specific package and live asset checks
are recorded in the delivery staging folder after publication.

Release audit: compared both signing certificates and package IDs with downloaded
v1.0.18 APKs; verified code48 ->76, full APK ZIP integrity, native edition
payloads and unchanged hashes. Executed the actual v1.0.18 UpdatePolicy Java
class against the new tag/names, codes15?75 and equal/newer-code rejection.
Existing updater regression suite passed. Public source privacy scan and runtime
tree comparison passed. Private commit history is not pushed.
