# Test39 device acceptance checklist

All items below are pending until exercised on the matching physical devices.
Source tests, APK inspection and compilation do not count as headset acceptance.

## Regression baseline

- Install VR and flat APKs over the matching existing packages; confirm no data loss.
- Quest starts in VR; Safe geometry default behaves as expected.
- Flat Android touch UI remains visible/usable and connected gamepad/touch behavior is unchanged.
- Load and resume a campaign save; verify checkpoints and configuration persist.
- Join/host ordinary PvP and campaign co-op with Test39 and a prior compatible build.
- Verify menus, network browser, server setup and version selector.
- Check scope zoom with one- and two-handed weapons; verify SPNKR and every supported scope class.
- Test Shade, Ghost, tank and Warthog mounted reticles with each configured aim source.
- Enter/exit each vehicle and passenger seat; confirm camera/recenter and glass settings.

## Shake cooling toggle

- Confirm **SHAKE COOLING** defaults OFF after clean install and remains OFF after update.
- Confirm OFF reproduces normal native overheat/cooldown behavior.
- In solo VR, overheat a supported weapon and verify deliberate back-and-forth motion speeds cooling.
- Compare one-way movement, head motion, small tracking jitter and controller stillness; none should trigger the bonus.
- Verify it affects only the selected weapon, stops after weapon switch/reload/exit, and never exceeds the authored base cooling rate by more than the configured cap.
- Confirm the effect is inactive in PvP, co-op, seated play and while VR/controller tracking is unavailable.

## Weight haptics and interactions

- Confirm **WEIGHT HAPTICS**, **CUSTOM SCENERY** and **CUSTOM NPC RIGS** default OFF.
- With haptics enabled, move a light and heavy supported object and verify pulses are brief, comfortable and rate-limited on either hand.
- Confirm haptics stop after release, menu/session reset, tracking loss and online transition.
- Test eligible unnamed custom scenery; verify scripted, animated, structural, malformed or unsupported scenery remains fixed.
- Test supported Elite and opt-in alternate Assassin variants; confirm unknown/custom skeletons remain untouched.
- Re-run Test38 grasp, throw, impact, ragdoll recovery, wall collision, release and mission transition cases.

## Cross-device networking

- Quest host + Quest client, Quest host + Android client, Android host + Quest client.
- New/new, Test38/new and new/Test38 peer combinations; mixed/stock clients fall back cleanly.
- At 1–4 remote machines verify eligible NPC interactions/palette interpolation.
- At five or more remote machines verify world-object interaction remains available while NPC interaction and custom NPC poses fall back to native.
- Test disconnect/reconnect, stale capability lease, lost/reordered packets, checkpoint/map transition and a peer changing game state while holding an object.
- Measure host bandwidth, send queues, Quest CPU/frame timing and co-op stability at several actual player counts. Do not mark 128-player campaign safe from a source fixture alone.

## Remaining physical systems

- Manual reload with each authored weapon profile, both handedness settings, pouch positions, partial ammo, cancellation, death, vehicle entry and network fallback.
- Parkour wallrun/walljump/climb at low frame rate, corners, stairs, map transitions and cancellation.
- NPC species-specific hand requirements, live/dead state, settling, native get-up, AI behavior, checkpoints and mission progression.
- Vehicle third/first-person views, each steering/turret aim source, virtual wheel reach/position/visibility and all seat transitions.

Record candidate version, headset/OS, game revision, host/client role, network
target, exact settings, map/mission, reproduction steps, log and video with every
failure. Send it to **@MeWhenINameMyself** or https://discord.gg/S9uSCKxKx.
