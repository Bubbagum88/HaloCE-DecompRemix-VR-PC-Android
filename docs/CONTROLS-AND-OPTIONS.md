# Controls and gestures (Test73)

Every control and gesture of the VR game (Quest, Pico, Steam Frame and PC VR), what changes it, and the flat builds'
keys. Open the pause menu (the Menu button) and choose VR SETTINGS to change any of it. Every VR feature is on
after the Test73 update; anything you turn off stays off. The notes of earlier tests are in docs/CONTROLS-HISTORY.md.

## Buttons (defaults)

- The gun hand is the right hand (LEFT-HAND MODE swaps it). A and B are the gun hand's lower and upper face buttons,
  X and Y the other hand's.
- Gun hand trigger: fire.
- Zoom: the right stick's click, while your hands do the melee. (With MELEE SPEED OFF, or seated, the other hand's
  trigger zooms instead: the left trigger for right-handed play.)
- A: jump (JUMP). B: use and reload (USE / RELOAD): take a weapon, get in a vehicle; with MANUAL RELOAD it drops
  the magazine.
- X: a tap throws a grenade, a hold switches grenades (GRENADE, NEXT GRENADE). Y: next weapon (NEXT WEAPON).
- Left stick: move. Its click: the reticle on or off.
- Right stick: turn. Held down: crouch. Pushed up: BULLET TIME.
- Grips: hold the gun, holster, grab, climb, take grenades and magazines, hold a vehicle's controls.
- Menu button: pause. Recentre: both stick clicks together, or hold the left controller's upper face button (Y; View
  where a controller has one) for a second.
- PUSH TO TALK has no button until you give it one (VOICE CHAT > MICROPHONE: PUSH TO TALK or OPEN MIC).
- Seated in a vehicle: the stick clicks sound the horn; R UP and R DOWN do nothing.

## Changing a button (VR SETTINGS > BUTTONS)

- A, or left and right, on a row chooses a button: it shows with a "?" and nothing changes until A sets it.
- A button another action has asks first: CANCEL, SWAP, CLEAR (the other action gets none) or BOTH (one button does
  both). The line at the bottom says whose it is and what A will do.
- Every action can be NONE. RESET CONTROLS is the first and the last row; (DEFAULT) marks an action's own button.
- A "*" marks a button that does nothing for now; a "+" marks a button two actions share.
- The menus never use these buttons, so no choice can lock you out of them.

## Your gun

- WEAPONS: PHYSICAL (default): your grip holds the gun; let go and it falls, at a holster it is put away, and an
  empty hand gripping by a gun on the ground takes it. LOCKED: the gun always stays in your gun hand.
  PHYSICAL + MP: physical in multiplayer too.
- TWO HANDS: the other hand at the gun's front grip steadies it (AUTO LOCK; SQUEEZE: only while gripping; OFF).
- HAND SWAP: palms together and the other hand's grip passes the gun across (10 cm).
- HOLSTERS: over each shoulder and at each hip. Grip there to put the gun away or draw one; the hand buzzes as it
  comes into one. HOLSTER HAPTICS off turns off only that buzz: reload and other haptics still follow the global
  HAPTICS strength (GAMEPLAY).
- WEAPON PULL: point a free hand at a weapon lying within PULL REACH (3 m), squeeze, then flick the hand back and it
  flies to you (PULL STYLE GRIP: keep squeezing instead). PULL GLOW shows what can be pulled.
- SCOPE (GAMEPLAY): a zoomed weapon shows its zoom in a scope held at the gun. SCOPES: each weapon's scope moves
  FORWARD, UP and RIGHT (1 cm steps, up to ±30 cm) and changes SIZE (up to 400%).
- AIM STEADY (HUD + RETICLE) smooths the aim. AIM: HAND (the gun aims) or HEAD (where you look).
- DEFLECT SHOTS: hold the gun in a shot's path and it glances off; swing the gun or a fist to bat it back
  (DEFLECT AID, DEFLECT FORCE).

## Manual reload

- MANUAL RELOAD (BUTTONS page): B drops the magazine; the gun never reloads by itself while it is on.
- Take a fresh magazine from a pouch with the free hand: HIP POUCH at that hand's hip, SHOULDER POUCH behind its
  shoulder (MAG POUCH SIDE: AUTO, LEFT, RIGHT or BOTH). RELOAD INPUT: the free hand's GRIP or TRIGGER takes it.
- Push it into the gun's magazine well. If the chamber was empty, charge the gun: take the slide or charging handle
  and pull it (CHARGE GRAB is how close your hand must be).
- Shotgun: shells one by one, then cock it. Rocket launcher: its tubes. Flamethrower: its canister.
- Needler: shake it to reload. Plasma weapons have no magazine: SHAKE COOLING cools a hot one faster when you shake
  it (offline).
- An emptied gun that must be charged ticks your gun hand every 1.5 s until you charge it.
- MAG DEBRIS: dropped magazines stay where they fall until the map changes.
- A weapon that cannot be reloaded by hand keeps the game's own reload.

## Grenades

- PHYS GRENADES: two grenades wait at your waist, frag on the left and plasma on the right (GRENADE DOWN 60 cm
  below your eyes, GRENADE FWD 12 cm, GRENADE GAP 18 cm).
- A free hand's grip takes one; let go of the grip to throw. Your hand's speed is the throw's (THROW POWER 1.5x, at
  most 15 m/s).
- GRENADE SIZE: 100% is the game's own grenade.
- X still throws (a tap) and switches (a hold).

## Fists and melee

- MELEE (BODY): IMPACT (default): a hand moving faster than MELEE SPEED (2 m/s) strikes what it sweeps through,
  harder the faster. SWING: a fast swing up or down makes the game's own melee. "+ ONLINE" also in network games.
  MELEE SPEED OFF turns the hands' melee off (the right stick's click then melees, and the trigger zooms).
- FIST REQUIRED: grip and trigger together make a fist for melee.
- FIST COMBAT: punch the enemy you look at. LUNGE: a punch at an enemy up to 12 m away carries you to it, with a
  Spartan leap (LUNGE HOP). HIT ASSIST (50 cm) lands a punch that passes close to its body. FIST REACH, ENEMY HEALTH.
- Block: hold a hand or forearm up between your face and the attacker. Parry: swipe a hand hard just before its
  blow lands; the attacker staggers, open to a takedown or a grab.
- COUNTERS: an enemy about to strike shows a blue warning and taps both hands; punch toward it to undo its blow and
  knock it down.
- COMBAT MOVES: duck or sidestep to dodge; arm-control and jump-pummel openings.
- COMBO DISPLAY counts your combo; HIT HIGHLIGHTS lights the blows.

## Grabbing and bodies

- NPC GRAB: grip near an enemy or an ally to take hold of it (GRAB ASSIST: 30 cm from its body); LIFT and THROW set
  how strongly. ONE-HAND HEAVIES: an Elite or a Hunter lifts with one hand (off: the second hand lifts).
- WORLD GRAB: weapons, equipment and movable props; OBJECT THROW sets how far they fly. CUSTOM SCENERY and
  CUSTOM NPC RIGS: mods' props and characters too.
- LIFT VEHICLES: grip an empty Warthog, Ghost, Scorpion or turret and lift it (offline).
- DEATH RAGDOLLS, ACTIVE RAGDOLL, GRAB RAGDOLL, NPC RESCUE and IMPACT DAMAGE: what bodies do when grabbed, thrown or
  killed.
- FINGERS: your fingers follow yours on the controller; a free hand stops at what it touches, its palm laid flat.
- ARMS FROM (BODY): AUTO, CHARACTER or FIRST PERSON: with a custom character, its own arms reach to your hands.

## Moving

- MOVE WITH: the left stick moves you where your HEAD faces, or where the LEFT HAND or RIGHT HAND points.
- TURNING: SMOOTH or SNAP (COMFORT: SMOOTH SPEED, SNAP ANGLE, VIGNETTE).
- VEHICLE TURN (COMFORT, and VEHICLES > VEHICLE OPTIONS): SMOOTH (default): if you snap turn, a vehicle's seat
  turns you smoothly at SMOOTH SPEED, and you snap again once you are out; AS SET: a seat turns as TURNING says.
- ROOM-SCALE: walk about your room. Duck to crouch (CROUCH DEPTH 35 cm below your height at the last recentre).
- Sprint: BUTTON SPRINT (the left stick's click; SPRINT TOGGLE: a click starts and stops it) or ARM RUN (swing your
  arms as in running; ARM EFFORT is how hard). SPRINT SPEED 1.5x, offline.
- SLIDE: sprint, then crouch (the crouch button, or duck with CROUCH SLIDES); stand up to stop, jump to cancel
  (JUMP CANCELS). SLIDE DISTANCE, SLIDE FRICTION, SLIDE IMPACT.
- WALLRUN: jump near a wall while moving along it. WALLJUMP: press jump again beside the wall and you leap where you
  look. WALL SPEED, WALL TIME, WALL LEAP.
- GRIP CLIMB: touch a wall with a free hand, squeeze grip, pull yourself up, and let go to launch (CLIMB LAUNCH,
  CLIMB GRAB).
- BULLET TIME: the right stick pushed up slows the world (BULLET TIME MODE: HOLD or TOGGLE; TIME SCALE 25% to 65%).
  Solo games only; not in a seat, a menu or a cutscene.

## Head gestures, HUD and menus

- Flashlight: bring the other hand to the middle of your head (FLASHLIGHT: 20 cm; OFF turns the gesture off). A
  controller with a bumper: the other hand's bumper too.
- HUD: hold the gun hand beside its own temple for a moment to hide or show the HUD (HUD TAP on HEAD GESTURES,
  HEAD TAP on HUD + RETICLE: 10 cm); HUD + RETICLE > HUD too.
- WRIST HUD (off): shield, health, ammo, grenades and the motion tracker on your other wrist, shown while you look at
  it.
- CROSSHAIR, CROSSHAIR SIZE and OPACITY: the reticle.
- MENU POSITION: HEAD (menus ride ahead of your head), WORLD (fixed in front of you: lean in to read) or FOLLOW
  (fixed, brought back when you look well away). MENU DISTANCE, MENU SIZE, MENU HEIGHT. A stick click brings a fixed menu
  back in front of you. The launcher's Menu position button sets it too.
- THIRD PERSON (GAMEPLAY): on foot in a campaign or co-op, the view from behind you; aim with your head, and the
  buttons do the hands' work while it is on.
- CUTSCENES: IMMERSIVE, 3D SCREEN or FLAT.

## Vehicles

- Get in with B beside the vehicle, as the game does. The left stick is the throttle.
- VIEW: FIRST PERSON or THIRD PERSON. IMMERSIVE VEHICLE brings FIRST PERSON with it. HORIZON: LEVEL, HALF, VEHICLE.
- IMMERSIVE VEHICLE: grip the vehicle's own controls and turn them with your hands: the Warthog's wheel, the
  Ghost's handlebar, the Scorpion's drive stick (TANK DRIVE: push to drive on, pull to reverse, lean to turn) and
  the Banshee's flight bar (push and pull to dive and climb; roll it, or slide it with BANSH SLIDE, to turn). Each
  turns in proportion all the way to full lock and returns to centre when let go.
- HAND LOCK: while you grip a control, your hand stays on it and turns with it.
- COCKPIT LOCK: the cockpit stays still around you and the world moves. VIRTUAL WHEEL, GRIP GUIDE, CONTROL GLOW,
  STEER HAPTICS, COMFORT REACH (controls brought within reach), TANK HATCH (the view over the tank's hull).
- Without IMMERSIVE VEHICLE, STEERING: RIGHT HAND, LEFT HAND, HEAD or STICK.
- Turrets and gunners' seats: TURRET AIM: RIGHT HAND, LEFT HAND, HEAD or STICK.
- Passengers aim the gun in their hand and look around freely.
- Each vehicle's VIEW UP, FWD and RIGHT, and its controls' REACH, LEFT, HEIGHT and SIZE, line things up.

## Settings that change the controls

- LEFT-HAND MODE: the gun in the left hand; fire, zoom and the grenade swap hands. Vehicle STEERING and MOVE WITH
  follow when they used a hand.
- MIRROR CONTROLS (AUTO): left-handed, you move on the right stick and turn on the left, and the face buttons swap
  hands. OFF: the standard layout.
- MIRROR BUTTONS (AUTO): left-handed, the face buttons are on the gun hand even when the sticks stay standard.
- L STICK CLICK: RETICLE (default) or CROUCH (crouch moves to the click and R DOWN is left free).
- BUTTON SPRINT takes the left stick's click; what was on it comes back when you turn it off.
- MELEE SPEED OFF moves zoom back to the other hand's trigger and gives the right stick's click back to melee.
- WEAPONS PHYSICAL: the grip holds the gun, so a button on GRIP does nothing ("*").
- GRENADE on GRIP: NEXT GRENADE cannot be HOLD.
- CONTROLS: VR (this layout) or XBOX (as an Xbox controller).
- AIM: HAND or HEAD.

## Online

- Co-op: the host's VR INTERACTIONS (Server Setup > CO-OP OPTIONS, on by default) lets every VR player use fists
  and FIST COMBAT (lunges, combos, takedowns; the host deals each blow), waist grenades, manual reload, parkour and
  slides, and grab NPCs and objects. Off, or in PvP, those are the buttons. Online, a guard or a parry protects
  only the host, and DEFLECT SHOTS is the host's only.
- Offline only: sprint's speed boost, BULLET TIME, SHAKE COOLING, LIFT VEHICLES and CLOSE CONTACT.

## PC (flat): keyboard and mouse

- Defaults (Settings > Controls Setup changes any): W, A, S, D move; the mouse looks; left mouse fires; right mouse
  or G throws a grenade; F or Mouse 4 melees; R reloads; E is the action; Z or the middle mouse button zooms; the
  wheel or 1 switches weapon; X switches grenades.
- Space jumps; Left Ctrl or C crouches; Left Shift sprints; Q is the flashlight; Tab the scoreboard; Escape pauses.
- T chats, Y chats to the team, V is push to talk; F10 takes a screenshot; Keypad Enter is third person, Alt held
  looks around.
- A gamepad plays as on the Xbox. Flat PC: SPRINT, SLIDE, WALL RUN and WALL JUMP are in Player profile > MOVEMENT.

## Android (flat)

- Touch and gamepad: the Field guide's "Flat touch & gamepad".
