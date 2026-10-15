"""Test70: weapon handling fixes from the owner's list.

- Shake cooling did not work: test39's detector needed > 1 m/s in both
  33 ms samples either side of a turn, where a shaking hand's speed passes
  through zero (a brisk 4 Hz, 10 cm shake read about 0.96 m/s there), and it
  sampled only once the gun was fully overheated. vr_shake_detect.h counts
  strokes by their own peak speed and length; cooling applies while hot.
- The needler, with MANUAL RELOAD, reloads when shaken (no crystal-by-crystal
  loading): four strokes within 1.2 s; its automatic reload waits for that
  or the reload button.
- Rocket launcher: emptied, its new tubes are ready once seated (no push bar
  step), as a tactical reload already was.
- Locked weapons can be holstered (hand empty) and drawn again.
- Left hand: lettered UNSC guns drawn the right way round; winding per part.
- Pistol / Assault Rifle magazine holds fitted into the hand.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

reload = read("port/linux/game/vr_manual_reload.c")
weapons = read("source/items/weapons.c")
shake = read("port/linux/game/vr_cooldown_shake.c")
frame = read("port/linux/src/vr_frame.c")
render = read("port/linux/game/vr_render.c")
raster = read("source/rasterizer/xbox/rasterizer_xbox.c")
config = read("port/linux/src/port_config.c")

# rocket launcher / canister: ready once seated
assert "input.no_chamber = reload.kind == RELOAD_CRYSTALS || reload.kind == RELOAD_TUBES ||\n        reload.kind == RELOAD_CANISTER;" in reload
assert "vr_haptic(vr_weapon_hand(), 0.20f, 0.030f);" in reload  # charging owed: the gun hand reminded
# the needler: no magazine profile; shaken to reload
assert '"weapons\\\\needler\\\\fp\\\\fp", "frame needle01"' not in reload
assert "vr_needler_shake_update(weapon_index," in weapons and "VR_NEEDLER_SHAKE_SUPPRESS_AUTO" in weapons
assert "vr_shake_reload_ready(&shake.detect, shake.now) && shake.now - shake.reload_time > 1.5" in shake
# (Test71: or a mod's needler, by its rig)
assert '(vr_gun_class() != VR_GUN_NEEDLER && !vr_manual_reload_needle_rig(weapon_index))' in shake
# cooling while hot, every tick
heat = weapons[weapons.index("real heat_loss= weapon_definition->weapon.heat_loss_per_second"):]
heat = heat[:heat.index("weapon->weapon.heat-= heat_loss;")]
assert "heat_loss *= vr_cooldown_shake_rate(weapon_index);" in heat and "_weapon_overheated_bit" not in heat
# locked holstering
assert "static int locked_holstering(void)" in frame and "return hand_states() && vr.hand_state == HAND_EMPTY;" in frame
assert "locked weapons: weapon=%ld put away in the %s holster; the hand is empty" in frame
assert "holster_draw(w, holster_names[zone - 1]);" in frame and "holster_draw(w, holster);" in frame
assert "!vr_hand_empty();" in frame  # the grip as a button never acts from an empty hand
# left hand
assert "vr_mirror_subtree(matrices, graph, gun, &normal);" in render
for kind in ("VR_GUN_ROCKET_LAUNCHER", "VR_GUN_SNIPER_RIFLE", "VR_GUN_SHOTGUN", "VR_GUN_PISTOL"):
    assert "case %s:" % kind in render[render.index("static boolean vr_left_hand_gun_reads_right"):][:600]
assert "VR_GUN_ASSAULT_RIFLE" not in render[render.index("static boolean vr_left_hand_gun_reads_right"):][:600]
assert "nodes = rasterizer_vr_part_nodes(vertices, triangles);" in raster and "vertices->count > 512" not in raster
# magazine holds
assert '{ "vr.reload_grip_fit", _config_boolean, "true"' in config
assert "vr_reload_grip_fit(graph, model_index, units);" in render
fits = render[render.index("static boolean vr_reload_grip_fits(char const *model)\n{"):][:300]
assert "assault rifle" in fits and "pistol" in fits and "sniper" not in fits

check = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "vr_shake_detect.h"
/* a hand moving `amplitude` metres back and forth at `hertz` along x, with
`noise` metres of tracking jitter, sampled at 30 Hz for `seconds` */
static int counted(double hertz, double amplitude, double noise, double seconds, int reload, double drift)
{
    struct vr_shake s; int strokes = 0, ready = 0; unsigned seed = 7;
    vr_shake_reset(&s);
    for (int i = 0; i <= (int)(seconds * 30); i++) {
        double t = i / 30.0;
        float p[3];
        seed = seed * 1103515245u + 12345u;
        p[0] = (float)(amplitude * sin(2 * M_PI * hertz * t) + drift * t + noise * ((seed >> 16 & 1023) / 1023.0 - 0.5));
        p[1] = (float)(noise * ((seed >> 6 & 1023) / 1023.0 - 0.5)); p[2] = 0.3f;
        strokes += vr_shake_sample(&s, p, 100.0 + t);
        if (reload && vr_shake_reload_ready(&s, 100.0 + t)) ready = 1;
    }
    return reload ? ready : strokes;
}
int main(void) {
    struct vr_shake s;
    /* the owner's shake: brisk, 10 cm across at 4 Hz: counted, where test39's missed it */
    assert(counted(4.0, 0.05, 0.001, 1.0, 0, 0) >= 6);
    assert(counted(2.5, 0.06, 0.001, 1.0, 0, 0) >= 3);
    /* not a shake: tracking jitter, slow aiming, a melee swing's long strokes, walking */
    assert(counted(10.0, 0.002, 0.003, 2.0, 0, 0) == 0);
    assert(counted(0.5, 0.10, 0.001, 3.0, 0, 0) == 0);
    assert(counted(1.5, 0.30, 0.001, 2.0, 0, 0) == 0);
    assert(counted(0.0, 0.0, 0.002, 2.0, 0, 1.2) == 0);
    /* cooling: two strokes close together, bounded 1.5x..3x */
    vr_shake_reset(&s);
    {
        float m = 1.0f;
        for (int i = 0; i <= 30; i++) {
            double t = i / 30.0; float p[3] = { (float)(0.05 * sin(2 * M_PI * 4 * t)), 0, 0.3f };
            vr_shake_sample(&s, p, 50.0 + t);
            m = vr_shake_cooling_multiplier(&s, 50.0 + t);
        }
        assert(m >= 1.5f && m <= 3.0f);
        assert(vr_shake_cooling_multiplier(&s, 52.0) == 1.0f);   /* stopped: back to the gun's own */
    }
    /* the needler: a deliberate shake reloads; a short wiggle does not */
    assert(counted(4.0, 0.06, 0.001, 1.2, 1, 0));
    assert(!counted(4.0, 0.06, 0.001, 0.25, 1, 0));
    assert(!counted(1.5, 0.30, 0.001, 2.0, 1, 0));
    /* a gap in the samples restarts cleanly; NaN resets */
    vr_shake_reset(&s);
    { float p[3] = { NAN, 0, 0 }; assert(!vr_shake_sample(&s, p, 1.0) && !s.valid); }
    puts("PASS: Test70 shake detection: 4 Hz and 2.5 Hz shakes counted; jitter, aiming, swings, walking not; cooling 1.5-3x; needler reload needs a deliberate shake");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test70-weapons-") as temp:
    out = Path(temp)
    (out / "check.c").write_text(check, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Werror", "-Wno-unused-function", "-fsanitize=address,undefined",
                    "-I", str(ROOT / "port/linux/game"), str(out / "check.c"), "-lm", "-o", str(out / "check")], check=True)
    subprocess.run([str(out / "check")], check=True)
print("PASS: Test70 weapons: shake cooling while hot, needler shake reload, rocket ready when seated, locked holstering, left-hand lettering, magazine holds fitted")
