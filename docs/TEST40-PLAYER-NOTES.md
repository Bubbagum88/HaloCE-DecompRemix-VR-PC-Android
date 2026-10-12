# Test40 private test build — 1.0.21-test40

This is a private Quest VR and Android test candidate, not a public release.
It keeps OpenCE Build157/network24 and carries the previous candidate's
features forward. The four new interaction options below are experimental,
VR-only and OFF by default.

## New options

- **CUSTOM NPC RIGS:** permits a narrowly validated, unclassified humanoid
  biped graph in solo play. Known enemy types keep their existing behavior.
  It cannot map every custom skeleton; unknown or unsafe graphs are ignored.
- **DROPPED MAGAZINES:** keeps supported physical reload magazines visible
  after ejection. Debris has gravity and world collision, remains until a map
  or game-state reload, and uses a 32-magazine pool that replaces the oldest when
  full. It is visual only: magazines cannot be picked up, and ammo is not
  changed by the debris. Requires manual reload. The VR menu label is
  **MAG DEBRIS** to fit the settings page.
- **LIFT VEHICLES:** with **WORLD GRAB** enabled, a free hand can use vertical lifting
  on eligible unoccupied Warthogs, Ghosts, Scorpions and turrets. Native gravity
  and collision stay active. Horizontal carrying and rotation are not included.
- **NPC RESCUE:** after an eligible live encounter NPC has been falling
  unsupported or outside the map for 10 seconds, it may return to its last
  grounded pose if the full standing space is clear. It does not revive or
  respawn characters or take over active mission scripts.

Find these toggles in the VR settings controls pages. They are local/solo
features and automatically retain stock behavior online. The new settings
default OFF. Disable them to compare against the prior baseline.

## Retained multiplayer and VR behavior

Hosting remains on OpenCE network version 24. Test39's client network selector,
population-sorted server list, native co-op, controller/touch support, and
previous VR settings remain carried forward. **SHAKE COOLING** and
**WEIGHT HAPTICS** remain opt-in and solo-only. When enabled, bounded,
rate-limited load pulses cover held props, supported NPC limbs and vehicle
lifting. Grab/acquisition pulses and fingertip collision contact pulses use the
regular **HAPTICS** strength setting and remain available independently.
Enhanced world-object interactions can negotiate within the native 128-machine
table when every
peer supports the capability; articulated NPC pose synchronization remains
limited to four remote machines. This does not enable or certify a
128-player campaign. Manual reload and parkour remain solo-only.

## Testing notes

Please report the headset/model, game image revision, selected settings, map
and mission checkpoint, and attach the generated game log. For custom rigs,
include the map/tag name and whether the NPC is alive or a corpse. For
magazines, report weapon, handedness and whether a map/checkpoint reload cleared
them. For a lifted vehicle, include vehicle class and whether it was named or
occupied. For rescue, note the NPC and the location where it became stuck.

This candidate has automated source and package checks, but has not yet been
accepted on a Quest/Android device or in live co-op. Public v1.0.18 remains the
published release; do not treat this candidate as a release announcement.
