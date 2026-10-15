/* Offline VR-only motion assists for the held weapon: shaking a hot weapon
 * cools it faster (vr.cooldown_shake), and with MANUAL RELOAD the needler is
 * reloaded by shaking it (Test70: the owner, "Needler does not need a fake
 * magazine-based interaction"). Weapon state and thresholds remain native:
 * cooling multiplies the authored heat loss, the needler's reload is the
 * native reload. Shakes are told apart by vr_shake_detect.h. */
#ifdef HALO_VR
#include "cseries.h"
#include "game/game.h"
#include "game/players.h"
#include "objects/objects.h"
#include "units/units.h"
#include "items/weapons.h"
#include "items/weapon_datum_flags.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_cooldown_shake.h"
#include "vr_cooldown_shake_math.h"
#include "vr_shake_detect.h"
#include <math.h>

void platform_log(char const *format, ...);
unsigned long system_milliseconds(void);

static struct {
    long weapon, unit;
    long tick;
    double now;
    struct vr_shake detect;
    int sampled;
    /* the needler's shake reload: when the last one was asked for */
    double reload_time;
} shake = { NONE, NONE, -1, 0.0 };

static void vr_held_shake_reset(void)
{
    shake.weapon = shake.unit = NONE;
    shake.sampled = 0;
    vr_shake_reset(&shake.detect);
}

/* The local player's held weapon `weapon_index`, sampled once a game tick
 * (weapon_update runs for every world weapon; another's update never touches
 * the local gun's sample). FALSE: not that weapon, or nothing to sample. */
static boolean vr_held_shake_sample(long weapon_index)
{
    short local, current_slot;
    long player, unit_index, current_weapon, tick;
    struct unit_datum *unit;
    struct player_datum *player_datum;
    float position[3], forward[3], up[3], relative[3], units;
    real_point3d camera;
    int axis;

    if (game_connection() != _game_connection_local || !vr_active() || !vr_aiming()) {
        vr_held_shake_reset(); return FALSE;
    }
    local = local_player_get_next(NONE);
    player = local != NONE ? local_player_get_player_index(local) : NONE;
    player_datum = player != NONE ? player_try_and_get(player) : NULL;
    unit_index = player_datum ? player_datum->unit_index : NONE;
    unit = unit_index != NONE ? unit_try_and_get(unit_index) : NULL;
    if (unit_index == NONE || !unit || unit->object.parent_object_index != NONE ||
        TEST_FLAG(unit->object.damage_flags, _object_dead_bit) || !((units = vr_units_per_metre()) > 0.0f) ||
        vr_hand_empty()) {
        vr_held_shake_reset(); return FALSE;
    }
    current_slot = unit->unit.current_weapon_index;
    current_weapon = current_slot >= 0 && current_slot < MAXIMUM_WEAPONS_PER_UNIT ?
        unit_inventory_get_weapon(unit_index, current_slot) : NONE;
    if (current_weapon == NONE) { vr_held_shake_reset(); return FALSE; }
    if (shake.unit != unit_index || shake.weapon != current_weapon) {
        vr_held_shake_reset();
        shake.unit = unit_index; shake.weapon = current_weapon;
    }
    if (weapon_index != current_weapon) return FALSE;
    tick = game_time_get();
    if (shake.sampled && tick == shake.tick) return TRUE;
    unit_get_camera_position(unit_index, &camera);
    if (!vr_hand_world(vr_weapon_hand(), camera.n, position, forward, up)) {
        vr_held_shake_reset(); return FALSE;
    }
    /* Relative to the head, in metres: walking or room-scale drift alone
     * never shakes the gun. */
    for (axis = 0; axis < 3; axis++) relative[axis] = (position[axis] - camera.n[axis]) / units;
    shake.now = (double)system_milliseconds() * 0.001;
    shake.tick = tick;
    shake.sampled = 1;
    if (vr_shake_sample(&shake.detect, relative, shake.now) &&
        config_boolean("vr.cooldown_shake")) {
        struct weapon_datum *weapon = weapon_try_and_get(weapon_index);
        /* a stroke felt while it helps: the gun is hot */
        if (weapon && weapon->weapon.heat > 0.0f)
            vr_haptic(vr_weapon_hand(), 0.25f, 0.025f);
    }
    return TRUE;
}

float vr_cooldown_shake_rate(long weapon_index)
{
    struct weapon_datum *weapon;
    float multiplier;

    if (!vr_held_shake_sample(weapon_index) || !config_boolean("vr.cooldown_shake")) return 1.0f;
    weapon = weapon_try_and_get(weapon_index);
    /* Test70: while the gun is hot at all, not only once overheated (test39's
     * rule left a hot plasma rifle cooling at its own pace) */
    if (!weapon || !(weapon->weapon.heat > 0.0f)) return 1.0f;
    multiplier = vr_shake_cooling_multiplier(&shake.detect, shake.now);
    return isfinite(multiplier) && multiplier >= 1.0f && multiplier <= 3.0f ? multiplier : 1.0f;
}

unsigned vr_needler_shake_update(long weapon_index, boolean reload_button)
{
    struct weapon_datum *weapon;
    unsigned result;

    if (!config_boolean("vr.manual_reload") || vr_gun_class() != VR_GUN_NEEDLER ||
        !vr_held_shake_sample(weapon_index)) return 0;
    weapon = weapon_try_and_get(weapon_index);
    if (!weapon || weapon->weapon.state != _weapon_state_idle) return VR_NEEDLER_SHAKE_SUPPRESS_AUTO;
    result = VR_NEEDLER_SHAKE_SUPPRESS_AUTO;
    if (reload_button) {
        result |= VR_NEEDLER_SHAKE_RELOAD;
    } else if (vr_shake_reload_ready(&shake.detect, shake.now) && shake.now - shake.reload_time > 1.5) {
        shake.reload_time = shake.now;
        vr_shake_spent(&shake.detect);
        vr_haptic(vr_weapon_hand(), 0.8f, 0.12f);
        platform_log("VR needler: shaken to reload weapon=%ld", weapon_index);
        result |= VR_NEEDLER_SHAKE_RELOAD;
    }
    return result;
}
#else
#include "cseries.h"
#include "vr_cooldown_shake.h"
float vr_cooldown_shake_rate(long weapon_index){return 1.0f;}
unsigned vr_needler_shake_update(long weapon_index, boolean reload_button){return 0;}
#endif
