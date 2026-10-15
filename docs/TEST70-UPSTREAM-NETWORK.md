# Test70 upstream and network status (OpenCE, HALOFREAK95, GulchCE)

Checked 2026-10-15 (owner items 56-65). Kept so later candidates need not
rediscover it.

## OpenCE reference

- Repository: github.com/OpenCommunityEdition/OpenCE.
- `main` = `8102e711` = tag **build-206** (2026-10-14, merge of PR #353).
  `testing` (`3e0ba551`) is contained in build-206: nothing newer upstream.
- This port: Build 206 merged in Test68 (merge `9a4d69c0`, APKs from
  `c331ef2b`); Test69 and Test70 add no upstream code.

## Network compatibility

- OpenCE builds speak one network version each (`HALO_PORT_NETWORK_VERSION`,
  29 in build-206); an OpenCE client joins only a host of exactly its own
  version and tells the player which version the host has. There are no
  alternate network modes, optional backends or compatibility layers
  upstream: the only other protocol family seen is GulchCE's network 42
  (MCC custom maps online), a separate fork.
- This port hosts network **29** and joins hosts of **11 through 29**
  (campaign co-op 15-29, Custom Edition maps 23-29; legacy campaign 12-14 opt
  in). It is wider than upstream, not narrower: its compatibility layers for
  older versions are its own (Test38-Test68).
- Live directory (halo.milenko.org/v1/games.txt, 2026-10-15): 20 servers,
  network 29 x13, 28 x3, 26 x2, 25 x2. All are within the join range; the
  Custom Edition map servers (v25, v29) meet its CE minimum 23. No server is
  excluded by protocol today.
- Discovery is not compatibility: the browser lists by the advertised version;
  join negotiation (`network_client_manager.c`) checks the version range,
  then the map (Custom Edition by name and hash on 29, by name and header
  checksum below 29: Test68), then gameplay replication by version (Test38+).
  Player state, co-op and disconnects are those versions' own paths.
- **Not done, deliberately:** no network version change; no claim of
  GulchCE network 42 (online MCC needs its messages 87-90 and a 32-byte
  network_game hash; the owner deferred online MCC in Test67, and this
  port's community extras already use kinds 87-92). Supporting 42 alongside
  29 is a protocol project of its own, not a constant to bump.

## HALOFREAK95 (github.com/jcompto95-tech/OpenCE)

30 branches. Test67 reviewed and took/adapted every branch then present
(TEST67-EVIDENCE.md). Since then:

| Branch | Head | Status |
|---|---|---|
| fast-decals | `1b9b09d4` (2026-10-14 17:06 UTC) | **new; reviewed, not taken in Test70** |
| all others | unchanged since Test67's review | kept as integrated |

fast-decals draws each decal as a quad list of its own straight from its
vertex stream (display.decals_on_gpu) and keeps one shared quad index
buffer. It is a CPU win on desktop GL. Not taken here because (1) it turns
one batched draw into one draw call per decal, which on the Quest's mobile
GPU, twice per frame (two eyes), may cost more than it saves, and (2) this
port's GLES path rebases indices on the CPU (`geometry compatibility: safe
streaming (fenced ring); CPU index rebasing`), which the shared quad index
buffer assumes is never needed. Its decal half applies cleanly; the
renderer half does not (this port's d3d8_gl.c differs). Take it only with an
on-headset frame-time comparison (decal-heavy level, both settings).

YouTube (HALOFREAK95): no newer posting could be found by search; GitHub is
the authoritative record of the fork's features.

Existing fork-derived features (Test67): third person (flat only, off in
VR), Extra Effects screen, item draw scale, overshield effect, corpse/decal
limits, projectile effects v2 with dynamic/vehicle blood, stencil shadows,
item physics on Jolt, Armor menu, text chat, vote-ban; community extras on
kinds 87-92 behind network.community_extras. Test70 changes none of them;
their pins (test_test67_fork) still pass.

## GulchCE

`gulch/main` `ebb197ba` (unchanged since Test67). Test70 restores three of
its hooks this port's merge had dropped (cache_files_windows.c: MCC map
availability, precache and reads), the cause of the "problem with the disc"
error on every MCC level. MCC stays solo-only and labelled experimental
until a headset confirms it.

## Platform parity

Android (flat) and Quest (VR) build from the same guest sources and the same
Build 206 core; VR-only systems (manual reload, physical grenades, IK,
parkour, immersive vehicles, scopes, fist combat, hand interactions, SLIDE,
BULLET TIME) are behind HALO_VR or vr.* settings and never replace the flat
equivalents on Android.
