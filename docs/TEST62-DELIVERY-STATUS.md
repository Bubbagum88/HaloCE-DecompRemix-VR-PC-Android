# Test62 delivery record

**Private candidate: 1.0.29-test62 / Android version code 74.**
Branch: `test39-interaction-completion`.
Baseline: Test61 `ccb380e5`, delivery record `23dd309f`, impact fallback
`4ed9b8f3`.

## Public baseline

The 2026-10-12 live
[latest-release check](https://github.com/moistman42069/HaloCE-Quest-VR/releases/latest)
resolves to [v1.0.18](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.18)
(network24/code48), matching local peeled tag `3867cd0e`. The v1.0.19 attempt
is withdrawn/cancelled, not the current baseline. Test62 remains private.

## Current state

Implementation review, all 125 suites in each flavor build run, both native builds, compiled Opus-table checks and guest ABI checks passed. The extra package-metadata suite passed five cases and is registered for future runs. Final packaging/hashes are pending in this immutable source snapshot; the finished manifest and final delivery record beside the APKs provide them. Device testing is pending. No files have been pushed, tagged, published, installed or launched as part of Test62.

- Final source commit: pending.
- VR APK path, size and SHA-256: pending.
- Flat APK path, size and SHA-256: pending.
- Matching source archive/path and hash: pending.
- Cache-format pytest: **127 passed, 4 skipped** (`D:\HaloQuest\_scratch\pytest62.log`); skips are absent optional real custom-map fixtures, not evidence of SPV1 support.
- Full-suite result: **125 suites passed for VR and 125 for flat**, `Failed suites: []` in `D:\HaloQuest\_scratch\build62-vr.log` and `build62-flat.log`; package-metadata suite separately **5 passed**.
- VR/flat native build: **both passed**, including compiled-image Opus and guest ABI gates; logs above.
- Package manifest, version/name/code, signing certificate and hash checks:
  pending.
- Owner headset/phone acceptance and paired co-op: pending.

Expected retained signing certificate SHA-256:
`53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
Record verification from the finished APKs; do not infer it from a keystore
filename.

## Scope and limitations

See [TEST62-CHECKLIST.md](TEST62-CHECKLIST.md) for every request and its
evidence, [TEST62-FIELD-GUIDE.md](TEST62-FIELD-GUIDE.md) for controls/settings,
and [TEST62-DEVICE-CHECKLIST.md](TEST62-DEVICE-CHECKLIST.md) for device tests.

This candidate includes original vehicle/grab/slam refinements plus reload
feedback, parkour defaults, optional assisted fist combat and chest grenades,
scope attachment/shared aim steadying and guarded host permissions. The
native damage wrapper now retains real shield depletion and adds authored
body/material art only after body damage; its automated regression results passed. Experimental actions remain off by default. Existing local-only
restrictions and the four-remote-machine NPC pose budget remain. No voice or network
protocol implementation changes; PC/Steam Frame deferred. Automated results
do not establish complete runtime compatibility or performance.
