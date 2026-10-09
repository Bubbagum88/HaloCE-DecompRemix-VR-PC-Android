# Test43 delivery status

Private candidate `1.0.24-test43`, Android version code 54, branch
`test39-interaction-completion`. Public v1.0.18 and prior candidate packages
remain unchanged. No publication, installation or game launch is authorized.
PC/Steam Frame remains deferred.

## Candidate changes

- Main launcher now displays the selected managed-data label and count and opens
  the profile manager directly.
- Users can switch among distinct imported map sets, rename them, and delete an
  inactive managed copy after confirmation.
- Users can delete ISO/XISO copies stored in the import inbox. Source images
  selected with Android's picker are not stored or deleted by this app.
- Active and base/existing data are protected. Byte-identical map sets still
  deduplicate; Original/Rev 1/Rev 2 are not inferred from filenames.

## Validation

Focused managed-data tests: 97 checks passed, covering selection agreement with
native startup, profile isolation, safe deletion, inbox deletion, malformed
markers and traversal rejection. Launcher tests: 55 state/policy checks passed
and the full Android+SDL Java sources compile against the Android API. The
complete serial regression runner passed all 92 suites with no failures; the
strengthened managed-data fixture was rerun afterward and passed all 97 checks.
Both APK package gates are recorded below after the final build.

| Edition | File | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Quest / VR | pending | pending | pending |
| Android / flat | pending | pending | pending |

Matching build/source ZIP paths and final package manifest: pending.

Source checks do not confirm device storage-provider behavior, visible selector
UX, app update preservation or live gameplay. Device acceptance remains
pending; see `TEST43-DEVICE-CHECKLIST.md`.
