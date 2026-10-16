# Test72 checklist: every headset, the PC and the fight

Private successor to Test70 (published as v1.0.37), **1.0.39-test72 /
code84**, branch `test39-interaction-completion`. Test71 (1.0.38 / code83)
was never delivered on its own: its work is in this delivery and its
checklist (TEST71-CHECKLIST.md) still applies. Local commits only; no push,
publish or install. Saved settings preserved; network 29 unchanged; no
protocol change.

The owner's rule for this delivery: nothing is assumed, and each item says
how far it is verified.

Legend:
- [x] done and verified off-device (built, run or measured here);
- [s] source done and its source checks pass, **not yet compiled** (the
  owner: "dont build anything until EVERYTHING is done"; the single build
  pass compiles and checks these, and this list is updated then);
- [~] done; only the hardware can confirm it;
- [?] waits on the owner;
- [ ] not done.

## Platforms

- [x] One VR APK for Quest, Pico and Steam Frame: Pico 4 / Neo 3 / 4 Ultra
  and Steam Frame interaction profiles beside Touch (their registered names,
  behind their extensions); 200 bindings over 6 profiles checked against
  the Khronos registry and Valve's Frame document
  (`tools/test_openxr_bindings.py`, `tools/test_test72_pico.py`).
  [~] Pico and Steam Frame on the headsets themselves.
- [x] Windows flat `halo.exe`: builds, links, reaches the main menu
  (two fixes found by running it: blood before game time, one common block
  too small in the COFF link).
- [x] Windows PC VR `halo-vr.exe`: builds and links (ninja windows_vr),
  OpenXR loader 1.1.63 for Windows. [?] Runtime validation needs the owner's
  OK to use SteamVR's null driver (this PC has no headset and no OpenXR
  runtime registered). [~] On a headset.
- [x] One library: the XISO import (`xiso.c`) extracted the owner's USA disc
  image here: 24 maps, 1774 MB, every SHA-256 identical to the reference.
- [s] Desktop launcher (`desktop_launcher.c`): PLAY, PLAY IN VR, GAME DATA
  (import, VERIFY against `library.sha256`, REPAIR, the old maps put back if
  a repair fails), CUSTOM CAMPAIGNS (the Android app's recipes, folders and
  size + SHA-256 checks), SETTINGS, PC VR, WHAT'S NEW, UPDATES (GitHub, only
  on CHECK); `tools/test_test72_launcher.py`. Runtime check on Windows in
  the build pass.
- [x] Flat stereo 3D (Windows): side by side half/full, over and under
  half/full, red-cyan; eye swap, HUD depth, reticle depth. Disparity measured
  on frames equals the prediction (sbs_half 21.7, sbs_full 43.6, tab_half
  43.7, tab_full 21.8 px at infinity; HUD 1 m -65, reticle 25 m +39);
  `tools/test_test72_stereo.py`.
- [s] Flat remap UX (PC): a key taken from another action is named (5 s);
  Delete sets NONE; Backspace gives a binding its default; DEFAULTS resets
  all.
- [x] Flat movement (Android and PC): sprint hold/toggle/auto, slide, wall
  run, wall jump, each off by default; no wall grab or hand climbing flat.
  Compiled for Windows flat, Android flat and Android VR (VR modules
  unchanged); `tools/test_test72_flat_movement.py`.
- [s] Device-aware button names: the bound interaction profile reaches the
  game (`halo_xr_frame.controller_profile`, ABI 312 bytes); an Index's left
  controller shows L-A / L-B. The guest ABI lint runs in the build pass.
- [s] Version identity: 1.0.39-test72 / code84 in the VR banner, both APKs,
  the desktop version header and the packaging checks.

## Fist combat (VR)

From the owner's 17:32 log and video (the review is in the commit).

- [s] Lunges: 12 m by default (15 at most), a 30 cm Spartan leap scaled by
  distance and rise; airborne lunges kept; backing off as a lunge starts no
  longer cancels it.
- [s] Target intent from gaze and the fist's path together (uppercuts,
  hooks, off-axis punches); forgiving within 1.6 m; a refused punch logs
  why.
- [s] HIT ASSIST 50 cm (70 at most) from the fist's swept segment to every
  skeleton node.
- [s] The held enemy: a punch lands where the other hand holds it; a grab no
  longer cancels a strike on the held body. Seated enemies are targets.
- [s] **Shade death fixed**: the struck vehicle is pushed as the stock melee
  pushes it (acceleration_scale x 0.035, level, away from the striker); a
  hand pulled back out of an object no longer strikes; a rider's blow stays
  the rider's.
- [s] GRAB ASSIST 30 cm (50 at most), nearest body first (32 candidates).
- [s] Freeflow combo (blows, switches, parries, blocks, grabs, knockdowns;
  3 s), parry echo pulse, COMBO DISPLAY; damage bonus 5% a hit, 40% at most;
  melee durability by difficulty 0.80 / 1 / 1.30 / 1.60.
- [s] New defaults only replace values still at the old defaults (one
  migration, `vr.test72_combat_defaults_applied`).
- [~] How the fight feels: on a headset (Normal and Legendary).

## Menus and controls (VR)

- [s] BULLET TIME's settings on LOCOMOTION and IMMERSION > LOCOMOTION; its
  button on BUTTONS; no runtime change.
- [s] IMMERSION: LOCOMOTION, PARKOUR, TWO HANDS, SCOPE, vehicle VIEW; each
  row the same as on its usual page (`tools/test_vr_immersion_menu.py`).
- [s] SCOPES: one topic a weapon, rows FORWARD / UP / RIGHT / SIZE; each
  screen titled "PAGE: TOPIC".
- [s] MENU POSITION: HEAD LOCKED, WORLD, FOLLOW; distance, size, height;
  recentred by a stick click or the runtime's recentre.
- [s] LEFT-HAND MODE: BUTTONS rows show the physical letter (the saved
  bindings unchanged); Back is the right controller's B; BULLET TIME on R UP
  in vehicles and turrets; the held magazine follows the drawn wrist.
- [s] Passengers aim by hand (6DoF) when the seat's view is first person.
- [~] All of the above on a headset.

## The left eye garbled (SPV1, multiplayer)

The owner: models stretched, warped, garbled in the left eye alone; the
right fine; in SPV1 and a multiplayer match, worse as the frame rate falls.

- [x] Ruled out from the logs (01:38 multiplayer, 22:47 SPV1): stream wraps
  0, fence waits 0.01 ms, no OpenXR errors, the eyes' views mirror each
  other; Custom Edition's files (b30 takes no tags from them).
- [x] Ruled out by reading the code: per-eye projection, FOV, copy and
  vignette; swapchain acquire and release; the stream and index rings and
  their fences; the dynamic vertex and index buffers (copied at each draw
  in safe geometry); first-person interpolation (posed once a frame);
  render-time poses (copies); transparent groups (copied, per window);
  every raw GL bind outside the renderer (each sets its state anew);
  ragdolls (synchronous); window arrays.
- [s] The one structural difference found: the left eye is the frame's
  first pass. It advances the frame's state and begins after all the work
  between frames, where the right eye begins straight after a resolve that
  sets the GL state anew. Now the first eye begins the same way
  (`halo_vr_first_eye_begin`).
- [s] DISPLAY > EYE ORDER (`vr.eye_order`): RIGHT FIRST draws the right eye
  first, the frame's state advancing in its pass. If the garbling follows,
  it belongs to the first pass; if it stays, to the left eye.
- [s] `[vr-eyes]` in the log every 10 s: each eye's draws and streamed
  bytes, and a warning when the eyes draw different amounts;
  `tools/test_test72_eyes.py`.
- [~] Whether it is gone: only the headset shows it. The owner's test is
  in TEST72-DEVICE-CHECKLIST.md.

## SPV1 diagnostics

- [s] Each eye's bounds, viewport, aspect and field logged once a map (and
  on a change), with an asymmetry warning; the cube-map/2D-bitmap error once
  a bitmap, then a count every 2000; stream-buffer wraps name the pass.

## HALOFREAK95 (jcompto95-tech)

- [x] Searched: no public Halo 2 animation or dual-wield source.
  jcompto95-tech/OpenCE's branches equal ours (`refs/jc/*`); its only open
  PR is fast decals (held back since Test70, unmeasured on a headset);
  upstream OpenCE build-208 has 5 new commits, none about animation.
- [?] The owner is asked for the link to these updates.

## Not changed

- Network 29 and its protocol, voice chat, the custom campaigns' installs,
  manual reload: as Test71.
