# Test65 delivery status

Private **1.0.32-test65 / Android code77**, branch
`test39-interaction-completion`, built on Test64 / public 1.0.31
(`21b5c988`). Scope and evidence: `TEST65-CHECKLIST.md`; what to try:
`TEST65-DEVICE-CHECKLIST.md`.

## Artifacts

Folder: `D:\HaloQuest\builds\test65-20261013-v1.0.32-test65`
APK source commit: `098a5a9182095b293f8243736da70f7478e072c1` (both flavors built from this exact tree, in WSL
with clang 18; the full regression suite ran before each flavor build with
`Failed suites: []`; the guest ABI lint passed).

| File | SHA-256 |
|---|---|
| `HaloCE-Quest-VR-test65.apk` | `9bf6affc07377d37ea3696a95dd1c4a48b28e2b0baf1f3bbf318551e854a88c4` |
| `HaloCE-Android-test65.apk` | `08d68984c099c80078589d02d173cce2f0024be48cf81b7e4a2d1cbd77162b17` |
| `HaloCE-Quest-test65-source.zip` | `45c0d87289afe642221744ad1251565114d17ed54a32d8a3feae89d04e68f534` |
| `HaloCE-Quest-test65-build.zip` | `d6bf9cc989af394f873325482b31721c08d6326a696d5ac13aec7a8f53200bec` |
| `manifest.json` | `0049e83858ef251692fbdf1d8fbd29d2485bd666a095187ea66d7bb8cce33711` |
| `compatibility.json` | `63c5ddbcdd4e9eab7bf80f40aff4e7a60565c00302f8fe30e5baf7055901ea70` |

- `HaloCE-Quest-VR-test65.apk`: package `com.halo.decomp.vr`, code 77, version `1.0.32-test65`; signer SHA-256 `53d416f7...8e2aa4` (the project debug key, as Test64)
- `HaloCE-Android-test65.apk`: package `com.halo.decomp`, code 77, version `1.0.32-test65`; signer SHA-256 `53d416f7...8e2aa4` (the project debug key, as Test64)

The package check (`tools/package-quest.py --label test65`) confirmed the
Test65 banner, code 77, the Test65 guide section and the candidate documents
in each APK. `sha256sum -c` passed in the delivery folder.

## Verification

- **Automated (passed):** full regression suite (including test_test65 and
  the updated test_test62_extra combat harness, which runs a fist tick before
  the frame's head view exists), both native builds, ABI lint, package
  checks, signature and version checks.
- **Device (pending):** `TEST65-DEVICE-CHECKLIST.md`, plus
  `TEST64-DEVICE-CHECKLIST.md` and `TEST63-DEVICE-CHECKLIST.md` (none of
  them confirmed on a headset yet).

## Dual wield: not implemented, design for a later build

Halo CE's player fires only the weapon in hand: the other inventory weapons
are disconnected from the world and hidden, are not updated, aimed or drawn
in first person, and the network carries one firing weapon per unit. A real
second gun therefore needs, in a later build: the second weapon kept
attached and updated (heat, ammo, triggers) beside the current one; its own
aim from the off hand's pose; its first-person model drawn in the off hand;
the off-hand trigger routed to it; and a local/solo-only gate (or a protocol
extension) for multiplayer. A suggested entry: hold a pickup with the off
hand while armed and a DUAL WIELD prompt appears. Nothing of this is in
Test65; no stub or toggle was added.

No push, publish, tag, install or launch. No network protocol or voice code
change.
