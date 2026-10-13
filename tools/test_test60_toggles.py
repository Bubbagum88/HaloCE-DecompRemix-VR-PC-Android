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
            '{ "vr.vehicle_tank_drive", "vr.vehicle_handles", TRUE }',
            # Test61: the owner's Test60 session: IMMERSIVE VEHICLE on left VIEW in third person
            '{ "vr.vehicle_handles", "vr.vehicle_view", FALSE }',
            '{ "vr.vehicle_tank_hatch", "vr.vehicle_view", TRUE }',
            '{ "vr.vehicle_warthog_hide_glass", "vr.vehicle_view", TRUE }',
            '{ "vr.reload_shoulder", "vr.manual_reload", TRUE }',
            '{ "vr.reload_hip", "vr.manual_reload", TRUE }',
            '{ "vr.button_sprint_toggle", "vr.button_sprint", TRUE }',
            '{ "vr.npc_interaction", "vr.custom_npc_rigs", TRUE }',
            '{ "vr.world_interaction", "vr.custom_scenery_grab", TRUE }',
            # Test63: ONE-HAND HEAVIES is a way of grabbing: it brings NPC GRAB
            '{ "vr.npc_one_hand_heavy", "vr.npc_interaction", FALSE }'):
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
#include <stdlib.h>
#include <math.h>
typedef float real;
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
    {"vr.vehicle_tank_drive",1},{"vr.vehicle_banshee_slide",1},{"vr.vehicle_tank_hatch",0},
    {"vr.vehicle_warthog_hide_glass",0},{"vr.reload_shoulder",0},{"vr.reload_hip",0},
    {"vr.button_sprint_toggle",0},{"vr.button_sprint",0},{"vr.assisted_combat",0},{"vr.close_contact",0},
    {"vr.npc_one_hand_heavy",0}, /* Test63: ONE-HAND HEAVIES */
    {"vr.vehicle_cockpit_lock",1},{"vr.vehicle_grip_guide",0},{"vr.npc_lift_to_ragdoll",1}}; /* Test65 */
static char automatic_store[256], view_store[32] = "chase", melee_store[32] = "swing";
static real speed_store, assist_store = 0.05f;
static real config_real(char const *key){if(!strcmp(key,"vr.npc_grab_assist"))return assist_store;assert(!strcmp(key,"vr.melee_speed"));return speed_store;}
static int sprint_setter_calls;
static int *slot(char const *key)
{ for (unsigned i = 0; i < NUMBEROF(store); i++) if (!strcmp(store[i].key, key)) return &store[i].on; assert(0); return 0; }
static boolean config_boolean(char const *key) { return *slot(key); }
static void config_write_boolean(char const *key, boolean on) { *slot(key) = on; }
static char const *config_string(char const *key) { assert(!strcmp(key, "vr.immersion_auto")); return automatic_store; }
static void config_write_string(char const *key, char const *value) { (void)key; snprintf(automatic_store, sizeof automatic_store, "%s", value); }
static void platform_log(char const *f, ...) { (void)f; }
static int config_matches(char const *key, char const *text) { if(!strcmp(key,"vr.melee"))return !strcmp(melee_store,text); assert(!strcmp(key, "vr.vehicle_view")); return !strcmp(view_store, text); }
static int config_write_text(char const *key, char const *text) { if(!strcmp(key,"vr.npc_grab_assist")){assist_store=atof(text);return 1;} if(!strcmp(key,"vr.melee_speed")){speed_store=atof(text);return 1;} if(!strcmp(key,"vr.melee")){snprintf(melee_store,sizeof melee_store,"%s",text);return 1;} assert(!strcmp(key, "vr.vehicle_view")); snprintf(view_store, sizeof view_store, "%s", text); return 1; }
''' + resolver + r'''
static boolean vr_menu_button_sprint_set(boolean enabled) { sprint_setter_calls++; config_write_boolean("vr.button_sprint", enabled); return TRUE; }
''' + r'''
/* a menu row turned on or off by hand: written, then the resolver */
static void choose(char const *key, int on)
{
    struct vr_menu_setting row = { "ROW", key, _vr_setting_boolean };
    config_write_boolean(key, on);
    vr_menu_dependencies(&row, on ? "true" : "false");
}
/* VIEW chosen by hand */
static void choose_view(char const *view)
{
    struct vr_menu_setting row = { "VIEW", "vr.vehicle_view", 2 };
    config_write_text("vr.vehicle_view", view);
    vr_menu_dependencies(&row, view);
}
static void choose_melee(char const *mode)
{
    struct vr_menu_setting row = { "MELEE", "vr.melee", _vr_setting_multi };
    char value[80];
    config_write_text("vr.melee", mode);
    snprintf(value,sizeof(value),"vr.melee=%s;vr.melee_multiplayer=false",mode);
    vr_menu_dependencies(&row,value);
}
static void choose_speed(char const *speed)
{
    struct vr_menu_setting row = { "MELEE SPEED", "vr.melee_speed", 2 };
    config_write_text("vr.melee_speed",speed);
    vr_menu_dependencies(&row,speed);
}
int main(void)
{
    choose("vr.assisted_combat",1);
    assert(config_boolean("vr.melee_requires_fist")&&config_boolean("vr.close_contact")&&config_boolean("vr.npc_interaction"));
    assert(!strcmp(melee_store,"impact")&&speed_store==2.0f);
    choose("vr.melee_requires_fist",0);assert(!config_boolean("vr.assisted_combat"));
    speed_store=1.4f;choose("vr.assisted_combat",1);assert(speed_store==1.4f);
    choose_melee("swing");assert(!config_boolean("vr.assisted_combat")&&!strcmp(melee_store,"swing"));
    choose("vr.assisted_combat",1);assert(!strcmp(melee_store,"impact")&&speed_store==1.4f);
    choose_speed("0");assert(!config_boolean("vr.assisted_combat")&&speed_store==0.0f);
    choose("vr.assisted_combat",1);assert(speed_store==2.0f);
    choose_speed("1.4");assert(config_boolean("vr.assisted_combat"));
    choose("vr.assisted_combat",0);assert(speed_store==1.4f);
    choose("vr.melee_requires_fist",0);
    /* DEATH RAGDOLLS turns on NPC GRAB, NPC RESCUE and IMPACT DAMAGE, and NPC
     * GRAB in turn FIST REQUIRED */
    choose("vr.death_ragdolls", 1);
    assert(config_boolean("vr.npc_interaction") && config_boolean("vr.npc_rescue") &&
           config_boolean("vr.interaction_damage") && config_boolean("vr.melee_requires_fist"));
    /* Test61: and, through NPC GRAB, CUSTOM NPC RIGS */
    assert(config_boolean("vr.custom_npc_rigs"));
    /* the player may turn one off; it stays off */
    choose("vr.npc_rescue", 0);
    assert(!config_boolean("vr.npc_rescue") && config_boolean("vr.death_ragdolls"));
    choose("vr.vehicle_handles", 0);
    assert(!config_boolean("vr.npc_rescue"));
    /* DEATH RAGDOLLS off: what it alone turned on goes off with it */
    choose("vr.death_ragdolls", 0);
    assert(!config_boolean("vr.npc_interaction") && !config_boolean("vr.interaction_damage") &&
           !config_boolean("vr.melee_requires_fist"));
    /* Test61: CUSTOM NPC RIGS (which needs NPC GRAB) does not hold NPC GRAB on */
    assert(!config_boolean("vr.custom_npc_rigs"));
    /* NPC GRAB alone: NPC RESCUE and IMPACT DAMAGE */
    choose("vr.npc_interaction", 1);
    assert(config_boolean("vr.npc_rescue") && config_boolean("vr.interaction_damage") && config_boolean("vr.melee_requires_fist"));
    choose("vr.npc_interaction", 0);
    assert(!config_boolean("vr.npc_rescue") && !config_boolean("vr.interaction_damage"));
    /* WORLD GRAB: IMPACT DAMAGE; a requirement chosen by hand stays the player's */
    choose("vr.interaction_damage", 1);
    choose("vr.world_interaction", 1);
    /* Test61: WORLD GRAB brings CUSTOM SCENERY; turned off by hand it stays off */
    assert(config_boolean("vr.custom_scenery_grab"));
    choose("vr.custom_scenery_grab", 0);
    assert(!config_boolean("vr.custom_scenery_grab") && config_boolean("vr.world_interaction"));
    choose("vr.world_interaction", 0);
    assert(config_boolean("vr.interaction_damage") && !config_boolean("vr.custom_scenery_grab"));
    choose("vr.world_interaction", 1);
    assert(config_boolean("vr.custom_scenery_grab"));
    choose("vr.world_interaction", 0);
    assert(!config_boolean("vr.custom_scenery_grab") && !config_boolean("vr.world_interaction"));
    /* a vehicle refinement turned on turns IMMERSIVE VEHICLE on */
    choose("vr.vehicle_steer_haptics", 0);
    assert(!config_boolean("vr.vehicle_handles"));
    choose("vr.vehicle_steer_haptics", 1);
    assert(config_boolean("vr.vehicle_handles"));
    /* Test61: IMMERSIVE VEHICLE puts VIEW in FIRST PERSON (the refinement
     * above turned it on, so it did already); THIRD PERSON chosen turns it
     * off; on again, FIRST PERSON again; off, back to THIRD PERSON */
    assert(!strcmp(view_store, "first_person"));
    choose_view("chase");
    assert(!config_boolean("vr.vehicle_handles") && !strcmp(view_store, "chase"));
    choose("vr.vehicle_handles", 1);
    assert(!strcmp(view_store, "first_person"));
    choose("vr.vehicle_handles", 0);
    assert(!strcmp(view_store, "chase"));
    /* FIRST PERSON chosen by hand stays when the controls go off */
    choose_view("first_person");
    choose("vr.vehicle_handles", 1);
    choose("vr.vehicle_handles", 0);
    assert(!strcmp(view_store, "first_person"));
    choose_view("chase");
    /* TANK HATCH and HOG GLASS bring FIRST PERSON; may be left in third */
    choose("vr.vehicle_tank_hatch", 1);
    assert(!strcmp(view_store, "first_person"));
    choose_view("chase");
    assert(config_boolean("vr.vehicle_tank_hatch") && !strcmp(view_store, "chase"));
    choose("vr.vehicle_tank_hatch", 0);
    choose("vr.vehicle_warthog_hide_glass", 1);
    assert(!strcmp(view_store, "first_person"));
    choose("vr.vehicle_warthog_hide_glass", 0);
    assert(!strcmp(view_store, "chase"));
    /* a pouch brings MANUAL RELOAD, SPRINT TOGGLE BUTTON SPRINT (by its own setter) */
    choose("vr.reload_hip", 1);
    assert(config_boolean("vr.manual_reload"));
    choose("vr.reload_hip", 0);
    assert(!config_boolean("vr.manual_reload"));
    choose("vr.button_sprint_toggle", 1);
    assert(config_boolean("vr.button_sprint") && sprint_setter_calls == 1);
    choose("vr.button_sprint_toggle", 0);
    assert(!config_boolean("vr.button_sprint") && sprint_setter_calls == 2);
    /* hard requirements as before: CUSTOM NPC RIGS chosen by hand brings NPC
     * GRAB and keeps it; NPC GRAB off takes it off */
    choose("vr.custom_npc_rigs", 1);
    assert(config_boolean("vr.npc_interaction"));
    choose("vr.vehicle_handles", 0);
    assert(config_boolean("vr.npc_interaction") && config_boolean("vr.custom_npc_rigs"));
    choose("vr.npc_interaction", 0);
    assert(!config_boolean("vr.custom_npc_rigs"));
    /* Test66: NPC GRAB and FIST COMBAT bring GRAB ASSIST of at least 10 cm,
     * back to 5 cm when the last of them goes; more chosen by hand stays */
    assist_store=0.05f;choose("vr.npc_interaction",1);assert(assist_store>0.099f&&assist_store<0.101f);
    choose("vr.assisted_combat",1);choose("vr.npc_interaction",0);assert(assist_store>0.099f);
    choose("vr.assisted_combat",0);assert(assist_store>0.049f&&assist_store<0.051f);
    assist_store=0.20f;choose("vr.npc_interaction",1);choose("vr.npc_interaction",0);assert(assist_store>0.199f);
    puts("PASS: Test66 NPC GRAB and FIST COMBAT bring a 10 cm GRAB ASSIST (released with the last of them; a larger one chosen by hand stays)");
    puts("PASS: Test60 toggles: DEATH RAGDOLLS turns on NPC GRAB, NPC RESCUE and IMPACT DAMAGE (and FIST REQUIRED through NPC GRAB); grabs turn on IMPACT DAMAGE; vehicle refinements turn on IMMERSIVE VEHICLE; turned off by hand stays off; released with their feature; Test61: IMMERSIVE VEHICLE puts VIEW in FIRST PERSON, TANK HATCH and HOG GLASS bring it, pouches MANUAL RELOAD, SPRINT TOGGLE BUTTON SPRINT, the grabs CUSTOM NPC RIGS and CUSTOM SCENERY");
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
