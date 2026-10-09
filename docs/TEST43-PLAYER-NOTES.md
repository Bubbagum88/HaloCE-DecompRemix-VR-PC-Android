# Test43 private candidate: 1.0.24-test43

Private Quest VR and Android test build. Public v1.0.18 remains the accepted
release; this candidate has not been published or device-tested. It carries
forward all project changes made after v1.0.18 through Test42, including the OpenCE
Build157/network24 base with selected Build167 compatibility fixes. See the
Test42 requirement and integration records for the carried-forward feature
scope and limits.

## Game-data selection and storage

- The main launcher now shows the selected game-data label and number of
  installed distinct sets. Tap it to open **Game files & versions** and choose
  the set used on the next launch.
- The full manager marks the active set, shows detected cache build and map
  fingerprint, and allows each imported set to be selected or renamed.
- **Delete imported copy** removes an inactive managed set, including its maps,
  configuration and local saves. The current active set must be switched away
  from first. Existing/base data cannot be deleted using this control.
- ISO/XISO files placed inside the import inbox can be deleted there after
  import. An ISO/XISO selected directly through Android's file picker is not
  retained; the source ISO/XISO stays where you selected it. Source folders
  also remain untouched.
- Byte-identical map sets deduplicate to one profile. The verified USA Original,
  Rev 1 and Rev 2 XISOs contain identical bytes for their 24 maps, so importing
  them does not create three distinct selectable map sets. Other images remain
  separately selectable when their imported maps differ. Filenames do not
  verify a disc revision.

Selection uses the existing atomic active-data marker consumed by native and
Java startup. Switching remains between launches; network compatibility,
revision requirements and saves remain governed by the active set and game
content. See `GAME-DATA-LIBRARY.md` and `USA-IMAGE-COMPARISON.md` for evidence.

## Preserve prior behavior

Keep the in-game OpenCE menus, multiplayer/co-op, Safe Geometry defaults,
touch/gamepad controls, VR settings, saves/config isolation, and all documented
Test38-42 features unchanged. PC/Steam Frame remains deferred. The offline
player, controls and touch guides are generated from the current project docs.
