# Halo CE VR on Steam Frame: architecture and status

Historical Steam Frame notes below, preserved from the upstream VR work.
They are not Quest test9 acceptance results. For the active Quest candidate,
read [TEST9-PROGRESS.md](TEST9-PROGRESS.md) and `QUEST_VR_HANDOFF.md`.

This fork adds a VR build of the Android port for the Steam Frame. The headset runs Android
apps inside Lepton, a container, and the build uses OpenXR to talk to SteamVR. Desktop and phone
builds are unchanged: everything here is behind `configure.py --vr` (`HALO_VR`).

## Status (2026-10-02)

| Area | State |
| --- | --- |
| Build, deploy, OpenXR session | Done; played in the headset. |
| Menus and loading on a flat screen | Done; played. |
| Stereo gameplay with a HUD layer | Done; played. The HUD's alpha is made from its brightness. |
| Performance | **72 Hz held at 1.5× resolution (2592² an eye)**, played. Fixed: lens-flare occlusion reads that stalled the CPU on the GPU (now asynchronous), Mesa's trace markers, per-draw buffer maps (now persistently mapped). The game thread is busy 53% of a 72 Hz frame. |
| 90 Hz | Set in the Frame's display settings. The game thread needs about 7.3 ms of CPU a frame, against 90 Hz's 11.1 ms. **Not yet seen worn at 90.** |
| Hand-aimed weapons | Default (`vr.aim = "hand"`); verified unattended with synthetic hands. **Not yet played.** |
| Arm IK | Default (`vr.arms = "ik"`); verified unattended. **Not yet played.** |
| 3D cutscenes on a screen, fades | Default (`vr.cinema_3d`); verified unattended. **Not yet seen worn.** |
| Vehicles: first-person seats, stick steering | Built, **not yet run on the device** (the headset went offline mid-test). `vr.vehicle_view` "first_person" (default) or "chase"; `vr.vehicle_steering` "stick" (default), "head" or "hand". |
| VR-native controls, gestures, left-handed play | Built (`vr.controls = "vr"`, default; `"pad"` keeps the Xbox mapping). **Not yet run on the device.** |
| Aim smoothing when zoomed, haptics | Built, **not yet run on the device.** |
| Picture-in-picture scope | Built (`vr.scope`), **not yet run on the device.** |
| Far HUD drawn from the head | Built (15 m away, 10 m wide), **not yet seen worn.** |
| Menu laser pointer | Built, **not yet run on the device.** |
| Room-scale walking | Built (`vr.roomscale`, off by default), **not yet run on the device.** |
| VR settings in the pause menu | Built, **not yet run on the device.** |
| Comfort options, foveation | Not started. |

## Device facts (Steam Frame, Lepton 2.8.14, 2026-10-02)

- **Android:** Android 11 (API 30), arm64-v8a, 4 KB pages. Upstream's limit on 16 KB pages
  does not apply here.
- **GL:** OpenGL ES 3.2 is Mesa **Zink** on Turnip (Adreno 750). `GL_EXT_sRGB_write_control`
  is available.
- **OpenXR:** the runtime is SteamVR 2.17.10, found through
  `/vendor/etc/openxr/1/active_runtime.json`; the Khronos runtime broker is absent.
  - Eyes are 1728×1728, and the default refresh is 72 Hz.
  - Swapchain formats: `SRGB8_ALPHA8`, `SRGB8`, depth.
  - `XR_VALVE_frame_controller_interaction` is present.
- **Missing services:** Lepton runs without a clipboard service.
  `port/android/patches/sdl3-no-clipboard-service.patch` handles that in SDL3.
- **Storage:** `/sdcard/Documents` is the headset's `~/Documents`, which survives Lepton
  resets. Game data, `config.toml` and saves go to `Documents/HaloCE`.
  *Superseded in Test73:* Android 11's scoped storage keeps an app out of
  `/sdcard/Documents`, so the app now uses the SteamOS user's folder at its host path,
  `/home/<user>/Documents/HaloCEQuestVR` (see "Test73" below).

## Test73: the Steam Frame plan (item 8, 2026-10-20)

This was written from Valve's Steamworks Steam Frame pages, Lepton's behaviour, and the field
findings of [ringfall-mjolnir-vr](https://github.com/Cesarus85/ringfall-mjolnir-vr) (now Mjolnir VR;
CC0, AGPL-3.0 or later since 2026-10-19), and on 2026-10-22 from Lepton's own source and the other
Frame ports (below). It has
**not been run on a Frame**: none of it has device acceptance. The same VR APK serves the Quest,
the PICO and the Frame. Everything below is chosen at run time and applies only inside Lepton.

- **Detection** (`Lepton.java`, `host_lepton_running` in `host_main.c`): one of the properties
  `lepton.app_id` or `waydroid.host.user` is set, `ro.steam.running_in_app_container` is "true", or
  the build's model is "Lepton" (Lepton 3; its maker is now "Valve") or its maker "Lepton" (before).
- **Data** (`Lepton.dataRoot`, `lepton_data_root`): `/home/<user>/Documents/HaloCEQuestVR`.
  It is used only when writable, and the user name must be a plain one. The launcher, the game,
  config.toml, saves and logs all go there (`RunLog` writes to its `logs/`). Lepton 2 emptied
  `/sdcard/Android/data` and reinstalled the APK at every start; Lepton 3 (below) keeps an install
  until the APK changes, but the folder in Documents is kept by both, and by a Lepton reset.
- **Steam launches are headless** (`lepton.headless`):
  - if the data is present, the launcher starts the game at once;
  - otherwise it unpacks the largest `.iso`/`.xiso` in the user's Downloads, Documents or
    Desktop (`XisoExtractor`) and then starts it;
  - otherwise it writes `STEAM-FRAME-README.txt` there and ends.
- **One process:** Lepton ends the container when the package's main process ends. So the VR
  game runs in the main process there (`HaloFrameActivity`) rather than in `:halo_game`.
- **No self-update** on the Frame: Lepton installs the APK it is given (updating is installing a
  newer bundle, below), and the package-replaced receiver starts nothing there.
- **Pickers:** a missing document picker (`ActivityNotFoundException`) is reported instead of
  crashing.
- **The fdm_injection layer:** SteamVR lists `XR_APILAYER_VALVE_fdm_injection` as an implicit
  layer, but an app cannot load the system's library from its own namespace, so the loader fails
  `xrCreateInstance`. The VR APK carries a pass-through layer under that library's name
  (`port/android/xr_layer/fdm_injection_stub.c`, ringfall's). The Quest and PICO never load it.
- **Controllers:** the Frame's own profile was already bound. Its touch sensors are now bound
  too, for the finger poses, and so are the Index's (`suggest_pair`). If the runtime refuses
  them, the profile is suggested again without them. A controller that never reports a touch
  (HP Reverb G2, or a refused pair) shows a hand resting on it. Before, holding grip for a second
  showed the middle finger there.
- **Frame timing on Mesa zink** (each `glGet*` waits for Mesa's GL thread):
  - uniform locations are asked once per program (`uniform_location`, `vr_frame.c`);
  - on SteamVR in Lepton, the swapchain images are released together as the frame ends, with a
    flush after the right eye (`HALO_XR_DEFERRED=1|0` overrides this on any runtime);
  - the frame thread is pinned to the fast cores (`HALO_XR_ANY_CORE` turns that off).
- **Quitting:** the main menu's QUIT GAME (pause > quit to the main menu > QUIT GAME) ends the
  process, and with it the container, and leaves `quit_requested.txt` beside the data (for the
  launcher below). Started from the Steam library by `launch.sh`, Steam's "Exit game" works too.
- **Deploying from a computer:** `tools/steam_frame/deploy.sh` copies the maps to
  `~/Documents/HaloCEQuestVR/maps` and makes the folder writable for the app.

### Installing without a computer (2026-10-22; ringfall's, AGPL-3.0, adapted)

`tools/steam_frame/bundle.py <VR APK> <folder>` makes `HaloCEQuestVR-SteamFrame.zip`: the VR APK as
`HaloCEQuestVR.apk`, `install.sh`, `launch.sh`, "Install HaloCE Quest VR.desktop" and a README. A
player unpacks it in the Frame's Downloads (Desktop Mode) with a disc image there, and opens the
desktop file:
- `install.sh` (zenity dialogs; `HALO_UNATTENDED=1` for testing) puts the APK and the launcher
  (`halo-ce-quest-vr.sh`) in `~/Documents/HaloCEQuestVR`, says whether it sees a disc image, and has
  Steam add the game to the library (`steam://addnonsteamgame`, from a desktop file beside the game,
  as SteamOS's "Add to Steam" does; Steam is not closed). Running it again with a newer bundle
  updates the game; settings, saves and data stay.
- `launch.sh`, the library entry, runs `lepton waitforexitandrun -- HaloCEQuestVR.apk` as Steam
  runs an Android title of its own: a container id of its own (4290007373; with the shortcut's id
  SteamVR's client stalled in `xrCreateInstance`, ringfall's finding), a compat data path with its
  `internal/`, a watcher that ends the container when Steam ends the script ("Exit game"), the
  container's logcat in `logcat.txt`, and a start that ends within 30 s tried again (up to three
  times) unless the game was quit (`quit_requested.txt`). No self-update: test candidates have no
  public release to fetch (ringfall's launcher fetches its releases).

### Lepton 3.0.8, from its source (gitlab.steamos.cloud/frame-public/lepton, 2026-10-22)

- **The activity started** is the first `<activity>` whose intent filter has both MAIN and
  LAUNCHER (`apk_extractor`; an `activity-alias` is not looked at), here `LauncherActivity`; the
  manifest must have exactly one `<uses-sdk>` (Gradle's merge writes it). `uses-feature` is never
  read, so `android.hardware.vr.headtracking` `required="true"` blocks nothing (HaloCE-VR, which
  runs on the Frame, declares it the same way; ringfall declares `"false"`).
- **Two images:** Android 11 (API 30) and Android 14 (API 34); the app works the same in both
  (its data folder is reached at its host path either way).
- **Storage:** `/sdcard` is the compat data path's `external/` and is kept; Documents, Download and
  Movies in it are links to the SteamOS user's folders, which are mounted at their host paths.
- **Installs are kept** ("baked") until the APK's hash or Lepton's version changes; a container
  that ends within 30 s of its start has its install dropped (the next start installs again).
- **The 2D window** is hidden unless the depot has a `lepton-show-flatscreen` file.

### From the other Frame ports (2026-10-22)

Taken, each tested in `tools/test_test73_frame_ports.py`:
- **The runtime waited for** (astromaddie's HaloCE-VR, e92d54fa): in Lepton, an instance SteamVR
  refuses (not running yet, or asleep with the headset) is asked for again each second for a
  minute; then, or on any later failure, the game ends with its reason in the log and no message
  box. A flat screen fallback there drew to a window Lepton never shows, and its display composer
  aborted, taking the container down. Elsewhere the flat screen stays.
- **The clock by display times** (HaloCE-VR 02887521): the runtime's frame is begun at the top of
  the main loop and the game clock steps from one frame's display time to the next, whole
  periods, so steady motion between the ticks no longer judders (seen on the Frame). A movie's
  and `debug.fixed_step`'s own steps still stand.
- **The 72 Hz fall back said once** (HaloCE-VR 82b6d12e): the Frame's SteamVR offers only the
  display setting's rate, so asking for 72 every twenty seconds got nothing.
- **No start on a reinstall in Lepton** (HaloCE-VR 6be73ed4, `UpdateReceiver`).
- **The runtime's extensions listed once**, not at each retry.
- **The Steam library launcher and installer** (ringfall's, above).

Already here: the vDSO clock (halo-ce-universal's), the profiler's texture timer only while its
graph shows, the null tag table and the VR menu's allocations (HaloCE-VR 7d96cc32, 19c433c9).

Not taken (decided 2026-10-22, the owner leaving it to this port's judgement: each changes how every
headset draws, Quest and PC VR included, and only a Frame can show what it gains; Test73's first
need is that its untested whole builds and runs). Candidates once a Frame can measure them:
- single-pass stereo (multiview; Mjolnir VR turned it off by default on 2026-10-16: doubled pictures
  online; HaloCE-VR has it on);
- one atlas swapchain for the eyes and the quad (HaloCE-VR 3cfa297b: SteamVR's GL binding makes its
  own context current at each acquire, wait and release; this port's deferred releases already take
  the zink stalls ringfall measured);
- the runtime's hidden-area mask drawn first in each eye (HaloCE-VR 6eaf8e92, XR_KHR_visibility_mask:
  the GPU's frame from 11.5 to 10.0 ms at 1.5x; it would draw on the Quest too);
- cutscenes' and menus' screens drawn at the quad's resolution (HaloCE-VR 75cdea48; here the 3D
  screen's layer takes each eye's whole image, so it needs the layer's rectangle in the frame ABI).
Meanwhile the Frame's automatic resolution is 1.0 (1728 an eye). Mjolnir VR's field advice: keep the
Frame's display at 72 Hz, or lower `vr.resolution_scale` (about 0.85) for 90.

## Build and deploy

```bash
export ANDROID_HOME=$HOME/Library/Android/sdk JAVA_HOME=/opt/homebrew/opt/openjdk@17
python3 configure.py --lto=off --pgo=off --vr
ninja android_apk          # port/android/app/build/outputs/apk/vr/debug/app-vr-debug.apk
tools/steam_frame/extract_maps.py "Halo.iso" /tmp/halo   # once: maps out of your disc image
tools/steam_frame/deploy.sh --maps /tmp/halo/maps        # copy, install, start
```

**To play** on the headset alone, launch **HaloCEVR** from the Steam library. It is a Lepton
devkit title running `~/devkit-game/HaloCEVR/HaloCE-VR.apk`, and `deploy.sh` refreshes that
copy. To register it on another headset, copy the APK there, then run:

```bash
ssh steamos@<device-ip> 'cd ~/devkit-utils && python3 steam-client-create-shortcut --parms "{\"gameid\": \"HaloCEVR\", \"directory\": \"/home/steamos/devkit-game/HaloCEVR\", \"force_appid\": \"\", \"argv\": [\"HaloCE-VR.apk\"], \"env\": {}, \"settings\": {\"steam_play\": \"1\", \"compat_tool\": \"lepton\"}, \"lepton_args\": \"\"}"'
```

**The refresh rate** follows the Steam Frame's display setting: SteamVR offers the app only
the rate it is on.

**To develop**, start **Lepton Development** from the Frame's Steam library first. Logs:
`adb -s 127.0.0.1:5555 logcat -s halo`.

Ninja does not rerun Gradle when only Java sources changed (the SDL patch, for example). Run
`./gradlew -PhaloVr assembleVrDebug` in `port/android` in that case.

## How it fits together

**Host (64-bit, `port/android/host/host_xr.c`).** The host owns:
- the Khronos loader, 1.1.63, fetched from Maven Central with its SHA-256 checked;
- the instance and a GLES session on the game thread's EGL context;
- six swapchains: left eye, right eye, a quad (the flat screen or HUD), the hand's reticle, a
  fade to black, and the scope;
- controller actions for the Frame, Touch and Index profiles;
- recentring.

The guest calls seven functions (`host_imports_vr.list`) with plain structures
(`halo_android_abi.h`, layout asserted on both ABIs). Swapchain images go to the guest as GL
texture names, which it draws into directly.

**Guest platform layer (`port/linux/src/vr_frame.c`, `vr.h`).**
- **Frame protocol.** The runtime's frame is begun by whichever comes first: the main loop's
  time update (`vr_frame_seconds`, Test73), `vr_aim` (`player_control_update`), `vr_stereo_begin`
  (`main_game_render`) or `vr_present` (`D3DDevice_Present`). It is ended in `vr_present`, which
  replaces the window blit and swap, so `xrWaitFrame` paces the loop. Halo interpolates its 30 Hz
  simulation to the display rate; since Test73 its clock steps by the frames' display times
  (whole periods), not by the loop's own measure, which wandered with the tick and the drawing.
- **Screen.** In VR the game draws its 640×480 screen at the eye resolution
  (`vr.resolution_scale` × 1728, through the existing `screen_scale`).
- **Flat frames** (menus, loading, cutscenes) copy the picture to an opaque quad floating ahead
  (`vr.screen_distance`, `vr.screen_width`).
- **Eye views.** An eye's view is the game camera's position plus the tracked eye offset (head
  reach clamped to 0.35 m; 1 world unit = 10 ft), turned by the VR heading. Its frustum bounds are
  `{tanL/A, tanR/A, tanD, tanU}` with a 90° vertical field of view and A = 4/3. That is exactly
  `render_camera_build_frustum`'s off-centre form.
- **Copies to swapchains** run with `GL_FRAMEBUFFER_SRGB_EXT` disabled. The game's pixels are
  gamma-encoded already.

**Game side (`port/linux/game/vr_render.c`, `port/linux/include/halo_vr.h`).**
- **Windows.** `vr_render_windows` turns `main_game_render`'s single player window into four
  windows: left eye, right eye, HUD, console. While a hand-aimed weapon is zoomed it makes five:
  left eye, right eye, scope, HUD, console. `render_frame` then renders them in its own window
  loop. `render.frame_index` advances once per frame, and each eye has its own `window_index`, so
  lens-flare occlusion and fog history stay per eye.
- **Eye resolve.** `vr_render_window_end` copies each eye's back buffer into its swapchain image.
- **HUD pass.** It clears to transparent and draws only `interface_draw_screen`, the screen
  flash and the UI widgets. `vr_present` shows that image head-locked with alpha, far away
  (`vr.hud_distance` 15 m, `vr.hud_width` 10 m, about 37° across, as HaloCEVR's), so the eyes
  needn't refocus between it and the world.
  - It is drawn from the head's camera, with frustum bounds matching the panel's field
    (`vr_hud_bounds`). Nav points and friends' names are projected from where the eyes are, so
    they sit over what they mark (not where the hand points).
  - The motion sensor turns with the head (`vr_render_motion_sensor_yaw`), as the HUD does.
- **Once per frame** (left eye only): the sky's animation phase (`render_sky.c`), weather
  simulation, glow particles, and the first-person weapon's pose. The weapon is posed from the
  head between the eyes. The fog's screen layers are left out of the eyes.
- **Head aim.** `vr_player_control_facing` (in `player_control.c`) sets the player's facing to
  the head's direction turned by the heading.
  - The right stick turns the heading, not the game: `vr.snap_turn` (30°) or
    `vr.smooth_turn_speed`.
  - Pressing both sticks recentres.
  - When the game turns the player itself, the heading follows.
  - View magnetism is off while the head aims.

**Hand aim (`vr.aim = "hand"`).**
- **On foot.** The right controller's aim pose sets the facing. Shots, grenades and melee follow
  the aiming vector.
  - The left stick is turned to move relative to the head.
  - In local games shots start at the hand, through `unit_adjust_projectile_ray`, unless a wall
    stands between the hand and the unit's eye.
- **Weapon model.** It is posed from a camera at the grip minus `vr.weapon_offset_*` (in the aim
  frame).
- **Reticle.** The HUD crosshair is hidden. A reticle quad is drawn where
  `collision_test_vector` along the hand's ray meets the world.
- **Seats.** In vehicle and turret seats the head aims.

**Input.** The headset's controllers merge into the first Xbox pad (`xinput_sdl.c`). Each frame
`layout_controls` (`vr_frame.c`) builds that pad from the controllers by `vr.controls`:
- `"pad"`: the Frame controllers map one-to-one onto the Xbox pad (A/B/X/Y, bumpers as
  white/black, d-pad, view/menu as back/start).
- `"vr"` (default), a VR-native layout from each hand's own buttons (`hand_buttons` in the frame):

  | Input | Action |
  | --- | --- |
  | Weapon hand's trigger | Fire |
  | Off hand's trigger | Zoom (the scope) |
  | Right A | Jump |
  | Right B | Action / reload |
  | Right X | Switch grenades |
  | Right Y | Switch weapons |
  | Right stick click | Melee |
  | Weapon hand's bumper | Throw a grenade |
  | Off hand's bumper | Flashlight |
  | Left stick | Move; click to crouch |
  | Right stick | Turn |
  | Menu | Pause |
  | View | Back; held 1 s, recentre (with a buzz) |

While the head or hand aims, the right stick is consumed for turning.

**Gestures** (`update_gestures`, either layout; injected in `handle_one_player_input`):

| Gesture | Does | Setting |
| --- | --- | --- |
| A hand swung up or down fast | Melee | `melee_speed` (2.5 m/s) |
| Off hand at the side of the head | Flashlight | `flashlight_distance` (0.2 m) |
| Head lowered below the height at the last recentre | Crouch (held) | `crouch_height` (0.15 m) |
| Weapon hand's grip at a shoulder | Switch weapons | `holsters` |
| Off hand's grip held (with the gun) | Two-handed aim: the gun points from the weapon hand to the off hand | `two_handed` ("grip", "auto", "off") |
| Palms together, gripping | Swap the weapon hand | |

`vr.left_handed` starts with the gun in the left hand; the first-person model is drawn
mirrored (`halo_vr_mirror_winding` flips the triangles' winding).

**Weapon feel.** When zoomed, the aim is eased toward the hand's (`steady_aim`, after
HaloCEVR's half-life formula), steadying the scope. Shots buzz the weapon hand by weapon (and the
off hand when two-handed), scaled by `vr.haptics`.

**VR settings in the pause menu** (`port/linux/game/vr_menu.c`). Halo's menus are widget
tags in each map, so when a level's tags load the VR build adds its own, cloned from the solo
pause menu's: same font, colours, buttons and boxes.
- **The pause menu** gets a fifth item, VR SETTINGS. Its button hints (B back, A select) move
  from under the list to under the mission objectives, making room.
- **VR SETTINGS** is the pause menu's backdrop and boxes with nine settings in two columns:
  controls (VR / Xbox), aim (hand / head), gun hand, turning (snap 30 / snap 45 / smooth),
  room-scale, scope, vehicles (inside / chase), steering (stick / head / hand), cutscenes
  (3D / flat).
- **Changing a setting:** A or right steps it on, left steps it back, and B returns to the pause
  menu. The laser pointer clicks them too.
- **Saving:** each change is written into `config.toml` (`config_write_*`) and taken up at once
  (`vr_reload_settings`).
- **How the tags are added:** `cache_file_add_tag` puts tags made in memory after the map's own,
  in a copy of its tag table. A button's text comes from code (game data input function 41), and
  its changes run event handler functions 102 and 103, one past the end of each table.

**Menus' laser pointer** (`vr_ui_pointer`, behind `halo_ui_pointer_update`). The weapon hand
points at the screen the menus are on, as the desktop builds' mouse does: the flat screen, or
in stereo (the pause menu) the HUD's panel. Its trigger clicks (with a tick of buzz), the right
B goes back, and a dot on the reticle's layer shows where it points. The pad's buttons still work.

**Room-scale** (`vr.roomscale`, off by default; after HaloCEVR's). Each tick on foot,
`biped_update_moving` moves the player's collision pill by how far the head walked from where
the player stands (`vr_room_step`), with `collision_move_pill`, so a step into a wall slides
along it as walking does. Then that place to stand moves to the head.
- The whole step is taken even where a wall stopped the player. The view stays with the player
  rather than in the wall, and the room and the game drift apart; recentre to line them up.
- The eyes lean from that place, blended between its last two ticks as the game's camera is
  (`head_offset`). Walking then has no added latency and no judder at the 30 Hz ticks.
- Vehicles, cutscenes, scripts holding the player, death and network games hold it. Walking
  resumes from wherever the head is then, as does a jump of more than 0.5 m in a tick (tracking
  lost, a recentre).
- `vr.diag_walk_speed` walks the synthetic head ahead and logs how far the player went each
  second.

**Scope** (`vr.scope`, with the hand aiming). While zoomed:
- A pass between the eyes and the HUD (window 2, a repeat pass) renders the view along the gun.
  The camera is the hand's aim, rolled with the gun and kept out of walls. Its field is the middle
  of the game's zoomed one: half its height for a round sight, the sniper rifle's wide rectangle
  for the sniper.
- It draws into a square at the corner of the back buffer, as large as the scope's image (768²),
  so its cost scales with the scope, not the eyes. It has no HUD, fog screen or mirror, and the
  first-person gun is left out.
- `vr_resolve_scope` copies it through a mask (disc or rounded rectangle, a darker rim, a thin
  cross) into the scope swapchain. The image is shown on a layer held at the gun, at HaloCEVR's
  per-weapon offsets (pistol, sniper rifle, rocket launcher), `vr.scope_size` across.
- The eyes are never zoomed: the first-person gun stays in the hand, and the HUD layer leaves out
  the zoom mask.

## Measuring without wearing the headset

- `vr.force_render` renders stereo with the headset in standby. It uses a synthetic head and
  hands: the head is turned by `vr.diag_yaw`, the right hand by `vr.diag_hand_yaw`.
- `vr.dump_frame` and `vr.dump_cinema_frame` write the eyes and HUD of a gameplay or cutscene
  frame, and the scope when one is shown (`vr-scope.bmp`). A dump logs the aim state (seated or
  on foot, hand or head, yaws).
- `vr.diag_zoom_seconds` zooms in that long into play, switching first to a weapon that zooms.
  `vr.diag_two_handed` holds the synthetic left hand on the gun.
- `vr.timing` logs where a frame's time goes (`[vr-frame]`); `vr.timing_gpu` waits for the GPU
  to time it separately.
- `debug.telnet_console` opens a script console on 127.0.0.1:2323. Reach it with
  `adb forward tcp:2323 tcp:2323`. Useful commands: `map_name levels\a30\a30` loads a level,
  and `cinematic_skip_start_internal` / `cinematic_skip_stop_internal` skip its intro.
- `simpleperf` from the NDK runs in Lepton (`adb push` it to `/data/local/tmp`) and profiles the
  game thread. Threads' CPU time: `/proc/<pid>/task/*/stat`.
- Large copies over SSH time out while the game runs; use `adb pull`.

## Settings (`config.toml`, `[vr]`)

`enabled`, `stereo`, `resolution_scale` (1.5), `refresh_rate` (90), `world_scale` (0.328084 units/m),
`cinema_3d`, `cinema_separation`, `cinema_convergence`, `cinema_distance`, `cinema_width`, `arms`
("ik" / "hidden" / "animated"),
`screen_distance`, `screen_width`, `hud_distance`, `hud_width`, `aim` ("head"/"hand"),
`weapon_offset_right`/`_up`/`_back`, `snap_turn`, `smooth_turn_speed`, `vehicle_view`,
`vehicle_steering`, `controls` ("vr"/"pad"), `move_relative` ("head"/"left"/"right"),
`two_handed`, `left_handed`, `melee_speed`, `flashlight_distance`, `crouch_height`, `holsters`,
`haptics`, `scope`, `scope_size` (0.06 m), `roomscale` (false).

Diagnostics:
- `probe_seconds`: dim colours in each eye.
- `force_render` + `diag_yaw`: synthetic head with the headset in standby.
- `dump_frame`: writes `vr-eye0.bmp`, `vr-eye1.bmp` and `vr-hud.bmp` to the data folder.

`tools/steam_frame/deploy.sh --config vr.KEY=VALUE` edits these on the headset.

## Known gaps and next steps

- **Scope.** Its offsets and size are HaloCEVR's starting points and need tuning in the headset.
  Its reticle is our own cross, not the game's (the HUD isn't drawn into it). With the head
  aiming (`vr.aim = "head"`) a zoom shows nothing.
- **Gesture thresholds** (melee speed, duck depth, holster spots) are HaloCEVR's defaults and
  need tuning worn.
- **Vehicles.** `vr.vehicle_view = "first_person"` makes the director treat every seat as first
  person, which hides your own body. The eyes sit at your character's `head` marker. A seat's
  camera marker is the chase camera's place, so it isn't used.
  - The view turns with the vehicle's yaw only, keeping the horizon level. A passenger seat
    facing aside (the Pelican's) keeps the turn it had when you sat down.
  - The driver's right stick steers as in flat Halo, and your head only looks. Gunner seats aim
    with your head, and the handheld weapon is hidden in driver and gunner seats.
  - `vr.diag_drive_seconds` seats you as a driver for unattended tests; spawn a vehicle first
    with `cheat_all_vehicles`.
  - Untested on the device.
- **The HUD** is a flat panel locked to the head. Its image is the quad swapchain (1280×960,
  about 34 px a degree at the default size), shared with the flat screen.
- **Existing `config.toml` files** keep the HUD's old 1.5 m / 1.4 m (the file holds every key):
  set `vr.hud_distance = 15` and `vr.hud_width = 10` there.
- **Comfort options** are missing: no vignette, no seated or standing height.
- **Map loads** block the game loop. SteamVR shows its own loading state while one runs.
- **Battery.** The Frame discharges even on the Mac's USB.

## Credits

The controls, gestures, aim smoothing, haptics and scope follow the designs of LivingFray's PC
mod [HaloCEVR](https://github.com/LivingFray/HaloCEVR), re-implemented here for the decompiled
game.
