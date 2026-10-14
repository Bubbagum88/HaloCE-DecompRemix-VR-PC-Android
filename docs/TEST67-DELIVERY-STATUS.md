# Test67 delivery status

Private **1.0.34-test67 / Android code 79**, branch
`test39-interaction-completion`. One combined candidate: Test67's precision
polish, Test68 (GulchCE Halo 1 MCC maps, solo only, with the launcher's Steam
Workshop) merged in, OpenCE testing 52e33a39's hardening, and every branch of
the OpenCE fork by jcompto95-tech (HALOFREAK95). No install, game launch, push,
tag or release.

## Builds and source

Folder: `D:\HaloQuest\builds\test67-20261014-v1.0.34-test67`

Both APKs were built from runtime source
`d8cf46c740b94a8b9af9865bf93d1f759700d8b2` (the working tree at build time,
committed unchanged right after, with the regenerated in-APK guide). The source
ZIP holds that commit (`source_commit` and `runtime_source_commit` in
`manifest.json`); this record is a later documentation-only commit. The source
ZIP's hash is in `SHA256SUMS.txt` with the build ZIP and both manifests.

| APK | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test67.apk` | 72,557,679 | `b0f87a89fa5a6011ba1284bfa4ec3145b1607ce74cccddc2cbc3a27e94b327fc` |
| `HaloCE-Android-test67.apk` | 70,213,716 | `b44a6e88d268933120a256e9f27a0dc15639902c7897886b76e7b2bbfc4d6540` |

- Quest: `com.halo.decomp.vr`; Android: `com.halo.decomp`.
- Both: `1.0.34-test67`, version code **79**, ARM64 only.
- Signing certificate SHA-256:
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`, the
  existing project signer. Install over the matching edition to keep app data.
- Guest compiler: WSL Clang 18 as before; built without profile-guided
  optimisation (the profiles need Clang 22). No PGO improvement is claimed.
- **Size:** about 72 MB, against Test66's 38.7 MB. The game is about the same
  size; the growth is the Steam Workshop's Java libraries (JavaSteam, Bouncy
  Castle, Kotlin, Ktor, Protocol Buffers: about 31 MB of code), kept whole.
  Shrinking them (R8) risks breaking JavaSteam's reflection and is left for a
  later, device-tested candidate.

## Completed automated verification

- Full suite: 142 registered suites. The standalone run found two suites not
  yet adapted to the MCC loader (test_test31_audio, test_test32_menu_arrows:
  test stubs, not game bugs); both fixed and rerun alone. Then the suite passed
  completely before **each** flavor build (`Failed suites: []`, twice).
- GulchCE's MCC tests: 890 passed, including 140 32-bit programs run under
  qemu-i386 (WSL1 cannot start them directly). Not run: 152 cases of two
  harnesses GulchCE gates to Windows with clang, and 1 opt-in case needing a
  local MCC map. Left out for MCC solo only: 2 online files, 3 cases (reasons in
  TEST67-EVIDENCE.md).
- Both native/Gradle builds exited 0. The built guest image's Opus table check
  and the guest ABI lint passed for each flavor. Both flavors' launcher Java
  compiled against JavaSteam 1.8.0 and OkHttp 5.3.2.
- APK audit: exact package/version/code, the existing signer, ZIP integrity,
  AArch64 native libraries with satisfied dependencies, all 26 defined Jolt host
  imports, zstd-jni bundled, OpenXR loader only in the Quest APK, the Test67
  guide (Extra Effects, ALL TO DEFAULT, MCC maps, Community extras, Third Person)
  and credits (the fork, GulchCE, JavaSteam, zstd-jni).
- Package: `sha256sum -c` passed for both APKs, both ZIPs and both manifests;
  `apksigner verify` and `aapt dump badging` evidence saved.

## Network and audio

Voice, the voice codec and the network wire version (28) are unchanged. The
community extras (armor sync, text chat, vote details) use new message kinds
87-92 only, which stock OpenCE network-28 peers ignore; each is behind
`network.community_extras` (default on; launcher Server Browser switch). The
campaign resource and converted-sound cache addressing changed (the Altheros
fix). MCC maps are solo only; online MCC (GulchCE's network 42) is not included.

## Not verified

Nothing here was installed or launched. Every headset and phone result in
TEST67-DEVICE-CHECKLIST.md is pending: combat, reload, MCC maps and the Steam
Workshop sign-in (with the tester's own account), every fork feature on the
Quest's GPU and frame time, online play with stock and extras peers, and
keyboard chat/votes. Automated checks are not device acceptance.
