"""Test72: a tester's reports (their log: 1.0.37-test70 on a Quest 3S).

1. "physical grenade throwing needs some work": their throws left at 6-7
   m/s (one 12.8) with GRENADE POWER 1.5x already applied, and two grabs
   missed at 23 and 30 cm. The release speed came from the last three game
   ticks (30 a second), weighted to the last, as the hand opened: the hand
   slowing, the release seen up to a tick late. Now the speed is the hand's
   peak over the last tenth of a second (vr_hand_speed, every frame) along
   the ticks' direction; the slot's reach is 15 cm (12).
2. The Shade: "turret viewpoint (too low, cant see over it enough) ... the
   first time i got in i was facing backwards ... Controlled apparently with
   r stick, inverted". Its only seat is a driver's: it took VEHICLE STEERING
   (theirs "stick": the right stick to the game as a gamepad's, its vertical
   by the profile's look setting) instead of TURRET AIM; the view faced the
   turret's base, not its gun; turrets had no view offsets. Now a turret's
   occupant is its gunner, faces the gun on entry, and its view is 25 cm up
   (TURRET UP, FWD, RIGHT). tools/test_test32_vehicles.py runs the seat code.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
extra = read("port/linux/game/vr_extra_interaction.c")
render = read("port/linux/game/vr_render.c")
vehicles = read("source/units/vehicles.c")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")

# ---- grenades
release = extra[extra.index("            if(release){"):extra.index("                extra.hand[h].held=extra.hand[h].samples=0;vr_interaction_release(h,VR_INTERACTION_GRENADE);")]
assert "real tick_speed=magnitude3d(&velocity),peak=vr_hand_speed(h)*units/TICKS_PER_SECOND;" in release
assert "if(tick_speed>.0001f&&isfinite(peak)&&peak>tick_speed)scale_vector3d(&velocity,peak/tick_speed,&velocity);" in release
assert release.index("peak/tick_speed") < release.index('extra_bound("vr.grenade_throw_scale",1,.5f,2)') < release.index("cap=15.0f*units/TICKS_PER_SECOND")
assert "int hover=best>=0&&nearest<=.15f*units;" in extra and "if(press&&best>=0&&nearest<=.15f*units&&" in extra
assert ".12f*units&&vr_interaction_claim" not in extra

# ---- the Shade
assert "boolean vehicle_is_turret(\n\tlong vehicle_index)\n{" in vehicles
assert "return vehicle_specific_definition_get(object->definition_index)->vehicle_type == _vehicle_type_turret;" in vehicles
seat = render[render.index("static void vr_update_seat("):]
seat = seat[:seat.index("\n}\n")]
assert "vr_render.seat.turret = vehicle_is_turret(vehicle_index);" in seat
assert "vr_render.seat.gunner = TRUE;\n\t\t\tvr_render.seat.driver = FALSE;" in seat
assert "real_vector3d aim = vehicle->unit.aiming_vector;" in seat
assert seat.index("vr_render.seat.turret = vehicle_is_turret") < seat.index("vr_render.seat.offset = vr_yaw(&aim) - vr_yaw(&vehicle->object.forward);")
assert 'profile = vr_render.seat.turret ? "turret" : vr_vehicle_profile(tag_get_name(vehicle->definition_index));' in render
assert re.search(r'\{ "vr\.vehicle_turret_up", _config_real, "0\.25",', config)
assert re.search(r'\{ "vr\.vehicle_turret_forward", _config_real, "0\.0",', config)
assert re.search(r'\{ "vr\.vehicle_turret_right", _config_real, "0\.0",', config)
for row in ('{ "VIEW UP", "vr.vehicle_turret_up"', '{ "VIEW FWD", "vr.vehicle_turret_forward"', '{ "VIEW RIGHT", "vr.vehicle_turret_right"'):
    assert row in menu, row
# a second tester: "I couldn't find an option to specifically adjust shade turret or any turret positioning ...
# not sure I want to lower every vehicle": VEHICLES in topics, one a vehicle, TURRETS + SHADE among them
page = menu[menu.index("static struct vr_menu_setting const vr_menu_vehicles[] ="):]
page = page[:page.index("\n};\n")]
rows = [line.strip() for line in page.split("\n")[2:] if line.strip().startswith(('{ "', 'VR_IMMERSION_'))]
sections = menu[menu.index("static struct vr_menu_section const vr_menu_vehicles_sections[] ="):]
sections = re.findall(r'\{ "([^"]+)", (\d+) \}', sections[:sections.index("};")])
assert [name for name, _ in sections] == ["DRIVING", "VEHICLE OPTIONS", "ALL VEHICLES", "WARTHOG", "GHOST", "BANSHEE",
                                          "SCORPION", "PELICAN", "TURRETS + SHADE"]
assert sum(int(count) for _, count in sections) == len(rows) == 57 and all(0 < int(c) <= 8 for _, c in sections)
topic, at = {}, 0
for name, count in sections:
    topic[name] = rows[at:at + int(count)]
    at += int(count)
assert topic["TURRETS + SHADE"][0].startswith('{ "TURRET AIM", "vr.turret_aim"')
assert [r.split('"')[3] for r in topic["TURRETS + SHADE"][1:]] == ["vr.vehicle_turret_up", "vr.vehicle_turret_forward", "vr.vehicle_turret_right"]
for name, key in (("ALL VEHICLES", "all"), ("WARTHOG", "warthog"), ("GHOST", "ghost"), ("BANSHEE", "banshee"),
                  ("SCORPION", "scorpion"), ("PELICAN", "pelican")):
    keys = [r.split('"')[3] for r in topic[name] if r.startswith('{ "VIEW ')]
    assert keys == ["vr.vehicle_%s_%s" % (key, axis) for axis in ("up", "forward", "right")], (name, keys)
assert "VR_IMMERSION_HOG_REACH," in topic["WARTHOG"] and "VR_IMMERSION_TANK_SIZE," in topic["SCORPION"]
assert '{ "VEHICLES", vr_menu_vehicles, NUMBEROF(vr_menu_vehicles),\n\t\tvr_menu_vehicles_sections, NUMBEROF(vr_menu_vehicles_sections) },' in menu
assert "7 + 6 + 8 + 8 + 7 + 7 + 7 + 3 + 4 == NUMBEROF(vr_menu_vehicles) ? 1 : -1];" in menu
assert 'static const char *const vehicles[]={"all","warthog","ghost","banshee","scorpion","pelican","turret"};' in menu

print("PASS: Test72 tester's reports: VEHICLES in topics (TURRETS + SHADE its own); grenade throws at the hand's peak speed, 15 cm grabs; the Shade a turret gunner "
      "(TURRET AIM), facing its gun, its view 25 cm up")
