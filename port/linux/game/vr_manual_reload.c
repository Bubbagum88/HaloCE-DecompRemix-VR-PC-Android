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
    int hand_sample_valid, debris_pending, pouch_zone;
    /* Test59: the pulled magazine has been clear of the well (4 cm), so
     * coming back to it seats it again */
    int pulled_clear;
    double grip_press_time;
    struct vr_magazine_debris_transaction debris_transaction;
    real_point3d bounds_min[2], bounds_max[2];
} reload;
struct dropped_magazine {
    int active, provisional, node_count;
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
static boolean reload_button_down;
static boolean reload_local_weapon(long weapon_index, long *unit_out);
static boolean reload_matrix_valid(real_matrix4x3 const *matrix);
static boolean reload_component_bounds_touch(real_matrix4x3 const *socket,
	real_matrix4x3 const *held, real radius);
static long bounds_logged_weapon = NONE, bounds_logged_model = NONE;
static boolean bounds_log_initialized;
static long gate_logged_weapon = NONE, profile_logged_model = NONE;
static double gate_logged_time = -1000.0;
static char gate_logged_reason[48];
static long input_logged_weapon = NONE;
static int input_logged_state = -1;

/* Reload crosses the frame, input and weapon simulation paths. Report a
 * blocked state transition without writing the same reason every tick. */
static void reload_log_gate(long weapon_index, char const *reason)
{
	double now = vr_pose_time();
	if (!reason) return;
	if (gate_logged_weapon != weapon_index || strcmp(gate_logged_reason, reason) ||
		!isfinite(now) || now - gate_logged_time >= 3.0)
	{
		platform_log("VR manual reload gate: weapon=%08lx reason=%s", (unsigned long)weapon_index, reason);
		gate_logged_weapon = weapon_index;
		snprintf(gate_logged_reason, sizeof(gate_logged_reason), "%s", reason);
		gate_logged_time = isfinite(now) ? now : 0.0;
	}
}

/* Test62: free-hand transforms use vr_hand_pose, the same adjusted rotation
 * as the visible hand. Raw vr_hand_world ignored HAND ANGLE adjustments,
 * leaving a replacement magazine rotated away from the fingers. */
/* A replacement magazine starts at the free palm, not at the old weapon
 * socket. Capturing this hand-relative transform is required for both the
 * normal pull-out path and the contextual button-eject path. */
static boolean reload_attach_to_hand(real_matrix4x3 const *hand_matrix,
	real_matrix4x3 const *world_item)
{
	real_matrix4x3 inverse;
	if (!hand_matrix || !world_item || !reload_matrix_valid(hand_matrix) ||
		!reload_matrix_valid(world_item))
		return FALSE;
	matrix4x3_inverse(hand_matrix, &inverse);
	matrix4x3_multiply(&inverse, world_item, &reload.attachment);
	if (!reload_matrix_valid(&reload.attachment))
		return FALSE;
	reload.held = *world_item;
	reload.have_attachment = TRUE;
	return TRUE;
}

/* A dropped mag is provisional until the native ammunition transaction
 * commits. Cancellation restores the still-loaded authored mag, so retaining
 * its ejected clone would show two magazines for one weapon. */
static void debris_cancel_transaction(void)
{
	int slot_index = vr_magazine_debris_transaction_cancel(&reload.debris_transaction);
	if (slot_index >= 0 && slot_index < VR_MAGAZINE_DEBRIS_CAPACITY) {
		struct dropped_magazine *slot = &dropped_magazines[slot_index];
		if (slot->active && slot->provisional) {
			platform_log("VR reload debris: cancelled provisional magazine slot=%d", slot_index);
			memset(slot, 0, sizeof(*slot));
		}
	}
	reload.debris_pending = FALSE;
}

static void debris_commit_transaction(void)
{
	int slot_index = vr_magazine_debris_transaction_commit(&reload.debris_transaction);
	if (slot_index >= 0 && slot_index < VR_MAGAZINE_DEBRIS_CAPACITY) {
		struct dropped_magazine *slot = &dropped_magazines[slot_index];
		if (slot->active && slot->provisional) {
			slot->provisional = FALSE;
			platform_log("VR reload debris: committed magazine slot=%d", slot_index);
		}
	}
}

void vr_manual_reload_reset(void)
{
    if (reload.state.phase != VR_MR_IDLE) {
        cancelled_phase=reload.state.phase; cancelled_weapon=reload.weapon;
    }
    debris_cancel_transaction();
    vr_interaction_release(0, VR_INTERACTION_RELOAD);
    vr_interaction_release(1, VR_INTERACTION_RELOAD);
    memset(&reload, 0, sizeof(reload));
    vr_magazine_debris_transaction_init(&reload.debris_transaction);
    reload.weapon = reload.model = NONE;
    reload.magazine = reload.chamber = NONE;
    /* After a tracking/session reset, require a release before a new
     * contextual eject can fire. This prevents a held button from ejecting
     * a magazine when tracking returns. */
    reload_button_down = TRUE;
    input_logged_weapon = NONE;
    input_logged_state = -1;
}

void vr_manual_reload_debris_reset(void)
{
	if (dropped_magazines_have_state)
        memset(dropped_magazines, 0, sizeof(dropped_magazines));
	dropped_magazines_have_state = FALSE;
    dropped_magazines_full_reported = FALSE;
	vr_magazine_debris_transaction_init(&reload.debris_transaction);
	reload.debris_pending = FALSE;
}

void vr_manual_reload_debris_prepare_for_state_restore(void)
{
	int retained = 0;
	int detached_owners = 0;
	/* Physical reload state is transient. Cancel its uncommitted floor visual,
	 * but retain already-committed map-session drops through the restore. */
	vr_manual_reload_reset();
	for (int index = 0; index < VR_MAGAZINE_DEBRIS_CAPACITY; ++index) {
		struct dropped_magazine *slot = &dropped_magazines[index];
		if (!slot->active) continue;
		retained++;
		if (slot->owner_unit != NONE) {
			slot->owner_unit = vr_magazine_debris_owner_after_state_restore(
				TRUE, slot->owner_unit, NONE);
			detached_owners++;
		}
	}
	if (retained > 0) {
		platform_log("VR reload debris: retaining %d map-local visual magazines across same-map state restore; detached %d old collision-owner handles",
			retained, detached_owners);
	}
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
    if (!config_boolean("vr.dropped_magazines") || !config_boolean("vr.manual_reload") ||
        game_connection() != _game_connection_local ||
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
    slot->provisional = vr_magazine_debris_transaction_is_provisional(&reload.debris_transaction);
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
	if (slot->provisional && !vr_magazine_debris_transaction_record(&reload.debris_transaction, slot_index)) {
		memset(slot, 0, sizeof(*slot));
		platform_log("VR reload debris: provisional transaction rejected slot=%d", slot_index);
		return;
	}
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

/* Test59: this transaction's dropped magazine (provisional: the gun still
 * has its rounds) where it lies, or -1 */
static int reload_dropped_slot(void)
{
    int slot_index = reload.debris_transaction.slot;
    struct dropped_magazine const *slot;
    if (!reload.debris_transaction.slot_valid || slot_index < 0 || slot_index >= VR_MAGAZINE_DEBRIS_CAPACITY)
        return -1;
    slot = &dropped_magazines[slot_index];
    if (!slot->active || !slot->provisional || slot->model != reload.model ||
        reload.magazine < 0 || reload.magazine >= slot->node_count ||
        !reload_matrix_valid(&slot->matrices[reload.magazine]) || !valid_real_point3d(&slot->center))
        return -1;
    return slot_index;
}

static boolean reload_hand_touches_part(int part, real_matrix4x3 const *transform, real_point3d const *hand,
    real extra_metres)
{
    real_point3d local;
    real radius, units=vr_units_per_metre();
    if(part<0 || part>1 || !reload.bounds_valid[part] || !transform || !hand ||
        !reload_matrix_valid(transform) || !(units>0.0f))return FALSE;
    double configured_contact=config_real("vr.interaction_reach");
    radius=((real)(isfinite(configured_contact)?PIN(configured_contact,0.02,0.08):0.04)+extra_metres)*units;
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

/* Test54: each physical step has its own feel (VR HAPTICS scales them all):
 * the free hand feels grabbing, pulling free, the pouch, the well and the
 * slide; the gun hand feels the magazine leave, lock and the gun come ready. */
/* Test62: OpenXR replaces an active vibration when another is requested.
 * Keep render contact buzz from overwriting the insert/charge click before
 * it is felt. This window is only the event duration, per hand; it never
 * sends or repeats feedback by itself and master HAPTICS still owns output. */
static double reload_feedback_start[2],reload_feedback_until[2];
static void reload_pulse(int hand,float amplitude,float seconds)
{
    double now=vr_pose_time();
    if(hand<0 || hand>1 || !isfinite(now) || !(seconds>0.0f && seconds<=.1f)) return;
    reload_feedback_start[hand]=now;
    reload_feedback_until[hand]=now+seconds;
    vr_haptic(hand,amplitude,seconds);
}
int vr_manual_reload_feedback_active(int hand)
{
    double now=vr_pose_time();
    return hand>=0 && hand<2 && isfinite(now) && now>=reload_feedback_start[hand] &&
        now<reload_feedback_until[hand];
}
static void reload_event_haptic(int event, int free_hand)
{
    int gun_hand = vr_weapon_hand();
    switch (event) {
    case VR_MR_BEGIN: reload_pulse(free_hand, 0.30f, 0.035f); break;
    case VR_MR_PULLED: reload_pulse(free_hand, 0.45f, 0.040f); reload_pulse(gun_hand, 0.25f, 0.030f); break;
    case VR_MR_EJECT: reload_pulse(gun_hand, 0.50f, 0.050f); break;
    case VR_MR_DISCARD: reload_pulse(free_hand, 0.15f, 0.020f); break;
    case VR_MR_PICKUP: reload_pulse(free_hand, 0.40f, 0.040f); break;
    case VR_MR_INSERT: reload_pulse(free_hand, 0.55f, 0.045f); reload_pulse(gun_hand, 0.40f, 0.040f); break;
    case VR_MR_SEATED: reload_pulse(free_hand, 0.35f, 0.030f); reload_pulse(gun_hand, 0.70f, 0.050f); break;
    case VR_MR_CHARGE: reload_pulse(free_hand, 0.30f, 0.030f); break;
    case VR_MR_RACKED: reload_pulse(free_hand, 0.60f, 0.045f); reload_pulse(gun_hand, 0.35f, 0.035f); break;
    case VR_MR_COMMIT: reload_pulse(free_hand, 0.50f, 0.040f); reload_pulse(gun_hand, 0.80f, 0.060f); break;
    case VR_MR_CANCEL: reload_pulse(free_hand, 0.10f, 0.020f); break;
    /* Test59: the gun's own magazine taken back up, and locked back in */
    case VR_MR_RECOVER: reload_pulse(free_hand, 0.40f, 0.040f); break;
    case VR_MR_RESEAT: reload_pulse(free_hand, 0.45f, 0.040f); reload_pulse(gun_hand, 0.75f, 0.055f); break;
    default: break;
    }
}

unsigned vr_manual_reload_update(long weapon_index, int explicit_reload)
{
    long unit_index = NONE;
    real units = vr_units_per_metre();
    real_point3d camera, hand, weapon_hand;
    real_vector3d forward, up, gun_forward, gun_up;
    real_matrix4x3 hand_matrix, inverse;
    struct weapon_datum *weapon;
    struct weapon_definition *definition;
    struct weapon_magazine *magazine;
    struct weapon_magazine_definition *magazine_definition;
    struct vr_mr_input input = {0};
    int event, hand_index = 1-vr_weapon_hand();
    int reload_owner = VR_INTERACTION_NONE;
    boolean reload_pressed = FALSE, grip_pressed = FALSE;
    boolean trigger_input = FALSE, mapped_action_down = FALSE;
    unsigned int buttons;float triggers[2],thumbs[4];
    boolean current = reload_local_weapon(weapon_index, &unit_index);
    char const *gate = NULL;
    boolean suppress_native = vr_mr_suppress_native_reload(
        config_boolean("vr.manual_reload"), game_connection() == _game_connection_local,
        reload.ready && reload.weapon == weapon_index && reload.model != NONE);
    /* Other world/NPC weapons must not cancel the local transaction. */
    if (!current) {
        if (reload.weapon == weapon_index) vr_manual_reload_reset();
        return 0;
    }
    {
        mapped_action_down = vr_manual_reload_action_down();
		int reload_button_held = vr_mr_reload_button_down(mapped_action_down, explicit_reload);
		reload_pressed = vr_mr_button_pressed(reload_button_down, reload_button_held);
		reload_button_down = reload_button_held ? TRUE : FALSE;
	}
    if (!vr_active()) gate = "vr-inactive";
    else if (!vr_controller(&buttons,triggers,thumbs)) gate = "controller-unavailable";
    else if (!config_boolean("vr.manual_reload")) gate = "manual-reload-disabled";
    else if (game_connection() != _game_connection_local) gate = "network-session";
    else if (!(units > 0)) gate = "invalid-unit-scale";
    else if (vr_hand_empty()) gate = "weapon-hand-empty";
    else if (!reload.ready) gate = "first-person-profile-not-ready";
    else if (reload.weapon != weapon_index || reload.hand != hand_index) gate = "weapon-or-free-hand-mismatch";
    else if (vr_pose_time()-reload.sample_time > 0.25 || vr_pose_time()<reload.sample_time) gate = "stale-first-person-pose";
    if (gate) {
        reload_log_gate(weapon_index, gate);
        vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
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
    if (weapon->weapon.state == _weapon_state_primary_recoil && !reload_pressed &&
        reload.state.phase == VR_MR_IDLE) return VR_MANUAL_SUPPRESS_AUTO;
    if (definition->weapon.magazines.count != 1) {
        reload_log_gate(weapon_index, "unsupported-magazine-count");
        vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
    }
    if (weapon->weapon.state != _weapon_state_idle ||
        TEST_FLAG(weapon->weapon.control_flags, _weapon_control_user_busy_bit) ||
        TEST_FLAG(weapon->weapon.control_flags, _weapon_control_user_switching_weapons_bit)) {
        reload_log_gate(weapon_index, "weapon-busy-or-switching");
        vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
    }
    magazine = &weapon->weapon.magazines[0];
    magazine_definition = TAG_BLOCK_GET_ELEMENT(&definition->weapon.magazines, 0, struct weapon_magazine_definition);
    if (magazine->state != _magazine_idle || magazine_definition->rounds_reloaded <= 0 ||
        magazine_definition->rounds_recharged_per_second != 0) {
        reload_log_gate(weapon_index, "magazine-busy-or-unsupported-policy");
        vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
    }
    /* Test59: the hands from the camera the gun was drawn from, as the
     * magazine well (reload.socket) was taken from the drawn gun: from the
     * game tick's camera the held magazine and the hand on it stepped
     * against the gun by up to a tick of the player's walk */
    if (!vr_render_drawn_camera(camera.n)) unit_get_camera_position(unit_index, &camera);
    reload.camera=camera;
    if (!vr_hand_world(vr_weapon_hand(), camera.n, weapon_hand.n, gun_forward.n, gun_up.n) ||
        !vr_hand_pose(hand_index, camera.n, hand.n, forward.n, up.n)) {
        vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
    }
    matrix4x3_from_point_and_vectors(&hand_matrix, &hand, &forward, &up);
    if (reload.have_attachment) matrix4x3_multiply(&hand_matrix, &reload.attachment, &reload.held);
    /* The selected input applies only to the free-hand manual-reload state
     * machine. Other grab systems and game firing continue to use their usual
     * grip/weapon-trigger paths. */
    input.held = trigger_input ? vr_interaction_trigger(hand_index) :
        vr_interaction_grip(hand_index, NULL, NULL);
    reload_owner = vr_interaction_owner(hand_index);
    input.valid = reload_owner == VR_INTERACTION_NONE ||
        reload_owner == VR_INTERACTION_RELOAD;
    input.explicit_reload = reload_pressed;
    /* Test54: with manual reload on, Reload is the magazine release: it drops
     * the magazine wherever the free hand is and never reloads by itself. */
    input.eject_pressed = reload_pressed;
    /* A round left in the chamber (a tactical reload) needs no charging. */
    input.chambered = magazine->rounds_loaded > 0;
    input.loose_round = reload.kind == RELOAD_SHELL || reload.kind == RELOAD_CRYSTALS;
    input.no_chamber = reload.kind == RELOAD_CRYSTALS;
    input.seated = vr_pose_time()-reload.insertion_time >= 0.10;
    /* A full magazine can still be tactically replaced when reserve remains.
     * The native finish_reload path retains or discards its rounds according
     * to the authored magazine policy and performs the only ammo mutation. */
    input.can_load = magazine->rounds_total > 0;
    if (reload.state.phase == VR_MR_IDLE &&
        (TEST_FLAG(weapon->weapon.control_flags, _weapon_control_primary_trigger_bit) ||
         TEST_FLAG(weapon->weapon.control_flags, _weapon_control_secondary_trigger_bit))) input.can_load = FALSE;
    /* Pickup begins only when the free hand's contact sphere overlaps the
     * authored magazine bounds. A center-to-socket reach radius is not touch. */
    input.near_mag = reload_hand_touches_part(0,&reload.socket,&hand,0.015f); /* Test55: 1.5 cm more forgiving */
    if (reload.state.phase == VR_MR_NEW_HELD) {
        real alignment = dot_product3d(&reload.held.forward, &reload.socket.forward);
        real up_alignment = dot_product3d(&reload.held.up, &reload.socket.up);
        /* Test54: a hand-held magazine finds the well within 1.5 cm and
         * 50 degrees, then locks itself home (SEATING blends the rest). */
        /* Test55: forgiving but deliberate: within 3 cm of the well and about
         * 63 degrees (66 once aligned) of its direction, then it locks home */
        input.near_mag = reload_component_bounds_touch(&reload.socket,&reload.held,0.03f*units) &&
            alignment > (reload.aligned ? 0.40f : 0.45f) && up_alignment > (reload.aligned ? 0.40f : 0.45f);
    }
    /* Test55: the slide / charging handle locks on from 4 cm further away
     * once it is the next step (or while held) */
    {
        /* Test56: CHARGE GRAB (vr.charge_grab_radius, 4 cm as Test55's lock-on) */
        double charge_reach = config_real("vr.charge_grab_radius");
        input.near_chamber = reload_hand_touches_part(1,&reload.charge,&hand,
            reload.state.phase == VR_MR_NEED_CHAMBER || reload.state.phase == VR_MR_CHAMBER_HELD ?
            (real)(isfinite(charge_reach) ? PIN(charge_reach, 0.02, 0.10) : 0.04) : 0.0f);
    }
    {
        /* Test54: the pouches are body volumes in the head-heading frame
         * (vr_reload_pouch_zone), on the free hand's side by default. With
         * both turned off the hip stays, so a dropped magazine is never a
         * dead end. */
        int hip_enabled = config_boolean("vr.reload_hip") || !config_boolean("vr.reload_shoulder");
        int zone = vr_reload_pouch_zone(hand_index, hip_enabled, config_boolean("vr.reload_shoulder"));
        input.near_pouch = vr_mr_pouch_enabled(hip_enabled, config_boolean("vr.reload_shoulder"),
            zone == 1, zone == 2);
        if (zone && zone != reload.pouch_zone &&
            (reload.state.phase == VR_MR_NEED_MAG || (reload.state.phase == VR_MR_IDLE && input.loose_round)))
            vr_haptic(hand_index, 0.18f, 0.02f);
        reload.pouch_zone = zone;
    }
    grip_pressed = input.held && !reload.state.down;
    if (grip_pressed) reload.grip_press_time = vr_pose_time();
    input.grace_press = reload.state.phase == VR_MR_NEED_CHAMBER && input.held && !grip_pressed &&
        vr_pose_time() - reload.grip_press_time <= 0.35 && vr_pose_time() >= reload.grip_press_time;
    {
		int diagnostic_state = (input.held ? 1 : 0) | (input.near_mag ? 2 : 0) |
			(input.near_pouch ? 4 : 0) | (input.near_chamber ? 8 : 0) |
			(input.valid ? 16 : 0) | (reload_pressed ? 32 : 0) |
			(mapped_action_down ? 64 : 0) | (explicit_reload ? 128 : 0) |
			((reload_owner & 7) << 8);
		if (input_logged_weapon != weapon_index || input_logged_state != diagnostic_state) {
			platform_log("VR manual reload input: weapon=%ld phase=%d grip=%d input=%s action_down=%d native_reload=%d grip_edge=%d contact_mag=%d contact_pouch=%d contact_chamber=%d owner=%d valid=%d",
				weapon_index, reload.state.phase, input.held, trigger_input ? "trigger" : "grip",
				mapped_action_down, explicit_reload, grip_pressed, input.near_mag,
				input.near_pouch, input.near_chamber, reload_owner, input.valid);
			input_logged_weapon = weapon_index;
			input_logged_state = diagnostic_state;
		}
	}
    if (reload_pressed || grip_pressed) {
        platform_log("VR manual reload attempt: weapon=%ld phase=%d action=%s input=%s grip_edge=%d contact_mag=%d contact_pouch=%d contact_chamber=%d bounds_mag=%d bounds_chamber=%d rounds=%d reserve=%d capacity=%d can_load=%d owner=%d hand=(%.3f,%.3f,%.3f) magazine=(%.3f,%.3f,%.3f)",
            weapon_index, reload.state.phase, reload_pressed ? "reload-button" : "grip",
            trigger_input ? "trigger" : "grip", grip_pressed,
            input.near_mag, input.near_pouch, input.near_chamber,
            reload.bounds_valid[0], reload.bounds_valid[1],
            magazine->rounds_loaded, magazine->rounds_total,
            magazine_definition->rounds_loaded_maximum, input.can_load,
            vr_interaction_owner(hand_index), hand.x, hand.y, hand.z,
            reload.socket.position.x, reload.socket.position.y, reload.socket.position.z);
    }
    if (reload.state.phase == VR_MR_NEW_HELD) {
        if (input.near_mag && !reload.aligned) vr_haptic(hand_index, 0.20f, 0.025f);
        reload.aligned = input.near_mag;
    } else reload.aligned = FALSE;
    input.magazine_out = reload.have_attachment && !reload_component_bounds_touch(&reload.socket,&reload.held,0.005f*units);
    /* Test59: the gun's own magazine goes back in. Pulled out and brought
     * back (once 4 cm clear) to within 3 cm of the well, lined up as a
     * replacement must be, it seats again, gripped or let go; let go at the
     * well it seats even if it never came clear. Dropped, the free hand
     * takes it back up where it lies (DROPPED MAGS draws it). */
    if (reload.state.phase == VR_MR_OLD_HELD && reload.have_attachment) {
        real alignment = dot_product3d(&reload.held.forward, &reload.socket.forward);
        real up_alignment = dot_product3d(&reload.held.up, &reload.socket.up);
        if (!reload_component_bounds_touch(&reload.socket,&reload.held,0.04f*units)) reload.pulled_clear = TRUE;
        input.returned = reload.state.pulled && alignment > 0.45f && up_alignment > 0.45f &&
            reload_component_bounds_touch(&reload.socket,&reload.held,0.03f*units) &&
            (reload.pulled_clear || !input.held);
    } else reload.pulled_clear = FALSE;
    if (reload.state.phase == VR_MR_NEED_MAG) {
        int slot_index = reload_dropped_slot();
        if (slot_index >= 0) {
            double configured_contact = config_real("vr.interaction_reach");
            real reach = dropped_magazines[slot_index].radius +
                ((real)(isfinite(configured_contact) ? PIN(configured_contact, 0.02, 0.08) : 0.04) + 0.02f) * units;
            input.near_dropped = distance_squared3d(&hand, &dropped_magazines[slot_index].center) <= reach * reach;
        }
    }
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
        int previous_phase = reload.state.phase, previous_own = reload.state.own;
        event = vr_mr_step(&reload.state, &input);
        if (event == VR_MR_DISCARD && previous_phase == VR_MR_OLD_HELD)
            reload.debris_pending = TRUE;
        /* Test59: the gun's own magazine, taken back up, dropped again */
        else if (event == VR_MR_DISCARD && previous_phase == VR_MR_NEW_HELD && previous_own) {
            reload.debris_pending = TRUE;
            vr_magazine_debris_transaction_new_reload(&reload.debris_transaction);
        }
        else if (event == VR_MR_RESEAT)
            debris_cancel_transaction();
        else if (event == VR_MR_EJECT) {
            reload.debris_pending = TRUE;
            reload.held = reload.socket;
            vr_magazine_debris_transaction_new_reload(&reload.debris_transaction);
        }
        else if (event == VR_MR_CANCEL)
            debris_cancel_transaction();
        else if (event == VR_MR_COMMIT)
            debris_commit_transaction();
        if (event == VR_MR_BEGIN)
            vr_magazine_debris_transaction_new_reload(&reload.debris_transaction);
    }
    if (event == VR_MR_INSERT) {
        matrix4x3_inverse(&reload.gun, &inverse);
        matrix4x3_multiply(&inverse, &reload.held, &reload.insertion_local);
        reload.insertion_time = vr_pose_time();
    }
    if (event == VR_MR_BEGIN || event == VR_MR_PICKUP || event == VR_MR_CHARGE || event == VR_MR_RECOVER) {
        if (!vr_interaction_claim_input(hand_index, VR_INTERACTION_RELOAD, input.held)) {
            platform_log("VR manual reload: grip ownership refused weapon=%ld hand=%d event=%d owner=%d; transaction cancelled without ammo change",
				weapon_index, hand_index, event, vr_interaction_owner(hand_index));
            vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
        }
        reload.grip_time=vr_pose_time();
        if (event == VR_MR_BEGIN) {
            matrix4x3_inverse(&hand_matrix, &inverse);
            matrix4x3_multiply(&inverse, &reload.socket, &reload.attachment);
            reload.have_attachment = TRUE;
        }
        if (event == VR_MR_PICKUP) {
            /* A replacement is taken from the configured body-side pouch. It
             * starts at the palm using the authored part orientation, then
             * follows the hand through a captured relative transform. This
             * must also replace an old magazine's prior hand offset after
             * direct pull-out. */
            real_matrix4x3 attached = reload.socket, gun_matrix;
            attached.position = hand;
            /* Test55: held as it sits in the gun: the magazine keeps the same
             * relation to the free hand that it has to the gun hand, with its
             * body centred in the palm (the fingers close around it:
             * vr_render.c), instead of the socket's world angle at the palm. */
            matrix4x3_from_point_and_vectors(&gun_matrix, &weapon_hand, &gun_forward, &gun_up);
            if (reload_matrix_valid(&gun_matrix)) {
                real_matrix4x3 gun_inverse, relative, grip;
                matrix4x3_inverse(&gun_matrix, &gun_inverse);
                matrix4x3_multiply(&gun_inverse, &reload.socket, &relative);
                matrix4x3_multiply(&hand_matrix, &relative, &grip);
                if (reload_matrix_valid(&grip)) {
                    if (reload.bounds_valid[0]) {
                        real_point3d middle, world_middle;
                        for (int axis = 0; axis < 3; ++axis)
                            middle.n[axis] = (reload.bounds_min[0].n[axis] + reload.bounds_max[0].n[axis]) * 0.5f;
                        matrix4x3_transform_point(&grip, &middle, &world_middle);
                        if (valid_real_point3d(&world_middle))
                            for (int part_axis = 0; part_axis < 3; ++part_axis)
                                grip.position.n[part_axis] += hand.n[part_axis] - world_middle.n[part_axis];
                    }
                    attached = grip;
                }
            }
            if (!reload_attach_to_hand(&hand_matrix, &attached)) {
                reload_log_gate(weapon_index, "replacement-attachment-invalid");
                vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
            }
        }
        if (event == VR_MR_RECOVER) {
            /* Test59: the dropped magazine, as it lies, into the hand; the
             * floor copy goes (it is the one in the hand now) */
            int slot_index = reload_dropped_slot();
            real_matrix4x3 lying;
            if (slot_index < 0) {
                reload_log_gate(weapon_index, "dropped-magazine-gone");
                vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
            }
            lying = dropped_magazines[slot_index].matrices[reload.magazine];
            if (!reload_attach_to_hand(&hand_matrix, &lying)) {
                reload_log_gate(weapon_index, "dropped-magazine-attachment-invalid");
                vr_manual_reload_reset(); return suppress_native ? VR_MANUAL_SUPPRESS_AUTO : 0;
            }
            memset(&dropped_magazines[slot_index], 0, sizeof(dropped_magazines[slot_index]));
            vr_magazine_debris_transaction_init(&reload.debris_transaction);
            reload.debris_pending = FALSE;
            platform_log("VR reload debris: magazine slot=%d taken back up", slot_index);
        }
        if (event == VR_MR_CHARGE) {
            matrix4x3_inverse_transform_point(&reload.gun, &hand, &reload.charge_start);
            reload.chamber_travel = 0;
        }
    }
    if (reload.have_attachment) matrix4x3_multiply(&hand_matrix, &reload.attachment, &reload.held);
    if (event != VR_MR_NONE) {
        platform_log("VR manual reload: input=%s weapon=%ld event=%d phase=%d rounds=%d reserve=%d chambered=%d",
            trigger_input ? "trigger" : "grip", weapon_index, event, reload.state.phase,
            magazine->rounds_loaded, magazine->rounds_total, reload.state.chambered);
        reload_event_haptic(event, hand_index);
        if (event == VR_MR_RESEAT)
            platform_log("VR manual reload: the gun's own magazine went back in weapon=%ld rounds=%d; ammo unchanged",
                weapon_index, magazine->rounds_loaded);
    }
    if (reload_pressed && event == VR_MR_NONE && reload.state.phase == VR_MR_IDLE && !input.can_load)
        vr_haptic(vr_weapon_hand(), 0.12f, 0.02f); /* no reserve: the release clicks, nothing drops */
    if (!input.held || event == VR_MR_CANCEL || event == VR_MR_COMMIT || event == VR_MR_RESEAT)
        vr_interaction_release(hand_index, VR_INTERACTION_RELOAD);
    /* The edge is consumed by vr_mr_step() to eject/cancel. Do not return on
     * the raw held button here: the active transaction must keep blocking fire. */
    return vr_mr_output_flags(suppress_native, input.valid, reload.state.phase, event,
        VR_MANUAL_SUPPRESS_AUTO, VR_MANUAL_BLOCK_FIRE, VR_MANUAL_COMMIT);
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
    int corner,axis;
    if(!reload.bounds_valid[0] || !socket || !held || !reload_matrix_valid(socket) ||
        !reload_matrix_valid(held) || !isfinite(radius) || radius<0.0f)return FALSE;
    radius_local=radius/socket->scale;
    if(!isfinite(radius_local))return FALSE;
    /* Transform the held magazine's authored bounds into socket space. A
     * successful seat needs actual component-bound contact, not origin range. */
    for(corner=0;corner<8;corner++) {
        real_point3d part,world,local;
        for(axis=0;axis<3;axis++)
            part.n[axis]=(corner&(1<<axis))?reload.bounds_max[0].n[axis]:reload.bounds_min[0].n[axis];
        if(!valid_real_point3d(&part))return FALSE;
        matrix4x3_transform_point(held,&part,&world);
        matrix4x3_inverse_transform_point(socket,&world,&local);
        if(!valid_real_point3d(&world)||!valid_real_point3d(&local))return FALSE;
        for(axis=0;axis<3;axis++) {
            if(local.n[axis]<held_min.n[axis])held_min.n[axis]=local.n[axis];
            if(local.n[axis]>held_max.n[axis])held_max.n[axis]=local.n[axis];
        }
    }
    for(axis=0;axis<3;axis++) {
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
        if(vr_hand_pose(reload.hand,reload.camera.n,hand.n,forward.n,up.n)) {
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
    if (!name) {
        reload_log_gate(weapon_index, "first-person-model-name-missing");
        return;
    }
    for (int index=0; index<NUMBEROF(profiles); ++index)
        if (!strcmp(name, profiles[index].path)) { profile = &profiles[index]; break; }
    if (!profile) {
        if (profile_logged_model != model_index) {
            platform_log("VR manual reload profile unavailable: weapon=%ld model=%ld tag=%s",
                weapon_index, model_index, name);
            profile_logged_model = model_index;
        }
        return;
    }
    model = model_definition_get(model_index);
    magazine = model_find_node(model_index, profile->ammo);
    chamber = model_find_node(model_index, profile->chamber);
    if (model->nodes.count <= 0 || model->nodes.count > MAXIMUM_NODES_PER_MODEL || magazine < 0 ||
        chamber < 0 || magazine >= model->nodes.count || chamber >= model->nodes.count) {
        reload_log_gate(weapon_index, "authored-reload-node-missing");
        return;
    }
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
    {
        /* Test59: the held magazine from this frame's camera, with the gun */
        real_point3d drawn;
        if (vr_render_drawn_camera(drawn.n)) reload.camera = drawn;
    }
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
