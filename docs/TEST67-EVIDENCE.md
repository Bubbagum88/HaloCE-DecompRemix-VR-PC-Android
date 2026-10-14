# Test67 evidence and review

Baseline: c74e4a59 (APK runtime 0b5c7e62), private Test66/code78. Latest public
release remains v1.0.31. No new upstream merge or protocol/voice change in this pass.

## Owner media

Logs: halo_log_2026-10-13_22-25-19-809_6263 and 22-31-54-528_9200.
Video: com.halo.decomp.vr-20261013-223239-0.mp4, 149.413 seconds.
Whole clip reviewed in 4-second contact sheets, with focused reload frames at
8/12 and 94/96/98/100/102/104 seconds. Dark a50 footage was brightened only for
inspection. This is visual sampling, not a frame-by-frame playback claim.
Both logs end in exit0 cleanup; no new fatal signal found. The logs explicitly
record COMBAT REACH=3 and LUNGE REACH=8. At 22:33:08.881 a lunge landed then a
new same-hand lunge began in that same tick; 22:25:53.196 shows the same defect.
Stroke ownership now persists through landing and rearms on slowdown/release.

## Reload audit: decoded data, not guessed offsets

Offline sampler compiles production model_animations.c, real_math.c and
matrix_math.c against the owner's USA Xbox a50/c40/bloodgulch cache data. No game
was launched. Every relevant reload/ready clip was sampled. Files stay outside
the repo under D:/HaloQuest/_scratch/anim67; no proprietary assets are bundled.

| Profile | Finding and treatment |
| --- | --- |
| AR | Old full frame52 is a slap, relative motion 6.53 cm/frame. New full frame40 is a held replacement mag. Adjacent samples move at most .325 cm; wrist-to-part origin10.25 cm. |
| Sniper | Accepted empty frame25, about9.09 cm wrist distance, retained by the unchanged legacy sampler. No override. |
| Pistol | First empty clip's nearest origin22.4 cm was rejected; full frame35 is held steadily, origin20.63 cm. Exact stock shape and neighboring pose guards allow this genuine hold. |
| Shotgun | Part is frame bullet, not frame magazine. Empty frame6 holds the shell, origin16.55 cm; adjacent movement.267 cm. Pump has no moved grip in that reload clip; existing charging fallback retained. |
| Rockets | Part is frame tubes; empty frame59 held steadily. Origin39.87 cm lies along the long tubes, not at the gripping surface. Exact stock shape/continuity guard, not a global loosened reach threshold. Charge part frame push_bar recognized. |
| Flamethrower | frame ammo/cover: no verified nearby left-wrist hold in reload animation; existing generic part/charge grip preserved. No fabricated native pose. |
| Needler | frame needle01/body: crystals replenish without a detachable part held by the native off hand; existing cluster/body interaction preserved. |

AR/Pistol/Shotgun/Rocket selected poses each pass three-frame positional and
orientation continuity checks (minimum axis dot .999788). Runtime rejects wrong
node count, wrong clip length, nonfinite pose, excessive origin distance, or
unstable adjacent poses; custom graphs keep the old sampler. All use the same
native per-finger transforms relative to the wrist, mirrored by existing left-
hand mode. Insertion/chamber travel, socket geometry, owner arbitration, feedback,
finite checks, storage, cancellation and native ammo transaction were reviewed
and retained. AR charging sample remains unchanged; no unsupported charging pose
is forced onto weapons whose clip lacks one.

An additional offline comparison compiled the complete production
vr_reload_grip_learn function from HEAD (Test66) and this candidate, with the real
animation decoder and matrix math. Both were run on all seven local graphs.
The complete Sniper sampled magazine/finger output is byte-identical. Results:
AR mag52->40/charge15 unchanged; pistol invalid38->valid35; shotgun none->shell6;
rockets none->tube59 and charge33; Flamethrower/Needler unchanged fallback.
Scripts grip67build.py/grip67run.py and output production-grip-parity.json are
preserved under D:/HaloQuest/_scratch (raw decoded data stays private).

## Fist and grab scope

Regular assisted blows use a scoped owner/target/tick context to suppress only
the native unsuspecting instant-kill shortcut. Fist-only damage multiplier adds
difficulty tuning; bullets/global health/armed melee unchanged. Damage-category
check prevents a raised guard from scaling unrelated bullet damage while an
attacker is in a melee animation. Parry/block feedback uses existing native impact
sounds, short haptic pulses and small blue/amber world markers.

Grab acquisition projects onto the touched skeletal capsule, fixes that node and
bone-local offset until release; visible hand attraction eases and stays within
6 cm. Heavy rules, articulated pins, Jolt handoff, slams/recovery and multiplayer
capability gates retained. Existing curved-wall probes/blending/gap grace reviewed;
no concrete defect justified changing accepted parkour or vehicle code.

## Combat reference review

User reference: [Batman: Arkham Shadow - Infinite Combat Challenge](https://www.youtube.com/watch?v=YGu9XIQN_lA),
fan channel BatmanArkhamVideos, 1,399 seconds. Review covered four contact sheets
sampled every 20 seconds through 1,380 seconds, plus detail frames at 2 fps from
16 through 28 seconds. The private 480p reference is
`D:/HaloQuest/_scratch/reference67/ref480.mp4`. This was sampled visual review,
not continuous playback or inspection of every frame. Observed material includes
multi-enemy blue/red/yellow warnings, counters, weak-point/combo follow-ups,
stun opportunities, target switching and shield/heavy opponents.

These observations inform combat flow and cues. Candidate glyphs are original
Halo-themed angular cyan/amber shapes, with existing Halo impact sounds. No
Batman assets, animations or code were copied. The additional conceptual source
is [Camouflaj's GDC talk synopsis](https://gdcvault.com/play/1035681/); only its
synopsis was available, so no full-talk review is claimed.

## Procedural combat pose evidence

`port/linux/game/vr_combat_pose.h` adds bounded sweep, overhead, jab, arm-clutch/
kneel and recoil presentation over the current native `real_matrix4x3` palette.
The helper writes a complete result only after validating the request, matrices,
node count, terminated names and parent topology. Missing/unrecognized chains, cycles,
invalid parents, nonfinite input and unreachable leg geometry return no overlay.
It uses native limb lengths, rigid subtree rotations and the existing two-bone
IK reach math; weights ease within 0..1. Zero weight leaves the native pose intact.
Attack offsets are neutral at phase 0, phase 1 and the shared contact phase .65.
`vr_combat_moves.c` maps that contact phase to the current native clip's primary
hit keyframe. No forced animation state or new hit frame is introduced by the
pose helper.

Kneeling lowers only the rendered root. Human thigh/calf/foot and Elite/Jackal
thigh/calf/horselink/foot chains keep their bone lengths and native foot frames;
digitigrade horselinks remain pinned too. Body position/collision remain native;
the gameplay opening is a separate short stun. Stock Grunt rigs lack the separate
hand chain required for clutch/kneel and retain their native pose for that mode.
Hunter control/kneel is excluded by gameplay policy, even though the helper can
solve its stock bind geometry. NPC grab/Jolt palette ownership takes precedence:
no combat overlay is applied while that system owns the palette. A release
opening can expire while NPC settling still owns it; visual kneeling is therefore
not guaranteed after every successful arm opening.

`tools/test_test67_combat_pose.py` executes the actual helper with synthetic
geometry: 1,800 mode/phase/weight/side/facing cases and 4,000 continuity samples
pass with ASan/UBSan. Checks cover finite frames, every bone length, byte-identical
feet/toes, both sides, zero/tiny weights, in-place output, contact/end phases,
distant control targets and malformed/count/cycle/NaN/degenerate-rig guards.
The helper also compiles against the real 32-bit game headers.

Private stock a50 model metadata supplied names and parent topology. Offline
bind-pose checks passed all five modes on both sides for Captain, Marine,
Cyborg, Elite, Jackal and Hunter; Grunt attack/recoil passed and clutch/kneel
returned no overlay as intended. Inputs and results remain outside the repo at
`D:/HaloQuest/_scratch/combat67-modelnodes.json` and
`D:/HaloQuest/_scratch/combat67-pose/stock-results.txt`. These checks establish
geometry and guard behavior, not headset animation, contact timing or game-wide
species acceptance. No model or animation assets are included in the helper test.

## Altheros load failure and resource layout

Owner log `halo_log_2026-10-13_21-55-41-586_14959.txt` identifies Test66/code78,
Quest 2, Android 14 and Oculus runtime 207.299.0. At 21:55:52.545 it requests
`d:\maps\b40.yelo`; at 21:55:52.547 the loader reports
`custom edition: a resource map is too large for this loader`, followed by
`game_load() failed`. OpenXR remains focused at 72 Hz with zero draws. The log
does not show a crash or allocation failure at this point; the empty blue view
follows the rejected map load. The earlier menu-cache recognition assertion is
not the immediate b40 failure.

The unmodified local `Latest Altheros Experience 10.24.2019` resources contain
613,838,703 bitmap bytes, 333,893,198 sound bytes and 447,783 locale bytes.
The bitmap file exceeds the old 512 MiB bitmap interval. Its `alsthetic` mod name
selects the existing `data_files/alsthetic-{bitmaps,sounds,loc}.map` aliases.

`port/linux/game/custom_edition_cache.c` now computes disjoint resource intervals
within the same signed offset limit. Bitmaps still start at `0x40000000`; sounds
start at `max(0x60000000, 0x40000000 + bitmap_bytes)`. Subtraction-based size
checks reject a combined end beyond `0x80000000` without overflow. For these
Altheros files, sounds start at `0x64966F6F` and end at `0x787D3DBD`. Ordinary
stock/SPV1-sized resources retain the original layout. The CE read branch uses
byte offsets before the stock sector-rounding path, so the exact resource-file
boundary need not be sector aligned. File streams and lazy reads remain in use;
this change does not allocate a buffer containing the complete resource files.

Converted `.audio` cache version 3 records the source sound interval. Matching
version 3 caches are reused; version 2 caches remain reusable with the historical
sound offset. A moved interval invalidates the old cache and requires its normal
conversion path once. This preserves ordinary-map cache reuse and prevents stale
sound offsets after the layout changes.

`tools/test_test67_resources.py` executes extracted production layout, read
routing and cache open/finish functions under ASan/UBSan. Virtual byte sources
cover the real Altheros sizes without allocating entire resource files. Cases
include stock/SPV1 layout, zero/exact-end/overflow sizes, both sides of the old
512 MiB boundary, first/last sound bytes, chunked/invalid reads, and version 2/3
cache identity, reuse and invalidation. A negative control reinstates the old
512 MiB cap and fails the same Altheros regression. The existing
`tools/test_test34_opence.py` guard was updated for the computed sound offset
and passed.

Offline reports used the original ten maps and resources through production
`cache_file_formats.c`, then the production 32-bit tag schema validator. Scratch
hardlinks supplied the expected resource aliases without modifying source assets.
All maps passed format load/conversion and schema validation using existing
corrections; no schema rule was relaxed for this fix:

| Map | Existing schema corrections |
| --- | ---: |
| a10 | 101 |
| a30 | 111 |
| a50 | 111 |
| b30 | 86 |
| b40 | 125 |
| c10 | 61 |
| c20 | 61 |
| c40 | 125 |
| d20 | 105 |
| f10 | 94 |

Reports remain private at `D:/HaloQuest/_scratch/altheros67/report-native-formats.txt`
and `report-schema.txt`. The standalone report path does not execute the game's
Ogg decoder/transcoder, GPU bitmap/model conversion or live BSP transitions; its
`sounds_undecodable` counts are not an audio playback test. No game was launched.
The evidence addresses the observed resource-size rejection and offline schema
compatibility, not complete Altheros/OpenSauce feature support. Campaign play,
first-run audio conversion, save/reload, transitions, rendering, audio and Quest
memory behavior still require device results.

## Optional content provenance

SPV1: existing D:/HaloQuest/mods/spv1/maps and ce_resources, CMT 2006 HaloMaps
campaign versions; author/source confirmed at
https://www.halomaps.org/hce/detail.cfm?fid=1921 . Required maps/resources have
13 size/SHA-256 entries in assets/campaigns/spv1.properties.
Altheros: existing Latest Altheros Experience 10.24.2019 folder and its ReadMe,
private beta by Altheros/Eric. Thirteen size/SHA-256 entries in altheros.properties.
The ModDB page could not be retrieved in this environment; local ReadMe/source
version is the evidence. No redistribution grant was found locally, so no mod or
Halo assets are in the APK. Only our own setup recipes and code are included.
Known local content was hashed, not downloaded again or changed. Optional mod
preparation does not replace the base game; install remains an explicit action.
Validation covers content identity; it is not a full campaign playthrough.

## Verification status

Focused production helper/state tests pass (ASan/UBSan where applicable), including
stroke rearm/opposite-hand switching, four difficulties, scoped damage, block/parry
feedback, capsule anchors, reticle states and sprint. Offline Java campaign tests
exercise prepare/import/reuse/hash failures/repair/install/restore, plus existing
Test66 campaign cycles. Full suite, APK builds and package audit are recorded in
TEST67-DELIVERY-STATUS.md once completed. Device validation remains pending.

## Final review (resumed session, 2026-10-14)

- Drawn-pose coherence: combat poses are render-only (vr_combat_render), while
  grab acquisition, combat_regions (head/chest for hit judgement, glyphs and
  highlights) and touch shoves read Halo's native nodes. A CLUTCH_KNEEL lowers
  the drawn body by up to 0.28 of the shorter leg (about 0.3-0.4 m on a stock
  Elite) for at most a second; RECOIL tilts the drawn spine 0.18 rad. Attack
  overlays are exactly native at the clip's hit keyframe (CONTACT_PHASE), so the
  enemy's real contact geometry is unaffected. Fix: vr_combat_pose_map_point
  carries a point on the drawn body onto the native pose through the nearest
  drawn node (rigid); vr_combat_drawn_to_native wraps it; combat_regions reads
  the drawn pose; local grab and touch acquisition test the mapped point while
  the hold target stays the real hand (holds slip only past 1.2 m; the offset
  is far below). No reach change; remote hands, NPC hand and Jolt ownership
  unchanged (the pose already stands aside for owned bodies). Test:
  test_test67_combat_pose maps 460 points on drawn bones across every mode, side
  and both rigs (ASan/UBSan) and checks malformed input.
- Melee parry gun-hand rules now match deflection: a two-handed gun's support
  hand records no parry stroke, and a recorded stroke counts only with the same
  weapon handle (vr_parry_hand_weapon); drop/holster/swap/hand-over cancel it.
  test_test62_extra covers both.
- Move callbacks: overlay phase follows the native clip's own frame and hit
  keyframe; dodges are judged in the native damage callback within one frame of
  the hit keyframes; the clip identity is rechecked each tick.
- Gates: moves and deflection run for the local player in a local game, or a
  co-op host with HOST VR ACTIONS and compatible peers; never on network clients
  or ordinary PvP hosts; never against players. OFF switches checked each tick.
- Guest gnu89 build errors in the uncommitted additions (duplicate loop
  variables; actors.c's private copy of _projectile_will_super_explode_bit, now
  exported by projectiles.h) fixed; both flavors compile and link.

## Merged Test68 and fork integration (resumed session 2, 2026-10-14)

Sources, fetched into the repository as refs: OpenCE main (still build 201) and
testing (52e33a39), GulchCE main ebb197ba, and every jcompto95-tech branch.
Each change was applied as a three-way merge and its conflicts resolved by hand
against this port; the commits name the source branch.

- OpenCE testing 52e33a39: map sharing trust, tag validation, Custom Edition
  geometry byte limit (BSP too large), Ogg frame/size/rate limits and the
  hardened stb_vorbis (byte-identical). Found on the way: this port's own CE Ogg
  conversion could wrap its frame count; now bounded the same way.
- GulchCE MCC maps: solo only. Its MCC tests were adapted to this port
  (tools/test_test67_mcc_upstream.py): 750 pass; 140 compile but are not run on
  WSL1 (32-bit programs; reported as M32-NOT-RUN, not as passes); the online-MCC
  files test_mcc_network and test_mcc_ui_teams excluded; deselected:
  test_mcc_identity session resolution (online), test_mcc_seats[replication]
  (online), test_viewmodel_shield[None] (fails on GulchCE's own source in 64-bit).
- Fork branches taken and adapted: third person (guarded off in VR), Extra Effects
  screen, item draw scale (VR network pose kept), overshield height fade
  (this renderer's program/uniform), corpse/decal limits, projectile effects v2
  with dynamic/vehicle blood (the fork's dropped blood_vehicle_hit_body restored:
  ragdoll.c calls it), stencil shadows (one face a draw: no glStencilOpSeparate
  import on GLES; own unit excluded in VR), item physics on Jolt (seven new host
  imports; items held by a VR hand or owned remotely are never Jolt's; clients
  follow the host), the Armor menu with recolor/glow in this renderer, text chat,
  vote-ban. Superseded and not taken: player-colors (a network 29 bump; armor sync
  replaces it), separate visor-color, dynamic-blood v1/v2, projectile-effects v1,
  the v1 blood tuning console; light bloom stays a no-op (the fork's desktop pass).
- Network: the extras use new kinds 87-92 only; OpenCE drops kinds at or past its
  NUMBER_OF_DISTRIBUTED_MESSAGES, so stock network-28 peers ignore them. Each send
  is behind network.community_extras (default on; launcher Server Browser switch).
  Votes 78/79, the network version and voice are unchanged.
- Launcher: JavaSteam 1.8.0 and OkHttp 5.3.2 resolved by Gradle; both flavors'
  javac pass against them. Licenses: CREDITS.md and THIRD-PARTY-NOTICES.txt carry
  complete texts fetched from each project's repository.
- Pins: tools/test_test67_fork.py (network, defaults and rows, VR guards, kept
  pieces, VR BUTTONS reset, licenses) and tools/test_test67_upstream_harness.py.
  Full suite, builds and package: TEST67-DELIVERY-STATUS.md. Not device tested.
