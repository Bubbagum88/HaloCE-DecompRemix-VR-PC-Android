/* Opt-in adjustable player clearance. Never edits tags, NPC colliders, world
 * collision flags or network movement contracts. */
#ifdef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "objects/objects.h"
#include "units/bipeds.h"
#include "units/biped_definitions.h"
#include "physics/collisions.h"
#include "physics/collision_features.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_close_contact.h"
#include "vr_close_contact_math.h"

static struct { long unit, tick; real radius; boolean active; } clearance;
void vr_close_contact_reset(void) { memset(&clearance, 0, sizeof(clearance)); }

static boolean clearance_can_expand(long unit, real radius)
{
    static struct collision_feature_list features;
    struct collision_plane hit;
    struct biped_datum *biped = biped_get(unit);
    struct biped_definition *definition = biped_definition_get(biped->definition_index);
    real_point3d base, center;
    real height = 0;
    real units = vr_units_per_metre();
    object_get_origin(unit, &base);
    if (!valid_real_point3d(&base) || !isfinite(biped->biped.crouch) ||
        biped->biped.crouch < 0 || biped->biped.crouch > 1 ||
        !isfinite(definition->biped.collision_height_standing) ||
        !isfinite(definition->biped.collision_height_crouching)) return FALSE;
    if (!TEST_FLAG(definition->biped.flags, _biped_pill_centered_at_origin_bit)) base.z += radius;
    if (!TEST_FLAG(definition->biped.flags, _biped_spherical_bit))
        height = MAX(0.0f, definition->biped.collision_height_standing +
            (definition->biped.collision_height_crouching-definition->biped.collision_height_standing)*biped->biped.crouch - 2*radius);
    center = base;
    center.z += height*.5f;
    collision_get_features_in_sphere(_collision_test_for_bipeds_living_flags,
        &center, height*.5f + radius, height, radius, unit, &features);
    /* Truncated feature sets cannot establish a safe expansion. */
    for (int type = 0; type < NUMBER_OF_COLLISION_FEATURE_TYPES; type++)
        if (features.count[type] >= MAXIMUM_COLLISION_FEATURES_PER_TEST) return FALSE;
    return !collision_features_test_point(&features, &base, &hit) ||
        (isfinite(hit.t) && hit.t <= 0.0001f*units);
}

float vr_grab_contact_radius(long unit, float baseline, float stock)
{
    char const *mode = config_string("vr.grab_contact");
    real units = vr_units_per_metre(), target, candidate;
    long tick = game_time_get();
    boolean enabled = vr_active() && (!strcmp(mode, "on") || (!strcmp(mode, "auto") && (config_boolean("vr.world_interaction") || config_boolean("vr.npc_interaction"))));
    if (game_connection() != _game_connection_local || !isfinite(units) || units <= 0)
        return baseline;
    target = vr_close_radius_target(stock, baseline, config_real("vr.grab_radius"), units, enabled);
    if (!clearance.active || clearance.unit != unit || tick < clearance.tick) {
        clearance.active = TRUE; clearance.unit = unit; clearance.radius = MIN(target, baseline);
        clearance.tick = tick;
    }
    if (clearance.tick != tick) {
        candidate = vr_close_radius_step(clearance.radius, target, units);
        if (candidate <= clearance.radius || clearance_can_expand(unit, candidate)) clearance.radius = candidate;
        clearance.tick = tick;
    }
    return clearance.radius;
}
#endif
