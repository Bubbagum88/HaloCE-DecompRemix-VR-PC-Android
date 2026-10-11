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
table = menu[menu.index("static struct vr_menu_setting const vr_menu_immersion[] ="):]
table = table[:table.index("};")]
listed = re.findall(r"(VR_IMMERSION_\w+),", table)
assert sorted(listed) == sorted(macros), "every immersion row is on the IMMERSION page"
rest = menu.replace(table, "")
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
first = re.search(r'\{ "([A-Z +]+)", vr_menu_\w+', pages).group(1)
assert first == "IMMERSION", "IMMERSION is the first category"
print(f"PASS: IMMERSION page lists {len(listed)} immersion settings, each the same row as on its usual page")
