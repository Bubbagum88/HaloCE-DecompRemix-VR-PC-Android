"""Test66: the owner's Test65 session (2026-10-13 16:08 and 16:24 logs and
videos, 17:37 weapon pull log and video) and requests.

Compiled here from the production sources:
- WEAPON PULL (vr_weapon_pickup.c): a free hand pointed at a gun lying on the
  ground locks on with a squeeze, a flick back throws it to the hand in an
  arc, a closed hand catches it, an open one lets it drop; the gun hand is
  refused with the reason; a squeeze at nothing says how far the nearest is.
- the wall run's faces (vr_parkour_math.h): steeper than ~53 degrees runs, a
  hill underfoot does not, and the facing eases round a bend.
Pinned: the seat's eyes held per seat, the wheel's turn followed past half a
circle, fist damage as the multiplier, block and parry in damage.c, grab
assist from the body's surface, a held body kept, OBJECT THROW, LEFT-HAND
MODE, the waist grenades, the IMMERSION vehicle topics, OpenCE Build 201's
display options.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
pull = read("port/linux/game/vr_weapon_pickup.c")
pull = re.sub(r"^#include[^\n]*\n", "", pull, flags=re.M).replace("#ifdef HALO_VR", "", 1).rsplit("#endif", 1)[0]

PULL = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
typedef float real; typedef int boolean;
typedef union { float n[3]; struct { float x, y, z; }; } real_point3d;
typedef union { float n[3]; struct { float i, j, k; }; } real_vector3d;
typedef struct { float alpha, red, green, blue; } real_argb_color;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define TICKS_PER_SECOND 30
#define FLAG(b) (1u << (b))
#define TEST_FLAG(v, b) (((v) & FLAG(b)) != 0)
#define SET_FLAG(v, b, on) ((on) ? ((v) |= FLAG(b)) : ((v) &= ~FLAG(b)))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define PIN(v, a, b) MIN(MAX(v, a), b)
enum { _game_connection_local, _game_connection_network_client };
enum { _object_dead_bit, _object_connected_to_map_bit, _object_at_rest_bit };
enum { _object_mask_weapon = 4, _collision_result_object = 3, _collision_test_for_line_of_sight_flags = 1 };
enum { VR_INTERACTION_NONE, VR_INTERACTION_RELOAD };
struct object_fields { long parent_object_index; unsigned damage_flags, flags; real_point3d position, bounding_sphere_center;
    real bounding_sphere_radius; real_vector3d translational_velocity, angular_velocity; };
struct object_datum { long definition_index; struct object_fields object; };
struct weapon_datum { long definition_index; struct object_fields object; };
struct unit_datum { long definition_index; struct object_fields object; };
struct player_datum { long unit_index; };
struct object_iterator { long index; };
struct collision_result { int type; long object_index; float t; };
static real_vector3d up_axis = {{0, 0, 1}}, zero, *global_up3d = &up_axis, *global_zero_vector3d = &zero;
static struct object_datum objects[4];
static struct unit_datum player_unit;
static struct player_datum player = { 9 };
static long now = 100;
static int grip[2], owner[2], weapon_hand = 1, hand_empty, tracked = 1, can_use = 1, taken = 0, haptics, ground_hit;
static long taken_index = NONE; static int weapon_hand_set = -1;
static real_point3d hands[2]; static real_vector3d forwards[2];
static char style[16] = "flick"; static double reach = 3.0; static int enabled = 1;
static char logged[256];
void platform_log(char const *f, ...) { va_list a; va_start(a, f); vsnprintf(logged, sizeof logged, f, a); va_end(a); }
static int config_boolean(char const *k) { return !strcmp(k, "vr.weapon_pull") ? enabled : !strcmp(k, "vr.weapon_pull_glow"); }
static double config_real(char const *k) { (void)k; return reach; }
static char const *config_string(char const *k) { (void)k; return style; }
static int vr_active(void) { return 1; }
static int game_connection(void) { return _game_connection_local; }
static long local_player_get_player_index(short l) { (void)l; return 0; }
static struct player_datum *player_get(long p) { (void)p; return &player; }
static struct unit_datum *unit_try_and_get(long u) { return u == 9 ? &player_unit : NULL; }
static int cinematic_in_progress(void) { return 0; }
static int director_inhibited_input(short l) { (void)l; return 0; }
static int game_time_get_paused(void) { return 0; }
static long game_time_get(void) { return now; }
static int vr_controller(unsigned *b, float *t, float *s) { (void)b; (void)t; (void)s; return 1; }
static float vr_units_per_metre(void) { return 1; }
static double vr_pose_time(void) { return now / 30.0; }
static void unit_get_camera_position(long u, real_point3d *p) { (void)u; *p = (real_point3d){{0, 0, 1.6f}}; }
static int vr_hand_world(int h, float const *c, float *p, float *f, float *u) { (void)c; memcpy(p, hands[h].n, 12); memcpy(f, forwards[h].n, 12); u[0] = u[1] = 0; u[2] = 1; return tracked; }
static int vr_interaction_grip(int h, int *p, int *r) { (void)p; (void)r; return grip[h]; }
static int vr_interaction_owner(int h) { return owner[h]; }
static int vr_weapon_hand(void) { return weapon_hand; }
static int vr_hand_empty(void) { return hand_empty; }
static void vr_set_weapon_hand(int h) { weapon_hand_set = h; }
static void vr_haptic(int h, float a, float s) { (void)h; (void)a; (void)s; haptics++; }
static int vr_render_palm_point(int h, long u, float p[3]) { (void)u; memcpy(p, hands[h].n, 12); return 1; }
static float dot_product3d(real_vector3d const *a, real_vector3d const *b) { return a->i * b->i + a->j * b->j + a->k * b->k; }
static float magnitude3d(real_vector3d const *v) { return sqrtf(dot_product3d(v, v)); }
static float normalize3d(real_vector3d *v) { float n = magnitude3d(v); if (n > 0) for (int k = 0; k < 3; k++) v->n[k] /= n; return n; }
static void vector_from_points3d(real_point3d const *a, real_point3d const *b, real_vector3d *v) { for (int k = 0; k < 3; k++) v->n[k] = b->n[k] - a->n[k]; }
static float distance3d(real_point3d const *a, real_point3d const *b) { real_vector3d d; vector_from_points3d(a, b, &d); return magnitude3d(&d); }
static void object_iterator_new(struct object_iterator *i, unsigned m, int f) { (void)m; (void)f; i->index = -1; }
static struct object_datum *object_iterator_next(struct object_iterator *i) { while (++i->index < 4) if (objects[i->index].definition_index) return &objects[i->index]; return NULL; }
static struct object_datum *object_get(long i) { assert(i >= 0 && i < 4); return &objects[i]; }
static void *object_try_and_get_and_verify_type(long i, unsigned m) { (void)m; return i >= 0 && i < 4 && objects[i].definition_index ? &objects[i] : NULL; }
static int unit_can_use_weapon(long u, long i) { (void)u; (void)i; return can_use; }
static char const *tag_get_name(long d) { (void)d; return "weapons\\pistol\\pistol"; }
static void object_activate(long i) { (void)i; }
static void object_set_position(long i, real_point3d const *p, real_vector3d const *f, real_vector3d const *u) { (void)f; (void)u; objects[i].object.position = *p;
    objects[i].object.bounding_sphere_center = *p; }
/* the eyes' line to a gun lying on the ground: the ground meets it first
 * unless aimed over its middle (ground_hit: the ground's height there) */
static int collision_test_vector(unsigned f, real_point3d const *from, real_vector3d const *ray, long u, struct collision_result *hit)
{
    (void)f; (void)u; hit->type = 0; hit->object_index = NONE;
    real_point3d end = {{from->x + ray->i, from->y + ray->j, from->z + ray->k}};
    if (ground_hit && end.z < 0.02f) { hit->t = 0.80f; return 1; }
    return 0;
}
static int player_vr_take_weapon(long p, long i) { (void)p; taken++; taken_index = i; objects[i].object.parent_object_index = 9; return 1; }
static void render_debug_sphere(int b, real_point3d const *p, float r, real_argb_color const *c) { (void)b; (void)p; (void)r; (void)c; }
static void render_debug_line(int b, real_point3d const *p, real_point3d const *q, real_argb_color const *c) { (void)b; (void)p; (void)q; (void)c; }
''' + pull + r'''
static void tick(void) { now++; vr_weapon_pickup_tick(0); }
static void setup(void)
{
    memset(objects, 0, sizeof objects); memset(grip, 0, sizeof grip); memset(owner, 0, sizeof owner);
    objects[1].definition_index = 7; objects[1].object.parent_object_index = NONE; objects[1].object.flags = FLAG(_object_connected_to_map_bit);
    /* a pistol lying 2.5 m ahead on the ground (its middle 1 cm up) */
    objects[1].object.position = objects[1].object.bounding_sphere_center = (real_point3d){{2.5f, 0, 0.01f}};
    objects[1].object.bounding_sphere_radius = .12f;
    hands[0] = (real_point3d){{0.3f, 0.2f, 1.2f}}; hands[1] = (real_point3d){{0.3f, -0.2f, 1.2f}};
    real_vector3d at = {{2.2f, -0.2f, -1.19f}}; normalize3d(&at); forwards[0] = at; forwards[1] = at;
    player_unit.object.parent_object_index = NONE;
    weapon_hand = 1; hand_empty = 0; tracked = 1; can_use = 1; ground_hit = 1; taken = 0; taken_index = NONE; weapon_hand_set = -1;
    enabled = 1; reach = 3.0; strcpy(style, "flick");
    vr_weapon_pickup_reset(); tick();
}
int main(void)
{
    /* 1. the free (left) hand points at it: marked, through the ground's
     *    graze (the Test65 line of sight refused it) */
    setup(); tick(); assert(pickup.hand[0].candidate == 1);
    /* 2. squeeze: locked; flick back toward the body: thrown */
    grip[0] = 1; tick(); assert(pickup.hand[0].state == PULL_LOCKED && strstr(logged, "locked on"));
    tick(); assert(pickup.hand[0].state == PULL_LOCKED); /* held still: no throw yet */
    hands[0].x -= 0.08f; tick(); assert(pickup.hand[0].state == PULL_FLYING && strstr(logged, "throws"));
    /* 3. it flies: over the line between (an arc), nearer each tick */
    {
        real previous = distance3d(&objects[1].object.position, &hands[0]); int over = 0;
        for (int t = 0; t < 30 && pickup.hand[0].state == PULL_FLYING; t++) {
            real_point3d before = objects[1].object.position; tick();
            if (pickup.hand[0].state != PULL_FLYING) break;
            real d = distance3d(&objects[1].object.position, &hands[0]); assert(d < previous); previous = d;
            real s = (real)(now - pickup.hand[0].start_tick) / (real)pickup.hand[0].duration;
            real line = pickup.hand[0].start.z + (hands[0].z - pickup.hand[0].start.z) * (s * s * (3 - 2 * s));
            if (objects[1].object.position.z > line + 0.05f) over = 1;
            (void)before;
        }
        assert(over);
    }
    /* 4. a closed hand catches it: taken into that hand */
    assert(taken == 1 && taken_index == 1 && weapon_hand_set == 0 && strstr(logged, "caught in hand 0"));
    /* 5. let go in flight: it arrives at an open hand and drops */
    setup(); tick(); grip[0] = 1; tick(); hands[0].x -= 0.08f; tick(); assert(pickup.hand[0].state == PULL_FLYING);
    grip[0] = 0; for (int t = 0; t < 30 && pickup.hand[0].state == PULL_FLYING; t++) tick();
    assert(taken == 0 && strstr(logged, "drops"));
    /* 6. GRIP style: kept squeezed a little over half a second, no flick */
    setup(); strcpy(style, "grip"); tick(); grip[0] = 1; tick();
    for (int t = 0; t < 17; t++) { tick(); assert(pickup.hand[0].state == PULL_LOCKED); }
    tick(); tick(); assert(pickup.hand[0].state == PULL_FLYING);
    /* 7. let go before the flick: nothing thrown */
    setup(); tick(); grip[0] = 1; tick(); grip[0] = 0; tick(); assert(pickup.hand[0].state == PULL_IDLE && strstr(logged, "let go before"));
    /* 8. the gun hand holding its gun: refused, and it says so */
    setup(); tick(); grip[1] = 1; tick(); assert(pickup.hand[1].state == PULL_IDLE && strstr(logged, "gun hand holds its gun"));
    /* ... an empty gun hand pulls */
    setup(); hand_empty = 1; tick(); grip[1] = 1; tick(); assert(pickup.hand[1].state == PULL_LOCKED);
    /* 9. pointed away: nothing marked, and a squeeze says how far the nearest lies */
    setup(); forwards[0] = (real_vector3d){{-1, 0, 0}}; tick(); assert(pickup.hand[0].candidate == NONE);
    grip[0] = 1; tick(); assert(strstr(logged, "the nearest lies"));
    /* 10. beyond PULL REACH, or WEAPON PULL off: nothing */
    setup(); reach = 1.0; tick(); assert(pickup.hand[0].candidate == NONE);
    setup(); enabled = 0; tick(); assert(pickup.hand[0].candidate == NONE && pickup.hand[0].state == PULL_IDLE);
    /* 11. the off hand at the gun's support grip steadies the gun: no pull */
    setup(); hands[0] = (real_point3d){{0.3f, -0.1f, 1.2f}}; tick(); assert(pickup.hand[0].candidate == NONE);
    puts("PASS: Test66 WEAPON PULL: a free hand marks a gun on the ground (in sight through the ground's graze), locks with a squeeze, a flick throws it in an arc closing on the hand, a closed hand catches it, an open hand lets it drop; GRIP style; the gun hand refused with the reason; reach, the switch and the support grip respected");
    return 0;
}
'''

MATH = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "port/linux/game/vr_parkour_math.h"
int main(void)
{
    float wall[3] = {1, 0, 0}, rock[3] = {0.83f, 0, 0.55f}, hill[3] = {0.60f, 0, 0.80f}, overhang[3] = {0.85f, 0, -0.52f};
    float steep_low[3] = {0.88f, 0, 0.47f};
    /* a wall, a rock face of ~57 degrees and an overhang run; a hill does not */
    assert(vr_pk_runnable(wall, 0) && vr_pk_runnable(rock, 0) && vr_pk_runnable(overhang, 0) && !vr_pk_runnable(hill, 0));
    /* the knee-high probe wants a real wall: a steep slope underfoot is none */
    assert(vr_pk_runnable(wall, 1) && !vr_pk_runnable(steep_low, 1));
    /* round a bend: the facing eases toward the face met, unit length */
    float facing[3] = {1, 0, 0}, bend[3] = {0.866f, 0.5f, 0};
    vr_pk_blend_normal(facing, bend);
    assert(facing[1] > 0.1f && facing[1] < 0.4f && fabsf(facing[0] * facing[0] + facing[1] * facing[1] - 1) < 1e-4f);
    /* a corner past ~80 degrees is taken whole */
    float corner[3] = {0, 1, 0}; facing[0] = 1; facing[1] = 0; facing[2] = 0;
    vr_pk_blend_normal(facing, corner); assert(facing[1] == 1 && facing[0] == 0);
    puts("PASS: Test66 wall run faces: walls, rock faces to ~53 degrees and overhangs run, a hill does not, the knee probe wants a wall; the facing eases round a bend, a sharp corner is taken whole");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test66-") as directory:
    path = Path(directory)
    for name, code in (("pull", PULL), ("wall", MATH)):
        (path / f"{name}.c").write_text(code, encoding="utf-8")
        subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function", "-Wno-unused-parameter",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-I", str(ROOT),
                        str(path / f"{name}.c"), "-lm", "-o", str(path / name)], check=True)
        subprocess.run([str(path / name)], check=True)

# pins
render = read("port/linux/game/vr_render.c")
assert "vr_vehicle_handles_steady())\n\t{\n\t\tstatic double strayed_logged;" in render
assert "the head marker strayed %.0f cm" in render
math = read("port/linux/game/vr_vehicle_controls_math.h")
assert "#define VR_WHEEL_TURN_LIMIT 2.0943951f" in math and "static float vr_wheel_grip_follow(" in math
units = read("source/units/units.c")
assert "damage_data.multiplier = vr_combat_damage_share();" in units
damage = read("source/objects/damage.c")
assert "damage_definition->category == _damage_category_melee ?" in damage and "vr_combat_defend(object_index, damage->owner_object_index) : 1.0f" in damage
npc = read("port/linux/game/vr_npc_interaction.c")
assert "collision_model_touch_sphere(&model,&point,surface_reach,&model_node)" in npc
assert "static void npc_keep_held(void)" in npc and "npc_keep_held();" in npc
assert "its root brought to the body in the hands" in npc
world = read("port/linux/game/vr_world_interaction.c")
assert 'double strength = config_real("vr.object_throw");' in world and "OBJECT THROW: a vehicle let go" in world
frame = read("port/linux/src/vr_frame.c")
assert "void vr_weapon_hand_preferred(void)" in frame and "eyes_from_neck" in frame
assert "vr_weapon_hand_preferred();" in render
config = read("port/linux/src/port_config.c")
for key, value in (("vr.grenade_chest_down", "0.60"), ("vr.grenade_chest_forward", "0.12"), ("vr.grenade_chest_spread", "0.18"),
                   ("vr.object_throw", "2.0"), ("vr.npc_grab_assist", "0.10"), ("vr.weapon_pull_reach", "3.0")):
    assert re.search(r'\{ "%s", _config_real, "%s",' % (re.escape(key), re.escape(value)), config), key
for key in ("display.fov", "display.viewmodel_fov", "display.viewmodel_visible", "display.viewmodel_shield",
            "display.first_person_legs", "display.shield_glow", "display.shield_glow_intensity", "display.shield_color"):
    assert f'{{ "{key}",' in config, key
menu = read("port/linux/game/vr_menu.c")
assert '{ "VEHICLES", 8 }, { "VEHICLE OPTIONS", 6 }, { "WARTHOG + GHOST", 8 }, { "TANK + BANSHEE", 8 }' in menu
assert '"LEFT-HAND MODE", "vr.left_handed"' in menu and '"SHIELD COLOR", "display.shield_color"' in menu
view = read("port/linux/game/view_fov.c")
assert view.count("if (vr_active())") >= 3
legs = read("port/linux/game/first_person_legs.c")
assert "if (vr_active())\n\t\treturn FALSE;" in legs
print("PASS: Test66 wiring (seat eyes held per seat, the wheel's turn past half a circle, fist damage as the multiplier, block/parry, grab assist from the surface, held bodies kept, OBJECT THROW, LEFT-HAND MODE, waist grenades, the IMMERSION vehicle topics, OpenCE Build 201 display options with VR's own projection, gun and body)")

# Host-only internet signalling has no several-join peer keys. Do not send
# a fabricated all-zero seed to upstream clients. A real key still works.
p2p = read("port/linux/src/p2p.c")
start = p2p.index("int p2p_peer_key_hash(")
end = p2p.index("/* Map sharing between", start)
seed_check = r"""
#include <assert.h>
#include <string.h>
#define P2P_IDENTIFIER_SIZE 16
#define P2P_KEY_HASH_SIZE 32
struct peer { unsigned char identifier[16], key_hash[32]; } seed;
static struct { int running; } p2p;
static int p2p_lock, locks;
static void pthread_mutex_lock(int *p) { (void)p; ++locks; }
static void pthread_mutex_unlock(int *p) { (void)p; --locks; }
static struct peer *find_peer_by_address(unsigned long a) { return a == 7 ? &seed : 0; }
""" + p2p[start:end] + r"""
int main(void) {
 unsigned char id[16], key[32];
 memset(id, 0x55, sizeof(id)); memset(key, 0x55, sizeof(key));
 assert(!p2p_peer_key_hash(7,id,key));
 p2p.running=1;
 assert(!p2p_peer_key_hash(8,id,key));
 assert(!p2p_peer_key_hash(7,id,key));
 assert(id[0]==0x55 && key[0]==0x55 && locks==0);
 seed.identifier[0]=0x42; seed.key_hash[31]=0x77;
 assert(p2p_peer_key_hash(7,id,key));
 assert(id[0]==0x42 && key[31]==0x77 && locks==0);
 return 0;
}
"""
with tempfile.TemporaryDirectory(prefix="test66-seeds-") as temp:
    source = Path(temp) / "seeds.c"
    binary = Path(temp) / "seeds"
    source.write_text(seed_check)
    subprocess.run(["clang", "-std=gnu89", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("PASS: map seed advertising rejects missing/zero keys, retains valid keys, and unlocks every path")
