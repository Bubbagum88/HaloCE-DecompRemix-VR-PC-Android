# Test66 delivery status

Private **1.0.33-test66 / Android code 78**, branch
`test39-interaction-completion`. Continued from `d34e42b1` after reviewing
the owner's Test65 feedback and later additions in the local session record.

## Builds and source

Folder: `D:\HaloQuest\builds\test66-20261013-v1.0.33-test66`

Both APKs were built from runtime source
`0b5c7e628060d977f7613f28433cca094a3f35d0`. The source archive also includes the subsequent
documentation-only completion commit, identified by `source_commit` in
`manifest.json`; `runtime_source_commit` identifies the APK source exactly.
The source ZIP's own hash is in `SHA256SUMS.txt`, avoiding a circular hash
inside the archive. That file also records the build ZIP and both manifests.

| APK | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test66.apk` | 38,660,190 | `45231f63a188f5da0908bb703bcce9b47f40e4d8416c0ab11b9581ae7b95cbc7` |
| `HaloCE-Android-test66.apk` | 36,314,559 | `6fdacd497614f7cb4a0b97780f195e4a84c9e469deea0a5dfe4e7ea357912071` |

- Quest: `com.halo.decomp.vr`; Android: `com.halo.decomp`.
- Both: `1.0.33-test66`, version code **78**, ARM64.
- Signing certificate SHA-256:
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
  This is the existing project signer. Install over the matching edition
  to retain app data; uninstalling is unnecessary for this candidate.
- Guest compiler: WSL Clang **18.1.3**, same compiler line as Test65.
  Build configuration explicitly reports that the newer LLVM 22 PGO profiles
  are not used. No PGO performance improvement is claimed for these APKs.

## Completed automated verification

- **131/131 registered suites passed** in the standalone rerun and again
  before **each** flavor build (three complete runs; `Failed suites: []`).
- Both native/Gradle builds exited **0**. Exact built-image Opus table checks
  and the guest ABI lint passed for each flavor.
- APK audit checked exact package/version/code, the existing signer, ZIP
  integrity, AArch64 native libraries, all 19 defined Jolt host imports,
  resolvable bundled/system library dependencies, VR/flat separation,
  bundled Test66 guide and Jolt/Lucide attribution.
- Production host ragdoll bridge checked with ASan/UBSan: contact stride and
  fields, signed vehicle IDs, capacity limit, empty/null guards and canaries.
- Jolt's compiled falling-body test landed and settled above the floor and
  passed destruction/reset. This is a host test, not a headset observation.
- The new map-seed compiled harness rejects the pre-fix implementation in a
  negative-control run, then passes with the fix.

Evidence logs are in `D:\HaloQuest\_scratch`: `full66.log`,
`build66-vr.log`, `build66-flat.log`, `test66-apk-audit.json`,
`test66-bridge-audit.log`, `test66-negative-seed.log`, and `pkg66.log`.
`tools/package-quest.py` is the final archive/APK gate; the delivered
`SHA256SUMS.txt` covers the immutable APKs, ZIPs and manifests.

## Resumed audit changes

- Corrected the escaped speaker bitmap path; voice codec, microphone and
  playback implementations remain unchanged.
- Prevented advertising zero-valued internet peer keys as map-download
  sources. Host downloads and LAN seeding remain; no wire/version change.
- Added missing Jolt and Lucide license notices and credits.
- Corrected stale Build201 identity assertions without removing gameplay
  checks; preserved UTF-8 labels in the fixtures.
- Updated continuation documents, feature checklist and guide evidence
  wording. The accepted Android touch layout and updater were preserved.

## Feature inventory and testing limits

`TEST66-CHECKLIST.md` covers every current Test66 item;
`TEST66-FIELD-GUIDE.md` explains the controls and changes;
`TEST66-OPENCE-PARITY.md` records the upstream integration and exclusions.
These include vehicle/reload/fist/grab/wall-run refinements, left-hand mode,
waist grenades, gravity-glove weapon pull, dynamic Jolt ragdolls,
SPV1/Altheros/original campaign switching, map sharing, vote kick,
Server Setup sub-screens and display options. Android includes the PR's
Video Setup > Graphics > Physics selector: RAGDOLL (default) or CLASSIC;
choose OK to save. VR uses IMMERSION > RAGDOLLS > DEATH PHYSICS.

**Device checks remain pending for this exact pair.** No headset/phone game
session, real campaign progression, immersive-vehicle comfort, remote
voice/co-op session or real internet map transfer was run here. Use
`TEST66-DEVICE-CHECKLIST.md`; automated tests do not certify those behaviors.
Ghost/tank acceptance refers to the owner's prior Test65 result; Banshee
remains untested. Test63-65 checklists still apply where not confirmed.

Internet map sharing uses the host; LAN peers can seed. WebRTC/browser
players and multi-peer internet signalling were deliberately not introduced.
Network remains host 28 / client targets 11-28. Two upstream harnesses
(`test_server_teardown`, `test_cinematic_titles`) fail on upstream itself and
are not in the 131-project-suite claim; see the parity document.
Dual wield remains the documented future design from Test65. PC and Steam
Frame remain deferred.

No push, publication, tag, installation or game launch was performed.
