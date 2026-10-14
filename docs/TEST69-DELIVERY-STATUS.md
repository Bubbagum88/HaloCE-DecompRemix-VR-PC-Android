# Test69 private delivery status

Private **1.0.36-test69 / Android version code 81**, branch
`test39-interaction-completion`. This is Test68 plus compatibility for the
OpenSauce script calls and Halo PC display global used by The Altheros Experience.
No install, game launch, push, tag, or public release was performed.

## Builds and source

Folder: `D:\HaloQuest\builds\test69-20261014-v1.0.36-test69`

Both APKs were built from runtime source `03c364eaf7819f333c37d4cb8cb05838cb0bbd0f`. The tree was clean
before and after the serial builds. This delivery record and checklist are a
later documentation-only commit. The source ZIP includes those final documents;
`manifest.json` records its `source_commit` separately from the unchanged
`runtime_source_commit` above.

| APK | Bytes | SHA-256 |
|---|---:|---|
| `HaloCE-Quest-VR-test69.apk` | 72,560,719 | `df7ffd714237e03fced4ff043119fe381a191fe3c77c2552a2cbe132492dda9a` |
| `HaloCE-Android-test69.apk` | 70,216,756 | `a8c5c13106919cb8f29dcbe77fe9730471094335e3d2083fab1000befac3ed30` |

- Quest package: `com.halo.decomp.vr`; Android package: `com.halo.decomp`.
- Both APKs: version `1.0.36-test69`, exact version code **81**, ARM64.
- Existing signing certificate SHA-256:
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
- Install the matching edition over Test68/Test67 or an earlier build signed
  with that certificate. Do not uninstall first if you want to retain app data.
- Guest compiler: WSL Clang 18; no profile-guided optimization (the checked-in
  profiles require Clang 22). Android NDK 27.2.12479018, build tools 36.0.0,
  Java 17; same toolchain as Test68.

## Change and limits

The owner's Test67 Altheros b40 log passed checksum/resource conversion, then
refused the map for eight missing OpenSauce calls. Test69 adds the five function
names found across the owner's ten maps and handles constant boolean uses of
`rasterizer_fps` without adding a checkpoint-state global.

- Object-data reads/writes support a30's gravity-lift velocity scripts.
- VISR/bloom calls are accepted and explicitly logged, but their OpenSauce tint
  and bloom are **not rendered**.
- Unknown fields, read-only writes, missing objects, NaN and either infinity
  cannot write object physics through these new setters.
- Display-global conversion accepts the actual maps' permanent boolean
  constants; malformed/nonboolean/computed sets still fail validation.
- No new network protocol, voice, input, settings-default or checkpoint-layout
  changes. Test68's OpenCE Build 206/network 29 and prior features are retained.

## Completed automated verification

- **145 registered suites passed before each flavor build**, twice total:
  both logs end with `Failed suites: []` and build exit code 0.
- Both native/Gradle builds succeeded. Built-image Opus table checks and guest
  ABI lint passed for both flavors.
- The two focused Test69 suites also passed with ASan/UBSan. The converter
  retains actual a10/a30 boolean literals (`0xFFFFFF00/01`), confirmed from the
  owner's maps; malformed constants and nonfinite setter values have regressions.
- `_scratch/test69-apk-audit.json`: exact package/version/code, existing signer,
  ZIP integrity, AArch64 native libraries and dependency closure, all 26 Jolt
  host imports, zstd-jni, OpenXR only in VR, carried-forward guide/credits and
  the new script-function markers in both guest images.
- `tools/package-quest.py` preflight passed: signatures, identity/banner,
  networking parity (host 29, joins 11-29), required assets/guide and source/build
  ZIP integrity. Preflight checksums passed in `_scratch/package69-preflight`.
- Final packaging repeats those checks with this completed delivery record.
  `SHA256SUMS.txt` in the delivered folder covers the APKs, archives and manifests.

Evidence is local under `D:\HaloQuest\_scratch`: `build69-vr.log`,
`build69-flat.log`, `test69-apk-audit.json`, `test69-rasterizer-literals.json`,
`pkg69-preflight.log`, `pkg69.log`, and `stage69` signing/badging reports.

## Device testing still required

Nothing was installed or launched. Automated checks do not establish headset
or phone acceptance. Start with Altheros b40, then a10/a30/a50 and the remaining
maps; verify the a30 gravity lift. Model conversion follows the repaired script
validation step and has not yet been observed on a device for these maps.

Follow `TEST69-DEVICE-CHECKLIST.md`, including stock/SPV1 campaign checks and
the carried-forward Test68/Test67 regressions. If loading still fails, provide
the new launch log so the next failing stage can be identified.
