# Test46 private candidate delivery status

Candidate **1.0.27-test46 / Android code57** on
`test39-interaction-completion`. This is a private owner-test candidate. Keep
public v1.0.18 and all older candidate/release assets unchanged; do not publish.

## Work carried into this candidate

- Carries forward the full Test45 candidate and the accepted Test44 behavior:
  launcher/imported game-data management, network selection and in-game
  browser, touch preset export/import and per-control hide, calibration reticle
  tracking, Safe Geometry defaults, co-op, controllers, scopes, vehicle/turret
  controls, logs, manual reload, parkour, hands, NPC/object interactions,
  haptics, holsters, shake cooling and their documented compatibility gates.
- Includes the post-Test45 source follow-ups for same-map discarded-magazine
  visual retention and bounded, contact-driven translation/orientation of
  eligible unoccupied ground vehicles. Both are now in the candidate source;
  their in-game movement and lifecycle still need Quest acceptance.
- Fixes the NPC rescue eligibility check to use the real
  `script_state_resumable` field. A source audit found and removed a stale
  nonexistent-field reference; the focused production-source test now guards
  this predicate.
- Integrates Build167 host-relayed Opus voice on optional protocol messages
  80-82, without changing Build157/network24. Android declares
  `RECORD_AUDIO`; permission is requested asynchronously only when voice
  transmit is enabled and active. VR exposes Off/PTT/Open Mic, controller PTT
  binding and 0-200% receive volume. Permission denial waits for an explicit
  voice-mode cycle; transient recording-device open errors retry after ten
  seconds. The device test record distinguishes these from a successful live
  voice session.

## Build and artifact record

This section is completed only after both final APKs are rebuilt from the same
committed source, checked by `tools/package-quest.py`, and packaged with their
matching source/build ZIPs. Final source commit, APK sizes and SHA-256 values
will be recorded here. No APK installation, game launch or public release is
part of this task.

## Validation boundary and known limits

- Source fixtures and host builds do not prove Quest hand feel, NPC recovery,
  magazine retention, vehicle collision/release, microphone permission UI,
  audio-device routing or two-client voice. These have explicit steps in
  `TEST46-DEVICE-CHECKLIST.md` and `TEST46-VOICE-CHAT.md`.
- Physical interaction options retain their documented solo-only or
  capability/host-gated behavior. Unsupported rigs, arbitrary scenery,
  unvalidated vehicle classes, network vehicle lifting, save-file/networked
  magazine objects and universal arbitrary-rig retargeting remain unsupported.
- Campaign player-count options remain OpenCE's. The 128-machine transport
  table is not verified 128-player campaign support. Enhanced world-object
  interactions can negotiate above four remote peers with unanimous support;
  articulated NPC pose sync remains limited to four remote peers. Manual reload
  and parkour remain solo-only.
- Halo's native ragdoll eligibility and corpse cleanup are retained; the mod's
  `NPC RIG SLOTS` does not raise an undocumented native corpse cap.
- Flat Android supports keyboard PTT or Open Mic; this candidate has no
  dedicated touch/gamepad PTT control. A per-player mute state helper exists,
  but there is no scoreboard control wired to it in this candidate; global
  receive volume zero mutes all remote voices.
- PC and Steam Frame work remains deferred. Live headset, campaign and network
  acceptance remains pending the owner's test.
