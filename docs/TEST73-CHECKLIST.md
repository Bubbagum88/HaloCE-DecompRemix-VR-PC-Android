# Test73 checklist: every VR feature on, co-op VR for everyone, the newest OpenCE

Private successor to Test72, **1.0.40-test73 / code85**, branch `test39-interaction-completion`, on OpenCE
**Build 256** with its testing branch and its fix-scenery-shields-network branch (network 34: hosts 34, joins
11 to 34). Test72's checklist (TEST72-CHECKLIST.md) and the earlier ones still apply. Local work only; no push, publish or install. Saved settings preserved, but for the
one-time switch-on of the VR features (below).

The owner's rule for this delivery: nothing is assumed, and each item says how far it is verified.

Legend:
- [x] done and verified off-device (built, run or measured here);
- [s] source done and its source checks pass, **not yet compiled** (the owner: "dont provide/build any
  exes/apks until EVERYTHING in the list is done"; the single build pass compiles and checks these, and this
  list is updated then);
- [~] done; only the hardware can confirm it;
- [?] waits on the owner;
- [ ] not done.

## OpenCE and the forks

- [x] OpenCE Build 232, 235, 242 and 244 merged (network 32); Build 246's co-op gravity-lift fix ported
  (`coop_scripts.c` byte for byte Build 246's; its harness test runs, 64-bit and -m32).
- [s] OpenCE Build 249 to 256 and its testing branch: co-op's Pillar of Autumn softlock, the cached high-res HUD
  setting, the desktop visibility readback that no longer stalls a threaded driver, the menus' blue cursor
  (desktop), ALLY FRIENDLY FIRE (network 33) and Android Custom Edition texture residency (two adaptations: the GL
  state refresh only while a Custom Edition map is loaded; streamed Android geometry is this port's Safe geometry).
- [s] OpenCE's fix-scenery-shields-network branch (network 34): clients break and see broken the map's scenery
  shields and tripmines; a client of a host before 34 keeps that host's rules (`static_target_shields`; the
  harness test adapted, 35/35 both ways). web-wasm is the browser build's binary (no web build here).
- [x] OpenCE's harness tests that nothing ran (19, `biped_discard` adapted to this port's VR-held bodies) and
  256's own, in `test_test73_opence256` (64-bit less the 32-bit layout cases, then -m32: 319 under qemu-i386).
- [x] Server-browser pings (OpenCE 2759fc6db, ported by hand): checked end to end on PC with a private
  broker. [x] GulchCE's desktop visibility fix (AMD lens flares); `test_test73_visibility` on both vendor
  paths.
- [x] Every commit of the innerhat, universal, GulchCE and halofreak forks has a verdict
  (`_scratch/t72/item3_eval.md`); nine ports, each with a test (`test_test73_forks`).
- [x] Item 7 parity audit (renderer ports, 244's harness tests, the window icon, HDR in VR, the pause boxes).

## The owner's items

- [s] 10h: every VR feature on, once, with the update (46 settings through the menu's own apply), MAG DEBRIS
  included; BULLET TIME too (`test_test73_features`). [~] in the headset.
- [s] 10d: one co-op VR toggle, VR INTERACTIONS, for the host and every player: fists and FIST COMBAT (each
  client blow dealt by the host), waist grenades, manual reload, parkour, slides (`test_test73_network_vr`: the
  protocol itself compiled, its negative controls; `test_test62_extra`, `test_test38_network_interaction`,
  `test_vr_parkour`, `test_test70_movement`). On by default (the owner), once for older configs. Every player's
  fist combat (the owner): a client's blow sent to the host and dealt there (`test_test67_strike` runs the client
  branch). Online, a knockdown is a shove on the host, a stun stays the client's own, and block, parry and
  deflection protect the host only. [ ] a two-instance run (flat host, PC VR client) at the build pass.
  [?] sprint's speed boost online (left offline).
- [s] 10j STENCIL SHADOWS take away only the light they block: drawn before the dynamic lights, so a
  flashlight's or a shield's light is no longer dimmed in them; fog, particles and glass no longer darkened
  either (`test_test73_shadow_lights`: the production pass on a software stencil, 5 negative controls). The
  grass of detail objects is no longer darkened (no clean mark for it). [ ] frames on PC at the build pass.
- [s] Driving in proportion for every vehicle (`test_test73_driving`). [~] the feel.
- [s] 10c HAND LOCK (`test_test73_hand_lock`). [~]
- [s] 10i VEHICLE TURN (a tester's request; the owner: a toggle, on by default): a seat turns smoothly for a snap
  turner and snaps again on foot (`test_test24b` runs turn() itself: seat, off, leaving with the stick pushed, no
  SMOOTH SPEED; 5 negative controls). [~] the feel.
- [s] 10e passengers in full 6DoF; the wall-run leap by the head (`test_test32_vehicles`, `test_test70_movement`).
  [~] [?] "parkour quality": waits on the owner's specifics.
- [s] 10f GRENADE SIZE and the held grenade shown (seen in a PC VR eye dump). The waist slots are the
  waist since Test66; ringfall's grenade work compared (no change needed). [?] whether the waist spot moves.
- [s] 10g the 10-18 log: the tag-0 sound, the dynamic vertex pools, the seat-eye drift (`test_test73_log_fixes`,
  `test_test22`).
- [s] 10a MENU POSITION in both launchers (`test_test73_menu_position`); [x] WORLD held on PC VR.
- [s] 10b SCOPES: SIZE to 400%. [ ] per-weapon base places and sizes, measured at the build pass.
- [s] Item 6: ARMS FROM, the played character's arms (`test_test73_session`); [x] PC VR dump. [~] SPV1.
- [s] Item 8: Steam Frame (Lepton, the fdm_injection layer, touch bindings; `test_test73_frame`). [~] no Frame.
- [s] The Steam Frame against Valve's Lepton 3.0.8 source and the other Halo CE Frame ports (HaloCE-VR, Mjolnir
  VR): Lepton 3 detection; SteamVR waited for a minute in Lepton, then a clean end; the clock stepped by display
  times (every headset); the 72 Hz fall back said once; no start on a reinstall in Lepton; a no-computer installer
  and a Steam library launcher (`tools/steam_frame`, Exit game works) (`test_test73_frame_ports`). The headtracking
  feature's `required="true"` blocks nothing (Lepton never reads it). [~] no Frame. Four renderer speedups
  (multiview, one atlas swapchain, the hidden-area mask, quad-resolution screens) left out, the owner leaving it to
  judgement: each changes every headset's drawing and only a Frame can measure it (`docs/VR_ARCHITECTURE.md`).
- [s] Item 9: PC launcher saves and GEOMETRY (`test_test73_desktop_saves`). [?] the saves' import and export,
  checked by the owner (the owner: "ill verify that myself later").
- [s] Levels unlocked for a new profile (`test_test73_session`). [ ] a fresh profile's level list at the build
  pass.
- [s] Item 11: the Test73 identity (banner, package markers, Updater, version), What's New rewritten and
  shown styled on both launchers (`test_test73_whats_new`), the controls guide (`test_test73_controls_guide`).

## The build pass (last)

- [x] Full suite 196 of 196; the VR and flat Android builds with their guest ABI lint (799 + 923 units) and
  Opus tables check; windows_vr and the flat halo.exe, full rebuilds: no warnings anywhere. The VR build found
  one error (a declaration only the flat build saw), fixed before the commit.
- [?] The runtime checks moved there (scopes per weapon, the 10d two-instance run, a fresh profile, a PC VR smoke
  run, the desktop cursor, 10j's frames): not run, the owner's call ("just skip the running checks and provide the
  builds if possible. i will test it all myself").
- [x] The APKs, the Steam Frame bundle, the Windows zip, the build and source zips: TEST73-DELIVERY-STATUS.md.
