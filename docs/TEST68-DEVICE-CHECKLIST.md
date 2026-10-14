# Test68 device checklist

Automated checks cannot substitute for these. Test67's device checklist still
applies in full (TEST67-DEVICE-CHECKLIST.md): nothing in Test68 changes VR,
combat, vehicles, MCC maps or the fork's features.

- Update each APK over Test67 without uninstalling; saves and settings kept.
- Server browser: All compatible networks lists network 29 hosts (OpenCE build
  206) and older ones; Network v29 can be chosen.
- Host a game: an OpenCE build 206 player (PC) and another Test68 player can
  join; a Test67 player cannot (expected: different network version).
- Join an OpenCE build 206 host on a stock map and on a Custom Edition map you
  both have; the lobby and browser show the map's own name (no hash).
- Join a network 28 host (Test67, or older OpenCE) with a Custom Edition map:
  joins as before when your copy matches; a different version of the map is
  refused with a message.
- Two versions of one Custom Edition map in the active set: the map list shows
  "Name" and "Name (2)"; a map an earlier build renamed with a hash shows its
  own name again.
- Custom Edition and SPV1/Altheros campaigns and an MCC map still load (stricter
  map validation must not refuse them); their sounds play.
- Community extras online with a build 206 player who lacks them: no disconnects
  or stray text; with another Test68 player: armor, chat, votes.

Report build, device/OS, map, settings, actions and the launch log.
