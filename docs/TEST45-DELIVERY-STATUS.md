# Test45 delivery status

Candidate **1.0.26-test45 / Android code56** on branch
`test39-interaction-completion`. Test44 and all older candidate artifacts,
plus public v1.0.18, remain preserved. This is a private testing candidate;
do not publish it.

## Scope

- Keeps all accepted Test44 launcher, ISO/XISO, A10 calibration, Android touch,
  VR settings, network and gameplay behavior.
- Removes ordinary hand-distance and pose-jump release triggers from held local
  NPCs, world objects and host-authoritative remote props. A held target follows
  a bounded per-step hand target; a tracking discontinuity resets throw velocity
  instead of dropping the interaction.
- Lets supported friendly campaign actors with ordinary AI command lists be
  held while only their transient movement/trigger controls are suppressed.
  Actor team, orders and command-list data remain native. Forced immediate
  orders and unsafe animation/weapon states remain ineligible.
- Restores the missing OpenCE Build167 teamplay settings overlay for voice
  routing, lobby voice, bitrate and proximity. This supplies menu widgets only;
  it does not by itself establish working microphone or network audio.
- Integrates the selected Build167 host-relayed Opus voice path, Android
  recording bridge, client microphone/receive-volume settings and VR controller
  PTT mapping. Microphone transmit defaults Off. Source-level wiring is checked;
  Quest/Android runtime audio and two-client sessions remain unverified.
- Adds explicit acquisition, hold-start, tracking-rebase, constraint-strain,
  and release/cancellation-reason diagnostics.

## Validation record

Both APK flavors were built from source commit `c34b74d6` with
`tools/build-quest.sh`. Each flavor build ran the full
`tools/run-quest-checks.py` suite; all suites passed, including voice-chat
integration/protocol coverage, NPC/ally interaction, physics, reload, parkour,
vehicle, launcher, network and Android input checks. The VR APK initially
exposed a missing include for the production sprint math helper at link time;
that source omission was fixed and guarded by `test_quest_vr_math.py` before
both final builds.

`aapt dump badging` confirms the flat package `com.halo.decomp` and VR package
`com.halo.decomp.vr`, both version code 56 / version `1.0.26-test45`, arm64-v8a.
Both APKs declare `android.permission.RECORD_AUDIO`. `apksigner verify` passes
for both, with certificate SHA-256
`53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.

| Flavor | Size | SHA-256 |
|---|---:|---|
| Android / flat | 33,775,643 bytes | `9ea69422313d04acd042285c4016fa0a7fb9f2ce69cbc3e3861c9dce935e52c2` |
| Quest / VR | 35,952,150 bytes | `9d349f2293be67d83e98697a571fa748506d7a6581e0f60067f9d0a065d01c7d` |

The build environment has Clang 18; its PGO profiles require Clang 22, so both
flavors were built without profile-guided optimization. This is a performance
optimization omission, not a build or link failure.

No APK was installed and no game was launched. Quest contact feel, ally AI
behavior, microphone permission UI, capture/playback routing, voice chat with a
second client, and live co-op remain unverified until device testing. These
limitations are not represented as passed tests; use
`TEST45-DEVICE-CHECKLIST.md` for acceptance steps. The candidate remains
private and the public release is unchanged.
