# Test62 delivery record

Private owner-test candidate **1.0.29-test62 / Android version code 74**.
Built and packaged on 2026-10-12. **Device acceptance is pending.**
No push, tag, release, install or game launch was performed.

## Artifacts and source

- Folder: `D:\HaloQuest\builds\test62-20261012-v1.0.29-test62`
- Exact source of both APKs and source archive: `ed60571ff85eaacbfe178cc98872d603bad32085`.
- Branch: `test39-interaction-completion`.
- Baseline: Test61 `ccb380e5`, record `23dd309f`, Test62 initial impact fallback `4ed9b8f3`.
- Packages: `com.halo.decomp.vr` and `com.halo.decomp`; both code74, min SDK28.
- Install as an update over Test61/earlier; do not uninstall first. Package names
  and the signing identity are retained so application data can be preserved.
- Certificate SHA-256 (verified in each APK): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
- WSL Ubuntu 24.04; clang18 guest; NDK27.2.12479018; Android build-tools36.0.0.
- Network/voice implementations preserved: host28, compatible joins11..28 under
  existing rules. Default selector target is **0 / All compatible**. No protocol change.

| File | Bytes | SHA-256 |
|---|---:|---|
| HaloCE-Quest-VR-test62.apk | 36154554 | `07bf30d33deae3a132096c45f8609df37a8a25268779adfc8923fe3eb4c3ed26` |
| HaloCE-Android-test62.apk | 33892275 | `46059ce304f5e0e9657674baac257363a09fc8149642f9c9e9a99475e279b72d` |
| HaloCE-Quest-test62-source.zip | 23013951 | `5a5c1c5eb25b5768455276feafc353c94822ed07bcc177fcff01505011bb316c` |
| HaloCE-Quest-test62-build.zip | 33866360 | `0952f62f19cd0ef40485837f253ab46a715f380a5a5ff8e1a6f81d1e083e9ac6` |
| manifest.json | 2638 | `c991bafcccd7c0e991a0e75754ad923f195c372564770a6ed6fc3404e5205ff9` |
| compatibility.json | 837 | `e542edfe099afd0641e52a2212dc362aaa226838cfc5ec5fac1bbbfb102f2e11` |

The ZIPs are immutable snapshots of the source commit above, including its
pre-package status document. This later delivery record supplies completed
verification and final hashes; it changes no runtime source or APK. A copy is
beside the APKs. The source archive ZIP comment matches the source commit.

## Completed verification

- Both `tools/build-quest.sh` flavor runs passed all **125 suites** registered
  when those runs began (`Failed suites: []`). Logs:
  `D:\HaloQuest\_scratch\build62-vr.log` and `build62-flat.log`.
- The additional `test_package_candidate_metadata.py` suite passed **5 tests**
  separately and is registered for future full runs (126 suites total).
- Cache-format pytest: **127 passed, 4 skipped**; `D:\HaloQuest\_scratch\pytest62.log`.
  Skips are absent optional custom-map fixtures, not SPV1/custom-map validation.
- After both native builds: compiled Opus pulse-cache tables exactly matched
  vendored source; all direct guest calls matched definitions across 717
  game/port/library and 924 musl units. Correct variadic declarations were
  also checked for new impact diagnostics; no voice edits were necessary.
- Production-function sanitizer fixtures cover the new grenade/combat
  state machine and native projectile transaction, actual NPC readiness and
  simulation authority, restrained/stunned melee, native shield/body effect
  selection, scope anchoring and reload/grenade event-haptic priority.
- Native-menu tests include real construction, startup/unload/reload,
  allocation-failure recovery, pointer/settings wiring and all 51 XML assets.
- `tools/package-quest.py --label test62`: original certificate, package names,
  ABI, version/code, networking parity, icon/guide/launcher assets, required
  feature identities, ZIP layout and checksum checks all passed.
- `D:\HaloQuest\_scratch\verify62.py`: independently verified both APKs,
  original signatures, embedded guest/guide contents, exact source-commit
  files, all four Test62 documents inside the build ZIP, manifest target0,
  source/build ZIP CRCs and every `SHA256SUMS.txt` entry.
- The completed Quest APK hash stayed unchanged while the flat flavor built.
- Final packaging did not include game maps, ISOs or signing keys.

## What changed

- Seat-eye settling before immersive control measurement (3 s cap), all-vehicle
  offsets and reachable controls; preserved native view/steering paths.
- Modest default body-contact assist; stationary one-hand living Elite/Hunter
  restraint, second-hand lift, one-hand corpses and native recovery.
- Campaign slam damage fallback/configured floor threshold; real shield
  depletion/body-material effects; 60 m death range and guarded existing solver.
- Reload magazine palm alignment and protected insertion/charging feedback;
  parkour contact/default refinements; final-wrist scope anchor and optional
  shared angular aim steadying.
- Optional enemy-only fist assistance, bounded approach/combo restraint/stun,
  native damage and procedural feedback; optional adjustable physical chest
  grenades with native counts/projectiles and safe cancellation.
- HOST VR ACTIONS in native co-op setup, existing capability gates and explicit
  host-only NPC simulation. Ready clients still submit requests/display host poses.
- Lifecycle/ownership/collision/input checks, complete request ledger and current
  guides; corrected package guide inclusion and default-network metadata.

## Boundaries and next device tests

Read [TEST62-CHECKLIST.md](TEST62-CHECKLIST.md) for full request accounting,
[TEST62-FIELD-GUIDE.md](TEST62-FIELD-GUIDE.md) for controls/settings and
[TEST62-DEVICE-CHECKLIST.md](TEST62-DEVICE-CHECKLIST.md) for the owner checks.

The new combat/grenade options start OFF and are experimental. Combat uses a
renewable two-second target restraint/native-collision approach and procedural
hit/stun reactions; no choreographed finisher or magnetic camera attachment.
The tested parent-relative ragdoll solver was refined; no Euphoria engine,
active-balance system or unvalidated solver replacement was added.

Manual reload/custom-rig fallback/magazine debris remain local-only. New fist
and chest actions allow local play or a permitted compatible co-op host, not
PvP or remote clients. Existing NPC pose sync supports four remote machines;
ordinary co-op capacity is unchanged. PC/Steam Frame remains deferred.

Saved choices are preserved: select GRAB ASSIST 5 CM, CLIMB GRAB 14 CM or
WALL TIME 2 S manually if older values remain. Check vehicles, heavy grabs,
shield/body slams, reload pulses, chest throws, combo comfort, scopes, and
baseline holster/drop/haptics/touch/join/voice behavior on devices. Test host
and client together. Automated tests cannot certify tracking feel, all maps,
all revisions, every server or sustained headset performance.

## Public baseline

The live 2026-10-12 latest-release check resolved to
[v1.0.18](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.18),
network24/code48, matching local peeled tag `3867cd0e`. The withdrawn v1.0.19
attempt remains history. This Test62 pair is private and does not change any
public release or the public README/About presentation.
