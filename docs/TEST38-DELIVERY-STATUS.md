# Test38 private candidate: completion and remaining work

## Packaging authorization

On 2026-10-08 the owner changed the earlier all-features packaging hold: finish
the work already in progress, then package both APKs because of usage limits.
This delivery follows that override. It is a private 1.0.19-test38 / code49
candidate, not a public release. Public v1.0.18 remains the accepted baseline.
No installation, game launch, public push, tag or release is authorized here.

## Implemented in this candidate

| Area | Delivered source behavior |
| --- | --- |
| Scope profiles | All gun classes including SPNKR; native authored zoom retained |
| Mounted reticles | Removed proven target-attraction contribution from preview; native shots and normal guns preserved |
| Manual reload | Seven stock profiles, actual authored parts, insertion/seating/charging where appropriate, native ammo commit, classic cancellation |
| Reload pouches | Independent shoulder/hip toggles; automatically on free-hand side |
| Hand contact | Volume probes, finger search/smoothing, detached-part and held-object contacts, entry haptics, separation limit with coherent arm visibility |
| Loose objects | Arbitrary surface grips, two hands, weight response, throws, native items and eight audited scenery tags |
| NPCs/ragdolls | Eight native species classes, species-dependent one/two-hand requirements, live and identifiable dead bodies, up to four active articulated rigs, collision/self-collision, settling and safe native recovery |
| Impacts | Actual collision-triggered, speed/weight-scaled native damage, ownership, caps, debounce and host authority |
| Co-op interactions | Explicit host permission and negotiated capability; host simulation, remote grip intent, NPC/hand/collision pose synchronization; native fallback for incompatible sessions |
| Closer contact | AUTO with grabbing, adjustable collision radius, occupied-space expansion guard |
| Parkour | Separate solo-only wallrun/walljump/climb toggles and tuning, native capsule collision, look-directed leaps |
| Virtual vehicle controls | Optional vehicle-specific wheel/yoke, independent visibility, per-vehicle position/size, grip-driven steering and normal-input fallback |
| Legacy co-op | Normal campaign admission 15-24; explicit optional 12-14 prefix adapter with old-host limitation warning; host24 unchanged |
| Saves/lifecycle | Transient ownership cleared on relevant resets; prop save freeze; no save-format extension or signing-key change |

Implementation and focused automated evidence are not headset acceptance.
Detailed M1-M29 and W1-W66 dispositions are in
VR-INTERACTION-REQUIREMENTS.md, TEST38-REQUIREMENT-AUDIT.md,
MANUAL-RELOAD.md and WORLD-INTERACTION-STATUS.md.

## Worked through completely as an evidence task

- Compared the three supplied USA Original/Rev1/Rev2 XISOs: all 24 maps are
  byte-identical, and actual production import/detection succeeds. It does not
  prove compatibility with every other ISO or region.
- Identified the mounted reticle preview's target-attraction call and isolated
  its change from native firing and normal handheld reticles.
- Inspected historical campaign schemas and implemented only evidenced layouts.
  Network11 predates OpenCE campaign co-op. Networks12-14 never transmit later
  allegiance state; their opt-in path retains that old-host limitation rather
  than inventing team data.
- Confirmed native scenery co-op synchronization already exists and corrected
  its omission of pure roll changes instead of adding a competing protocol.

## Unfinished / intentionally restricted in this candidate

- Headset and real network acceptance is unfinished for all new physical modes.
- Manual reload and parkour remain solo-only. Online native fallback is
  intentional; shared manual reload/parkour gameplay synchronization is not done.
- Unknown/custom weapon reload rigs and arbitrary custom scenery/NPC rigs have
  no universal physical profile. Battery weapons keep their real native behavior.
- The shotgun physical sequence inserts/pumps one shell at a time. Native
  button reload retains its faster multi-shell sequence.
- Used magazines do not remain as persistent thrown physical world objects.
- Prop collision uses conservative authored bounding boxes; detached parts use
  authored bounds. Neither is a triangle-perfect rigid-body mesh simulation.
- Flying/swarm/unidentified NPC rigs and scripted/protected entities are not
  blindly enabled. Whole-vehicle lifting and unrestricted structural scenery
  manipulation are not implemented; vehicle handles are a separate feature.
- Continuous weight vibration, a visual force/probe overlay, and automatic
  mission-critical NPC rescue have not been implemented. Event/aggregate logs
  and the original physical test checklists are present.
- Enhanced physics is limited to four remote peers to bound pose traffic.
  Larger enhanced sessions need separate performance/network work;
  capability/budget restrictions do not change ordinary native co-op capacity.
- No claim of universal server compatibility, zero clipping, perfect physical
  feel, or regression-free headset behavior is made without the device results.

## Not started in this pass

The optional systems immediately above that lack implementations remain explicit
future work. This pass did not start a new PC/Steam Frame delivery or a relay
service. Quest and Android were the requested build targets.

## Still needs testing on actual devices

1. Baseline VR and Android startup, controls, menus, Safe geometry, saves and
   normal multiplayer with the new modes OFF.
2. Every reload profile with both weapon hands, shoulder/hip toggles, partial
   ammo, cancellation, weapon switching and repeated loads.
3. Stereo hand/finger contact, deeply obstructed arm visibility, frame time and
   comfort during sustained interaction.
4. Each NPC species alive/dead, heavy two-hand requirements, release/impact,
   recovery near obstacles, AI behavior, checkpoints and mission progression.
5. Props against walls/floors/corners and players, throws, save/load and script
   ownership transitions across maps.
6. Quest-host/Android-client and Android-host/Quest-client co-op, both enabled
   peers and an incompatible/stock peer joining or leaving, packet loss and
   reconnects. Also legacy hosts of each admitted network version.
7. Parkour at low frame rates, stairs/corners, jumps/climbs and cancellation.
8. Each vehicle control profile, visibility/offset settings, transitions and
   the reported Shade/Ghost/tank reticle behavior.

TEST38-DEVICE-CHECKLIST.md preserves the original 52 hand/reload and 70 world
interaction checks. None is silently marked passed by a build or fixture.

## Build evidence

All 83 regression suites passed before each flavor build. Cache/tag-format
pytest checks: 131 passed, four skipped. Both native/Gradle builds completed;
the Android Gradle cache journal was repaired and clean assembly repeated.
APK identities, signing certificate and hashes are recorded with the packaged
artifacts. A matching source archive is included.
The packaging manifest's runtime_accepted remains false pending owner testing.

## Reporting

Send version, headset/OS, map/revision, role, settings, reproduction steps,
launch log and video to **@MeWhenINameMyself** or https://discord.gg/S9uSCKxKx.
Do not attach game data, disc images or signing keys.
