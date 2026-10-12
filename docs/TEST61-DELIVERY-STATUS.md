# Test61 delivery record

Private owner-test candidate **1.0.28-test61 / Android version code 73**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test61-20261012-v1.0.28-test61`
- Source of both APKs: commit `ccb380e5481d0f5b6a9892915acab6e556c6d183`
  (branch `test39-interaction-completion`): the Test61 changes (`0cc1ec73`
  immersive controls held under the hands, IMMERSIVE VEHICLE → FIRST PERSON
  and the other settings that come on together, impacts with the unarmed
  blow, 24 rig slots, one-hand corpses, the menu-held reload, identity and
  docs) on the Test60 delivery, plus the bundled guide files the build
  generated from them. Later commits change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test60 (code 72) and earlier, keeping settings, saves and
  game data.
- Network: unchanged from Test59. Hosts OpenCE network 28; joins 11-28
  (manifest `native_host_version` 28, compatibility 11..28). The larger
  rig-slot pool is local; snapshots carry unit indexes, not slots.
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test61.apk | `309986310e1269e23f4bfd00193372dd413f49524fbdee54909a3d58b1ab6e67` |
| HaloCE-Android-test61.apk | `b691e37bea4d649837bbbcae78e920c4213defd1821e9551f320ef63c0e65a10` |
| HaloCE-Quest-test61-source.zip | `6c81567c3f66f5840b21ba75365eced73adde62dcdf83762ddc1da5d3db586ad` |
| HaloCE-Quest-test61-build.zip | `897dffa8f3403fd566e76cde4052c9684120dbdecb1ea55eb27cc0410b4941b4` |
| manifest.json | `079183299e9f51c763f028a65b453eab9040e3efdfee6eb63a417cd52b6b505a` |
| compatibility.json | `394a4c8a14dfa26e75ecb30e55807cd6a939929f9ec164652d6703b1929ccc3c` |

Guest images: `1bc85cc3…826b`, `aefaef38…e86b`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, including the new
  `test_test61_vehicle_hold` and `test_test61_fixes`): **Failed suites: []**
  inside each flavor's `tools/build-quest.sh` (VR and flat). A stand-alone
  run before them found tests that pinned the old placement or interfaces
  (`test_test57_vehicles`, `test_test57b_vehicle_anchor`, `test_test22`,
  `test_interaction_lifecycle`, `test_vr_npc_interaction`, `test_test20d`),
  updated to the new behaviour before the builds.
- `test_test61_vehicle_hold` compiles the real placement: 40 random pitches
  and rolls move neither the wheel nor the turn a still hand reads; the
  Warthog's wheel stays at COMFORT REACH and is never thrown to the chest.
  `test_test22`: with the controls up, a leaning head marker moves the seat's
  eyes not at all. `test_test57b`: every control on its vehicle at boarding
  at 5 places, headings and tilts.
- `test_interaction_impact` runs the real impact transaction with a unit
  that has no melee damage of its own: the unarmed blow lands; with no blow
  at all nothing is damaged.
- `test_test60_toggles` runs the real resolver: IMMERSIVE VEHICLE ↔ FIRST
  PERSON, TANK HATCH/HOG GLASS, pouches, SPRINT TOGGLE, CUSTOM NPC RIGS and
  CUSTOM SCENERY (released with their grab, not holding it on).
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee.
- `tools/package-quest.py --label test61`: certificate, package names, ABI,
  version 1.0.28-test61 / code 73, networking parity, ZIP integrity,
  launcher assets, bundled Test61 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.

## Boundary

Host checks and builds do not prove headset behaviour:
[TEST61-DEVICE-CHECKLIST.md](TEST61-DEVICE-CHECKLIST.md),
[TEST61-CHECKLIST.md](TEST61-CHECKLIST.md).
