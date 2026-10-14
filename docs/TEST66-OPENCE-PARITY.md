# Test66 OpenCE parity

Upstream: OpenCE, mirror `D:\HaloQuest\OpenCE-audit-20261009.git`. The latest
release, verified on GitHub on 2026-10-13, is **build-201** (`b1ef7f7e`,
2026-10-12); the testing branch had one newer commit (`52e33a39`, map
sharing hardening), also reviewed. This port's base was **Build 157**
(`73dc01d`). 259 upstream commits lie between them.

## Method

1. 65 commits that applied cleanly were applied (voice include `84cf2f8f`
   skipped).
2. Every file upstream changed was merged three ways: base Build 157's file,
   ours, Build 201's (`_scratch/merge66b.py`): 94 clean, 49 new files, 88
   conflicted files resolved by hand, file by file. A first attempt that
   used "the upstream version closest to ours" as the base was reverted: it
   silently dropped upstream code this port never had.
3. Files that differ in ways that predate Build 157 (this port's own lineage)
   were reviewed separately.

No network protocol change: this build hosts **network 28** (Build 201's) and
joins 11 to 28; map sharing and votes to kick travel in network 28 already.

## Taken (both builds unless noted)

- Map sharing (`map_share*.c`): Server Setup > MAP SHARING, `network.map_share`,
  `map_share_upload`, `map_seed`, `map_seed_upload`, `map_download`. Maps are
  kept in and downloaded to the **active managed game set's maps folder**
  (`CUSTOM_EDITION_MAP_DIRECTORY` is `cache_files_map_directory()`), this
  port's sole source of maps. Over the internet a map comes from the host
  (this port's signalling reaches the host alone, `p2p_reach_player` returns
  0); LAN players can seed.
- Votes to kick (`network_votekick.c`), scoreboard and console; `network.votekick*`.
- Server Setup regrouped into CO-OP OPTIONS, VOICE AND VOTING and MAP SHARING
  sub-screens; this port's PHYSICAL INTERACTIONS and HOST VR ACTIONS rows
  moved into CO-OP OPTIONS (help strings 19-22).
- Display options: field of view, viewmodel field of view and visibility,
  shield colour and glow, viewmodel shield; first-person legs (flat only; VR
  keeps its own projection, gun and full body).
- Campaign pause menu SETTINGS (flat only; VR keeps VR SETTINGS there).
- `game.enhanced_animations` (grenade throws, riders), and the throw turn gated on it.
- `powerup_render_bounds.c` (overshield/camouflage culling), `object_bounds_cache.c`
  (collision broad phase in crowded clusters).
- OpenCE's dynamic ragdolls (PR #317, Jolt Physics 5.6.0), with Jolt in the
  Android 64-bit host and a guest bridge (`ragdoll_physics_guest.c` ->
  `host_ragdoll.c`); `game.death_physics`; VR hands and Jolt share bodies.
- High-res HUD sprite sheets and button icons (`tools/embed_assets.py` merged,
  `point_threshold`), high-res text oversampling and letter fitting.
- `ustring_format_checked`, co-op script origin fixes, Custom Edition map
  hashing, resource-map checks, node-tree repair and HUD meter conversion,
  XISO plain names (Java and native), the 10 s clock start, profiling build
  files, menu platform lists (`platform="desktop web"`: the parser hunk of
  `menu_files.c`), the voice talking icon (bitmap, with this port's drawn
  speaker as fallback), guest defines `HALO_ARM64_GUEST` and `HALO_GLES`.
- Many clean merges across `source/` (players, items, weapons, HUD, game
  engine modes, game state, networking managers).

## Kept this port's own (not taken), with reasons

| Upstream change | Reason |
|---|---|
| Android app shell (HaloActivity, TouchControls/TouchLayout, Updater, manifest, a `:game` process with HaloApplication) | this port's launcher, VR, accepted touch layout and updater; a process split risks the Quest launcher and VR session |
| Host memory/ART reclaim rework, host_main, host_sdl audio/mic path, guest/host ABI v2 | this port's own tested port of the reclaim; voice and audio work as they are |
| OpenCE touch controls (touch_input, touch_game, touch look in player_control) | the app's own touch controls are the owner-accepted ones |
| Browser players (WebRTC, DTLS) in internet play; several-join signalling | needs a DTLS stack in the host; this port's dual-version signalling (reaching older hosts) is confirmed working |
| Renderer rework in d3d8_gl.c (vertex arrays, render-target cache, batched visibility), nv2a shaders, GL loader | VR rendering; the Android mirror fix (343eef15) was already present |
| Band-limited sinc resampler in the mixer | about 48 taps a sample is heavy for the Quest; this port's Catmull-Rom mixer works |
| Screenshots | upstream made them desktop only |
| Keyboard controls moved into input_abstraction | this port reads the keyboard in xinput_sdl.c |
| Desktop items in sdl_platform (fullscreen modes, window icon, frame pacing, Steam keyboard, scoreboard mouse) | not on Android/Quest; the scoreboard pointer is a stub as on upstream's Android |
| Custom Edition loader lineage: in-memory Ogg decoder (custom_edition_sounds.c, stb_vorbis), loose sounds, Chimera behaviours table, `custom_maps`/install folders | this port's loader (OpenSauce/.yelo, managed sets, disk Ogg transcoder) predates Build 157 and serves SPV1 and Altheros |
| `brokers.txt` | this port keeps `network.signalling_brokers` |
| Android texture cache back to the Xbox's | this port keeps twice the Xbox's (0xB00 pages) |
| Voice audio/encoder files | owner's rule; the packet-length fix is already present |
| Web, Windows, macOS, iOS ports | not this project's platforms |

## Upstream tests

Upstream harness tests `test_server_teardown` and `test_cinematic_titles`
fail even natively on Build 201 and are not in this project's suites;
`test_map_share_names` runs (`HALO_HARNESS_NATIVE=1`).
