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
markers, traversal rejection and symlink-target preservation. Launcher tests:
55 state/policy checks passed and the full Android+SDL Java sources compile
against the Android API. The complete serial regression runner passed all 92
suites with no failures; the strengthened managed-data fixture was rerun
afterward and passed all 97 checks. Both edition builds each reran all 92 suites
with no failures. Both APKs passed compaction checks preserving every payload
entry hash and signing certificate, plus APK alignment. The final APK metadata,
cross-edition parity and archive checks are performed by the package gate.

| Edition | File | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Quest / VR | `HaloCE-Quest-VR-1.0.24-test43.apk` | 35,536,126 | `267512d460457685310e71950c46d093770260e491fb6cad0c9b2318ef39e57e` |
| Android / flat | `HaloCE-Android-1.0.24-test43.apk` | 33,373,359 | `036b29962f6af7f75e729fd22d1aca69444e39cf4c1d8b5478f64208f6c863ae` |

Final package directory: `<artifacts>\test43-20261009-v1.0.24-test43-game-data-manager`.
Matching archives: `HaloCE-Quest-test43-build.zip` and
`HaloCE-Quest-test43-source.zip`. The package gate generates `manifest.json`,
`compatibility.json` and `SHA256SUMS.txt` in the same directory.

Source checks do not confirm device storage-provider behavior, visible selector
UX, app update preservation or live gameplay. Device acceptance remains
pending; see `TEST43-DEVICE-CHECKLIST.md`.
