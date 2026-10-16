"""Test72: the fist combat and grab refinement pass (the owner's 2026-10-15
17:32 session: halo_log_2026-10-15_17-32-06-470_15017.txt and its video).

What the log and the frames showed, and what each check below holds:
- SHADE: three punches on a Shade (e28d001e) each killed the player 0.07 to
  0.54 s later (the "button sprint exited" of his death); the frames show
  the Shade turning over into him. units.c shoved a struck vehicle along the
  hand's sweep (a hand drawn back out of the hull pointed it at him) and up
  to 1.5x the game's own melee shove. Now: the game's strength at most,
  level, away from the striker; a hand drawn back out of an object strikes
  nothing; no blow points back at the player. Not an immunity.
- RIDERS: a blow on a seated rider went to its vehicle, and fist combat
  never took a seated enemy (a Shade's gunner was "no enemy within 8 m").
  Riders take their own blows, are targets (struck over their hull), are
  never knocked or shoved out of their seats, and are measured where they
  are in the world (a rider's object.position is its seat's).
- HELD ENEMY: an Elite held in one hand and punched with the other: each
  punch lunged 3 to 6 m to where its unit was grabbed and the grab cancelled
  it. Now the blow lands where the hand holds the body.
- ACQUISITION: refusals inside reach and cone (3 and 28 degrees) and many
  50 to 90 degrees off the gaze: one judgement (combat_intent) from the gaze
  and the fist's own way in 3D, forgiving within 1.6 m; visible at the
  chest or the head; the refusal's reason logged.
- LUNGE: 12 m by default (the owner's 8 m was the old maximum), up to 15;
  a dash to 14 m/s; a leap from a metre's lunge, 30 cm by default, higher
  to an enemy above; 1.6 m on the ground, 4 m in the air; already backing
  off as a punch is thrown no longer cancels its lunge.
- HIT ASSIST: the fist's stroke against every node of the drawn skeleton
  (head, chest, arms, legs), 50 cm by default (the owner's old maximum).
- GRAB ASSIST: 30 cm by default, to 50 (the owner's 25 cm was the old
  maximum and the clamp); bodies tried nearest first.
- Defaults move once for values still at the old defaults; a player's own
  value stays.
- FREEFLOW: the combo counts blows, switches to another enemy, parries,
  blocks, grabs and knockdowns, in a 3 s window; a parry pulses twice; the
  combo's damage bonus kept modest (5% a hit, 40% at most); melee
  durability by difficulty .80/1.0/1.30/1.60; COMBO DISPLAY (optional).
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
units = read("source/units/units.c")
extra = read("port/linux/game/vr_extra_interaction.c")
extra_h = read("port/linux/game/vr_extra_interaction.h")
npc = read("port/linux/game/vr_npc_interaction.c")
config = read("port/linux/src/port_config.c")
frame = read("port/linux/src/vr_frame.c")
menu = read("port/linux/game/vr_menu.c")


def function(text, signature):
    start = text.rindex(signature)  # the definition (after any prototype)
    depth, i = 0, text.index("{", start)
    while True:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return text[start:i + 1]
        i += 1


# ---- the Shade: the shove and the blow's direction
probe = function(units, "static boolean unit_vr_impact_melee_target(\n\tlong unit_index,\n\treal_point3d const *from,")
apply = function(units, "static boolean unit_vr_impact_melee_apply(\n\tlong unit_index,\n\tstruct collision_result const *struck,")
assert "!hit && dot_product3d(sweep, &sight) > 0.0f" in probe  # a hand drawn back strikes nothing
assert "return unit_vr_impact_melee_apply(unit_index, &collision, sweep, scale, weapon_hand, expected_target);" in probe
shove = apply[apply.index("_object_type_vehicle)\n\t{"):]
shove = shove[:shove.index("vehicle_accelerate(hit_object_index, &acceleration);")]
assert "0.035f * (scale < 1.0f ? scale : 1.0f)" in shove  # the game's own strength at most
assert "&unit->object.position, &vehicle->object.bounding_sphere_center, &acceleration" in shove  # away from the striker
assert "acceleration.k = 0.0f;" in shove  # level
assert "direction.i" not in shove  # never along the hand's sweep
assert "dot_product3d(&direction, &away) < 0.25f" in apply and "direction = away;" in apply
# the stock melee it matches
stock = units[units.index("best_object_definition->object.acceleration_scale * 0.035f;") - 600:]
assert "unit->unit.aiming_vector.i" in stock[:1200]
# no immunity: the striker's own unit is not exempted anywhere new
assert "_object_cannot_take_damage_bit" not in apply

# ---- riders
assert "hit_object->object.type != _object_type_biped &&\n\t\t\thit_object->object.parent_object_index != NONE" in apply
assert "expected->object.parent_object_index != hit_object_index" in apply
assert "static boolean extra_seated(struct unit_datum const *u)" in extra
assert "(u->object.parent_object_index==NONE||extra_seated(u))" in extra
assert "unit_get(target)->object.parent_object_index==NONE&&\n           vr_npc_interaction_knock(" in extra
assert "if(unit_get(target)->object.parent_object_index==NONE)biped_accelerate(target,&shove);" in extra
assert "object_get_origin(object,&origin);" in extra
# every read of a target's position goes through its world origin
for line in extra.splitlines():
    if "object.position" in line and "unit_get(" in line:
        assert re.search(r"unit_get\(unit\)->object\.position", line) or "rider's" in line, line
assert "hit.object_index==unit_get(target)->object.parent_object_index" in extra  # seen over its hull

# ---- the held enemy
assert "boolean unit_vr_combat_strike_point(long unit,long target,real_point3d const *point,real_vector3d const *direction,real scale);" in extra_h
strike_point = function(units, "boolean unit_vr_combat_strike_point(\n\tlong unit_index,")
assert "collision.object_index = target_index;" in strike_point and "unit_vr_impact_melee_apply(" in strike_point
assert "vr_npc_interaction_contact(h,&object,&node,point)&&object==target" in extra
engage = function(extra, "static void combat_engage(long unit,long target,int hand,boolean counter,real_point3d const *fist)")
assert "if(held>=0&&held!=hand){" in engage and "extra.strike_held=1;" in engage
held_block = engage[engage.index("if(held>=0&&held!=hand){"):]
assert held_block.index("return;") < held_block.index("approach_until")  # no lunge
assert "if(!extra.strike_held)extra.strike_pending=0;" in extra  # the grab keeps the blow on its body
assert "unit_vr_combat_strike_point(unit,target,&at,&along,extra.strike_scale)" in extra

# ---- acquisition
intent = function(extra, "static int combat_intent(")
assert "boolean near=distance<=1.6f*units;" in intent
assert "facing>=.64f||(thrown>=.75f&&facing>=.17f)||(near&&facing>=0.0f&&thrown>=.2f)" in intent
assert "if(!near&&level_punch)" in intent  # no 'behind' refusal close in
punch = function(extra, "int vr_combat_punch(long unit,int hand,real_point3d const *point,real_vector3d const *sweep)")
assert "level_punch=whole>.0001f&&flat>=.5f*whole" in punch  # an uppercut's level part is not used
assert punch.count("combat_intent(&gaze,&stroke,&level,level_punch,point,&chest,") == 2  # counters and punches
assert "extra_visible(unit,it.index,&head,&chest)||extra_visible(unit,it.index,&head,&target_head)" in punch
assert "nearest_reason" in punch and "neither looked at nor punched at" in punch
assert "facing>=.70f" not in punch

# ---- the lunge
assert 'extra_bound("vr.combat_lunge_reach",12.0f,0.0f,15.0f)' in extra
assert "extra.lunge_hop=extra.lunge_metres>=1.0f&&combat_lunge_hop()>0;" in extra
assert "MIN(rise+.25f,1.2f)" in extra and "combat_lunge_hop()*PIN(metres/4.0f,.5f,1.0f)" in extra
assert "b->unit.throttle.i<-.5f&&!extra.lunge_started_back" in extra
assert "(airborne?4.0f:1.6f)*units" in extra
assert 'extra_bound("vr.combat_lunge_hop",.30f,0.0f,.45f)' in extra

# ---- hit assist on the skeleton
assert 'extra_bound("vr.combat_hit_assist",.50f,0.0f,.70f)' in extra
reach = function(extra, "static real combat_body_reach(long target,")
assert "for(short n=0;n<count;n++)" in reach and "combat_segment_distance(from,to,&nodes[n].position)" in reach
assert "near=combat_body_reach(target,&from,&to,&node);" in engage

# ---- grab assist
assert 'npc_setting("vr.npc_grab_assist",0.30f,0.0f,0.50f)' in npc
assert "#define NPC_GRAB_CANDIDATES 32" in npc
assert "while(at>0&&order_gap[at-1]>gap)" in npc and "candidate=unit_try_and_get(candidate_index);" in npc
loop = npc[npc.index("for(int ordered=0;ordered<order_count;ordered++)"):npc.index("if(!acquired&&eligible_count)")]
assert "it.index" not in loop

# ---- defaults, once, keeping a player's own
for key, value in (("vr.combat_lunge_reach", "12.0"), ("vr.combat_hit_assist", "0.50"), ("vr.combat_lunge_hop", "0.30"),
                   ("vr.npc_grab_assist", "0.30"), ("vr.combat_combo_display", "true")):
    assert re.search(r'\{ "%s", _config_\w+, "%s",' % (re.escape(key), re.escape(value)), config), key
assert '"vr.test72_combat_defaults_applied", _config_boolean, "false"' in config
migration = frame[frame.index('if (!config_boolean("vr.test72_combat_defaults_applied"))'):]
migration = migration[:migration.index('config_write_boolean("vr.test72_combat_defaults_applied", 1);')]
for key, old, new in (("vr.combat_lunge_reach", "8.0", "12.0"), ("vr.combat_hit_assist", "0.30", "0.50"),
                      ("vr.combat_lunge_hop", "0.15", "0.30"), ("vr.npc_grab_assist", "0.15", "0.30")):
    assert '{ "%s", %s, %s },' % (key, old, new) in migration, key
assert "fabs(config_real(moves[index].key) - moves[index].old_value) < 0.001" in migration
assert 'return on ? "0.30" : "0.10";' in menu and "assist >= 0.145f" in menu  # (a player's 15 cm or more kept)
# the menus offer the new defaults and ranges
assert '{ "12 M", "12" }, { "15 M", "15" }' in menu
assert '{ "50 CM", "0.50" }, { "60 CM", "0.60" }, { "70 CM", "0.70" }' in menu
assert '{ "NORMAL", "0.30" }, { "HIGH", "0.45" }' in menu
assert '{ "30 CM", "0.30" }, { "40 CM", "0.40" }, { "50 CM", "0.50" }' in menu

# ---- freeflow
assert "#define COMBAT_COMBO_WINDOW (3*TICKS_PER_SECOND)" in extra
for why in ('"a grab"', '"a knockdown"', '"a parry"', '"a block"'):
    assert "combat_combo_add(1,%s)" % why in extra, why
assert "extra.combo_last_target!=target" in extra  # a switch counts
assert "(1.0f+.05f*(real)MIN(extra.combo-1,8))" in extra and ".08f*(real)MIN(extra.combo-1,10)" not in extra
assert "extra.parry_echo_tick=now+3;" in extra and "extra_pulse(0,.85f,.05f);extra_pulse(1,.85f,.05f);" in extra
assert "static real const d[]={.80f,1.0f,1.30f,1.60f}" in extra
# the display: optional, from two in a row, the HUD's blue, gold at a takedown
display = function(extra, "static int combat_combo_render(long unit,real_point3d const *camera)")
assert 'config_boolean("vr.combat_combo_display")||extra.combo<2' in display
assert "combat_ui_digit(" in display and "COMBAT_SPECIAL" in display
assert '#define VR_IMMERSION_COMBAT_COMBO { "COMBO DISPLAY", "vr.combat_combo_display"' in menu
assert menu.count("VR_IMMERSION_COMBAT_COMBO,") == 2  # its page and IMMERSION
assert '{ "FIST OPTIONS", 5 }' in menu

print("PASS: Test72 fist combat: the Shade shove (game strength, level, away; no pull-back blow), riders struck and "
      "targeted where they are, the held enemy struck where held, 3D intent with close-range forgiveness, 12 m leaping "
      "lunges, skeleton hit assist, nearest-first 30 cm grabs, defaults moved once, freeflow and COMBO DISPLAY")
