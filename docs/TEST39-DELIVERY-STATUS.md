# Test39 implementation and validation status

## Candidate identity

Private **1.0.20-test39 / Android code50**, based on Test38 and OpenCE Build157 /
network24. Public v1.0.18 remains the accepted/public baseline. Packaging is
for owner testing only. No public push, tag, release, install or game launch is
authorized. PC/Steam Frame work remains deferred.

## Completed in source for this pass

| Request | Implementation and limit |
|---|---|
| Shake overheated weapon to cool faster | New VR-only **SHAKE COOLING** OFF/ON setting, default OFF; solo connection and valid VR hand/controller required. Only the selected held weapon is affected and only while native overheated state is set. Two valid direction reversals within 0.5 seconds reject one-way/head motion and single accidental movement; the rolling signal decays over time and multiplier is bounded to 1–2.5x. Native heat recovery and thresholds remain in charge. Automatically returns 1x online. |
| Make shake cooling a toggle | Added as an explicit OFF/ON row in the existing VR Controls settings menu; stored in `vr.cooldown_shake`. |
| Continuous weight haptics | New **WEIGHT HAPTICS** OFF/ON setting, default OFF; local/offline only, refreshed every 120 ms per hand for a sustained sensation and amplitude capped at 0.24. The signal estimates solver resistance/strain/speed and is not physical mass or remote force feedback. State resets clear haptic timers. |
| Custom scenery | New opt-in toggle allows otherwise unnamed scenery only through the existing strict collision-model/OBB bounds and movement constraints. Animated, scripted, malformed, structural and unsafe entities remain excluded. |
| Custom NPC rigs | New opt-in admits only the actor-assassin enum, which the source maps to the native Elite rig family, and still requires successful native graph/node validation. It is not a general custom-skeleton loader. |
| Enhanced co-op above four peers | Host world-object permission now accepts all connected machines within the native 128-machine table, requiring every peer's capability lease. Client inputs are paced at 20 Hz while held and 4 Hz released; duplicate host results are not re-sent each simulation tick. The protocol keeps the old Test38 v1 boolean confirmation and adds a separate NPC-budget confirmation. |
| Preserve bounded NPC co-op | Articulated NPC interaction/palette packets stay limited to four remote machines and are refused above that count; world-object interactions can remain negotiated. Normal OpenCE co-op is not capped or modified by this optional channel. |
| Reset behavior | Interaction/session reset clears the per-hand weight-haptic cadence. All new settings default OFF, and online gates fail closed for solo-only effects. |

The supplied Halo CE Combat Evolved VR / Open CE Port logo is now used for
both the Quest and Android adaptive launcher icons. The full artwork is
included in the generated Android icon resources; it does not change game
runtime or user settings.

## Preserved from Test38

Test38's scope profiles, vehicle/turret reticle behavior, reload profiles,
hands/contact, loose props, NPC/ragdoll solver, impact authority, close-contact
and vehicle-control work were carried forward without changing their design.
The prior seven reload profiles use native ammo commits; normal reload stays
available. World/NPC network interactions still require explicit host
permission and protocol negotiation. Read TEST38-DELIVERY-STATUS.md for that
candidate's full implementation record; read its device checklist for original
physical validation steps.

## Explicitly incomplete or restricted

- Manual reload remains solo-only. There is no negotiated reload phase,
  authoritative magazine/ammo transaction, or cancellation protocol for
  unmodified peers. Native reload remains the online path.
- Parkour remains solo-only. The local movement/collision impulse does not
  become host-authoritative movement for mixed clients.
- NPC articulated interaction remains at four remote machines. The higher
  negotiated peer count applies to bounded world-object interaction only.
- A 128-machine transport ceiling is not evidence that campaign is stable at
  128 players. This candidate does not change campaign player count. Full
  campaign capacity still requires specific roster, saved-unit/recovery,
  spawn-space, checkpoint, AI, vehicle, script, transition and device evidence.
- Custom NPC rigs are limited to the validated alternate Elite actor enum;
  arbitrary rig maps are not implemented.
- Custom scenery is opt-in and bounded. It is not a universal physics engine.
- Discarded magazines do not persist as independent physical ammo objects.
- Whole-vehicle lifting and generic vehicle physics are not implemented;
  virtual steering wheels/handles are a separate, existing control feature.
- Automatic mission-critical NPC rescue is not implemented. Only existing
  validated local recovery paths remain.
- PC/Steam Frame work is deferred.

These limits preserve native behavior where the required game/network state
cannot be safely established. Do not describe them as finished or universally
compatible.

## Tests and acceptance

Completed before delivery:

- All **84 regression suites** in `tools/run-quest-checks.py` passed under WSL
  clang/JDK, including a second clean run inside each flavor build.
- Cache-format pytest: **127 passed, 4 optional real-map fixtures skipped**.
- Quest and flat Android native/Gradle builds both completed with the supplied
  launcher logo. All 84 regression suites passed in the VR and flat build
  workflows. A clean Gradle assembly was required after the package gate caught
  stale unindexed bytes in incremental APK output; those rejected APKs were not
  packaged or delivered.
- The final `package-quest.py` run passed certificate, package/version, arm64,
  guide and license, OpenXR/touch flavor separation, networking parity,
  APK ZIP/orphan data, required marker, and source/build archive checks. Both
  APKs carry the established certificate SHA-256
  `53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.
  Final sizes and hashes are in [TEST39-DELIVERY.md](TEST39-DELIVERY.md).
- Focused host-sanitizer tests cover input pacing, the 128-machine negotiation
  ceiling, old-peer confirmation compatibility, NPC gating above four, finite
  shake math, capped weight feedback and safe reset behavior.

Build/package checks are not headset acceptance.

No real Quest/Android session, cross-device co-op session, 128-peer simulation,
long campaign or heat-weapon gameplay test is recorded yet. Keep `runtime_accepted`
false in the candidate manifest until the owner tests it. Complete
TEST39-DEVICE-CHECKLIST.md after testing; don't mark skipped tests passed.
