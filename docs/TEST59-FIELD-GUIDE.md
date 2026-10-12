# Test59 private candidate: 1.0.26-test59

## Test59: real hands in vehicles, the latest network, magazines back in

This private test build answers your Test58 sessions (the 05:18 vehicle log
and video, the 05:36 log and the 05:48 video). It installs over Test58 and
earlier (same package names and signing key, Android version code 71) and
keeps your settings, profiles, saves and imported game data.

### Vehicles (only with IMMERSIVE VEHICLE on)

- **Real hands.** In a vehicle your hands were the body's flat, fingerless
  hands, steered by the driver's animation, which is why your free hand
  turned with the wheel. The game puts a driver's gun away, and with the gun
  away there were no first-person arms at all. Now, while the immersive
  controls steer, your carried weapon lends its first-person arms (the gun
  itself stays hidden), so you get the tracked hands with finger gestures.
  Each hand moves only with your own hand. The rest of your body in the
  vehicle is as before.
- **Controls where you can reach them.** Your Test58 log had the Warthog's
  wheel 74-97 cm from your eyes (arms stretched) and the Scorpion's stick
  2.2 m away: it was placed once, half a second after getting in, while the
  driver was still climbing in. The stick and the Banshee's bar are now
  placed from your eyes every frame. **COMFORT REACH** (VEHICLES page, on)
  brings any control further than 55 cm in toward you on the same line.
  If you hid the Warthog's wheel to line it up with the model's, it stays on
  the model's wheel.
- **Ghost.** Its grips take your hand 2 cm sooner and along more of each
  grip.
- **Tank.** **TANK DRIVE** (VEHICLES page, on): push the drive stick forward
  to drive, pull it back to reverse; tilt it to turn as before. The stick
  leans as you push. The thumbstick still works, whichever is pushed
  further wins. It drives where your machine runs the tank (solo or as the
  host).

### OpenCE Build 201 and the network

- This build hosts on **network 28**, OpenCE's latest (Build 201), and joins
  hosts of networks 11 to 28. **All compatible networks** is still the
  launcher's default, and the selector lists every network one by one,
  **network 27** included.
- Network 27 added map sharing: an OpenCE player missing a Custom Edition
  map asks the host for it. This app doesn't share maps, so its host answers
  "the host does not share its maps" straight away instead of leaving the
  player waiting.
- Network 28's rules are in: a multiplayer map's first scripted BSP is kept,
  lights and the flashlight stay on in big matches with many players or
  vehicles, and a second weapon you pick up while firing is readied.
- Also from Build 201: the overshield's slow drain no longer flashes your
  shield meter and plays the hit sound on clients, bodies the host moves
  are no longer drawn floating or in walls on clients (never a body your VR
  hands or ragdolls are holding), and big co-op fights draw more effects
  before running out of room.

### Manual reload

- **Your magazine goes back in.** In your video you pulled a magazine out
  and held it at the gun for three seconds, and it wouldn't go back. Now
  bring it back to the well (lined up, as a fresh one) and it locks in,
  whether you're still squeezing or let go right there. If you dropped it,
  squeeze it where it lies (DROPPED MAGS shows it) and put it back. The gun
  keeps exactly the rounds it had and fires again. A magazine from a pouch
  works as before.
- **No more jitter while walking.** The gun was drawn from your view each
  frame, but the hand on the magazine came from the game's 30-per-second
  step, so while you walked they slid apart and snapped back. Both now
  come from the same view.

### Ragdolls

- **DEATH FORCE** (VR Settings > IMMERSION, the new RAGDOLLS screen, with
  DEATH RAGDOLLS; STRONG by default).
  Shot dead, a body now goes back along your shots as hard as the burst that
  killed it: an assault rifle burst throws it back about 2.5-3.7 m/s with a
  little lift (Test58 gave it 0.04 m/s, so it dropped where it stood), a
  sniper round about 4.7 m/s. Explosions throw bodies about twice as hard,
  with more lift, and a body right at a blast keeps more of the blast's own
  throw (Test58 clipped every one to 9 m/s). **CLASSIC** is Test58's feel;
  **HUGE** throws further still.
- Living NPCs you drop or throw still get up within 1 second.

### Checked here, and what to try

Every change has an automated check, and the full regression suite passed.
Nothing here has been tried in the headset yet. See TEST59-DEVICE-CHECKLIST.md.

---

# Test58 private candidate: 1.0.25-test58

## Test58: vehicle controls where your hands are

This private test build fixes what your Test57 session found: the Warthog's
wheel and the Scorpion's stick never showed up or took your hands, and the
reticle jittered with immersive vehicles. It installs over Test57 and earlier
(same package names and signing key, Android version code 70) and keeps your
settings, profiles, saves and imported game data. Nothing else changes.

### Why the Warthog wheel and the Scorpion stick didn't work

Test57's new log line says how far each missed squeeze was from the
controls. Your log showed every Warthog squeeze missing by about **540 m**
and every Scorpion squeeze by about 2 m.

- **Warthog:** the wheel's position was read from the wrong number. The game
  stores a marker's few-centimetre offset from its bone next to the bone's
  real position, and Test56 and Test57 used the offset as if it were a place
  in the world. So the wheel sat at the map's centre point, about 540 m from
  your Warthog on Blood Gulch, and you never saw it. It now uses the
  wheel's real position in the Warthog, on every map, wherever the Warthog
  is, whichever way it faces or tilts. It moves with the Warthog as you
  drive.
- **Scorpion (and Banshee):** the stick (and the Banshee's bar) sat between
  the driver's own hands, which are inside the hull. Both now sit in front of
  your chest, measured from your eyes when you get in. The drive stick is the
  same on every tank.
- **Safety net for every vehicle:** if a control would ever end up more than
  a metre from your eyes, or a vehicle has no hand markers, it's put in front
  of your chest instead, and the log says so.
- A new automated test puts every vehicle at five different places on and
  off the map, facing different ways and tilted, and checks the controls are
  under your hands, take a squeeze and move with the vehicle. With the old
  mistake put back, the test fails with the wheel 566 m away.

### The reticle with immersive vehicles

With the immersive controls in your hands, your head aims the guns. The
reticle followed the gun, which only moves 30 times a second, while your head
moves 72 times a second, so it stepped. It now turns with your head between
the game's updates and sits on the vehicle as you see it, like the hand
reticle on foot has since Test20e.

### Tank view

You like the tank's view as it is, so it hasn't changed. **TANK HATCH** (VR
Settings → VEHICLES, off by default) is an option that raises your eyes over
the tank's hull, as if you were standing in an open hatch.

These changes are checked on a PC (automated checks and builds), not yet in
the headset. Please test with **CONTACT LOG** on and keep the log from
Download/HaloCE: [Test58 device checks](TEST58-DEVICE-CHECKLIST.md).

---

# Test57 private candidate: 1.0.24-test57

## Test57: final polish: every vehicle its own controls

This private test build follows Test56 and was shaped by your Test56 session
(the 19:56 log, the Blood Gulch drive and the assault rifle close-up) and your
messages. It installs over Test56, Test55, Test54, Test53 and v1.0.19 (same
package names and signing key, Android version code 69) and keeps your
settings, profiles, saves and imported game data. Ragdolls, grabbing, NPC
lifting, throwing, climbing, wall running, manual reload, holsters, voice
chat, multiplayer and co-op, OpenCE compatibility (network 26), aiming,
scopes, left-handed play and the launcher are unchanged.

### Vehicles: every vehicle its own controls

All of this applies only with **IMMERSIVE VEHICLE** on. Ordinary vehicle
controls are exactly as before, and nothing below is drawn or used with it
off.

- **Warthog: a virtual wheel.** Your log showed 50 seconds of Warthog driving
  in which the Warthog's own wheel never took your hand, while the Ghost's
  handlebar took it every time. The Warthog now has its own drawn steering
  wheel: a rubber rim, three spokes, a hub, and an olive mark at twelve
  o'clock that shows how far it's turned. It sits just in front of the
  Warthog's wheel. Grip anywhere on it, rim or spokes, with one hand or both.
  Either hand can let go and the other keeps steering. It reaches 4 cm
  further than before.
- **Prefer the Warthog's own wheel?** Set **VIRTUAL WHEEL** to HIDDEN (VR
  Settings → VEHICLES). The grab then sits exactly on the Warthog's own wheel,
  and HOG REACH, HOG LEFT, HOG HEIGHT and HOG SIZE line it up.
- **Scorpion: a drive stick.** One stick between your hands. Grip the knob
  and lean it the way you want to go. The tank's turret follows your head.
  A Wraith gets the same stick, on maps where a player can drive one.
- **Banshee: a flight bar.** Roll it, or slide it sideways (12 cm is a full
  turn), to turn. Push to dive and pull to climb.
- **Ghost:** the handlebar you liked, unchanged in reach and steering. It
  now also gets the two touches below.
- **Feel and look:** a soft tick when the steering crosses straight ahead,
  and the controls light up when a free hand is close enough to take them.
  Your fingers close around whatever you hold, and let go smoothly.
- **New VEHICLES rows (all on):** **CONTROL GLOW** (the highlight),
  **STEER HAPTICS** (the turning ticks, the centre tick and the full-lock
  buzz; the grab and let-go pulses stay) and **BANSH SLIDE** (turning the
  Banshee by sliding its bar).
- If a squeeze doesn't take the controls, the log now says how far away your
  hand was (`immersive ... not taken by hand`).

Getting in and out resets everything: each vehicle starts with its own
controls centred, and no grip carries over from one vehicle to another.

### The assault rifle's safety button

The small round part with a red ring on the side of the assault rifle is the
gun's **safety button** ("frame safety button" in the model). It was checked
against the stock animations on your disc. In the idle, walking and firing
animations it sits exactly where you see it. The draw animation pushes it in
and lets it pop out to that spot. In the flat game the camera never shows that
side of the gun. Nothing is wrong, so it was left as it is.

### Checked and left alone

- **Ragdolls:** they already carry the shot and the throw into the fall.
  Anything stronger would risk the settling that now works, so they're
  unchanged.
- **Holster and pouch calibration:** the triggers, the blue markers, the
  sizes, the left/right mirroring and the saved settings all agree. No
  change.

These changes are checked on a PC (automated checks and builds), not yet in
the headset. Please test with **CONTACT LOG** on and keep the log from
Download/HaloCE: [Test57 device checks](TEST57-DEVICE-CHECKLIST.md).

---

# Test56 private candidate: 1.0.23-test56

## Test56: polish: ragdolls, immersive vehicles, throwing and lifting

This private test build follows Test55. It was shaped by your two Test55
sessions (the night fight against Elites, Grunts, Jackals and Hunters, and the
Blood Gulch Ghost and Warthog drive) and your messages. It installs over
Test55, Test54, Test53 and v1.0.19 (same package names and signing key,
Android version code 68) and keeps your settings, profiles, saves and imported
game data. Voice chat, multiplayer and co-op, OpenCE compatibility (network
26), wall running, manual reload, aiming, scopes, holsters, sprint, button
remapping, left-handed play and the launcher are unchanged.

### Ragdolls that come to rest, for every species

Your logs showed dead bodies still twitching 5 seconds after they fell
(`settle still pending`), and living NPCs lying for the full 5 seconds before
getting up. The cause: every joint's limits are authored relative to its
parent bone, but the ragdoll compared them against the world. On an Elite, the
spine is one rigid piece, so the chest was held upright while the rest of the
body fell, and the two fought forever.

The joints now work the way the game's own data describes them, relative to
their parent: rigid pieces stay rigid, hips, shoulders and necks swing in
cones, and knees and elbows bend one way only and never backwards. This was
tested offline on the real skeletons from your Xbox disc: Elites, Grunts,
Jackals, **Hunters**, Marines, crew, Keyes, and every **Flood** form (combat
Elite and human, carrier, infection form, Flood Keyes), each dropped five
ways. Every body now comes to rest, most within 1 to 2 seconds. The old
ragdoll never settled most of them.

### Deaths react to the shot

A killed NPC is now pushed by what killed it, from where it hit:

- light rounds snap a limb (assault rifle about 1 m/s at the hit), the pistol
  harder, the sniper rifle hardest (about 4 m/s);
- a leg shot buckles the leg, a side shot turns the body, a head shot snaps it
  back;
- melee shoves the body;
- grenades and explosions throw it away from the blast and up;
- shotgun pellets in one blast add up.

The game's own push from the hit is never doubled. Bodies next to a wall fall
into it, using the world's collision.

### NPCs get up within 1 second

A living NPC you let go of gets up as soon as it lies still, and never lies
limp longer than **NPC RECOVERY** (new, IMMERSION → ADVANCED; 0.25 to 1 s,
default 1 s). Dead bodies stay down and are never stood back up.

### Throwing and lifting

- **THROW** now defaults to **2X** (the row still goes from 0.75X to 2X).
- A throw takes your hand's speed at the peak of the swing, from your last
  few movements, so a flick carries and a hand already slowing at release
  doesn't weaken it. This applies to props, weapons and NPCs.
- Something you throw that hits a living body or a vehicle shoves it with
  part of its momentum before the damage, so a kill flies on as a ragdoll.
  A Hunter barely moves.
- **NPC HOLD is now LIFT.** It's the same setting (your choice is kept), and it
  now also sets how firmly props, turrets and vehicles follow your hands. The
  default (SPARTAN) holds props exactly as before; IRON lifts heavy things
  readily.
- **Elites and Hunters:** one hand grabs and holds them back while you hold
  Grip, but can't lift them. The second hand lifts, carries and throws. You
  feel the weight arrive in the hand left holding, and both hands buzz when the
  second hand takes it up. Grunts, Jackals and Marines stay one-hand
  liftable and throwable.

### Vehicles: IMMERSIVE VEHICLE

All of this applies only with **IMMERSIVE VEHICLE** on. Ordinary vehicle
controls are exactly as before.

- **Steering goes the right way.** Every control steered backwards: moving
  your hands left turned the Ghost right. Right is right now, for the Warthog,
  Ghost, Scorpion and Banshee.
- **Ghost:** the handlebar steers by turning and tilting. **Scorpion:** the
  sticks steer like a tank's. **Banshee:** roll the yoke to turn; push to
  dive, pull to climb. There's a small dead zone (1.5°), a full lock at 60°,
  and the controls re-centre when you let go.
- **Warthog wheel:** reach for its own wheel and grip anywhere on the rim. The
  rim now comes from the wheel in the model, slightly higher and tilted, with
  a little more reach. Your hands stay on it as it turns. Either hand can let
  go and the other keeps steering.
- **Feel:** a buzz when you grab, ticks as you turn, a stronger buzz at full
  lock, and one when you let go.
- **No more stutter.** The controls were placed where the vehicle is in the
  game's newest tick, while the vehicle is drawn one tick behind (smoothed),
  so the hands slid on the wheel and the steering jumped every frame. They now
  sit on the vehicle as it's drawn.
- **Steering apart from aiming.** Your hands steer and your head aims, so the
  Ghost's and Banshee's guns and the Scorpion's turret follow where you look.
  As an online co-op client, the Test55 behaviour is kept.
- **Hands grip.** Your fingers close round the controls over about a tenth of
  a second, even without finger tracking, and open again when you let go.

### Manual reload: CHARGE GRAB

**CHARGE GRAB** (new, IMMERSION → RELOAD; 2 to 10 cm, default 4 cm, as in
Test55) sets how far past your hand the slide or charging handle is still
caught, for every weapon. POUCH SIZE moved to the POUCH PLACES screen to make
room.

### Smaller fixes

- The "heavy hold one hand" log line appeared about 100 times a session. It's
  now written only when you actually let go.
- A middle-finger gesture was considered and dropped. Quest Touch controllers
  have no middle-finger sensor (the grip covers middle, ring and little
  fingers). The only signal, trigger pressed with grip released, is your
  ordinary resting or clicking hand, menu clicks included, so it would fire by
  accident.

### OpenCE Builds 189 and 190

OpenCE Build 189 adds sharing of Custom Edition maps between players, and
moves OpenCE to network 27. It's not included, so this build stays on network
26 and works with the same servers and players as before. From Build 190 this
build takes the lobby fix: a player joining or leaving the lobby no longer
restarts the countdown (they join the game in progress instead). It changes
only what your host does, not what it sends.

### If the Ghost's hood blocks your view

In first person, the Ghost's hood can fill the view, because the Ghost's seat
is built for a third-person camera. VR Settings → VEHICLES → **GHOST UP** and
**GHOST FWD** move your seat in the Ghost. Tell us what values suit you.

These changes are checked on a PC (automated checks, an offline ragdoll
simulation on your disc's skeletons, and builds), not yet in the headset.
Please test with **CONTACT LOG** on and keep the log from Download/HaloCE:
[Test56 device checks](TEST56-DEVICE-CHECKLIST.md).

---

# Test55 private candidate: 1.0.22-test55

## Test55: polish: grabbing everything, vehicles, calibration and one immersion menu

This private test build follows Test54 and was shaped by your Test54 play
session, the Blood Gulch vehicle test, and your messages. It installs over
Test54, Test53 and v1.0.19 (same package names and signing key, Android version
code 67) and keeps your settings, profiles, saves and imported game data. Voice
chat, multiplayer and co-op, OpenCE compatibility, aiming, scopes, holsters,
sprint, button remapping, left-handed play and the launcher are unchanged.

### Why so many things could not be grabbed

The stock campaign gives most placed objects a script name, and the grab code
refused anything with one. Reading your own USA Xbox disc showed how much that
excluded. 59 of the 61 Shade turrets carry a name, as do nearly all Ghosts,
Warthogs, Banshees, Wraiths and Scorpions, most placed bodies (88 of 95 on
343 Guilty Spark) and, on Assault on the Control Room, 201 of 203 pieces of
equipment and 43 of 45 weapons. Named things can now be grabbed and lifted:
**Shades**, vehicles, bodies, weapons, equipment and scenery. Things a
cutscene is controlling still can't. **LIFT VEHICLES** now also takes the
Banshee. Pelicans and dropships stay as they are, because they're scripted
transports.

### NPCs

- Elites, Marines and anyone mid-shot, mid-reload, diving or meleeing can be
  grabbed. Before, about two in three NPCs nearby were refused for being
  "busy".
- One hand on an Elite or Hunter holds it back and drags it (no lifting), and
  you feel its weight. Two hands lift it. Letting go with one hand keeps it
  in the other.
- Throws have Spartan strength. Light NPCs fly farthest, heavy ones less, up
  to about 24 m/s. A thrown body hitting something hard is hurt by the impact,
  as is what it hits, scaled by speed. Thrown bodies stay where they land.

### Ragdolls

Bodies are less stiff and puppet-like, because heads, hands and feet now
rotate with their limbs. They grip the floor instead of sliding. A killed NPC
is pushed from where the shot hit it.

### Manual reload

- A magazine from a pouch sits in your hand the way it sits in the gun, centred
  in your palm, with your fingers closed around it.
- Inserting is more forgiving: about 3 cm and a wider angle. Grabbing the old
  magazine is 1.5 cm more forgiving too.
- The slide and charging handle lock on from 4 cm further away. A squeeze up to
  a third of a second before your hand arrives still catches it.

### Calibrating pouches and holsters

IMMERSION → **POUCH PLACES** and **HOLSTER PLACES** move the magazine pouches
and the holsters: out from your body, up and back, in 1 cm steps. While those
rows are on screen, a translucent blue ball shows each real zone, exactly
where and how big it triggers. It hides when you leave the rows. Left-handed,
the pouches mirror to your other side. **POUCH SIZE** sets how big the pouches
are.

### Wall running

Wall running is more automatic:

- it finds walls you meet at an angle, and holds you lightly to the wall;
- it carries you along at least 4 m/s (times WALL SPEED, up to 9 m/s), even if
  you ease off the stick;
- it keeps you level for most of WALL TIME before you start to fall;
- you can chain wall to wall: after a wall jump, a new wall within two seconds
  starts a new run.

The wall jump still goes where you look.

### Vehicles: IMMERSIVE VEHICLE

The **IMMERSIVE VEHICLE** toggle (formerly PHYSICAL HANDLES) gives you first-person
driving controls:

- **Warthog:** grab its own steering wheel anywhere on the rim. No extra wheel
  is drawn.
- **Ghost:** a handlebar with grips.
- **Scorpion:** two control sticks.
- **Banshee:** a yoke. Push it to dive, pull it to climb.
- While it's on, the controls own the steering (the controller's aim no longer
  fights them), and they return to centre when you let go.
- Your own first-person hands, with finger poses, hold them.

### Zoom with physical melee

Making a fist with your off hand used to zoom, because a fist pulls the index
trigger. With physical melee in use, zoom moves to the **right stick** click,
which used to be melee. The arms do the meleeing now. This only happens if
nothing else is mapped to that click, and you're on foot. Otherwise the trigger
still zooms.

### One IMMERSION menu

IMMERSION and IMMERSION+ are one category now. Its screens are topics, and the
NEXT button names the next one: WEAPONS, RELOAD, POUCH PLACES, HOLSTER PLACES,
MOVEMENT, BODY, GRAB + NPCS, ADVANCED. Turning a feature on still turns on what
it needs, and never anything optional.

### Performance in big fights (OpenCE Build 188)

Your Test54 log shows draws per frame climbing from about 600 to over 3,000
during a long fight (the frame rate fell from 72 to 45), and dropping back
after a revert. That's bullet holes and blood decals building up, each drawn
separately in both eyes. OpenCE Build 188 draws them in batches, and that
change is included here. OpenCE Builds 185 to 188 made no network change, so
Build 188 servers are joined as before.

These changes are checked on a PC (automated checks and builds), not yet in the
headset. Please test with **CONTACT LOG** on and keep the log from
Download/HaloCE: [Test55 device checks](TEST55-DEVICE-CHECKLIST.md).

---

# Test54 private candidate: 1.0.21-test54

## Test54: manual reload, grabbing, climbing and ragdolls refined

This private test build follows Test53 (which made these systems run for the
first time). It installs over Test53 and v1.0.19 (same package names and
signing key, Android version code 66) and keeps your settings, profiles, saves
and imported game data. It was shaped by your 2026-10-11 logs and videos.
Voice chat, wall run, wall jump, the climb leap, multiplayer and co-op, aiming,
holsters, sprint, left-handed play and the launcher are untouched; voice was
working in your online log and its code was not changed.

### Manual reload, start to finish

- **B (Use / Reload) drops the magazine.** With MANUAL RELOAD on, the reload
  button ejects the magazine wherever your free hand is. It never starts the
  automatic reload, and pressing it again mid-reload does nothing (it used to
  cancel). With MANUAL RELOAD off, B reloads as always. A gun with no spare
  ammo keeps its magazine (you feel a short click).
- **Fresh magazines on your body.** Reach your free hand to your **hip** or
  **over your shoulder** on the free hand's side (left for a right-handed
  player, mirrored when left-handed) and squeeze. You feel a tick when your
  hand is over a pouch. The pouches are large and follow your body, so you can
  find them without looking. **MAG POUCH SIDE** (AUTO, LEFT, RIGHT, BOTH)
  moves them. The HIP and SHOULDER pouch switches are on IMMERSION+.
- **Push it home.** Hold the magazine against the magazine well, roughly
  lined up: it locks in while you still hold it (or when you let go there).
- **Charge only when needed.** If the gun was empty, work the slide or
  charging handle (pistol slide, assault-rifle handle, sniper bolt, shotgun
  pump). After a **tactical reload** with a round still chambered, the gun is
  ready as soon as the magazine locks.
- **Feel each step:** grabbing, the magazine pulling free, the eject, the
  pouch, touching the well, the lock, the slide reaching the end, and the gun
  coming ready each have their own buzz (VR HAPTICS scales them).

### Grabbing Marines, Grunts, Jackals, Elites and bodies

Your log showed every NPC miss with no collision contact. The palm had to
overlap the small hit-detection model at only 4 cm. Grabs now also count your
hand touching any part of the body (the limbs and torso of its current pose),
so a hand on a Marine's back, a Grunt's arm or a body lying on the floor
grabs it. **GRAB ASSIST** adds reach (TOUCH by default: you must touch
them). **NPC HOLD** (LIGHT, NORMAL, SPARTAN default, IRON) sets how firmly a
held NPC follows your hand. A Grunt stays in one hand, while Elites and
Hunters still need two hands and drag behind.

### Throwing, ragdolls and bodies that stay

- Throws use your hand's last motion (a flick carries), multiplied by the **THROW** setting.
- **Thrown bodies no longer vanish.** The engine's "root" of a thrown body
  stayed where you let go while the body flew on, so the game culled or
  rebuilt it there. The root now follows the body, which lands and stays where
  it lands and can be picked up again.
- Bodies are heavier at the torso than at the hands and feet, and they come
  to rest instead of jittering on the ground.
- **DEATH RAGDOLLS** (new, on IMMERSION): enemies and allies killed near you
  fall as physical ragdolls carrying the hit's momentum, then rest as bodies
  you can pick up. It uses the NPC RIG SLOTS pool; with no free slot, the
  usual death animation plays.

### Climbing

Grip climbing now holds onto rock faces and slopes steeper than about 40
degrees, overhangs, and the top of a ledge at or above your waist. It no
longer needs a perfectly vertical wall, and the floor at your feet is never a
hold. A hand pushed *into* a wall grips the wall's surface (tracked hands pass
through walls, which made most attempts miss). **CLIMB GRAB** (default 10 cm)
sets how close the hand must be. A squeeze just before your hand arrives still
catches. Wall runs ease out of the wall's hold through the run, so they arc
into a fall instead of dropping suddenly. Wall run, wall jump direction and the
climb leap are otherwise unchanged.

### Melee and grabbing don't mix

An open hand is for grabbing, and a fist or a hand holding a gun is for
striking. With any grab or climb feature on, a fast open-hand reach makes no
melee blow or sound. Turning on a grab or climb feature also turns on **FIST
REQUIRED** (you can turn it off again). It goes back off when no grab or climb
feature needs it, unless you set it yourself.

### Hands and guns

- The visible hand stays with your controller. A held prop, climbing hold or
  magazine draws it at most 6 cm, so the arm no longer stretches.
- Fingers ease into and out of contact with walls instead of snapping or
  contorting.
- The assault rifle's operating handle (and any other gun part) no longer
  slides in and out while you walk or turn: the walking and sway animations
  keep moving the arms but no longer move parts of the gun in your hand.

### VR Settings: IMMERSION and IMMERSION+

**IMMERSION** now holds the features and the tuning that changes how they
feel. New rows: MAG POUCH SIDE, CLIMB GRAB, GRAB ASSIST, NPC HOLD, THROW,
DEATH RAGDOLLS, plus HAPTICS, SPRINT SPEED and ARM EFFORT.
**IMMERSION+** holds the technical options: pouch switches, hand-contact size,
holster haptics, custom scenery and NPC rigs, rig slots, NPC rescue, impact
limits, shake cooling, close contact and physical handles. Every row is also
still on its usual page.

Turning a feature on turns on what it needs. MAG DEBRIS turns on MANUAL
RELOAD, CUSTOM SCENERY turns on WORLD GRAB, CUSTOM NPC RIGS turns on NPC GRAB,
and grabbing or climbing turns on FIST REQUIRED. What was turned on only for a
feature is counted and goes back off with the last feature that needed it.

### Online

Nothing here changes the network protocol. Death ragdolls and grabs follow the
existing co-op path: a compatible co-op host simulates them and sends body
poses to compatible clients (up to four). Stock OpenCE servers and Android
players see the normal game. Manual reload and parkour stay off as a co-op
client and in PvP, where the host's movement and ammo checks would undo them.
That is listed as remaining work in TEST54-NETWORK.md.

These changes are checked on a PC (automated checks and builds), not yet in
the headset. Please test with **CONTACT LOG** on and keep the log from
Download/HaloCE: [Test54 device checks](TEST54-DEVICE-CHECKLIST.md).

---

# Test53 private candidate: 1.0.20-test53

## Test53: voice crash fixed and immersion features repaired

This private test build follows public v1.0.19. It is for the owner's Quest
and phone testing; it is not a release. It installs over v1.0.19 (same
package names and signing key, Android version code 65) and keeps your
settings, profiles, saves and imported game data.

### Voice chat: the crash when you speak

v1.0.19 closed as soon as you spoke in a voice-enabled game. The cause was
in the build, not the voice code: the step that converts the Quest guest's
assembly for Android deleted one byte from an Opus voice-codec table, so the
encoder read past the end of a table once real speech arrived. The build no
longer alters data, a check compares the built tables with the Opus source
after every build, and the encoder now also cleans its microphone input and
keeps its bitrate between 8 and 64 kbps. Calls the build could compile wrongly
on the Quest (undeclared or mismatched functions) are now refused at build
time. Please retest: talk in a lobby and in a match, and check that others hear
you and you hear them.

### Network: current OpenCE servers (network 26)

OpenCE moved to network 26 (Build184). This build hosts on network 26 and
joins hosts on networks 11 to 26, so current OpenCE servers appear and can be
joined again, and current OpenCE players can join your games. **All
compatible networks** is now the launcher's default target (the most
servers); a specific network you chose before is kept. OpenCE's new browser
players cannot join this app's hosts (that needs WebRTC, which this app does
not have). Selected Build184 fixes are included: co-op elevators no longer drop
riders, a co-op crash on stale player handles, vehicle respawns, Custom
Edition HUD digits, and a race that could delete Custom Edition maps while
the menus started.

### VR Settings: IMMERSION

A new **IMMERSION** page (first in VR Settings) gathers every immersion
option in one place: physical weapons, holsters and melee, manual reload and
pouches, wall-run / wall-jump / grip climb and their tuning, world, NPC and
vehicle grabbing, NPC rig slots, body retention, NPC rescue, impact damage,
close contact, physical vehicle handles, fingers and room-scale. Each is the
same setting as on its usual page; change it in either place.

### Why grabbing, climbing and manual reload did not work

- **Grabbing NPCs, objects and vehicles (and co-op grabs):** the touch test
  asked the engine whether a *moving* hand sphere would hit a model, with no
  movement, and the engine answers "no" for that. Your logs show hundreds of
  misses at the largest contact size. Grabs now test whether the hand
  actually touches (or is inside) the model.
- **Parkour (wall-run, wall-jump/leap, grip climb / wall grabs) and manual
  reload:** both asked for the head's position from the game's simulation
  step, which the VR code only answered while drawing a frame. Every
  simulation step was refused, so parkour reset itself constantly and manual
  reload cancelled before it read your hands. Both now run.
- **Released NPCs** could stay limp with their AI switched off for a long
  time. They now get up (or a body settles) within five seconds.
- **Body retention:** campaign scripts clear bodies at many encounters,
  which ignored the setting. In single player with retention on, those
  clean-ups now keep the newest bodies (45 at "75", 60 at "100").

Parkour works in single player and for a **co-op host's own player**. It stays
off as a co-op client and in PvP: hosts check client movement and would pull a
wall-running or climbing player back (and it would be an unfair advantage).
A wall run may start on a wall you reach within a second of jumping.

These fixes are confirmed by automated checks on a PC, not yet in the
headset. Please test each option with **CONTACT LOG** on and keep the log
from Download/HaloCE: [Test53 device checks](TEST53-DEVICE-CHECKLIST.md).

---

# Test52 (committed, not delivered): 1.0.20-test52

## Test52: voice crash root cause fixed

Test51 / v1.0.19 still closed on Quest as soon as you spoke in a voice-enabled
game. The supplied logs show the crash right after the first microphone frame
was encoded, inside the Opus voice codec (`encode_pulses`). The cause was in the
build pipeline, not the voice code: the step that converts the Quest guest's
assembly from Apple to Android format was rewriting text and byte-table data.
It deleted one byte of the **Opus pulse-cache table**, so the encoder read past a
table and crashed when real speech arrived. The converter now passes all data
through untouched; a new check compares the built tables with the Opus source.
The same conversion bug had also altered a few other strings and tables (the
loading tone, a sound-effects image, settings-file number parsing and text
classification); they are corrected too.

A second, related bug class is fixed as well: **missing function prototypes**.
On the Quest/Android guest ABI, a call to an undeclared function passes
variadic and decimal arguments in the wrong place. That is why Test50/Test51
voice logs showed nonsense numbers (and why Test50 crashed in a log line). It
also gave the NPC grab/recovery clearance test a garbage radius, drew the
scoreboard at the wrong scale, and could misread multiplayer vehicle-placement
results. Every guest file now declares what it calls, and the build fails if a
future change forgets.

This candidate is built with the same compiler setup as public v1.0.18. Gameplay,
network protocol (network 24), voice protocol and settings are otherwise
unchanged from v1.0.19. Voice still needs a voice-enabled host and a nonzero
receive volume; please retest talking in a lobby and in a match, on more than
one server if possible. See [Test52 crash analysis](TEST52-CRASH-ANALYSIS.md)
and [Test52 device checks](TEST52-DEVICE-CHECKLIST.md).

---

---

# Test51 private candidate: 1.0.32-test51

## Test51: network-join crash and voice-config fix

The two supplied Quest crash logs show successful admission and map loading,
followed by a fault in Test50's host voice-settings diagnostic. Test51 changes
all voice diagnostics to integer-only formatting and records the host settings
before logging. **Host voice settings accepted before diagnostics.** The voice
protocol, host routing, microphone behavior and existing in-game voice controls
remain unchanged. No Android launcher voice options were added.

Voice still requires the host to enable lobby/in-game routing, a compatible
Build167 voice relay on the host and peers, a nonzero listener receive volume,
and a speaking player. If logs report no host settings, confirm host setup and
version first. The fix is source/test verified; Quest join and two-client voice
still need a device check. See [Test51 crash analysis](TEST51-CRASH-ANALYSIS.md)
and [Test51 device checks](TEST51-DEVICE-CHECKLIST.md).

---

## Test50 carried-forward features

## Test50: voice diagnostics and sprint toggle

- **Mounted reticle alignment:** driver and gunner shots (including tanks,
  Ghosts and mounted turrets) now follow the selected reticle/muzzle ray. The
  Test49 log showed native camera aim assist turning shots 2.28°/2.61° away
  from the reticle. Test50 bypasses that correction only for the local VR
  driver/gunner, avoiding target snapping. On-foot, passenger, remote-player
  and flat Android aim assist stay unchanged. Random spread can still move
  individual rounds around the center ray.

- **Sprint:** in VR Settings → Locomotion, turn **Button Sprint** on. **Sprint Toggle** defaults to **Hold**; choose **Toggle** to click left stick once to start and again to stop. Hold remains unchanged unless Toggle is selected. Recenter, losing focus, seating, or losing the VR input state cancels the toggle. Sprint remains local/offline movement only and respects existing movement limits.
- **Voice:** behavior and privacy defaults are unchanged. Test50 logs host voice settings, local mic mode and receive volume, encoded frames handed to the network path, host-accepted/relayed frames, and successful incoming Opus decoding. It never records/logs audio or player names. A host that sends no Build167 settings is called out after five seconds. Voice still requires a compatible, voice-enabled host and peers, host routing that includes the listener, nonzero receive volume, and a speaking player.
- **Evidence boundary:** the supplied Test49 log shows Wi-Fi, a 48 kHz stereo output device without reported underruns, and microphone open/close without permission/device errors. It does not establish that anyone spoke or that remote audio was received. See [Test50 voice diagnostics](TEST50-VOICE-DIAGNOSTICS.md).
- **Upstream:** the latest official release checked on 2026-10-10 is OpenCE Build177; the exact-match reticle art was already integrated. Engine base remains Build157/network24 with selected compatible changes through Build177, not a full Build177 rebase.

Device checks: [TEST50-DEVICE-CHECKLIST.md](TEST50-DEVICE-CHECKLIST.md).

---
# Test49 private candidate: 1.0.30-test49

This candidate carries forward Test48, Test47, and the cumulative
player-facing features below. It retains the signed weapon-datum fix and
restores surface-contact haptics to the v1.0.18 collision and animation
ownership gates. Weapon recoil values and routing match v1.0.18. It also logs
whether melee and weapon-switch actions were emitted separately. The APKs are
for owner testing; they are not a public release.

## Test49 corrections and Test48/Test47 changes to retest

- **Controller haptics:** palm pressure buzzes only when the tracked hand's
  actual surface collision is pressing in and VR IK owns that arm, matching
  v1.0.18. Finger contact feedback uses that same arm-ownership gate. The
  extra head-to-hand collision probe no longer renews vibration every render
  update. Weapon recoil amplitudes/durations and two-hand routing are unchanged
  from v1.0.18. The OpenXR log confirms action availability and runtime
  acceptance, but only headset testing can verify motor feel.
- **Weapon switch / melee:** the supplied log records holster weapon switches
  and resulting weapon changes, but does not record a melee action. The
  gameplay action bits and default inputs remain separate; this candidate
  reports the emitted melee/switch mask and physical swing events for any
  retest. No input binding was changed.

- **Grip release / holsters (confirmed regression fix):** OpenCE weapon datum handles are signed values; valid live handles can be negative. Only `-1` means no weapon. Test47's release latch, holster storage/pruning, and pending-release recovery incorrectly rejected every negative handle. Test48 checks the actual empty sentinel, so releasing a gripped weapon drops it, releasing inside a holster stores it, and re-gripping an occupied holster can request that exact weapon. Retest with both weapons shown in the supplied log (`-431815724` and `-431750187`).
- The matching regression tests exercise negative live unit/weapon handles through the release, hand-state recovery, holster store/draw/prune paths, and preserve cancellation when grip is re-pressed, tracking/focus is lost, recenter occurs, or an interaction owns the hand.
- **Signed weapon datum fix:** negative live weapon IDs are valid; only `-1` is the empty sentinel. Grip release, dropping, holster storage/pruning, and exact holster draw use that sentinel correctly. Test49 retains the Test48 fix.

- **Hands/arms:** the arm model now keeps the original upper-arm and forearm
  lengths. The wrist target is clamped to what the shoulder and authored bone
  lengths can reach, with a small shoulder adjustment; the solver no longer
  lengthens or compresses the arm to force the controller pose. Test normal
  reach, crossing arms, looking down at the torso, turning the body, and
  tracking/recentering transitions.
- **Manual reload:** enable **MANUAL RELOAD** in VR Controls. Use the configured
  free-hand **RELOAD INPUT** (Grip by default; Trigger is optional) only after
  the palm touches the authored magazine/handle or the enabled hip/shoulder
  pickup point. Pull the magazine clear, release, take a replacement from the
  body pouch, align it with the socket, and release it to seat. Finish with the
  authored handle/pump/latch. The configured **USE / RELOAD** action ejects a
  magazine only while the free palm contacts it; it cancels an active reload.
  Quest B is the default USE / RELOAD button. Right-stick click remains melee.
  Unsupported profiles keep native reload; physical reload remains solo-only.
- The reload log now reports changes in the mapped action, native reload bit,
  free-hand Grip/Trigger, contact with the authored magazine/pouch/chamber, and
  interaction ownership. A missing contact or conflicting owner should now be
  diagnosable from a single session log.
- **New Game > multiplayer map:** a local solo map load should spawn at a
  multiplayer scenario start inside the BSP with the multiplayer biped, instead
  of reusing a campaign continuation unit. Network matches and campaign starts
  are unchanged.
- **BODY RETENTION** (saved as `vr.ragdoll_retention`): solo campaign defaults to a higher active-garbage
  cleanup threshold (75 trigger / 45 target, scaled per 16 players). Choose
  **STOCK** for OpenCE's 50 / 30 thresholds or **100** for 100 / 60. Corpses
  share this pool with other garbage, so this retains eligible offscreen bodies
  longer but is not a fixed corpse-count guarantee. Memory/object pressure may
  still collect sooner. Network and local multiplayer always use stock values.

## Changes in Test46: contact latching and allied NPCs

- **NPC GRAB** now accepts supported friendly Marines and crew as well as the
  existing enemy species and corpses. Acquisitions still require the tracked
  palm collision volume to overlap the NPC's authored collision model, followed
  by a fresh Grip press. Pointing at an NPC or holding Grip before contact does
  not acquire it. Friendly ordinary AI orders are preserved while the mod
  temporarily suppresses movement/trigger controls during the hold; forced
  immediate orders remain excluded.
- While Grip remains held, ordinary hand movement and target-to-joint distance
  no longer drop an NPC or prop. The held target follows a bounded per-step
  hand position. Large tracking discontinuities clear throw velocity and rebase
  the target instead of releasing it. Invalid tracking, lost ownership, stale
  entities, unsafe target states and explicit Grip release remain logged
  cancellation/release conditions.
- Host-authoritative co-op prop holds now rate-limit large remote target steps
  while retaining contact ownership. The host still independently checks palm
  overlap with the object's authored collision model and validates line of
  sight after contact.
- Interaction logs now distinguish a contact acquisition, a started hold
  constraint, a tracking rebase, solver strain and a release/cancellation
  reason. Logs help diagnose a session but do not prove a controller action
  succeeded.

Private Quest VR and Android test build. Public v1.0.18 remains the accepted
release; Test46 has not been published or device-tested. It carries forward all
project changes made after v1.0.18 through Test45, plus the A10 calibration,
Build167 voice, retained-magazine, vehicle-lift and rescue-eligibility updates
documented below. PC/Steam Frame remains deferred.

## Changes in Test46

- The first-run screen, main launcher and **Game files & versions** manager now
  explain that picker-selected ISO/XISO files import supported maps
  only. The original image remains in its original location; the launcher does
  not keep or delete it. Use Android Files to remove that original file. Only a
  copy placed in `game-versions/inbox` can be deleted from the launcher.
- The first-run import is installed as the protected **Existing game data**
  base set. The manager explains that its disabled **Currently selected** row
  is expected when it is the only set; use **Import ISO / XISO** or **Scan
  inbox** to add separately selectable managed sets. The base row cannot be
  deleted or replaced from the manager.
- In Halo CE's opening A10 look-calibration sequence, the directional checks
  and scripted look-at checks follow the current hand-aim reticle ray when the
  rendered ray is fresh and valid. Outside A10 and in head-aim mode, the
  existing head-based behavior remains. In hand-aim mode, invalid/stale ray
  data pauses calibration progress until a valid rendered ray is available.
- No other mission's script visibility, AI behavior, weapon aim, reticle render,
  saves, networking, Android touch input, or Safe Geometry behavior is changed.

This is source/test verified only. Calibration still requires Quest testing to
confirm the in-game tutorial's authored timing and target sequence.

## Game-data selection and storage

- The main launcher shows the selected game-data label and number of installed
  distinct sets. Tap it to open **Game files & versions** and choose the set
  used on the next launch.
- The full manager marks the active set, shows detected cache build and map
  fingerprint, and allows each imported set to be selected or renamed.
- **Delete imported copy** removes an inactive managed set, including its maps,
  configuration and local saves. Switch to another complete set first. Existing
  game data cannot be deleted through this control.
- ISO/XISO files placed inside the import inbox can be deleted there after
  import. An ISO/XISO selected directly through Android's file picker is not
  retained; the source ISO/XISO stays where you selected it. Source folders
  also remain untouched.
- Byte-identical managed map sets deduplicate to one profile; Existing game data
  is a separate protected base row. The verified USA Original,
  Rev 1 and Rev 2 XISOs contain identical bytes for their 24 maps, so importing
  them does not create three distinct selectable map sets. Other images remain
  separately selectable when their imported maps differ. Filenames do not
  verify a disc revision.

Selection uses the existing atomic `active-data.txt` marker consumed by native
and Java startup. Switching applies to the next launch. See
`GAME-DATA-LIBRARY.md` and `USA-IMAGE-COMPARISON.md` for evidence and limits.

## Retained features since v1.0.18

- **Manual reload and weapon handling:** optional physical magazine removal and
  insertion, charging where profiled, two-hand handling and cancellation use
  the native ammo/state path. Reload remains solo-only. Supported weapon
  profiles determine which actions are available. Shoulder/hip magazine pouches
  follow the gun hand; the free hand performs the reload. Diagnostic contact
  bounds are logged once per weapon/model profile.
- **Weapon scopes and mounted aiming:** per-weapon scope adjustment and
  diagnostics; configurable right/left/head/stick vehicle and turret aiming;
  vehicle view/recenter settings and scoped reticles remain available.
- **Physical world interactions:** optional hand/object contact, consent-gated
  interaction sync and NPC handling. NPC graph fallback is limited to
  recognized or validated layouts. Manual reload and parkour remain solo-only;
  networked physics requires compatible peers and host permission.
- **SHAKE COOLING:** the optional gesture cools supported overheating weapons
  in solo play. It does not alter normal firing heat rules online.
- **CUSTOM SCENERY / CUSTOM NPC RIGS / MAG DEBRIS / LIFT VEHICLES / NPC RESCUE:**
  optional custom scenery/NPC graph paths, magazine debris, bounded vehicle
  lifting and mission-NPC recovery. Magazine debris is visual and local. Up to
  32 discarded magazines remain visible through same-map checkpoint/core
  restores during the running session; map change, disabling MAG DEBRIS, or
  entering an online session clears them. When full, new visuals are skipped.
  Vehicle lift uses contact plus Grip to move and rotate a supported unoccupied
  Warthog, Ghost, Scorpion or turret with one or two hands. Translation and
  orientation are speed-capped; release lets the native vehicle solver continue
  with gravity and collision. It is solo-only, does not teleport, and excludes
  occupied, destroyed, parented, named/movie-star, boat, aircraft and networked
  vehicles. Rescue applies only to eligible live actors
  in the documented fall/recovery state. Custom scenery uses validated
  collision bounds; it does not enable arbitrary BSP geometry or script-owned
  scenery.
- **HAND CONTACT:** sets the shared palm-collider radius (2, 4, 6, or 8 cm; 4 cm default), not a target-search reach. World objects and NPCs can be grabbed only when the tracked hand volume overlaps their collision model; the co-op host repeats the NPC/object collision check. Manual reload part bounds, virtual pouch points, and optional vehicle-wheel handles use touch-then-press. Magazine insertion is a separate held-object alignment step. To climb, touch a solid vertical surface with a free hand, then squeeze Grip. Aim direction cannot select these targets. **NPC RIG SLOTS** controls 1, 2, 4, 8, 12 or 16 mod interaction rigs (default 8). **BODY RETENTION** separately raises solo-only engine garbage thresholds to 75/45 by default or 100/60; STOCK restores 50/30. This changes the shared pool, not a fixed corpse count. Native tag eligibility remains; memory/object pressure may clean sooner, and multiplayer always uses stock thresholds.
  **HAPTICS** is the master controller-vibration control. **HOLSTER HAPTICS**
  only mutes holster entry/draw/stow buzzes and does not mute reload or other
  effects.
- **Diagnostics:** interaction logs state the local/network session and active
  interaction settings when changed; logs do not prove an action completed.
- **Android touch-layout presets:** in-game **HUD > OPTIONS** can export or
  import a versioned layout through Android's file picker. Presets include
  touch positions, sizes, visibility and touch/gyro options, not gamepad
  mappings or saved game data. Imports stay preview-only until **SAVE**; use
  **CANCEL** to discard. Select a control and turn off **Show and enable this
  touch control** to hide it from gameplay; hidden controls remain recoverable
  in the editor. Existing installs keep controls visible by default.
- **Refresh rate:** **Graphics > Display > Refresh > Auto** removes this app's
  fixed-rate preference and asks OpenXR to use the runtime's choice again.
  Choosing 72/80/90/120 Hz continues to request the highest supported rate at
  or below that value; the runtime can still decline a request.

## OpenCE Build167 voice chat (selected Test46 integration)

Test46 adds OpenCE's host-relayed Opus voice path using optional message IDs
80-82. The engine remains based on Build157/network24; this does not raise or
change the network protocol version. Voice-capable peers participate after
they advertise that they can hear voice; this is not a claim that older or
unmodified clients support voice.

- The microphone mode defaults to **Off** for privacy. Off stops transmitting
  but still allows incoming voice when **Voice Volume** is above zero. Set
  Voice Volume to **Muted** (0) to silence all incoming speakers; the available
  range is 0-200%.
- In VR, open **VR Settings > Voice Chat** to choose Off, Push to Talk or Open
  Mic and set incoming voice volume. Bind a Quest controller button under
  **VR Settings > Buttons > Push to Talk**. The binding defaults to **None** to
  avoid taking over a gameplay control. The keyboard binding remains available
  in VR too.
- On flat Android, the default keyboard PTT key is **V** and can be changed in
  **Controls Setup**. Flat Android has no dedicated hold-to-talk touch button
  or gamepad PTT binding; use a connected keyboard or Open Mic.
- Android declares the microphone permission. The SDL permission request is
  asynchronous and starts only when voice transmission is enabled and allowed
  by the host; capture opens later only if PTT/Open Mic is still active after
  permission is granted. Actual permission UI and headset microphone routing
  still need device testing.
- Hosts configure lobby voice, in-game routing, bitrate and proximity in
  **Server Setup > Teamplay Options**. Lobby speaker icons show who is speaking.
  Per-player mute controls are not exposed; set Voice Volume to zero to mute
  everyone.

Source checks verify configuration, controls, network wiring and Android audio
bridging. Quest permission prompts, capture/playback, lobby/match routing and
two-client voice have not been runtime-verified. See
[`TEST46-VOICE-CHAT.md`](TEST46-VOICE-CHAT.md) for setup and the device test
boundary.

## OpenCE, network and image compatibility

The engine base remains OpenCE Build157 / network24. This is a selective
integration through official Build177, **not** a full Build177 engine rebase;
network24 and the launcher's network selector stay unchanged. The candidate
includes the compatible Custom Edition tag guard, Android cleanup, large
co-op respawn selection, pagemap-denied ART-memory fallback and exact-match
reticle artwork. Build175's old-kernel fixed-map safeguard was already present
and is retained. Build174's high-resolution button rendering was reviewed but
not merged because its upstream renderer/asset patch conflicts with the
customized Android and VR menu paths. The exact scope and test limits are in
[the Build177 integration audit](TEST47-OPENCE177-INTEGRATION.md).

Build167 voice chat remains integrated as described above, without changing
network24. The launcher offers client targets 11-24 or All compatible, while
hosting stays on 24. Selected assets do not establish device-level voice,
server, map-revision or co-op compatibility; see the device checklist.

The supplied USA Original, Rev 1 and Rev 2 XISOs all import successfully and
their 24 map files are byte-identical. Original remains the recommended
conservative baseline; this does not mean the tested Rev 1/Rev 2 sets are known
to be incompatible. Other regions, repacks and modified images remain
unverified.

## Campaign co-op and enhanced interaction limits

Campaign player-count options remain those supplied by OpenCE. The 128-machine
transport table is not a claim that 128-player campaign spawning, AI, vehicles,
checkpoints or transitions are stable or device-tested. Enhanced world-object
interaction can negotiate above four remote peers when the host enables it and
all participating clients support it. Articulated NPC pose synchronization is
still limited to four remote peers; above that, NPC physical handling falls
back to native behavior. Manual reload and parkour remain solo-only. Native
campaign co-op and its usual capacity are unchanged by these optional systems.

## Important limits

NPC RIG SLOTS changes the mod's articulated interaction pool, not native
ragdoll eligibility. Test47's BODY RETENTION adjusts the shared active-
garbage cleanup threshold only in solo VR campaign. There is no exact corpse
count guarantee: eligible bodies run the tag-gated settling solver, and memory
or object pressure may reclaim off-screen garbage. NPC interaction slots allow 1,
2, 4, 8, 12 or 16 active mod rigs; new configurations remain at 8 to limit
Quest CPU work. Custom rig support is opt-in and solo-only for otherwise-
unprofiled grounded humanoid actor variants whose native biped capsule and
authored graph checks pass. It simulates the captured graph without assuming
stock head/pelvis markers; malformed,
flying, swarm and online custom-layout rigs remain unsupported. Dropped magazines are not serialized into save files, do not survive a
map change, create ammo, or replicate; the 32 visual props survive only same-map
state restores in the current process. Vehicle lifting supports bounded
hand-driven translation and rotation for the listed ground vehicle classes;
it does not teleport or add an extra throw impulse, and release retains only
the capped native velocity.
NPC rescue does not revive dead actors, override scripts or guarantee every
mission encounter. These interactions still need Quest testing. Automated
checks do not establish headset or live-server acceptance.

Install over the existing app without clearing data. Follow
`TEST46-DEVICE-CHECKLIST.md` before treating this candidate as accepted.
