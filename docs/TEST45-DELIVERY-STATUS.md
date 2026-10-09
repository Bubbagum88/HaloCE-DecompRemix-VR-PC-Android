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

Update this section after the two edition builds and package gate complete.
Automated source tests cannot establish Quest contact feel, AI behavior, or
live co-op results. No APK install, game launch or public release is part of
this task.
