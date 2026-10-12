# Test54 device checks

Turn **CONTACT LOG** on (VR Settings → BODY) and keep the log from
Download/HaloCE after each session. Each loop names the log lines that confirm it.

## 1. Manual reload (MANUAL RELOAD on; AR, then pistol, sniper, shotgun)

1. Fire the AR to empty. Press B: the magazine drops (`VR manual reload: ... event=8`).
2. Reach your free hand to your hip or over your shoulder; feel the tick; squeeze
   (`event=3`, magazine in hand).
3. Push it into the well: it locks while held (`event=4`, then `event=9`).
4. Pull the charging handle back and let go (`event=10`, `event=6`); fire.
5. Tactical: fire a few rounds, press B, take a new magazine, insert: the gun is
   ready without charging (`event=6` right after `event=4`; `chambered=1`).
6. MANUAL RELOAD off: B reloads as before. Left-handed: pouches on the right.

## 2. Grabbing NPCs (NPC GRAB on)

1. Walk up to a Marine from behind; palm on his back; squeeze
   (`VR NPC: grabbed ... friendly=1`). No telekinesis: a hand 20 cm away misses.
2. One-hand Grunt: lift, walk, it stays in your hand; throw it at a wall; walk
   over, pick it up again (`release ... throw=1`, later `grabbed` on the same actor).
3. Elite: needs two hands, resists.
4. A body on the floor: touch and squeeze.
5. Reach fast with an open hand: no melee blow/sound.

## 3. Climbing (GRIP CLIMB on)

1. Ordinary wall, then a sloped rock face like the one at 2:43 in your video,
   then a ledge top at chest height (`wall grip ... normal_z=`).
2. Push a hand into the rock and squeeze: it grips the surface.
3. Wall run, wall jump (head-directed) and the climb leap feel as in Test53.

## 4. Ragdolls (DEATH RAGDOLLS on, BODY RETENTION 75)

1. Kill Grunts with grenades and the AR: they fall as ragdolls
   (`VR NPC: death ragdoll`), come to rest, and can be picked up.
2. Throw a body far, look away, come back: it is where it landed.

## 5. Hands and guns

1. Walk and turn holding the AR: the operating handle no longer slides. Check
   the other guns.
2. Slide an open hand along a wall: fingers move smoothly, no contortion.
3. Hold a prop or climb and pull the controller away: the hand stays near
   the controller (no stretched arm).

## 6. Settings

1. IMMERSION and IMMERSION+ pages; NPC GRAB on turns FIST REQUIRED on; all
   grab/climb features off turns it off again (unless set by hand).
2. MAG DEBRIS on turns MANUAL RELOAD on; MANUAL RELOAD off turns MAG DEBRIS off.

## 7. Regression

Voice in a lobby and a match; join a network 26 server; co-op host and client;
sprint, holsters, scopes, reticles, remapped buttons, left-handed play; flat
Android launch, join and touch controls.
