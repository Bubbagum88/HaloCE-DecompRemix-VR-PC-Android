# Release 1.0.37 provenance

The owner authorized Test70 as the new public latest release on 2026-10-15.
The prior v1.0.31 release and tag remain unchanged. Repository About metadata
was not changed.

- Public tag/title: **v1.0.37 / Halo CE Quest VR + Android 1.0.37**.
- Supplied runtime: Test70, commit
  `1cd63dc453768a3ca94bef37e8c20b3b77583bee`.
- Internal APK name: `1.0.37-test70`; Android version code **82**; ARM64/API28.
- Package IDs: Quest `com.halo.decomp.vr`, flat Android `com.halo.decomp`.
- The release APKs are byte-for-byte copies of the supplied Test70 binaries,
  renamed to the stable names required by `UpdatePolicy.asset()`:

| Public asset | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-1.0.37.apk` | 72,655,134 | `d229db0b210b1539a21c93ab0890838a7211055afca6df9d736ca1f9f3ec86e6` |
| `HaloCE-Android-1.0.37.apk` | 70,241,719 | `92de8da1c8e4ca9ef107084de0d60f7ef5bc01f72d61e9667da9d19d422ab519` |

Signing certificate SHA-256:
`53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
It matches the established signer so Android can update the installed app while
preserving app data.

`compatibility.json` has schema 1, exact v1.0.37 filenames, APK sizes/hashes,
code 82 and network range 11–29. The launcher verifies this metadata and the
GitHub asset digests before offering an update. Saves and config are marked
preserve. GitHub's source archives are generated from the release tag; no
duplicate source ZIP is attached.

The release tag contains the Test70 runtime plus release README, release notes,
provenance and stable updater metadata. The previous v1.0.31 tag/assets are
retained. About metadata stays unchanged.

Build evidence is in the supplied Test70 delivery record:
`TEST70-DELIVERY-STATUS.md` and its checklists. The documented 149-suite runs,
both builds, ABI checks and package checks passed. The supplied candidate has
not been installed/launched for this release by the packaging agent; device
acceptance remains pending. Publication is for user testing and logs, not a
claim that experimental systems or every device/mod/server combination is
fully validated.
