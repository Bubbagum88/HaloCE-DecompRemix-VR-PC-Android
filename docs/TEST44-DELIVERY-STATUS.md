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

- `tools/run-quest-checks.py`: all suites passed. The Quest and flat build
  workflows each reran the full regression gate successfully.
- Quest and flat APK builds both succeeded from runtime source commit
  `547f1234`. The Quest build was cleaned and rebuilt after the packaging gate
  detected stale ZIP records; the final clean artifact passed the orphan-data
  check and contains the VR scope/settings markers.
- `tools/package-quest.py`: passed signing-certificate, package/version/ABI,
  APK integrity, launcher art, content, networking and app-class parity checks.
  The two APKs share version code 55 and min SDK 28.
- Focused contact tests passed for solo and host-validated co-op enemy/object
  grabs, fresh Grip edges, parkour contact, reload part/socket contact and
  virtual vehicle handles. The device checklist remains pending: automated
  collision/API tests do not prove Quest hand feel or two-headset co-op behavior.
- No APK was installed or game launched. This remains a private test candidate,
  not a published release.

| Edition | File | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Quest / VR | `HaloCE-Quest-VR-1.0.25-test44-Quest.apk` | 35,436,978 | `15b74913a541cbd2ca79e537eae97a735806a1d6ef551e1cd2628487a31e647a` |
| Android / flat | `HaloCE-Quest-VR-1.0.25-test44-Android.apk` | 33,271,891 | `ded2a6850b525da23161c7bdbed1475b32669a38bd119a6242c834f5c15cde49` |

Candidate package directory: `D:\HaloQuest\builds\test44-20261009-v1.0.25-test44-contact-verified-final`.
No publication, installation or game launch is authorized.
