#!/usr/bin/env python3
"""Verify holster-only haptics are optional and don't steal reload pouches."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FRAME = (ROOT / "port/linux/src/vr_frame.c").read_text()
CONFIG = (ROOT / "port/linux/src/port_config.c").read_text()
MENU = (ROOT / "port/linux/game/vr_menu.c").read_text()
RELOAD = (ROOT / "port/linux/game/vr_manual_reload.c").read_text()


def extract_function(source, marker):
    start = source.index(marker)
    brace = source.index("{", start)
    depth, end = 1, brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


setting = re.search(
    r'\{\s*"vr\.holster_haptics",\s*_config_boolean,\s*"(true|false)"', CONFIG
)
assert setting and setting.group(1) == "true", "new players keep holster feedback enabled by default"
assert '"HOLSTER HAPTICS", "vr.holster_haptics", _vr_setting_boolean' in MENU

anchors = FRAME[FRAME.index("static const float holster_places"):FRAME.index("static const char *const holster_names")]
for anchor in ["-0.18f, -0.15f, 0.15f", "0.18f, -0.15f, 0.15f",
               "-0.22f, -0.62f, 0.00f", "0.22f, -0.62f, 0.00f"]:
    assert anchor in anchors, "left/right shoulder and hip weapon holsters remain present"

holster_region = FRAME[FRAME.index("/* holsters (vr.holsters)"):FRAME.index("/* physical weapons (vr.weapons", FRAME.index("/* holsters (vr.holsters)") )]
assert "vr.frame.hand_valid[w]" in holster_region and "vr.grip_pressed[w]" in holster_region
assert "vr.in_holster = zone != 0" in holster_region
assert holster_region.count("holster_haptic(w,") == 2
assert "vr_haptic(" not in holster_region, "every holster-only pulse uses the optional wrapper"
physical_region = FRAME[FRAME.index("/* physical weapons (vr.weapons"):FRAME.index("/* the off hand's grip", FRAME.index("/* physical weapons (vr.weapons"))]
assert physical_region.count("holster_haptic(w,") == 2, "draw and stow confirmations obey the toggle"
assert "vr_haptic(w, 0.5f, 0.05f)" in physical_region, "dropping away from a holster retains normal feedback"

# Manual reload deliberately owns only the free hand and mirrors its pouch to
# that side. Holster zones are evaluated on the weapon hand, so the hands and
# their switching/reload actions remain independent even when both use hip or
# shoulder regions. Reload feedback stays under the master HAPTICS strength.
assert "hand_index = 1-vr_weapon_hand()" in RELOAD
assert "vr_mr_pouch_side(hand_index)" in RELOAD
assert 'config_boolean("vr.reload_hip"),config_boolean("vr.reload_shoulder")' in RELOAD
assert "vr_haptic(hand_index" in RELOAD and "holster_haptic" not in RELOAD

wrapper = extract_function(FRAME, "static void holster_haptic(")
test = r'''
#include <assert.h>
#include <string.h>
static int enabled, calls, last_hand;
static float last_amplitude, last_seconds;
static int config_boolean(char const *key) { assert(strcmp(key,"vr.holster_haptics")==0); return enabled; }
static void vr_haptic(int hand, float amplitude, float seconds) { calls++;last_hand=hand;last_amplitude=amplitude;last_seconds=seconds; }
WRAPPER
int main(void) {
  holster_haptic(1,.45f,.05f); assert(calls==0);
  enabled=1;holster_haptic(1,.45f,.05f);
  assert(calls==1&&last_hand==1&&last_amplitude==.45f&&last_seconds==.05f);
  enabled=0;holster_haptic(0,.6f,.06f);assert(calls==1);
  return 0;
}
'''.replace("WRAPPER", wrapper)
with tempfile.TemporaryDirectory(prefix="holster-haptics-") as temp:
    source = Path(temp) / "check.c"
    output = Path(temp) / "check"
    source.write_text(test)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(output)], check=True)
    subprocess.run([str(output)], check=True)

print("PASS: holster buzzes are independently optional; holster actions, free-hand magazine pouches and reload haptics stay separate")
