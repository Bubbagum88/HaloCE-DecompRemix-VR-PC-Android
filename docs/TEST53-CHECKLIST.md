# Test53 checklist (private candidate after v1.0.19)

Every change since v1.0.18 and every requested item gets an explicit outcome.
Columns: **Implemented** (source change in this candidate), **Automated**
(a host check that exercises it), **Device** (what only the owner's Quest /
phone can confirm). "—" means not applicable.

Test52 (1.0.20-test52, code64) was committed but never built or delivered;
Test53 supersedes it and carries all of its changes.

## 1. Voice crash and guest ABI

| Item | Implemented | Automated | Device |
|---|---|---|---|
| Root cause: asm converter dropped byte 338 of Opus `cache_bits50` | Test52 converter fix kept; re-proved independently (shipped Test51 guest table differs at 338; host Opus with only that byte dropped overflows in `quant_partition` under ASan, fails at 28 kbps without; correct table clean 8–64 kbps) | `test_android_asm_convert` (pre-build: compile path; post-build: built image must match) | Speak in a voice lobby and a match; others hear you; you hear them |
| Input sanitizing (NaN/Inf→0, clamp ±1) and bitrate clamp 8–64 kbps, packet limit | `voice_audio_encode` | `test_voice_encode_hardening` (real vendored Opus, assertions, ASan/UBSan, garbage bitrates incl. 995719466) | — |
| `platform_log` missing prototype (garbage voice logs, Test50 crash) | Test52 fix kept | `test_android_guest_prototypes` | Voice log numbers readable |
| Every guest unit rejects implicit declarations (was: game/port/platform only; libtiff exempt) | `android_build.py` applies it in `guest_object` to all 1,640 units; libtiff's undeclared calls declared | `test_android_guest_prototypes` (also proves the flags fail an undeclared call in C89 with `-w`) | — |
| K&R `long lseek()` in libtiff (32-bit offset into a 64-bit `off_t`) | `tiffcompat.h` uses the C library prototypes | build | — |
| Cross-unit prototype mismatches (count/type/return/extension) | Fixed rasterizer, keyboard, libtiff `debug_malloc` declarations | `tools/android_guest_abi_lint.py` (whole-program LLVM Lint + extension check), run by `build-quest.sh` after each flavor | — |
| "VR manual reload gate: weapon=-303103938" | Not garbage: a valid datum handle printed signed; now logged in hex | — | — |

## 2. Interaction features (owner: "not working")

| Item | Implemented | Automated | Device |
|---|---|---|---|
| NPC / world / vehicle-lift / remote co-op grabs never acquire (logs: hundreds of misses, `collision_overlaps=0` at 8 cm) | Root cause: zero-length pill sweep never reports touch. New `collision_model_touch_sphere` (surfaces within radius or hand inside) used by all four paths; the always-FALSE `collision_model_test_sphere` stub completed | `test_contact_acquisition` (runs the engine's pill test to show the miss), updated NPC/world/remote suites | Grab Grunt/Jackal/Marine (one hand), Elite/Hunter (two), weapons, crates, vehicles |
| Parkour (wall-run, wall-jump/leap, grip climb = wall grab) never ran | Root cause: `vr_head_view` refused outside the stereo pass; ticks run before it, so parkour reset every tick. Fixed | `test_vr_tick_head_view`, `test_vr_parkour` | Each toggle solo; co-op host |
| Parkour online | Co-op host's own player allowed; clients/PvP stay stock (host movement checks would refuse) | `test_vr_parkour` (client, PvP host, co-op host) | Co-op host test |
| Wall-run entry window | 0.33 s → 1 s after Jump | `test_vr_parkour` | Feel |
| Manual reload never reached input stage (Test47 log) | Same `vr_head_view` root cause | `test_vr_tick_head_view`, `test_manual_reload` | Full magazine cycle per weapon |
| Released NPC stays limp/AI suppressed (Test46: 85 s) | Bounded handoff: settle ≤5 s, pose handoff ≤1.5 s | `test_vr_npc_interaction` | Throw/drop NPCs; they get up/fight; corpses rest |
| BODY RETENTION does nothing in campaign | Script `garbage_collect_now` now keeps newest 45/60 in solo | `test_vr_corpse_retention` | Bodies persist past encounters |
| Settings lookups O(n) per call in hot paths | Lookup cache by name address, content-verified | build | Frame time |

## 3. Owner additions (2026-10-11)

| Item | Implemented | Automated | Device |
|---|---|---|---|
| OpenCE release 184 (network 25: integrated light in object states; network 26: WebRTC signalling) | pending | pending | Join current OpenCE servers |
| "All compatible networks" default in the network selector | pending | pending | Launcher shows All by default |
| VR Settings IMMERSION page duplicating immersion toggles | pending | pending | Page present, toggles mirror |

## 4. Audit v1.0.18..HEAD

Pending (see sections added below as each area is reviewed).
