# Test42 device acceptance checklist

Status: pending owner testing. Install the matching private APK over the
existing app; do not clear app data. Keep the v1.0.18 and Test40/Test41
packages unchanged for comparison. Test solo first, then test multiplayer and
co-op separately.

## Identity, data and launch

- [ ] Confirm Android and Quest app names/icons, version `1.0.23-test42`, and
      that both install over the previous signed build without uninstalling.
- [ ] Confirm imported game-data sets, saves, controls and VR settings remain.
- [ ] Confirm the launcher selects the expected data set/revision and logs its
      recognized identity. Try each supplied image only with its known source.
- [ ] Confirm Quest enters VR, flat Android retains its original circular touch
      layout, and optional touch-anywhere look does not replace or move controls.
- [ ] Verify Safe Geometry is the default on both editions; confirm a saved
      explicit setting remains after restart.
- [ ] In Quest **Graphics > Display > Refresh**, select 90 Hz, then Auto. Confirm
      the log records a 90 Hz request followed by a runtime-default request, and
      that returning to a fixed rate still works.
- [ ] Open the Versions & updates section and confirm project updates and
      official upstream downloads remain separate; do not install an upstream
      build as a replacement for this candidate.

## VR and interaction carry-forward

- [ ] Check familiar Test37/1.0.18 weapon alignment, scopes, reticles, body,
      fingers, Safe Geometry, menus, hand collision and third-person vehicle
      defaults before enabling experimental options.
- [ ] Confirm the Test40 options CUSTOM NPC RIGS, MAG DEBRIS, LIFT VEHICLES and
      NPC RESCUE are off in a fresh profile. Upgrade an existing profile and
      verify its saved settings and game data remain intact.
- [ ] Manual reload on a supported profiled gun: left/right dominant hands,
      shoulder and hip pouch, magazine extraction/insertion, charge action,
      cancellation, empty/full ammo, weapon swap and map change. Verify ammo
      matches the HUD and never duplicates. Test unsupported weapons stay native.
- [ ] Adjust scopes on several different weapon profiles. Confirm the scope
      stays aligned with single and two-hand grips; compare pistol, rifle and
      sniper classes where present.
- [ ] Test vehicle and turret aim separately with right hand (default), left
      hand, head and stick. Enter/exit recenters as intended; check third-person
      default, passenger camera and Warthog glass option.
- [ ] With Shade turret, Ghost and Scorpion, hold each aim source steady near
      and over a moving target; confirm the mounted reticle stays on the selected
      weapon/muzzle ray instead of being pulled toward head-camera convergence.
      Compare reticle position with actual impacts, and check smooth movement
      while turning the head independently. Native shot autoaim remains intact.
- [ ] Test SHAKE COOLING only in a solo match with a supported heat weapon;
      compare enabled/disabled cooldown. Then enter a network game and confirm
      the feature is suppressed.
- [ ] Test WORLD GRAB with both hands and 12, 25 and 40 cm reach. Try wall,
      scripted object and ordinary solid object; ensure no wall penetration.
- [ ] Test NPC GRAB on a Grunt, Elite and Hunter; one-hand/two-hand rules,
      release, throw/impact, ragdoll and recovery. Vary NPC RIG SLOTS. Confirm
      this setting affects mod interaction rigs only and note frame time. Test
      native death ragdoll/settling separately: NPC RIG SLOTS does not set a
      native corpse count. Note that general object/memory pressure may reclaim
      eligible off-screen corpses; do not infer a fixed native count from one
      mission or tag.
- [ ] Test CUSTOM NPC RIGS with a compatible unclassified humanoid graph.
      Verify arm/hand selection and release; malformed/non-humanoid graphs
      must fail closed without a crash.
- [ ] Test CUSTOM SCENERY only on its validated supported collision-bound path.
      Verify unsupported tags, arbitrary BSP geometry and script-owned scenery
      stay native and cannot be grabbed or displaced through this option.
- [ ] Test MAG DEBRIS through repeated reloads, fill the bounded 32-slot pool,
      switch or discard the source weapon, and confirm existing visuals stay
      while later drops are skipped. Verify gravity, floor
      collision, stillness after settling, depth/occlusion in both eyes, and
      unchanged ammo. Confirm checkpoint/game-state load and map change clear
      stale debris.
- [ ] Test LIFT VEHICLES on supported unoccupied vehicles, and confirm occupied,
      parented, scripted, named/unsupported and online vehicles remain native.
      Try Warthog, Ghost, Scorpion and turret where eligible. Check bounds,
      collision, release and both-hand acquisition/hold feedback through master
      HAPTICS; there is no separate load-feedback control.
- [ ] Test NPC RESCUE only with an eligible live actor. Verify no recovery for
      an ordinary jump, AI movement, combat, scripted order, cutscene, occupied
      vehicle or network session. Let an eligible actor fall for less than ten
      seconds, land it and confirm the timer resets; then test a fall beyond ten
      seconds and recovery to a clear prior grounded capsule. Verify existing
      AI/mission state continues. Test blocked recovery space, checkpoint/game
      state load, actor deletion and map change.
- [ ] Set HAPTICS to 0 then a medium value. Check firing, contact, reload,
      movement and supported load feedback. Toggle HOLSTER HAPTICS off and
      verify only holster entry/draw/stow buzzes stop.
- [ ] Test parkour wall grab/climb/jump in solo. Verify it does not consume
      unrelated menu/input actions and is suppressed online.

## Networking and Android

- [ ] In the in-game browser, move the pointer between adjacent server rows and
      confirm hover/selection changes to the row under it. Test scrolling,
      arrows, menu categories, lobby-type switching and the launcher
      network/population selector with touch and controller input.
- [ ] In the in-game browser, join at least one network24 PvP server and one
      campaign co-op lobby. Test host and client separately; note map/image
      revision, network target, player count and route type.
- [ ] Confirm legacy targets still show their availability rule and do not
      change the network24 host protocol.
- [ ] Verify test session diagnostics show `local(0)` for solo even with a
      pending invite, then `network-client`/`network-server` only after a real
      join/host. Test local-only feature suppression after actual join.
- [ ] On flat Android, verify touch controls remain in their original positions;
      optional touch-look hides only the LOOK joystick while touch aiming works.
      Test controller hot-plug, menu navigation, triggers and touch fallback.
- [ ] In the Android HUD editor, hide a selected action control and confirm it
      neither draws nor captures touch in gameplay; use the control picker to
      restore it. Confirm controls from an upgraded install remain visible by
      default, and Save/Cancel/Reset preserve their documented behavior.
- [ ] Export a layout through Android's document picker, change several
      positions and visibility states, import the preset, then Save. Restart
      and confirm the imported layout persists. Repeat import then Cancel and
      confirm the old layout returns. Cancel both pickers, try an invalid and
      oversized file, and confirm none changes the active preferences. Check
      that the preset does not alter controller settings.
- [ ] If using an ARM-translation environment, inspect the log for page-hash
      write tracking; native ARM should default to page protection unless
      `debug.memory_watch=false` is configured.

For any issue, attach the full generated log and report APK version, headset and
Quest OS, Android device/controller, game image source/revision, mission/map,
network target, actual joined session type, exact settings, hand/buttons used,
and reproducible steps. Passing this checklist is the acceptance gate for the
runtime; host tests/builds alone are not headset acceptance.
