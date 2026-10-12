# Test39 scope disposition

This ledger distinguishes source work from physical/device acceptance. It
continues the Test38 requirement audit and does not claim that every requested
physical behavior is complete.

| Requirement | Test39 status | Remaining evidence or limitation |
|---|---|---|
| Toggle to shake an overheated weapon for faster cooling | Implemented as the **SHAKE COOLING** OFF/ON control, default OFF, offline VR only; selected weapon, two directional reversals within 0.5 seconds, time-decaying movement signal, bounded 1–2.5x native heat-loss multiplier | Device testing for heat weapons, controller handedness, comfort and thermal pacing |
| Adjustable all-weapon scopes | Carried forward from Test38 | Verify each authored weapon/revision on headset; no change in this pass |
| Stabilize mounted Shade/Ghost/tank reticles | Carried forward from Test38 | Device/video acceptance still needed for each mount; no normal-gun behavior change |
| Manual reload and physical magazine insertion | Carried forward, offline only | No networked ammo transaction; no persistent discarded physical magazine entity |
| Hand/object contact and weight feedback | Existing solver plus new optional, local low-amplitude haptic refreshed every 120 ms | Haptics are heuristic feedback, not measured mass; online relay absent |
| World/NPC grabbing, ragdolls, impacts and safe recovery | Carried forward with native authority/bounds | Generic NPC rescue and arbitrary actor state restoration remain unsupported |
| More than four-peer co-op interaction | World-object interaction negotiation accepts up to native machine-table ceiling; NPC poses remain <=4 remote machines | No large-session live test; do not interpret 128 machines as verified 128-player campaign |
| Custom scenery | Narrow, explicit opt-in over validated collision bounds | Arbitrary scripts, animation graphs, structural geometry and unsupported tags remain excluded |
| Custom NPC rigs | Toggle for validated Assassin/Elite-family alias only | No arbitrary skeleton profiles or unknown race support |
| Vehicle handles | Existing per-vehicle steering controls carried forward | Whole-vehicle lifting is not implemented; handles do not grant vehicle physics ownership |
| Parkour | Carried forward solo-only | No host-authoritative movement protocol for online use |
| Automatic mission NPC rescue | Not implemented generically | Requires per-mission actor/goal/checkpoint-safe mapping and device tests |
| 128-player campaign selector/guarantee | Not added | Campaign stability, saved-unit capacity, transition barriers, AI and map scripting need a separate evidence-backed project |
| PC/Steam Frame | Deferred as requested | Quest/Android remain the target |

## Safety defaults

All Test39-specific toggles default OFF. Optional online interactions require
the host's explicit setting and capability leases. Solo-only actions return
native behavior when online. Unsupported custom tags and actor graphs are
refused rather than guessed. The public v1.0.18 release and its assets remain
unchanged.
