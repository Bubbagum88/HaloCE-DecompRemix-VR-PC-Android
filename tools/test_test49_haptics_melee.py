"""Guard the v1.0.18 weapon haptic path and keep holster switching distinct from melee."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def function(source, name):
    match = re.search(r"^(?:static )?(?:inline )?[\w *]+\b" + re.escape(name) + r"\s*\([^;{]*\)\s*\{", source, re.M)
    assert match, name
    start = source.index("{", match.start())
    depth, end = 1, start + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


render_path = "port/linux/game/vr_render.c"
frame_path = "port/linux/src/vr_frame.c"
render = (ROOT / render_path).read_text(encoding="utf-8")
frame = (ROOT / frame_path).read_text(encoding="utf-8")
released_render = subprocess.check_output(
    ["git", "show", f"v1.0.18:{render_path}"], cwd=ROOT, text=True
)

# Keep the released per-weapon amplitudes/durations, local-player filter,
# shotgun de-duplication, and two-hand output exactly as the accepted baseline.
for name in ("vr_weapon_buzz", "vr_render_weapon_fired"):
    assert function(render, name) == function(released_render, name), name

# Surface buzz is tied to actual hand contact and the tracked arm's ownership.
# It must not be driven by the independent head-to-hand collision sampler.
assert "vr_hand_contact_sample" not in render
assert "vr_hand_contact_feedback" not in render
assert "if (pressed && action.weight[side] == 0) vr_pressure_buzz(controller, depth);" in render
assert "else if (contacts && action.weight[side] == 0) vr_haptic(controller, 0.05f + 0.05f * contacts, 0.03f);" in render

# Weapon switching and melee are separate input bits and default controls.
vr_header = (ROOT / "port/linux/src/vr.h").read_text(encoding="utf-8")
render_header = (ROOT / "port/linux/include/halo_vr.h").read_text(encoding="utf-8")
player_control = (ROOT / "source/game/player_control.c").read_text(encoding="utf-8")
weapons = (ROOT / "source/items/weapons.c").read_text(encoding="utf-8")
assert "#define VR_ACTION_MELEE 0x1u" in vr_header
assert "#define VR_ACTION_SWITCH_WEAPON 0x8u" in vr_header
assert "#define VR_RENDER_ACTION_MELEE 0x1u" in render_header
assert "#define VR_RENDER_ACTION_SWITCH_WEAPON 0x8u" in render_header
assert "vr.actions |= VR_ACTION_SWITCH_WEAPON;" in frame
assert "vr.actions |= VR_ACTION_MELEE;" in frame
assert "VR_BUTTON_SOURCE_RIGHT_STICK, VR_BUTTON_SOURCE_RIGHT_STICK_DOWN,\n\tVR_BUTTON_SOURCE_Y" in frame
assert "if (actions & VR_RENDER_ACTION_MELEE)\n\t\t\tSET_FLAG(input.unit_control_flags, _unit_control_use_equipment_bit, TRUE);" in player_control
assert "if (actions & VR_RENDER_ACTION_SWITCH_WEAPON)\n\t\t\tSET_FLAG(input.player_control_flags, _player_control_rotate_weapons_bit, TRUE);" in player_control
assert "vr_render_weapon_fired(weapon_index, player_index);" in weapons

# Candidate guide generation must retain the cumulative field instructions,
# not reduce the installed guide to the short release note plus public guide.
guide_generator = (ROOT / "tools/generate-field-guide.py").read_text(encoding="utf-8")
field_guide = (ROOT / "docs/TEST49-FIELD-GUIDE.md").read_text(encoding="utf-8")
assert "TEST'+candidate+'-FIELD-GUIDE.md" in guide_generator
for marker in ("Manual reload", "OpenCE Build167 voice chat", "Retained features since v1.0.18",
               "Weapon recoil values and routing match v1.0.18"):
    assert marker.lower() in field_guide.lower(), marker

print("PASS: weapon recoil matches v1.0.18 exactly; surface buzz uses real contact; switch and melee actions remain distinct")
