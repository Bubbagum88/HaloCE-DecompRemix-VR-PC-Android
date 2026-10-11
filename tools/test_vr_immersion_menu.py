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
# Test54: IMMERSION (features and how they feel) and IMMERSION+ (technical
# options) together list every immersion row, each on exactly one of them.
table = page("vr_menu_immersion")
advanced = page("vr_menu_immersion_advanced")
listed = re.findall(r"(VR_IMMERSION_\w+),", table) + re.findall(r"(VR_IMMERSION_\w+),", advanced)
assert sorted(listed) == sorted(macros), "every immersion row is on IMMERSION or IMMERSION+, once"
for essential in ("VR_IMMERSION_MANUAL_RELOAD", "VR_IMMERSION_NPC_GRAB", "VR_IMMERSION_WORLD_GRAB",
                  "VR_IMMERSION_GRIP_CLIMB", "VR_IMMERSION_DEATH_RAGDOLLS", "VR_IMMERSION_FIST_REQUIRED",
                  "VR_IMMERSION_NPC_GRAB_ASSIST", "VR_IMMERSION_NPC_HOLD", "VR_IMMERSION_THROW_STRENGTH",
                  "VR_IMMERSION_CLIMB_GRAB", "VR_IMMERSION_POUCH_SIDE"):
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
assert first == ["IMMERSION", "IMMERSION+"], first

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
print(f"PASS: IMMERSION and IMMERSION+ list {len(listed)} immersion settings, each the same row as on its usual page; dependencies reference-counted")
