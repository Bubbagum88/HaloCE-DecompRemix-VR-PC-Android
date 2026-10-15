"""Test71: manual reload for the mods' own weapons.

The owner (2026-10-15): "adapt manual reload to any custom weapons/new
weapon meshes given by the mods". Manual reload knew six first-person
models by their tag names; a mod's weapon has its own, and a protected map
(SPV1) hides every name ("<protected>"), so no SPV1 gun, its stock rifles
included, could be reloaded by hand. vr_reload_generic_profile.h takes the
profile from the model's own nodes and its weapon's first magazine.

The rigs below are the first-person models' "frame" nodes and magazines
(magazine count, rounds loaded at most, rounds per reload) as read from the
caches during this work: the stock weapons (Xbox maps, and Project Lumoria's,
which keeps them all and adds a plasma cannon) and SPV1's ten levels.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "port/linux/game"
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

STOCK = {
    "weapons\\assault rifle\\fp\\fp": (["gun", "display", "magazine", "ophandle", "safety button"], 1, 60, 60),
    "weapons\\pistol\\fp\\fp": (["gun", "magazine", "slide", "slide_release", "trigger", "bullet", "chamber_button"], 1, 12, 12),
    "weapons\\sniper rifle\\fp\\fp": (["gun", "magazine", "ophandle", "bullet"], 1, 4, 4),
    "weapons\\shotgun\\fp\\fp": (["gun", "bullet", "magazine", "pump"], 1, 12, 1),
    "weapons\\rocket launcher\\fp\\fp": (["gun", "body", "foregrip", "tubes", "push_bar"], 1, 2, 2),
    "weapons\\flamethrower\\fp\\fp": (["gun", "ammo", "cover"], 1, 100, 100),
}
FINGERS = ["bone24", "l upperarm", "r upperarm", "l forearm", "r forearm", "l wriste", "r wriste",
           "l index low", "r index low", "l thumb tip", "r thumb tip"]
# name: (nodes, magazines, loaded, reloaded), expected (kind, ammo, chamber) or None
OTHERS = {
    "stock needler": ((["body", "eneedle13"] + ["needle%02d" % n for n in (1, 2, 3, 4, 5, 12, 14, 15, 16)], 1, 20, 20), None),
    "stock plasma pistol": ((["gun", "cover", "dial", "face"], 0, 0, 0), None),
    "stock plasma rifle": ((["gun", "rod_left", "rod_right", "wing_left", "wing_right"], 0, 0, 0), None),
    "Lumoria plasma cannon": ((["gun", "barrel", "grip", "handle", "vents"], 1, 0, 0), None),
    "SPV1 SMG": ((["gun", "magazine", "slide", "stock", "trigger"], 1, 60, 60), (0, "magazine", "slide")),
    "SPV1 pistol": ((["gun", "magazine", "slide", "slide_release", "trigger", "bullet", "ejection", "safety"], 1, 12, 12),
                    (0, "magazine", "slide")),
    "SPV1 sniper (bipod)": ((["gun", "bipod", "magazine", "ophandle", "bullet"], 1, 4, 4), (0, "magazine", "ophandle")),
    "SPV1 rifle with shotgun": ((["gun", "magazine", "ophandle", "pump", "safety button", "shotdoor"], 2, 36, 36),
                                (0, "magazine", "ophandle")),
    "SPV1 shotgun (arms rig)": ((["bone24", "gun", "l upperarm", "r upperarm", "cock", "l forearm", "port", "r forearm",
                                 "shell", "l wriste", "r wriste"], 1, 12, 1), (1, "shell", "cock")),
    "SPV1 flamethrower": ((["gun", "ammo", "barrel", "cover"], 1, 100, 100), (3, "ammo", "cover")),
    "SPV1 plasma rifle (arms rig)": ((FINGERS + ["gun", "left rod", "right rod", "left wing", "right wing"], 0, 0, 0), None),
    "SPV1 single-tube launcher": ((["gun", "body", "foregrip", "tubes", "push_bar"], 1, 1, 1), (2, "tubes", "push_bar")),
}

# --- the stock table, as vr_manual_reload.c has it: the generic rules must give exactly it
source = read("port/linux/game/vr_manual_reload.c")
kinds = {"RELOAD_MAGAZINE": 0, "RELOAD_SHELL": 1, "RELOAD_TUBES": 2, "RELOAD_CANISTER": 3}
table = re.findall(r'\{ "(weapons\\\\[^"]+)", "frame ([^"]+)", "frame ([^"]+)", (RELOAD_\w+) \}', source)
assert len(table) == 6, table
expected = {}
for path, ammo, chamber, kind in table:
    expected[path.replace("\\\\", "\\")] = (kinds[kind], ammo, chamber)
assert set(expected) == set(STOCK)

cases = []
for label, (nodes, magazines, loaded, reloaded) in STOCK.items():
    cases.append((label, nodes, magazines, loaded, reloaded, expected[label], False))
for label, ((nodes, magazines, loaded, reloaded), want) in OTHERS.items():
    cases.append((label, nodes, magazines, loaded, reloaded, want, "needler" in label))


def c_string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


program = ['#include <stdio.h>', '#include <string.h>', '#include "vr_reload_generic_profile.h"', 'int main(void) {',
           '  int failures = 0; struct vr_reload_generic found;']
for index, (label, nodes, magazines, loaded, reloaded, want, needle) in enumerate(cases):
    names = ", ".join(c_string("frame " + node) for node in nodes)
    program.append('  { static char const *const names[] = { %s };' % names)
    program.append('    int got = vr_reload_generic_profile(names, %d, %d, %d, %d, &found);' % (len(nodes), magazines, loaded, reloaded))
    if want is None:
        program.append('    if (got) { printf("FAIL %%s: a profile\\n", %s); failures++; }' % c_string(label))
    else:
        kind, ammo, chamber = want
        program.append('    if (!got || found.kind != %d || strcmp(found.ammo, %s) || strcmp(found.chamber, %s)) {'
                       % (kind, c_string("frame " + ammo), c_string("frame " + chamber)))
        program.append('      printf("FAIL %%s: %%d %%d %%s %%s\\n", %s, got, got ? found.kind : -1, got ? found.ammo : "", got ? found.chamber : ""); failures++; }'
                       % c_string(label))
    program.append('    if (vr_reload_generic_needle_rig(names, %d) != %d) { printf("FAIL %%s: needle rig\\n", %s); failures++; } }'
                   % (len(nodes), 1 if needle else 0, c_string(label)))
program.append('  { struct vr_reload_generic none; char const *const empty[] = { "frame gun" };')
program.append('    if (vr_reload_generic_profile(NULL, 0, 1, 1, 1, &none) || vr_reload_generic_profile(empty, 1, 1, 30, 30, &none)) failures++; }')
program.append('  printf("%d rigs, %d failures\\n", ' + str(len(cases)) + ', failures); return failures != 0; }')

with tempfile.TemporaryDirectory(prefix="test71-reload-") as temp:
    out = Path(temp)
    (out / "check.c").write_text("\n".join(program) + "\n", encoding="utf-8")
    subprocess.run(["cc", "-std=c99", "-Wall", "-Werror", "-Wno-unused-function", "-I", str(GAME),
                    "-o", str(out / "check"), str(out / "check.c")], check=True)
    result = subprocess.run([str(out / "check")], check=True, capture_output=True, text=True)
    assert "0 failures" in result.stdout, result.stdout

# --- wiring: the table first, then the model's own nodes; the needler shaken whatever its name
for needle in ('#include "vr_reload_generic_profile.h"', "reload_generic_kinds_match[",
               "vr_reload_generic_profile(node_names, node_count, definition->weapon.magazines.count,",
               "first->rounds_loaded_maximum, first->rounds_reloaded, &found)",
               "if (!profile && definition && definition->weapon.magazines.count > 0)",
               '"VR manual reload: generic profile weapon=%ld model=%ld tag=%s kind=%d ammo=%s chamber=%s"',
               "needle_rig_weapon = vr_reload_generic_needle_rig(node_names, node_count) ? weapon_index : NONE;",
               "if (definition->weapon.magazines.count < 1) {", "int vr_manual_reload_needle_rig(long weapon_index)"):
    assert needle in source, needle
assert source.index("if (!strcmp(name, profiles[index].path))") < source.index("vr_reload_generic_profile(node_names")
shake = read("port/linux/game/vr_cooldown_shake.c")
assert "(vr_gun_class() != VR_GUN_NEEDLER && !vr_manual_reload_needle_rig(weapon_index))" in shake
weapons = read("source/items/weapons.c")
# only the triggers of the magazine loaded by hand are held back: for every
# one-magazine weapon (all the stock ones) exactly as before
assert "if (physical_reload_block && trigger_definition->magazine_index <= 0) triggers_down[trigger_index] = FALSE;" in weapons
assert "if (!(physical_reload_auto && trigger_definition->magazine_index == 0) && magazine &&" in weapons
assert "weapon_magazine_finish_reload(weapon_index, 0);" in weapons
notes = read("port/android/app/src/main/assets/whats_new.txt")
assert "MANUAL RELOAD now works with the mods' own guns" in notes and "shaken to reload" in notes
assert 'still marked "Experimental — currently not working"' in notes  # Altheros, as the owner asked
assert 'STATUS_EXPERIMENTAL,' in read("port/android/app/src/main/java/com/halo/decomp/ModInstaller.java")
print("PASS: Test71 manual reload for mods' weapons: %d rigs (stock table reproduced; SPV1, Lumoria), "
      "needler rig shaken, a second magazine left to the game" % len(cases))
