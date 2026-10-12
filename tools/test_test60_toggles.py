"""Test60: features turn on what they play best with, and impacts work on every NPC.

Owner's Test59 session (2026-10-12 07:04 log and video): DEATH RAGDOLLS was
turned on and NPC RESCUE stayed off; slamming friendly NPCs did no impact
damage (the log had no impact at all). This suite runs the production
dependency resolver (vr_menu.c) on a stand-in settings store, and pins the
impact wiring (vr_articulated_native.c, vr_interaction_impact.c); the impact
probes themselves run in tools/test_test56_ragdoll.py.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
menu = read("port/linux/game/vr_menu.c")
native = read("port/linux/game/vr_articulated_native.c")
impact = read("port/linux/game/vr_interaction_impact.c")

resolver = menu[menu.index("static struct vr_menu_dependency"):menu.index("/* a page of settings, opened")]
for row in ('{ "vr.death_ragdolls", "vr.npc_interaction", TRUE }',
            '{ "vr.death_ragdolls", "vr.npc_rescue", TRUE }',
            '{ "vr.death_ragdolls", "vr.interaction_damage", TRUE }',
            '{ "vr.npc_interaction", "vr.npc_rescue", TRUE }',
            '{ "vr.npc_interaction", "vr.interaction_damage", TRUE }',
            '{ "vr.world_interaction", "vr.interaction_damage", TRUE }',
            '{ "vr.vehicle_lift", "vr.interaction_damage", TRUE }',
            '{ "vr.holster_haptics", "vr.holsters", TRUE }',
            '{ "vr.vehicle_steer_haptics", "vr.vehicle_handles", TRUE }',
            '{ "vr.vehicle_tank_drive", "vr.vehicle_handles", TRUE }'):
    assert row in resolver, row

# Impacts: a sphere contact is probed into the face it met; bodies and
# vehicles are tested for (the dead-body sweep passes through them); the
# blow carries no team (allies' friendly-damage resistance no longer applies).
assert "FLAG(_collision_test_objects_bipeds_bit))" in native
assert "found=collision_test_vector(VR_IMPACT_TEST_FLAGS,&from,&into,rig->unit_index,&hit);" in native
assert "collision_test_vector(VR_IMPACT_BODY_TEST_FLAGS,&from,&reach,rig->unit_index,&hit)" in native
assert "struck->unit.player_index==NONE" in native
assert impact.count("damage.owner_team_index=NONE;") == 2 and "owner->object.owner_team_index" not in impact

code = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int boolean;
enum { FALSE, TRUE };
#define NUMBEROF(a) (sizeof(a) / sizeof((a)[0]))
enum { _vr_setting_boolean, _vr_setting_multi };
struct vr_menu_setting { char const *label, *key; int type; };
static struct { char const *key; int on; } store[] = {
    {"vr.death_ragdolls",0},{"vr.npc_interaction",0},{"vr.npc_rescue",0},{"vr.interaction_damage",0},
    {"vr.melee_requires_fist",0},{"vr.world_interaction",0},{"vr.vehicle_lift",0},{"vr.parkour_climb",0},
    {"vr.custom_npc_rigs",0},{"vr.custom_scenery_grab",0},{"vr.dropped_magazines",0},{"vr.manual_reload",0},
    {"vr.holster_haptics",1},{"vr.holsters",1},{"vr.vehicle_handles",0},{"vr.vehicle_wheel_visible",1},
    {"vr.vehicle_control_glow",1},{"vr.vehicle_steer_haptics",1},{"vr.vehicle_comfort_reach",1},
    {"vr.vehicle_tank_drive",1},{"vr.vehicle_banshee_slide",1}};
static char automatic_store[256];
static int *slot(char const *key)
{ for (unsigned i = 0; i < NUMBEROF(store); i++) if (!strcmp(store[i].key, key)) return &store[i].on; assert(0); return 0; }
static boolean config_boolean(char const *key) { return *slot(key); }
static void config_write_boolean(char const *key, boolean on) { *slot(key) = on; }
static char const *config_string(char const *key) { assert(!strcmp(key, "vr.immersion_auto")); return automatic_store; }
static void config_write_string(char const *key, char const *value) { (void)key; snprintf(automatic_store, sizeof automatic_store, "%s", value); }
static void platform_log(char const *f, ...) { (void)f; }
''' + resolver + r'''
/* a menu row turned on or off by hand: written, then the resolver */
static void choose(char const *key, int on)
{
    struct vr_menu_setting row = { "ROW", key, _vr_setting_boolean };
    config_write_boolean(key, on);
    vr_menu_dependencies(&row, on ? "true" : "false");
}
int main(void)
{
    /* DEATH RAGDOLLS turns on NPC GRAB, NPC RESCUE and IMPACT DAMAGE, and NPC
     * GRAB in turn FIST REQUIRED */
    choose("vr.death_ragdolls", 1);
    assert(config_boolean("vr.npc_interaction") && config_boolean("vr.npc_rescue") &&
           config_boolean("vr.interaction_damage") && config_boolean("vr.melee_requires_fist"));
    /* the player may turn one off; it stays off */
    choose("vr.npc_rescue", 0);
    assert(!config_boolean("vr.npc_rescue") && config_boolean("vr.death_ragdolls"));
    choose("vr.vehicle_handles", 0);
    assert(!config_boolean("vr.npc_rescue"));
    /* DEATH RAGDOLLS off: what it alone turned on goes off with it */
    choose("vr.death_ragdolls", 0);
    assert(!config_boolean("vr.npc_interaction") && !config_boolean("vr.interaction_damage") &&
           !config_boolean("vr.melee_requires_fist"));
    /* NPC GRAB alone: NPC RESCUE and IMPACT DAMAGE */
    choose("vr.npc_interaction", 1);
    assert(config_boolean("vr.npc_rescue") && config_boolean("vr.interaction_damage") && config_boolean("vr.melee_requires_fist"));
    choose("vr.npc_interaction", 0);
    assert(!config_boolean("vr.npc_rescue") && !config_boolean("vr.interaction_damage"));
    /* WORLD GRAB: IMPACT DAMAGE; a requirement chosen by hand stays the player's */
    choose("vr.interaction_damage", 1);
    choose("vr.world_interaction", 1);
    choose("vr.world_interaction", 0);
    assert(config_boolean("vr.interaction_damage"));
    /* a vehicle refinement turned on turns IMMERSIVE VEHICLE on */
    choose("vr.vehicle_steer_haptics", 0);
    assert(!config_boolean("vr.vehicle_handles"));
    choose("vr.vehicle_steer_haptics", 1);
    assert(config_boolean("vr.vehicle_handles"));
    /* hard requirements as before */
    choose("vr.custom_npc_rigs", 1);
    assert(config_boolean("vr.npc_interaction"));
    choose("vr.npc_interaction", 0);
    assert(!config_boolean("vr.custom_npc_rigs"));
    puts("PASS: Test60 toggles: DEATH RAGDOLLS turns on NPC GRAB, NPC RESCUE and IMPACT DAMAGE (and FIST REQUIRED through NPC GRAB); grabs turn on IMPACT DAMAGE; vehicle refinements turn on IMMERSIVE VEHICLE; turned off by hand stays off; released with their feature");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test60-") as temp:
    path = Path(temp)
    (path / "check.c").write_text(code)
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function", "-Wno-unused-parameter",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    str(path / "check.c"), "-o", str(path / "check")], check=True)
    subprocess.run([str(path / "check")], check=True)
print("PASS: Test60 wiring (impacts probed into the face met, bodies and vehicles struck, no team on a blow)")
