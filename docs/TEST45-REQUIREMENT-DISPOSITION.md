# Test45 requirement disposition

Test45 is focused on the supplied grab/contact report and the added request to
grab allies as well as enemies. It carries Test44 and earlier features forward.

| Requirement | Test45 implementation | Evidence and boundary |
|---|---|---|
| Actual contact followed by a fresh press | NPC/enemy/ally and prop acquisition use the tracked palm-volume overlap against the target's authored collision model. Climbing overlaps solid surface collision. Magazine/pouch and wheel interactions use their documented authored or virtual contact volume. A new Grip/configured-input edge is required; a ray cannot acquire. | Production-source harnesses and source guards cover local, host-validated co-op, world props, reload, climbing and handles. The Quest checklist still requires touch-first and press-first negative/positive cases. |
| Keep an NPC attached while Grip stays down | Ordinary hand displacement and hand-to-joint separation no longer clear the held state. The target follows through bounded per-step movement. A large tracking sample rebases throw velocity to zero. Invalid tracking, lost authority, stale owner/entity, unsafe target state and explicit Grip release remain logged exits. | `test_vr_npc_interaction.py` exercises the production target-follow helper and checks the former release thresholds are absent. Video/log evidence does not include a clear held-target release reason; a Quest retest is needed. |
| Keep held local/remote props attached | Local and remote props likewise remain owned through ordinary distance/strain. Remote target movement is rate-limited on the host; large samples cannot teleport the object or clear the grip. | Production release/remote host-oracle tests; the host collision stub is not the retail engine collision implementation. |
| Allow allies as well as enemies | Existing supported profiles include Grunts, Jackals, Marines, crew, Elites, Combat Forms, Hunters and Carrier Forms. A friendly living actor with a non-immediate command list may now be held; only transient control inputs are suppressed while its original team/orders/command data remain intact. Immediate forced orders, unsafe states and unsupported rigs stay blocked. | Production `eligible()` fixture covers friendly Marine and crew with ordinary orders, immediate-order rejection, enemy script rejection and preserved enemy-type coverage. Actual campaign actor behavior needs Quest verification. |
| Ragdoll retention | Grabbed dead actors continue through the existing articulated settle/recovery path; on settling, native corpse physics resumes. Halo's normal object/memory cleanup remains authoritative. | Source lifecycle and existing regression fixtures pass; no supplied capture proves the reported disappearance or tests long-term corpse retention. No native corpse cleanup policy was changed. |
| Selected Build167 voice chat | Host-relayed Opus voice uses optional network messages 80-82 without changing network24. Android declares recording permission; capture opens only for an enabled transmit mode when the host permits voice. VR offers Off/PTT/Open Mic, receive volume, and a controller PTT binding defaulting to None. Flat Android supports keyboard PTT (V by default) or Open Mic, with no touch/gamepad PTT binding. Host routing/lobby/bitrate/proximity settings use the Build167 menu overlay. | `test_voice_chat_integration.py` checks the source/config/build wiring, permission declaration/audio bridge, routing IDs, PTT/defaults and menus; `test_test31_menu_assets.py` checks embedded host rows/options/pointer input. The scoreboard mute UI is absent; volume 0 silences all incoming voices. Physical mic permission, headset routing, capture/playback and two-peer lobby/match behavior still require Quest testing. |
| Keep existing interactions and platforms stable | No network protocol, Android touch/gamepad, Safe Geometry default, launcher, saves, weapon aim, reload state machine, manual reload, parkour state machine, holster, or rendering defaults are intentionally changed. | Full regression suite and both flavor builds are required before delivery. Device acceptance is pending. |

## Existing scope recorded, not expanded in Test45

The build retains the documented Test38+ manual reload, parkour, arm-run,
physical melee, haptics, holsters, hand compliance, ragdoll handling, scopes,
network gates, co-op and Android features. These are covered by their existing
source fixtures and earlier requirement records; they are not newly validated
on a headset by the Test45 source work. The long supplied video does not provide
a controlled test of every one of those systems.

## Acceptance boundary

Source and host-oracle tests do not substitute for physical Quest testing. See
`TEST45-DEVICE-CHECKLIST.md`; retain the exact APK hashes and source revision in
the final delivery record. The public release remains unchanged.
