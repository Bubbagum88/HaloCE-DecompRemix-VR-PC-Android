# Test68 checklist: OpenCE Build 206

Private successor to Test67, 1.0.35-test68 / code80. Source: Test67's delivered
tree (APKs from d8cf46c7) plus OpenCE build-206 (8102e711, 2026-10-14). No
publish, push, install or game launch; local commits only. Saved settings
preserved.

Owner request (2026-10-14): "looks like opence updated again. update everything
to match the details of it and build new apks."

## Work

- [x] OpenCE build 206's three commits since what Test67 took (testing
  52e33a39): 6d64abdb map sharing restart overflow and map validation, 37ded328
  harness tests for clang 23, 3e0ba551 Custom Edition maps keep their names
  (network 29). Three-way merged; nine conflicts resolved by hand for this port.
- [x] Network 29: hosts 29, joins 11..29 (All compatible by default); launcher
  lists 29; every player-facing text says 29 / Build 206. Players on 28 cannot
  join this build's hosts (as with any OpenCE version change); this build still
  joins theirs.
- [x] Client of a host before 29: the map found by name and the header checksum
  checked, as before (custom_edition_map_version_is_checksum); of 29, upstream's
  hash version lookup. New behavioural test test_test68_network29.
- [x] Kept: OpenSauce .yelo maps beside .map (also in the new lookup by file,
  where upstream's .map-only extension cut is replaced), the active game set
  maps folder in messages, MCC map versions, MCC grenade HUD line (now bounded).
- [x] stb_vorbis floor index masked (byte-identical to Build 206's); GulchCE's
  MCC decoder compiles this copy, so MCC sounds get the fix too.
- [x] Stricter map validation (lightmap vertices, camera/player data) taken.
- [x] Community extras: Build 206 still drops kinds past 86; unchanged.
- [x] Test pins moved to 29 (18 files, each replaced exactly); tests whose
  behaviour Build 206 changes updated to its new behaviour (maps not renamed,
  "Name (2)"), plus the new map_share_restart harness test registered.
- [ ] Full suite, both builds, package identity/signature/hash checks.
- [ ] Delivery record, memory, local commits.

Automated results are not headset or phone verification.
