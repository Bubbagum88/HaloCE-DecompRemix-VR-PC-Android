"""VR Settings' IMMERSION page gathers every immersion feature in one place.

The owner asked (2026-10-11) for one section with all the VR immersion
features (parkour, physical melee, manual reload, grabbing, ...), while every
toggle also stays on its usual page. Each shared row is defined once
(VR_IMMERSION_* macro) and used on both pages, so the two can never differ:
they are the same setting row.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
menu = (ROOT / "port/linux/game/vr_menu.c").read_text(encoding="utf-8")
config = (ROOT / "port/linux/src/port_config.c").read_text(encoding="utf-8")

macros = dict(re.findall(r"^#define (VR_IMMERSION_\w+) (\{.*\})$", menu, re.M))
assert len(macros) >= 30, len(macros)
def page(name):
    text = menu[menu.index(f"static struct vr_menu_setting const {name}[] ="):]
    return text[:text.index("};")]
# Test55: one IMMERSION category whose screens are topics (sections); every
# immersion row is on it exactly once.
table = page("vr_menu_immersion")
advanced = ""
assert "vr_menu_immersion_advanced" not in menu and '"IMMERSION+"' not in menu
listed = re.findall(r"(VR_IMMERSION_\w+),", table)
assert sorted(listed) == sorted(macros), "every immersion row is on IMMERSION, once"
sections_text = menu[menu.index("static struct vr_menu_section const vr_menu_immersion_sections[] ="):]
sections_text = sections_text[:sections_text.index("};")]
sections = [(label, int(count)) for label, count in re.findall(r'\{ "([A-Z +]+)", (\d+) \}', sections_text)]
assert [label for label, _ in sections] == ["WEAPONS", "RELOAD", "POUCH PLACES", "HOLSTER PLACES",
                                            "MOVEMENT", "BODY", "GRAB + NPCS", "ADVANCED"], sections
assert all(0 < count <= 8 for _, count in sections) and sum(count for _, count in sections) == len(listed)
# each topic's rows, in order, are the ones its comment heads
blocks = re.split(r"/\* ([A-Z +]+) \*/", table)[1:]
for (label, count), (comment, rows) in zip(sections, zip(blocks[0::2], blocks[1::2])):
    assert label == comment, (label, comment)
    assert len(re.findall(r"VR_IMMERSION_\w+,", rows)) == count, label
assert '"NEXT: %s (%ld/%ld)"' in menu
assert "vr_calibration_note_shown(1);" in menu and "vr_calibration_note_shown(2);" in menu
for essential in ("VR_IMMERSION_MANUAL_RELOAD", "VR_IMMERSION_NPC_GRAB", "VR_IMMERSION_WORLD_GRAB",
                  "VR_IMMERSION_GRIP_CLIMB", "VR_IMMERSION_DEATH_RAGDOLLS", "VR_IMMERSION_FIST_REQUIRED",
                  "VR_IMMERSION_NPC_GRAB_ASSIST", "VR_IMMERSION_NPC_HOLD", "VR_IMMERSION_THROW_STRENGTH",
                  "VR_IMMERSION_CLIMB_GRAB", "VR_IMMERSION_POUCH_SIDE", "VR_IMMERSION_POUCH_HIP_OUT",
                  "VR_IMMERSION_HOLSTER_SHOULDER_BACK", "VR_IMMERSION_PHYSICAL_HANDLES"):
    assert essential + "," in table, essential
rest = menu.replace(table, "").replace(advanced, "")
for name, row in macros.items():
    uses = re.findall(r"\b" + name + r",", rest)
    assert len(uses) == 1, f"{name} must also stay on its usual page (found {len(uses)})"
    key = re.match(r'\{ "[^"]+", "([^"]+)"', row).group(1)
    assert f'{{ "{key}"' in config, f"{name}: {key} is a real setting"

for required in ("vr.parkour_wallrun", "vr.parkour_walljump", "vr.parkour_climb", "vr.melee", "vr.manual_reload",
                 "vr.world_interaction", "vr.npc_interaction", "vr.vehicle_lift", "vr.ragdoll_retention",
                 "vr.weapons", "vr.holsters", "vr.arm_run", "vr.vehicle_handles"):
    assert any(f'"{required}"' in row for row in macros.values()), required

pages = menu[menu.index("} const vr_menu_pages[] ="):]
pages = pages[:pages.index("};")]
first = re.findall(r'\{ "([A-Z +]+)", vr_menu_\w+', pages)[:2]
assert first[0] == "IMMERSION" and "IMMERSION+" not in first, first

# Test54: dependencies. Grabbing and climbing turn FIST REQUIRED on (soft:
# it may be turned off by hand), MAG DEBRIS / CUSTOM SCENERY / CUSTOM NPC RIGS
# turn on what they need (hard), and what was turned on only for a feature is
# reference-counted in vr.immersion_auto.
resolver = menu[menu.index("static struct vr_menu_dependency"):menu.index("/* a page of settings, opened")]
for row in ('{ "vr.dropped_magazines", "vr.manual_reload", FALSE }',
            '{ "vr.custom_scenery_grab", "vr.world_interaction", FALSE }',
            '{ "vr.custom_npc_rigs", "vr.npc_interaction", FALSE }',
            '{ "vr.npc_interaction", "vr.melee_requires_fist", TRUE }',
            '{ "vr.world_interaction", "vr.melee_requires_fist", TRUE }',
            '{ "vr.parkour_climb", "vr.melee_requires_fist", TRUE }',
            '{ "vr.vehicle_lift", "vr.melee_requires_fist", TRUE }'):
    assert row in resolver, row
assert 'config_write_string("vr.immersion_auto", automatic);' in resolver
assert "if (written && vr_menu_dependencies(setting, value))" in menu
assert '{ "vr.immersion_auto", _config_string' in config
for key in ("vr.death_ragdolls", "vr.npc_grab_assist", "vr.npc_hold_strength", "vr.throw_strength",
            "vr.climb_grab_radius", "vr.reload_pouch_side"):
    assert f'{{ "{key}"' in config, key
print(f"PASS: one IMMERSION category, {len(sections)} topic screens, {len(listed)} immersion settings, each the same row as on its usual page; dependencies reference-counted")
