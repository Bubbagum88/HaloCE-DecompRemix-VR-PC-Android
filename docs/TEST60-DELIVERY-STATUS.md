# Test60 delivery record

Private owner-test candidate **1.0.27-test60 / Android version code 72**.
Not a release: nothing was pushed, tagged, published, installed or launched.

- Folder: `<artifacts>\test60-20261012-v1.0.27-test60`
- Source of both APKs: commit `8da4673ade1818e51bc55f6e0c6bf6a87c09b308`
  (branch `test39-interaction-completion`): the Test60 changes (`e2769e90`
  impacts for every NPC, settings that come on together, identity and docs)
  on the Test59 delivery, plus the bundled guide file the build generated
  from them. Later commits change only docs.
- Signing certificate SHA-256 (both): `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`
- Packages: `com.halo.decomp.vr` (Quest VR), `com.halo.decomp` (Android);
  installs over Test59 (code 71) and earlier, keeping settings, saves and
  game data.
- Network: unchanged from Test59. Hosts OpenCE network 28; joins 11-28
  (manifest `native_host_version` 28, compatibility 11..28).
- Toolchain: WSL Ubuntu 24.04, clang 18 guest, NDK 27.2.12479018,
  build-tools 36.0.0.

| File | SHA-256 |
|---|---|
| HaloCE-Quest-VR-test60.apk | `8252dafaece1feac76e8fb69409680c4bb66670d389cd9a4a27a3fc98afa1a51` |
| HaloCE-Android-test60.apk | `49c3b28f542653bdf560663411b0f600a185a5c8b8e2ebcdd452c9db3412d59b` |
| HaloCE-Quest-test60-source.zip | `dc8349e6f24f92526e4b861c9f9fb004214540123a875f692d5bd143dd03eade` |
| HaloCE-Quest-test60-build.zip | `d0a9d70fc0a426a84dfa08f9f4e6c2383673f972b98a19a3a66f2a383b6a5e87` |
| manifest.json | `ff19ddef4d69dec40712b8be22b08116228bc71c8adbb81746e6c3229c16fb83` |
| compatibility.json | `59ea34bf0c87cbd334d51dba2e69e216bdc20a6489b2773ea55fd8d459c9f153` |

Guest images: `406ad0bc…70ce`, `b78b7d1b…a3c6`.

## Checks

- Full regression suite (`tools/run-quest-checks.py`, including the new
  `test_test60_toggles` and the extended `test_test56_ragdoll`): **Failed
  suites: []** stand-alone and inside each flavor's
  `tools/build-quest.sh` (VR and flat).
- `test_test60_toggles` compiles the real menu dependency resolver: DEATH
  RAGDOLLS turns on NPC GRAB, NPC RESCUE, IMPACT DAMAGE (and FIST REQUIRED
  through NPC GRAB); a requirement turned off by hand stays off; turning
  the feature off releases what it turned on but not what was chosen by
  hand; NPC GRAB alone and the vehicle refinements; hard rows unchanged.
- `test_test56_ragdoll` adds the impact probe: a glancing 27 m/s slam onto
  the floor counts, a 1 m/s touch does not, a fast joint stops at another
  body and reports it, a player's body is passed through, nothing fires
  with impacts disabled; all 12 stock skeletons still settle.
- After each flavor's build: Opus pulse-cache tables match the source; every
  direct guest call matches its callee.
- `tools/package-quest.py --label test60`: certificate, package names, ABI,
  version 1.0.27-test60 / code 72, networking parity, ZIP integrity,
  launcher assets, bundled Test60 guide markers, VR identity banner.
- `sha256sum -c SHA256SUMS.txt`: all OK; `apksigner` and `aapt` re-checked.

## Boundary

Host checks and builds do not prove headset behaviour:
[TEST60-DEVICE-CHECKLIST.md](TEST60-DEVICE-CHECKLIST.md),
[TEST60-CHECKLIST.md](TEST60-CHECKLIST.md).
