"""Test57: every vehicle its own immersive controls (wiring the replay in
test_test38_vehicle_handles.py does not reach).

Owner's Test56 session (2026-10-11 19:56 log, videos 20:05:22 and 20:07:02):
the Ghost's controls took a hand every time; the Warthog's, drawn by the model
and grabbed on its rim, never did in 50 seconds of driving with grip held.
The Warthog now draws its own wheel (hidden by VIRTUAL WHEEL, it is taken on
the model's wheel exactly); the Scorpion (and a Wraith) gets one drive stick,
the Banshee's flight bar also slides to turn; new VEHICLES rows switch the
highlight, the steering haptics and the slide off. The assault rifle's
"frame safety button" was checked against the stock animations and left as
authored (idle, moving and firing hold it where it is drawn).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
handles = read("port/linux/game/vr_vehicle_handles.h")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")

# one profile per vehicle; the Wraith (where a map lets a player drive it) is a tank
assert '{{"warthog",0},{"ghost",1},{"scorpion",2},{"wraith",2},{"banshee",3}}' in handles
assert '{{"steering wheel",0.08f},{"handlebar",0.04f},{"drive stick",0.05f},{"flight bar",0.04f}}' in handles
assert "contact_radius+=vr_wheel_profiles[vr_wheel.kind].extra-0.04f;" in handles
# the Ghost's reach is what it was (palm + 4 cm): its profile adds nothing
assert '{"handlebar",0.04f}' in handles

# the Warthog's wheel: drawn 2.5 cm in front of the model's; hidden, on it
assert "if(vr_wheel.kind==0 && vr_wheel.wheel_front)" in handles
assert 'vr_wheel.wheel_front=config_boolean("vr.vehicle_wheel_visible");' in handles
assert "if(out>=0.4f*radius && out<=radius) return fabsf(along);" in handles, "the wheel's face takes a hand"

# a squeeze that takes nothing is logged with the distance
assert 'not taken by hand %d: %.1f cm away (reach %.1f cm)%s' in handles

# the new rows, all on by default
for key, label in (("vr.vehicle_control_glow", "CONTROL GLOW"), ("vr.vehicle_steer_haptics", "STEER HAPTICS"),
                   ("vr.vehicle_banshee_slide", "BANSH SLIDE")):
    assert '{ "%s", _config_boolean, "true",' % key in config, key
    assert '{ "%s", "%s", _vr_setting_boolean, 2, { { "OFF", "false" }, { "ON", "true" } } },' % (label, key) in menu, label
assert "&& vr_wheel.glow" in handles and "|| !vr_wheel.steer_haptics" in handles and "vr_wheel.kind==3 && vr_wheel.slide" in handles

# Test57b: the Warthog's wheel from its node in the world (never the marker's
# local node_matrix, which put it at the map's origin), the stick and bar in
# front of the chest, anything over a metre away or without markers too
assert "center=markers[0].node_matrix.position" not in handles
assert "center=nodes[markers[0].node_index].position;normal=nodes[markers[0].node_index].up;" in handles
assert "if(kind==2 || kind==3 || !contacts || !(head_gap<=1.0f)) {" in handles
assert 'anchored at %s, %.0f cm from the eyes' in handles
# Test57b: the mounted guns' reticle follows the head between ticks and starts
# on the vehicle as drawn while the immersive controls steer
render = read("port/linux/game/vr_render.c")
reticle = render[render.index("Test57b: with IMMERSIVE VEHICLE controls the head aims"):]
reticle = reticle[:reticle.index("scale_vector3d(&direction, distance, &vector);")]
assert "if (vr_vehicle_handles_head_aims() && vr_render.hud_from_head)" in reticle
assert "if (cosine > 0.98f && sine > 0.00001f)" in reticle and "rotate_vector_about_axis(&direction, &axis, sine, cosine);" in reticle
assert "origin.x += drawn[0].position.x - simulated[0].position.x;" in reticle
assert "static int vr_vehicle_handles_head_aims(void)" in handles and "vr_vehicle_steering_split()" in handles

# Test57b: TANK HATCH, off by default (the owner likes the tank view as it is)
assert '{ "vr.vehicle_tank_hatch", _config_boolean, "false",' in config
assert '{ "TANK HATCH", "vr.vehicle_tank_hatch", _vr_setting_boolean, 2, { { "OFF", "false" }, { "ON", "true" } } },' in menu
assert "vr_seat_steady_anchor(anchor);\n\t\tvr_vehicle_hatch_lift(anchor);\n\t\tvr_vehicle_adjust_anchor(anchor);" in render
hatch = render[render.index("static void vr_vehicle_hatch_lift("):]
assert 'config_boolean("vr.vehicle_tank_hatch")' in hatch and 'strstr(name, "scorpion")' in hatch

# ordinary vehicle controls: nothing runs without IMMERSIVE VEHICLE
enabled = handles[handles.index("static int vr_vehicle_handles_enabled"):]
enabled = enabled[:enabled.index("}") + 1]
assert 'config_boolean("vr.vehicle_handles")' in enabled
print("PASS: Test57 vehicles (per-vehicle profiles incl. Wraith, Warthog virtual wheel and hidden alignment, face grab, miss log, CONTROL GLOW / STEER HAPTICS / BANSH SLIDE rows, IMMERSIVE VEHICLE gate)")
