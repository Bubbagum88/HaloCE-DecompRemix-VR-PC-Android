# Test68 delivery status

Private **1.0.35-test68 / Android code 80**, branch
`test39-interaction-completion`. Test67 (delivered from d8cf46c7) plus OpenCE
Build 206 (8102e711): network 29, Custom Edition maps keep their own names,
map sharing restart/validation hardening and the stb_vorbis floor fix. No
install, game launch, push, tag or release.

## Builds and source

Folder: `D:\HaloQuest\builds\test68-20261014-v1.0.35-test68`

Both APKs were built from runtime source
`c331ef2bbef048be4af86901be9dfb6b2c7e8f9f`: the Test68 commit 9a4d69c0, plus the
in-APK guide the build regenerates and one moved test pin. It was committed
before the final builds, and the tree stayed clean through them. The source ZIP
holds that commit (`source_commit` and `runtime_source_commit` in
`manifest.json`); this record is a later documentation-only commit.

| APK | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test68.apk` | 72,559,067 | `6abf04a0ff6e0937858d8f7e05c1dd19855ae9f448126b19fbe634a804586837` |
| `HaloCE-Android-test68.apk` | 70,215,096 | `11d8063b808f127203dc0d14b331681ff976af204707fbfe84cc31a754743d1f` |

- Quest: `com.halo.decomp.vr`; Android: `com.halo.decomp`.
- Both: `1.0.35-test68`, version code **80**, ARM64 only.
- Signing certificate SHA-256:
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`, the
  existing project signer. Install over Test67 (or any earlier build of the same
  edition) to keep app data.
- Guest compiler: WSL Clang 18, without profile-guided optimisation (the
  profiles need Clang 22).
- `SHA256SUMS.txt` covers both APKs, the source and build ZIPs, `manifest.json`
  and `compatibility.json`; `sha256sum -c` passed.

## Completed automated verification

- **Full suite: 143 registered suites, `Failed suites: []`** before each flavor
  build (twice).
- The first build attempt stopped at one suite: `test_voice_chat_integration`
  pins `package-quest.py`'s version-code chain, which Test68 had extended to
  code 80 without moving the pin. The pin was moved (c331ef2b; no voice code
  changed), and both builds were rerun from clean Gradle folders.
- Earlier failures in the session's logs (`test_test31_menu_maps`,
  `test_test67_fork`) predate 9a4d69c0. Both pass, alone and in the suites,
  as does `test_test68_network29`.
- Both native/Gradle builds exited 0. The guest image's Opus table check and the
  guest ABI lint passed for each flavor.
- APK audit (`_scratch/test68-apk-audit.json`):
  - exact package/version/code and the existing signer;
  - ZIP integrity, no orphaned ZIP data;
  - AArch64 native libraries with satisfied dependencies, and all 26 defined
    Jolt host imports;
  - zstd-jni bundled, and the OpenXR loader only in the Quest APK;
  - the guide and credits (network 29, OpenCE Build 206, Test67's features).
- `tools/package-quest.py`: signer, identities, the VR banner and networking
  parity (host 29, joins 11-29) passed. The `apksigner verify` and
  `aapt dump badging` evidence is in `_scratch/stage68`.

## Network and audio

**Network 29, as OpenCE Build 206.**
- This build hosts 29 and joins 11-29 (All compatible by default).
- Network-28 players (Test67, older OpenCE) cannot join its hosts, as with any
  OpenCE version change. It still joins theirs, finding a Custom Edition map by
  name and checking its header checksum.
- Voice and the voice codec are unchanged.
- The community extras keep message kinds 87-92 (stock peers ignore them).
- MCC maps remain solo only.

## Not verified

Nothing was installed or launched. Every check in
`TEST68-DEVICE-CHECKLIST.md` is pending, as is all of Test67's:
- network 29 hosting and joining with OpenCE Build 206 players;
- joining network-28 hosts with Custom Edition maps;
- the "Name (2)" map list;
- stricter map validation against SPV1, Altheros and MCC maps.

Automated checks are not device acceptance.
