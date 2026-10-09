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
#include "../src/port_config.h"
#include "../src/vr.h"
#include "vr_manual_reload.h"
#include "vr_manual_reload_math.h"
#include "vr_reload_contact_math.h"

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
    real_point3d camera;
    real chamber_travel;
    unsigned long long component_nodes;
    int bounds_tried, bounds_valid[2];
    real_point3d bounds_min[2], bounds_max[2];
} reload;
static int cancelled_phase;
static long cancelled_weapon;

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

static boolean reload_near(real_point3d const *a, real_point3d const *b, real radius)
{
    real x = a->x-b->x, y = a->y-b->y, z = a->z-b->z;
    return radius > 0 && x*x+y*y+z*z <= radius*radius;
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
    unsigned int buttons;float triggers[2],thumbs[4];
    boolean current = reload_local_weapon(weapon_index, &unit_index);
    /* Other world/NPC weapons must not cancel the local transaction. */
    if (!current) {
        if (reload.weapon == weapon_index) vr_manual_reload_reset();
        return 0;
    }
    if (!vr_active() || !vr_aiming() || !vr_controller(&buttons,triggers,thumbs) || !config_boolean("vr.manual_reload") ||
        game_connection() != _game_connection_local || !(units > 0) || vr_hand_empty() ||
        !reload.ready || reload.weapon != weapon_index || reload.hand != hand_index ||
        vr_pose_time()-reload.sample_time > 0.25 || vr_pose_time()<reload.sample_time) {
        vr_manual_reload_reset(); return 0;
    }
    weapon = weapon_get(weapon_index);
    if (!reload.bounds_tried) {
        reload.bounds_tried=1;
        reload.bounds_valid[0]=model_rigid_component_bounds(reload.model,reload.magazine,reload.component_nodes,&reload.bounds_min[0],&reload.bounds_max[0]);
        reload.bounds_valid[1]=model_rigid_node_bounds(reload.model,reload.chamber,&reload.bounds_min[1],&reload.bounds_max[1]);
        platform_log("VR manual reload: authored contact bounds weapon=%ld magazine=%d chamber=%d",weapon_index,reload.bounds_valid[0],reload.bounds_valid[1]);
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
    input.held = vr_interaction_grip(hand_index, NULL, NULL);
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
    input.near_mag = reload_near(&hand, &reload.socket.position, 0.09f*units);
    if (reload.state.phase == VR_MR_NEW_HELD) {
        real alignment = dot_product3d(&reload.held.forward, &reload.socket.forward);
        real up_alignment = dot_product3d(&reload.held.up, &reload.socket.up);
        input.near_mag = reload_near(&reload.held.position, &reload.socket.position, (reload.aligned ? 0.055f : 0.045f)*units) &&
            alignment > (reload.aligned ? 0.65f : 0.7f) && up_alignment > (reload.aligned ? 0.65f : 0.7f);
    }
    input.near_chamber = reload_near(&hand, &reload.charge.position, 0.075f*units);
    input.near_pouch = vr_mr_pouch_enabled(config_boolean("vr.reload_hip"),config_boolean("vr.reload_shoulder"),
        reload_near(&hand,&hip,0.19f*units),reload_near(&hand,&shoulder,0.16f*units));
    if (reload.state.phase == VR_MR_NEW_HELD) {
        if (input.near_mag && !reload.aligned) vr_haptic(hand_index, 0.20f, 0.025f);
        reload.aligned = input.near_mag;
    } else reload.aligned = FALSE;
    input.magazine_out = reload.have_attachment && !reload_near(&reload.held.position, &reload.socket.position, 0.06f*units);
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
    event = vr_mr_step(&reload.state, &input);
    if (event == VR_MR_INSERT) {
        matrix4x3_inverse(&reload.gun, &inverse);
        matrix4x3_multiply(&inverse, &reload.held, &reload.insertion_local);
        reload.insertion_time = vr_pose_time();
    }
    if (event == VR_MR_BEGIN || event == VR_MR_PICKUP || event == VR_MR_CHARGE) {
        if (!vr_interaction_claim(hand_index, VR_INTERACTION_RELOAD)) {
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
        platform_log("VR manual reload: weapon=%ld event=%d phase=%d rounds=%d reserve=%d", weapon_index,
            event, reload.state.phase, magazine->rounds_loaded, magazine->rounds_total);
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
