/* Optional physical reloads for verified stock first-person model profiles.
 * Game ammo is committed exactly once through weapons.c's native transaction.
 * This module owns transient grip/visual state only; it never saves ammo. */
#ifdef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "game/players.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "objects/objects.h"
#include "units/units.h"
#include "items/weapons.h"
#include "items/weapon_definitions.h"
#include "models/model_definitions.h"
#include "models/models.h"
#include "tag_files/tag_files.h"
#include "physics/collisions.h"
#include "physics/collision_features.h"
#include "physics/physics.h"
#include "render/render.h"
#include "render/render_cameras_internal.h"
#include "../src/port_config.h"
#include "../src/vr.h"
#include "vr_manual_reload.h"
#include "vr_manual_reload_math.h"
#include "vr_reload_contact_math.h"
#include "vr_magazine_debris_math.h"

void platform_log(char const *format, ...);
enum { RELOAD_MAGAZINE, RELOAD_SHELL, RELOAD_TUBES, RELOAD_CANISTER, RELOAD_CRYSTALS };
struct reload_profile { char const *path, *ammo, *chamber; int kind; };
static struct reload_profile const profiles[] = {
    { "weapons\\assault rifle\\fp\\fp", "frame magazine", "frame ophandle", RELOAD_MAGAZINE },
    { "weapons\\pistol\\fp\\fp", "frame magazine", "frame slide", RELOAD_MAGAZINE },
    { "weapons\\sniper rifle\\fp\\fp", "frame magazine", "frame ophandle", RELOAD_MAGAZINE },
    { "weapons\\shotgun\\fp\\fp", "frame bullet", "frame pump", RELOAD_SHELL },
    { "weapons\\rocket launcher\\fp\\fp", "frame tubes", "frame push_bar", RELOAD_TUBES },
    { "weapons\\flamethrower\\fp\\fp", "frame ammo", "frame cover", RELOAD_CANISTER },
    { "weapons\\needler\\fp\\fp", "frame needle01", "frame body", RELOAD_CRYSTALS },
};
static struct {
    struct vr_mr_state state;
    long weapon, model;
    short magazine, chamber;
    int ready, hand, have_attachment, kind, aligned;
    double sample_time, insertion_time, grip_time;
    real_matrix4x3 socket, charge, gun, attachment, held, insertion_local;
    real_point3d charge_start;
    real_point3d previous_hand;
    real_vector3d hand_velocity;
    real_point3d camera;
    real chamber_travel;
    unsigned long long component_nodes;
    int bounds_tried, bounds_valid[2];
    int hand_sample_valid, debris_pending;
    real_point3d bounds_min[2], bounds_max[2];
} reload;
struct dropped_magazine {
    int active, node_count;
    long model, owner_unit;
    unsigned long long nodes;
    real radius;
    real_point3d center;
    real_vector3d velocity;
    real_rgb_color colors[NUMBER_OF_OBJECT_CHANGE_COLORS];
    real function_values[NUMBER_OF_OUTGOING_OBJECT_FUNCTIONS];
    real_matrix4x3 matrices[MAXIMUM_NODES_PER_MODEL];
};
static struct dropped_magazine dropped_magazines[VR_MAGAZINE_DEBRIS_CAPACITY];
static boolean dropped_magazines_have_state;
static boolean dropped_magazines_full_reported;
static int cancelled_phase;
static long cancelled_weapon;
static boolean reload_local_weapon(long weapon_index, long *unit_out);
static boolean reload_matrix_valid(real_matrix4x3 const *matrix);
static long bounds_logged_weapon = NONE, bounds_logged_model = NONE;
static boolean bounds_log_initialized;

void vr_manual_reload_reset(void)
{
    if (reload.state.phase != VR_MR_IDLE) {
        cancelled_phase=reload.state.phase; cancelled_weapon=reload.weapon;
    }
    vr_interaction_release(0, VR_INTERACTION_RELOAD);
    vr_interaction_release(1, VR_INTERACTION_RELOAD);
    memset(&reload, 0, sizeof(reload));
    reload.weapon = reload.model = NONE;
    reload.magazine = reload.chamber = NONE;
}

void vr_manual_reload_debris_reset(void)
{
	if (!dropped_magazines_have_state) return;
    memset(dropped_magazines, 0, sizeof(dropped_magazines));
	dropped_magazines_have_state = FALSE;
    dropped_magazines_full_reported = FALSE;
}

static void debris_spawn_from_reload(struct model *model, real_matrix4x3 *matrices)
{
    int active[VR_MAGAZINE_DEBRIS_CAPACITY];
    int slot_index;
    real_matrix4x3 inverse, delta;
    struct dropped_magazine *slot;
    struct object_datum *source_weapon;
    real bound = 0.0f;
    real scale;
    long unit_index = NONE;
    if (!model || !matrices || !reload.debris_pending) return;
    reload.debris_pending = 0;
    if (!config_boolean("vr.dropped_magazines") || game_connection() != _game_connection_local ||
        reload.kind != RELOAD_MAGAZINE || !reload.component_nodes ||
        model->nodes.count <= 0 || model->nodes.count > MAXIMUM_NODES_PER_MODEL ||
        !reload.bounds_valid[0] || !reload_local_weapon(reload.weapon, &unit_index)) return;
    source_weapon = object_try_and_get_and_verify_type(reload.weapon, _object_mask_weapon);
    if (!source_weapon) return;
    if (!vr_magazine_debris_spawn_allowed(TRUE, TRUE, TRUE, model->nodes.count,
            reload.component_nodes, 0.01f, 0.20f)) return;
    matrix4x3_inverse(&reload.socket, &inverse);
    matrix4x3_multiply(&reload.held, &inverse, &delta);
    if (!reload_matrix_valid(&delta)) return;
    scale = fabsf(matrices[reload.magazine].scale * delta.scale);
    if (!isfinite(scale) || scale < 0.001f || scale > 100.0f) return;
    for (int axis = 0; axis < 3; ++axis) {
        real maximum = MAX(fabsf(reload.bounds_min[0].n[axis]), fabsf(reload.bounds_max[0].n[axis]));
        if (!isfinite(maximum)) return;
        bound += maximum * maximum;
    }
    bound = sqrtf(bound) * scale;
    if (!isfinite(bound) || bound < 0.001f || bound > 0.20f * vr_units_per_metre()) return;
    for (int i = 0; i < VR_MAGAZINE_DEBRIS_CAPACITY; ++i) {
        active[i] = dropped_magazines[i].active;
    }
    slot_index = vr_magazine_debris_choose_slot(active, VR_MAGAZINE_DEBRIS_CAPACITY);
    if (slot_index < 0) {
        if (!dropped_magazines_full_reported) {
            platform_log("VR reload debris: map-session pool full (%d); existing drops retained, new visuals skipped",
                VR_MAGAZINE_DEBRIS_CAPACITY);
            dropped_magazines_full_reported = TRUE;
        }
        return;
    }
    slot = &dropped_magazines[slot_index];
    memset(slot, 0, sizeof(*slot));
    slot->model = reload.model;
    slot->owner_unit = unit_index;
    slot->node_count = (int)model->nodes.count;
    slot->nodes = reload.component_nodes;
    slot->radius = bound;
    slot->active = 1;
    memcpy(slot->colors, source_weapon->object.outgoing_change_colors, sizeof(slot->colors));
    memcpy(slot->function_values, source_weapon->object.outgoing_function_values, sizeof(slot->function_values));
    for (short node = 0; node < model->nodes.count; ++node) {
        slot->matrices[node] = matrices[node];
        if (reload.component_nodes & (1ULL << node)) {
            matrix4x3_multiply(&delta, &matrices[node], &slot->matrices[node]);
            if (!reload_matrix_valid(&slot->matrices[node])) { memset(slot, 0, sizeof(*slot)); return; }
        } else {
            slot->matrices[node].scale = 0.0f;
        }
    }
    slot->center = slot->matrices[reload.magazine].position;
    slot->velocity = reload.hand_velocity;
    if (!vr_magazine_debris_speed_valid(slot->velocity.n, 0.24f * vr_units_per_metre()))
        slot->velocity = *global_zero_vector3d;
    dropped_magazines_have_state = TRUE;
    platform_log("VR reload debris: spawned visual magazine slot=%d model=%ld nodes=%d radius=%.4f online=0",
        slot_index, slot->model, slot->node_count, slot->radius);
}

void vr_manual_reload_debris_tick(void)
{
    if (!config_boolean("vr.dropped_magazines") || game_connection() != _game_connection_local) {
        vr_manual_reload_debris_reset();
        return;
    }
    for (int index = 0; index < VR_MAGAZINE_DEBRIS_CAPACITY; ++index) {
        struct dropped_magazine *slot = &dropped_magazines[index];
        real_point3d next;
        real_vector3d clipped, displacement;
        struct collision_plane planes[4];
        short collisions;
        if (!slot->active) continue;
        if (slot->node_count <= 0 || slot->node_count > MAXIMUM_NODES_PER_MODEL ||
            !isfinite(slot->radius) || slot->radius <= 0.0f || slot->radius > 0.20f * vr_units_per_metre() ||
            !valid_real_point3d(&slot->center) || !valid_real_vector3d(&slot->velocity)) {
            memset(slot, 0, sizeof(*slot));
            continue;
        }
        slot->velocity.k -= global_gravity;
        if (!vr_magazine_debris_speed_valid(slot->velocity.n, 0.30f * vr_units_per_metre())) {
            slot->velocity = *global_zero_vector3d;
        }
        displacement = slot->velocity;
        collisions = collision_move_sphere(_collision_test_for_bipeds_dead_flags,
            &slot->center, &displacement, slot->radius, slot->owner_unit,
            &next, &clipped, 4, planes);
        if (!valid_real_point3d(&next) || !valid_real_vector3d(&clipped)) {
            memset(slot, 0, sizeof(*slot));
            continue;
        }
        if (collisions > 0) {
            slot->velocity = clipped;
            for (short plane = 0; plane < collisions && plane < 4; ++plane) {
                if (planes[plane].plane.n.k > 0.5f) {
                    slot->velocity.i *= 0.72f;
                    slot->velocity.j *= 0.72f;
                    if (fabsf(slot->velocity.k) < 0.015f * vr_units_per_metre()) slot->velocity.k = 0.0f;
                }
            }
        }
        for (short node = 0; node < slot->node_count; ++node) if (slot->nodes & (1ULL << node))
            for (int axis = 0; axis < 3; ++axis)
                slot->matrices[node].position.n[axis] += next.n[axis] - slot->center.n[axis];
        slot->center = next;
    }
}

void vr_manual_reload_debris_render(void)
{
    short local = local_player_get_next(NONE);
    long player = local != NONE ? local_player_get_player_index(local) : NONE;
    long unit = player != NONE ? player_get(player)->unit_index : NONE;
    struct render_lighting *lighting;
    if (game_connection() != _game_connection_local || unit == NONE ||
        !config_boolean("vr.dropped_magazines")) return;
    lighting = object_get_cached_render_lighting(unit, 100.0f);
    if (!lighting) return;
    for (int index = 0; index < VR_MAGAZINE_DEBRIS_CAPACITY; ++index) {
        struct dropped_magazine *slot = &dropped_magazines[index];
        real pixels;
        if (!slot->active) continue;
        if (slot->node_count <= 0 || slot->node_count > MAXIMUM_NODES_PER_MODEL) {
            memset(slot, 0, sizeof(*slot));
            continue;
        }
        pixels = render_frustum_sphere_diameter_in_pixels(&render.frustum, &slot->center, slot->radius);
        render_model(slot->model, pixels, slot->matrices, NULL,
            slot->colors, slot->function_values,
            lighting, &slot->center, slot->radius, NULL,
            0x5A000000 + index, 0, 0);
    }
}

static boolean reload_near(real_point3d const *a, real_point3d const *b, real radius)
{
    real x = a->x-b->x, y = a->y-b->y, z = a->z-b->z;
    return radius > 0 && x*x+y*y+z*z <= radius*radius;
}

static boolean reload_hand_touches_part(int part, real_matrix4x3 const *transform, real_point3d const *hand)
{
    real_point3d local;
    real radius, units=vr_units_per_metre();
    if(part<0 || part>1 || !reload.bounds_valid[part] || !transform || !hand ||
        !reload_matrix_valid(transform) || !(units>0.0f))return FALSE;
    double configured_contact=config_real("vr.interaction_reach");
    radius=(real)(isfinite(configured_contact)?PIN(configured_contact,0.02,0.08):0.04)*units;
    matrix4x3_inverse_transform_point(transform,hand,&local);
    return vr_reload_sphere_touches_box(local.n,reload.bounds_min[part].n,
        reload.bounds_max[part].n,radius/transform->scale);
}

static boolean reload_local_weapon(long weapon_index, long *unit_out)
{
    short local = local_player_get_next(NONE);
    long player = local != NONE ? local_player_get_player_index(local) : NONE;
    long unit = player != NONE ? player_get(player)->unit_index : NONE;
    if (unit == NONE || unit_inventory_get_weapon(unit, unit_get(unit)->unit.current_weapon_index) != weapon_index)
        return FALSE;
    *unit_out = unit;
    return object_get(unit)->object.parent_object_index == NONE &&
        !TEST_FLAG(object_get(unit)->object.damage_flags, _object_dead_bit) &&
        !cinematic_in_progress() && !director_inhibited_input(local);
}

void vr_manual_reload_note_weapon(long weapon_index)
{
    long unit = NONE;
    if (cancelled_phase) {
        platform_log("VR manual reload: cancelled weapon=%ld phase=%d; ammo unchanged",cancelled_weapon,cancelled_phase);
        cancelled_phase=0;
    }
    if (weapon_index == NONE || weapon_index != reload.weapon || !vr_active() ||
        !config_boolean("vr.manual_reload") || game_connection() != _game_connection_local ||
        !reload_local_weapon(weapon_index, &unit) || vr_hand_empty())
        vr_manual_reload_reset();
}

unsigned vr_manual_reload_update(long weapon_index, int explicit_reload)
{
    long unit_index = NONE;
    real units = vr_units_per_metre();
    real_point3d camera, hand, head, hip, shoulder, weapon_hand;
    real_vector3d forward, up, head_forward, head_up, left;
    real_matrix4x3 hand_matrix, inverse;
    struct weapon_datum *weapon;
    struct weapon_definition *definition;
    struct weapon_magazine *magazine;
    struct weapon_magazine_definition *magazine_definition;
    struct vr_mr_input input = {0};
    int event, hand_index = 1-vr_weapon_hand();
    boolean trigger_input = FALSE;
    unsigned int buttons;float triggers[2],thumbs[4];
    boolean current = reload_local_weapon(weapon_index, &unit_index);
    /* Other world/NPC weapons must not cancel the local transaction. */
    if (!current) {
        if (reload.weapon == weapon_index) vr_manual_reload_reset();
        return 0;
    }
    if (!vr_active() || !vr_controller(&buttons,triggers,thumbs) || !config_boolean("vr.manual_reload") ||
        game_connection() != _game_connection_local || !(units > 0) || vr_hand_empty() ||
        !reload.ready || reload.weapon != weapon_index || reload.hand != hand_index ||
        vr_pose_time()-reload.sample_time > 0.25 || vr_pose_time()<reload.sample_time) {
        vr_manual_reload_reset(); return 0;
    }
    trigger_input = vr_mr_input_uses_trigger(config_string("vr.reload_input"));
    weapon = weapon_get(weapon_index);
    if (!reload.bounds_tried) {
        reload.bounds_tried=1;
        reload.bounds_valid[0]=model_rigid_component_bounds(reload.model,reload.magazine,reload.component_nodes,&reload.bounds_min[0],&reload.bounds_max[0]);
        reload.bounds_valid[1]=model_rigid_node_bounds(reload.model,reload.chamber,&reload.bounds_min[1],&reload.bounds_max[1]);
        if (vr_mr_profile_changed(bounds_log_initialized, bounds_logged_weapon,
                bounds_logged_model, weapon_index, reload.model)) {
            platform_log("VR manual reload: authored contact bounds weapon=%ld model=%ld magazine=%d chamber=%d",
                weapon_index,reload.model,reload.bounds_valid[0],reload.bounds_valid[1]);
            bounds_logged_weapon=weapon_index;
            bounds_logged_model=reload.model;
            bounds_log_initialized=TRUE;
        }
    }
    definition = weapon_definition_get(weapon->definition_index);
    if (weapon->weapon.state == _weapon_state_primary_recoil && !explicit_reload &&
        reload.state.phase == VR_MR_IDLE) return VR_MANUAL_SUPPRESS_AUTO;
    if (definition->weapon.magazines.count != 1 || weapon->weapon.state != _weapon_state_idle ||
        TEST_FLAG(weapon->weapon.control_flags, _weapon_control_user_busy_bit) ||
        TEST_FLAG(weapon->weapon.control_flags, _weapon_control_user_switching_weapons_bit)) {
        vr_manual_reload_reset(); return 0;
    }
    magazine = &weapon->weapon.magazines[0];
    magazine_definition = TAG_BLOCK_GET_ELEMENT(&definition->weapon.magazines, 0, struct weapon_magazine_definition);
    if (magazine->state != _magazine_idle || magazine_definition->rounds_reloaded <= 0 ||
        magazine_definition->rounds_recharged_per_second != 0) { vr_manual_reload_reset(); return 0; }
    unit_get_camera_position(unit_index, &camera);
    reload.camera=camera;
    if (!vr_hand_world(vr_weapon_hand(), camera.n, weapon_hand.n, forward.n, up.n) ||
        !vr_hand_world(hand_index, camera.n, hand.n, forward.n, up.n) ||
        !vr_head_view(camera.n, object_get(unit_index)->object.forward.n, head.n, head_forward.n, head_up.n)) {
        vr_manual_reload_reset(); return 0;
    }
    matrix4x3_from_point_and_vectors(&hand_matrix, &hand, &forward, &up);
    if (reload.have_attachment) matrix4x3_multiply(&hand_matrix, &reload.attachment, &reload.held);
    /* Ammo follows the free hand's body side. Shoulder and hip are independently
     * enabled; handedness changes cancel/reacquire the transaction above. */
    head_forward.k = 0;
    if (normalize3d(&head_forward) <= 0.001f) { vr_manual_reload_reset(); return 0; }
    left.i = -head_forward.j; left.j = head_forward.i; left.k = 0;
    scale_vector3d(&left,vr_mr_pouch_side(hand_index),&left);
    for (int axis=0; axis<3; ++axis) {
        hip.n[axis] = head.n[axis] + left.n[axis]*0.22f*units;
        shoulder.n[axis] = head.n[axis] + left.n[axis]*0.20f*units - head_forward.n[axis]*0.10f*units;
    }
    hip.z -= 0.55f*units; shoulder.z -= 0.15f*units;
    /* The selected input applies only to the free-hand manual-reload state
     * machine. Other grab systems and game firing continue to use their usual
     * grip/weapon-trigger paths. */
    input.held = trigger_input ? vr_interaction_trigger(hand_index) :
        vr_interaction_grip(hand_index, NULL, NULL);
    input.valid = vr_interaction_owner(hand_index) == VR_INTERACTION_NONE ||
        vr_interaction_owner(hand_index) == VR_INTERACTION_RELOAD;
    input.explicit_reload = explicit_reload;
    input.loose_round = reload.kind == RELOAD_SHELL || reload.kind == RELOAD_CRYSTALS;
    input.no_chamber = reload.kind == RELOAD_CRYSTALS;
    input.seated = vr_pose_time()-reload.insertion_time >= 0.10;
    input.can_load = magazine->rounds_total > 0 && magazine->rounds_loaded < magazine_definition->rounds_loaded_maximum;
    if (reload.state.phase == VR_MR_IDLE &&
        (TEST_FLAG(weapon->weapon.control_flags, _weapon_control_primary_trigger_bit) ||
         TEST_FLAG(weapon->weapon.control_flags, _weapon_control_secondary_trigger_bit))) input.can_load = FALSE;
    /* Pickup begins only when the free hand's contact sphere overlaps the
     * authored magazine bounds. A center-to-socket reach radius is not touch. */
    input.near_mag = reload_hand_touches_part(0,&reload.socket,&hand);
    if (reload.state.phase == VR_MR_NEW_HELD) {
        real alignment = dot_product3d(&reload.held.forward, &reload.socket.forward);
        real up_alignment = dot_product3d(&reload.held.up, &reload.socket.up);
        input.near_mag = reload_component_bounds_touch(&reload.socket,&reload.held,0.005f*units) &&
            alignment > (reload.aligned ? 0.65f : 0.7f) && up_alignment > (reload.aligned ? 0.65f : 0.7f);
    }
    input.near_chamber = reload_hand_touches_part(1,&reload.charge,&hand);
    double configured_contact=config_real("vr.interaction_reach");
    real contact_radius=(real)(isfinite(configured_contact)?PIN(configured_contact,0.02,0.08):0.04)*units;
    input.near_pouch = vr_mr_pouch_enabled(config_boolean("vr.reload_hip"),config_boolean("vr.reload_shoulder"),
        reload_near(&hand,&hip,contact_radius),reload_near(&hand,&shoulder,contact_radius));
    if (reload.state.phase == VR_MR_NEW_HELD) {
        if (input.near_mag && !reload.aligned) vr_haptic(hand_index, 0.20f, 0.025f);
        reload.aligned = input.near_mag;
    } else reload.aligned = FALSE;
    input.magazine_out = reload.have_attachment && !reload_component_bounds_touch(&reload.socket,&reload.held,0.005f*units);
    if (reload.state.phase == VR_MR_CHAMBER_HELD) {
        real_point3d local_hand;
        matrix4x3_inverse_transform_point(&reload.gun, &hand, &local_hand);
        real travel = vr_mr_pull_distance(reload.charge_start.x, local_hand.x);
        reload.chamber_travel = travel > 0 ? (travel < 0.07f*units ? travel : 0.07f*units) : 0;
        input.chamber_pulled = travel >= 0.035f*units;
        /* Tube/canister assemblies use their authored latch/cover rather than
         * pretending they have an operating handle. A fresh grip and release
         * at that node closes the replacement assembly. */
        if (reload.kind == RELOAD_TUBES || reload.kind == RELOAD_CANISTER) {
            input.chamber_pulled = input.near_chamber;
            reload.chamber_travel = 0;
        }
    }
    {
        real_vector3d change;
        int moving = reload.state.phase == VR_MR_OLD_HELD || reload.state.phase == VR_MR_NEW_HELD;
        if (moving && reload.hand_sample_valid) {
            vector_from_points3d(&reload.previous_hand, &hand, &change);
            for (int axis = 0; axis < 3; ++axis)
                reload.hand_velocity.n[axis] = reload.hand_velocity.n[axis] * 0.35f + change.n[axis] * 0.65f;
            if (!vr_magazine_debris_speed_valid(reload.hand_velocity.n, 0.24f * units))
                reload.hand_velocity = *global_zero_vector3d;
        } else if (!moving) {
            reload.hand_velocity = *global_zero_vector3d;
        }
        reload.previous_hand = hand;
        reload.hand_sample_valid = TRUE;
    }
    {
        int previous_phase = reload.state.phase;
        event = vr_mr_step(&reload.state, &input);
        if (event == VR_MR_DISCARD && previous_phase == VR_MR_OLD_HELD)
            reload.debris_pending = TRUE;
    }
    if (event == VR_MR_INSERT) {
        matrix4x3_inverse(&reload.gun, &inverse);
        matrix4x3_multiply(&inverse, &reload.held, &reload.insertion_local);
        reload.insertion_time = vr_pose_time();
    }
    if (event == VR_MR_BEGIN || event == VR_MR_PICKUP || event == VR_MR_CHARGE) {
        if (!vr_interaction_claim_input(hand_index, VR_INTERACTION_RELOAD, input.held)) {
            vr_manual_reload_reset(); return 0;
        }
        reload.grip_time=vr_pose_time();
        if (event == VR_MR_BEGIN) {
            matrix4x3_inverse(&hand_matrix, &inverse);
            matrix4x3_multiply(&inverse, &reload.socket, &reload.attachment);
            reload.have_attachment = TRUE;
        }
        if (event == VR_MR_PICKUP && (reload.kind == RELOAD_SHELL || reload.kind == RELOAD_CRYSTALS)) {
            /* A loose shell starts at the hand; no invisible magazine-removal
             * phase or transfer of ammunition happens here. */
            reload.attachment = reload.socket;
            reload.attachment.position = hand;
            matrix4x3_inverse(&hand_matrix, &inverse);
            real_matrix4x3 attached = reload.attachment;
            matrix4x3_multiply(&inverse, &attached, &reload.attachment);
            reload.have_attachment = TRUE;
        }
        if (event == VR_MR_CHARGE) {
            matrix4x3_inverse_transform_point(&reload.gun, &hand, &reload.charge_start);
            reload.chamber_travel = 0;
        }
    }
    if (reload.have_attachment) matrix4x3_multiply(&hand_matrix, &reload.attachment, &reload.held);
    if (event != VR_MR_NONE) {
        platform_log("VR manual reload: input=%s weapon=%ld event=%d phase=%d rounds=%d reserve=%d",
            trigger_input ? "trigger" : "grip", weapon_index, event, reload.state.phase,
            magazine->rounds_loaded, magazine->rounds_total);
        vr_haptic(hand_index, event == VR_MR_COMMIT ? 0.65f : 0.35f, 0.045f);
    }
    if (!input.held || event == VR_MR_CANCEL || event == VR_MR_COMMIT)
        vr_interaction_release(hand_index, VR_INTERACTION_RELOAD);
    if (explicit_reload || !input.valid) return 0;
    return VR_MANUAL_SUPPRESS_AUTO |
        (reload.state.phase != VR_MR_IDLE ? VR_MANUAL_BLOCK_FIRE : 0) |
        (event == VR_MR_COMMIT ? VR_MANUAL_COMMIT : 0);
}

static boolean reload_node_under(struct model *model, short node, short root)
{
    int remaining = model->nodes.count;
    while (node >= 0 && node < model->nodes.count && remaining-- > 0) {
        if (node == root) return TRUE;
        node = TAG_BLOCK_GET_ELEMENT(&model->nodes, node, struct model_node)->parent_node_index;
    }
    return FALSE;
}

static boolean reload_matrix_valid(real_matrix4x3 const *m)
{
    if (!(m->scale > 0.001f && m->scale < 1000)) return FALSE;
    for (int row=0; row<4; ++row) for (int axis=0; axis<3; ++axis)
        if (!(m->n[row][axis] > -1000000 && m->n[row][axis] < 1000000)) return FALSE;
    return TRUE;
}

static boolean reload_component_bounds_touch(real_matrix4x3 const *socket,real_matrix4x3 const *held,real radius)
{
    real_point3d held_min={FLT_MAX,FLT_MAX,FLT_MAX},held_max={-FLT_MAX,-FLT_MAX,-FLT_MAX};
    real radius_local,distance2=0.0f;
    if(!reload.bounds_valid[0] || !socket || !held || !reload_matrix_valid(socket) ||
        !reload_matrix_valid(held) || !isfinite(radius) || radius<0.0f)return FALSE;
    radius_local=radius/socket->scale;
    if(!isfinite(radius_local))return FALSE;
    /* Transform the held magazine's authored bounds into socket space. A
     * successful seat needs actual component-bound contact, not origin range. */
    for(int corner=0;corner<8;corner++) {
        real_point3d part,world,local;
        for(int axis=0;axis<3;axis++)
            part.n[axis]=(corner&(1<<axis))?reload.bounds_max[0].n[axis]:reload.bounds_min[0].n[axis];
        if(!valid_real_point3d(&part))return FALSE;
        matrix4x3_transform_point(held,&part,&world);
        matrix4x3_inverse_transform_point(socket,&world,&local);
        if(!valid_real_point3d(&world)||!valid_real_point3d(&local))return FALSE;
        for(int axis=0;axis<3;axis++) {
            if(local.n[axis]<held_min.n[axis])held_min.n[axis]=local.n[axis];
            if(local.n[axis]>held_max.n[axis])held_max.n[axis]=local.n[axis];
        }
    }
    for(int axis=0;axis<3;axis++) {
        real gap=0.0f;
        if(held_max.n[axis]<reload.bounds_min[0].n[axis])gap=reload.bounds_min[0].n[axis]-held_max.n[axis];
        else if(held_min.n[axis]>reload.bounds_max[0].n[axis])gap=held_min.n[axis]-reload.bounds_max[0].n[axis];
        distance2+=gap*gap;
    }
    return isfinite(distance2)&&distance2<=radius_local*radius_local;
}

static void reload_refresh_held_pose(void)
{
    /* Sample predicted tracking for visuals/contact, rather than leaving the
     * detached component at the 30 Hz gameplay tick pose. No state/ammo writes. */
    if(reload.have_attachment && (reload.state.phase==VR_MR_OLD_HELD || reload.state.phase==VR_MR_NEW_HELD)) {
        real_point3d hand;real_vector3d forward,up;real_matrix4x3 matrix;
        if(vr_hand_world(reload.hand,reload.camera.n,hand.n,forward.n,up.n)) {
            matrix4x3_from_point_and_vectors(&matrix,&hand,&forward,&up);
            if(reload_matrix_valid(&matrix))matrix4x3_multiply(&matrix,&reload.attachment,&reload.held);
        }
    }
}

int vr_manual_reload_trace(float const from[3],float const vector[3],float radius,struct collision_result *result)
{
    int hit=0;
    float best=1;
    if(!result || !reload.ready || !config_boolean("vr.manual_reload") || !vr_active() ||
        game_connection()!=_game_connection_local || vr_pose_time()<reload.sample_time ||
        vr_pose_time()-reload.sample_time>0.25)return 0;
    reload_refresh_held_pose();
    for(int part=0;part<2;part++) {
        if(!reload.bounds_valid[part] || (part && reload.kind==RELOAD_CRYSTALS) ||
            (!part && reload.state.phase==VR_MR_NEED_MAG))continue;
        if(!part && (reload.kind==RELOAD_SHELL || reload.kind==RELOAD_CRYSTALS) &&
            reload.state.phase!=VR_MR_NEW_HELD && reload.state.phase!=VR_MR_SEATING)continue;
        real_matrix4x3 transform=part?reload.charge:reload.socket;
        if(!part && (reload.state.phase==VR_MR_OLD_HELD || reload.state.phase==VR_MR_NEW_HELD || reload.state.phase==VR_MR_SEATING))transform=reload.held;
        if(part && reload.state.phase==VR_MR_CHAMBER_HELD)
            for(int charge_axis=0;charge_axis<3;charge_axis++)transform.position.n[charge_axis]-=reload.gun.forward.n[charge_axis]*reload.chamber_travel;
        if(!reload_matrix_valid(&transform))continue;
        real_point3d start,end,local_start,local_end;real_vector3d local_delta,local_normal,normal;
        for(int axis=0;axis<3;axis++){start.n[axis]=from[axis];end.n[axis]=from[axis]+vector[axis];}
        matrix4x3_inverse_transform_point(&transform,&start,&local_start);
        matrix4x3_inverse_transform_point(&transform,&end,&local_end);
        for(int delta_axis=0;delta_axis<3;delta_axis++)local_delta.n[delta_axis]=local_end.n[delta_axis]-local_start.n[delta_axis];
        float t;
        if(!vr_reload_box(local_start.n,local_delta.n,reload.bounds_min[part].n,reload.bounds_max[part].n,
            radius/transform.scale,&t,local_normal.n)||t>best)continue;
        matrix4x3_transform_vector(&transform,&local_normal,&normal);
        if(normalize3d(&normal)<=0.0001f)continue;
        memset(result,0,sizeof(*result));result->object_index=NONE;
        result->t=best=t;result->plane.n=normal;
        for(int point_axis=0;point_axis<3;point_axis++)result->point.n[point_axis]=from[point_axis]+t*vector[point_axis];
        result->plane.d=dot_product3d((real_vector3d const *)&result->point,&normal);
        hit=1;
    }
    return hit;
}

int vr_manual_reload_hand(int hand,float position[3])
{
    int part=reload.state.phase==VR_MR_CHAMBER_HELD;
    if(hand!=reload.hand || !reload.ready || !reload.bounds_valid[part] ||
        vr_interaction_owner(hand)!=VR_INTERACTION_RELOAD ||
        (!part && reload.state.phase!=VR_MR_OLD_HELD && reload.state.phase!=VR_MR_NEW_HELD))return 0;
    reload_refresh_held_pose();
    real_matrix4x3 transform=part?reload.charge:reload.held;
    if(part)for(int axis=0;axis<3;axis++)transform.position.n[axis]-=reload.gun.forward.n[axis]*reload.chamber_travel;
    if(!reload_matrix_valid(&transform))return 0;
    real_point3d point,local,contact;
    for(int input_axis=0;input_axis<3;input_axis++)point.n[input_axis]=position[input_axis];
    matrix4x3_inverse_transform_point(&transform,&point,&local);
    for(int clamp_axis=0;clamp_axis<3;clamp_axis++) {
        if(local.n[clamp_axis]<reload.bounds_min[part].n[clamp_axis])local.n[clamp_axis]=reload.bounds_min[part].n[clamp_axis];
        if(local.n[clamp_axis]>reload.bounds_max[part].n[clamp_axis])local.n[clamp_axis]=reload.bounds_max[part].n[clamp_axis];
    }
    matrix4x3_transform_point(&transform,&local,&contact);
    real t=(real)((vr_pose_time()-reload.grip_time)/0.08);
    t=t<0?0:t>1?1:t;t=t*t*(3-2*t);
    for(int output_axis=0;output_axis<3;output_axis++)position[output_axis]+=(contact.n[output_axis]-position[output_axis])*t;
    return 1;
}

void vr_manual_reload_model(long weapon_index, long model_index, real_matrix4x3 *matrices)
{
    struct model *model;
    char const *name;
    short magazine, chamber;
    long unit_index;
    struct reload_profile const *profile = NULL;
    if (!config_boolean("vr.manual_reload") || !vr_active() || game_connection() != _game_connection_local ||
        !reload_local_weapon(weapon_index, &unit_index) || !matrices) return;
    name = tag_get_name(model_index);
    if (!name) return;
    for (int index=0; index<NUMBEROF(profiles); ++index)
        if (!strcmp(name, profiles[index].path)) { profile = &profiles[index]; break; }
    if (!profile) return;
    model = model_definition_get(model_index);
    magazine = model_find_node(model_index, profile->ammo);
    chamber = model_find_node(model_index, profile->chamber);
    if (model->nodes.count <= 0 || model->nodes.count > MAXIMUM_NODES_PER_MODEL || magazine < 0 ||
        chamber < 0 || magazine >= model->nodes.count || chamber >= model->nodes.count) return;
    if (reload.weapon != weapon_index || reload.model != model_index || reload.hand != 1-vr_weapon_hand()) {
        vr_manual_reload_reset(); reload.weapon = weapon_index; reload.model = model_index;
        reload.hand = 1-vr_weapon_hand();
        /* Require an observed release after acquisition/reset. Focus loss
         * reports zero grip even if the controller is still squeezed. */
        reload.state.down = 1;
    }
    reload.magazine = magazine; reload.chamber = chamber; reload.kind = profile->kind;
    reload.component_nodes=0;
    for(short component=0;component<model->nodes.count;component++) {
        struct model_node *node=TAG_BLOCK_GET_ELEMENT(&model->nodes,component,struct model_node);
        if(profile->kind==RELOAD_CRYSTALS ?
            (!strncmp(node->name,"frame needle",12) || !strcmp(node->name,"frame eneedle13")) :
            reload_node_under(model,component,magazine))reload.component_nodes|=1ULL<<component;
    }
    reload.socket = matrices[magazine]; reload.charge = matrices[chamber]; reload.gun = matrices[0];
    /* Native idle animation can hide a loose shell. Its bind pose provides the
     * real insertion location, independent of that transient hiding scale. */
    if (profile->kind == RELOAD_SHELL || profile->kind == RELOAD_CRYSTALS) {
        real_matrix4x3 defaults[MAXIMUM_NODES_PER_MODEL], inverse, delta;
        real_point3d origin = {0,0,0};
        real_vector3d forward = {1,0,0}, up = {0,0,1};
        model_get_node_matrices(model, defaults, &origin, &forward, &up);
        matrix4x3_inverse(&defaults[0], &inverse);
        matrix4x3_multiply(&reload.gun, &inverse, &delta);
        matrix4x3_multiply(&delta, &defaults[magazine], &reload.socket);
        if(profile->kind==RELOAD_CRYSTALS && (reload.state.phase==VR_MR_NEW_HELD || reload.state.phase==VR_MR_SEATING))
            for(short crystal=0;crystal<model->nodes.count;crystal++)
                if(reload.component_nodes&(1ULL<<crystal))matrix4x3_multiply(&delta,&defaults[crystal],&matrices[crystal]);
    }
    if (!reload_matrix_valid(&reload.socket) || !reload_matrix_valid(&reload.gun) || !reload_matrix_valid(&reload.charge)) {
        vr_manual_reload_reset(); return;
    }
    reload.sample_time = vr_pose_time(); reload.ready = TRUE;
    reload_refresh_held_pose();
    if (reload.state.phase == VR_MR_SEATING) {
        real_matrix4x3 from;
        real_point3d position;
        real_vector3d forward, up, left;
        real t = (real)((vr_pose_time()-reload.insertion_time)/0.10);
        t = t < 0 ? 0 : t > 1 ? 1 : t;
        t = t*t*(3-2*t);
        matrix4x3_multiply(&reload.gun, &reload.insertion_local, &from);
        for (int axis=0; axis<3; ++axis) {
            position.n[axis] = from.position.n[axis]*(1-t)+reload.socket.position.n[axis]*t;
            forward.n[axis] = from.forward.n[axis]*(1-t)+reload.socket.forward.n[axis]*t;
            up.n[axis] = from.up.n[axis]*(1-t)+reload.socket.up.n[axis]*t;
        }
        normalize3d(&forward); cross_product3d(&up,&forward,&left); normalize3d(&left);
        cross_product3d(&forward,&left,&up);
        matrix4x3_from_point_and_vectors(&reload.held,&position,&forward,&up);
        reload.held.scale = from.scale*(1-t)+reload.socket.scale*t;
    }
    /* Capture the authored ejected magazine before NEED_MAG hides its subtree.
     * This clone is render-only and never participates in ammo accounting. */
    if (reload.debris_pending) debris_spawn_from_reload(model, matrices);
    if (reload.state.phase == VR_MR_OLD_HELD || reload.state.phase == VR_MR_NEW_HELD || reload.state.phase == VR_MR_SEATING) {
        real_matrix4x3 inverse, delta;
        matrix4x3_inverse(&reload.socket, &inverse);
        matrix4x3_multiply(&reload.held, &inverse, &delta);
        for (short n=0; n<model->nodes.count; ++n) if (reload.component_nodes&(1ULL<<n)) {
            real_matrix4x3 original = n == magazine ? reload.socket : matrices[n];
            matrix4x3_multiply(&delta, &original, &matrices[n]);
        }
    } else if (reload.state.phase == VR_MR_NEED_MAG) {
        for (short n=0; n<model->nodes.count; ++n)
            if (reload.component_nodes&(1ULL<<n)) matrices[n].scale = 0.0f;
    }
    if (reload.state.phase == VR_MR_CHAMBER_HELD) {
        for (short n=0; n<model->nodes.count; ++n) {
            if (reload_node_under(model,n,chamber))
                for (int axis=0; axis<3; ++axis)
                    matrices[n].position.n[axis] -= reload.gun.forward.n[axis]*reload.chamber_travel;
        }
    }
}
#endif
