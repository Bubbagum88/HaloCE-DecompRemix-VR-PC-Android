# Test73b checklist: the shadows, your body's shadow, B in the menus, faster map downloads, sprint, CONTROLS, world scale

Private successor to Test73, **1.0.41-test73b / code86**, branch `test39-interaction-completion`, on the same
OpenCE (Build 256, its testing and fix-scenery-shields-network branches: network 34, hosts 34, joins 11 to 34).
Test73's checklist (TEST73-CHECKLIST.md) and the earlier ones still apply. Local work only; no push, publish or
install. Saved settings preserved, but for two one-time changes: the map upload limits' raise and SPRINT TOGGLE
(below).

The owner, on the delivered Test73 (a Quest 3 log and video): "basically everything works great, so regress
nothing, BUT, stencil shadows is a bit fucked up". Every item below is one of the owner's messages since.

Legend:
- [x] done and verified off-device (built, run or measured here);
- [s] source done and its source checks pass, **not yet compiled** (the single build pass compiles and checks
  these, and this list is updated then);
- [~] done; only the hardware can confirm it;
- [?] waits on the owner;
- [ ] not done.

## Stencil shadows (the owner: "leave it as intended by halofreak95")

- [s] `render.c` calls `stencil_shadows_render` after `rasterizer_transparent_geometry_stop` again, as
  HaloFreak95's fork (`halofreak/stencil-shadows` 2c055e464) and Test72 do; Test73's 10j (drawn between the
  lightmaps and the dynamic lights, the stencil bits juggled) is gone, and with it its test.
- [s] `stencil_shadows.c` is Test72's, token for token in the flat builds (his code, one face a draw, his
  `game.shadow_objects_stop`); `tools/test_test73b_shadows.py` compares it and compiles its casters.
- [x] "Fix the lights report ... only if you can guarantee it": no lighting change. None can be confirmed
  without a headset, and 10j showed how a plausible one breaks the level's later passes (the video: black
  shadows, grey ground).
- [~] The look on the Quest (the owner's headset).

## The VR player's body shadow (the owner: "i do want a vr player body shadow ... should also work with the games normal shadows if possible")

- [s] `vr_render.c` keeps the observer palette (`vr_publish_body`: the whole body, the head as the headset
  turns, the arms reaching the hands) when a peer or a shadow may take it (`display.stencil_shadows` or the
  game's shadows), and `vr_render_body_shadow_matrices` hands it over for this frame only, for the player's
  own body as drawn (BODY on LEGS or FULL).
- [s] Stencil shadows: the player's unit cast with that palette, its held weapon not (it is drawn at the
  eyes), the caps pushed 12 cm along the light so the shadow falls on the level and not on the first-person
  arms and gun.
- [s] The game's shadows: `render_objects.c` admits the player's unit to the shadow pass with that palette,
  skips what it carries, and widens the shadow map to the hands (`vr_render_body_shadow_radius`).
- [x] `tools/test_test73b_shadows.py`: the casters compiled and run in the flat and VR builds (2 negative
  controls), the pins for both shadow paths.
- [~] Immersion: the shadow moves with your head and hands (the owner: "unless its somehow immersion
  breaking/visually broken").

## B in the menus (a Steam Frame player: "the b button didnt seem to work in menus")

- [s] The cause: only the Quest's menus took the face buttons by their letters (`vr.touch_layout`); on every
  other controller the menus kept the game layout, where the right B is the game's X, and B went back only
  through the pointer while it was on the menus (the player's Frame log has no back at all).
- [s] Every controller's menus take the letters (the Frame's X and Y are on its right controller; Index's and
  Pico's left upper button stays back), and B goes back pointed at the menus or not, once a press
  (`vr.menu_back_press` latches the pointer's back or the game's B for the whole press).
- [x] `tools/test_test73b_menu_back.py`: the production block and the pointer's back run frame by frame in
  both orders (4 negative controls); `test_test30`'s harness follows.
- [~] On a Frame, an Index, a Pico and a Quest.

## Faster map downloads (the owner: "raise the download limit to max (i think 10mb) by default")

- [s] `network.map_share_upload` 20480 (the host's most: 20 MB/s, was OpenCE's 1024) and
  `network.map_seed_upload` 10240 (a helping player's most: 10 MB/s, was 256); both menus offer these.
- [s] `network.map_share_revision`: a config saved at the old defaults is raised once; a value chosen
  otherwise, and any choice after, is kept.
- [x] `tools/test_test73b_map_share.py`: the production config loader on the flat, VR and desktop editions,
  2 negative controls.
- [?] The trade-off, told to the owner: a host whose internet upload is slower than that gives the map
  transfer all of it while someone downloads; UPLOAD LIMIT lowers it.

## Where the logs are (the owner: "where are logs generating for steam and pc? these things should be clarified" / "do that for all launchers")

- [s] Windows: each start keeps the last run's `halo.log` / `halo-vr.log` in `logs\` beside the game
  (`<stem>_<date>_<time>.log`, the newest ten of each; copied, as the run before may still have it open).
- [x] `tools/test_test73b_logs.py` runs that function, built with the Windows clang, on a real folder (an
  empty log, the time in the name, the newest ten, PC VR's apart, a log still open; 3 negative controls).
- [s] The PC launcher: a LOGS page on its first page (the files, what is in each, buttons opening the game's
  folder, the logs folder and a separate data folder); the PC VR page points to it.
- [s] The Steam Frame: its logs folder kept every run's; now the newest ten, never this run's
  (`RunLog.pruneFolder`, run with javac in the test, a negative control).
- [s] The Android launcher says the Frame's folder on the Frame and the Quest's elsewhere; the note in the
  Frame's data folder, the bundle's README and the installer's last dialog name the logs; the in-game guide
  names every device's; README, PLAYER-GUIDE, the Windows README and mods.md too.

## Sprint in VR (the owner: "I want the sprint button to have it on toggle, not hold")

- [s] SPRINT TOGGLE (VR SETTINGS > LOCOMOTION, `vr.button_sprint_toggle`) is TOGGLE by default, and
  `vr.test73b_sprint_toggle_applied` turns it on once in a config saved before (`vr_initialize`, after Test73's
  features); HOLD chosen after is kept. A toggle stops on a seat, on recentring and when the game loses focus.
- [s] Found with it: BUTTON SPRINT reads the move stick's click; mirrored left-handed play read the turn stick's.
- [s] On the other controllers' fixed layout (Index, PICO, Steam Frame, HP) the move stick's click crouched too
  while BUTTON SPRINT was on: it sprints only now, and the turn stick held down crouches (seated, the click is
  still the horn). The Quest's remappable layout and CONTROLS: XBOX are unchanged (BUTTON SPRINT is the VR
  layout's).
- [s] BULLET TIME on the right stick up for every controller (it was the Quest's alone).
- [x] `tools/test_test73b_sprint.py`: the one-time switch and the layout's block run frame by frame (2 negative
  controls each); `test_test73_features` and `test_test20d` follow.
- [~] On a Quest, an Index or Frame, left-handed too.

## Sprint in the flat builds (the owner: "an actual button ... That shows up on the screen ... on PC too ... Shift maybe")

- [s] Android: a SPRINT circle on the touch screen (TouchControls, bit 16) while SPRINT (Player Setup > MOVEMENT)
  is HOLD or TOGGLE, not over the menus; the setting is read again as the menus close. Held, it sprints as the key
  does; a quick tap counts once. The touch editor places it (TouchLayout's 20th control); presets saved before
  import with it at its default place, a partial one is refused (TouchLayoutCodec).
- [s] The host passes the bit (`HALO_TOUCH_BUTTONS` 0x1ffff, host_sdl.c); `platform_sprint_held` reads it.
- [s] PC: Left Shift (`controls.sprint`, the default already; Controls Setup rebinds it); the launcher's SETTINGS
  says so in the flat build.
- [x] `tools/test_test73b_sprint.py` (2 negative controls), `test_test31_touch_lifecycle` (the HUD circle is now the
  21st), `test_touch_layout_codec` (old presets).
- [~] On a phone; Left Shift on a PC.

## CONTROLS in the launchers (the owner: "a controlled section ... For each controller type ... what can change certain mappings")

- [s] `assets/controls/controllers.txt` (the APK's, and the PC launcher's through `tools/embed_assets.py`): a page per
  controller (QUEST (TOUCH), PICO, STEAM FRAME, VALVE INDEX, HP REVERB G2, OTHER PC VR, TOUCH SCREEN, GAMEPAD,
  KEYBOARD + MOUSE), each with the settings that change it, and what every VR or flat player shares; every line
  checked against the code (the bindings, the Quest's defaults, the fixed layout, the keyboard's defaults).
- [s] Android: "Controls: every button, for your controller" beside the Field guide and on the game-data screen; a
  dialog whose "Controller: ... (change)" lists the pages, the headset's own first (`ControlsText.first`).
- [s] PC: CONTROLS on the first page (the SETTINGS row), the controllers as two rows of buttons, the chosen one's page
  drawn as What's New is, scrolled.
- [s] Text only, no pictures of the controllers (the owner: "you don't need to do the controller visuals").
- [x] `tools/test_test73b_controls.py`: the content against the code, the Android parser (javac) and the PC's (clang,
  ASan) on the real file, the wiring (2 negative controls).
- [~] The look on a Quest, a Frame and the PC.

## Held bodies (a tester: "the body point of origin doesn't come with you, so they become invisible")

- [s] The cause: the game culls, lights and shoots an object by the bounding sphere `object_compute_node_matrices`
  takes from its own pose's root, and a body held in the hands is posed after that, where the hands are (the
  owner's Test73 log: "root brought ... (1.1 m behind)"); out of view of that sphere it was not drawn.
- [s] `vr_npc_interaction.c` `npc_bounds_about_pose`: a held corpse's bounds about the pose drawn, as OpenCE's
  ragdolls' are, every tick it is held (its place in the map taken again; outside the map, left as it was).
- [x] `tools/test_test73b_held_body.py` (3 negative controls).
- [~] In a headset: hold a body up as a shield and look around it.

## WORLD SCALE (a player: "a world scale slider/option in the menu ... like most other world scale options in vr games")

- [s] VR SETTINGS > COMFORT > WORLD SCALE (`vr.world_size`, 70% to 150%): the game units a metre makes are
  `vr.world_scale`'s divided by it, so the eyes' separation, the head's and the hands' movement scale together, as
  other games' world scales do (120%: the world a fifth bigger around you). At once (`vr_reload_settings`); bounded
  50% to 200%, an unreadable value 100%. Menus and the HUD keep their size.
- [x] `tools/test_test73b_world_scale.py` (2 negative controls).
- [~] In a headset.

## Reports with no change (nothing found that the report describes, no log)

- [?] A PC tester: "opening graphics settings breaks the game", fixed by a restart. Opening GRAPHICS runs nothing; OK
  writes the settings changed and applies the display, which is idempotent. One headless run showed nothing. Ask:
  what "breaks" looks like, which screen, what was changed, and halo.log (the LOGS page).
- [?] "after cutscene that introduces the flood my camera stuck in 1 of the rooms they pop out of" (343 Guilty Spark):
  the cutscene's camera and teleports are the map's script; the headset follows the game's camera. Ask: the log,
  solo or co-op, CUTSCENES, whether it came back.
- [?] "hud has issues, it attached to gun and tiny, it randomly disappears ... hud was on face once, but i think i
  didn't have guns": the HUD is fixed ahead of the eyes, and only the reticle rides the gun. WRIST HUD (off by
  default) fits every part: a small panel on the off hand, at the gun's grip when that hand holds it, shown while
  you look at it, hidden with both hands on the gun, the whole HUD ahead in a seat. Otherwise the SCOPE, or HEAD
  TAP. Ask: WRIST HUD's setting, a screenshot or video, the log.
- [?] "there was a large count down durring the cutscene its still on my screen" (The Maw): the bridge cutscene's
  self-destruct count is the map's own screen on the bridge (`display_count`, drawn in the world). Its script
  stops the count when Guilty Spark aborts it and never removes the screen, so it stays there after the
  cutscene, as on the Xbox; the HUD's 6:00 timer is turned off before the ending. Co-op mirrors these calls.
  Ask: a screenshot or video if it followed the view away from the bridge or kept counting.

## Identity and documents

- [s] 1.0.41-test73b / code86: Gradle, `halo_port_version.h`, the VR banner (package-quest's identities and
  markers), What's New (its Test73b section first, then Test73's without its stencil light line), the pins.
- [s] CURRENT-STATE and CLAUDE.md (Test73 delivered, Test73b in progress), PLATFORMS-PLAN, this checklist, the
  device checklist, the field guide, the in-APK guide.
- [x] The full suite, the build pass (VR, flat, `windows_vr`, `windows`), the local commit and the packages
  (below).

## The build pass (last)

- [x] Full suite 203 of 203 on the built tree; the VR and flat Android builds (1762 and 1760 steps) with their
  guest ABI lint (799 + 923 units) and Opus tables check, then Gradle; `windows_vr` (842 steps) and the flat
  `halo.exe` (839), full rebuilds: no errors and no warnings anywhere (the Android host's files compiled again
  on their own to show it, as the build log can lose its first steps' lines). Every [s] item above is compiled.
- [x] Before the commit: `.gitignore` kept `assets/controls/controllers.txt` (the CONTROLS pages) out of the
  repository, as it keeps everything in `assets/` but the guides and fonts; an exception like the guide's lets it
  in (the APKs carried it already).
- [?] The runtime checks (the shadows' frames, the menus' B on each controller, the sprint toggle, the touch
  SPRINT circle, the CONTROLS pages on a device, a body held as a shield, WORLD SCALE in a headset, a PC VR
  smoke run): not run, the owner's call for Test73 ("just skip the running checks and provide the builds if
  possible. i will test it all myself"), kept for Test73b.
- [x] The APKs, the Steam Frame bundle, the Windows zip, the build and source zips: TEST73B-DELIVERY-STATUS.md.
