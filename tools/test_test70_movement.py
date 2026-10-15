"""Test70: movement and fist combat from the owner's list.

- SLIDE (vr_slide_math.h / vr_slide.c): sprinting, a crouch slides on with
  the run's momentum; friction and slope; a little steering; jump cancels;
  NPCs struck by kind (Grunts knocked down, Hunters barely moved), never a
  kill. Offline only; off by default; it brings BUTTON SPRINT unless ARM RUN.
- BULLET TIME (vr_bullet_time.c): the game's time scaled while its button
  (the turning stick pushed up, the one free input) is held or toggled;
  local games only (never co-op or multiplayer), not in a seat, menu or
  cutscene; a map script's speed kept and given back.
- Wall jump (vr_pk_wall_leap): the level look leads, the wall run along is
  the one jumped from, momentum kept within bounds.
- Climbing: dense geometry (a tree's top) retried at smaller radii; short
  rays find a trunk the sphere missed.
- Fist combat: HIT ASSIST (in reach, within 30 cm of the body), LUNGE HOP,
  GRAB ASSIST 15 cm (and its mapping no longer undoes the assist).
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

slide = read("port/linux/game/vr_slide.c")
bipeds = read("source/units/bipeds.c")
bullet = read("port/linux/game/vr_bullet_time.c")
game_time = read("source/game/game_time.c")
frame = read("port/linux/src/vr_frame.c")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")
parkour = read("port/linux/game/vr_parkour.c")
extra = read("port/linux/game/vr_extra_interaction.c")
npc = read("port/linux/game/vr_npc_interaction.c")

# slide
assert "vr_slide_update(biped_index, &physics.forward, &biped->unit.throttle," in bipeds
assert 'config_boolean("vr.slide") && vr_active() && game_connection() == _game_connection_local' in slide
assert '{ "vr.slide", _config_boolean, "false"' in config
assert '{ "vr.slide", "vr.button_sprint", TRUE },' in menu
assert 'return config_boolean("vr.button_sprint") || config_boolean("vr.arm_run");' in menu
assert "vr_combat_knockable(target) && speed >= 6.0f" in slide and 'vr_slide_end("a heavy enemy")' in slide
# bullet time
assert "vr_bullet_time_frame();" in game_time and "vr_bullet_time_reset();" in game_time
assert "game_connection() == _game_connection_local && !network_coop_active()" in bullet
assert "!cinematic_in_progress()" in bullet and "!game_time_get_paused()" in bullet
assert '"vr.button_bullet_time", _config_string, "\\"right_stick_up\\""' in config
assert '{ "vr.bullet_time", _config_boolean, "false"' in config
assert "vr.turn_stick_up = !vr.seated" in frame and '"right_stick_up"' in frame
assert "saved >= (1L << VR_BUTTON_ACTIONS)" in menu  # every action's bit (push-to-talk's was dropped)
# fist combat and grabbing
assert '{ "vr.combat_hit_assist", _config_real, "0.30"' in config and "combat_hit_assist()*units" in extra
assert "extra.lunge_hop=extra.lunge_metres>=1.5f" in extra
assert '{ "vr.npc_grab_assist", _config_real, "0.15"' in config
assert 'return on ? "0.15" : "0.10";' in menu
assert "npc_contact_slack=assist;" in npc and "maximum_distance+=npc_contact_slack" in npc
assert 'fabs(assist - 0.10) < 0.001' in frame and '"vr.test70_defaults_applied"' in frame
assert '{ "FIST COMBAT", 8 }, { "FIST OPTIONS", 4 }' in menu
# climbing and the wall jump
assert "real r=radius*(attempt==0?1.0f:attempt==1?0.5f:0.25f);" in parkour
assert "parkour_grab_rays(unit,&point,&palm,&look,&up,parkour_grab_radius(units),waist_z,&hit)" in parkour
assert "real_vector3d from_wall=parkour.running&&parkour.wall_valid?parkour.wall_normal:wall.plane.n;" in parkour
assert "vr_pk_wall_leap(look.n,from_wall.n,carried,stick," in parkour

check = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "vr_slide_math.h"
#include "vr_parkour_math.h"
static float len2(float const v[2]) { return sqrtf(v[0]*v[0]+v[1]*v[1]); }
int main(void) {
    /* entry: the run's speed lifted a little, bounded */
    assert(fabsf(vr_slide_entry_speed(10.0f, 1.0f) - 11.5f) < 0.01f);
    assert(vr_slide_entry_speed(20.0f, 2.0f) == 14.0f);
    assert(vr_slide_entry_speed(NAN, 1.0f) == 0.0f && vr_slide_entry_speed(-1.0f, 1.0f) == 0.0f);
    assert(fabsf(vr_slide_duration(1.0f) - 1.1f) < 0.001f && vr_slide_duration(99.0f) == vr_slide_duration(1.0f));
    /* friction: 10 m/s gives up to about 4.5 in a second on the flat */
    {
        float v[2] = { 10.0f, 0.0f }, flat[3] = { 0, 0, 1 };
        for (int i = 0; i < 30; i++) vr_slide_step(v, 1.0f / 30.0f, 1.0f, flat, NULL, 0.0f);
        assert(len2(v) > 4.2f && len2(v) < 4.8f && fabsf(v[1]) < 1e-4f);
    }
    /* a slope: downhill faster, uphill slower than the flat */
    {
        float down[2] = { 8.0f, 0 }, up[2] = { 8.0f, 0 }, flat[2] = { 8.0f, 0 };
        float downhill[3] = { 0.26f, 0, 0.966f }, uphill[3] = { -0.26f, 0, 0.966f }, level[3] = { 0, 0, 1 };
        for (int i = 0; i < 15; i++) {
            vr_slide_step(down, 1.0f / 30.0f, 1.0f, downhill, NULL, 0);
            vr_slide_step(up, 1.0f / 30.0f, 1.0f, uphill, NULL, 0);
            vr_slide_step(flat, 1.0f / 30.0f, 1.0f, level, NULL, 0);
        }
        assert(len2(down) > len2(flat) + 0.5f && len2(up) < len2(flat) - 0.5f);
        /* a wall's face or a ceiling is no slope */
        float wall[3] = { 1, 0, 0 }, w[2] = { 8.0f, 0 };
        vr_slide_step(w, 1.0f / 30.0f, 1.0f, wall, NULL, 0);
        assert(len2(w) < 8.0f);
    }
    /* steering: a little, never a turn on the spot; a stick pulled back brakes */
    {
        float v[2] = { 10.0f, 0 }, left[2] = { 0, 1 }, back[2] = { -1, 0 };
        for (int i = 0; i < 15; i++) vr_slide_step(v, 1.0f / 30.0f, 1.0f, NULL, left, 1.0f);
        float turned = atan2f(v[1], v[0]) * 57.29578f;
        assert(turned > 20.0f && turned < 30.0f);
        float b[2] = { 10.0f, 0 }, c[2] = { 10.0f, 0 };
        vr_slide_step(b, 1.0f / 30.0f, 1.0f, NULL, back, 1.0f);
        vr_slide_step(c, 1.0f / 30.0f, 1.0f, NULL, NULL, 0.0f);
        assert(len2(b) < len2(c) && b[1] == 0.0f);
    }
    /* impact: nothing slow or glancing; at most half a melee at 1; never more than 1.5 */
    assert(vr_slide_impact_scale(3.5f, 1.0f, 1.0f) == 0.0f);
    assert(vr_slide_impact_scale(10.0f, 0.3f, 1.0f) == 0.0f);
    assert(fabsf(vr_slide_impact_scale(10.0f, 1.0f, 1.0f) - 0.5f) < 1e-5f);
    assert(vr_slide_impact_scale(30.0f, 1.0f, 9.0f) <= 1.5f && vr_slide_impact_scale(10.0f, 1.0f, 0.0f) == 0.0f);
    /* the wall jump: the wall on the left (its normal +x) */
    {
        float n[3] = { 1, 0, 0 }, out[3], v[3] = { 0, 0, 0 }, none[2] = { 0, 0 };
        /* looking away and ahead: where the look is, not sideways */
        float look[3] = { 0.6f, 0.8f, 0.0f };
        vr_pk_wall_leap(look, n, v, none, 5.0f, 2.0f, out);
        assert(fabsf(out[0] / len2(out) - 0.6f) < 0.01f && fabsf(out[1] / len2(out) - 0.8f) < 0.01f && out[2] == 2.0f);
        /* looking along the wall: it still leaves the wall (35% away) */
        float along[3] = { 0, 1, 0 };
        vr_pk_wall_leap(along, n, v, none, 5.0f, 2.0f, out);
        assert(out[0] / len2(out) >= 0.34f && out[1] > 0);
        /* looking into the wall: away from it, the look's side kept */
        float into[3] = { -0.7f, 0.714f, 0 };
        vr_pk_wall_leap(into, n, v, none, 5.0f, 2.0f, out);
        assert(out[0] > 0 && out[1] > 0);
        float straight[3] = { -1, 0, 0 };
        vr_pk_wall_leap(straight, n, v, none, 5.0f, 2.0f, out);
        assert(fabsf(out[0] - 5.0f) < 0.01f && fabsf(out[1]) < 0.01f);
        /* the head's pitch does not shorten the way; looking up jumps higher */
        float pitched[3] = { 0.36f, 0.48f, 0.8f }, flat[3] = { 0.6f, 0.8f, 0 }, a[3], b[3];
        vr_pk_wall_leap(pitched, n, v, none, 5.0f, 2.0f, a);
        vr_pk_wall_leap(flat, n, v, none, 5.0f, 2.0f, b);
        assert(fabsf(len2(a) - len2(b)) < 0.01f && a[2] > b[2]);
        /* momentum kept, within 1.5x; its way is the look's */
        float fast[3] = { 0, 9.0f, 0 };
        vr_pk_wall_leap(look, n, fast, none, 5.0f, 2.0f, out);
        assert(fabsf(len2(out) - 7.5f) < 0.01f && fabsf(out[0] / len2(out) - 0.6f) < 0.01f);
        /* the stick bends it, a fifth */
        float stick[2] = { 0, -1 };
        vr_pk_wall_leap(look, n, v, stick, 5.0f, 2.0f, out);
        assert(out[1] > 0 && out[1] / len2(out) < 0.8f);
        /* no wall normal to speak of: the old leap */
        float flat_n[3] = { 0, 0, 1 };
        vr_pk_wall_leap(look, flat_n, v, none, 5.0f, 2.0f, out);
        assert(isfinite(out[0]) && isfinite(out[1]) && out[2] >= 2.0f);
    }
    puts("PASS: Test70 movement math: slide entry/friction/slope/steer/brake/impact bounds; wall jump led by the look, escapes the wall, keeps bounded momentum");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test70-movement-") as temp:
    out = Path(temp)
    (out / "check.c").write_text(check, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Werror", "-Wno-unused-function", "-fsanitize=address,undefined",
                    "-I", str(ROOT / "port/linux/game"), str(out / "check.c"), "-lm", "-o", str(out / "check")], check=True)
    subprocess.run([str(out / "check")], check=True)
print("PASS: Test70 movement and fist combat wiring: slide, bullet time (offline, free input), wall jump, tree climbing, hit assist, lunge hop, grab assist 15 cm")
