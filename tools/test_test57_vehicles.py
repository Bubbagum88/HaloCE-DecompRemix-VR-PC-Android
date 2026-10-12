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

# ordinary vehicle controls: nothing runs without IMMERSIVE VEHICLE
enabled = handles[handles.index("static int vr_vehicle_handles_enabled"):]
enabled = enabled[:enabled.index("}") + 1]
assert 'config_boolean("vr.vehicle_handles")' in enabled
print("PASS: Test57 vehicles (per-vehicle profiles incl. Wraith, Warthog virtual wheel and hidden alignment, face grab, miss log, CONTROL GLOW / STEER HAPTICS / BANSH SLIDE rows, IMMERSIVE VEHICLE gate)")
