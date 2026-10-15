# Test70 input conflict audit (Quest Touch, VR layout)

Owner items 12, 26-34. Source of truth: `port/linux/src/vr_frame.c`
(`button_defaults`, `touch_source_down`, `layout_controls`), `vr_menu.c`
(BUTTONS page), `vr_button_remap.h`.

## Remappable actions and their defaults

| Action (BUTTONS row) | Default | Notes |
|---|---|---|
| JUMP | A | gun hand's lower face button |
| USE / RELOAD | B | gun hand's upper; with MANUAL RELOAD it is the magazine release |
| MELEE | R STICK (click) | with physical melee the click zooms instead (Test55) unless another action is on it |
| CROUCH | R DOWN | turning stick held down; never in a seat |
| NEXT WEAPON | Y | other hand's upper |
| GRENADE | X | other hand's lower; a tap throws, a hold switches (NEXT GRENADE = HOLD) |
| NEXT GRENADE | HOLD | inactive while GRENADE is on GRIP (row says so) |
| RETICLE | L STICK (click) | inactive while BUTTON SPRINT owns the click (row says so) |
| PUSH TO TALK | NONE | voice chat |
| BULLET TIME (Test70) | R UP | turning stick pushed up; only when BULLET TIME is on |

"A/B" are the gun hand's buttons and "X/Y" the other hand's when the face
buttons follow the gun hand: always right-handed, and left-handed with MIRROR
CONTROLS AUTO or (Test70) MIRROR BUTTONS AUTO. Stick clicks stay with their
sticks (MIRROR CONTROLS).

## Fixed (non-remappable) inputs

- Triggers: gun hand fires; off hand zooms (or the stick click zooms with
  physical melee); with MANUAL RELOAD INPUT = TRIGGER the free hand's trigger
  works the magazine.
- Grips: hold the gun (PHYSICAL weapons), draw/stow at holsters, climb,
  grab NPCs/props/vehicle controls, fist (Grip + Trigger) for FIST COMBAT and
  DEFLECT SHOTS. With LOCKED weapons the weapon hand's grip is free for a
  button binding (GRIP) except at a holster, and (Test70) never from an empty
  hand.
- Flashlight: the off hand brought to the head, or the off hand's bumper
  input where a controller reports one; both sticks clicked recentre; Menu
  pauses; View held recentres.
- Head and hand gestures (flashlight tap, HUD tap) are positional.
- Physical crouch (head lowered) crouches on foot.

## Contextual ownership (shown in the BUTTONS rows)

| Situation | What changes | Row shows |
|---|---|---|
| BUTTON SPRINT on | the left stick click sprints; actions on it are set aside and restored when sprint is off | `RETICLE: L STICK*` |
| GRENADE on GRIP | holding the grip throws, so NEXT GRENADE = HOLD cannot switch | `NEXT GRENADE: HOLD*` |
| PHYSICAL weapons | the grip holds the gun, so GRIP bindings do nothing | `...: GRIP*` |
| Two actions on one button (BOTH) | both fire from it | `JUMP: A+` |

The hints line explains the marks (`*: OFF FOR NOW`, `+: SHARED`) whenever a
row has one, and while a row is being chosen says whose a taken button is
and what A will do (rows are held to their width by test_test25).
| Physical melee, nothing else on R STICK | R STICK zooms; MELEE is the arms | (Test55; unchanged) |
| Seated | stick clicks sound the horn; R UP/R DOWN off; BULLET TIME off | (vehicle rules unchanged) |

## New features and the audit's conclusions

- **BULLET TIME**: every face button, both stick clicks and R DOWN have a
  default action; the grips are taken by holding, climbing and grabbing in
  every mode; both triggers fire/zoom; both sticks together recentre. The one
  input nothing reads on foot is the turning stick pushed up (turning reads
  only its sideways axis; its vertical reaches the game only as a look that
  the head overrides each frame, as R DOWN's does). R UP is its default,
  remappable; BULLET TIME itself is off by default.
- **SLIDE** reuses existing inputs by design (sprint + crouch: the button's or
  the head's), adds none.
- **Needler shake reload / shake cooling** are motion, add no input; melee
  swings are too long to count as shake strokes.
- **Fist combat, NPC grabbing, climbing** keep their grip/trigger ownership
  (`vr_interaction_claim`): a hand owned by a climb, a grab or a reload is
  never another's.
- **Left-hand mode** never rewrites bindings; MIRROR BUTTONS moves the face
  buttons to the gun hand (custom mappings move with them, unchanged).
- **Remapping** never moves another action: a conflict asks (CANCEL, SWAP,
  CLEAR the other, BOTH). Every gameplay action may be NONE; menu
  navigation never uses these bindings, so no setting can lock the player out
  of the menus. RESET CONTROLS heads and ends the page.

## Disabling features restores prior behavior

- BUTTON SPRINT off gives the left stick click back to what it had
  (Test63; Test70 also restores PUSH TO TALK's bit, which the 8-bit mask
  dropped).
- SLIDE off: a crouch while sprinting crouches as before.
- BULLET TIME off: R UP does nothing; the game's speed is given back (a map
  script's own speed is kept).
- MIRROR BUTTONS OFF: the face buttons as MIRROR CONTROLS has them (before
  Test70).
