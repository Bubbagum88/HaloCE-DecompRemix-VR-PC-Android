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

Conceptual combat reference: Camouflaj's GDC talk synopsis,
https://gdcvault.com/play/1035681/ . No full-talk access or copied assets/code claimed.

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
