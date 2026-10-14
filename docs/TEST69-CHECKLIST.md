# Test69 checklist: The Altheros Experience's scripts

Private successor to Test68, 1.0.36-test69 / code81. Source: Test68's delivered
tree (APKs from c331ef2b) plus this fix. No publish, push, install or game
launch; local commits only. Saved settings preserved. Network 29 unchanged.

Owner's report (2026-10-14): "altheros still gives a blue screen, investigate"
(Quest log of 1.0.34-test67, b40). Owner: "just proceed with your plan, test 69".

## Evidence

- The log shows Test67's large-resource fix working for b40: the large
  resource layout found, the checksum matched, all 4721 sounds converted
  (0 failed). The map is then refused: "the scripts use 8 functions or engine
  globals this build does not have, and cannot run" (OpenSauce's
  pp_set_effect_instance_fade and pp_set_effect_instance_active), then
  "game_load() failed" (the blue screen).
- A read-only scan of all ten Altheros levels' compiled scripts (the owner's
  copy, Latest Altheros Experience 10.24.2019) finds every function and engine
  global they use that this build lacks. Its b40 count is the log's (4 + 4).
  - pp_set_effect_instance_active (short, boolean) and
    pp_set_effect_instance_fade (short, real, real, real): b30, b40, c10, c20,
    c40, d20, f10 and a50, 4 + 4 each (the VISR night vision scripts);
  - pp_bloom_set_exposure (real, real): a50;
  - object_data_get_real (object, string, string) and object_data_set_real
    (object, string, string, real): a30, its gravity lift, which reads and
    raises transitional_velocity x/y/z;
  - the engine global rasterizer_fps (Halo PC's frame-rate counter): a10 and
    a30, (set rasterizer_fps false) and (set rasterizer_fps true).
  The types are the maps' own compiled argument types. Every other engine
  global they use (cheat_deathless_player, rasterizer_dynamic_lit_geometry,
  rasterizer_near_clip_distance, rider_ejection, weather) exists here.

## Work

- [x] custom_edition_opensauce.c: those five OpenSauce functions, found by
  name after the game's own table (and after GulchCE's MCC functions), at
  indices 0x7100-0x7104. Post-processing is accepted and draws nothing (this
  build has no OpenSauce post-processing: VISR's tint and bloom do not show).
  object_data_* read position, forward, up, center, radius (read only) and
  read/write transitional and angular velocity and scale; other names are
  logged and ignored; NaN and either infinity are not written.
- [x] The script engine (hs.c, hs_runtime.c) finds them where it finds MCC's:
  name lookup, the map's call check (argument types must match exactly),
  hs_function_get, the evaluator's index bound and function names.
- [x] custom_edition_scripts.c: a set of rasterizer_fps to a permanent boolean constant becomes
  a no-op, a read of it FALSE (as GulchCE turns MCC-only calls into
  constants); a set of a computed value, another missing global, or a
  non-boolean/malformed constant use is still refused. No engine global was added: engine
  globals live in checkpoint game state, and one more would not match saves
  of earlier builds.
  The owner's actual a10/a30 RHS nodes were rechecked before tightening this
  guard: each has type/constant_type 5 (boolean), flags 9 (permanent primitive),
  no next argument, and boolean byte 0 or 1. Their unused high value bytes are
  preserved as irrelevant; they are not required to be zero.
- [x] Tests: test_test69_opensauce (the production file, ASan/UBSan: names,
  the maps' types, the call check, post-processing, a30's velocity
  read-modify-write, read-only/unknown/missing/nonfinite values) and test_test69_scripts
  (the production converter on an a10-shaped script; it fails on the old
  converter, as the headset did). Full suite: 145 suites passed before the
  identity change.
- [x] docs/custom_edition_caches.md updated.
- [ ] Full suite, both builds, package identity/signature/hash checks.
- [ ] Delivery record, memory, local commits.

## Not known until the headset

The script check is the step before the model conversion, which reads each
level's model data whole (25-59 MB; guest memory comes in 256 MB pools). No
Altheros level has reached it on a device. If a level still stops, its launch
log names the step. Automated results are not headset or phone verification.
