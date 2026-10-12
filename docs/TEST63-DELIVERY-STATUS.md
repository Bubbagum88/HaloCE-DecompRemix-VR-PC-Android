# Test63 delivery status

Private **1.0.30-test63 / Android code75**, branch
`test39-interaction-completion`, continuing Test62 (`ed60571f`).

## Artifacts

Folder: `D:\HaloQuest\builds\test63-20261012-v1.0.30-test63`
APK source commit: `e2849e9b4effc9b1dab195bda0217e3aeabaf30e` (both flavors built from this exact tree, in WSL
with clang 18 as in v1.0.18; the full regression suite ran before each flavor
build with `Failed suites: []`; the guest ABI lint passed).

| File | SHA-256 |
|---|---|
| `HaloCE-Quest-VR-test63.apk` | `3880c7b96a29fcfa3da44cae917fde0b48a294600e7837d2ba7221db1a809747` |
| `HaloCE-Android-test63.apk` | `0026d5ea0068e17bec4bd38b47b8e8d2cc132b82fb0220a79e222c53680a1ea2` |
| `HaloCE-Quest-test63-source.zip` | `b2fd8a31768bdbae6fc90833713fdb05d35509b2ff19223d99bc0ac5bf56e7b0` |
| `HaloCE-Quest-test63-build.zip` | `5ccb016941bbc3f3fe4c15d1fdd43c22e20654aa58bbeb31a8ab53e0bfd818b5` |
| `manifest.json` | `b8851e4048e0491264b05cdd2c4135ec3e694954a586ef6b762d779409b93b1f` |
| `compatibility.json` | `15cc54db58a84fad3012965dd393308708494bd4fccf304abe33863d90ead5b9` |

- `HaloCE-Quest-VR-test63.apk`: package `com.halo.decomp.vr`, code 75, version `1.0.30-test63`; signer SHA-256 `53d416f7...8e2aa4` (the project debug key, as Test62)
- `HaloCE-Android-test63.apk`: package `com.halo.decomp`, code 75, version `1.0.30-test63`; signer SHA-256 `53d416f7...8e2aa4` (the project debug key, as Test62)

The package check (`tools/package-quest.py --label test63`) confirmed the
Test63 banner, code 75, the Test63 guide sections and the candidate
documents in each APK, so neither APK is stale. `sha256sum -c` passed in the
delivery folder.

## Verification

- **Automated (passed):** full regression suite (127 suites, including
  test_test63, test_test62_extra, the vehicle, menu, NPC, world, reload,
  parkour, network and voice suites), both native builds, ABI lint, package
  checks, signature and version checks.
- **Device (pending):** nothing in Test63 has been tried in the headset or
  on a phone. Use `TEST63-DEVICE-CHECKLIST.md`.

No push, publish, tag, install or launch. No network protocol or voice code
change. PC/Steam Frame deferred.
