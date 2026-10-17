"""Test72: a player's wireless controller on Android: "in game only the face
and trigger buttons work. Dpad and sticks dont. The controller tester in the
launcher detects the gamepad."

Buttons reach SDL at the activity (SDLActivity.dispatchKeyEvent); sticks and
the hat (most controllers' D-pad) only through SDL's surface listener, which
takes an event as a joystick's only when its source is exactly
SOURCE_JOYSTICK (some Bluetooth controllers report joystick and gamepad at
once: their motion was taken for a mouse's and dropped) and only while the
surface has the focus. HaloActivity now hands a joystick-class motion event
of an SDL joystick device to SDL itself, logging the device once.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
activity = (ROOT / "port/android/app/src/main/java/com/halo/decomp/HaloActivity.java").read_text(encoding="utf-8")

body = activity[activity.index("public boolean dispatchGenericMotionEvent(MotionEvent event) {"):]
body = body[:body.index("\n    }\n")]
assert "(event.getSource() & android.view.InputDevice.SOURCE_CLASS_JOYSTICK) != 0" in body  # any joystick class, not ==
assert "org.libsdl.app.SDLControllerManager.isDeviceSDLJoystick(event.getDeviceId())" in body
assert "org.libsdl.app.SDLControllerManager.handleJoystickMotionEvent(event);\n                return true;" in body
assert "catch (RuntimeException notReady)" in body
assert body.rstrip().endswith("return super.dispatchGenericMotionEvent(event);")
assert "if (motionDevicesLogged.add(event.getDeviceId()))" in body and '"Controller motion: %s (sources 0x%x' in body

# the source tests, worked through (android.view.InputDevice's constants)
SOURCE_CLASS_JOYSTICK = 0x10
SOURCE_JOYSTICK = 0x01000010
SOURCE_GAMEPAD = 0x00000401
SOURCE_DPAD = 0x00000201
SOURCE_MOUSE = 0x00002002
combined = SOURCE_JOYSTICK | SOURCE_GAMEPAD
assert combined != SOURCE_JOYSTICK                       # SDL's own test missed it
assert combined & SOURCE_CLASS_JOYSTICK                  # this takes it
assert SOURCE_JOYSTICK & SOURCE_CLASS_JOYSTICK           # the usual one still taken
assert not (SOURCE_MOUSE & SOURCE_CLASS_JOYSTICK) and not (SOURCE_GAMEPAD & SOURCE_CLASS_JOYSTICK)  # mice, keys: SDL's path
print("PASS: Test72 controller: sticks and hat to SDL at the activity, whatever the event's combined source or the "
      "view focused; the device logged once")
