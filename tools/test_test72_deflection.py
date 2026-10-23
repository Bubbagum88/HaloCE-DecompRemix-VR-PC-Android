"""Test72: SHOT DEFLECTION (the owner: "Shot Deflection does not appear to
work"; "it should also work if im just holding a gun against the
projectiles"; "proper vibration/feedback for projectile deflecting").

Root causes found (vr_projectile_parry.c's header has the detail):
- DEFLECT SHOTS was off by default and turned on only at the moment FIST
  COMBAT was turned on: a player with FIST COMBAT on before Test67 never had
  it. Now on by default; once, an OFF still at the old default goes on.
- a held gun deflected only while swung (1.2 m/s): held in a shot's path it
  never did. The gun is now a solid body along its aim: it blocks.
- an empty hand needed the grip and the trigger; the grip (a closed hand)
  now suffices.
- nothing was logged; deflections and refusals (with the reason) now are.

This compiles the production deflect_category against every stock map's
projectile tag (their values read from the caches: initial velocity in
world units a tick, gravity, fuse, collision radius, range, and whether the
tag has impact damage or a detonation effect) and checks the settings, the
migration and the feedback's wiring. tools/test_test67_projectile_parry.py
runs the whole module (contact, block, swing, kinds, ownership)."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
module = read("port/linux/game/vr_projectile_parry.c")
extra = read("port/linux/game/vr_extra_interaction.c")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")
frame = read("port/linux/src/vr_frame.c")


def function(source, name):
    match = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', source, re.M)
    assert match, name
    start = match.start()
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


# (name, initial velocity, gravity, fuse upper bound, collision radius, range, impact damage, detonation effect, expected)
STOCK = [
    ("frag grenade", 0.0, 1.00, .50, 0.00, 0.0, 0, 1, "GRENADE"),
    ("plasma grenade", 0.0, 1.00, 2.00, 0.00, 0.0, 0, 1, "GRENADE"),
    ("teleport ring", 0.0, 0.00, 0.00, 0.00, 2.0, 0, 0, "NEVER"),
    ("covenant blast bolt", 0.0, 1.00, 0.00, 0.00, 5000.0, 0, 0, "NEVER"),
    ("needle", 0.1, 0.00, .75, 0.00, 20.0, 1, 1, "BOLT"),
    ("cortana info", 0.1, 0.00, 0.00, 0.00, 1.5, 1, 0, "NEVER"),
    ("wraith mortar", 0.3, 1.00, 0.00, 0.50, 128.0, 0, 1, "NEVER"),
    ("flame", 0.3, 0.00, 0.00, 0.10, 2.5, 0, 1, "NEVER"),
    ("rocket", 0.4, 0.00, 0.00, 0.10, 128.0, 0, 1, "EXPLOSIVE"),
    ("fuel rod", 0.5, 1.00, 0.00, 0.00, 0.0, 0, 1, "EXPLOSIVE"),
    ("charged plasma bolt", 0.5, 0.00, 0.00, 0.10, 40.0, 1, 1, "BOLT"),
    ("banshee fuel rod", 0.7, 0.60, 0.00, 0.00, 0.0, 0, 1, "EXPLOSIVE"),
    ("plasma pistol bolt", 0.8, 0.10, 0.00, 0.00, 50.0, 1, 0, "BOLT"),
    ("shade bolt", 0.8, 0.00, 0.00, 0.00, 0.0, 1, 0, "BOLT"),
    ("plasma rifle bolt", 1.7, 0.00, 0.00, 0.00, 0.0, 1, 0, "BOLT"),
    ("banshee bolt", 1.7, 0.00, 0.00, 0.00, 70.0, 1, 0, "BOLT"),
    ("ghost bolt", 1.7, 0.00, 0.00, 0.00, 50.0, 1, 0, "BOLT"),
    ("tank shell", 3.3, 0.00, 0.00, 0.00, 1000.0, 0, 1, "NEVER"),
    ("shotgun pellet", 4.7, 1.00, 0.00, 0.00, 40.0, 1, 0, "BULLET"),
    ("beam emitter", 6.7, 0.00, 0.00, 0.00, 0.0, 0, 1, "NEVER"),
    ("warthog bullet", 9.8, 1.00, 0.00, 0.00, 0.0, 1, 0, "BULLET"),
    ("pistol bullet", 10.0, 1.00, 0.00, 0.00, 40.0, 1, 0, "BULLET"),
    ("assault rifle bullet", 10.8, 1.00, 0.00, 0.00, 40.0, 1, 0, "BULLET"),
    ("sniper bullet", 33.3, 0.00, 0.00, 0.00, 1000.0, 1, 0, "BULLET"),
]

rows = ",\n".join('{"%s",%.2ff,%.2ff,%.2ff,%.2ff,%.1ff,%d,%d,DEFLECT_%s}' % row for row in STOCK)
harness = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;typedef int boolean;
#define NONE (-1)
#define TRUE 1
#define FALSE 0
struct projectile_definition {struct {real initial_velocity,air_gravity_scale,maximum_range,timer_upper_bound,collision_radius;
 struct {long index;}effect,impact_damage;}projectile;};
enum {DEFLECT_NEVER,DEFLECT_BOLT,DEFLECT_BULLET,DEFLECT_GRENADE,DEFLECT_EXPLOSIVE};
enum {DEFLECT_BY_FIST,DEFLECT_BY_SWING,DEFLECT_BY_BLOCK};
''' + function(module, "deflect_category") + "\n" + function(module, "deflect_allowed") + r'''
struct row {char const *name;real v0,gravity,fuse,radius,range;int impact,effect,expected;};
static struct row const rows[]={
''' + rows + r'''
};
int main(void){
 for(unsigned i=0;i<sizeof rows/sizeof rows[0];i++){
  struct projectile_definition d;memset(&d,0,sizeof d);
  d.projectile.initial_velocity=rows[i].v0;d.projectile.air_gravity_scale=rows[i].gravity;
  d.projectile.timer_upper_bound=rows[i].fuse;d.projectile.collision_radius=rows[i].radius;d.projectile.maximum_range=rows[i].range;
  d.projectile.impact_damage.index=rows[i].impact?1:NONE;d.projectile.effect.index=rows[i].effect?1:NONE;
  int got=deflect_category(&d);
  if(got!=rows[i].expected){printf("%s: %d, expected %d\n",rows[i].name,got,rows[i].expected);return 1;}
 }
 /* the rules by way */
 assert(deflect_allowed(DEFLECT_BOLT,DEFLECT_BY_FIST,1.2f)&&deflect_allowed(DEFLECT_BOLT,DEFLECT_BY_BLOCK,0));
 assert(!deflect_allowed(DEFLECT_BULLET,DEFLECT_BY_FIST,5)&&deflect_allowed(DEFLECT_BULLET,DEFLECT_BY_BLOCK,0)&&deflect_allowed(DEFLECT_BULLET,DEFLECT_BY_SWING,1.2f));
 assert(deflect_allowed(DEFLECT_GRENADE,DEFLECT_BY_FIST,1.2f)&&deflect_allowed(DEFLECT_GRENADE,DEFLECT_BY_BLOCK,0));
 assert(!deflect_allowed(DEFLECT_EXPLOSIVE,DEFLECT_BY_BLOCK,9)&&!deflect_allowed(DEFLECT_EXPLOSIVE,DEFLECT_BY_FIST,2.4f)&&
  deflect_allowed(DEFLECT_EXPLOSIVE,DEFLECT_BY_FIST,2.5f)&&deflect_allowed(DEFLECT_EXPLOSIVE,DEFLECT_BY_SWING,3));
 assert(!deflect_allowed(DEFLECT_NEVER,DEFLECT_BY_SWING,9));
 /* bad data never deflects */
 {struct projectile_definition d;memset(&d,0,sizeof d);d.projectile.initial_velocity=NAN;d.projectile.impact_damage.index=1;
  assert(deflect_category(&d)==DEFLECT_NEVER);}
 printf("PASS: %d stock projectile tags sorted as they should be\n",(int)(sizeof rows/sizeof rows[0]));
}
'''
with tempfile.TemporaryDirectory(prefix="test72-deflection-") as directory:
    path = Path(directory)
    (path / "check.c").write_text(harness, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                    "-fsanitize=address,undefined", str(path / "check.c"), "-lm", "-o", str(path / "check")], check=True)
    subprocess.run([str(path / "check")], check=True)

# ---- the settings: on by default, aid and force; the menu rows; the migration
assert re.search(r'\{ "vr\.projectile_parry", _config_boolean, "true",', config)
assert re.search(r'\{ "vr\.deflect_assist", _config_real, "0\.03",', config)
assert re.search(r'\{ "vr\.deflect_strength", _config_real, "1\.0",', config)
assert '{ "DEFLECT AID", "vr.deflect_assist", _vr_setting_real, 3, { { "OFF", "0" }, { "NORMAL", "0.03" }, { "WIDE", "0.06" } } }' in menu
assert '{ "DEFLECT FORCE", "vr.deflect_strength", _vr_setting_real, 3, { { "75%", "0.75" }, { "100%", "1.0" }, { "125%", "1.25" } } }' in menu
assert menu.count("VR_IMMERSION_DEFLECT_ASSIST,") == 2 and menu.count("VR_IMMERSION_DEFLECT_STRENGTH,") == 2
assert '{ "FIST OPTIONS", 7 }' in menu
migration = frame[frame.index('if (!config_boolean("vr.test72_combat_defaults_applied"))'):]
migration = migration[:migration.index('config_write_boolean("vr.test72_combat_defaults_applied", 1);')]
assert 'if (!config_boolean("vr.projectile_parry"))' in migration and 'config_write_boolean("vr.projectile_parry", 1);' in migration

# ---- the gun blocks, the grip is a fist, the reasons are logged
tick = function(module, "vr_projectile_parry_tick")
assert "(armed||vr_interaction_grip(h,NULL,NULL))" in tick and "vr_interaction_trigger" not in tick
assert "if(vr_weapon_view(camera.n" in tick or "vr_weapon_view(camera.n,aim_at.n,aim.n,aim_up.n)" in tick
attempt = function(module, "vr_projectile_parry_try")
assert "this_way=parry.hand[h].strike?DEFLECT_BY_SWING:DEFLECT_BY_BLOCK;" in attempt
assert "if(projectile->object.owner_object_index==unit)return FALSE;" in attempt
assert '"VR shot deflection: a %s deflected by the %s (hand %d), %.0f m/s in, %.0f m/s out"' in attempt
assert '"VR shot deflection: a %s met a hand, not deflected: %s"' in module

# ---- the feedback: a crack, its ring, both hands on a two-handed gun, the sound
feedback = function(extra, "vr_extra_projectile_feedback")
for part in ("extra_pulse(hand,strength,.05f);", "if(both)extra_pulse(1-hand,strength*.7f,.05f);",
             "extra.deflect_echo_tick=now+2;", "unit_vr_guard_feedback(owner,!block);", "extra.defence_parry=1;"):
    assert part in feedback, part
tick_extra = function(extra, "vr_extra_tick")
assert tick_extra.index("vr_projectile_parry_tick(unit);") < tick_extra.index("if(extra.deflect_echo_tick>0&&now>=extra.deflect_echo_tick){") \
    < tick_extra.index("if(unit==NONE||(unit!=extra_player(TRUE)&&!grenades_only)")  # (the ring without FIST COMBAT too; Test73: a client's grenades alone)

print("PASS: Test72 shot deflection: on by default (once for players at the old default), a held gun blocks, the grip a fist, "
      "every stock projectile sorted by its data, DEFLECT AID and FORCE, logged, a crack and a ring")
