#include "cseries.h"
#include "game/game.h"
#include "objects/objects.h"
#include "objects/damage.h"
#include "units/units.h"
#include "units/unit_definitions.h"
#include "physics/collisions.h"
#include "network_coop.h"
#include "network_interaction.h"
#include "../src/port_config.h"
#include "vr_interaction_impact.h"
#include "vr_interaction_impact_math.h"
#include <string.h>
void platform_log(char const *format, ...);
/* Fixed storage, refreshed by held objects; expired thrown entries are reused. */
static struct impact_entry {
    long object, owner, expiry, last_tick, last_target;
    float mobility, units;
    int active;
} entries[64];
static struct { long object; struct collision_result hit; real_vector3d velocity; } pending[64];
static int pending_count;
static boolean authority(void)
{
    return game_connection() == _game_connection_local ||
        (game_connection() == _game_connection_network_server && network_coop_active() && network_interaction_host_ready());
}
void vr_interaction_impact_reset(void) { memset(entries, 0, sizeof(entries)); pending_count=0; }
void vr_interaction_impact_track(long object, long owner_unit, float mobility, float units)
{
    int i, slot = -1;
    long tick = game_time_get();
    if (!authority() || !config_boolean("vr.interaction_damage") ||
        !object_try_and_get(object) || !unit_try_and_get(owner_unit) ||
        !isfinite(mobility) || mobility <= 0 || !isfinite(units) || units <= 0) return;
    for (i=0; i<64; ++i) {
        if (entries[i].active && entries[i].object == object) { slot=i; break; }
        if (!entries[i].active || entries[i].expiry < tick) slot=i;
    }
    if (slot < 0) return;
    if (!entries[slot].active || entries[slot].object != object) {
        memset(&entries[slot],0,sizeof(entries[slot]));
        entries[slot].last_tick = -100;
        entries[slot].last_target = NONE;
    }
    entries[slot].active=TRUE; entries[slot].object=object;
    entries[slot].owner=owner_unit; entries[slot].mobility=mobility;
    entries[slot].units=units; entries[slot].expiry=tick+90;
}
static void apply_collision(long index, struct collision_result const *hit,
    real_vector3d const *velocity)
{
    int i;
    long tick=game_time_get(), target;
    struct unit_datum *owner;
    struct object_datum *source, *victim;
    struct unit_definition *definition;
    struct damage_data damage;
    float scale, units;
    if (!authority() || !config_boolean("vr.interaction_damage") || !hit || !velocity ||
        !(source=object_try_and_get(index))) return;
    if(game_connection()==_game_connection_local &&
        !config_boolean(source->object.type==_object_type_biped?"vr.npc_interaction":"vr.world_interaction")) return;
    for(i=0;i<64;++i) if(entries[i].active && entries[i].object==index) break;
    if(i==64 || tick>entries[i].expiry || tick<entries[i].last_tick) return;
    /* NPCs can injure themselves against real world surfaces; props only
     * damage the struck object. No radius/AOE or client-declared hit. */
    if(hit->type!=_collision_result_object && hit->type!=_collision_result_structure) return;
    target=hit->type==_collision_result_object ? hit->object_index :
        (source->object.type==_object_type_biped ? index : NONE);
    if(target==NONE || target==entries[i].owner ||
        !(victim=object_try_and_get(target)) ||
        TEST_FLAG(victim->object.damage_flags,_object_dead_bit) ||
        (entries[i].last_target==target && tick-entries[i].last_tick<10) ||
        !(owner=unit_try_and_get(entries[i].owner))) return;
    definition=unit_definition_get(owner->definition_index);
    if(definition->unit.melee_damage.index==NONE) return;
    units=entries[i].units;
    scale=vr_interaction_impact_scale(-dot_product3d(velocity,&hit->plane.n),units,
        entries[i].mobility,config_real("vr.impact_threshold"),config_real("vr.impact_damage_cap"));
    if(scale<=0) return;
    entries[i].last_tick=tick; entries[i].last_target=target;
    damage_data_new(&damage,definition->unit.melee_damage.index);
    damage.owner_object_index=entries[i].owner;
    damage.owner_player_index=owner->unit.player_index;
    damage.owner_team_index=owner->object.owner_team_index;
    damage.location=hit->location; damage.origin=hit->point; damage.epicenter=hit->point;
    damage.direction=*velocity; normalize3d(&damage.direction); damage.scale=scale;
    object_cause_damage(&damage,target,hit->type==_collision_result_object?hit->node_index:NONE,
        hit->type==_collision_result_object?hit->region_index:NONE,
        hit->type==_collision_result_object?hit->material_index:NONE,&hit->plane.n);
    platform_log("VR impact: object=%08lx target=%08lx owner=%08lx scale=%.3f",index,target,entries[i].owner,scale);
}

void vr_interaction_impact_collision(long object, struct collision_result const *hit,
    real_vector3d const *velocity)
{
    int i;
    if(!authority() || !hit || !velocity || pending_count>=64) return;
    for(i=0;i<64;++i) if(entries[i].active && entries[i].object==object) break;
    if(i==64) return;
    pending[pending_count].object=object; pending[pending_count].hit=*hit;
    pending[pending_count++].velocity=*velocity;
}
void vr_interaction_impact_flush(void)
{
    int count=pending_count, i;
    pending_count=0;
    for(i=0;i<count;++i) apply_collision(pending[i].object,&pending[i].hit,&pending[i].velocity);
}
