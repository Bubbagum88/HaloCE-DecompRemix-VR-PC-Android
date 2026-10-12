# Test60 device checklist

Install the Quest APK over Test59 (it keeps your settings). Logs and a short
video of anything that misbehaves help most. An impact writes a `VR impact:`
line to the log.

## Impacts (IMPACT DAMAGE on)

1. Grab a marine and slam it hard onto the ground: it is hurt (enough slams
   kill it).
2. Throw a marine into a wall: it is hurt.
3. Throw a Grunt into an Elite (or a marine into another marine): both are
   hurt, the one hit is knocked back, the thrown body doesn't pass through.
4. Swing a held body around you: it never catches on your own body.
5. A body dropped gently, or sliding along the ground, isn't hurt.

## Settings that come on together

6. In a fresh profile (or with them off), turn on DEATH RAGDOLLS: NPC GRAB,
   NPC RESCUE and IMPACT DAMAGE come on with it.
7. Turn NPC RESCUE off again: it stays off.
8. Turn on NPC GRAB alone: NPC RESCUE and IMPACT DAMAGE come on.
9. With IMMERSIVE VEHICLE off, turn STEER HAPTICS off and on: IMMERSIVE
   VEHICLE comes on.

## Regression

10. Ragdolls, DEATH FORCE, NPCs up within 1 second, vehicles, manual reload,
    network 28 joins, voice chat and the phone build as in Test59.
