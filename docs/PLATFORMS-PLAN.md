# Platforms plan: Quest, Pico, Steam Frame, Android flat, Windows flat, Windows PCVR

Status: plan and first findings, 2026-10-15. Owner's request: turn the newest
local project into a shared platform architecture without regressing Quest or
Android. Verification levels used throughout:

- **implemented**: code exists and compiles, with automated checks
- **runtime-validated**: ran against a real runtime (an OpenXR runtime, a
  Windows desktop), no headset
- **hardware-tested**: someone used it on the device

Nothing below is hardware-tested yet unless it says so.

## 1. Baseline (authoritative)

| Item | State |
|---|---|
| Branch | `test39-interaction-completion` (local; `origin/main` is behind it) |
| Newest commits | `a4b6811c` Test71 (one-tap mods, reload for mods' guns), `b192a87f` its launcher-check fix |
| Newest candidate | Test71, **1.0.38-test71 / code83**, building now from `b192a87f` |
| Newest packaged APKs | Test70, 1.0.37-test70 / code82 (`D:\HaloQuest\builds\test70-20261015-v1.0.37-test70`), also published as v1.0.37 |
| Handoff docs | `docs/CURRENT-STATE.md`, `CLAUDE.md`, `docs/TEST71-*.md`, `docs/TEST70-*.md` |
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
