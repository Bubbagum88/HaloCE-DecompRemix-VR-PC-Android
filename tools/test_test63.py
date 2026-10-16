"""Test63: the owner's fresh-install Test62 session (2026-10-12 12:06 log,
12:06:42 video) and requests.

- Reticle gone: its left-stick toggle hid it (12:10:53) just before BUTTON
  SPRINT took the click (12:11:04); nothing could show it again.
- X to drive the Warthog also dropped the pistol's magazine (12:09:37).
- Chest grenades orbited with the head; the hand closed on the slot (video
  1:16-1:34) and never took it; placeholder balls, not the grenades.
- Fist assist: no punch ever acquired (no "acquired" line in the log).
- A Covenant crate on b30's beach never took a hand.
- Vehicle controls looked like debug geometry; no visible calibration.
- Requested: ONE-HAND HEAVIES; the owner's parkour/throw values as defaults;
  jump straight to a settings section.
The torso frame is compiled from vr_frame.c and stepped here; the grenade,
combat, vehicle and menu code are exercised in test_test62_extra,
test_test57b_vehicle_anchor and test_test31_vr_menu.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
frame = read("port/linux/src/vr_frame.c")
menu = read("port/linux/game/vr_menu.c")
config = read("port/linux/src/port_config.c")
reload = read("port/linux/game/vr_manual_reload.c")
extra = read("port/linux/game/vr_extra_interaction.c")
world = read("port/linux/game/vr_world_interaction.c")
handles = read("port/linux/game/vr_vehicle_handles.h")
npc = read("port/linux/game/vr_npc_interaction.c")
render_objects = read("source/render/render_objects.c")


def body(text, signature):
    start = text.index(signature)
    brace = text.index("{", start)
    depth, end = 1, brace + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


# 1. BUTTON SPRINT owns the left stick's click; a hidden reticle comes back
settings = body(frame, "void vr_reload_settings(void)")
assert settings.index('vr.button_sprint_enabled = config_boolean("vr.button_sprint");') < settings.index("waits while BUTTON SPRINT has the left stick's click")
assert "if (vr.button_source[owned] == VR_BUTTON_SOURCE_LEFT_STICK)" in settings
assert "if (vr.button_source[VR_BUTTON_ACTION_RETICLE] == VR_BUTTON_SOURCE_NONE && vr.reticle_hidden)" in settings
assert "vr.reticle_hidden = 0;" in settings
# (Test70: the row's chooser skips it: vr_menu_button_sprint_skip)
assert 'return config_boolean("vr.button_sprint") ?' in menu and "vr_menu_button_value(setting, VR_BUTTON_SOURCE_LEFT_STICK)" in menu
# (the menu's existing move-aside and restore are kept)
assert "static boolean vr_menu_button_sprint_set(boolean enabled)" in menu and 'config_write("vr.button_sprint_saved_mask", text)' in menu

# 2. X with an action on offer is never a magazine release
update = body(reload, "unsigned vr_manual_reload_update(long weapon_index, int explicit_reload)")
assert "player->action_result != _player_action_result_reload" in update
assert update.index("input.eject_pressed = reload_pressed;") < update.index("input.eject_pressed = FALSE;")

# 3. grenades: chest frame, drawn palm, 12 cm, models
chest = body(extra, "static boolean chest_points(long unit,real_point3d const *camera,real_point3d points[2])")
assert "vr_torso_place(offset,camera->n,points[type].n)" in chest and "vr_head_view" not in chest
tick = body(extra, "void vr_extra_tick(long unit)")
assert "vr_render_palm_point(h,unit,palm.n)" in tick and "nearest<=.15f*units" in tick  # (Test72: 15 cm)
assert 'not taken by hand %d: %.1f cm from the %s slot (reach 15 cm)%s' in tick
models = body(extra, "void vr_extra_models_render(void)")
assert "extra_draw_grenade(unit,type,&slots[type]" in models and "extra_draw_grenade(unit,extra.hand[h].type,&point,&hf,&hu" in models
assert "return object_definition_get(grenade->projectile.index)->object.model.index;" in extra
assert "render_model(model_index,pixels,matrices,NULL,colors,functions,lighting,at,radius,NULL,id,0,0);" in extra
assert render_objects.index("vr_manual_reload_debris_render();") < render_objects.index("vr_extra_models_render();")

# 4. fist assist: acquisition, step, hold, grab takes over, diagnostics
punch = body(extra, "int vr_combat_punch(long unit,int hand,real_point3d const *point,real_vector3d const *sweep)")
# Test65 (Arkham Shadow): within LUNGE or FIST REACH, looked at (45 deg) or punched at (37 deg)
assert 'extra_bound("vr.combat_reach",3.0f,.75f,3)' in extra and "reach=combat_reach()*units" in punch
# Test72: the cone became combat_intent (the gaze, the fist's own 3D way,
# forgiving within 1.6 m): tools/test_test72_combat.py
assert "combat_intent(&gaze,&stroke,&level,level_punch,point,&chest,&delta,distance,&facing,&thrown)" in punch
engage = body(extra, "static void combat_engage(long unit,long target,int hand,boolean counter,real_point3d const *fist)")
assert "punch acquired" in engage and "punch took no target" in punch
velocity = body(extra, "void vr_combat_velocity(long unit,real_point3d const *position,real_vector3d *velocity)")
assert "velocity->i*=.35f;velocity->j*=.35f;" in velocity and "(extra.combo>=5?15.5f:14.0f)*units/TICKS_PER_SECOND" in velocity  # Test72: 14 m/s, 15.5 in a flow
assert "vr_interaction_owner(0)==VR_INTERACTION_NPC||vr_interaction_owner(1)==VR_INTERACTION_NPC" in velocity
assert "hand %d grabbed; the assist lets go" in tick
assert '{ "vr.combat_reach", _config_real, "3.0",' in config
assert '{ "FIST REACH", "vr.combat_reach", _vr_setting_real, 5, { { "1 M", "1" }, { "1.5 M", "1.5" }, { "2 M", "2" }, { "2.5 M", "2.5" }, { "3 M", "3" } } }' in menu

# 5. the crate: contact tests nearest bounds first, giants skipped, nearest named
candidate = body(world, "static long candidate(real_point3d const *point, real_point3d const *camera, long unit, real units,")
assert "item->object.bounding_sphere_radius > 4.0f" in candidate
assert candidate.index("gaps[slot] = gap; order[slot] = iterator.index;") < candidate.index("for (int index_in_order = 0;")
assert "nearest %s, %s, %.0f cm from its bounds" in world

# 6. vehicles: the Warthog's own wheel, redesigned controls, live preview
assert 'model_find_node(definition->object.model.index,"frame steering wheel")' in handles
wheel = body(handles, "real_matrix4x3 *vr_vehicle_controls_matrices(long object_index,real_matrix4x3 *stock)")
assert "vr_wheel.kind!=0" in wheel and "!vr_wheel.wheel_front" in wheel and "vr_calibration_shown(4)" in wheel
assert "target.position=vr_wheel.center;target.scale=rest.scale*vr_wheel.scale;" in wheel
assert "vr_vehicle_controls_matrices(object_index," in render_objects
assert "static void vr_wheel_tube(" in handles and "a UNSC drive stick" in handles and "a Covenant handlebar" in handles and "a Covenant flight" in handles
assert 'else if (!strncmp(setting->key, "vr.handle_", 10))\n\t\t\tvr_calibration_note_shown(4);' in menu
assert "if(vr_calibration_shown(4))vr_wheel_read_user(vr_wheel.kind);" in handles
assert "int vr_calibration_shown(int mask)" in frame

# 7. ONE-HAND HEAVIES and the owner's defaults
assert 'if(unit && config_boolean("vr.npc_one_hand_heavy")) *hands=1;' in npc
assert '{ "vr.npc_one_hand_heavy", _config_boolean, "false",' in config
assert '{ "vr.npc_one_hand_heavy", "vr.npc_interaction", FALSE },' in menu
for key, value in (("vr.wallrun_speed", "1.5"), ("vr.walljump_scale", "1.5"), ("vr.grenade_throw_scale", "1.5"),
                   ("vr.climb_launch_scale", "1.0"), ("vr.wallrun_duration", "2.0")):
    assert re.search(r'\{ "%s", _config_real, "%s",' % (re.escape(key), re.escape(value)), config), key

# 8. the settings index
assert "#define VR_MENU_INDEX_FROM 3" in menu and 'snprintf(line, sizeof(line), "PAGE %ld: %s...",' in menu

# the torso frame, compiled and stepped
start = frame.index("static struct { int valid; float yaw; double time; } torso;")
end = frame.index("/* a point in that chest frame")
torso = frame[start:end]
code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#define HALO_XR_FRAME_RECENTRED 1
static struct { struct { struct { float orientation[4]; } head; unsigned flags; } frame; } vr;
static double clock_now = 1.0;
static double vr_pose_time(void) { return clock_now; }
static void rotate(const float q[4], const float v[3], float out[3])
{
	float tx = 2.0f * (q[1] * v[2] - q[2] * v[1]);
	float ty = 2.0f * (q[2] * v[0] - q[0] * v[2]);
	float tz = 2.0f * (q[0] * v[1] - q[1] * v[0]);
	out[0] = v[0] + q[3] * tx + (q[1] * tz - q[2] * ty);
	out[1] = v[1] + q[3] * ty + (q[2] * tx - q[0] * tz);
	out[2] = v[2] + q[3] * tz + (q[0] * ty - q[1] * tx);
}
''' + torso + r'''
/* a head turned by `yaw` (about up) and pitched by `pitch` (about its right) */
static void head(float yaw, float pitch)
{
	float y[4] = { 0, sinf(yaw * .5f), 0, cosf(yaw * .5f) }, p[4] = { sinf(pitch * .5f), 0, 0, cosf(pitch * .5f) };
	float *q = vr.frame.head.orientation;
	q[3] = y[3] * p[3] - (y[0] * p[0] + y[1] * p[1] + y[2] * p[2]);
	q[0] = y[3] * p[0] + p[3] * y[0] + (y[1] * p[2] - y[2] * p[1]);
	q[1] = y[3] * p[1] + p[3] * y[1] + (y[2] * p[0] - y[0] * p[2]);
	q[2] = y[3] * p[2] + p[3] * y[2] + (y[0] * p[1] - y[1] * p[0]);
}
static float step(int frames)
{
	float yaw = 0;
	for (int f = 0; f < frames; f++) { clock_now += 1.0 / 72; yaw = torso_yaw_now(); }
	return yaw;
}
int main(void)
{
	head(0, 0); float start = torso_yaw_now();
	assert(fabsf(start) < 1e-4f);
	/* looking 30 degrees aside: the chest stays */
	head(0.52f, 0); assert(fabsf(step(144)) < 1e-4f);
	/* 60 degrees: it follows to within the 35-degree cone, a little at a time */
	head(1.05f, 0); { float first = step(1); assert(first > 0 && first < 0.1f); }
	{ float settled = step(216); assert(fabsf(settled - (1.05f - 0.61f)) < 0.01f); }
	/* looking down at the chest (60 degrees) and turning: it holds */
	{ float held = step(0 + 1); head(1.05f + 1.0f, -1.05f); assert(fabsf(step(144) - held) < 1e-4f); }
	/* level again: it follows */
	head(2.05f, 0); assert(step(216) > 1.3f);
	/* a recentre or a gap of half a second: it starts from the head */
	vr.frame.flags = HALO_XR_FRAME_RECENTRED; head(-0.3f, 0); clock_now += 1.0 / 72;
	assert(fabsf(torso_yaw_now() + 0.3f) < 1e-3f); vr.frame.flags = 0;
	head(0.9f, 0); clock_now += 0.6; assert(fabsf(torso_yaw_now() - 0.9f) < 1e-3f);
	puts("PASS: Test63 chest frame: still within 35 degrees, follows past it gradually, holds while looking down, resets on recentre or a gap");
	return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / "t.c").write_text(code, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", str(path / "t.c"),
                    "-o", str(path / "t"), "-lm"], check=True)
    subprocess.run([str(path / "t")], check=True)
print("PASS: Test63 wiring (sprint owns the stick click and the reticle returns, X kept for actions, chest grenades at the palm with the game's models, "
      "fist assist reach/cone/step/hold/grab, crate contact order, the Warthog's own wheel and redesigned controls with a live preview, "
      "ONE-HAND HEAVIES, the owner's defaults, the settings index)")
