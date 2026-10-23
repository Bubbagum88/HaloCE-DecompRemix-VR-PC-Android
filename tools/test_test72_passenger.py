"""Test72: vehicle passengers aim their own gun with the tracked hand.

The report (the owner, from players riding the Scorpion in AOTCR, and the
Warthog's passenger seat too): "you can't aim anymore. Arms lock to head
view and the crosshair isn't accurate". vr_vehicle_aim_source gave every
passenger the head's aim ("native passenger head aim"): a 3DoF gun. Now, in
the first-person seat view, a passenger's source is the on-foot one (1):
vr_aim sets the hand's aim, the shot starts at the hand (hand_origin) and
the reticle follows the hand's ray, the head looks freely, two hands and
LEFT-HAND MODE as on foot, AIM = HEAD still respected (vr.hand_aim). The
third-person seat view (no hands drawn) keeps the head. Drivers and gunners
keep their own choice (vr.vehicle_steering, vr.turret_aim). Nothing in the
network's messages changes: the facing a client sends is the aim, as on foot.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
render = (ROOT / "port/linux/game/vr_render.c").read_text(encoding="utf-8")
frame = (ROOT / "port/linux/src/vr_frame.c").read_text(encoding="utf-8")

source = render[render.index("static int vr_vehicle_aim_source(void)"):]
source = source[:source.index("\n}\n")]
passenger = source[source.index("if (role == 3)"):source.index("else\n\t{\n\t\tmode = role == 1")]
assert "if (vr_first_person_vehicles())" in passenger
first_person = passenger[passenger.index("if (vr_first_person_vehicles())"):passenger.index("else")]
assert "source = 1;" in first_person
assert "source = 0;" in passenger[passenger.index("else"):]
assert "native passenger head aim" not in render
assert 'source == 1 ? "the weapon hand"' in source
# role 1/2 untouched
assert "mode = role == 1 ? vr_vehicle_steering() : vr_turret_aim();" in source
# source 1 is the on-foot path in vr_aim: the hand's tracked aim when AIM is HAND
assert "else if (vr.hand_aim && hand_may_aim == 1 && hand_forward(aim))\n\t\tvr.hand_aiming = 1;" in frame
# the hand's shot origin follows vr_hand_aiming, seated or not
assert "if (unit_index != NONE && vr_hand_aiming() && game_connection() == _game_connection_local)" in render
# a passenger's gun stays drawn (only a driver or gunner puts it away)
assert "return vr_render.cinematic_view || (vr_seat_view() && (vr_render.seat.driver || vr_render.seat.gunner));" in render

# Test73 (the owner: "fix the passenger seats not being in full 6dof"): a passenger's head reaches 0.8 m from the
# seat's origin (test_test32_vehicles runs it), and once seated (1.5 s: the enter animation) its eyes are held in the
# vehicle's frame, so only the head moves them; never the third-person passenger track in the headset
assert "#define SEAT_PASSENGER_REACH 0.8f" in frame
assert ("float reach = vr.seated && vr.vehicle_seat.origin_valid && vr.vehicle_seat.role == 0 ?\n"
        "\t\t\tSEAT_PASSENGER_REACH : HEAD_REACH;") in frame
assert "#define VR_PASSENGER_SETTLE_SECONDS 1.5" in render
assert "boolean passenger = !vr_render.seat.driver && !vr_render.seat.gunner;" in render
assert ("(vr_vehicle_handles_steady() ||\n\t\t\t(passenger && now >= steady.entered && now - steady.entered > "
        "VR_PASSENGER_SETTLE_SECONDS)))") in render
assert "\t\t\tsteady.entered = now;" in render
camera = (ROOT / "port/linux/game/passenger_camera.c").read_text(encoding="utf-8")
guard = camera[camera.index("static struct unit_seat const *reference_seat("):]
assert guard.index("#ifdef HALO_VR\n\t(void)local_player_index;\n\t(void)vehicle_index;\n\treturn NULL;\n#endif") < \
    guard.index('config_boolean("display.passenger_third_person")')
# (the role passed for a passenger is 0: driver 1, gunner 2)
assert "vr_render.seat.driver ? 1 : vr_render.seat.gunner ? 2 : 0);" in render

print("PASS: Test72 passengers aim the gun in hand (first-person seat view), head aim kept for the third-person view; "
      "drivers and gunners unchanged; Test73: passengers in full 6DOF (0.8 m, eyes held once seated), no "
      "third-person passenger track in VR")
