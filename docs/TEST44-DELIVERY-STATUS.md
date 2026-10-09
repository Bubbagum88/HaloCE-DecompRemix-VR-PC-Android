# Test44 delivery status

Private candidate `1.0.25-test44`, Android version code 55, branch
`test39-interaction-completion`. Public v1.0.18 and the Test43 candidate remain
unchanged. Do not publish, install or launch the game. PC/Steam Frame remains
deferred.

## Candidate changes

- Clarifies in first-run onboarding, the main launcher and the game-data manager
  that Android picker imports copy supported maps only. The original ISO/XISO
  remains at its original location and the launcher cannot delete it; use
  Android Files. Only image copies placed in the managed inbox can be removed
  from the launcher.
- Explains that first-run imports become the protected **Existing game data**
  base set, so its disabled **Currently selected** row is expected when it is
  the only set. Additional selectable sets are imported from the manager.
- Refines the opening A10 look-calibration input: fresh valid hand-reticle rays
  drive directional look actions and script point-gaze checks. Head-aim mode
  and all non-A10 maps retain head-based behavior; stale/invalid rays during
  hand aim pause calibration progress instead of crediting head movement.
- Makes physical acquisition contact-driven throughout: NPC/enemy and loose
  object grabs require palm-sphere overlap with authored collision; solo and
  co-op host paths validate contact. Climbing requires wall-surface contact;
  reload pickup requires touching authored part bounds or a configured pouch
  contact point; optional wheel steering requires touching its virtual handle.
  A fresh Grip/selected-input press is required at contact. Aim direction and
  target-search rays cannot acquire these actions. Magazine socket alignment is
  a separate placement phase.
- Retains all Test43 and prior functionality. No general mission AI, weapon aim,
  reticle rendering, networking, saves, Android touch or Safe Geometry behavior
  is intentionally changed.

## Verification

Automated results, build manifests and artifact hashes will be recorded here
after both APK workflows and the package gate complete. Device acceptance is
pending. Passing source tests and package checks cannot verify the authored A10
tutorial sequence on a headset.

| Edition | File | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Quest / VR | pending | pending | pending |
| Android / flat | pending | pending | pending |

Candidate package directory: pending. No publication, installation or game
launch is authorized.
