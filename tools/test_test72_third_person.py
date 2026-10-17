"""Test72: VR THIRD PERSON (the owner: "make it so third person works in
vr. of course, when enabled, all inputs get auto converted to work for third
person, then reverted back to their previous/initial state after third
person is turned off").

- vr.third_person (GAMEPLAY > THIRD PERSON): on foot in a campaign or co-op;
- the flat game's camera behind the player, along the headset's heading;
- the head aims at what its gaze meets (from the camera behind);
- the hands' physical features held off meanwhile by values held over the
  settings (port_config.c's overrides: never written, given up all at once,
  a setting the player writes meanwhile keeping their choice).
The override layer is compiled from port_config.c itself and run.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
module = read("port/linux/game/vr_third_person.c")
third = read("port/linux/game/third_person.c")
render = read("port/linux/game/vr_render.c")
frame = read("port/linux/src/vr_frame.c")
config = read("port/linux/src/port_config.c")
header = read("port/linux/src/port_config.h")
menu = read("port/linux/game/vr_menu.c")

# ---- the setting and its row
assert re.search(r'\{ "vr\.third_person", _config_boolean, "false", "HALO_VR_THIRD_PERSON", _environment_value, _platform_vr,', config)
assert '{ "THIRD PERSON", "vr.third_person", _vr_setting_boolean, 2, { { "OFF", "false" }, { "ON", "true" } } },' in menu
gameplay = menu[menu.index("static struct vr_menu_setting const vr_menu_vr[] ="):]
assert gameplay.index('"THIRD PERSON"') < gameplay.index("};")

# ---- what it holds, all of them settings that exist
held = re.findall(r'\{ "(vr\.[a-z_]+)", "([^"]+)" \}', module[module.index("vr_third_person_settings[] ="):module.index("static boolean vr_third_person_held")])
names = dict(held)
assert names["vr.aim"] == "head" and names["vr.melee_speed"] == "0" and names["vr.roomscale"] == "false"
for name in ("vr.holsters", "vr.manual_reload", "vr.physical_grenades", "vr.assisted_combat", "vr.projectile_parry",
             "vr.world_interaction", "vr.npc_interaction", "vr.weapon_pull", "vr.parkour_climb", "vr.arm_run",
             "vr.slide_physical_crouch", "vr.wrist_hud", "vr.scope"):
    assert names.get(name) == "false", name
for name, _ in held:
    assert re.search(r'\{ "%s", _config_' % re.escape(name), config), "no such setting: " + name
wanted = module[module.index("static boolean vr_third_person_wanted(long unit_index)"):]
wanted = wanted[:wanted.index("\n}\n")]
assert "game_engine_running()" in wanted and "object->object.parent_object_index == NONE" in wanted  # not MP, on foot
hold = module[module.index("static void vr_third_person_hold(boolean hold)"):]
hold = hold[:hold.index("\n}\n")]
assert "config_override(vr_third_person_settings[index].name, vr_third_person_settings[index].value)" in hold
assert "config_override_clear();" in hold and hold.rstrip().endswith("vr_reload_settings();")
update = module[module.index("void vr_third_person_update(long unit_index)"):]
update = update[:update.index("\n}\n")]
assert "if (unit_index == NONE && vr_active() && vr_third_person_setting() && !game_engine_running())\n\t\treturn;" in update

# ---- the camera, the aim, the body
branch = third[third.index("\tif (vr_active())\n\t{\n\t\tplatform_third_person_active(FALSE);"):]
branch = branch[:branch.index("\t\treturn wanted;\n\t}")]
assert "wanted = vr_third_person_engaged() && !cinematic_in_progress() && third_person_unit() != NONE;" in branch
assert "unit->unit.current_zoom_level != NONE" in branch
update_camera = third[third.index("void third_person_camera_update("):]
assert "if (vr_active() && !vr_third_person_forward(&forward))\n\t\treturn;" in update_camera
facing = render[render.index("void vr_player_control_facing("):]
facing = facing[:facing.index("\n}\n")]
assert facing.index("vr_update_seat(unit_index);") < facing.index("vr_third_person_update(unit_index);")
assert "if (!seated && vr_third_person_engaged() && vr_third_person_aim(unit_index, &forward))\n\t\t\tvr_aim_adjusted(forward.n);" in facing
assert facing.index("vr_aim_adjusted(forward.n);") < facing.index("player_control_set_facing(local_player_index, &forward);")
aim = render[render.index("static boolean vr_third_person_aim(long unit_index, real_vector3d *forward)"):]
aim = aim[:aim.index("\n}\n")]
assert "real_point3d eye, camera = vr_render.head_camera.position, target;" in aim
assert "unit_get_camera_position(unit_index, &eye);" in aim and "vector_from_points3d(&eye, &target, &aim);" in aim
assert "&camera, &vector, unit_index, &collision)" in aim  # the player's own body not in the way
body = render[render.index("boolean vr_render_full_body("):]
assert body.index("if (vr_third_person_engaged())\n\t\treturn FALSE;") < body.index("return vr_render.stereo")
adjusted = frame[frame.index("void vr_aim_adjusted(const float forward[3])"):]
assert "vr.last_aim_yaw = atan2f(forward[1], forward[0]);" in adjusted[:adjusted.index("\n}\n")]

# the gaze-to-mark aim, worked through: from the camera behind and above the
# right shoulder, the mark straight ahead of the camera is not straight ahead
# of the eyes; the aim from the eyes meets it
import math
camera = (-1.7, 0.4, 0.15)
eye = (0.0, 0.0, 0.0)
gaze = (1.0, 0.0, 0.0)
mark = tuple(c + g * 20.0 for c, g in zip(camera, gaze))
aim_vector = tuple(m - e for m, e in zip(mark, eye))
length = math.sqrt(sum(a * a for a in aim_vector))
aim_direction = tuple(a / length for a in aim_vector)
assert abs(aim_direction[1] - 0.4 / length) < 1e-9 and aim_direction[0] > 0.99
# (a ray from the eyes along the aim reaches the mark; one along the gaze misses it by the camera's offset)
assert math.dist(tuple(e + a * length for e, a in zip(eye, aim_direction)), mark) < 1e-9
assert math.dist(tuple(e + g * length for e, g in zip(eye, gaze)), mark) > 0.4

# ---- the override layer, compiled from port_config.c and run
assert "int config_override(const char *name, const char *text);" in header
assert "if (config_overridden[index])\n\t\treturn &config_override_values[index];" in config
assert "config_overridden[index] = 0;\n\t\tconfig_change_count++;" in config  # a write ends its override
OUT = ROOT / "build/test72-third-person"
OUT.mkdir(parents=True, exist_ok=True)
source = config.replace('#include "platform.h"', 'static void platform_log(const char *s, ...) {(void)s;}').replace(
    '#include "halo_port_limits.h"', '#define HALO_PORT_NETWORK_VERSION 29\n#define HALO_PORT_NETWORK_VERSION_MINIMUM 11\n#define HALO_PORT_NETWORK_VERSION_MAXIMUM 29').replace(
    '#include <SDL3/SDL.h>', '#include <stdio.h>\n#include <stdlib.h>\n'
    'static void *SDL_LoadFile(const char *p, size_t *size){FILE *f=fopen(p,"rb");long n;void *d;if(!f)return NULL;fseek(f,0,SEEK_END);n=ftell(f);fseek(f,0,SEEK_SET);d=malloc((size_t)n+1);if(d&&fread(d,1,(size_t)n,f)!=(size_t)n){free(d);d=NULL;}fclose(f);if(d)*size=(size_t)n;return d;}\n'
    'static void SDL_free(void *p){free(p);}\n'
    'static int SDL_SaveFile(const char *p, const void *d, size_t n){FILE *f=fopen(p,"wb");int ok;if(!f)return 0;ok=fwrite(d,1,n,f)==n;return fclose(f)==0&&ok;}\n')
harness = r'''
#include <assert.h>
#include <string.h>
int main(void)
{
	unsigned long before;
	assert(!strcmp(config_string("vr.aim"), "hand"));
	assert(config_boolean("vr.holsters") == 1);
	before = config_changes();
	assert(config_override("vr.aim", "head") && config_override("vr.holsters", "false") && config_override("vr.melee_speed", "0"));
	assert(!config_override("vr.no_such_setting", "1"));
	assert(config_changes() > before);
	assert(!strcmp(config_string("vr.aim"), "head") && config_boolean("vr.holsters") == 0 && config_real("vr.melee_speed") == 0.0);
	assert(config_is_overridden("vr.aim") && !config_is_overridden("vr.roomscale"));
	/* the player's choice meanwhile wins, and stays */
	assert(config_write_text("vr.holsters", "true"));
	assert(config_boolean("vr.holsters") == 1 && !config_is_overridden("vr.holsters"));
	before = config_changes();
	config_override_clear();
	assert(config_changes() > before);
	assert(!strcmp(config_string("vr.aim"), "hand") && config_boolean("vr.holsters") == 1 && config_real("vr.melee_speed") > 0.0);
	assert(!config_is_overridden("vr.aim"));
	before = config_changes();
	config_override_clear(); /* (nothing held: no change) */
	assert(config_changes() == before);
	return 0;
}
'''
program = OUT / "override.c"
program.write_text("#define HALO_ANDROID 1\n#define HALO_VR 1\n" + source + harness, encoding="utf-8")
subprocess.run(["clang", "-std=gnu11", "-fno-sanitize-recover=all", "-fsanitize=address,undefined",
                "-I", str(ROOT / "port/linux/src"), "-I", str(ROOT / "port/third_party/tomlc17"), str(program),
                str(ROOT / "port/third_party/tomlc17/tomlc17.c"), "-pthread", "-o", str(OUT / "override")], check=True)
with tempfile.TemporaryDirectory(dir=OUT) as folder:
    env = dict(os.environ, HALO_DATA_ROOT=folder)
    for key in list(env):
        if key.startswith("HALO_VR_"):
            env.pop(key)
    subprocess.run([str(OUT / "override")], env=env, check=True)
    saved = (Path(folder) / "config.toml").read_text(encoding="utf-8")
    assert re.search(r'^aim = "hand"', saved, re.M), "an override is never written"
    assert re.search(r'^holsters = true', saved, re.M)
print("PASS: Test72 VR third person: GAMEPLAY > THIRD PERSON on foot in a campaign/co-op; camera along the heading; "
      "the gaze's mark aimed at from the eyes; %d settings held (never written), all given back, a player's write kept" % len(held))
