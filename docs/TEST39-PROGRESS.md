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

All 84 regression suites passed; cache-format pytest had 127 passes and four
optional map fixtures skipped. The Quest and flat native/Gradle builds passed,
and the final package gate verified signatures, build identities, APK contents,
flavor/network parity and source/build archives. The first Quest compile caught
and fixed a C89 loop-scope issue before the final build. Exact APK hashes and
package checks are in [TEST39-DELIVERY.md](TEST39-DELIVERY.md) and the generated
manifest. Headset, Android-device, heat-weapon and live co-op acceptance remain
the owner's test; compilation and sanitizer fixtures are not runtime proof.
