# Test56 device checks

Turn **CONTACT LOG** on (VR Settings → BODY) and keep the log from
Download/HaloCE after each session. Tell us which log and video go with each
result.

1. **Ragdolls, every species** (DEATH RAGDOLLS on): kill Elites, Grunts,
   Jackals, Hunters, Marines and Flood (combat forms, carriers). Bodies should
   fall loosely, knees and elbows bending only the right way, and lie still
   within a second or two, without twitching or sliding. Log:
   `VR NPC: death ragdoll ... kick_mps= push_mps= explosion=`; there should be
   no `settle still pending` lines.
2. **Shot reactions**: head shot (snaps back), leg shot (buckles), side shot
   (turns), sniper (hard), melee (shove), grenade (thrown away and up), a body
   next to a wall (falls into it).
3. **Getting up**: grab a living Grunt or Elite, drop it: it gets up within 1
   second (`VR NPC: recovery`). Try NPC RECOVERY at 0.25 s and 1 s.
4. **Vehicles, IMMERSIVE VEHICLE on**: Ghost, Warthog, Scorpion, Banshee.
   Hands left turns left, right turns right. Steering with both hands and with
   either hand alone. The guns and the Scorpion turret follow your head. Log:
   `immersive <vehicle> steering from the gripped controls`.
5. **Warthog wheel**: grip anywhere on the rim. The hands stay on it as it
   turns. Feel the grab, the ticks, the full-lock buzz and the release.
6. **Smooth driving**: no stutter in the view or the hands while driving.
7. **Hands grip**: fingers close round the bar, sticks, yoke and wheel, and
   open on release.
8. **Ghost view**: if the hood blocks the view, try GHOST UP / GHOST FWD
   (VR Settings → VEHICLES) and tell us the values.
9. **IMMERSIVE VEHICLE off**: drive each vehicle as before (no change).
10. **Throws** (THROW 2X): throw a Grunt, a crate and a weapon with a flick
    (`VR NPC: throw speed_mps`). Throw a body at an Elite and at a Warthog: it
    shoves it (`VR impact`).
11. **LIFT**: lift a Shade at SPARTAN (as in Test55) and at IRON.
12. **Elites and Hunters**: one hand holds and drags them (no lift). Add the
    second hand: lift, carry, throw. Let go with one hand: the other keeps it.
    Grunts, Jackals and Marines lift with one hand.
13. **CHARGE GRAB**: pistol slide and assault rifle handle at 4 cm, then 8 cm.
14. **Log**: no repeated `heavy hold one hand` lines.
15. **Lobby (OpenCE Build 190 fix)**: host a game, have a player join or leave
    during the countdown: it keeps counting, and they join in progress.
16. **Regression**: voice in a lobby and a match; join a network-26 server;
    co-op host and client; wall run and wall jump; manual reload; holsters,
    scopes, reticles, sprint, remapped buttons, left-handed play; flat Android
    launch, join and touch controls.
