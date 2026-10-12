# Halo CE Quest VR + Android 1.0.19-test38

Private test candidate, Android version code 49. The accepted public baseline
remains 1.0.18. This candidate is not a public release or headset acceptance.
The owner requested packaging the current work because of usage limits; the
remaining work and testing are recorded in TEST38-DELIVERY-STATUS.md.

## Installation

Install the Quest APK on the headset or the Android APK on the phone over the
matching existing app. Do not uninstall to update. Both use the existing signing
identity and remain separate apps. Keep a backup of saves/settings. Import your
own supported game data; no maps, ISOs or XISOs are included.

## Main changes

- All gun classes now have scope adjustment profiles, including SPNKR. These
  adjust authored zoom views; they do not add zoom to weapons that lack it.
- Vehicle/turret reticle previews no longer apply enemy target attraction.
  Normal handheld reticles and native projectile behavior are preserved.
- The supplied USA Original, Rev 1 and Rev 2 images contain identical 24-map
  sets and passed the production importer. This finding applies to those three
  images, not every regional, custom or corrupt image.
- Campaign compatibility extends to networks 15-24. An explicit optional legacy
  12-14 setting reproduces their old presentation behavior, with warnings about
  missing host allegiance updates. Hosting stays network 24; original-map PvP
  remains 11-24, and Custom Edition maps require 23/24.
- Optional physical reloads, object/NPC interaction, ragdolls, impact damage,
  contact refinements, virtual vehicle controls and parkour are described below.
  Existing Android touch/gamepad controls and Safe geometry defaults remain.

## Manual reload: off by default

Enable **MANUAL RELOAD** in VR Controls. This is a solo feature; online games
retain native reload. **SHOULDER POUCH** and **HIP POUCH** are separate toggles,
both on initially. Pouches follow the free-hand side automatically: left with
a right-hand gun, right with a left-hand gun.

Grip the magazine, pull it clear and release. Grip near an enabled pouch for a
replacement, align it with the weapon socket and release to seat it. A short
pulse confirms alignment; seating takes 0.10 seconds. Then finish as follows:

| Weapon | Reload finish |
| --- | --- |
| Assault rifle / sniper | Pull and release operating handle relative to gun |
| Pistol | Pull and release slide |
| Shotgun | Insert one shell, then pull/release pump; one round per cycle |
| SPNKR | Grip/release the push-bar latch after insertion |
| Flamethrower | Grip/release canister cover after insertion |
| Needler | Insert the authored crystal bundle; no invented bolt |

The normal reload button cancels the physical sequence and uses native reload.
Ammo transfers through native rules at completion. Battery weapons retain their
native battery/heat behavior. Unsupported custom/non-player reload rigs retain
native behavior. See MANUAL-RELOAD.md for exact profiles and cancellation rules.

## Hand contact and grabbing

**CONTACT VOLUMES** uses cached collision volume probes; OFF retains ray probes.
**CONTACT LOG** enables aggregate diagnostics. **CONTACT LIMIT** bounds visual
hand separation: an excessively obstructed arm/hand is hidden coherently and
restored as the controller returns, rather than moved through a wall. Detached
reload parts and held world/NPC surfaces participate in finger contact.

**WORLD GRAB** is off by default. With a free hand, press grip close to a valid
surface. Two hands can share an object or hold separate ones. Intentional
release throws; tracking loss or cancellation does not. Loose weapons/equipment
retain native physics. Eight audited loose scenery tags use collision-derived
bounding boxes and constrained movement; structural scenery is not made movable.
See VR-LOOSE-PROPS.md for the exact list and conservative-collision behavior.

**NPC GRAB** is off by default. Supported native Grunts, Jackals, Marines and
crew use one-hand handling. Elites, Hunters, Flood combat forms and carriers
require two distinct limb grips for lifting. Living NPCs and identifiable
corpses use articulated poses. Released bodies settle; living NPCs recover with
clearance checks and available native get-up animations. Dead bodies are never
revived. **ACTIVE RAGDOLLS** selects a bounded pool of 1-4.

**IMPACT DAMAGE**, **IMPACT SPEED** and **IMPACT CAP** control collision-based
physical damage. Only explicitly handled objects are tracked; authority remains
with the local game/co-op host. Native damage rules and normal falling damage
remain in place. Scripted/named, seated, invalid or unsupported entities are
protected rather than blindly converted into physics objects.

## Co-op physical interactions

The host must enable **VR INTERACTIONS** in Server Setup. New interaction
capabilities must negotiate successfully with the required peers. Enhanced physical interactions support at most four remote peers; above that limit they fall back to native behavior without reducing ordinary co-op capacity. Compatible
Quest clients send grip intent; Android or Quest hosts validate it and simulate
the objects. NPC poses, planted hand contacts and collision poses are synchronized.
No client may submit authoritative damage or arbitrary object transforms.

Competitive multiplayer and incompatible/mixed co-op sessions retain native
behavior for these custom interactions. Ordinary co-op and VR avatar rendering
remain separate features. Manual reload and parkour remain solo-only in this
candidate. Actual multi-device interaction testing is still required.

## Closer contact

**GRAB CONTACT** defaults to AUTO, following world/NPC grabbing. **BODY RADIUS**
defaults to 25 cm and offers 18-60 cm, never exceeding the native maximum.
ON enables it independently; OFF uses the previous CLOSE CONTACT policy.
This is solo-only. Expansion waits for free space; NPC hitboxes and solid world
collision are not removed.

## Virtual vehicle controls

Enable **PHYSICAL HANDLES** for first-person driving. Warthog, Ghost, Scorpion
and Banshee profiles have distinct virtual wheel/yoke appearances, native seated
anchors and per-vehicle reach, lateral, height and size adjustments. Grip near
a control, turn it to steer, then release for the normal selected steering mode.
Stick throttle remains; Banshee pitch retains its selected normal aim source.
**VIRTUAL WHEEL** controls visibility independently of grabbing.

Physical vehicle controls are off by default. The wheel is visible when that mode is enabled unless its separate visibility option is disabled. Third-person vehicles with right-hand steering
remain the default. Passengers/turrets keep their existing controls. First-person
vehicle comfort still needs refinement; third-person remains recommended.

## Parkour: off by default

**WALLRUN**, **WALLJUMP** and **GRIP CLIMB** are independent solo-only options.
Run/jump against a vertical wall to wallrun. A fresh jump input gives a
look-directed outward leap. Grip a static wall and pull to climb; release after
an arm pull to launch. Speed, duration and launch settings are adjustable.
Native capsule collision remains active. Moving objects, characters and vehicles
are not climbing anchors. Focus loss, menus, death, seats and state resets cancel
transient ownership.

## Testing and support

Start with ordinary gameplay and new features OFF. Then enable one subsystem
at a time. Headset comfort, real collision scenes, campaign recovery, performance,
checkpoints and live co-op require device testing; automated tests cannot prove
them. See TEST38-DEVICE-CHECKLIST.md and TEST38-DELIVERY-STATUS.md.

Report version, headset/OS, map/data set, solo/host/client role, settings, steps,
launch log and a short video. Never send disc images or signing keys.
DM **@MeWhenINameMyself** on Discord or report in the support server:
https://discord.gg/S9uSCKxKx

The baseline installation/control reference follows in the launcher's offline
guide. These candidate notes take precedence for the new features above.
