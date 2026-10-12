# Test64 delivery status

Private **1.0.31-test64 / Android code76**, branch
`test39-interaction-completion`: Test63 (`e2849e9b`) plus the fix for the
crash opening VR SETTINGS (`a27279e4`).

## Artifacts

Folder: `D:\HaloQuest\builds\test64-20261012-v1.0.31-test64`
APK source commit: `d1a61e06d08b5ed044a941c447e8872661aea0fa` (both flavors built from this exact tree, in WSL
with clang 18; the full regression suite ran before each flavor build with
`Failed suites: []`; the guest ABI lint passed). A first flat build stopped
before linking on a transient `fork: Invalid argument` from the NDK compiler
(nothing compiled wrong); it was rebuilt from the same commit and passed.

| File | SHA-256 |
|---|---|
| `HaloCE-Quest-VR-test64.apk` | `45119f2e246e68d9818e82c6874274945c69801a1a263540d501c4fadd19de90` |
| `HaloCE-Android-test64.apk` | `debcca425b2e467729ebeca991f5c0607bb986e42b93ec2c5c2dcfeef21de4a9` |
| `HaloCE-Quest-test64-source.zip` | `13b0cc4b2b06d05fbbdf77da1988bb8ef63e568a505cf95bed1ae5094387713a` |
| `HaloCE-Quest-test64-build.zip` | `68a5ce0944a788df411e94246c07c752687d249936a9d19fda652fb21e48a5cf` |
| `manifest.json` | `c11c023e763763368a2fe0187cdfdaa5de9e9c4ea80c7cc88a2008629d6dc881` |
| `compatibility.json` | `516a7e6681e7a917c4789ce67f298df2e2db605608ea4edaacea6ca4dfb68dba` |

- `HaloCE-Quest-VR-test64.apk`: package `com.halo.decomp.vr`, code 76, version `1.0.31-test64`; signer SHA-256 `53d416f7...8e2aa4` (the project debug key, as Test63)
- `HaloCE-Android-test64.apk`: package `com.halo.decomp`, code 76, version `1.0.31-test64`; signer SHA-256 `53d416f7...8e2aa4` (the project debug key, as Test63)

The package check (`tools/package-quest.py --label test64`) confirmed the
Test64 banner, code 76, the Test64 guide section and the candidate documents
in each APK. `sha256sum -c` passed in the delivery folder.

## Verification

- **Automated (passed):** full regression suite, both native builds, ABI
  lint, package checks, signature and version checks. The crash itself:
  test_test31_vr_menu with the game's seventeen categories fails without the
  fix (AddressSanitizer global-buffer-overflow in `vr_menu_paged`) and
  passes with it.
- **Device (pending):** `TEST64-DEVICE-CHECKLIST.md`, then all of
  `TEST63-DEVICE-CHECKLIST.md` (never reached on the headset: Test63 crashed
  opening VR SETTINGS).

No push, publish, tag, install or launch. No network protocol or voice code
change.
