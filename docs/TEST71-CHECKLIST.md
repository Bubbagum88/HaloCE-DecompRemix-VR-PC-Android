# Test71 checklist: every campaign mod in one tap

Private successor to Test70 (published as v1.0.37), **1.0.38-test71 /
code83**, branch `test39-interaction-completion`. Local commits only; no
push, publish, install or game launch. Saved settings preserved. Network 29
unchanged. Game source: manual reload only (below).

Owner's request (2026-10-15): "i want all of the mods to work like that for
future reference": every campaign mod installs from the launcher in one
tap, as SPV1 does, from its public host and verified; import only as a
fallback.

Legend: [x] done and tested off-device; [~] done, but only a headset can
confirm; [ ] not done.

## Mods

- [x] SPV1: unchanged (halomaps.org file ids 1912-1921, sizes, SHA-256 at
  install). Import from a folder, .zip or .rar now offered as its fallback too.
- [x] Project Lumoria: halomaps.org file ids 6503-6506 (Lumoria A-D). Each
  download was fetched off-device during this work and its map's SHA-256
  equals the recipe's (`assets/campaigns/lumoria.properties`). `ModMap`
  gained `extra` (a level of the mod's own, put aside nowhere), which file id
  0 used to mean, so a level of its own can also be downloaded. The mod is no
  longer import-only; its install path is SPV1's.
- [~] The Altheros Experience: moddb.com answers non-browser clients 403,
  so the launcher opens the download in its own WebView
  (`ModDownloadActivity`) and, when moddb hands the browser the file, takes
  the download over with the WebView's cookies and user agent (resume by
  Range). Kept only when exactly 1,477,832,127 bytes with moddb's MD5
  `7c76889eeed3e66654f4e91e8d5101e7` (equal to the owner's copy). Whether
  moddb accepts the hand-off can only be seen on a headset; import of the .rar
  or folder stays.
- [x] RAR5 on the device: `ArchiveExtractor` with libarchive-android 1.1.7
  (libarchive 3.8.8). The owner's moddb archive, extracted off-device by
  bsdtar built from libarchive 3.8.8: all 13 files equal the recipe's
  SHA-256. (Windows' own bsdtar, libarchive 3.5.2, fails on a30.yelo with
  "Truncated data in huffman tables": an old RAR5 decoder bug, not in 3.8.)
  Each unpacked file is size- and SHA-256-checked before it replaces
  anything; readmes and pictures are skipped.
- [x] Import of a .rar or .7z (the file picker): read in place by its file
  descriptor (no 1.4 GB copy); a .zip still takes Test70's path.
- [x] Delete also removes the archive and its .part.
- [x] Launcher texts: setup help names each mod's host; SPV1's resource
  steps name the selected mod; an installed Lumoria says its levels are in
  New Game (not "the campaign plays as").
- [x] What's New: a Test71 section on top; Test70's notes kept below it.
- [x] Credits: libarchive-android, libarchive and the libraries built into
  its native library (zlib, bzip2, liblzma, LZ4, Zstandard, Mbed TLS) in
  CREDITS.md and THIRD-PARTY-NOTICES.txt (complete notices), and the APK
  field guide.

## Manual reload with the mods' weapons

The owner (2026-10-15, before the builds): "adapt manual reload to any custom
weapons/new weapon meshes given by the mods. ignoring altheros for now until
i can confirm it even runs. still mark it as not working".

- [x] Cause: manual reload knew six first-person models by tag name. SPV1's
  maps are protected: every tag is named `<protected>` at run time (the
  loader gives back only the scenario's group), so none of SPV1's guns, its
  stock-rig rifles included, got a profile ("profile unavailable"), and its
  needler (gun class by name: OTHER) never shook to reload.
- [x] Every weapon of SPV1's ten levels and Lumoria's four was read from the
  caches (first-person model nodes, magazines). Lumoria keeps the stock
  rigs (already supported; its plasma cannon has no magazine). SPV1 has
  eleven rigs: AR (stock), SMG, a new pistol, a bipod sniper, a rifle with an
  underbarrel shotgun (two magazines), a shell-by-shell shotgun (arms rig:
  shell, cock), a flamethrower (ammo, cover, barrel), launchers (stock rig),
  needler (stock), plasma pistol (stock), plasma rifle (arms rig).
- [x] `vr_reload_generic_profile.h` (pure): after the stock table, the
  model's own nodes and the first magazine choose the kind: tubes+push_bar,
  ammo+cover, a loose round (bullet/shell) when a reload puts one round in,
  else a magazine with its handle/slide/bolt. On the six stock rigs it gives
  exactly the stock table; on every SPV1 and Lumoria rig the expected kind;
  energy weapons none (`tools/test_test71_reload.py`, 18 rigs).
- [x] A second magazine (SPV1's rifle with its shotgun): the first is loaded
  by hand; weapons.c now holds back only the triggers of magazine 0 (and
  those with none) while a reload is in hand. For every one-magazine weapon,
  all the stock ones, the conditions are the same as before.
- [x] A needler rig (needle nodes) is shaken to reload whatever its name.
- [~] Only a headset shows the hands on SPV1's new meshes; each gun logs
  "VR manual reload: generic profile" once with what it chose.
- [=] The Altheros Experience: left alone, still "Experimental — currently
  not working" (the owner).
- [=] Aim offsets, magazine grip fit and left-hand lettering still go by
  name: SPV1's guns keep the defaults there, as before.

## Not changed

- Network 29, controls, movement and every other weapon behaviour: as
  Test70.
