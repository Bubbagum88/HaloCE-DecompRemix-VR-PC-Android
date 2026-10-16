# Test72 delivery status

Private **1.0.39-test72 / version code 84**, branch
`test39-interaction-completion`. Test70 (published as v1.0.37) plus Test71
(never delivered on its own) plus the Test72 multi-platform work and the
owner's separate VR refinement pass. Local commits only: no push, tag,
publish or install.

## Builds and source

**Pending the single build pass.** The owner's rule for this delivery:
"dont build anything until EVERYTHING is done". The Windows flat and PC VR
executables and the Android flat native code were built earlier in the work
(see below); every change since is compiled, tested and packaged together
in one pass from one commit. That pass fills in this section: folder,
runtime source commit, each package's bytes and SHA-256, and the toolchain.

## How far each platform is verified

Levels: **implemented** (source done, source checks pass), **built**
(compiles and links), **runtime-validated** (run here, off the headset),
**hardware-tested** (on the device itself).

| Platform | Package | Implemented | Built | Runtime-validated | Hardware-tested |
|---|---|---|---|---|---|
| Quest 3 / 3S / Pro / 2 | universal VR APK | yes | before the refinement pass; again in the build pass | no (no headset here) | owner's tests pending |
| Pico 4 / Neo 3 / 4 Ultra | the same VR APK | yes (profiles vs the registry) | as above | no | no |
| Steam Frame | the same VR APK | yes (profile vs Valve's document) | as above | no | no |
| Android phones and tablets | flat APK | yes | native code before the refinement pass; again in the build pass | no | owner's tests pending |
| Windows, flat | `halo.exe` + launcher | yes | yes (launcher: in the build pass) | main menu reached; XISO import verified; stereo 3D measured on frames | no |
| Windows, PC VR | `halo-vr.exe` | yes | yes (links) | waits on the owner's OK for SteamVR's null driver | no |

## What changed

See TEST72-CHECKLIST.md for every item and its verification, and
TEST72-FIELD-GUIDE.md (the in-app guide's first section) for the player's
view. In short:

- One VR APK for Quest, Pico and Steam Frame, with button names by device.
- Windows: flat and PC VR builds sharing one folder, one library and one
  launcher (import, verify, repair, custom campaigns, settings, What's New,
  updates on request); flat stereo 3D; the remap UX.
- Flat (Android and PC): sprint, slide, wall run, wall jump.
- VR fist combat: longer leaping lunges, intent from the fist's path,
  skeleton hit assist, the held and seated enemies, the Shade death fixed,
  freeflow combo and its display, durability by difficulty.
- VR menus: Bullet Time on LOCOMOTION, IMMERSION's missing toggles,
  per-weapon SCOPES, world-anchored menus; left-hand mode by the physical
  letters with Back on B; Bullet Time in vehicles; passengers aim by hand.
- The left eye's garbling: the first eye begins from state set anew; EYE
  ORDER to tell the first pass from the left eye; `[vr-eyes]` in the log.

## Open

- PC VR runtime validation: needs the owner's OK to use SteamVR's null
  driver on this PC.
- Pico, Steam Frame and other headsets: untested on hardware.
- The left eye: confirmed gone only by the owner's EYE ORDER test.
- HALOFREAK95's Halo 2 animations and dual wielding: no public source found;
  the owner is asked for the link.
