# Test73 device checklist

Automated checks cannot stand in for these. Test72's and earlier device checklists still apply
(TEST72-DEVICE-CHECKLIST.md and before).

Install the VR or Android APK over Test72 (1.0.39), Test70 (1.0.37) or Test69 without uninstalling;
saves and settings are kept. What's New appears once, its Test73 section first. Send the log after each
session: every check below writes what it did.

## The update's VR features (first, please)

- Open VR SETTINGS > IMMERSION: every feature shows ON (manual reload, MAG DEBRIS, fist combat, grenades,
  parkour, slides, grabbing, the immersive vehicle controls). BULLET TIME is on too.
- Turn one off (FIST COMBAT, say), quit the game and start it again: it is still off.
- The log says once: "the update's VR features on, once".

## Vehicles

- Warthog: drive with both hands on the wheel. Turning your hands to full lock turns the wheels to full
  lock, and halfway turns them halfway. HAND LOCK: your hands stay on the wheel and turn with it.
- Scorpion: the drive stick turns the tank its whole turn at full lock. Climb in and drive for two
  minutes: your view stays in the seat (it used to stay off to one side after the climb-in).
- Ghost and Banshee: the turn follows your hand evenly; the Banshee as before.
- Warthog passenger and the Scorpion's riders: lean and look around; the view settles once you sit.
- Let go of a control: the hand returns to the controller.
- VEHICLE TURN (a tester's request): set TURNING to SNAP. Drive the Warthog and turn with the right stick: it
  turns smoothly. Get out: the right stick snaps again (a push held while getting out waits for the stick to
  come back first). COMFORT > VEHICLE TURN: AS SET makes a seat snap too.

## Grenades

- Take a grenade from your waist (frag left, plasma right): it is the game's own size and you see it in
  your hand.
- Throw at a walk and at a full swing: the throw follows your hand.
- Tell us if the waist spot should move (VR SETTINGS > IMMERSION > GRENADES: GRENADE DOWN, FWD, GAP).

## Movement

- Wall run along a wall, then jump off: you leap where you look, not along the wall.
- Slide from a sprint (the left stick's click), and stand up to stop.

## Co-op with VR INTERACTIONS (two Test73 players)

- The host: Server Setup > CO-OP OPTIONS > VR INTERACTIONS shows ON (the default now), then host a campaign.
- The other player: reload by hand (B, a magazine from the pouch, push it in), throw a waist grenade,
  climb a wall, wall run, slide, and fight with FIST COMBAT (a lunge, a combo, a takedown). Each works as it
  does alone; the host's log says "[physical network] player N: manual reload committed", "grenade ...
  thrown" and "fist blow on ... dealt".
- With VR INTERACTIONS OFF, those are the buttons again.
- What to expect online: a knockdown lands as a shove on the host, a stun is seen only by the player who
  struck, and block, parry and shot deflection protect only the host. Tell us if any of these matters.

## OpenCE (Build 256 and its newer branches, network 34)

- Host a co-op campaign with ALLY FRIENDLY FIRE OFF (Server Setup > CO-OP OPTIONS): shooting or punching a
  Marine does nothing; ON, as in the campaign.
- Co-op on The Pillar of Autumn: every player gets through the blast doors (one could shut for good).
- Join an OpenCE game (any network from 11 to 34). OpenCE players join your games only once their build is on
  network 34 too: tell us if they cannot.
- Rat Race's energy shields (or a Custom Edition map's tripmines), online: a player who is not the host breaks
  them, and everyone sees them broken and coming back.
- PC: the menus show OpenCE's blue arrow cursor; it hides while a controller is used.

## Graphics

- STENCIL SHADOWS on (Video Setup > EXTRA EFFECTS): stand in a Marine's or a vehicle's shadow and turn the
  flashlight on: its light is as bright inside the shadow as outside. A Jackal's shield lighting the floor
  too. (The grass of a level is no longer darkened by these shadows.)
- In the headset: a cutscene's camera pan, a flying Banshee and a vehicle beside you move smoothly, with no
  judder.

## Menus, body and launchers

- Launcher: Menu position: WORLD. In the game the main menu stays where it opened when you turn your head.
- SPV1: your arms are the SPV1 character's (BODY > ARMS FROM: AUTO).
- The Field guide's VR controls page: it reads as headings and points; tell us if anything is missing.
- A new profile: every level is unlocked.

## PC (Windows)

- Launcher > GAME DATA > EXPORT SAVES, then IMPORT SAVES from that .zip: your saves are there; a backup
  .zip is in the saves' backups folder.
- Launcher > SETTINGS > GEOMETRY: SAFE and NORMAL both start the game.
- PC VR: as on the Quest above.

## Steam Frame (if you have one)

- No computer: in Desktop Mode put HaloCEQuestVR-SteamFrame.zip and your disc image in Downloads, unpack the
  zip there and open "Install HaloCE Quest VR": it adds HaloCE Quest VR to the library. In Gaming Mode start
  it from the library: its first start copies the game data out of the disc image, then the game starts.
- Steam's Exit game ends it, as does the main menu's QUIT GAME.
- Start it with the headset asleep, or SteamVR not yet up: it waits up to a minute instead of failing.
- The buttons and finger touches; the BUTTONS page names them.
- The logs for us: Documents/HaloCEQuestVR (logs/, launcher.log, logcat.txt, install.log).
