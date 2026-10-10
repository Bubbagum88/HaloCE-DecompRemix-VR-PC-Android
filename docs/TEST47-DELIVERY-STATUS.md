# Test47 private candidate delivery status

**Superseded by private Test48.** The owner's Quest log showed live weapon
datum handles with negative signed values. Test47 rejected them in grip
release, holster storage/pruning, and pending-release recovery; see
`TEST48-REGRESSION-AUDIT.md`. Preserve these original Test47 artifacts and
hashes as historical records; do not retest or distribute them as the current
candidate.

Candidate target: **1.0.28-test47 / Android version code58**, branch
`test39-interaction-completion`, based on OpenCE Build157/network24 with the
selected Build167 and Build169-177 changes documented in
[TEST47-OPENCE177-INTEGRATION.md](TEST47-OPENCE177-INTEGRATION.md). This is
not a full Build177 engine rebase, and network24 is unchanged. Public
v1.0.18 and all older candidates remain unchanged. This is a private test
delivery only; do not publish, install, or launch it.

Both APKs and matching source/build ZIPs are packaged in
`D:\HaloQuest\builds\test47-20261010-v1.0.28-test47-final`. The APK pair was built
from runtime commit `9d62e1a0`; the manifest records the runtime-source and
source-documentation commits separately. Public v1.0.18 remains published.

## Changes completed in source

- **Hand stretch (priority fix):** the arm IK solver preserves the authored
  upper-arm and forearm lengths. It clamps the wrist target to the reachable
  range and keeps the existing bounded shoulder adjustment. It no longer
  stretches bones by up to 18% or compresses them to 65% to chase the hand.
- **Manual reload/ejection input:** manual reload now reads the configured VR
  USE/RELOAD action from the mapped controller state in addition to the native
  weapon reload bit. A rising edge is detected across the render/game-tick
  boundary; the native bit remains a fallback. Reload still requires actual
  palm contact with the authored magazine/chamber or pouch, followed by a
  fresh Grip/Trigger action. The normal action cancels an active transaction.
  Right-stick click remains melee; no duplicate binding was assigned.
- **Reload diagnostics:** bounded state-change records include controller
  Grip/Trigger, mapped action and native reload bits, authored part/pouch
  contact, current interaction owner, weapon phase, reserve and attempted
  action. Failed grip ownership is logged. Identical frames do not flood logs.
- **Solo multiplayer-map spawn:** local New Game loads of multiplayer scenarios
  clear and bypass a stale campaign continuation unit. They preserve a valid
  native game-type spawn when the local engine is running, otherwise use a
  validated in-BSP scenario player start or non-teleporter netgame marker, and
  select the multiplayer biped. Network matches and campaign scenarios remain
  on their existing spawn paths. Logs identify selected source, placement,
  assigned unit, BSP leaf, and failure reason.
- **Native corpse retention:** the **BODY RETENTION** setting raises the engine's active-garbage trigger/target
  higher in solo VR campaign by default (75/45 per 16 players) with a 100/60
  option and a STOCK 50/30 choice. Any network or multiplayer session keeps
  upstream thresholds. This preserves eligible offscreen corpses longer, but
  corpses share the pool with other garbage and hard memory/object pressure can
  collect earlier; it is not an exact corpse-count cap.
- The previously requested interaction, parkour/reload, haptic, magazine,
  vehicle-lift, NPC recovery, voice, Android control, launcher, revision,
  network/co-op, Safe Geometry and VR features remain carried forward as
  itemized in [TEST47-REQUIREMENT-DISPOSITION.md](TEST47-REQUIREMENT-DISPOSITION.md).
- The candidate includes the selected OpenCE Build177 weapon reticle artwork
  plus compatible upstream tag, co-op respawn, Android cleanup and memory
  fallback changes. Build174's UI rendering patch was not applied because its
  renderer/asset changes conflict with customized menu paths; see the upstream
  integration audit.

## Verification state

Focused host checks pass for manual reload transaction/input math, local
multiplayer-map spawn classification and start selection, arm reach math under
AddressSanitizer/UndefinedBehaviorSanitizer, the Test46 cumulative candidate
guards, pending weapon-release recovery, Build177 asset integration, and the
deterministic pagemap-denied memory fallback harness. The complete Quest
regression suite passed with no failed suites in standalone, VR-build and
flat-build runs. Both release builds completed. The Android guest used
Clang22 and the committed PGO profile. The package gate verified APK structure,
package IDs, version/code, matching network contents, current signing
certificate, selected feature markers, and source/build ZIP integrity. The WSL
container denies pagemap and does not implement `mincore`; the host harness
tests fallback decisions through a deterministic mincore shim, so Quest-device
fallback acceptance remains pending.

| Artifact | Version/package | SHA-256 / record | Result |
|---|---|---|---|
| `HaloCE-Quest-VR-1.0.28-test47.apk` | `com.halo.decomp.vr`, code58 | `0903a602c1f65e6548d399c210a58fb178ddc6adfcdbe8a39396117c6ca39142` | Signed; package checks passed |
| `HaloCE-Android-1.0.28-test47.apk` | `com.halo.decomp`, code58 | `db38dfc6e28a6ae09f6ceaa7ed963ddd239c41e7a1f180954109c6cb6ba77cc8` | Signed; package checks passed |
| `HaloCE-Quest-test47-source.zip` | source commit recorded in manifest | See bundled `SHA256SUMS.txt` | Archive integrity passed |
| `HaloCE-Quest-test47-build.zip` | APKs, manifest, compatibility record and docs | See bundled `SHA256SUMS.txt` | Archive integrity passed |

The Android signing certificate SHA-256 is
`53d416f7e123cc62b749940983209bc9a400002e033fd5f50900d4ffad8e2aa4`.

## Limits and owner retest

Host tests and compilation cannot prove the headset hand shape, tracked contact
fit, native animation feel, game-map spawn behavior, Quest startup, multiplayer
or Android runtime. The exact candidate needs device testing. The updated
reload log is intended to separate a missing controller action from missing
authored-part contact or an ownership conflict. Do not claim the reported
reload or out-of-bounds issue is device-accepted until the owner confirms it.

PC/Steam Frame remains deferred. No release, repository push, app installation,
or game launch is included in this candidate delivery.
