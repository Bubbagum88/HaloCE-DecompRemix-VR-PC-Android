# Game data compatibility and graphics evidence

Updated 2026-10-08 with the supplied USA image comparison. Disc labels and installed cache formats are different facts.

The supplied USA Original, Rev 1 and Rev 2 XISOs all contain the same 24 map files, verified by full SHA-256, and pass the production Java importer. See [USA image comparison](USA-IMAGE-COMPARISON.md). The historical test17 observations below are retained for context; their statement that no local comparison was available is superseded by this audit.

## What is established

The inherited decomp target is the Xbox PAL debug build 2342, not a restriction that every player's disc must have that label. The port's cache code recognizes Xbox cache format 5 and build strings `01.01.14.2342`, `01.10.12.2276`, and `01.08.15.1749`; its existing PAL tag normalization remains automatic. Launcher **Game data & compatibility** reads the installed header/build/type and can compute per-file SHA-256 fingerprints locally. The report is added to the existing launch log; it uploads nothing.

The exact owner-supplied USA Original, Rev 1 and Rev 2 images were compared: all 24 stock maps have identical full-file SHA-256 values, and all three pass the production importer. Their whole-image sizes and non-map file inventories differ, primarily under `xdemos`. The launcher continues to recommend the original XISO as a conservative baseline; the tested Rev 1 and Rev 2 images are also accepted and no map-content difference was found. The filename/label still does not authenticate disc provenance, and this sample does not cover other regions, modified images or every device/gameplay path. The evidence does not support blaming the observed scope or geometry reports on a map difference among these three supplied sets. See [the image comparison](USA-IMAGE-COMPARISON.md).

The complete supplied USA images were independently traversed and fingerprinted; production import finished all three as the same managed data set. This verifies container parsing, map inventory/content equality and import deduplication for these exact files, not a three-image headset or live-server play test. The launcher fingerprints current maps but cannot infer which whole-disc revision a remote server uses because the directory does not publish authoritative per-map hashes. See [Game files & versions](GAME-DATA-LIBRARY.md). Maps with incompatible format/build cannot be selected for launcher PvP hosting. Custom content remains experimental and needs matching resources on peers.

## Geometry changes

- Stream and index uploads now copy the actual payload length, reserving alignment padding separately. Tests use exact-sized allocations under AddressSanitizer.
- Persistent-buffer availability is tracked per ring slot; failed immutable allocation/mapping gets a new mutable buffer before fallback.
- A failed frame-fence wait completes queued GPU work before reusing storage.
- Static mirror writes use ordered `glBufferSubData`, including first writes. Adapted from [Andiweli/HaloCE-Android-AAOS a88f257](https://github.com/Andiweli/HaloCE-Android-AAOS/commit/a88f25763b8a51335554ef02e613127ee92677d4), whose diagnostic described zero GPU pages despite populated CPU geometry. Its global 30 FPS/interpolation-off policy is not imported.
- **Geometry compatibility > Safe** bypasses persistent streaming, static mirrors and GPU base-vertex rebasing. Restart required; potentially slower. Safe is the VR default since test16, including one-time migration; Normal remains the flat default.

The owner reports Safe fixed the submitted bridge rendering fault. This is a specific device/scene result; other scenes and devices remain unverified. Keep the launch log and data fingerprints when reporting a new issue.

## Networking is separate

Native v9/v10/v11 protocol support concerns message layouts, not disc revision names. Retail PC/Custom Edition/MCC/Xbox multiplayer protocols cannot join native-port games merely by choosing different data. Co-op needs matching mission/resource content and the campaign-capable project build. Unsupported/missing maps, full/closed sessions, expired invites and NAT failure can independently prevent joins.

Header-format reference: [SnowyMouse's Halo cache documentation](https://gist.github.com/SnowyMouse/39168bddd597549038a35d78aee39513), CC BY 3.0, author attribution retained. The launcher checks the 2048-byte header, signatures, format, build string and type; it does not authenticate a whole map from its header.


## Test17 join investigation

Different ISO/revision or modified map files can cause content incompatibilities;
the launcher now explicitly says so in both browsers and the data screens.
Revision names alone do not establish a cause. The supplied test16 failures
instead exposed a PvP in-progress/campaign flag collision and an unmasked
keyboard action-only control bit. [Detailed evidence](TEST17-PROGRESS.md).
The native map guard retains recognized cache-build checks because distributed
object/damage messages refer to tag definitions. The public feed does not
advertise per-map hashes or disc revisions, so set selection offers maps by
availability and never claims a verified per-server revision match.
