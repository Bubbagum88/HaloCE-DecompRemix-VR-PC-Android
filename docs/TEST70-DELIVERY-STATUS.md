# Test70 private delivery status

Private **1.0.37-test70 / Android version code 82**, branch
`test39-interaction-completion`. Test69 plus the owner's 72-item
release-preparation list (see TEST70-CHECKLIST.md for each item's
disposition). No install, game launch, push, tag or public release was
performed.

## Builds and source

Folder: `D:\HaloQuest\builds\test70-20261015-v1.0.37-test70`

Both APKs were built from runtime source
`1cd63dc453768a3ca94bef37e8c20b3b77583bee`; the tree was clean before and
after the serial builds. A packaging-check commit (`tools/package-quest.py`:
the RESET CONTROLS row and the remap prompts) and this delivery record
follow it; they change no runtime file. `manifest.json` records the final
`source_commit` separately from `runtime_source_commit`.

| APK | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test70.apk` | 72,655,134 | `d229db0b210b1539a21c93ab0890838a7211055afca6df9d736ca1f9f3ec86e6` |
| `HaloCE-Android-test70.apk` | 70,241,719 | `92de8da1c8e4ca9ef107084de0d60f7ef5bc01f72d61e9667da9d19d422ab519` |

- Quest package: `com.halo.decomp.vr`; Android package: `com.halo.decomp`.
- Both APKs: version `1.0.37-test70`, exact version code **82**, ARM64.
- Existing signing certificate SHA-256:
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
- Install the matching edition over Test69 (or an earlier build signed with
  that certificate). Do not uninstall first if you want to keep app data.
- Toolchain as Test69: WSL Clang 18 (no profile-guided optimisation; the
  profiles need Clang 22), Android NDK 27.2.12479018, build tools 36.0.0,
  Java 17.

## What changed (summary)

Launcher: campaign status labels; Project Lumoria (zip/folder import,
SHA-256 recipe); What's New once per version (assets/whats_new.txt, every
change named); MCC "problem with the disc" cause fixed (GulchCE hooks
restored). Controls: remapping asks (never reshuffles), NONE, RESET CONTROLS,
marks and a hints line, MIRROR BUTTONS, the Button Sprint mask fix. Weapons:
locked holstering, shake cooling and needler shake reload (stroke detector),
rocket/canister ready when seated, charge reminders, Pistol/AR magazine fit,
left-hand lettered guns and per-part winding. Movement: SLIDE, BULLET TIME
(R UP, solo), tree climbing, wall jumps by the look. Fist combat: HIT ASSIST,
LUNGE HOP, GRAB ASSIST 15 cm and its maximum fixed. Network 29 and OpenCE
Build 206 unchanged; HALOFREAK95 fast-decals reviewed, not taken
(TEST70-UPSTREAM-NETWORK.md).

## Completed automated verification

- **149 registered suites passed** before each flavor build (both logs end
  `Failed suites: []`, build exit 0), and once more on their own before the
  builds. New: test_test70_launcher, _controls, _weapons, _movement.
- Both native/Gradle builds succeeded; built-image Opus table checks and the
  guest ABI lint passed for both flavors.
- `_scratch/test70-apk-audit.json`: exact package/version/code, existing
  signer, ZIP integrity, AArch64 libraries and dependency closure, all 26
  Jolt host imports, zstd-jni, OpenXR only in VR, the Test70 guide (Project
  Lumoria) and credits in both.
- `tools/package-quest.py` preflight and final packaging: signatures,
  identity/banner, networking parity, guest markers (including the Test70
  remap prompts and BULLET TIME), required assets and guide, source/build ZIP
  integrity. `SHA256SUMS.txt` covers the delivered files.

Evidence is local under `D:\HaloQuest\_scratch`: `build70-vr.log`,
`build70-flat.log`, `t70/suite2.log`, `test70-apk-audit.json`,
`pkg70-preflight.log`, `pkg70.log`, `stage70` signing/badging reports.

## Device testing still required

Nothing was installed or launched. Automated checks do not establish headset
or phone acceptance. Follow TEST70-DEVICE-CHECKLIST.md (and Test69's and
before). Highest value first: an MCC map (the disc error fix), The Altheros
Experience b40 (send the launch log: model memory is the likely next step),
Project Lumoria import and play, the remap prompts, the left-hand guns, the
Pistol/AR magazine holds, SLIDE and BULLET TIME.
