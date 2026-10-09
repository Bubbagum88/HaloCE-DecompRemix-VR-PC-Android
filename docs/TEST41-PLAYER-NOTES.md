# Test41 private test build — 1.0.22-test41

This is a private Quest VR and Android test candidate, not a public release.
It retains OpenCE Build157/network24, Test40 interaction features and the
published v1.0.18 baseline.

## Solo session confirmation

The supplied logs include one multiplayer match and a separate solo saved
campaign loaded after an invite arrived. The pending invite did not complete a
network join; it did not turn the saved campaign into a network game. The
second log's repeated manual-reload bounds lines also prove the local-only
reload path was reached. Test41 logs a `VR interactions: session=...` line when
session/settings change; look for `session=local(0)` during solo play and
`network-client` or `network-server` only after a real join/host session begins.

## Physical interaction changes

- **GRAB REACH** in VR Controls covers 12 to 40 cm (12, 18, 25, 30 or 40 cm).
  New settings
  default to 25 cm. The old world/NPC surface checks were fixed at 12 cm. Try
  30 cm first if contact has been difficult. Solid collision, target identity
  and line of sight are still checked; the maximum does not allow reaching
  through walls.
- **NPC RIG SLOTS** allows 1-8 simultaneous physical NPC interaction rigs;
  new settings default to eight. It limits how many NPCs this VR interaction
  system can manipulate at once. It does not change Halo's native corpse
  ragdoll limit. Existing saved values are preserved.
- The session log reports actual local/network mode, active interaction options,
  configured reach, pool capacity and haptics strength when they change. It does
  not prove an interaction succeeded; use the action checklist when retesting.
- After enabling an interaction or returning from a menu/reset, release the
  controller grip fully and squeeze again. World/NPC grabs intentionally require
  a fresh grip press after reset so a held controller cannot unexpectedly grab
  something; the same fresh-press behavior is used by the manual reload state
  machine.

## Prior opt-in options and limits

**CUSTOM NPC RIGS**, **MAG DEBRIS**, **LIFT VEHICLES** and **NPC RESCUE** remain
off by default and preserve their Test40 limits. Enabling CUSTOM NPC RIGS also
enables NPC GRAB; MAG DEBRIS also enables MANUAL RELOAD. Vehicle lifting is
independent of WORLD GRAB, but only accepts supported unoccupied vehicles and
applies bounded vertical motion. Rescue applies only to eligible live
encounter actors after ten seconds of unsupported falling. Manual reload and
parkour remain solo-only. **HAPTICS** is the only vibration control and scales
every effect. Load feedback follows that setting automatically during eligible
local interactions when meaningful strain or motion occurs; a static light
hold is not expected to buzz continuously.

Test41 corrects the hard-coded NPC/world contact distance, maps broad root or
unspecified NPC collision hits to a nearby authored joint, applies the same
configured reach to wall climbing, and releases parkour hand ownership when
disabled. These source paths and the actual production NPC eligibility gate
have host fixtures; Quest action tests remain pending. If an enabled option
still has no effect, provide the full log and report solo/network state, map,
target type/distance, setting, hand and grip/action used. Public v1.0.18 remains
the published release.
