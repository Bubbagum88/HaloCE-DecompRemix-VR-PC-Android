# Test39 progress and upstream check

## Upstream check — 2026-10-08

The official [OpenCE releases page](https://github.com/OpenCommunityEdition/OpenCE/releases)
currently lists **Build 157 (`73dc01d`)** as Latest. Test39 continues the
project's already integrated Build157/network24 base; no newer release was
available to integrate at this check. Build157's release note is about stereo
world-sound fading. This pass does not alter that audio behavior or claim a new
upstream merge.

## Work in this pass

The Test38 candidate work was reviewed for preserved behavior, then this pass
adds a toggle for the user's shake-to-cool feature, bounded local weight
haptics, narrowly scoped custom scenery/NPC opt-ins and a revised optional
interaction capability budget. The exact implementation and boundaries are
recorded in [TEST39-DELIVERY-STATUS.md](TEST39-DELIVERY-STATUS.md),
[TEST39-INTERACTION-NETWORK.md](TEST39-INTERACTION-NETWORK.md), and
[TEST39-REQUIREMENT-DISPOSITION.md](TEST39-REQUIREMENT-DISPOSITION.md).

The existing Test38 shake-proof path does not change when the new toggle is
OFF. Native weapon cooling remains authoritative. Physical reload and parkour
remain solo-only rather than bypassing native multiplayer ammo/movement
authority. This is a deliberate safe boundary, not an assertion that every
requested multiplayer feature is finished.

## Build and acceptance status

Source regression, Quest native/Gradle, flat Android native/Gradle, signing,
APK parity and packaging results are recorded in
[TEST39-DELIVERY.md](TEST39-DELIVERY.md) after the final candidate build.
The matching candidate source archive and `manifest.json` travel with the
private package. Headset, Android device, heat-weapon and live co-op acceptance
remain the owner's test; no runtime claim should be inferred from compilation
or host sanitizer fixtures.
