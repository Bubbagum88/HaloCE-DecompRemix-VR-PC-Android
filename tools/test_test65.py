"""Test65: the owner's 2026-10-13 requests (logs and videos of 2026-10-12).

- The Warthog's "weird purple part" was the Banshee's flight yoke drawn over
  the Warthog's own wheel; GRIP GUIDE (off) marks the grips instead.
- COCKPIT LOCK: the eyes, the hands and the immersive controls turn with the
  vehicle as drawn (the wheel and camera "snap"/were not stable).
- HAND SWAP: the palms-together swap reach is the player's (10 cm, was 20).
- A Shade turret in the hands killed its holder (vehicle-on-biped crush).
- Held friendly NPCs died; thrown corpses vanished; touching NPCs did nothing.
- ACTIVE RAGDOLL, GRAB RAGDOLL, WEAPON PULL, the Arkham Shadow fist combat
  (its compiled checks are in test_test62_extra; held impacts in
  test_interaction_impact; the turret in test_vr_world_physics; the wheel in
  test_test61_vehicle_hold).
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
handles = read("port/linux/game/vr_vehicle_handles.h")
render = read("port/linux/game/vr_render.c")
frame = read("port/linux/src/vr_frame.c")
vrh = read("port/linux/src/vr.h")
config = read("port/linux/src/port_config.c")
menu = read("port/linux/game/vr_menu.c")
physics = read("source/physics/physics.c")
world = read("port/linux/game/vr_world_interaction.c")
units = read("source/units/units.c")
damage = read("source/objects/damage.c")
npc = read("port/linux/game/vr_npc_interaction.c")
impact = read("port/linux/game/vr_interaction_impact.c")
extra = read("port/linux/game/vr_extra_interaction.c")
objects_render = read("source/render/render_objects.c")
player_control = read("source/game/player_control.c")
players = read("source/game/players.c")
pickup = read("port/linux/game/vr_weapon_pickup.c")
reactions = read("port/linux/game/vr_body_reactions.c")


def fn(text, name):
    """the definition of `name` (a prototype before it is skipped)"""
    at = text.index(name)
    while True:
        brace, semicolon = text.find("{", at), text.find(";", at)
        if brace != -1 and (semicolon == -1 or brace < semicolon):
            break
        at = text.index(name, at + 1)
    start = text.rindex("\n", 0, at) + 1
    body = text.index("{", start)
    depth = 0
    for i in range(body, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1] + "\n"
    raise AssertionError(name)


def default(key, kind, value):
    assert re.search(r'\{ "%s", %s, "%s",' % (re.escape(key), kind, re.escape(value)), config), key


# 1. the purple part: the Warthog's own wheel has its own branch, before the
# drive stick, the handlebar and the Banshee's yoke (the final else)
draw = fn(handles, "boolean vr_render_vehicle_controls(void)")
assert draw.index("} else if(vr_wheel.kind==0) {") < draw.index("} else if(vr_wheel.kind==2) {") < \
    draw.index("} else if(vr_wheel.kind==1) {") < draw.index("/* Banshee: a Covenant flight yoke")
assert "if(vr_wheel.grip_guide) {" in draw
default("vr.vehicle_grip_guide", "_config_boolean", "false")
assert '"GRIP GUIDE", "vr.vehicle_grip_guide"' in menu

# 2. COCKPIT LOCK: on by default with the immersive controls; the renderer
# gives the drawn seat frame before the eyes are placed; HORIZON's own tilt
# steps aside; the wheel is placed in the same frame
default("vr.vehicle_cockpit_lock", "_config_boolean", "true")
assert '"COCKPIT LOCK", "vr.vehicle_cockpit_lock"' in menu
stereo = render[render.index("vr_cockpit_update();"):]
assert stereo.index("vr_cockpit_update();") < stereo.index("eye_camera(eye, &windows[window].rasterizer_camera")  # (Test72: each eye's window, vr.eye_order)
update = fn(render, "static void vr_cockpit_update(")
assert "vr_vehicle_handles_steady()" in update and "vr_render.seat.driver" in update and 'config_boolean("vr.vehicle_cockpit_lock")' in update
assert "vr_set_cockpit_frame((float)NAN, NULL, NULL, NULL);" in update
tilt = fn(render, "static void vr_vehicle_tilt_view(")
assert "vr_cockpit_frame(cockpit[0], cockpit[1], cockpit[2]) ||" in tilt
assert "if(vr_cockpit_frame(cockpit[0],cockpit[1],cockpit[2])) {" in fn(handles, "static void vr_wheel_hand_frame(")
assert "void vr_set_cockpit_frame(float heading" in vrh and "int vr_cockpit_frame(" in vrh
aim = fn(frame, "int vr_aim(")
assert "vr.heading_from_seat = base_heading != NULL;" in aim and "if (vr_cockpit_active())" in aim

# 3. HAND SWAP
default("vr.hand_swap_distance", "_config_real", "0.1")
assert "vr.hand_swap_distance > 0.0f && hands_apart < vr.hand_swap_distance && !vr.grip_held[w]" in frame
assert "hands_apart < 0.2f && !vr.grip_held[w]" not in frame
controls = menu[menu.index("static struct vr_menu_setting const vr_menu_controls[] ="):]
controls = controls[:controls.index("};")]
# (Test72: the TWO HANDS row is VR_IMMERSION_TWO_HANDS, shared with IMMERSION)
assert '#define VR_IMMERSION_TWO_HANDS { "TWO HANDS", "vr.two_handed",' in menu
assert controls.index('VR_IMMERSION_TWO_HANDS') < controls.index('"HAND SWAP", "vr.hand_swap_distance"')
assert '{ "OFF", "0" }, { "6 CM", "0.06" }, { "8 CM", "0.08" }, { "10 CM", "0.1" }' in controls

# 4. the turret: the engine's vehicle-on-biped crush spares the holder
crush = fn(physics, "static boolean physics_compute_biped_collision(")
assert "int held_by_biped = vr_world_interaction_protects(instance->object_index, biped_index);" in crush
assert "if (held_by_biped == 2)\n\t\t\treturn FALSE;" in crush and "if (cause_damage && !held_by_biped)" in crush
assert "int vr_world_interaction_protects(long object, long biped)" in world

# 5. held NPCs (compiled in test_interaction_impact) and vanishing corpses
assert "#define VR_IMPACT_HOLD_GRACE_TICKS 15" in impact and "#define VR_IMPACT_HELD_SLAM_MPS 5.0f" in impact
settle = fn(npc, "void vr_npc_interaction_palette(")
assert "if(restore_garbage) npc_defer_garbage(index,u);" in settle
assert "limit=2*NPC_SETTLE_LIMIT_TICKS" in settle and "maximum=torso_step;" in settle
assert "npc_deferred_garbage_tick();" in fn(npc, "void vr_npc_interaction_tick(void)")

# 6. ACTIVE RAGDOLL and GRAB RAGDOLL
default("vr.active_ragdoll", "_config_boolean", "true")
default("vr.npc_lift_to_ragdoll", "_config_boolean", "true")
assert "#define NPC_LIFT_METRES 0.18f" in npc and "#define NPC_YANK_METRES_PER_SECOND 3.5f" in npc
assert "npc_touch_tick();" in fn(npc, "void vr_npc_interaction_tick(void)")
assert "vr_body_reaction_render(object_index," in objects_render
assert "vr_body_reaction_hold(index,(short)npc.node[h],&npc.target[h]);" in settle
assert "0.20f*MAX(0.0f,1.0f-(real)npc.settling/(real)MAX(npc_recovery_ticks(),1))" in settle
assert "int vr_npc_interaction_knock(long index," in npc and "npc.knocked=1;" in npc
# living recovery is never over a second: a knocked body uses NPC RECOVERY's limit
assert "int limit=dead?NPC_SETTLE_LIMIT_TICKS:npc_recovery_ticks()" in settle

# 7. the fists (behaviour compiled in test_test62_extra)
default("vr.combat_lunge_reach", "_config_real", "12.0")  # Test72: 12 m (8 before)
default("vr.combat_enemy_health", "_config_real", "3.0")
default("vr.combat_counters", "_config_boolean", "true")
assert "vr_head_view_recent(camera.n,unit_get(unit)->object.forward.n,head.n,gaze.n,up.n)" in fn(extra, "int vr_combat_punch(")
begin = fn(units, "boolean unit_melee_attack_begin(")
assert "vr_combat_note_melee(unit_index);" in begin
assert "vr_combat_note_damage(object_index);" in damage
assert "boolean unit_vr_combat_strike(" in units

# 8. WEAPON PULL
default("vr.weapon_pull_reach", "_config_real", "3.0")  # Test66: 3 m (1 to 5)
default("vr.weapon_pull", "_config_boolean", "true")  # Test66: the switch
default("vr.weapon_pull_style", "_config_string", chr(92) + chr(34) + "flick" + chr(92) + chr(34))
default("vr.weapon_pull_glow", "_config_boolean", "true")
assert player_control.index("vr_render_impact_melee(local_player_index);") < player_control.index("vr_weapon_pickup_tick(local_player_index);")
assert "boolean player_vr_take_weapon(" in players and "return player_vr_take_weapon(player_index, nearest_index);" in players
assert "game_connection()!=_game_connection_local" in pickup and "player_vr_take_weapon(player,index)" in pickup
assert "if(VR_RENDER_EYE()&&vr_weapon_pickup_render(vr_render.game_camera_position.n))extras=1;" in handles

# compiled: the view through a locked cockpit, and the drawn body reactions
view_code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
static struct { int cockpit_valid, heading_from_seat, heading_valid; float cockpit[3][3], heading, units_per_metre; } vr;
static float wrap_angle(float a) { while (a > 3.14159265f) a -= 6.28318531f; while (a < -3.14159265f) a += 6.28318531f; return a; }
''' + fn(frame, "static void rotate(") + fn(frame, "static void to_halo(") + fn(frame, "static int vr_cockpit_active(") + \
    fn(frame, "static void cockpit_to_halo(") + fn(frame, "void vr_set_cockpit_frame(") + fn(frame, "static void view(") + r'''
int main(void)
{
    static const float identity[4] = { 0, 0, 0, 1 }, ahead[3] = { 0, 0, -1 }, origin[3] = { 10, 20, 3 }, north[3] = { 0, 1, 0 };
    float p[3], f[3], u[3], pitch = 0.35f;
    float fwd[3] = { cosf(pitch), 0, sinf(pitch) }, left[3] = { 0, 1, 0 }, up[3] = { -sinf(pitch), 0, cosf(pitch) };
    vr.units_per_metre = 1; vr.heading_valid = 1;
    /* out of a seat the frame is never used, even if one was given */
    vr.heading_from_seat = 0; vr_set_cockpit_frame(0.0f, fwd, left, up);
    view(ahead, identity, origin, north, p, f, u);
    assert(fabsf(f[1] - 1) < 1e-5f && fabsf(p[1] - 21) < 1e-5f && fabsf(u[2] - 1) < 1e-5f);
    /* in the seat: the head's forward is the cockpit's (pitched up 20 deg) */
    vr.heading_from_seat = 1; vr_set_cockpit_frame(0.5f, fwd, left, up);
    assert(vr.cockpit_valid && fabsf(vr.heading - 0.5f) < 1e-6f);
    view(ahead, identity, origin, north, p, f, u);
    for (int i = 0; i < 3; i++) assert(fabsf(f[i] - fwd[i]) < 1e-5f && fabsf(u[i] - up[i]) < 1e-5f && fabsf(p[i] - origin[i] - fwd[i]) < 1e-5f);
    /* a bad frame is no frame; NULL keeps the heading only */
    { float bad[3] = { NAN, 0, 0 }; vr_set_cockpit_frame(0.25f, bad, left, up); assert(!vr.cockpit_valid && fabsf(vr.heading - 0.25f) < 1e-6f); }
    vr_set_cockpit_frame(NAN, NULL, NULL, NULL); assert(!vr.cockpit_valid && fabsf(vr.heading - 0.25f) < 1e-6f);
    puts("PASS: Test65 COCKPIT LOCK view: the seat's frame turns the head (and hands) only in a seat; a bad frame is dropped");
    return 0;
}
'''
react_code = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;
typedef union { struct { float x, y, z; }; float n[3]; } real_point3d;
typedef union { struct { float i, j, k; }; float n[3]; } real_vector3d;
typedef struct { real scale; real_vector3d forward, left, up; real_point3d position; } real_matrix4x3;
typedef int boolean;
#define NONE (-1)
#define PIN(v, a, b) ((v) < (a) ? (a) : (v) > (b) ? (b) : (v))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define TEST_FLAG(v, b) (((v) >> (b)) & 1)
#define MAXIMUM_NODES_PER_MODEL 64
#define TAG_BLOCK_GET_ELEMENT(b, i, t) ((t *)((b)->address) + (i))
enum { _object_type_biped = 1, _object_dead_bit = 0 };
struct object_datum { long definition_index; struct { int type; unsigned damage_flags; struct { long size; } node_matrices; } object; };
struct object_definition { struct { struct { long index; } model; } object; };
struct model_node { char name[32]; short parent_node_index; };
struct model { struct { int count; struct model_node *address; } nodes; };
static struct model_node names[5] = { { "bip01", -1 }, { "bip01 spine", 0 }, { "bip01 l upperarm", 1 }, { "bip01 l forearm", 2 }, { "bip01 l hand", 3 } };
static struct model model = { { 5, names } };
static struct object_definition definition = { { { 3 } } };
static struct object_datum body = { 1, { _object_type_biped, 0, { 5 * sizeof(real_matrix4x3) } } };
static real_matrix4x3 nodes[5];
static double clock_now = 10;
static double vr_pose_time(void) { return clock_now; }
static int config_boolean(char const *k) { (void)k; return 1; }
static struct object_datum *object_try_and_get(long i) { return i == 5 ? &body : NULL; }
static struct object_datum *object_get(long i) { (void)i; return &body; }
static struct object_definition *object_definition_get(long i) { (void)i; return &definition; }
static struct model *model_definition_get(long i) { (void)i; return &model; }
static real_matrix4x3 *object_get_node_matrices(long i) { (void)i; return nodes; }
static real_vector3d up_axis = { { 0, 0, 1 } }, *global_up3d = &up_axis;
static real dot_product3d(real_vector3d const *a, real_vector3d const *b) { return a->i * b->i + a->j * b->j + a->k * b->k; }
static real normalize3d(real_vector3d *v) { real m = sqrtf(dot_product3d(v, v)); if (m > 0) for (int k = 0; k < 3; k++) v->n[k] /= m; return m; }
static void cross_product3d(real_vector3d const *a, real_vector3d const *b, real_vector3d *c) { real_vector3d r = { { a->j * b->k - a->k * b->j, a->k * b->i - a->i * b->k, a->i * b->j - a->j * b->i } }; *c = r; }
static void vector_from_points3d(real_point3d const *a, real_point3d const *b, real_vector3d *v) { for (int k = 0; k < 3; k++) v->n[k] = b->n[k] - a->n[k]; }
static void point_from_line3d(real_point3d const *p, real_vector3d const *v, real s, real_point3d *o) { for (int k = 0; k < 3; k++) o->n[k] = p->n[k] + v->n[k] * s; }
static real distance_squared3d(real_point3d const *a, real_point3d const *b) { real_vector3d d; vector_from_points3d(a, b, &d); return dot_product3d(&d, &d); }
static int valid_real_point3d(real_point3d const *p) { return isfinite(p->x) && isfinite(p->y) && isfinite(p->z); }
static int valid_real_vector3d(real_vector3d const *v) { return isfinite(v->i) && isfinite(v->j) && isfinite(v->k); }
void platform_log(char const *f, ...) { (void)f; }
''' + re.sub(r'^#include[^\n]*\n', '', reactions, flags=re.M).replace('#ifdef HALO_VR', '', 1).rsplit('#endif', 1)[0] + r'''
static real length(real_matrix4x3 const *m, int a, int b) { real_vector3d d; vector_from_points3d(&m[a].position, &m[b].position, &d); return sqrtf(dot_product3d(&d, &d)); }
int main(void)
{
    static const float places[5][3] = { { 0, 0, 0 }, { 0, 0, 1 }, { 0, .2f, 1.4f }, { 0, .2f, 1.1f }, { 0, .2f, .85f } };
    real_matrix4x3 *pose;
    real_point3d hand = { { 0, .2f, .85f } };
    real_vector3d push = { { 1, 0, 0 } };
    vr_body_reactions_reset();
    for (int n = 0; n < 5; n++) { nodes[n].scale = 1; nodes[n].forward.i = nodes[n].left.j = nodes[n].up.k = 1; memcpy(nodes[n].position.n, places[n], 12); }
    assert(vr_body_reaction_render(5, nodes) == nodes); /* nothing yet */
    vr_body_reaction_hit(5, &hand, &push, 1.0f);
    clock_now += 0.06;
    pose = vr_body_reaction_render(5, nodes);
    assert(pose != nodes && pose[4].position.x > 0.05f); /* the struck hand swings with the push */
    assert(pose[1].position.x == nodes[1].position.x); /* the spine's pivot stays */
    assert(fabsf(length(pose, 2, 3) - length(nodes, 2, 3)) < 1e-4f && fabsf(length(pose, 3, 4) - length(nodes, 3, 4)) < 1e-4f);
    assert(nodes[4].position.x == 0); /* the stock pose is untouched */
    clock_now += 2.0;
    assert(vr_body_reaction_render(5, nodes) == nodes); /* eased out and forgotten */
    /* a held limb reaches toward the hand */
    { real_point3d target = { { .5f, .2f, 1.4f } }; real before, after; real_vector3d d;
      vr_body_reaction_hold(5, 4, &target); clock_now += 0.2; pose = vr_body_reaction_render(5, nodes);
      vector_from_points3d(&nodes[4].position, &target, &d); before = sqrtf(dot_product3d(&d, &d));
      vector_from_points3d(&pose[4].position, &target, &d); after = sqrtf(dot_product3d(&d, &d));
      assert(after < before - 0.1f); }
    /* a corpse does not react */
    body.object.damage_flags = 1; vr_body_reaction_hit(5, &hand, &push, 1.0f); clock_now += 0.06;
    assert(vr_body_reaction_render(5, nodes) == nodes);
    puts("PASS: Test65 ACTIVE RAGDOLL reactions: a struck limb swings with the blow (lengths kept), a held limb reaches for the hand, both ease out; corpses and the stock pose untouched");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="test65-") as temp:
    path = Path(temp)
    for name, code in (("view", view_code), ("reactions", react_code)):
        (path / (name + ".c")).write_text(code)
        subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function", "-Wno-unused-parameter",
                        "-Wno-missing-field-initializers", "-Wno-missing-braces", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        str(path / (name + ".c")), "-lm", "-o", str(path / name)], check=True)
        subprocess.run([str(path / name)], check=True)
print("PASS: Test65 wiring: the Warthog's wheel without the Banshee's yoke (GRIP GUIDE off), COCKPIT LOCK, HAND SWAP 10 cm, held vehicles never crush, held-body impacts, corpses kept until they rest, ACTIVE/GRAB RAGDOLL, fists (lunge/counters/health), WEAPON PULL")
