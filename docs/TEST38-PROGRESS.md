# Test38: interaction and compatibility work

## Packaging override and baseline (2026-10-08)

The owner's latest usage-limit override is to finish current work and package
both private APKs now. It supersedes the earlier all-features packaging hold.
Source is frozen; validation and packaging continue without feature expansion.
Target `1.0.19-test38`, code49, on `test38-interactions-compatibility`.
Public v1.0.18 remains the accepted baseline. Publication and installation are
not authorized.

[TEST38-DELIVERY-STATUS.md](TEST38-DELIVERY-STATUS.md) is the authoritative
completed/remaining/restricted/unstarted disposition. New physical modes remain
opt-in. Preserve working mobile/VR behavior, saves, signing identity and network24
hosting. Automated checks do not establish device or live cross-play acceptance.

## Scope ledger

| Work | Status | Evidence / next step |
| --- | --- | --- |
| Scope adjustment for all applicable weapons, including SPNKR (issue #2) | Implemented / tests passing | All gun-class profiles; preserves authored zoom availability and legacy keys. |
| Vehicle/turret reticle snapping: Shade, Ghost, tank | Implemented / tests passing | Mounted preview used native target attraction; now uses existing geometric convergence. Real shot logic unchanged. |
| Original, Rev 1 and Rev 2 XISO comparison | Completed supplied-image audit | All 24 maps byte-identical; production importer recognizes/deduplicates identical map sets. USA-IMAGE-COMPARISON.md. |
| Legacy co-op client support across feasible network versions | Implemented / wire tests passing | Campaign 15-24 normally supported; 12-14 use an explicit legacy opt-in with old-host allegiance limitations;11 predates co-op. Hosting24/PvP retained. |
| Manual physical reload M1-M11 | Implemented / integration review | Seven verified model profiles; native ammo conservation and cancellation tests. MANUAL-RELOAD.md. |
| Finger/palm contact M12-M29 | Implemented / integration review | Bounded volumetric feature queries, intermediate pose search, contact-entry haptics, grip priority. |
| Vehicle physical handle grabbing/steering | Implemented / integration review | Optional vehicle-specific virtual controls, independent visibility and position/size adjustments; native steering fallback. |
| World/object/NPC/ragdoll/impact interactions W1-W66 | Implemented / device checks pending | Loose items and eight scenery tags; eight native NPC species, articulated recovery and authoritative impacts. Enhanced co-op supports at most four remote peers; restrictions are recorded in TEST38-DELIVERY-STATUS.md. |
| Adjustable closer-contact radius | Implemented / integration review | AUTO with grabbing; occupied-space expansion guard; offline native capsule. |
| Optional parkour | Implemented / device checks pending | Solo-only wallrunning, climbing, walljumps and look-directed leaps; native collision retained. |
| Documentation and diagnostics | Source frozen / delivery reconciliation | Exact disposition in TEST38-DELIVERY-STATUS.md; preserve complete M28/W58 physical test checklists. |
| Quest and Android candidate packages | Authorized / validation and packaging | Latest usage-limit override authorizes packaging current work; do not claim headset verification. |

Keep Astra for architecture, physics, protocol and regression diagnosis. Luna is
suitable later for bounded documentation/checklist reconciliation once behavior
and evidence are established; do not switch the main reasoning task prematurely.
