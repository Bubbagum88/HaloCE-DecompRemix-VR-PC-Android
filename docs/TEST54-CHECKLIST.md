# Test54 checklist (refinement after Test53)

Source: the owner's 2026-10-11 logs (`halo_log_2026-10-11_09-34-28` solo,
`..._09-39-51` online), the 3:44 solo video and the 15 s assault-rifle video,
the 35-item brief, and three additions (death ragdolls as a toggle on
IMMERSION; gun parts sliding while walking; grab/climb features turning on
FIST REQUIRED). Columns: **Implemented**, **Automated** (host check),
**Device** (what only the Quest/phone can confirm).

## Evidence (logs and video)

| Observation | Cause found | Test54 |
|---|---|---|
| Mag pulled and dropped at 3:07-3:29; ammo stays 00; `contact_pouch=0` in every one of 120+ reload input lines | Pouch was a 4 cm point offset from the head; never reachable blind | Body-frame pouch volumes (16 cm) |
| B pressed mid-reload: `event=7` (cancel) | Reload button cancelled an open transaction | B ejects; ignored mid-transaction |
| 37+22+19+... NPC misses, all `collision_candidates=0`, `contact_radius=4.00 cm`; Marine attempts 1:00-1:11, 2:41 | Only the shot-hit collision model was tested at 4 cm | Bone-capsule touch of the live pose |
| 68+38 `wall grip missed`; sloped rock 2:43-2:56 | Required a vertical normal within 4 cm; tracked hands enter walls | Slopes/overhangs/ledges, through-wall hold, 10 cm, grace |
| Contorted fingers on walls 0:38-0:54 | Contact direction flipped and snapped per frame | Eased contact, no instant flips |
| 16 `hold strain separation 0.65 m` | Loose root spring for one-hand species | NPC HOLD strength (SPARTAN default) |
| `settle still pending ... garbage_queued=1; handing back` after throws | Root left behind while the rig flew; culled/rebuilt at the root | Root follows the pelvis while settling |
| AR part sliding while walking (second video) | First-person moving/sway overlays animate gun parts | Gun parts keep the gun's pose in VR |
| Voice: online log encoded/sent and decoded 586-1081 frames | Working | Untouched |

## Items

| # | Item | Implemented | Automated | Device |
|---|---|---|---|---|
| 1 | Manual reload full loop | Eject (B or pull) → pouch pickup → insert on contact → charge if needed → commit via native transaction | test_manual_reload (state machine, ammo conservation), test_test54_interactions | Full cycle per weapon |
| 2 | B behaviour | OFF: stock reload. ON: drops the magazine anywhere, never reloads natively, ignored mid-transaction; no reserve = click | test_manual_reload (eject without contact; no cancel) | Both modes |
| 3 | Body magazine storage | `vr_reload_pouch_zone`: hip/shoulder on the free hand's side (mirrored left-handed), MAG POUCH SIDE auto/left/right/both; hip kept if both pouches off. Magazine attaches at the palm while held; traced for hand collision; inserted on aligned contact | test_manual_reload (pouch wiring, config) | Reach without looking; left-handed |
| — | Optional calibration | Side choice only; no positional calibration (not implemented) | — | Report if hip/shoulder heights are off for your body |
| 4 | Hand poses for parts | Existing reload grasp (fingers conform to the held magazine/handle); hand drawn ≤6 cm onto the part | test_test54 (soft anchor) | Look of the grip |
| 5 | Finger/contact smoothing | Eased contact in and out, no direction flips; controller authority (≤6 cm) | test_test54 (wiring) | Slide a hand along rock |
| 6 | Weapon-specific charging | Charging only when the chamber was empty (`chambered` captured at eject/pull); pistol slide, AR handle, sniper bolt, shotgun pump, rocket bar, flamethrower cover as profiled | test_manual_reload (tactical commits without charge; empty needs it) | Pistol, AR, sniper, shotgun |
| 7 | Reload haptics | Per-event patterns on free and gun hand (grab, pull free, eject, pouch entry, well contact, insert, lock, charge, rack, ready, cancel), scaled by HAPTICS | test_manual_reload (helper pinned) | Feel |
| 8 | World-grab detection for climbing | Feature sphere at CLIMB GRAB radius (default 10 cm) + eye-to-hand ray through the surface + 6-tick grace; walls, steep rock, overhangs, ledge tops above the waist | test_test54 (climbable math, wiring) | Ordinary walls, rock faces, ledges |
| 9 | All NPCs incl. allies/corpses | Bone-capsule acquisition for every eligible biped (Marines, crew, Grunts, Jackals, Elites, Hunters, Flood, corpses) | test_test54, test_vr_npc_interaction | Marine from behind; corpse on floor |
| 10 | Grab radius / assist | GRAB ASSIST: TOUCH (default) / 5 / 10 / 15 cm added to body capsules only | test_test54 | Natural feel |
| 11 | Strong hold | NPC HOLD (LIGHT/NORMAL/SPARTAN/IRON); species mobility and two-hand rule kept | test_test54 (strength math, Elite < Grunt) | One-hand Grunt; Elite resists |
| 12 | Melee vs grab | Open hand never strikes with any grab/climb feature on; FIST REQUIRED needs a fist; gun hand strikes with the gun | test_test54 (melee math) | Fast reach for an NPC makes no blow |
| — | Grab/climb turns on FIST REQUIRED | Soft, reference-counted dependency (`vr.immersion_auto`) | test_vr_immersion_menu | Toggle NPC GRAB, watch FIST REQUIRED |
| 13 | Ragdoll refinement | Mass by carried joints; low-speed contact damping; native joint limits unchanged; throw/drop momentum per joint | test_test54 (mass wiring) | Shot/killed/thrown/dropped bodies |
| 14 | Thrown ragdolls vanish | Root follows the pelvis while settling (cull/collection/rebuild no longer at the release point); retained as garbage newest-first with BODY RETENTION | test_test54 (root follow), test_vr_corpse_retention | Throw far, look away, return |
| 15 | Throws | Latest hand motion weighted over the average × THROW (0.75-2×), capped | test_test54 (throw math) | Flick vs lob |
| 16 | Wall run / wall jump preserved | Wall detection (`vr_pk_vertical`), entry, jump and leap code unchanged | test_vr_parkour, test_test54 | Same as Test53 |
| 17 | Wall-run momentum | Wall's fall hold fades over WALL TIME; horizontal momentum carries on | test_vr_parkour | Run feel |
| 18 | Head-directed wall jump | Unchanged | test_vr_parkour | — |
| 19 | Climb leap / grab reliability | Leap unchanged; grabs per #8 | test_vr_parkour | Leap still works |
| 20 | Voice preserved | No voice code touched | test_voice_chat_integration, test_voice_encode_hardening | Speak online |
| 21 | Locomotion as one system | Sprint, arm run, wall run, wall jump, climb, leap share the capsule path; climbing holds now include slopes and ledges; open hands don't melee | suites above | Session through a level |
| 22 | Useful tuning only | New: MAG POUCH SIDE, CLIMB GRAB, GRAB ASSIST, NPC HOLD, THROW, DEATH RAGDOLLS. Reused existing rows for haptics, sprint, arm effort, melee speed, fist, hand contact | test_vr_immersion_menu, test_test25 (fit) | — |
| 23 | Immersion dependencies; Advanced | Hard: MAG DEBRIS→MANUAL RELOAD, CUSTOM SCENERY→WORLD GRAB, CUSTOM NPC RIGS→NPC GRAB. Soft: grab/climb→FIST REQUIRED. Reference counted; IMMERSION+ page for technical rows | test_vr_immersion_menu | Toggle chains |
| — | Death ragdolls toggle | DEATH RAGDOLLS (IMMERSION and Controls); supported NPC killed within 40 m, solo or co-op host; uses rig slots; not players' bodies | test_test54 | Kill groups of Grunts |
| — | AR part sliding | Gun-model parts restore their state-animation pose through moving/sway/push-back overlays (all guns) | test_test54 (wiring order) | Walk and turn with each gun |
| 24-31 | Multiplayer sync, Android, negotiation, authority, ragdoll state, parkour networking, equal access, host policy | Existing negotiated co-op path used unchanged; death ragdolls ride it; no protocol change. See TEST54-NETWORK.md | network suites | Two VR clients + phone |
| 32 | Don't force risky networking | Parkour/manual reload as a client left off; documented | — | — |
| 33 | Review the whole video | 19 contact sheets (3:44) + 15 s AR video | — | — |
| 34 | Verify results | Host checks above; device loops listed in TEST54-DEVICE-CHECKLIST.md | — | Required |
| 35 | Regress nothing | Full suite + both flavors built (TEST54-DELIVERY-STATUS.md) | run-quest-checks | Required |
