# Test50 private candidate notes

Test50 builds on Test49 without changing the network protocol, voice routing,
capture policy, or existing hold-to-sprint behavior.

## New VR option: toggle sprint

In the VR settings, open **Locomotion**:

- Enable **Button Sprint** to use left-stick click for sprint.
- **Sprint Toggle** defaults to **Hold** to preserve the previous behavior.
  Choose **Toggle** to click once to start sprinting and click again to stop.
- Button Sprint continues to reserve left-stick click while enabled. Disabling
  it restores the prior button assignment when it has not been changed since.
- Sprint is local/offline movement only and follows the existing speed limits
  and movement guards; it does not change network movement or gameplay inputs
  used by other players. Recenter, loss of focus, seating, or loss of the VR
  input state cancels a toggle latch.

## Mounted vehicle and turret reticles

The supplied Test49 log includes shots while seated in a Ghost and a Scorpion.
Shot diagnostics measured the displayed reticle about 2.3–2.6 degrees from the
final shot direction. Source comparison identified why: mounted sights used
the weapon's muzzle ray, while native aim assist corrected the fired projectile
against the game camera. That camera can differ from the selected VR controller
or head aim, which also caused target-snapping behavior. Test50 keeps mounted
reticles on the selected weapon/muzzle ray and bypasses camera-based aim assist
for the local VR driver/gunner shot, so the visible sight and shot center use
the same aim source. One shared path covers vehicle classes and mounted turrets.
On-foot weapons, passengers, remote players, and flat Android firing keep their
existing native aim-assist behavior; network protocol and vehicle input choices
are unchanged.

Random weapon spread still affects individual projectiles, so the reticle marks
the selected center ray rather than guaranteeing every pellet or round lands on
one pixel. The shot log now names the mounted role and records reticle error
against both pre-assist aim and final shot for future reports. Verification is
source/test based; a headset test must confirm the visible tank and turret
impact alignment.

## Voice-chat diagnostics

Voice chat behavior is unchanged. Logs now distinguish the host's voice
settings, local microphone mode and incoming volume, encoded frames submitted
to the network path, remote frames accepted/relayed, and Opus frames decoded
into the playback queue. The first successful remote decode is logged without
recording audio or player names. A host that sends no Build167 voice settings
is reported after five seconds and capture remains closed.

Use **Audio settings** or the VR **Voice Chat** page to select Off, Push to Talk,
or Open Mic and adjust incoming voice volume. On a host, allow lobby voice and
choose an in-game routing mode in **Server Setup**. Every relevant peer must
support the Build167 voice messages; no separate voice-capability negotiation
exists. An opened microphone proves permission/device initialization only; it
does not prove that speech was encoded or that another player sent audio.

## Upstream review

OpenCE Build177 remains the newest official release checked on 2026-10-10.
Test49 already has its exact-match reticle/scope artwork integration. The
current engine base remains Build157/network24 with selected compatible changes
through Build177; this candidate is not a full Build177 rebase and does not
change network compatibility. See [Test47's Build177 integration review](TEST47-OPENCE177-INTEGRATION.md).

## Validation limit

Source and host tests verify toggle edges, recenter cancellation, eligibility
guards, the mounted driver/gunner direct-fire selection, on-foot and passenger
aim-assist preservation, voice diagnostics wiring and builds. They cannot prove
sprint feel, in-headset vehicle reticle alignment or two-headset voice playback.
Use [TEST50-DEVICE-CHECKLIST.md](TEST50-DEVICE-CHECKLIST.md) for those tests.
