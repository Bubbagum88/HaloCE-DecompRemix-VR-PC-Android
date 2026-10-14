"""Test66: OpenCE's dynamic ragdolls (the owner's video "Dynamic Ragdolls Are
Now In Halo CE": OpenCE PR #317, Jolt Physics) as the base for the dead,
on Android: Jolt runs in the 64-bit host and the ILP32 guest calls it
through the import table.

1. The bridge: every ragdoll_physics_* call the guest makes has a host import
   (host_imports.list, guest_host.h, ragdoll_physics_guest.c,
   host_ragdoll.c) with matching parameters; a vehicle contact crosses in the
   guest's layout (its long key 32 bits).
2. Jolt and the C interface, compiled here with the Android host's flags
   (C++17, no exceptions or RTTI, no fused multiply-add): a two-bone
   ragdoll dropped over a floor falls, lands on it and stops (the
   interface's own units: world units and ticks).
3. The hands and the ragdolls share bodies (ragdoll.c leaves what a hand's
   state has; a dead body let go of goes to Jolt; the hands' own death
   ragdoll stands aside); game.death_physics is "ragdoll" by default;
   the VR row DEATH PHYSICS.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

names = ["initialize", "reset", "create", "destroy", "exists", "set_environment", "step", "get_bone",
         "get_bone_velocity", "active", "hit", "add_velocity", "add_spin", "translate", "bounds",
         "vehicles_begin", "vehicle", "vehicles_end", "vehicle_contacts"]
imports = read("port/android/host_imports.list").split()
guest_host = read("port/android/guest/runtime/guest_host.h")
shim = read("port/linux/game/ragdoll_physics_guest.c")
host = read("port/android/host/host_ragdoll.c")
interface = read("port/linux/game/ragdoll_physics.h")
for name in names:
    host_name = "host_ragdoll_" + name
    assert host_name in imports, host_name
    declared = re.search(r"\b\w+\s+" + host_name + r"\(([^)]*)\);", guest_host)
    shim_declared = re.search(r"\b\w+\s+" + host_name + r"\(([^)]*)\);", shim)
    assert declared and shim_declared, host_name
    assert " ".join(declared.group(1).split()) == " ".join(shim_declared.group(1).split()), host_name
    assert re.search(r"\b" + host_name + r"\(", host), host_name
    assert "ragdoll_physics_" + name + "(" in interface, name
assert "out[index].vehicle = (int32_t)found[index].vehicle;" in host
build = read("tools/android_build.py")
assert '"-std=c++17", "-fno-exceptions", "-fno-rtti", "-DNDEBUG"' in build and '"-ffp-contract=off"' in build
assert '"-DHALO_JOLT" if jolt_present() else ""' in build and "$android_host_cxx -static-libstdc++ " in build

ragdoll = read("port/linux/game/ragdoll.c")
update = ragdoll[ragdoll.index("boolean ragdoll_biped_update("):]
update = update[:update.index("\nvoid ragdoll_note_damage(")]
assert update.index("if (vr_npc_interaction_has(biped_index))") < update.index("back to life (a Flood combat form")
take = ragdoll[ragdoll.index("boolean ragdoll_vr_take("):]
take = take[:take.index("\n}\n")]
assert "vr_npc_interaction_has(biped_index)" in take and "ragdoll_seed(ragdoll, biped_index, NULL)" in take
assert "SET_FLAG(biped->biped.flags, BIPED_PORT_RAGDOLL_BIT, TRUE);" in take
npc = read("port/linux/game/vr_npc_interaction.c")
assert "if(ragdoll_takes_death(index)) return;" in npc
assert "ragdoll_vr_take(index,&velocity,NULL)" in npc
assert "return index!=NONE&&state_for_object(index)!=NULL;" in npc
config = read("port/linux/src/port_config.c")
assert '{ "game.death_physics", _config_string, "\\"ragdoll\\"", "HALO_DEATH_PHYSICS", _environment_value, _platform_all,' in config
menu = read("port/linux/game/vr_menu.c")
assert '"DEATH PHYSICS", "game.death_physics", _vr_setting_string, 2, { { "DYNAMIC", "ragdoll" }, { "CLASSIC", "classic" } }' in menu
graphics = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.video_settings.graphics.xml")
assert 'op_death_physics" x="54" y="283"/>' in graphics  # shown on Android too
objects = read("source/objects/objects.c")
assert "object_bounds_cache_update(object_index, &object->object.bounding_sphere_center" in objects
assert (ROOT / "port/linux/game/object_bounds_cache.c").is_file()

drop = r'''
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "ragdoll_physics.h"
int main(void)
{
    struct ragdoll_physics_bone bones[2];
    struct ragdoll_physics_settings settings;
    /* a floor 2 world units across at z = 0, two triangles facing up */
    static const float floor[18] = { -1,-1,0, 1,-1,0, 1,1,0,  -1,-1,0, 1,1,0, -1,1,0 };
    float position[3], rotation[4], start;
    int tick;
    memset(bones, 0, sizeof(bones));
    memset(&settings, 0, sizeof(settings));
    for (int b = 0; b < 2; b++) {
        bones[b].parent = b - 1;
        bones[b].position[0] = 0.1f * b; bones[b].position[2] = 0.5f;
        bones[b].rotation[3] = 1;
        bones[b].capsule_end[0] = 0.1f;
        bones[b].radius = 0.03f;
        bones[b].joint = b ? 1 : 0;
        bones[b].joint_axis[0] = 1; bones[b].joint_normal[2] = 1;
        bones[b].swing_limit = 0.7f; bones[b].twist_limit = 0.3f;
        bones[b].friction_scale = 1;
    }
    settings.mass = 90; settings.friction = 0.8f; settings.restitution = 0.1f;
    settings.linear_damping = 0.1f; settings.angular_damping = 0.3f; settings.joint_friction = 0.2f;
    settings.gravity = 0.00356f; /* the game's gravity, world units a tick a tick */
    if (!ragdoll_physics_initialize()) { puts("no engine"); return 1; }
    if (!ragdoll_physics_create(0, bones, 2, &settings)) { puts("not made"); return 1; }
    ragdoll_physics_set_environment(0, 0, floor, 2);
    ragdoll_physics_get_bone(0, 0, position, rotation);
    start = position[2];
    for (tick = 0; tick < 300; tick++)
        ragdoll_physics_step(2, settings.gravity);
    ragdoll_physics_get_bone(0, 0, position, rotation);
    printf("fell from %.3f to %.3f; active %d\n", start, position[2], ragdoll_physics_active(0));
    if (!(position[2] < start - 0.3f) || !(position[2] > -0.01f) || !(position[2] < 0.1f)) return 1;
    ragdoll_physics_destroy(0);
    if (ragdoll_physics_exists(0)) return 1;
    ragdoll_physics_reset();
    puts("PASS: Test66 Jolt ragdoll (host flags): dropped, landed on the floor, at rest above it, destroyed");
    return 0;
}
'''
jolt = ROOT / "port/third_party/JoltPhysics"
with tempfile.TemporaryDirectory(prefix="test66-ragdolls-") as temp:
    out = Path(temp)
    (out / "drop.cpp").write_text(drop, encoding="utf-8")
    sources = sorted((jolt / "Jolt").rglob("*.cpp")) + [ROOT / "port/linux/physics/ragdoll_physics.cpp", out / "drop.cpp"]
    objects_built = []
    flags = ["-O1", "-std=c++17", "-fno-exceptions", "-fno-rtti", "-DNDEBUG", "-ffp-contract=off", "-w",
             f"-I{jolt}", f"-I{ROOT / 'port/linux/game'}"]
    procs = []
    for index, source in enumerate(sources):
        obj = out / f"{index}.o"
        objects_built.append(obj)
        procs.append(subprocess.Popen(["clang++", *flags, "-c", str(source), "-o", str(obj)]))
        if len(procs) >= 8:
            assert procs.pop(0).wait() == 0
    for proc in procs:
        assert proc.wait() == 0
    subprocess.run(["clang++", *map(str, objects_built), "-o", str(out / "drop"), "-lpthread"], check=True)
    subprocess.run([str(out / "drop")], check=True)
print("PASS: Test66 ragdoll bridge: every ragdoll call a host import with the same parameters, contacts in the guest's layout, Jolt built with the host's flags; hands and ragdolls share bodies; DEATH PHYSICS")
