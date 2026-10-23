# Platforms plan: Quest, Pico, Steam Frame, Android flat, Windows flat, Windows PCVR

Status: plan and first findings, 2026-10-15. Owner's request: turn the newest
local project into a shared platform architecture without regressing Quest or
Android. Verification levels used throughout:

- **implemented**: code exists and compiles, with automated checks
- **runtime-validated**: ran against a real runtime (an OpenXR runtime, a
  Windows desktop), no headset
- **hardware-tested**: someone used it on the device

Nothing below is hardware-tested yet unless it says so.

**Where it stands (2026-10-16, Test72, 1.0.39-test72 / code84):** every
phase below is implemented in source. Built: Windows flat (`halo.exe`,
reaches the main menu here), Windows PC VR (`halo-vr.exe` links), Android
flat and VR native code (before the latest VR changes). Runtime-validated
here: the XISO import (24 maps, SHA-256 identical) and flat stereo 3D
(disparity measured on frames). The launcher, the remap UX, device-aware
labels and the latest VR changes compile in the single build pass the owner
asked for. PC VR runtime validation waits on the owner's OK for SteamVR's
null driver. Nothing is hardware-tested yet. Per item:
`docs/TEST72-CHECKLIST.md`; per platform: `docs/TEST72-DELIVERY-STATUS.md`.

**Since then (2026-10-22, Test73, 1.0.40-test73 / code85, delivered):** PC VR
is runtime-validated on SteamVR's null driver (eye dumps: the menus' world and
follow modes, grenades in the hand, the played character's arms). The Steam
Frame was checked against Lepton 3.0.8's own source and the other Halo CE
Frame ports (§5), and gained a no-computer installer and a Steam library
launcher (`tools/steam_frame`). OpenCE is merged to Build 256, its testing
branch and its fix-scenery-shields-network branch: network 34 (§10). Per item:
`docs/TEST73-CHECKLIST.md`; per platform: `docs/TEST73-DELIVERY-STATUS.md`.
The owner on the Quest: "basically everything works great", but for the
stencil shadows. A player has started it on a Steam Frame (from Steam, the
menus, quit from the menu: their log), where B did not go back in the menus.

**Then (2026-10-22, Test73b, 1.0.41-test73b / code86, in progress):** the
stencil shadows as HaloFreak95 made them, the VR body's shadow, B back in the
menus on every controller (the Frame's report), map sharing at its most by
default, and every launcher's log locations (the PC launcher's LOGS page);
then (10-23) SPRINT TOGGLE by default with BUTTON SPRINT's fixes and BULLET
TIME on every controller, the flat builds' sprint (a touch button on Android,
Left Shift on PC), a CONTROLS page in every launcher, held bodies drawn where
they are held, and WORLD SCALE. Per item: `docs/TEST73B-CHECKLIST.md`.

## 1. Baseline (authoritative)

| Item | State |
|---|---|
| Branch | `test39-interaction-completion` (local; `origin/main` is behind it) |
| Newest commits | `fcaa04e3` Test73 and `cde43a78` its delivery record (local); Test73b's work is uncommitted on top of them (a local commit at its build pass, as Test73's) |
| Newest candidate | Test73b, **1.0.41-test73b / code86** (Test73, 1.0.40 / code85, Test72, 1.0.39 / code84, and Test71, 1.0.38 / code83, travel with it) |
| Newest packaged APKs | Test70, 1.0.37-test70 / code82 (`D:\HaloQuest\builds\test70-20261015-v1.0.37-test70`), also published as v1.0.37; Test72's and Test73's private packages (`docs/TEST72-DELIVERY-STATUS.md`, `docs/TEST73-DELIVERY-STATUS.md`) |
| Handoff docs | `docs/CURRENT-STATE.md`, `CLAUDE.md`, `docs/HANDOFF-2026-10-*.md`, `docs/TEST73-*.md`, `docs/TEST72-*.md` |
| Public release | v1.0.37 (= Test70). History only; never the base |

Every new target starts from this tree. No source is taken from a release.

## 2. What already exists (reuse, do not rewrite)

- **Game core, 32-bit by necessity.** Tag data, cache files and saves hold
  32-bit pointers. Android runs the core as an arm64_32 *guest* inside a
  64-bit *host*. The upstream desktop ports build it natively for 32-bit x86:
  `ninja windows` gives `build/windows/halo.exe` (clang for
  i686-pc-windows-msvc, SDL3, OpenGL 4.5); `ninja linux` gives the Linux one.
- **Shared platform layer** (`port/linux/src`), used by Windows and Linux:
  D3D8-to-OpenGL renderer, SDL input (keyboard, mouse, XInput/SDL gamepads),
  `config.toml` settings with a schema that already scopes each key to
  platforms (`_platform_linux|android|windows|vr`), updater, networking,
  voice, **`xiso.c` (extracts the maps folder from an XISO, with
  progress)**, and **`vr_frame.c`** (the VR frame logic).
- **VR is already OpenXR**, through the Khronos loader. The whole platform
  contract the shared VR gameplay needs is **nine host functions**
  (`host_xr_init`, `begin_frame`, `acquire`, `release`, `end_frame`,
  `recenter`, `set_refresh_rate`, `haptic`, `resize_eyes`), plus one frame
  structure (`halo_xr_frame`): head, eyes, FOV, grip and aim poses, triggers,
  sticks, squeeze, Xbox-style logical buttons, and **each hand's buttons by
  position** (south, east, west, north, bumper, stick, menu, view, thumb and
  index touch). Gameplay code never names a controller model.
- **Controller profiles today**: Steam Frame (Valve's
  `frame_controller_valve`), Meta Touch, Valve Index. All 98 binding paths
  are verified against the Khronos registry and Valve's documentation
  (`tools/test_openxr_bindings.py`, new).
- **Steam Frame is already reached by the VR APK**: Valve's documented route
  for custom engines is "Android 10 or Linux ARM64" with OpenXR; its Android
  layer ("Lepton") runs ARM64 APKs, and our Frame binding table matches
  Valve's published paths. (Hardware-tested: no.)
- **Content model on Android**: launcher, XISO, revision sets, verification,
  mod recipes (`assets/campaigns/*.properties`, data only: shareable).

## 3. Target matrix: how each is built

| Target | Build | New work |
|---|---|---|
| Quest VR | VR APK (unchanged) | none; must stay byte-for-byte behaviour |
| Pico native | **the same VR APK** (one APK, as PPSSPP ships) | Pico profiles and manifest entries (section 4) |
| Steam Frame | **the same VR APK**, via Valve's Android layer | device checks; Linux ARM64 build only if Lepton falls short |
| Android flat | flat APK (unchanged) | movement extras (section 8) |
| Windows flat | upstream `halo.exe` path, with the fork's shared code | build health, launcher, settings parity, stereo 3D |
| Windows PCVR | `halo.exe` built with `HALO_VR` | a Windows OpenXR host implementing the nine functions |
| Linux flat | comes with the shared layer | free side effect, not a priority |

One APK for Quest, Pico and Frame keeps one VR gameplay build. Separate
flavors stay possible if a store requires them.

## 4. Pico: review of pull request #4 (lucahttp, 2026-10-10)

Written against `493b46c5` (1.0.16 era), far behind us. Not merged; adapted:

| Part of the PR | Verdict |
|---|---|
| Pico binding table (sticks, triggers, squeeze, A/B/X/Y, left menu, touches) | **Adopt.** Every path is valid under the registered Pico profiles. |
| Profile name `/interaction_profiles/bytedance/pico4s_controller` | **Fix.** Not a registered profile. Registered: `bytedance/pico4_controller`, `pico_neo3_controller` (`XR_BD_controller_interaction`), and `bytedance/pico_ultra_controller_bd` (`XR_BD_ultra_controller_interaction`) for the Pico 4 Ultra. Suggest each when its extension is offered. |
| Enabling `XR_BD_controller_interaction` when offered | **Adopt**, plus the Ultra extension. |
| Manifest: `pvr.app.type=vr`, `com.picovr.intent.category.VR` | **Adopt** (Pico's docs; SDL's XR notes). |
| Manifest: `pvr.app.inputType`, `pvr.app.handtrackingSupport=0` | Adopt, marked unverified (the PR's own finding; harmless elsewhere). |
| Manifest: `oculus.software.eye_tracking`, `enable_shared_context`, `pvr.supportedDevices` | Skip: no evidence, and eye tracking can prompt on Quest. |
| `host_memory.c`: "try munmap, trust the kernel" when pagemap is hidden | **Reject.** Superseded: ours already falls back to `mincore` and `smaps` (tested). And `munmap` unmaps live pages without error, so the PR's premise would corrupt ART. |

What Pico teaches the general layer: nothing gameplay-side needed changing,
because the abstraction is already logical. The one real lesson is
**binding hygiene**: one bad path silently drops a whole controller, so every
table is now checked against the registry.

## 5. One controller layer for every headset

Shared VR gameplay → OpenXR actions (logical) → per-profile binding tables.

- **Already logical**: buttons by position, triggers, grips, sticks, touch.
- **Add now**: Pico profiles (above).
- **PCVR headsets through SteamVR**: Index and Touch are suggested; SteamVR
  remaps others to them (Valve: Frame binding, then *generic controller*,
  then Touch). **PSVR2 Sense on PC** has no OpenXR profile of its own:
  SteamVR presents it through these remaps (its four face buttons and
  menu map to Touch's). Implemented by design; hardware-tested no.
- **Held back on purpose**: `khr/generic_controller` has no menu button, and
  SteamVR prefers it to Touch, so suggesting it could *remove* pause from
  controllers that work today. It gets a table only with a menu fallback
  (for example a held stick click). Vive wands and WMR (trackpads, no face
  buttons) likewise wait for a designed mapping rather than a guessed one;
  SteamVR's own remap covers them meanwhile.
- **Controller audit (verified 2026-10-15; hardware-tested: none)**:

  | Controller | Runtime | How it gets bindings | Status |
  |---|---|---|---|
  | Quest Touch / Touch Plus / Pro | Quest native, Meta PC (Link), Virtual Desktop | `oculus/touch_controller` (ours) | implemented; Quest hardware-tested over many candidates |
  | Valve Index | SteamVR | `valve/index_controller` (ours) | implemented |
  | Steam Frame | Frame (Lepton), SteamVR | `valve/frame_controller_valve` (ours, Valve's documented paths, its touches too; Test73: checked again against Valve's Input page and Lepton 3.0.8, and against HaloCE-VR and Mjolnir VR, `docs/VR_ARCHITECTURE.md`) | implemented; no Frame here |
  | PICO 4 / Neo 3 / 4 Ultra | PICO native | `bytedance/pico4_controller`, `pico_neo3_controller`, `pico_ultra_controller_bd` (ours) | implemented |
  | Vive wands, Vive Cosmos, WMR, PSVR2 Sense, others | SteamVR 1.26+ | SteamVR converts the highest-priority layout the app binds (Valve's OpenVR driver documentation, remapping files), and its binding UI can change it | by design; unverified on hardware |
  | WMR / HP Reverb G2 | Windows Mixed Reality's own runtime (removed from Windows 11 24H2) | no remap there: tables for `microsoft/motion_controller` and `hp/mixed_reality_controller` belong in the shared PCVR layer | to do with the PCVR host |
  | any | any | `khr/generic_controller` deliberately **not** suggested: it has no menu button and SteamVR prefers it to Touch (Valve's Frame docs), which could remove pause | decided |

  Every table is checked path by path against the Khronos registry (and
  Valve's Frame documentation) by `tools/test_openxr_bindings.py`.
- **Device-aware labels**: the host learns the active profile
  (`xrGetCurrentInteractionProfile`); passing its family to the game lets
  menus say "A" or "Cross" instead of a Quest name. Needs one ABI field
  (`halo_xr_frame` is size-asserted: both sides change together).
- **Haptics**: already one call (amplitude, duration) through OpenXR's
  standard vibration output, which every profile has. Richer haptics later,
  only as an optional extension path.
- **Left-handed mode and remapping** act on logical actions already; they
  carry over unchanged.

## 6. Windows PCVR

- **Same game binary family as Windows flat**, compiled with `HALO_VR` and
  the shared VR code (it is in `port/linux/src` and `port/linux/game`).
- **New: a Windows OpenXR host** implementing the nine functions with
  `XR_KHR_opengl_enable` (the desktop renderer is OpenGL). Split today's
  `host_xr.c` into the portable part (actions, binding tables, input sync,
  recentring, frame loop) and a graphics/platform part (EGL/GLES on
  Android, WGL/OpenGL on Windows), so both hosts share one action layer.
- **32-bit runtimes**: the game is 32-bit. SteamVR registers a 32-bit OpenXR
  runtime from 2.17 (stable since 2026-09-10); Meta's PC runtime has a 32-bit
  manifest. Runtimes without a 32-bit or OpenGL path (Virtual Desktop's
  VDXR is D3D/Vulkan) need either GL-to-D3D11 interop
  (`WGL_NV_DX_interop2`) or a small 64-bit helper process. Start with GL on
  SteamVR and Meta; add interop second.
- **Full feature set**: the VR gameplay code is shared, so PCVR gets
  manual reload, IK, fist combat, parkour and everything else by
  construction. PC graphics options (render scale, MSAA, anisotropy, draw
  distance, frame rate) are desktop settings, not Quest limits.

## 7. Windows flat, launcher and content

- **Build health first**: the fork has only built Android since Test42 or
  so; `ninja windows` and `ninja linux` must compile the fork's shared code
  again. Needs Visual Studio Build Tools (x86 MSVC libraries, Windows SDK),
  LLVM and ninja on this PC (an install only the owner can approve).
- **Launcher**: one desktop launcher for Windows flat and PCVR (and Linux),
  native (SDL3, no new UI toolkit): Play, Game data (pick XISO, validate,
  detect revision, extract with `xiso.c`), Verify/Repair, Mods (the same
  recipe files Android uses), What's New, Graphics, Controls, VR or stereo
  options by target.
- **One extracted library** per machine (for example
  `%LOCALAPPDATA%\HaloCE\library`), shared by the flat and PCVR executables;
  each keeps its own `config.toml`. No second extraction.
- **Content pipeline sharing**: keep Android's working Java pipeline as it
  is; the desktop uses the C one; both read the same recipes and hashes so
  their results are identical. Merging the two into one C library is
  possible later, not a precondition.
- **Input**: keyboard/mouse and gamepads exist; the remap UX
  (ask on conflict, NONE, per-action reset, Reset All) is ported from the VR
  menu's rules to the desktop bindings.

## 8. Flat movement extras (Android flat and desktop flat)

The owner: parkour, slide and sprint with toggle options on flat too;
hand-only things (wall grab, hand climbing, pull-to-launch) stay VR.

| Feature | Flat? | Why |
|---|---|---|
| Wall running | **yes** | uses the body's throttle, jump and velocity, and wall probes; no hands |
| Wall jumps | **yes** | same; the look direction comes from the camera instead of the head |
| Slide | **yes** | a biped movement hook; needs only sprint and crouch |
| Sprint (hold or toggle) | **yes** | the speed math is shared; flat needs its own input: Shift, a pad button, a touch button |
| Bullet time | candidate | solo time scale, a button; offered if it survives review |
| Hand climbing, wall grab, pull-to-launch, physical melee, manual reload | no | need tracked hands |

Rules: separate `flat.*` settings, **off by default** (flat play does not
change unless the player turns them on); offline and co-op host only, as in
VR (no network change); VR behaviour stays identical (the VR path and its
settings are untouched; shared math moves into shared helpers only where
the tests prove it identical).

## 9. Stereo 3D for Windows flat

Reuse the VR renderer's two-eye path with a virtual head: left and right
cameras offset by eye separation, asymmetric (off-axis) projections meeting
at the convergence distance, then composed as Full/Half SBS, TAB, or
anaglyph (red-cyan, Dubois). Settings: enabled, mode, separation,
convergence, eye swap, HUD depth, reticle depth, reset. Off means the normal
single-camera path, untouched.

## 10. Networking

No protocol change for any of this. Platform differences are local: VR and
movement extras already act only offline or on a co-op host's own player,
so every platform stays compatible with network 29.

Test73: the network follows OpenCE to **34** (Build 256's 32, its testing
branch's 33 for co-op's ALLY FRIENDLY FIRE, its fix-scenery-shields-network
branch's 34 for the map's shields and tripmines). This port hosts 34 and joins
any host from 11 to 34, each by that host's rules; OpenCE's own players join
a host of their own version only. Co-op's VR INTERACTIONS (on by default) is
this port's extension inside the game's messages (`network_interaction.c`,
its own version 1, its kinds unknown to older peers, which drop them): every
VR player's fists, grenades, reload, parkour and slides, each dealt or allowed
by the host; a player without it plays with the buttons.

## 11. Phases

1. **Now (safe, no platform risk)**: Test71 packaged. Registry-checked
   bindings (done). Pico profiles and manifest entries. Flat movement
   extras with settings, off by default. Plan in the repo.
2. **Desktop build health**: toolchain installed; `ninja windows` and
   `ninja linux` compile the fork; tests for the shared layer.
3. **Windows flat**: launcher, shared library, settings parity, remap UX.
4. **Windows PCVR**: `host_xr` split; Windows OpenXR host (GL); SteamVR and
   Meta runtimes; then GL/D3D interop for others.
5. **Device-aware labels**, profile family in the frame ABI.
6. **Stereo 3D** for flat PC.
7. **Validation on hardware** by the owner and testers: Pico, Steam Frame,
   PCVR headsets.

## 12. Needs from the owner

- Approve installing Visual Studio Build Tools (C++ workload, x86 libs,
  Windows SDK) and LLVM on this PC, for phases 2 to 4.
- Testers with Pico, Steam Frame and PCVR headsets (Quest Link, Index,
  PSVR2 adapter), since none of these can be hardware-tested here.
