# Halo CE Quest VR + Android 1.0.20-test39

Private candidate for owner testing. Android version code 50. The accepted
public baseline remains v1.0.18; this candidate is not a public release and
has not received headset or live-network acceptance. The Quest/VR and flat
Android apps remain separate packages. Install over the matching app; do not
uninstall to update because that removes app data. Keep a save backup and
provide your own supported Halo CE game data.

## Main changes in Test39

- Optional **SHAKE COOLING** toggle for offline VR. It is OFF by default and
  is in the VR menu's Controls page. When an overheated, currently selected
  weapon is held, deliberate back-and-forth controller motion can speed its
  normal native heat recovery by up to 2.5x after repeated reversals. One-way
  movement, a single accidental reversal and head motion alone do not count.
  Native heat thresholds, weapon state and normal reload
  behavior are unchanged. This feature is automatically inactive online.
- Optional **WEIGHT HAPTICS** (OFF by default) gives sustained, low-amplitude
  local feedback for resistance and strain while handling objects. This is an
  approximate comfort cue derived from motion and the bounded interaction
  solver, not a measurement of an object's physical mass. It is not relayed to
  remote players and is inactive online.
- Optional **CUSTOM SCENERY** (OFF by default) permits a narrow set of unnamed,
  unanimated, non-scripted scenery with valid bounded collision geometry to
  use the existing constrained box-grab solver. It does not make arbitrary,
  structural or animated level scenery movable.
- Optional **CUSTOM NPC RIGS** (OFF by default) admits only the alternate
  Assassin actor enum that aliases the native Elite behavior and rig family,
  and only after the normal graph/node validation succeeds. It does not accept
  arbitrary custom skeletons, unknown races or swarm actors.
- Networked world-object grip intent and host decisions are no longer rejected
  solely because a session has more than four remote machines. They remain
  gated by host permission, peer capability negotiation, ownership checks,
  range checks and leases. The native transport's 128-machine table is the
  implementation ceiling, not a verified campaign player-count promise.
- Articulated NPC pose synchronization remains capped at four remote machines.
  Above that, NPC poses/custom NPC interaction fall back to native behavior;
  this avoids sending a full joint palette to every peer at an unbounded rate.
  Native co-op capacity and campaign settings are unchanged by this feature.

## Controls and options

Open the VR settings menu and use **Controls** and its page arrows to reach:

- **SHAKE COOLING**: OFF / ON. New installs default to OFF.
- **WEIGHT HAPTICS**: OFF / ON. New installs default to OFF.
- **CUSTOM SCENERY**: OFF / ON. New installs default to OFF.
- **CUSTOM NPC RIGS**: OFF / ON. New installs default to OFF.

These are independent toggles. Existing world/NPC grab, manual reload, parkour,
vehicle, body, contact, scope and controller controls retain their prior
settings and behavior. Offline-only systems stay inactive in network games;
networked interactions require the host's **VR INTERACTIONS** permission and
successful peer negotiation.

## Existing features carried forward

Test39 is based on the Test38 candidate and carries forward its scope profiles
for every weapon class, mounted vehicle/turret reticle changes, physical reload
profiles and pouch locations, hand/world/NPC interaction modes, bounded ragdoll
recovery, impact controls, close-contact radius, optional parkour, and
vehicle-specific virtual steering controls. It also retains the earlier
network-version selector, OpenCE browser, Safe geometry defaults, Android
touch/gamepad controls, and the user's prior VR settings.

Normal button reload remains available and native. Manual physical reload and
parkour remain solo-only because this build does not add the host-authoritative
ammo-phase/cancellation or movement protocol required to synchronize them with
unmodified peers. Physical vehicle handles are steering controls; lifting or
carrying whole vehicles is not implemented.

## Compatibility and remaining boundaries

- Hosting remains network version 24. Client target and map/revision rules are
  unchanged from v1.0.18; the original Xbox Halo CE XISO remains recommended.
- Campaign player-count options remain those supplied by OpenCE. This candidate
  does not add or validate a 128-player campaign mode. A 128-machine transport
  table and a high-player PvP session do not prove campaign spawning, AI,
  checkpoints, vehicles or transitions at that scale.
- Enhanced world-object interactions can negotiate above four remote machines,
  but no 128-peer headset/network session was run. NPC interaction and
  articulated poses are intentionally unavailable above four remote machines.
- Arbitrary custom NPC skeletons, arbitrary scripted/animated scenery, persistent
  discarded physical magazines, whole-vehicle lifting and automatic
  mission-critical NPC rescue are not implemented. Their safe behavior cannot
  be inferred from generic tag names alone.
- PC/Steam Frame remains deferred.

For crashes, desync, lost interactions or unexpected cooling, send the exact
candidate version, headset/OS, game revision, host/client role, network target,
settings, reproduction steps and the generated game log to
**@MeWhenINameMyself** or https://discord.gg/S9uSCKxKx. Do not share game images
or signing keys.
