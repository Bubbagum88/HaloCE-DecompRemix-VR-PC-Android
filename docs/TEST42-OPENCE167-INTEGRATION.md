# Test42 OpenCE Build167 integration audit

## Baseline and network identity

The accepted public v1.0.18 build is OpenCE Build157 / network24. The latest
official upstream tag checked for this candidate is [Build167](https://github.com/OpenCommunityEdition/OpenCE/releases/tag/build-167),
commit `f479e34914604df5a22a2bdb0b38f180a1f702d8`. Build167 does not change
network24. The port remains a network24 host; its client selector still covers
compatible client targets 11–24 with the existing campaign/Custom Edition
floors. This candidate does not claim universal compatibility with every
historical server, game image or campaign map.

Build167 changes the upstream application icon. The project keeps the owner's
Halo CE Quest icon (`port/android/art/android-icon.png`) instead of replacing
it with OpenCE branding.

## Selected source changes carried into this candidate

These focused upstream fixes are compatible with the current fork and have
production-source tests:

| Change | Candidate behavior | Focused verification |
| --- | --- | --- |
| Custom Edition map names | Accepts `[ ] ( ) +` map names while rejecting path traversal, unsupported path characters and Windows device-name paths. | `test_opence_167_fixes.py` exercises accepted and refused names. |
| Fixed-size remembered map name | Writes a zero-filled, bounded multiplayer-map name record instead of reading past a caller's short string. | The production copy helper is compiled and tested with short and truncated names. |
| Co-op PVS cluster | Any negative or out-of-range cluster from a peer selects normal PVS rather than indexing outside the cluster array. | The production setter is compiled with negative, upper-bound and valid indices. |
| Grenade spawn inventory | A network-created unit starts with zero predicted grenades until the host inventory arrives, avoiding a local throw the host never saw. | The production reset helper and its placement in unit creation are checked. |
| Grenade shock-wave hit reports | Damage effects caused by the same thrown grenade are recognized for the whole same-tick blast, while the existing source/rate validation stays in place. | The production attribution helper is tested for matching projectile, damage, epicenter and tick. |
| Teleporter correction | A large host correction records the remote player's landing teleporter so the client does not immediately bounce the player back. | The production correction helper is compiled and tested for large versus small corrections. |
| HTTP chunk parsing | Update chunk lengths must start with hexadecimal digits, reject signs/whitespace/prefixes/overflow, and remain within the download-size limit. | The exact parser is compiled and tested with valid chunks, extensions, malformed input and overflow. |
| Android ARM native bridge | When Android reports an ARM native bridge, cached guest-page writes are detected by frame-bounded page hashes because translated guest page faults cannot be handled reliably. Native ARM keeps page protection by default; `debug.memory_watch=false` opts into hashes. | `test_host_watch_hash.py` compiles upstream's hash tracker tests and checks host detection, guest bridge, frame hook and import registration. Runtime logs identify the selected tracking mode. |

The focused upstream regression tests are registered in `tools/run-quest-checks.py`.
The existing Test37 network compatibility rules, all Test38-Test41 local
interaction systems, Safe Geometry migration, mobile controls and user icon
remain intact in the Test42 cumulative candidate.

## Upstream work intentionally not described as integrated

Build157→Build167 also contains changes outside this candidate's verified
scope. Build167 itself is primarily the upstream icon change. In particular,
this candidate does not claim to port or validate OpenCE voice chat/votekick,
the new upstream co-op setup screen structure, desktop-only features, or the
Build165–166 renderer/camera/animation changes. Voice chat needs runtime
microphone permission handling plus cross-version message compatibility; the
renderer/animation changes intersect the fork's stereo renderer, Safe Geometry
path and accepted VR body/hand pose. Importing those broadly without a Quest
session would risk regressions. Existing in-game server browsing and the
project's working lobby UI remain in place.

This is an audit boundary, not a claim that those upstream features are broken.
They require separate, feature-specific integration and verification before
the launcher or release notes can say they are supported.
