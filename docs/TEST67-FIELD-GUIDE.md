# Test67: reload grips, fist flow and simpler campaign setup

Private 1.0.34-test67 / code79. Install the matching Quest VR or Android APK over
Test66; the package IDs and signing certificate are unchanged. Keep your saved
settings. No uninstall is needed. No public release is being changed.

## Weapon handling and empty hands

- Holstering both weapons hides the weapon reticle. Taking a weapon back out
  restores it, subject to your reticle toggle. Vehicle reticles still work;
  fist-combat target markers are separate.
- The AR uses a steady native magazine-holding pose rather than the later slap
  pose. Pistol magazines, shotgun shells and rocket tubes get verified native
  holding poses as well. The accepted Sniper magazine pose is unchanged.
- Extraction, insertion, charging travel, magazine storage, ammo accounting,
  cancellation, native reload fallback and existing haptic clicks stay intact.
  Flamethrower/Needler retain their working generic grip where their native
  animations do not contain a verified left-hand hold.
- Left-Hand Mode mirrors the same profiles. No new reload button binding.

## Sprint and assisted fists

- SPRINT SPEED now offers 1x through 3x, including 1.75x, 2.25x and 2.75x.
  Default remains 1.5x. Button Sprint and Arm Run share this speed setting.
  Existing hold/toggle sprint choices stay. Network safety gates stay.
- Fresh settings use COMBAT REACH 3 m / LUNGE REACH 8 m, matching the owner's
  useful starting point. Existing saved values are retained.
- A deliberate swing owns one assisted strike. Continuing the same fast arm
  motion cannot repeatedly lunge/damage; slow or release the fist to rearm.
  A fresh opposite-hand punch can select a different enemy by gaze/direction.
- ENEMY HEALTH remains a fist-damage divisor, not a global health increase.
  Easy/Normal/Heroic/Legendary add melee durability factors .85/1/1.25/1.5.
  Regular assisted punches cannot accidentally invoke the native instant rear
  melee kill. Deliberate takedowns and ordinary weapon melee retain their rules.
- Block: raise a hand between your face and the melee attacker. A short amber
  impact, lighter pulse and native impact sound mark reduced damage.
- Parry: swipe into the attack shortly before contact. A blue impact, stronger
  haptic response and different native impact sound mark the interruption and
  short counter/grab opportunity. Timing tightens with difficulty. No giant UI.
- Grunts remain easier to stagger; Jackal shields reward angles; shielded Elites
  withstand combinations and answer flurries; Hunters keep armor/heavy rules.
  Bullets and global NPC health are unchanged. Native reactions, bounded living
  knockdowns and Jolt death ragdolls remain distinct.

## New combat options and gestures

**VR SETTINGS > IMMERSION > FIST COMBAT** contains **COMBAT MOVES**. It works
inside the existing optional FIST COMBAT mode. Enabling FIST COMBAT also enables
COMBAT MOVES and DEFLECT SHOTS; each can be switched off separately afterward.
If fist combat was already saved on, switch it off/on once to enable the new
companions, or choose DEFLECT SHOTS directly. Your saved settings are not reset.

| Action / cue | What to do |
| --- | --- |
| Cyan downward arrow below a cap | Duck your actual head about 20 cm after the sweep starts. Button crouch alone does not satisfy this physical dodge. |
| Cyan sideways arrows | Physically sidestep about 22 cm from the incoming overhead/jab line during the windup. Native collision still applies. |
| Cyan incoming chevrons | Counter by punching toward that attacker, or time an active hand/weapon parry. Several enemies can warn at once. |
| Gold bent-arm mark | An earned arm-control opening: hold the actual arm and strike near the held contact with the free fist. Releasing gives at most one second of follow-up opportunity. |
| Gold descending strike bars | Jump naturally and land a real downward punch to earn a brief pummel opening; continue deliberate downward punches. There is no forced mount, camera attachment or teleport. |
| Cyan impact rays | A successful active parry/deflection, with a strong short pulse and native Halo impact sound. Amber rays indicate a reduced-damage block. |

The original animations are procedural additions over Halo's own attack clips:
sweeps, overheads, jabs, recoil and supported arm-clutch/kneeling reactions.
Native hit-frame geometry, body collision and existing ragdoll/grab ownership
remain authoritative. These are experimental combat refinements, not copied
Batman animation assets. A held gun can actively parry an incoming melee attack;
merely aiming it does not create a passive shield. Reloading, climbing, carrying
an NPC or another exclusive hand interaction prevents that hand from parrying.
As with deflection, the supporting offhand of a two-handed gun does not parry
(the gun hand does), and a swing counts only with the weapon it was made with:
dropping, holstering, swapping or passing the gun on cancels it.
HIT HIGHLIGHTS controls the optional visual combat cues.

The kneel, recoil and attack poses are drawn only; Halo's own pose stays where
the game keeps it. Your hands and the cues follow what you see: a hand on a
kneeling enemy's drawn shoulder grabs that shoulder, a punch on its drawn head
counts as a head hit, and the cues sit over the drawn head. Grab reach is not
widened, and other players' hands are unaffected.

| Enemy | Combat behavior / opening rules |
| --- | --- |
| Grunt | Easier stagger and throw, sweeping/jabbing pressure, arm/pummel opportunities. Its stock rig lacks the wrist needed for the new kneel overlay, so it retains its native/physical reaction there. |
| Jackal | Front shielding rewards attacking from side/rear or after an earned stagger. Arm control and pummel require that exposed angle/opening. |
| Elite | Shields and counterattacks keep longer fights. Arm control/pummel require depleted shields or an earned opening. One-hand heavy restraint and two-hand lift remain. |
| Hunter | Heavy overhead pressure and sidestep cues. Armor/heavy rules remain; no lightweight arm-control or pummel opening. |
| Other/custom actors | Existing combat and native animation fallback; unsupported custom skeletons do not receive guessed new limb poses. |

An opening belongs to its enemy: staggering A, switching to B, then returning to A
keeps A's original short deadline. It does not start that deadline over. The
new kneeling presentation stands aside while a held/thrown NPC's physics owns
the body; it may therefore not appear on every earned opening.

## Projectile deflection (including a gun in hand)

**VR SETTINGS > IMMERSION > WEAPONS > DEFLECT SHOTS** is the separate toggle.
It is also available on CONTROLS. It can remain enabled without FIST COMBAT.

- Empty hand: hold **Grip + Trigger** and physically punch through a moving shot.
- Hand holding a gun: deliberately swing that hand through the shot. Trigger is
  not required; pointing or firing a stationary gun does not deflect anything.
- Actual palm contact and a brisk stroke (at least 1.2 m/s) are required. The
  return direction follows the physical stroke, not gaze or automatic aiming.
- Covers native projectile objects, including moving bullets, plasma, Wraith/
  Banshee shots, rockets and airborne/bouncing grenades. It does not turn a
  hitscan attack into a projectile or unstick attached/settled grenades.
- Faster rounds keep their speed; slow grenades gain the measured hand speed.
  Fuses, arming, range limits and explosion behavior remain native. The shot's
  damage credit/team transfers to the player. It may be deflected once per life.
- A reload, grab, climb or other reserved hand cannot deflect. The supporting
  offhand of a two-handed gun is excluded; the moving primary gun hand can parry.
- New actions run only in solo or on a compatible co-op host with host VR actions
  enabled and the existing capability checks satisfied. They are disabled for
  ordinary PvP, stock/unready hosts and network clients. No wire protocol changes.

## Grabs, vehicles and parkour

NPC grabs choose a point on the touched skeletal segment once, then retain it
until release. Fingers close on the hold. The visible hand eases toward contact
with the existing 6 cm controller displacement cap to prevent arm stretching.
Allies remain grabbable; heavy two-hand requirements and release/recovery remain.
The accepted vehicle behavior and curved-wall parkour are preserved.

## Optional campaigns: Prepare / verify mod files

Under CUSTOM CAMPAIGNS choose SPV1 or The Altheros Experience:

1. Tap **Prepare / verify mod files**. The launcher creates the folders and
   installs the app's own setup recipe. It checks files already present.
2. Import your extracted campaign folder. SPV1 also accepts the original PC
   Halo Custom Edition bitmaps.map, sounds.map and loc.map in that folder, or
   through the separate multi-file picker. Altheros takes its .yelo files and
   data_files; the launcher renames its resource files correctly.
3. Tap **Install** once all required files are present. SPV1 can still download
   missing maps from its existing HaloMaps source. Valid local files are reused.
4. Use the normal in-game campaign menu. **Play the original campaign** restores
   the base maps and keeps mod files for switching later. Start a fresh level
   after switching campaigns; checkpoints belong to their original campaign.

Included: our setup recipes, folder preparation, SHA-256 reference fingerprints,
installation and restore code. No Halo game files or mod assets are bundled.
Required: your complete supported mod version and its resource maps. Each panel
explains the source/version and lists missing files. Size and SHA-256 are checked
before newly prepared content is installed. A mismatch is an error, not proof
that some other mod/version can never work. Select the supported files again to
repair; base maps and existing valid imports are preserved on rejection.
Altheros's resource mapping now accommodates its 585 MiB bitmap resource file;
the reported "resource map too large" loading failure is fixed. Existing converted
audio caches are regenerated when their resource offsets differ. Stock/SPV1
resource layout stays unchanged. Altheros remains its author's 2019 beta with
the existing level-specific notes.
These file checks do not certify every level or modified map's runtime behavior.

## New from the OpenCE fork (HALOFREAK95's videos)

Everything from the fork by jcompto95-tech (HALOFREAK95 on YouTube) is in. Every
visual option starts off (or Classic), so the game looks as before until you
choose otherwise. Most live in a new screen:
**Settings > Video Setup > EXTRA EFFECTS**.

| Option | Where | What it does |
| --- | --- | --- |
| Shield Glow, Glow Intensity | Extra Effects | Moved here from Graphics, unchanged. |
| Overshield | Extra Effects | The overshield rises up the body as it charges and stays lit in its own color. |
| Dynamic Blood | Extra Effects | Hits throw blood on the wall behind, and it runs down. |
| Vehicle Blood | Extra Effects | Blood stains vehicles and objects and rides with them. A vehicle that hits a body gets blood on it. |
| Projectile Effects | Extra Effects | Bullet holes and burns on vehicles and armor; plasma sparks, smoke and light. |
| Stencil Shadows | Extra Effects | Hard shadows from characters and vehicles. Costly on the Quest. In VR your own body casts none (it follows the headset, not the game). |
| Weapons Physics | Extra Effects | Enhanced: dropped guns and grenades tumble and roll (the same physics as the ragdolls). A gun in your hand is never moved by it. |
| Big Multiplayer Guns | Graphics | Classic: guns on the ground are oversized in multiplayer (the game's own). Enhanced: real size. Looks only. |
| Corpse Duration, Corpse Limit | Graphics | Bodies stay longer, or many more of them. The host's setting decides online. |
| Decal Duration | Graphics | Bullet holes and scorch marks stay until the limit instead of fading. |
| Decals | Graphics, PC only | The fork keeps this one to computers (memory). |
| Third Person | FOV and Viewmodels | Flat game only (phone, tablet): the camera over your shoulder, on foot, in a campaign or co-op. A keyboard's Keypad Enter toggles it, and Alt looks around. Never in VR. |
| Spartan Armor | FOV and Viewmodels, and Pause > ARMOR | Your armor, armor lights, visor, flashlight and shield colors (Blackout for the armor). Show Players' Custom Armor and Flashlights: see other players' choices. Reset to Classic. |

**Multiplayer extras.** The players' armor choices are shared, there is **text
chat** (T opens a line: Enter sends it, Tab switches team/all, Escape cancels),
and **votes to kick or ban for 12 hours with a reason** (F1 votes yes, F2 no).
They travel in messages of their own. OpenCE players without them simply ignore
those messages, so you join and host the same games as before (network 28).
Turn them off in the launcher: **Server Browser > Community extras**. Chat's
own options (show it, opacity, size) are in **Settings > Network Setup > Text
Chat**.

Typing chat and voting use keyboard keys. A Bluetooth keyboard paired with the
Quest or phone works. Without one you still see chat lines and other players'
votes.

## VR controls: reset to default

**VR SETTINGS > BUTTONS** now starts with **ALL TO DEFAULT** (the same reset as
RESET BUTTONS at the bottom). Either row shows DONE for two seconds once pressed.

## Halo 1 MCC maps (solo, experimental)

From GulchCE (chestahh). MCC maps play **solo only** in this build; online MCC
games are for later. The launcher's **HALO 1 MCC MAPS (SOLO, EXPERIMENTAL)**
section has:

- **Steam Workshop: download MCC maps.** Browse the Halo 1 Workshop in the
  launcher. On a map's or collection's page, tap DOWNLOAD TO HALO. Downloading
  needs a Steam account that owns Halo MCC: sign in with your name and password,
  then approve in the Steam app or type the Steam Guard code. Only a sign-in
  token is kept, never your password.
- **Installed MCC maps:** see each one with its size; enable, disable, delete
  (your saves are kept), check for updates, open its Workshop page.
- **Import MCC maps from a folder** and **Import MCC's resource maps (from your
  MCC).** Some maps need MCC's own shared resource maps; they come from your copy
  of MCC and are not bundled.
- **Remove all MCC maps.**

In game: **New Game** (campaign) or **Multiplayer**, then pick the map kind
**MCC SINGLEPLAYER** or **MCC MULTIPLAYER**. Hosting a network game skips the MCC kinds;
local split screen keeps them. This is experimental on the Quest (memory, texture
decoding on the CPU). Some MCC models may draw wrong.

## What to test

See TEST67-DEVICE-CHECKLIST.md. Weapon pose comfort, combat balance, feedback and
campaign playthroughs still need device results. This candidate has not been
installed or launched by the agent. The network version (28) and voice chat are
unchanged; the community extras use new message kinds that stock OpenCE players
ignore. Optional campaign resource addressing and its converted-audio cache
identity changed, as described above.

---

## Carried-forward Test66 features and controls

# Test66 private candidate: 1.0.33-test66

## Test66: OpenCE Build 201, dynamic ragdolls, a second campaign mod

**Validation status:** these are implemented changes with automated checks; the exact Test66 pair still needs headset/phone testing. The descriptions below explain intended behavior, not completed device acceptance.

This private build answers your 2026-10-13 Test65 list (both logs and videos
of 16:08 and 16:24, and the 17:37 weapon-pull log and video) and your later
additions. It installs over Test65 and earlier (same package names and
signing key, Android version code 78) and keeps your settings, profiles,
saves and game data. The network protocol is unchanged (this build hosts
OpenCE network 28 and joins 11 to 28) and voice chat is unchanged (only the
talking icon's drawing is new).

### Warthog: no camera jump, the wheel turns all the way (IMMERSIVE VEHICLE on)

- **The view no longer jumps into the dash.** Your videos (4:41, 5:36) show
  the eyes dropping 30-50 cm for about a second and a half. The seat's eye
  point was being re-captured whenever the vehicle's head marker strayed, and
  then held there. With the controls up the eye point is now fixed per seat
  (a stray is only logged).
- **The wheel never lets go or flips.** Turning past half a circle used to
  wrap the angle to the other lock, which looked like a release and a snap.
  The wheel now follows your hands frame to frame: it turns up to 120 degrees
  each way while you hold it, and steering reaches full lock at 60 degrees.
  Grip held on the wheel means it stays held.
- The Ghost and tank were reported good; their controls are unchanged. The Banshee profile is also unchanged and still needs device testing.
- **IMMERSION > VEHICLES** now has every immersive-vehicle setting (wheel,
  handlebar, sticks, sizes, offsets, glow, haptics, COCKPIT LOCK, RESET
  CONTROLS), not under WEAPONS. Per-vehicle calibration is kept.

### LEFT-HAND MODE (CONTROLS)

Your gun starts in the left hand at every level start and respawn, and the
holsters and pouches mirror. Swapping by hand works as before (HAND SWAP
radius unchanged).

### Manual reload, polished (RELOAD page)

- The hand holding the magazine now takes Halo's own reload pose for that
  weapon (sampled from the game's first-person reload animations), and the
  magazine locks into the grip on contact without shaking.
- Bring it to the gun: a small mag-well assist lines it up, the seat follows
  the well's axis with haptics growing as it goes in, and a pulse when it
  seats. The charging handle or slide locks to your hand and moves only along
  its own track. CHARGE REACH is unchanged.

### FIST COMBAT, as a mode

- **ENEMY HEALTH now scales fist damage correctly.** At 6X ordinary fist damage is divided by six before other combat modifiers. Combo, armour and takedown rules mean the actual punch count is not an exact six-times guarantee.
- **Airborne lunge**: punch an enemy above or below you (up to 3 m) and you
  fly to it.
- Hit lights follow the enemy's own bones (head and chest).
- **Block and parry.** Raise a hand between your face and an attacker: its
  melee is blocked (reduced). Swipe at its arm as it swings: parried, it
  staggers open.
- Enemies fight back by type: Grunts are stunned easily, Jackals guard from
  the front (hit them from behind), Elites answer a flurry with a swing of
  their own and fall only to takedowns and counters, Hunters are never
  knocked down and only take full damage from behind.
- Turning FIST COMBAT on brings NPC GRAB's assist with it (10 cm).

### Grabbing NPCs and bodies

- **GRAB ASSIST works from the body's surface now** (it measured from the
  bone's centre line, so a hand touching an Elite's armour could miss). It
  goes up to 25 cm; NPC GRAB and FIST COMBAT bring 10 cm.
- **A body you hold never vanishes.** The game was tidying up held corpses
  (and leaving their root behind); a held body is now kept awake and off the
  clean-up list, and thrown bodies stay where they land.
- Shot and blast deaths throw bodies harder (STRONG), and where a shot hits
  matters: legs fold, the head snaps back.

### Wall running on curved and angled walls

The Silent Cartographer's rock walls failed: only near-vertical flat walls
counted. Now curved, angled (rock faces to about 53 degrees), segmented and
overhanging walls run, checked at three heights, with the facing eased round
bends and a short grace over gaps. Steering away from the wall ends the run.

### OBJECT THROW (comes on with world and vehicle grabs)

A crate, prop or vehicle you let go of while swinging flies the way you
threw it (2X default; OFF just drops it).

### Grenades at your waist

Chest grenades are smaller and sit at the waist by default (FWD 12 cm, DOWN
60 cm, GAP 18 cm; your earlier positions are moved there once). They no
longer warp when set very low (the drawn model kept its detail level and is
placed from your neck, not your head's pitch).

### WEAPON PULL, gravity-glove style (on by default)

Like Half-Life: Alyx and the Half-Life 2 VR mod: point a free hand at a
weapon up to 3 m away (PULL REACH 1-5 m) and it glows with a line to your
palm; squeeze to lock it, then flick your hand back: it arcs through the air
into your hand. A closed hand catches it, an open hand lets it drop. PULL
STYLE GRIP pulls it on a held grip instead of a flick. WEAPON PULL OFF turns
it off.

### Dynamic ragdolls (OpenCE's, with Jolt Physics)

Bodies now fall as OpenCE's dynamic ragdolls: limp, thrown by what killed
them, tumbling down stairs and over ledges. On the Quest and on Android the
physics runs in the app's 64-bit host. Your hands and these ragdolls share
bodies: a body you hold is yours, and when you let go it goes back to the
ragdoll physics. Living knockdowns (punches, slams) stay this build's own,
up again within a second. IMMERSION > RAGDOLLS > DEATH PHYSICS: DYNAMIC
(default) or CLASSIC (the game's own death animations).

### Custom campaigns: SPV1 and The Altheros Experience

- The launcher's warnings about SPV1 are gone: it plays now.
- **CUSTOM CAMPAIGNS** (launcher): "Campaign now:" shows what plays; one
  button per mod (SPV1, The Altheros Experience) and "Play the original
  campaign". One campaign is installed at a time; switching puts the other
  back first, and installed mods stay imported to switch back at once.
- **The Altheros Experience** (Altheros's 2019 campaign beta, OpenSauce
  maps) is not downloaded by the app. On a computer, extract "Latest Altheros
  Experience 10.24.2019" (moddb.com), copy its folder (the .yelo files and
  data_files) to the headset's Download folder over USB or SideQuest, then
  in the launcher tap The Altheros Experience > Import, choose that folder,
  and Install. About 3.4 GB; each level converts its sounds the first time it
  loads (up to about 1 GB more, once).
- Play it from the game's normal Campaign menu (there is no separate in-game
  section: the menu plays whichever campaign the launcher installed). F10 (a
  reworked Stockade) is an extra level, not in the menu. It is a beta, as its
  author says: read its notes in the launcher.

### From OpenCE Build 201 (the newest release), on both builds

- **Map sharing**: join a game on a Custom Edition map you lack and the host
  sends it (and the resource maps it needs) into your active game set's maps
  folder. Server Setup > MAP SHARING turns it on and sets the speed. Over the
  internet the map comes from the host; on a LAN other players help.
- **Votes to kick** (VOICE AND VOTING), **Server Setup** grouped into CO-OP
  OPTIONS (your PHYSICAL INTERACTIONS and HOST VR ACTIONS are here now),
  VOICE AND VOTING and MAP SHARING.
- Display options: field of view, the gun's field of view and visibility,
  shield colour and glow, the shield on your arms; your legs in first person
  (flat build; VR has its own full body). On VR the headset's view, gun and
  body stay VR's own.
- Overshield and camouflage no longer vanish at the edges of the view;
  faster collision in crowded fights; high-res button icons and text; many
  smaller fixes. The flat build's campaign pause menu gets SETTINGS.
- **Not taken** (they would replace parts of this build that work): browser
  players (WebRTC), OpenCE's touch controls and Android app shell, its audio
  resampler and renderer rework, screenshots (desktop only). The full list
  and reasons: TEST66-OPENCE-PARITY.md.


---

# Test65 private candidate: 1.0.32-test65

## Test65: Arkham Shadow fists, a steady Warthog, safer grabs

This private build answers your 2026-10-13 list (your Test64 logs and video
and a tester's report). It installs over Test64 and earlier (same package
names and signing key, Android version code 77) and keeps your settings,
profiles, saves and game data. Multiplayer, the network protocol and voice
are unchanged (the phone join fix in 1.0.31 stays).

### Fist combat, after Batman: Arkham Shadow (FIST COMBAT on)

- **It works now.** In Test64 a punch never picked a target: the game asked
  for your head's position a moment before each frame had it, and got
  nothing (65 punches in your logs, not one "fist combat" line). It now uses
  the last frame's head.
- **Punch across the room (LUNGE, 6 m).** Make a fist (grip and trigger),
  look at an enemy (or throw the punch at one) and punch: you dash to it (up
  to 10 m/s) and the blow lands as you arrive. Chain punches between enemies
  the same way. LUNGE OFF keeps the old short step (FIST REACH).
- **Combo meter.** Each hit within two seconds of the last adds to your
  combo (white lights over the enemy, and each hit lands 8% harder, up to
  +80%). Getting hit breaks it. At 8 the lights turn gold: a hard punch is a
  **takedown** (six times the blow) that knocks the enemy down. A hit from
  behind on a stunned enemy is a takedown too.
- **Counters (COUNTERS on).** When an enemy swings at you, a blue light
  pulses over its head and both hands tap. Punch toward it to counter: its
  blow never lands, it is knocked down, and your combo goes on.
- **ENEMY HEALTH (3X).** Enemies take three times as many punches, so fights
  flow as combos instead of ending in one hit. Guns, grenades and takedowns
  are unchanged.
- Long lunges, counters and takedowns knock enemies down as short ragdolls;
  they are up again within a second (your NPC RECOVERY rule).

### Warthog: steady wheel and view, no purple bar (IMMERSIVE VEHICLE on)

- **The purple bar is gone.** It was the Banshee's flight yoke being drawn
  by mistake over the Warthog's own wheel. GRIP GUIDE (off by default) can
  show small pads where your hands go instead.
- **COCKPIT LOCK (on).** Your eyes, your hands and the wheel now move as one
  with the Warthog, so the wheel stays on the dash under your hands. Before,
  the view stayed level and smooth while the hands and wheel were turned in
  30 Hz steps and kept level; on rough ground and in turns the dash swam
  against the wheel and it snapped. With the cockpit lock the cockpit stays
  still around you and the world moves (the vehicle's pitch, roll and turns).
  Turn it off to go back to HORIZON's choice.

### Hands and guns

- **HAND SWAP (CONTROLS page, 10 cm).** Racking the pistol's slide could pass
  the gun to the other hand: the swap (the off hand's grip with the hands
  close) reached 20 cm. It is 10 cm now; choose 6 to 20 cm, or OFF.
- **WEAPON PULL (1 m) and PULL GLOW.** Point a free hand at a weapon lying
  within reach (or hold it right by one): it glows. Grip, and it flies into
  that hand and is equipped (into a free slot, or in place of the gun you
  hold). Let go early and it drops. Solo, or as the host.
- **Dual wielding is not in this build.** Halo CE fires only the gun in
  hand; a real second gun needs new engine work (see the delivery notes).

### Grabbing, bodies and ragdolls

- **Shade turrets no longer kill you.** A turret (any vehicle) in your hands
  pressed into you counted as a vehicle running you over, every tick. Now
  what you hold never hurts or pushes you, and for two seconds after you let
  go it can push but not hurt you.
- **Friendly NPCs survive being picked up.** A body in your hands hurts
  nothing for its first half second, never hurts an ally (itself or one it
  bumps) while held, and otherwise only when you slam it (5 m/s). A thrown
  ally takes half.
- **Thrown bodies stay.** A body still flying when its time ran out went
  back to the engine marked for clean-up, and the engine deletes moving
  bodies it thinks you cannot see. Bodies now rest first (up to 10 s), and
  their clean-up mark waits until they are still.
- **GRAB RAGDOLL (ON LIFT).** Taking a living NPC by an arm or leg no longer
  ragdolls it at once: it stays on its feet, held (it cannot walk or shoot;
  a light one is dragged along). Lift it 18 cm off the floor, or yank it,
  and it becomes a ragdoll in your hands. AT ONCE is the old way.
- **ACTIVE RAGDOLL (on).** Bodies react: a slow hand pushes an NPC (ally or
  enemy) and the touched arm or the torso gives; hits make the struck limb
  swing and the torso lean; the held limb reaches toward your hand. Knocked
  and thrown NPCs keep some of their posture as they stagger and get up,
  and a body just killed slumps instead of dropping limp.
- **Easier grabs.** A hand that touches nothing now takes the nearest object
  within GRAB ASSIST and 3 cm more (8 cm by default): turrets, crates, props.

Test with a log, please: the new lines start "VR fist combat:", "vr: cockpit
lock:", "VR pickup:", "VR NPC: lifted", "VR NPC: touch push", "VR NPC:
knocked down", "VR world: grab assist" and "vr: hand swap:".

---

# Test64 private candidate: 1.0.31-test64

## Test64: VR SETTINGS open again

This private build fixes your Test63 crash and changes nothing else. It
installs over Test63 and earlier (same package names and signing key, Android
version code 76) and keeps your settings, profiles, saves and game data.

- **Opening VR SETTINGS crashed the game in Test63.** Your 14:09 log ends in
  a crash the moment the settings opened. Test63's new topic list (a
  category with three or more screens opens a list of its sections first)
  was also built for the list of categories itself, which is three screens
  long, and it read past the end of the category table to name its rows.
  The topic list is now made only for a category's own pages; the category
  list pages with NEXT as before.
- Everything else in Test63 is unchanged and still waits for your headset
  test: see the Test63 section below and `TEST63-DEVICE-CHECKLIST.md`.

---

# Test63 private candidate: 1.0.30-test63

## Test63: your Test62 session, fixed

This private build answers your fresh-install Test62 session (the 12:06 log
and the 12:06:42 video) and the requests that came with it. It installs over
Test62 (same package names and signing key, Android version code 75) and
keeps your settings, saves and imported game data. Everything that worked in
Test62 (impacts, reload and its haptics, magazines, charging, grabbing,
climbing, wall running, ragdolls, vehicles, holsters, scopes, co-op, voice)
is unchanged unless listed here. None of this has been tried in the headset
yet.

### The reticle and BUTTON SPRINT

Your log shows what happened: the left stick's click hid the reticle
(12:10:53), then you turned BUTTON SPRINT on (12:11:04), which takes that
click. The reticle stayed hidden and no button could bring it back.

- While BUTTON SPRINT is on, the left stick's click only sprints. Anything
  else on that click waits, and comes back when you turn sprint off (as
  before).
- If the reticle's toggle has no button, a hidden reticle is shown again.
- The Buttons menu skips L STICK while BUTTON SPRINT is on, so two things
  can't end up on one click.

### X: get in, or drop the magazine

Pressing X to drive the Warthog also dropped your pistol's magazine
(12:09:37). Now, when X has an action on offer (get in a vehicle, swap or
pick up a weapon, press a switch), it does that action and never drops the
magazine.

### Chest grenades

- **They stay on your chest.** The slots followed your head, so they moved
  every time you looked around. They now sit in a chest frame that turns
  with your body. It only follows your head once you've turned more than
  35 degrees, and it holds still while you look down at it, so your hand
  learns where they are.
- **They're the real grenades.** The green and blue balls were stand-ins.
  The slots and your hand now show the game's own frag and plasma grenade
  models.
- **Grabbing works.** In your video your hand closed right on the slot and
  never took it: the test used the controller's grip point, not the palm you
  see. It now uses the palm drawn on screen, with 12 cm of reach. You feel
  a light tick when your hand reaches a slot, and a near miss is logged
  with the distance.
- THROW POWER is now 1.5X by default (your setting).

### Fist assist (FIST COMBAT)

Your log has no "acquired" line: not one punch picked a target. Now:

- **FIST REACH** is 2.5 m by default (1 to 3 m). A deliberate punch (closed
  fist, above MELEE SPEED) picks the enemy you're looking at, within about
  45 degrees of your gaze, in sight, and not behind the punch. Hooks count.
- If it's a step or two away, you get a short Spartan step toward it (up to
  5 m/s), stopping at striking range.
- The target is slowed (not frozen) during the step and for half a second
  after a hit, and its AI keeps running. The next punch prefers the same
  enemy, so combos chain.
- The moment a hand grabs or climbs, the assist lets go: punch, then grab
  and slam.
- When a punch takes nothing, the log says why: how far away the nearest
  enemy was, at what angle, and whether it was in sight.
- With FIST COMBAT off, physical melee is exactly as before.

### Grabbing that purple Covenant crate

The crates on the beach were grabbable, but the hand never got to test
them: the beach's trees and the crashed Pelican (17 m across) used up the
hand's 32 contact tests first. The hand now tests the nearest objects first
and skips anything too big to lift. A miss now names the nearest object in
the log.

### Vehicles (IMMERSIVE VEHICLE on)

- **The Warthog's wheel is the Warthog's own.** The model's steering wheel
  is drawn where your virtual wheel is, and your hands turn it: one wheel,
  the real one. With VIRTUAL WHEEL hidden, nothing changes (you grab the
  model's wheel where it sits).
- **The Ghost, Scorpion and Banshee controls are redesigned** after the
  vehicles: rounded, shaded parts in their own materials. The Ghost has a
  violet Covenant handlebar with blue-lit pods, the Scorpion a UNSC drive
  stick with a rubber boot and a grip, and the Banshee a violet flight yoke.
- **A live calibration preview.** Sit in a vehicle and open the VEHICLES
  offset rows (CTRL REACH / LEFT / HEIGHT, HOG, GHOST, TANK, BANSH): the
  controls show in blue where your hands will actually take them, with the
  grab reach and which way they face, and they move as you change a value.

### ONE-HAND HEAVIES

New in GRAB + NPCS, off by default: with it on, one hand lifts a living
Elite or Hunter (normally one hand holds it in place and the second
lifts). It turns NPC GRAB on.

### Your parkour defaults

WALL SPEED 1.5X and WALL LEAP 1.5X are the new defaults (what you set in
the video). CLIMB LAUNCH stays 1X and WALL TIME 2 S, as you left them. If
you've already saved other values, yours stay.

### Settings: jump to a section

A category with three or more screens now opens a list of its sections.
IMMERSION lists its topics (FIST COMBAT, GRENADES, RELOAD, MOVEMENT...),
and long categories like VEHICLES list their pages by their first setting.
Pick one and you're there. B takes you back to the list in one press. NEXT
still pages on as before.

### Checked here, and what to try

Every change has an automated check, and the full regression suite runs
before each build. Nothing here has been tried in the headset yet. See
TEST63-DEVICE-CHECKLIST.md.

---

# Test62 private candidate: 1.0.29-test62

## Test62: settled controls, easier grabs and campaign impacts

Private owner-test build, Android version code 74. Install the matching APK
as an update over Test61; package names and signing identity are retained.
Keep the app installed to preserve game data, profiles, settings and saves.
This candidate also adds experimental fist-combat assistance and physical
grenades. Automated checks do not establish headset comfort or multiplayer
acceptance; the device checklist covers those remaining checks.

### Immersive vehicles

- Controls wait for the seat eye to settle before measuring and locking:
  at least half a second after entry, then 350 ms within 1.5 cm. Moving the
  whole vehicle does not reset that check. A three seconds maximum prevents
  an idle animation from leaving the controls unavailable indefinitely.
- The seat locks when that measurement completes, replacing the separate
  half-second and one-second timers during the boarding animation.
- VEHICLES adds **CTRL REACH**, **CTRL LEFT**, **CTRL HEIGHT** for all immersive
  controls. These add to HOG/GHOST/TANK/BANSH adjustments; combined offsets
  stay within 50 cm. COMFORT REACH still limits final reach. Adjust while
  ungripped. Wraith uses the tank profile if a map provides a drivable seat.
- IMMERSIVE VEHICLE still brings FIRST PERSON with it. Its changes apply
  only while enabled. The existing wheel visibility, grip choices, steering,
  hand frame, third-person controls and vehicle reticles remain available.

### NPC grabs, impacts and ragdolls

- New settings default **GRAB ASSIST to 5 CM**: NPC body contact reach becomes
  16 cm with default HAND CONTACT, previously 11 cm. Saved choices stay:
  choose 5 CM in IMMERSION > GRAB + NPCS if yours still says TOUCH.
  This affects body capsules only; world and prop grabs remain contact based.
- The first hand on a living Elite or Hunter restrains its horizontal root
  where it was caught; a second distinct body contact enables the lift.
  Gravity and native world collision remain active. Releasing one hand after
  lifting retains the existing lowering/drag behavior. Allies are still
  grabbable under the existing rules. Corpses use one hand; a heavy NPC killed
  during the first grip changes to a one-hand lift. A restrained NPC cannot
  start a melee attack or deal an already queued/contact/continuous melee hit
  while the restraint is active; its native recovery remains in charge.
- Campaign impact damage falls back to the map's falling-damage effect, then
  vehicle collision effect, when the unit/unarmed weapon supplies no melee
  effect. Test61's claim that the unarmed lookup alone fixed campaign slams
  was incorrect: the owner's 08:58 log still showed no damage effect.
- Floor slams honor **IMPACT SPEED**, just like wall slams. The separate 6 m/s
  floor gate is removed. Damage depends on speed into the surface; grazing
  along it is not a full slam. The same-target repeated-hit guard remains.
- Slams and physical melee use the native damage result for shield and body
  feedback. Shields break only when their actual vitality is depleted. Blood
  or body-hit art appears only when body vitality drops, using the target's
  authored effect. If it has none (as with stock Elites), a currently loaded
  assault-rifle projectile can provide that body's material response. Missing
  effect art is skipped; nothing is loaded during the hit. This preserves
  Halo's species/material differences instead of showing blood on shields.
- Logs record the damage tag/scale, material, and before/after shield and body
  vitality. Include these **VR contact damage** lines when reporting a slam
  that looks or feels wrong.
- **RAGDOLL RANGE** offers 20 / 40 / **60** / 80 metres; 60 is the new default.
  **NPC RIG SLOTS** stays at 24; the existing settling, slot reuse and recovery
  limits remain. Use a shorter range if a busy scene costs performance.
- The parent-relative joint solver is retained, with invalid transient
  topology rejected before indexed work. Living-NPC recovery remains capped
  at one second. This is not Euphoria or GTA IV's active-balance system.

### Manual reload and hand feedback

- The existing manual reload sequence and ammo rules are retained. A loose
  magazine now follows the same adjusted palm rotation as the visible hand,
  including HAND ANGLE and either handedness.
- Insertion, seating, charging and ready pulses already existed. Brief reload
  pulses now take priority over subsequent finger/surface contact buzz on the
  same hand, including the central wall-contact feedback path, so contact
  requests cannot immediately replace the pulse.
- Master **HAPTICS** still scales all feedback; the existing **HOLSTER HAPTICS**
  exception remains. No separate reload-haptics setting is added.
- Magazine insertion tolerances, charge travel, pouch choices and bindings
  remain the same. **USE/RELOAD** ejects while MANUAL RELOAD is active; the
  normal reload path remains for disabled/unsupported cases. Manual reload
  remains local-play only. Check tactical and empty reloads, both hands,
  holsters, release-grip drop, firing feedback and native animation handoff.

### Experimental assisted fist combat

Enable **VR Settings > IMMERSION > FIST COMBAT > FIST COMBAT**. It starts OFF.
The same controls are also available on CONTROLS.

- Turning it on requires **FIST REQUIRED** and impact **MELEE**, and also
  turns on NPC GRAB and CLOSE CONTACT through the existing dependency system.
  These settings support a closed-fist interaction without an open hand swinging
  into accidental melee. If MELEE SPEED was OFF, enabling FIST COMBAT restores
  the positive default threshold; an existing positive threshold is preserved.
  Choosing MELEE SPEED OFF afterward visibly turns FIST COMBAT off. Changing
  MELEE to SWING also turns FIST COMBAT off. The runtime requires impact mode
  and closed fists even when assistance was enabled by editing config; it cannot combine a
  native swing with assisted direct-hit damage. Review automatically changed
  rows before playing.
- Look at an enemy and throw a qualifying forward punch with a free fist.
  **FIST REACH** selects the acquisition distance: 0.75 / 1 / **1.5** / 2 m.
  It uses actual enemy allegiance, active NPC state and line of sight;
  players and allies are not targets.
- The approach uses the normal collision sweep and the two characters'
  native capsule widths to stop outside body contact, while preserving gravity.
  It does not teleport through scenery. Pulling backward, strongly strafing,
  being airborne or climbing cancels approach.
- Repeated punches maintain one target rather than jumping between enemies.
  Its horizontal movement is restrained during the short combo lock. The
  lock expires after two seconds without a qualifying punch/hit, or earlier
  if it dies, becomes obstructed, gets too far away or you look well away.
  This holds the same opponent for the exchange; it does not rotate your
  camera or move the enemy to stay magnetically attached to your gaze.
- **HIT HIGHLIGHTS** marks head/chest in cyan and changes to amber during a
  brief stun. A head contact or a three-hit sequence can stun for 0.9 seconds.
  New, queued, contact-attachment and continuous native melee attacks are
  suppressed during that bounded stun. A rear hit during the window uses
  increased native melee damage; existing protected-actor rules still apply. NPC grabbing/slamming remains available.
  An empty campaign fist with no available melee effect uses a reduced native
  impact fallback only while this assist is enabled; ordinary weapon melee
  keeps its authored damage.
- A small additive spine reaction and impact flash accompany the exchange.
  Existing Halo hurt sounds and damage behavior provide audio feedback.
  Death/ragdoll poses and held NPCs keep their own animation path. This is a
  bounded assist inspired by Arkham Shadow, not that game's assets or combat
  engine. The custom animation is the hit/stun reaction; the rear strike
  uses native damage rather than a choreographed finisher. Comfort, spacing
  and species-specific results need headset tests.

### Experimental physical grenade throwing

Enable **IMMERSION > GRENADES > PHYS GRENADES** (OFF by default).

- Available frag grenades appear at the left chest and plasma grenades at
  the right. Use an empty/free hand, touch the grenade, then press **Grip**.
  **Release Grip to throw**. The grenade is not cooking in your hand; its
  native fuse/behavior begins on release.
- **CHEST FWD**, **CHEST DOWN** and **CHEST SPACING** move the slots. Defaults
  are 16 cm forward from the head, 30 cm below and 14 cm to either side.
  Slots follow the horizontal head-facing chest frame. They are adjustable,
  not dependent on the visible torso mode.
- **THROW POWER** ranges from 0.5X to 2X, default 1X. Recent hand movement,
  including rotation at the palm, determines throw direction and momentum;
  final speed is limited to 15 m/s.
- Native grenade counts are charged only after the projectile is successfully
  placed. Invalid tracking, a large tracking jump, recenter, lost hand
  ownership, death, pause/state reset or rejected placement cancels a held
  throw without losing its grenade. New-map/disposal hooks also clear grenade
  and combat state before map-local object identities can be reused.
  After cancellation, release and squeeze Grip again to pick up another one. There is no magazine-style persistent
  grenade object while held.
- A held grenade follows the fresh final visible palm after hand collision
  and action blending. Hidden/unsupported hand rigs use a tracked fallback
  clamped away from world obstructions; an old hand pose is not reused.
- Grab/release feedback uses master HAPTICS. Its short event pulses get
  priority over continuous wall/fingertip feedback on that hand, without
  changing other haptic settings. Grenades respect hand ownership
  for reload, holsters/weapon use, climbing, vehicle controls and NPC/world
  grabbing. Standard grenade buttons remain available; a button throw is
  suppressed while a chest grenade is held and on its release tick to avoid
  spending two grenades.

### Parkour, aiming and scopes

- Optional parkour keeps its existing collision/state rules. New defaults
  give **CLIMB GRAB 14 CM** and **WALL TIME 2 S**, previously 10 cm and 1.5 s.
  Saved choices stay. These are reach/time refinements, not auto-enabling
  parkour or disabling its collision checks. The eye-to-hand fallback now
  requires the hand itself to be within the configured contact radius of the
  wall, so a deeply penetrating hand cannot latch a distant crossed surface.
- **AIM STEADY** is on IMMERSION > FIST COMBAT and HUD + RETICLE:
  OFF / LIGHT / MEDIUM / STRONG / MAX. OFF preserves existing scoped smoothing. Higher choices add
  angular steadying to the shared gun/shot/scope aim, rather than smoothing
  only a cosmetic reticle that could disagree with the bullet direction.
  Recenter and invalid frame timing reset the filter.
- The scope lens origin follows the final drawn gun wrist when gun anchoring
  is active. This includes gun offsets, visible hand adjustment and wall
  pullback; a stale frame's anchor is never reused. The fresh wrist is
  published even when its translation is zero, preventing that normal case
  from falling back to a different scope origin. Scope orientation and weapon
  aiming stay on their shared pose.
- Existing per-weapon scope position/size adjustments remain for all supported
  weapon profiles. This does not substitute a universal scope offset for
  each gun. Check one/two hands, left/right handedness, gun offsets, movement
  and close walls; the automated geometry cases cannot prove eye comfort.

### Co-op, multiplayer and Android

Use the actual in-game **Server Setup**, not a separate launcher host form.

- **HOST VR ACTIONS** is a new OFF-by-default co-op option. To let the VR host
  use fist assistance or chest grenades, enable it and **VR INTERACTIONS**,
  then enable the relevant VR feature. Every connected peer must complete the
  existing physical-interaction capability handshake. A mixed/older peer or
  missing permission disables these new actions.
- This permission applies to the host's new actions. Remote clients retain
  native grenade/melee inputs, and PvP does not enable these combat assists.
  No new protocol or capability version is introduced. Resulting projectiles,
  damage and movement use existing host-authoritative gameplay paths.
- NPC physics authority is explicitly limited to local play or the permitted
  server. A client completing the handshake still sends grips and displays
  replicated poses through the existing path; readiness alone does not let
  it drive the same NPC independently.
- Existing NPC ragdoll synchronization remains limited to **four remote
  machines**. This is not a four-player limit on ordinary campaign co-op.
  Existing world interactions have their own guards. Custom NPC rig fallback,
  manual reload and magazine debris retain their local-only restrictions;
  parkour retains its existing local/co-op-host restriction.
- Network and voice implementations are unchanged: hosting remains network 28,
  with joining 11-28 under the existing compatibility rules. No new upstream
  integration or universal server-compatibility claim is part of Test62.
- Flat Android keeps its familiar touch/controller behavior and receives the
  matching code74 package, guide and co-op host setup option. VR-only actions
  do not become touchscreen gestures.

### Validation and preserved work

The targeted checks cover control anchoring, contact grabs, heavy restraint,
native impact transactions, stock ragdoll skeletons, reload state/ammo/haptics,
new grenade/combat state, setting dependencies, scopes and menu layout.
The full-suite/build/package results belong in TEST62-DELIVERY-STATUS.md after
completion. On-device interaction, comfort, performance and paired co-op still
need the owner tests in TEST62-DEVICE-CHECKLIST.md.

Changes remain local and private. Packaging does not install, launch, push or
publish anything. PC/Steam Frame work stays deferred. Existing public releases
and README presentation are not changed.

The sections below are historical candidate notes. This Test62 status
supersedes their earlier claims; those notes are not new device confirmations.

---

# Test61 private candidate: 1.0.28-test61

## Test61: the wheel stays in your hands, impacts that hurt, more ragdolls

This private test build answers your Test60 sessions (the 07:58 and 08:09
logs and the 08:03 video). It installs over Test60 and earlier (same package
names and signing key, Android version code 72 before, 73 now) and keeps your
settings, profiles, saves and imported game data.

### Immersive vehicles

- **The Warthog's wheel stays in your hands.** With HORIZON on LEVEL your
  view stays level while the Warthog pitches and rolls. The wheel was fixed to
  the Warthog's body, so it rolled under your still hands: the roll read as
  steering and your grip slid off. Your view also swayed with the driver's
  steering animation, which moved your hands on the wheel. Now, while
  IMMERSIVE VEHICLE is on, the seat holds your view still (the vehicle's own
  bumps and turns still carry you), and the controls sit where your hands
  are tracked: they turn with the vehicle but don't tip and roll under you.
  This is the same for the Ghost's handlebar, the Scorpion's stick and the
  Banshee's bar.
- The Warthog's wheel no longer jumps between the dashboard and your chest
  (its spot was right on the old one-metre limit). Where the controls sit is
  decided once when you get in.
- Turning on **IMMERSIVE VEHICLE** now also sets VIEW to **FIRST PERSON**
  (the controls only exist in first person), and choosing THIRD PERSON
  turns IMMERSIVE VEHICLE off. **TANK HATCH** and **HOG GLASS** also bring
  FIRST PERSON with them.

### Impacts, ragdolls and bodies

- **Slams and throws now really hurt.** The blow was set up from the Master
  Chief's own melee damage, and he has none of his own (the game uses his
  unarmed punch instead), so every impact was quietly dropped: your logs
  never had a single one. It now uses that same unarmed blow. Each impact
  writes a `VR impact:` line to the log.
- **More ragdolls at once: NPC RIG SLOTS now goes up to 24** (and starts at
  24). Explosions killing a group while the last fight's bodies were still
  settling used to run out of slots, so some enemies played the old death
  animation. If all 24 are ever busy, the body that has lain longest is
  handed to the game's own corpse physics to make room. A death that still
  doesn't ragdoll writes `death ragdoll skipped` with the reason to the log.
- **Dead Elites and Hunters lift with one hand.** Two hands are only needed
  while they're alive and fighting back.
- **NPC GRAB** now also turns on **CUSTOM NPC RIGS**, and **WORLD GRAB**
  turns on **CUSTOM SCENERY**, so every NPC and every piece of scenery can be
  taken. You can still turn either off yourself.

### Other settings that come on together

- **SHOULDER POUCH** and **HIP POUCH** turn on MANUAL RELOAD, and **SPRINT
  TOGGLE** turns on BUTTON SPRINT.

### The gun that stopped firing

- In your 08:09 log a menu was closed with the button still held, and 27 ms
  later that held button counted as a reload press: it ejected the magazine
  with 24 rounds left, and the gun can't fire until a reload finishes. A
  button still held from a menu no longer counts as a reload until you let
  go of it.

---

# Test60 private candidate: 1.0.27-test60

## Test60: impacts for every NPC, settings that come on together

This private test build answers your Test59 session (the 07:04 log and the
07:12 video). It installs over Test59 and earlier (same package names and
signing key, Android version code 72) and keeps your settings, profiles,
saves and imported game data.

### Impact damage

- **Slamming and throwing bodies hurts them, friendly or not.** Your Test59
  log has no impact at all, even for marines thrown at 24 m/s with IMPACT
  DAMAGE on. Three things were wrong:
  - A body slammed flat onto the floor or glancing off a wall touched it
    with the edge of a joint, never its centre, and only a centre hit
    counted. Now a touch is checked straight into the surface it met, so a
    hard slam counts (how hard still depends on the speed into the surface,
    so a body sliding along the ground isn't hurt).
  - A thrown or slammed body passed straight through other NPCs and
    vehicles, so it could never hit them. Now it strikes them: the body
    stops against them, both take the blow and the one hit is knocked back.
    Your own body (the hands holding it) is never hit.
  - The blow counted as friendly fire, and allies such as marines shrug off
    most friendly fire, so a slammed marine barely felt it. A physical blow
    now hurts every NPC fully (it is still yours, for kills).
- IMPACT SPEED and IMPACT CAP work as before.

### Settings that come on together

- Turning on **DEATH RAGDOLLS** now also turns on **NPC GRAB**, **NPC
  RESCUE** and **IMPACT DAMAGE** (and FIST REQUIRED, as NPC GRAB always
  did). Turning on **NPC GRAB** turns on NPC RESCUE and IMPACT DAMAGE;
  **WORLD GRAB** and **LIFT VEHICLES** turn on IMPACT DAMAGE.
- Turning on a vehicle option that only works with the immersive controls
  (STEER HAPTICS, COMFORT REACH, TANK DRIVE, BANSH SLIDE, CONTROL GLOW,
  VIRTUAL WHEEL) turns on **IMMERSIVE VEHICLE**; **HOLSTER HAPTICS** turns
  on **HOLSTERS**.
- You can still turn any of them off yourself afterwards and it stays off.
  What a feature turned on goes off again when you turn that feature off,
  unless you chose it yourself.

---

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
