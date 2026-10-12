/* Optional bounded articulated NPC interaction. Native sphere collision owns
 * ordinary NPC root motion; joint palettes own limb collision. Local play or
 * negotiated co-op host authority only; actor metadata is never recreated. */
#include "cseries.h"
#include "game/game.h"
#include "game/game_allegiance.h"
#include "game/players.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "ai/actors.h"
#include "ai/actor_types.h"
#include "ai/actor_definitions.h"
#include "cache/cache_files.h"
#include "units/units.h"
#include "units/bipeds.h"
#include "units/biped_definitions.h"
#include "items/weapons.h"
#include "physics/collisions.h"
#include "physics/collision_models.h"
#include "physics/collision_bsp.h"
#include "physics/physics.h"
#include "physics/collision_features.h" /* collision_test_sphere: a float radius needs its prototype */
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_npc_interaction.h"
#include "vr_articulated_native.h"
#include "vr_world_math.h"
#include "vr_interaction_hold_math.h"
#include "vr_world_interaction.h"
#include "network_interaction.h"
#include "vr_interaction_impact.h"
#include "vr_npc_impulse.h"
#include <math.h>
#include <string.h>
void platform_log(char const *,...);
unsigned long system_milliseconds(void);
static unsigned long timing_frames,timing_total,timing_maximum;
#ifndef HALO_VR
#define VR_INTERACTION_NONE 0
#define VR_INTERACTION_NPC 5
#define vr_interaction_release(h,o) ((void)0)
#define vr_interaction_owner(h) 0
#define vr_interaction_claim(h,o) 0
#define vr_interaction_grip(h,p,r) 0
#define vr_weapon_hand() 0
#define vr_hand_empty() 0
#define vr_hand_world(h,c,p,f,u) 0
#define vr_haptic(h,a,t) ((void)0)
static float vr_units_per_metre(void){return 0.32808399f;}
#endif

enum { NPC_POOL_SIZE=VR_NPC_INTERACTION_POOL_SIZE, NPC_REMOTE_PLAYERS=128 };
/* A released body is handed back to the engine within bounded time. Test46
 * logs showed a released Jackal's rig still simulating 85 seconds later: a
 * live NPC waited for its standing pose to be entirely clear of the BSP (a
 * body lying on a floor or against a wall may never be), and a corpse for
 * the engine's at-rest flag, so the AI stayed suppressed indefinitely. */
enum {
    NPC_SETTLE_LIMIT_TICKS=150,   /* 5 s a corpse settles before native dead-body physics */
    NPC_RECOVERY_BLEND_TICKS=12,  /* Test56: 0.4 s from the limp pose to the get-up (was 0.6 s) */
    NPC_HANDOFF_LIMIT_TICKS=9     /* Test56: 0.3 s blocked pose handoff, then the native pose (was 1.5 s) */
};
static struct npc_state {
    int active,recovery,settling,minimum_hands,started,is_remote,getting_up,torso_node,species_type,was_garbage;
    int settle_stuck_logged,recovery_blocked_logged;
    int recovery_blocked_ticks;
    /* Test54: death (a ragdoll begun at death, not by a hand) and the
     * pelvis-to-root offset a released body's root follows while it settles */
    int death,root_follow;
    real_vector3d root_offset,last_delta[2];
    real mobility;
    long index,tick,player;
    struct vr_articulated_native rig;
    int node[2],held[2],edge[2],sample[2],strain_logged[2],sample_rebased[2];
    /* Test56: each hand's last few ticks of movement (vr_world_throw_peak) */
    float history[2][VR_WORLD_THROW_HISTORY][3];
    int history_count[2],history_next[2];
    real_vector3d offset[2],root_anchor[2],velocity[2];
    real_vector3d body_forward_local;
    real_point3d target[2],previous[2],root;
} npc_pool[NPC_POOL_SIZE],*npc_current=&npc_pool[0];
#define npc (*npc_current)
static struct remote_state {long player,candidate[2];int valid,held[2],seen[2],edge[2];real_point3d point[2];} remote_pool[NPC_REMOTE_PLAYERS],*remote_current=&remote_pool[0];
#define remote (*remote_current)
static int local_edges[2]={1,1};
static struct {long definition;short type;int valid;} species_cache[64];
/* Cache only graph profiles that passed live capture plus rooted native-biped
 * validation. A failed capture may be transient (for example during a pose
 * update), so failures are deliberately retried rather than cached. */
static struct {long definition;int valid;} custom_rig_graph_cache[64];
static void cancel_one(void);
static struct npc_state *free_state(void)
{
    int n,limit=PIN(config_integer("vr.npc_max_ragdolls"),1,NPC_POOL_SIZE);
    for(n=0;n<limit;++n) if(!npc_pool[n].active) return &npc_pool[n];
    return NULL;
}
static struct npc_state *state_for_object(long index)
{
    for(int n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active&&npc_pool[n].index==index) return &npc_pool[n];
    return NULL;
}
static int select_owner(long player,int is_remote,int hand)
{
    int n;
    for(n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active && npc_pool[n].player==player &&
        npc_pool[n].is_remote==is_remote && (hand<0?(npc_pool[n].held[0]||npc_pool[n].held[1]):npc_pool[n].held[hand])) {npc_current=&npc_pool[n];return TRUE;}
    for(n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active && npc_pool[n].player==player &&
        npc_pool[n].is_remote==is_remote && npc_pool[n].minimum_hands>1 && (npc_pool[n].held[0]||npc_pool[n].held[1])) {npc_current=&npc_pool[n];return TRUE;}
    if(free_state()) {npc_current=free_state();return TRUE;}
    return FALSE;
}
static long probe_remote(real_point3d const *point,real_point3d const *camera,long player_unit,long required,int hand);
static real interaction_units(void) {return npc.is_remote?.32808399f:vr_units_per_metre();}
static real npc_setting(char const *key,real fallback,real low,real high)
{
    double value=config_real(key);
    return isfinite(value)?PIN((real)value,low,high):fallback;
}
/* Test56: NPC RECOVERY, the longest a living NPC lies limp after a hand lets
 * it go (0.25 to 1 s; the owner: never more than 1 s) */
static int npc_recovery_ticks(void)
{
    return (int)ceilf(npc_setting("vr.npc_recovery",1.0f,0.25f,1.0f)*(real)TICKS_PER_SECOND);
}
/* Test54: whether the state's feature is still on (a death ragdoll needs only
 * DEATH RAGDOLLS; a hand's grab needs NPC GRAB). */
static int feature_enabled(void)
{
    return npc.is_remote||config_boolean("vr.npc_interaction")||(npc.death&&config_boolean("vr.death_ragdolls"));
}
static int authority(void)
{
    return game_connection()==_game_connection_local ||
        (config_boolean("net.physical_interactions") && network_interaction_npc_ready());
}
int vr_npc_interaction_remote(long player_index,int hand,int held,const float world[3])
{
    struct player_datum *player;
    struct unit_datum *unit;
    real_point3d camera,point;
    real_vector3d delta;
    unsigned int slot=(unsigned int)player_index&0xffff;
    if(hand<0 || hand>1 || !world || !config_boolean("net.physical_interactions") ||
       !network_interaction_npc_ready() || slot>=NPC_REMOTE_PLAYERS || !select_owner(player_index,TRUE,hand)) return FALSE;
    remote_current=&remote_pool[slot];
    player=player_try_and_get(player_index);
    unit=player?(struct unit_datum *)object_try_and_get_and_verify_type(player->unit_index,_object_mask_biped):NULL;
    if(!unit || unit->object.parent_object_index!=NONE || TEST_FLAG(unit->object.damage_flags,_object_dead_bit)) return FALSE;
    memcpy(point.n,world,sizeof(point.n));if(!valid_real_point3d(&point)) return FALSE;
    unit_get_camera_position(player->unit_index,&camera);vector_from_points3d(&camera,&point,&delta);
    if(magnitude3d(&delta)>1.5f*.32808399f) return FALSE;
    if(!remote.valid || remote.player!=player_index) {memset(&remote,0,sizeof(remote));remote.player=player_index;remote.valid=1;}
    if(held && !(npc.active && npc.is_remote && npc.player==player_index && npc.held[hand])) {
        long required=npc.active&&npc.minimum_hands>1?npc.index:NONE;
        long selected=probe_remote(&point,&camera,player->unit_index,required,hand);
        if(selected==NONE) return FALSE;
        remote.candidate[hand]=selected;
    }
    remote.seen[hand]=1;remote.held[hand]=held!=0;remote.point[hand]=point;
    return TRUE;
}
void vr_npc_interaction_remote_cancel(long player,int hand)
{
    unsigned int slot=(unsigned int)player&0xffff;
    if(slot>=NPC_REMOTE_PLAYERS) return;
    remote_current=&remote_pool[slot];
    if(hand<0 || hand>1 || !remote.valid || remote.player!=player) return;
    remote.held[hand]=0;remote.seen[hand]=0;
    for(int n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active && npc_pool[n].is_remote && npc_pool[n].player==player && npc_pool[n].held[hand]) {
        npc_current=&npc_pool[n];cancel_one();
    }
    if(!remote.seen[0]&&!remote.seen[1]) remote.valid=0;
}
int vr_npc_interaction_snapshot(long *index,int *count,real_matrix4x3 *matrices,int capacity)
{
    static int cursor;
    if(!index || !count || !matrices) return FALSE;
    for(int n=0;n<NPC_POOL_SIZE;++n) {
        struct npc_state *state=&npc_pool[cursor];
        cursor=(cursor+1)%NPC_POOL_SIZE;
        if(!state->active || !state->started || capacity<state->rig.body.count) continue;
        *index=state->index;*count=state->rig.body.count;
        memcpy(matrices,state->rig.captured,state->rig.body.count*sizeof(*matrices));return TRUE;
    }
    return FALSE;
}
/* Deliberate gameplay strength classes, not invented kilogram tag data.
 * Exact native actor enums determine support; graph data defines joints. */
static int species(short type,int *hands,real *mobility)
{
    *hands=1;*mobility=.5f;
    switch(type) {
    case _actor_grunt:return TRUE;
    case _actor_jackal:*mobility=.4f;return TRUE;
    case _actor_marine:case _actor_crew:*mobility=.35f;return TRUE;
    case _actor_elite:case _actor_combat_form:*hands=2;*mobility=.25f;return TRUE;
    case _actor_hunter:*hands=2;*mobility=.12f;return TRUE;
    case _actor_carrier_form:*hands=2;*mobility=.2f;return TRUE;
    default:
        /* The Assassin actor enum aliases the native Elite actor behavior and
         * rig family. It has a known two-hand profile; the unclassified path
         * below handles validated custom humanoid graphs. */
        if(!config_boolean("vr.custom_npc_rigs") || type!=_actor_assassin ||
           actor_type_get_swarm(type) || actor_type_get_race(type)!=_race_covenant)
            return FALSE;
        *hands=2;*mobility=.25f;return TRUE;
    }
}
static int custom_rig_graph_valid(struct unit_datum *unit,long index)
{
    struct biped_definition *definition;
    struct vr_articulated_native rig;
    int slot=-1,n;
    if(!unit || index==NONE || unit->definition_index==NONE)return FALSE;
    for(n=0;n<NUMBEROF(custom_rig_graph_cache);++n) {
        if(custom_rig_graph_cache[n].valid && custom_rig_graph_cache[n].definition==unit->definition_index)return TRUE;
        if(!custom_rig_graph_cache[n].valid && slot<0)slot=n;
    }
    /* Native capture validates the loaded animation-graph block, parent
     * indices, finite authored axes/ranges, current matrices and the 64-node
     * bound. Count alone is not evidence of a safe articulated biped graph. */
    if(!vr_articulated_native_capture(index,&rig) || rig.body.count<4 ||
       rig.body.count>VR_ARTICULATED_NODES || rig.body.nodes[0].parent!=-1)return FALSE;
    definition=biped_definition_get(unit->definition_index);
    if(!definition)return FALSE;
    /* Use the engine's native biped classification and capsule, but do not
     * assume a custom rig has the stock head/pelvis split. The articulated
     * solver retains its complete authored parent graph and contact pins the
     * touched node. That allows nonstandard grounded humanoid biped layouts
     * without guessing joint names or remapping them onto a stock skeleton. */
    if(TEST_FLAG(definition->biped.flags,_biped_flying_bit) ||
       !isfinite(definition->biped.collision_height_standing) ||
       !isfinite(definition->biped.collision_radius) ||
       definition->biped.collision_height_standing<=0 || definition->biped.collision_radius<=0 ||
       definition->biped.collision_height_standing<=definition->biped.collision_radius*2)return FALSE;
    /* Native capture already checks all matrices, axes, ranges and parents;
     * repeat the complete rooted-tree condition here because this decision is
     * cached for later instances of the same custom biped definition. */
    for(n=1;n<rig.body.count;++n) {
        int parent=rig.body.nodes[n].parent;
        if(parent<0 || parent>=n)return FALSE;
    }
    if(slot>=0) {
        custom_rig_graph_cache[slot].definition=unit->definition_index;
        custom_rig_graph_cache[slot].valid=1;
    }
    return TRUE;
}
static int custom_humanoid_rig(short type,struct unit_datum *unit,long index,int *hands,real *mobility)
{
    struct actor_datum *actor;
    struct actor_definition *actor_definition;
    short race;
	/* Validated custom-layout fallbacks are local-only. Known species continue
	 * to use their existing negotiated path; custom graph layouts are never
	 * assumed to match another peer's tag revision. */
	if(!config_boolean("vr.custom_npc_rigs") || game_connection()!=_game_connection_local)return FALSE;
    /* CE content reuses the fixed actor-type enum, so the actor name alone
     * cannot distinguish custom variants. Admit an otherwise-unprofiled actor
     * only when its actor definition proves a grounded, non-swarm
     * human/Covenant/Flood biped and the complete native rig is safe. This
     * handles arbitrary authored humanoid joint layouts without claiming
     * support for non-biped, flying, swarm, malformed or scripted rigs. */
    if(type<0 || type>=NUMBER_OF_ACTOR_TYPES || !unit || index==NONE)return FALSE;
    if(actor_type_get_swarm(type))return FALSE;
    race=actor_type_get_race(type);
    if(race!=_race_human && race!=_race_covenant && race!=_race_floodcombat)return FALSE;
    actor=unit->unit.actor_index!=NONE?actor_try_and_get(unit->unit.actor_index):NULL;
    if(!actor || actor->meta.swarm || actor->meta.definition_index==NONE)return FALSE;
    actor_definition=actor_definition_get(actor->meta.definition_index);
    if(!actor_definition || TEST_FLAG(actor_definition->flags,_actor_definition_flying_bit) ||
       TEST_FLAG(actor_definition->flags,_actor_definition_swarm_actor_bit))return FALSE;
    if(!custom_rig_graph_valid(unit,index))return FALSE;
    /* Generic custom-layout profiles are deliberately conservative: both
     * hands must be engaged and mobility is no stronger than the validated
     * Elite-family path. */
    *hands=2;*mobility=.25f;
    return TRUE;
}
static int interaction_profile(short type,struct unit_datum *unit,long index,int *hands,real *mobility)
{
    return species(type,hands,mobility) || custom_humanoid_rig(type,unit,index,hands,mobility);
}
/* Collision models may report their root node (0) or NONE for broad body
 * contact. Neither identifies a limb that can be pinned by the articulated
 * solver. Map those contacts to the nearest authored non-root joint, while
 * preserving valid explicit nodes and the distinct-node rule for heavy NPCs. */
static int npc_contact_node(struct vr_articulated_native const *rig,short hit_node,
    real_point3d const *contact,real units,int other_node,int *mapped)
{
    real best_distance_squared=INFINITY;
    real maximum_distance;
    int best=NONE;
    if(mapped)*mapped=FALSE;
    if(!rig||!contact||rig->body.count<2||rig->body.count>VR_ARTICULATED_NODES||
       !valid_real_point3d(contact)||!isfinite(units)||!(units>0.0f&&units<100.0f)||
       hit_node < NONE || hit_node >= rig->body.count)return NONE;
    if(hit_node>0&&hit_node!=other_node)return hit_node;
    maximum_distance=.22f*units;
    for(int node=1;node<rig->body.count;++node){
        real distance_squared=0;
        if(node==other_node)continue;
        for(int axis=0;axis<3;++axis){
            real delta=rig->body.nodes[node].position[axis]-contact->n[axis];
            if(!isfinite(delta)){distance_squared=INFINITY;break;}
            distance_squared+=delta*delta;
        }
        if(!isfinite(rig->body.nodes[node].radius)||rig->body.nodes[node].radius<0)continue;
        maximum_distance=MAX(maximum_distance,rig->body.nodes[node].radius*4.0f);
        if(distance_squared<best_distance_squared){best_distance_squared=distance_squared;best=node;}
    }
    if(best==NONE||!isfinite(best_distance_squared)||best_distance_squared>maximum_distance*maximum_distance)return NONE;
    if(mapped)*mapped=TRUE;
    return best;
}
/* Test54: the nearest bone capsule (parent joint to joint, about a limb's
 * thickness plus the hand's reach) the hand point lies in; NONE when the hand
 * touches none. The touched joint becomes the hold's pinned node. */
static int npc_body_touch(struct vr_articulated_native const *rig,real_point3d const *point,
    real reach,real units,int other_node)
{
    int best=NONE;
    real best_distance=INFINITY;
    if(!rig||!point||rig->body.count<2||rig->body.count>VR_ARTICULATED_NODES||!valid_real_point3d(point)||
       !isfinite(reach)||!(units>0.0f))return NONE;
    for(int n=1;n<rig->body.count;++n) {
        int parent=rig->body.nodes[n].parent;
        real distance;
        if(parent<0||parent>=rig->body.count||n==other_node)continue;
        distance=vr_world_segment_distance(point->n,rig->body.nodes[parent].position,rig->body.nodes[n].position);
        if(distance<=reach&&distance<best_distance){best_distance=distance;best=n;}
    }
    /* A coincident helper joint has no length; hold its parent instead. */
    if(best!=NONE&&rig->body.nodes[best].length<.01f*units&&rig->body.nodes[best].parent>0&&
       rig->body.nodes[best].parent!=other_node)best=rig->body.nodes[best].parent;
    return best;
}
static void surface_offset(int hand,real_vector3d *offset)
{
    matrix4x3_transform_vector(&npc.rig.captured[npc.node[hand]],&npc.offset[hand],offset);
}
static short unit_species(struct unit_datum *unit,long index)
{
    struct actor_datum *actor=unit->unit.actor_index!=NONE?actor_try_and_get(unit->unit.actor_index):NULL;
    struct npc_state *state=state_for_object(index);
    int slot=-1;
    short result=NONE;
    struct tag_iterator iterator;
    long tag;
    if(actor) return actor->meta.type;
    if(state) return (short)state->species_type;
    for(int n=0;n<64;++n) {
        if(species_cache[n].valid && species_cache[n].definition==unit->definition_index) return species_cache[n].type;
        if(!species_cache[n].valid && slot<0) slot=n;
    }
    /* Corpses may have no actor datum. Loaded actor variants prove the unit
     * definition's species. Ambiguous custom-tag mappings are refused. */
    tag_iterator_new(&iterator,ACTOR_VARIANT_DEFINITION_TAG);
    while((tag=tag_iterator_next(&iterator))!=NONE) {
        struct actor_variant_definition *variant=actor_variant_definition_get(tag);
        short type;
        if(variant->unit_reference.index!=unit->definition_index || variant->actor_reference.index==NONE) continue;
        type=actor_definition_get(variant->actor_reference.index)->type;
        if(result!=NONE && result!=type) {result=NONE;break;}
        result=type;
    }
    if(slot>=0) {species_cache[slot].valid=1;species_cache[slot].definition=unit->definition_index;species_cache[slot].type=result;}
    return result;
}

static struct unit_datum *eligible(long index)
{
    struct unit_datum *u=(struct unit_datum *)object_try_and_get_and_verify_type(index,_object_mask_biped);
    struct actor_datum *a;
    int required_hands;
    real mobility;
    struct npc_state *state=state_for_object(index);
    int dead=u&&TEST_FLAG(u->object.damage_flags,_object_dead_bit);
    /* (Test55: script-named NPCs and bodies too: most placed bodies are
     * named; movie stars and scripted immediate orders stay excluded) */
    if(!u || u->unit.player_index!=NONE || (!dead&&u->unit.actor_index==NONE) ||
       u->object.parent_object_index!=NONE ||
       TEST_FLAG(u->object.flags,_object_movie_star_bit) ||
       TEST_FLAG(u->object.flags,_object_no_collisions_bit) ||
       !TEST_FLAG(u->object.flags,_object_connected_to_map_bit) ||
       TEST_FLAG(u->object.flags,_object_outside_of_map_bit) ||
       TEST_FLAG(u->unit.flags,_unit_possessed_by_recording_bit) ||
       unit_is_playing_custom_animation(index) ||
       u->unit.grenade_throw_state!=_unit_grenade_throw_idle ||
       (u->unit.animation.state>_unit_state_land_hard &&
        !(u->unit.animation.state==_unit_state_hard_ping) &&
        /* Test55: a dodging (AI impulse) or swinging (melee) fighter is a
         * normal combat state, not a scripted one: Elites dive and Marines
         * melee constantly, which kept them out of reach */
        !(u->unit.animation.state==_unit_state_ai_impulse) &&
        !(u->unit.animation.state==_unit_state_melee_attack) &&
        !(u->unit.animation.state==_unit_state_melee_continuous) &&
        !(dead&&(u->unit.animation.state==_unit_state_dying_airborne||
            u->unit.animation.state==_unit_state_dying)) &&
        !(state&&state->getting_up&&
            (u->unit.animation.state==_unit_state_resurrect_front||
             u->unit.animation.state==_unit_state_resurrect_back)))) return NULL;
    a=u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
    /* Both friendly and hostile encounter actors commonly have ordinary AI
     * command lists. Contact-grabbing overrides only transient movement and
     * trigger controls; team, orders and command lists remain native and
     * resume when released. Immediate orders remain excluded because they
     * represent a forced scripted action. A hard-ping animation is likewise
     * a normal combat reaction, not a scripted ownership transition. */
    if(!interaction_profile(unit_species(u,index),u,index,&required_hands,&mobility) ||
       (!dead&&(!a || !a->meta.active ||
        a->state.command_list_immediate))) return NULL;
    /* Test55: a firing, bursting or reloading weapon no longer refuses the
     * grab. Marines and Elites are almost always mid-burst in a fight, so the
     * Test54 rule (match native weapon_busy) left them ungrabbable. The held
     * body's next-tick controls are zeroed (vr_npc_interaction_controls): a
     * burst in progress ends at its own trigger release and a reload finishes
     * natively; no weapon state is written here. */
    return u;
}
/* Acquisition is deliberately strict: an unsupported animation, a busy
 * native weapon, or a scripted immediate command must not start a new hold.
 * Once a contact hold owns an articulated rig, however, those short-lived
 * states can change every simulation tick (combat flinch, damage, grenade
 * state, AI command transition). Re-running acquisition rules here used to
 * cancel the hold and snap the NPC back while the player's grip remained
 * closed. Continuation checks only object/session invariants that make it
 * unsafe to keep owning this exact object; the captured rig handles its
 * current pose and native recovery on release.
 */
static struct unit_datum *continuable(long index)
{
    struct unit_datum *u=(struct unit_datum *)object_try_and_get_and_verify_type(index,_object_mask_biped);
    if(!u || u->unit.player_index!=NONE || u->object.parent_object_index!=NONE ||
       TEST_FLAG(u->object.flags,_object_movie_star_bit) ||
       TEST_FLAG(u->object.flags,_object_no_collisions_bit) ||
       !TEST_FLAG(u->object.flags,_object_connected_to_map_bit) ||
       TEST_FLAG(u->object.flags,_object_outside_of_map_bit) ||
       TEST_FLAG(u->unit.flags,_unit_possessed_by_recording_bit)) return NULL;
    return u;
}
static long probe_remote(real_point3d const *point,real_point3d const *camera,long player_unit,long required,int hand)
{
    struct object_iterator it;
    struct unit_datum *unit;
    struct collision_result hit;
    struct collision_model_instance model;
    short model_node;
    struct vr_articulated_native capture;
    real_vector3d delta;
    real contact_radius=(real)vr_world_hand_contact_radius((float)config_real("vr.interaction_reach"),.32808399f);
    int budget=0;
    object_iterator_new(&it,_object_mask_biped,0);
    while((unit=object_iterator_next(&it))!=NULL) {
        struct npc_state *existing=state_for_object(it.index);
        real_point3d contact;
        int node,mapped=FALSE;
        if((required!=NONE&&required!=it.index) || (existing&&existing!=npc_current&&(existing->held[0]||existing->held[1])&&
           !(existing->is_remote&&existing->player==remote.player)) || !eligible(it.index)) continue;
        vector_from_points3d(point,&unit->object.bounding_sphere_center,&delta);
        if(magnitude3d(&delta)>unit->object.bounding_sphere_radius+contact_radius) continue;
        if(++budget>16) break;
        if(!collision_model_instance_new(&model,it.index) ||
           !collision_model_touch_sphere(&model,point,contact_radius,&model_node)) continue;
        /* A biped is selectable only when the tracked hand's collision sphere
         * overlaps its authored model. A center ray, aim direction, or broad
         * reach radius is never sufficient. */
        contact=*point;node=model_node;
        vector_from_points3d(camera,&contact,&delta);
        if(collision_test_vector(_collision_test_for_line_of_sight_flags,camera,&delta,player_unit,&hit) &&
           !(hit.type==_collision_result_object&&hit.object_index==it.index)) continue;
        if(!existing&&!vr_articulated_native_capture(it.index,&capture)) continue;
        node=npc_contact_node(existing?&existing->rig:&capture,(short)node,&contact,.32808399f,
            existing&&existing->held[1-hand]?existing->node[1-hand]:NONE,&mapped);
        if(node==NONE) continue;
        if(mapped)platform_log("VR NPC: remote contact fallback player=%ld actor=%08lx mapped_node=%d",remote.player,it.index,node);
        return it.index;
    }
    return NONE;
}
static void reset_one(void)
{
    /* Safe even after object-array replacement; no datum lookup here. */
    if(!npc.is_remote) {
        if(npc.held[0]) vr_interaction_release(0,VR_INTERACTION_NPC);
        if(npc.held[1]) vr_interaction_release(1,VR_INTERACTION_NPC);
    }
    memset(&npc,0,sizeof(npc));npc.index=npc.tick=npc.player=NONE;
    npc.edge[0]=npc.edge[1]=1;
}
static void cancel_one(void)
{
    long index=npc.active?npc.index:NONE;
    int restore_garbage=npc.was_garbage;
    reset_one();
    /* Before-save/cancellation occurs while IDs are valid. No persistent AI
     * flag was altered; regenerate a native pose before serialization. If a
     * corpse was already queued for engine cleanup, restore that queue entry
     * only after the temporary articulated hold is over. */
    if(index!=NONE && object_try_and_get_and_verify_type(index,_object_mask_biped)) {
        object_compute_node_matrices(index);
        if(restore_garbage) object_set_garbage(index,TRUE);
    }
}
void vr_npc_interaction_reset(void)
{
    for(int n=0;n<NPC_POOL_SIZE;++n) {npc_current=&npc_pool[n];reset_one();}
    memset(remote_pool,0,sizeof(remote_pool));local_edges[0]=local_edges[1]=1;
    memset(species_cache,0,sizeof(species_cache));
    memset(custom_rig_graph_cache,0,sizeof(custom_rig_graph_cache));
}
void vr_npc_interaction_cancel(void)
{
    for(int n=0;n<NPC_POOL_SIZE;++n) {npc_current=&npc_pool[n];cancel_one();}
    memset(remote_pool,0,sizeof(remote_pool));local_edges[0]=local_edges[1]=1;
}
static void cancel_one_reason(char const *reason)
{
	if(npc.active)platform_log("VR NPC: cancel actor=%08lx hand0=%d hand1=%d started=%d reason=%s",
		npc.index,npc.held[0],npc.held[1],npc.started,reason?reason:"unspecified");
	cancel_one();
}
static void log_ineligible_state(long index)
{
	struct unit_datum *u=(struct unit_datum *)object_try_and_get_and_verify_type(index,_object_mask_biped);
	struct actor_datum *a=u&&u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
	if(!u) {
		platform_log("VR NPC: eligibility lost actor=%08lx detail=datum-invalid",index);
		return;
	}
	platform_log("VR NPC: eligibility lost actor=%08lx state=%d dead=%d parent=%ld name=%ld movie_star=%d no_collision=%d connected=%d outside=%d possessed=%d custom_animation=%d grenade_state=%d actor=%ld actor_active=%d command_list=%ld immediate=%d",
		index,u->unit.animation.state,TEST_FLAG(u->object.damage_flags,_object_dead_bit),
		u->object.parent_object_index,u->object.name_index,
		TEST_FLAG(u->object.flags,_object_movie_star_bit),
		TEST_FLAG(u->object.flags,_object_no_collisions_bit),
		TEST_FLAG(u->object.flags,_object_connected_to_map_bit),
		TEST_FLAG(u->object.flags,_object_outside_of_map_bit),
		TEST_FLAG(u->unit.flags,_unit_possessed_by_recording_bit),
		unit_is_playing_custom_animation(index),u->unit.grenade_throw_state,
		u->unit.actor_index,a?a->meta.active:FALSE,
		a?a->state.command_list_index:NONE,a?a->state.command_list_immediate:FALSE);
}
/* Test54: a released (or killed) body simulates in the world; its native root
 * capsule follows the pelvis instead of carrying the limbs. Bodies thrown far
 * used to leave their root (where the engine culls, collects and later
 * rebuilds the pose) behind, so a landed corpse could vanish from view or
 * snap back to where it was let go. */
static void npc_begin_root_follow(void)
{
    struct unit_datum *u=continuable(npc.index);
    int torso=npc.torso_node>=0&&npc.torso_node<npc.rig.body.count?npc.torso_node:0;
    if(!u){npc.root_follow=0;return;}
    for(int k=0;k<3;++k) npc.root_offset.n[k]=npc.rig.body.nodes[torso].position[k]-u->object.position.n[k];
    npc.root_follow=1;
}
static void release(int hand,int throwing,char const *reason)
{
    int was_held=npc.held[hand];
    if(was_held)platform_log("VR NPC: release actor=%08lx hand=%d grip_released=%d throw=%d reason=%s",
		npc.index,hand,throwing,throwing,reason?reason:"unspecified");
    npc.held[hand]=0;if(!npc.is_remote) vr_interaction_release(hand,VR_INTERACTION_NPC);
    /* Test55: a heavy (two-hand) body let go by one hand stays in the other:
     * one hand still restrains and drags it but can no longer lift it
     * (vr_npc_interaction_velocity, the palette's sinking pin). Test54 let go
     * of both, which read as the grab failing. */
    /* Test56: only when this hand really let go (release() also runs every
     * tick for a hand that holds nothing: the log repeated 100 times). The
     * hand still holding feels the weight come onto it. */
    if(was_held && npc.active && npc.started && npc.held[1-hand] && npc.held[0]+npc.held[1]<npc.minimum_hands) {
        platform_log("VR NPC: heavy hold one hand actor=%08lx hand=%d grip=held reason=one-hand-drag (no lift)",
            npc.index,1-hand);
        if(!npc.is_remote) vr_haptic(1-hand,.45f,.08f);
    }
    npc.strain_logged[hand]=0;
    if(npc.active && !npc.held[0] && !npc.held[1] && !npc.recovery) {
        if(!npc.started) {cancel_one();return;}
        npc.settling=1;
        npc_begin_root_follow();
        if(throwing && was_held && npc.started) {
            real_vector3d velocity,peak;
            /* Test56: the hand's peak at release (vr_world_throw_peak) */
            int have_peak=vr_world_throw_peak((float const (*)[3])npc.history[hand],npc.history_count[hand],peak.n);
            if(vr_world_throw_velocity_spartan(have_peak?peak.n:npc.velocity[hand].n,have_peak?peak.n:npc.last_delta[hand].n,
                npc_setting("vr.throw_strength",2.0f,0.75f,2.0f),
                vr_world_throw_class(npc.minimum_hands,npc.mobility),interaction_units(),velocity.n)) {
                struct unit_datum *u=continuable(npc.index);
                real units=interaction_units(),speed=magnitude3d(&velocity);
                if(u) u->object.translational_velocity=velocity;
                /* The whole body carries the throw; the limb in the hand leads
                 * a little, so the body tumbles about its torso. */
                for(int n=0;n<npc.rig.body.count;++n) {
                    real lead=n==npc.node[hand]?1.25f:1.0f;
                    for(int k=0;k<3;++k)
                        npc.rig.body.nodes[n].previous[k]=npc.rig.body.nodes[n].position[k]-velocity.n[k]*lead;
                }
                if(units>0.0f) {
                    real mps=speed*(real)TICKS_PER_SECOND/units;
                    platform_log("VR NPC: throw actor=%08lx hand=%d speed_mps=%.2f class=%.2f",
                        npc.index,hand,(float)mps,(float)vr_world_throw_class(npc.minimum_hands,npc.mobility));
                    if(!npc.is_remote) vr_haptic(hand,PIN(0.25f+mps*0.025f,0.25f,0.7f),0.05f);
                }
            }
        }
    }
}
static int owns(long index)
{
    int found=0;
    for(int n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active&&npc_pool[n].index==index) {npc_current=&npc_pool[n];found=1;break;}
    if(!found) return FALSE;
    if(!authority() || !feature_enabled() || !continuable(index)) {
		if(npc.active && authority() && feature_enabled())
			log_ineligible_state(index);
        cancel_one_reason(!authority()?"authority-lost":!feature_enabled()?"feature-disabled":"target-ineligible");return FALSE;
    }
    return TRUE;
}
int vr_npc_interaction_owned(long index) {return owns(index)&&npc.started;}
int vr_npc_interaction_hand(int hand,float point[3])
{
    real_vector3d offset;
    int found=0;
    if(hand<0 || hand>1 || !point) return FALSE;
    for(int n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active&&!npc_pool[n].is_remote&&npc_pool[n].held[hand]) {npc_current=&npc_pool[n];found=1;break;}
    if(!found || !owns(npc.index)) return FALSE;
    surface_offset(hand,&offset);
    for(int k=0;k<3;++k) point[k]=npc.rig.body.nodes[npc.node[hand]].position[k]+offset.n[k];
    return TRUE;
}
long vr_npc_interaction_object(int hand)
{
    float point[3];return vr_npc_interaction_hand(hand,point)?npc.index:NONE;
}
int vr_npc_interaction_remote_contact(long player,int hand,long *object,float point[3])
{
    real_vector3d offset;
    if(hand<0 || hand>1 || !object || !point) return FALSE;
    for(int n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active&&npc_pool[n].is_remote&&npc_pool[n].player==player&&npc_pool[n].held[hand]) {
        npc_current=&npc_pool[n];if(!owns(npc.index)) return FALSE;
        surface_offset(hand,&offset);*object=npc.index;
        for(int k=0;k<3;++k) point[k]=npc.rig.body.nodes[npc.node[hand]].position[k]+offset.n[k];
        return TRUE;
    }
    return FALSE;
}
void vr_npc_interaction_controls(long index)
{
    struct unit_datum *u;
    /* Test55: a heavy body restrained by one hand (held, not yet lifted) is
     * held still too: it neither walks off nor fires while restrained. */
    if(!owns(index) || !(npc.started || npc.held[0] || npc.held[1])) return;
    u=unit_get(index);
    u->unit.control_flags=0;u->unit.primary_trigger=0;u->unit.throttle=*global_zero_vector3d;
    /* Timers, actor target, perception, team, inventory and command state stay
     * native. On release the next AI control tick supplies fresh input. */
}
void vr_npc_interaction_velocity(long index,float velocity[3])
{
    real_vector3d error={0},result;
    int count=0,h,k;
    if(!owns(index) || npc.recovery || !velocity) return;
    if(npc.root_follow && npc.settling && !npc.held[0] && !npc.held[1]) {
        int torso=npc.torso_node>=0&&npc.torso_node<npc.rig.body.count?npc.torso_node:0;
        real_vector3d follow;
        struct unit_datum *u=unit_get(index);
        for(k=0;k<3;++k) follow.n[k]=npc.rig.body.nodes[torso].position[k]-npc.root_offset.n[k]-u->object.position.n[k];
        /* The offset relaxes toward the pelvis (a lying body's root is under it). */
        for(k=0;k<2;++k) npc.root_offset.n[k]*=0.9f;
        /* Test55: a hard throw flies faster than 9 m/s; the root keeps up
         * (it is what the engine culls and collects by) */
        if(vr_world_limit(follow.n,.90f*interaction_units())) {
            velocity[0]=follow.n[0];velocity[1]=follow.n[1];
            if(follow.n[2]>velocity[2]) velocity[2]=follow.n[2]; /* rise with a body thrown up; fall natively */
        }
        return;
    }
    for(h=0;h<2;++h) if(npc.held[h]) {
        real_vector3d offset;
        surface_offset(h,&offset);
        /* The initial root-to-grab anchor is independent of the solver's
         * current pinned node. Otherwise pinning consumes the error and the
         * root never follows a lift. Only native capsule accepts this move. */
        for(k=0;k<3;++k) error.n[k]+=npc.target[h].n[k]-offset.n[k]-npc.root_anchor[h].n[k]-unit_get(index)->object.position.n[k];
        ++count;
    }
    if(!count) return;
    for(k=0;k<3;++k) error.n[k]/=count;
    if(count<npc.minimum_hands) {
        /* Test55: fewer hands than the body needs (one on an Elite or Hunter)
         * restrain and drag it along the ground, slowly, but never lift it:
         * the root keeps its native vertical motion. */
        if(vr_world_restrain(error.n,velocity,npc.mobility,interaction_units(),result.n)) {
            velocity[0]=result.n[0];velocity[1]=result.n[1];
        }
        return;
    }
    if(vr_world_spring_strength(error.n,velocity,npc.mobility,count,interaction_units(),global_gravity,
        npc.is_remote?1.5f:npc_setting("vr.npc_hold_strength",1.5f,0.75f,2.5f),result.n))
        memcpy(velocity,result.n,sizeof(result.n));
}
static void tick_player(int use_remote,long player)
{
    short local=local_player_get_next(NONE);
    int *edges=use_remote?remote.edge:local_edges;
    struct player_datum *player_datum=player!=NONE?player_try_and_get(player):NULL;
    long unit=player_datum?player_datum->unit_index:NONE,tick=game_time_get();
    struct unit_datum *u=unit!=NONE?(struct unit_datum *)object_try_and_get_and_verify_type(unit,_object_mask_biped):NULL;
    real units=use_remote?.32808399f:vr_units_per_metre();
    real_point3d camera;
    int h;
    unsigned int buttons;
    float triggers[2],thumbs[4];
    if(!authority() || (!use_remote && (!vr_active() || !config_boolean("vr.npc_interaction") ||
       !vr_controller(&buttons,triggers,thumbs))) ||
       !u || u->object.parent_object_index!=NONE || TEST_FLAG(u->object.damage_flags,_object_dead_bit) ||
       cinematic_in_progress() || (!use_remote&&director_inhibited_input(local)) || !(units>0)) {
        cancel_one_reason("session-or-owner-invalid");return;
    }
    if(tick==npc.tick && player==npc.player) return;
    if(tick<npc.tick || tick>npc.tick+1 || player!=npc.player) {
        cancel_one_reason("player-or-tick-discontinuity");
    }
    npc.tick=tick;npc.player=player;npc.is_remote=use_remote;
    if(npc.active && !owns(npc.index)) return;
    if(npc.active && npc.started) vr_interaction_impact_track(npc.index,unit,npc.mobility,units);
    unit_get_camera_position(unit,&camera);
    for(h=0;h<2;++h) {
        for(int slot=0;slot<NPC_POOL_SIZE;++slot) if(npc_pool[slot].active&&npc_pool[slot].player==player&&
            npc_pool[slot].is_remote==use_remote&&npc_pool[slot].held[h]) {npc_current=&npc_pool[slot];npc.tick=tick;break;}
        int pressed,released,grip=use_remote?remote.held[h]:vr_interaction_grip(h,&pressed,&released);
        real_point3d point;
        real contact_radius=(real)vr_world_hand_contact_radius((float)config_real("vr.interaction_reach"),(float)units);
        real_vector3d forward,up,delta;
        pressed=grip&&!edges[h];edges[h]=grip;
        if(use_remote) point=remote.point[h];
        if((use_remote&&!remote.seen[h]) || (!use_remote&&((h==vr_weapon_hand()&&!vr_hand_empty()) || !vr_hand_world(h,camera.n,point.n,forward.n,up.n)))) {
            release(h,FALSE,use_remote&&!remote.seen[h]?"remote-pose-missing":
				(!use_remote&&h==vr_weapon_hand()&&!vr_hand_empty()?"weapon-hand-occupied":"hand-tracking-lost"));
			npc.sample[h]=0;npc.velocity[h]=*global_zero_vector3d;npc.history_count[h]=0;continue;
        }
        if(npc.sample[h]) {
            vector_from_points3d(&npc.previous[h],&point,&delta);
			if(magnitude3d(&delta)>0.45f*units) {
				/* A fast swing or tracking rebase is not a release gesture.
				 * Rebase throw velocity so a pose jump cannot launch the target. */
				npc.velocity[h]=*global_zero_vector3d;npc.history_count[h]=0;
				if(!npc.sample_rebased[h])platform_log("VR NPC: hand sample rebased actor=%08lx hand=%d grip=%d held=%d movement_m=%.3f",
					npc.index,h,grip,npc.held[h],(float)magnitude3d(&delta)/(float)units);
				npc.sample_rebased[h]=1;
			} else {
				npc.sample_rebased[h]=0;
				npc.last_delta[h]=delta;
				for(int k=0;k<3;++k) npc.velocity[h].n[k]=npc.velocity[h].n[k]*.55f+delta.n[k]*.45f;
				vr_world_throw_note(npc.history[h],&npc.history_count[h],&npc.history_next[h],delta.n);
			}
        }
        if(npc.held[h]) {
			int limited=0;
			if(!vr_interaction_hold_target_step(npc.target[h].n,point.n,.45f*units,&limited)) {
				release(h,FALSE,"invalid-hand-target");npc.sample[h]=0;continue;
			}
			if(limited&&!npc.strain_logged[h]) {
				platform_log("VR NPC: hold target rate-limited actor=%08lx hand=%d grip=held max_step_m=0.450",
					npc.index,h);
				npc.strain_logged[h]=1;
			} else if(!limited)npc.strain_logged[h]=0;
		} else npc.target[h]=point;
		npc.previous[h]=point;npc.sample[h]=1;
        if(npc.held[h]) {
            real_vector3d offset;
            if(npc.node[h]<0||npc.node[h]>=npc.rig.body.count) {
				release(h,FALSE,"invalid-contact-node");continue;
			}
            surface_offset(h,&offset);
			for(int k=0;k<3;++k) delta.n[k]=npc.rig.body.nodes[npc.node[h]].position[k]+offset.n[k]-npc.target[h].n[k];
			if(magnitude3d(&delta)>.65f*units&&!npc.strain_logged[h]) {
				platform_log("VR NPC: hold strain actor=%08lx hand=%d grip=held separation_m=%.3f action=keep-contact",
					npc.index,h,(float)magnitude3d(&delta)/(float)units);
				npc.strain_logged[h]=1;
			} else if(magnitude3d(&delta)<.50f*units)npc.strain_logged[h]=0;
			if(!npc.started && !use_remote) {
				/* Test55: one hand restraining a heavy body: its resistance in
				 * the hand, and a hand pulled well clear loses its hold (a
				 * Spartan cannot keep an Elite at arm's length plus a metre). */
				real speed=magnitude3d(&npc.velocity[h])*(real)TICKS_PER_SECOND/units;
				vr_world_interaction_weight_feedback(h,npc.mobility,(float)(magnitude3d(&delta)/units),(float)speed);
				if(magnitude3d(&delta)>1.2f*units) {
					release(h,FALSE,"restraint-slipped");npc.sample[h]=0;continue;
				}
			}
        }
        if(npc.held[h] && (!grip || (!use_remote&&vr_interaction_owner(h)!=VR_INTERACTION_NPC))) {
            int intentional=!grip&&(use_remote||vr_interaction_owner(h)==VR_INTERACTION_NPC);
			release(h,intentional,intentional?"grip-released":"interaction-owner-lost");continue;
        }
        if(!pressed || npc.held[h] || npc.recovery || (!use_remote&&vr_interaction_owner(h)!=VR_INTERACTION_NONE)) continue;
        {
            struct object_iterator it;
            struct unit_datum *candidate;
            struct collision_result hit;
            struct collision_model_instance model;
            short model_node;
            int budget=0,budget_exhausted=0,scanned=0,eligible_count=0,surface_hits=0,body_hits=0;
            real body_reach=contact_radius+npc_setting("vr.npc_grab_assist",0.0f,0.0f,0.15f)*units+.07f*units;
            int graph_rejects=0,node_rejects=0,capacity_rejects=0,acquired=0;
            object_iterator_new(&it,_object_mask_biped,0);
            while((candidate=object_iterator_next(&it))!=NULL) {
                int node,mapped=FALSE;
                struct npc_state *existing=state_for_object(it.index),*destination;
                ++scanned;
                if((npc.active&&npc.minimum_hands>1&&npc.index!=it.index) ||
                   (existing&&existing!=npc_current&&(existing->held[0]||existing->held[1])&&
                    !(existing->is_remote==use_remote&&existing->player==player)) ||
                   (use_remote&&remote.candidate[h]!=it.index)) continue;
                if(!eligible(it.index)) continue;
                ++eligible_count;
                destination=existing?existing:(!npc.active?npc_current:free_state());
                if(!destination){++capacity_rejects;continue;}
                vector_from_points3d(&point,&candidate->object.bounding_sphere_center,&delta);
                if(magnitude3d(&delta)>candidate->object.bounding_sphere_radius+body_reach) continue;
                if(++budget>16) {budget_exhausted=1;break;}
                real_point3d contact;
                {
                    /* Test54: the authored collision model (the shot-hit
                     * geometry) first; otherwise the live pose's bone capsules,
                     * so a palm on a Marine's back, a Grunt's arm or a corpse
                     * lying on the floor grabs it. NPC GRAB ASSIST widens only
                     * the capsules; natural touch is the default. */
                    int captured=FALSE;
                    contact=point;
                    if(!collision_model_instance_new(&model,it.index) ||
                       !collision_model_touch_sphere(&model,&point,contact_radius,&model_node)) {
                        struct vr_articulated_native const *probe;
                        if(!existing && !vr_articulated_native_capture(it.index,&destination->rig)) {++graph_rejects;continue;}
                        captured=!existing;
                        probe=existing?&existing->rig:&destination->rig;
                        model_node=(short)npc_body_touch(probe,&point,body_reach,units,
                            destination->held[1-h]?destination->node[1-h]:NONE);
                        if(model_node==NONE) continue;
                        ++body_hits;
                    }
                    ++surface_hits;
                    node=model_node;

                    vector_from_points3d(&camera,&contact,&delta);
                    if(collision_test_vector(_collision_test_for_line_of_sight_flags,&camera,&delta,unit,&hit) &&
                       !(hit.type==_collision_result_object && hit.object_index==it.index)) continue;
                    if(!existing && !captured && !vr_articulated_native_capture(it.index,&destination->rig)) {++graph_rejects;continue;}
                }
                node=npc_contact_node(&destination->rig,(short)node,&contact,units,
                    destination->held[1-h]?destination->node[1-h]:NONE,&mapped);
                if(node==NONE){++node_rejects;continue;}
                if(!use_remote&&!vr_interaction_claim(h,VR_INTERACTION_NPC)) break;
                {
                    real_vector3d velocity=npc.velocity[h];
                    npc_current=destination;npc.player=player;npc.is_remote=use_remote;npc.tick=tick;
                    npc.target[h]=npc.previous[h]=point;npc.velocity[h]=velocity;npc.sample[h]=1;
                    npc.recovery=0;npc.recovery_blocked_logged=0;
                    if(!existing)
                        npc.was_garbage=TEST_FLAG(candidate->object.flags,_object_garbage_bit);
                }
                npc.species_type=unit_species(candidate,it.index);
                npc.active=1;npc.index=it.index;npc.node[h]=node;npc.held[h]=1;npc.root=candidate->object.position;
                object_activate(it.index);object_set_garbage(it.index,FALSE);
                if(!existing) {
                    real_matrix4x3 inverse;
                    int torso=biped_definition_get(candidate->definition_index)->biped.runtime_pelvis_node_index;
                    npc.torso_node=torso>=0&&torso<npc.rig.body.count?torso:0;
                    matrix4x3_inverse(&npc.rig.captured[npc.torso_node],&inverse);
                    matrix4x3_transform_vector(&inverse,&candidate->object.forward,&npc.body_forward_local);
                }
                if(!interaction_profile((short)npc.species_type,candidate,it.index,
                    &npc.minimum_hands,&npc.mobility)) {cancel_one_reason("unsupported-interaction-profile");break;}
                npc.settling=0;npc.settle_stuck_logged=0;
                if(!npc.started && npc.held[0]+npc.held[1]>=npc.minimum_hands) {
					npc.started=1;
					platform_log("VR NPC: hold constraint started actor=%08lx species=%d hands=%d remote=%d",
						it.index,npc.species_type,npc.held[0]+npc.held[1],use_remote);
					/* Test56: a heavy body taken up by the second hand: both
					 * hands feel it come off the ground */
					if(!use_remote && npc.minimum_hands>1) {vr_haptic(0,.5f,.05f);vr_haptic(1,.5f,.05f);}
				}
                {
                    real_matrix4x3 inverse;
                    for(int k=0;k<3;++k) {
                        delta.n[k]=contact.n[k]-npc.rig.body.nodes[node].position[k];
                        npc.root_anchor[h].n[k]=npc.rig.body.nodes[node].position[k]-candidate->object.position.n[k];
                    }
                    matrix4x3_inverse(&npc.rig.captured[node],&inverse);
                    matrix4x3_transform_vector(&inverse,&delta,&npc.offset[h]);
                }
				{
					struct actor_datum *grabbed_actor=actor_try_and_get(candidate->unit.actor_index);
					int friendly=grabbed_actor && grabbed_actor->meta.team_index>=0 &&
						!game_team_is_enemy(_game_team_player,grabbed_actor->meta.team_index);
					if(!existing) platform_log("VR NPC: temporary garbage hold actor=%08lx was_queued=%d; restore native cleanup after release/settle",
						it.index,npc.was_garbage);
				platform_log("VR NPC: grabbed actor=%08lx species=%d team=%d friendly=%d hand=%d node=%d requires=%d acquisition=authored-contact-plus-fresh-grip",
						it.index,npc.species_type,grabbed_actor?grabbed_actor->meta.team_index:NONE,
						friendly,h,node,npc.minimum_hands);
				}
                if(mapped)platform_log("VR NPC: contact fallback actor=%08lx mapped_node=%d",it.index,node);
                /* Test55: the grab's weight in the hand: a short strong pulse
                 * for a heavy body, a light tap for a Grunt or Jackal */
                if(!use_remote) vr_haptic(h,npc.minimum_hands>1?.60f:.25f,npc.minimum_hands>1?.06f:.035f);
                acquired=1;
                break;
            }
            if(!acquired)platform_log("VR NPC: contact grab miss hand=%d scanned=%d eligible=%d collision_candidates=%d body_capsule_hits=%d collision_budget=16 budget_exhausted=%d graph_rejects=%d node_rejects=%d no_rig_slot=%d contact_radius=%.2f cm body_reach=%.2f cm custom_rigs=%d",
                h,scanned,eligible_count,surface_hits,body_hits,budget_exhausted,graph_rejects,node_rejects,capacity_rejects,
                (float)contact_radius*100.0f/(float)units,(float)body_reach*100.0f/(float)units,config_boolean("vr.custom_npc_rigs"));
        }
    }
}
void vr_npc_interaction_tick(void)
{
    short local=local_player_get_next(NONE);
    long player=local!=NONE?local_player_get_player_index(local):NONE;
    if(select_owner(player,FALSE,-1)) tick_player(FALSE,player);
    for(int n=0;n<NPC_REMOTE_PLAYERS;++n) if(remote_pool[n].valid) {
        remote_current=&remote_pool[n];
        if(select_owner(remote.player,TRUE,-1)) tick_player(TRUE,remote.player);
    }
}
void vr_npc_interaction_palette(long index)
{
    struct unit_datum *u;
    real_matrix4x3 *native;
    struct vr_articulated_pin pins[2];
    real units;
    int count=0,n,k,h;
    unsigned long started;
    if(!owns(index)) return;
    started=system_milliseconds();
    units=interaction_units();
    {
        struct player_datum *owner=npc.player!=NONE?player_try_and_get(npc.player):NULL;
        if(owner) vr_interaction_impact_track(index,owner->unit_index,npc.mobility,interaction_units());
    }
    if(TEST_FLAG(unit_get(index)->object.damage_flags,_object_dead_bit)) {npc.getting_up=0;npc.recovery=0;}
    npc.rig.impact_enabled=npc.started&&!npc.recovery;
    npc.rig.impact_units=interaction_units();
    u=unit_get(index);native=object_get_node_matrices(index);
    if(!native || npc.rig.body.count>u->object.node_matrices.size/(long)sizeof(*native)) {cancel_one_reason("invalid-native-palette");return;}
    /* Translate by accepted native root motion. Ordinary NPCs already use a
     * zero-height root sphere (biped_get_physics_pill); every articulated node,
     * including the rig root, remains free and swept against world geometry. */
    if(!(npc.root_follow&&npc.settling&&!npc.held[0]&&!npc.held[1]))
    for(n=0;n<npc.rig.body.count;++n) for(k=0;k<3;++k) {
        real delta=u->object.position.n[k]-npc.root.n[k];
        npc.rig.body.nodes[n].position[k]+=delta;npc.rig.body.nodes[n].previous[k]+=delta;
        npc.rig.captured[n].position.n[k]+=delta;
    }
    npc.root=u->object.position;
    if(!npc.started) {
        /* The first grip is a support latch for heavy actors; it cannot lift
         * or collapse them until a second distinct limb is held. */
        for(n=0;n<npc.rig.body.count;++n) {
            npc.rig.captured[n]=native[n];
            memcpy(npc.rig.body.nodes[n].position,native[n].position.n,sizeof(native[n].position.n));
            memcpy(npc.rig.body.nodes[n].previous,native[n].position.n,sizeof(native[n].position.n));
        }
        return;
    }
    if(npc.recovery) {
        float targets[VR_ARTICULATED_NODES][3];
        for(n=0;n<npc.rig.body.count;++n) memcpy(targets[n],native[n].position.n,sizeof(targets[n]));
        if(!vr_articulated_recovery(&npc.rig.body,targets,1.0f/npc.recovery,vr_articulated_native_sweep,&npc.rig)) {cancel_one_reason("recovery-solver-invalid");return;}
        for(n=0;n<npc.rig.body.count;++n) {
            real t=1.0f/npc.recovery;
            real_matrix4x3 *m=&npc.rig.captured[n];
            vectors_interpolate(&m->forward,&native[n].forward,t,&m->forward);
            vectors_interpolate(&m->up,&native[n].up,t,&m->up);
            normalize3d(&m->forward);cross_product3d(&m->up,&m->forward,&m->left);normalize3d(&m->left);
            cross_product3d(&m->forward,&m->left,&m->up);
            memcpy(m->position.n,npc.rig.body.nodes[n].position,sizeof(m->position.n));
            if(!valid_real_matrix4x3(m)) {cancel_one_reason("recovery-palette-invalid");return;}
        }
        if(npc.recovery==1) {
            int clear=1;
            int blocked_node=NONE,collision_blocked=FALSE;
            real blocked_distance=0;
            for(n=0;n<npc.rig.body.count;++n) {
                real_vector3d difference;
                vector_from_points3d(&native[n].position,&npc.rig.captured[n].position,&difference);
                blocked_distance=magnitude3d(&difference);
                if(blocked_distance>.005f) {clear=0;blocked_node=n;break;}
                if(collision_test_sphere(&native[n].position,npc.rig.body.nodes[n].radius,index)) {
                    clear=0;blocked_node=n;collision_blocked=TRUE;break;
                }
            }
            if(clear) {cancel_one();return;}
            if(!npc.recovery_blocked_logged) {
                platform_log("VR NPC: native pose handoff blocked actor=%08lx node=%d recovery=%d position_delta=%.4f collision=%d",
                    index,blocked_node,npc.recovery,blocked_distance,collision_blocked);
                npc.recovery_blocked_logged=1;
            }
            if(++npc.recovery_blocked_ticks>=NPC_HANDOFF_LIMIT_TICKS) {
                /* The native pose is regenerated by cancel_one; the capsule
                 * already owns the root, so the AI resumes rather than the
                 * body staying limp because one sphere grazes the floor. */
                platform_log("VR NPC: native pose handoff forced actor=%08lx after_ticks=%d node=%d collision=%d",
                    index,npc.recovery_blocked_ticks,blocked_node,collision_blocked);
                cancel_one();return;
            }
        } else --npc.recovery;
    } else {
        for(n=0;n<2;++n) if(npc.held[n]) {
            real_vector3d offset;
            surface_offset(n,&offset);
            pins[count].node=npc.node[n];
            for(k=0;k<3;++k) pins[count].position[k]=npc.target[n].n[k]-offset.n[k];
            if(npc.node[n]<0||npc.node[n]>=npc.rig.body.count) {cancel_one_reason("invalid-pinned-node");return;}
            /* Test55: one hand on a body that needs two cannot hold it up: the
             * held limb follows the hand across and down, never up, and sinks
             * about 12 cm a second until the body rests on the ground. */
            if(npc.held[0]+npc.held[1]<npc.minimum_hands)
                pins[count].position[2]=MIN(pins[count].position[2],npc.rig.body.nodes[npc.node[n]].position[2]-.004f*units);
			if(!vr_articulated_native_sweep(&npc.rig,npc.rig.body.nodes[npc.node[n]].position,
					npc.rig.body.nodes[npc.node[n]].radius,pins[count].position)) {cancel_one_reason("pinned-node-collision-state-invalid");return;}
            ++count;
        }
        if(!vr_articulated_native_step(&npc.rig,1.f/30.f,global_gravity*900.f,pins,count)) {cancel_one_reason("articulated-solver-rejected-state");return;}
        if(npc.settling) {
            /* Test54: joints creeping slower than about 0.6 m/s lose most of
             * their motion each tick (contact friction), so a landed body
             * comes to rest instead of jittering; fast flight is untouched. */
            for(n=0;n<npc.rig.body.count;++n) {
                struct vr_articulated_node *node=&npc.rig.body.nodes[n];
                real_vector3d motion;
                for(k=0;k<3;++k) motion.n[k]=node->position[k]-node->previous[k];
                if(magnitude3d(&motion)<.02f*units)
                    for(k=0;k<3;++k) node->previous[k]=node->position[k]-motion.n[k]*.6f;
            }
        }
        if(npc.settling) {
            real maximum=0;
            int overdue,dead=TEST_FLAG(u->object.damage_flags,_object_dead_bit);
            /* Test56: a living NPC dropped or thrown gets up as soon as it
             * rests (a third of a second at the least) and never lies limp
             * longer than NPC RECOVERY (vr.npc_recovery, at most 1 s); a
             * corpse keeps the 5 s settle before native dead-body physics */
            int limit=dead?NPC_SETTLE_LIMIT_TICKS:npc_recovery_ticks(),rest=dead?30:MIN(10,limit);
            for(n=0;n<npc.rig.body.count;++n) {
                real_vector3d motion;
                for(k=0;k<3;++k) motion.n[k]=npc.rig.body.nodes[n].position[k]-npc.rig.body.nodes[n].previous[k];
                maximum=MAX(maximum,magnitude3d(&motion));
            }
            npc.settling=MIN(npc.settling+1,300);
            overdue=npc.settling>=limit;
            if(overdue && dead && !npc.settle_stuck_logged) {
                platform_log("VR NPC: settle still pending actor=%08lx ticks=%d dead=%d native_at_rest=%d max_node_step=%.4f garbage_queued=%d; handing back to the engine",
                    index,npc.settling,TEST_FLAG(u->object.damage_flags,_object_dead_bit),
                    TEST_FLAG(u->object.flags,_object_at_rest_bit),maximum,npc.was_garbage);
                npc.settle_stuck_logged=1;
            }
            if((npc.settling>=rest && maximum<.02f*interaction_units()) || overdue) {
                if(dead) {
                    /* A corpse never enters live get-up or AI recovery. Give
                     * the actual settled palette back to native dead-body
                     * relaxation when its root has reached rest (or the
                     * settle has run out of time). */
                    if(TEST_FLAG(u->object.flags,_object_at_rest_bit) || overdue) {
                        for(n=0;n<npc.rig.body.count;++n) native[n]=npc.rig.captured[n];
                        {
                            int restore_garbage=npc.was_garbage;
                            reset_one();
                            if(restore_garbage) object_set_garbage(index,TRUE);
                        }
                        biped_start_limp_body_physics(index);return;
                    }
                } else {
                int clear=1;
                for(n=0;n<npc.rig.body.count;++n) if(collision_test_sphere(&native[n].position,npc.rig.body.nodes[n].radius,index)) {clear=0;break;}
                if(clear || overdue) {
                    real_vector3d body_forward;
                    matrix4x3_transform_vector(&npc.rig.captured[npc.torso_node],&npc.body_forward_local,&body_forward);
                    npc.getting_up=unit_interaction_recover(index,body_forward.k<0);
                    npc.settling=0;npc.settle_stuck_logged=0;
                    npc.recovery=NPC_RECOVERY_BLEND_TICKS;npc.recovery_blocked_logged=0;npc.recovery_blocked_ticks=0;
                    platform_log("VR NPC: recovery object=%08lx front=%d authored=%d",index,body_forward.k<0,npc.getting_up);
                }
                }
            }
        }
    }
    for(n=0;n<npc.rig.body.count;++n) native[n]=npc.rig.captured[n];
	/* Local hands get the same optional, rate-limited load feedback as held
	 * props. Measure solver displacement/movement at the actually pinned limb;
	 * remote-owned bodies never buzz this headset. */
	if(!npc.is_remote && npc.started && !npc.recovery && isfinite(units) && units > 0.0f) {
		for(h=0;h<2;++h) if(npc.held[h] && npc.node[h]>=0 && npc.node[h]<npc.rig.body.count) {
			real_vector3d offset, strain, movement;
			struct vr_articulated_node *node=&npc.rig.body.nodes[npc.node[h]];
			real lift=0.0f;
			surface_offset(h,&offset);
			for(k=0;k<3;++k) {
				strain.n[k]=npc.target[h].n[k]-offset.n[k]-node->position[k];
				movement.n[k]=node->position[k]-node->previous[k];
			}
			/* Test55: a heavy body raised high (chest height and over the
			 * head) weighs more in the hands than one held low */
			if(npc.minimum_hands>1)
				lift=PIN((node->position[2]-u->object.position.n[2])/units-0.9f,0.0f,1.0f)*0.3f;
			vr_world_interaction_weight_feedback(h,npc.mobility,
				(float)(magnitude3d(&strain)/units+lift),
				(float)(magnitude3d(&movement)*(real)TICKS_PER_SECOND/units));
		}
	}
    {
        unsigned long elapsed=system_milliseconds()-started;
        timing_total+=elapsed;timing_maximum=MAX(timing_maximum,elapsed);
        if(++timing_frames==300) {
            platform_log("VR NPC: simulation nodes=%d ticks=%lu total_ms=%lu max_ms=%lu remote=%d",
                npc.rig.body.count,timing_frames,timing_total,timing_maximum,npc.is_remote);
            timing_frames=timing_total=timing_maximum=0;
        }
    }
}

/* Test55: the last few hits on bipeds (object_cause_damage), so a death
 * ragdoll can start from where the killing blow landed. Test56: with how hard
 * it was (vr_npc_impulse.h); hits on one body in one tick (shotgun pellets)
 * add up in one note, which keeps the point of the hardest. Fixed storage;
 * read only within a couple of ticks of the hit. */
static struct {long object,tick;int area;real_point3d point;real_vector3d direction;struct vr_npc_hit hit;} npc_damage_notes[16];
static int npc_damage_cursor;
/* Test59: the shots each body took over the last half second (DEATH FORCE's
 * burst push, vr_npc_impulse.h); fixed storage, the oldest taken */
static struct {long object,tick;real damage;} npc_bursts[32];
static int npc_burst_cursor;
static int npc_death_force(void)
{
    return vr_npc_force_from_name(config_string("vr.death_force"));
}
static void npc_note_burst(long object,real damage)
{
    long now=game_time_get();
    int n;
    for(n=0;n<(int)NUMBEROF(npc_bursts);++n) if(npc_bursts[n].object==object) {
        npc_bursts[n].damage=vr_npc_burst_add(npc_bursts[n].damage,now-npc_bursts[n].tick,damage);
        npc_bursts[n].tick=now;
        return;
    }
    npc_bursts[npc_burst_cursor].object=object;
    npc_bursts[npc_burst_cursor].tick=now;
    npc_bursts[npc_burst_cursor].damage=vr_npc_burst_add(0.0f,0,damage);
    npc_burst_cursor=(npc_burst_cursor+1)%(int)NUMBEROF(npc_bursts);
}
static real npc_burst_damage(long object)
{
    long now=game_time_get();
    for(int n=0;n<(int)NUMBEROF(npc_bursts);++n)
        if(npc_bursts[n].object==object && now>=npc_bursts[n].tick && now-npc_bursts[n].tick<=VR_NPC_BURST_TICKS)
            return vr_npc_burst_add(npc_bursts[n].damage,now-npc_bursts[n].tick,0.0f);
    return 0.0f;
}
void vr_npc_interaction_note_damage(long object,real_point3d const *point,real_vector3d const *direction,
    real damage,real acceleration,short category,int area)
{
#ifdef HALO_VR
    real_vector3d unit_direction;
    struct vr_npc_hit hit;
    long now;
    int last=(npc_damage_cursor+(int)NUMBEROF(npc_damage_notes)-1)%(int)NUMBEROF(npc_damage_notes);
    if(object==NONE || !point || !direction || !valid_real_point3d(point) ||
       !config_boolean("vr.death_ragdolls") ||
       !vr_npc_hit_kick_force(damage,acceleration,category,area,vr_units_per_metre(),npc_death_force(),&hit)) return;
    if(!area && category!=VR_NPC_HIT_CATEGORY_MELEE && !(acceleration>0.0f)) npc_note_burst(object,damage);
    unit_direction=*direction;
    if(!valid_real_vector3d(&unit_direction) || normalize3d(&unit_direction)<0.0001f) return;
    now=game_time_get();
    if(npc_damage_notes[last].object==object && npc_damage_notes[last].tick==now) {
        if(hit.local>npc_damage_notes[last].hit.local) {
            npc_damage_notes[last].point=*point;npc_damage_notes[last].direction=unit_direction;
        }
        if(area) npc_damage_notes[last].area=TRUE;
        vr_npc_hit_add(&npc_damage_notes[last].hit,&hit);
        return;
    }
    npc_damage_notes[npc_damage_cursor].object=object;
    npc_damage_notes[npc_damage_cursor].tick=now;
    npc_damage_notes[npc_damage_cursor].area=area?TRUE:FALSE;
    npc_damage_notes[npc_damage_cursor].point=*point;
    npc_damage_notes[npc_damage_cursor].direction=unit_direction;
    npc_damage_notes[npc_damage_cursor].hit=hit;
    npc_damage_cursor=(npc_damage_cursor+1)%(int)NUMBEROF(npc_damage_notes);
#else
    (void)object;(void)point;(void)direction;(void)damage;(void)acceleration;(void)category;(void)area;
#endif
}
static int npc_recent_damage(long object,real_point3d *point,real_vector3d *direction,struct vr_npc_hit *hit,int *area)
{
    long now=game_time_get();
    for(int n=0;n<(int)NUMBEROF(npc_damage_notes);++n) {
        int slot=(npc_damage_cursor+(int)NUMBEROF(npc_damage_notes)-1-n)%(int)NUMBEROF(npc_damage_notes);
        if(npc_damage_notes[slot].object==object && now>=npc_damage_notes[slot].tick && now-npc_damage_notes[slot].tick<=2) {
            *point=npc_damage_notes[slot].point;*direction=npc_damage_notes[slot].direction;
            *hit=npc_damage_notes[slot].hit;*area=npc_damage_notes[slot].area;return TRUE;
        }
    }
    return FALSE;
}

/* Test54: DEATH RAGDOLLS. A supported NPC killed where this machine owns the
 * simulation (solo, or a co-op host whose clients take its rig poses) falls
 * as the same articulated body a hand would hold: its last living pose, the
 * momentum the killing blow gave it, mass by joint and the world's collision.
 * It then rests and is handed back to native dead-body physics as a corpse
 * that can be picked up again. No slot free, unsupported rig, or too far from
 * every local player: the stock death animation plays as before. */
void vr_npc_interaction_death(long index)
{
#ifdef HALO_VR
    struct unit_datum *u;
    struct npc_state *state,*saved;
    int hands;
    real mobility,units=vr_units_per_metre();
    short local,species;
    int near=FALSE;
    if(!config_boolean("vr.death_ragdolls") || !vr_active() || !authority() || !(units>0.0f) ||
       state_for_object(index) || !(state=free_state())) return;
    u=(struct unit_datum *)object_try_and_get_and_verify_type(index,_object_mask_biped);
    if(!u || u->unit.player_index!=NONE || !TEST_FLAG(u->object.damage_flags,_object_dead_bit) ||
       u->object.parent_object_index!=NONE ||
       TEST_FLAG(u->object.flags,_object_movie_star_bit) || TEST_FLAG(u->object.flags,_object_outside_of_map_bit) ||
       !TEST_FLAG(u->object.flags,_object_connected_to_map_bit) || cinematic_in_progress()) return;
    for(local=local_player_get_next(NONE);local!=NONE;local=local_player_get_next(local)) {
        long player=local_player_get_player_index(local);
        struct player_datum *datum=player!=NONE?player_try_and_get(player):NULL;
        struct object_datum *body=datum&&datum->unit_index!=NONE?object_try_and_get_and_verify_type(datum->unit_index,_object_mask_unit):NULL;
        real_vector3d between;
        if(!body)continue;
        vector_from_points3d(&body->object.position,&u->object.position,&between);
        if(magnitude3d(&between)<=40.0f*units){near=TRUE;break;}
    }
    if(!near)return;
    /* A death can come in the middle of another hold's tick (a thrown body's
     * impact kills an NPC): keep that hold's state current afterwards. */
    saved=npc_current;
    npc_current=state;
    reset_one();
    /* Test55: the species is read before this slot claims the body. Test54
     * read it after (npc.active and npc.index already set), so it found this
     * slot's own blank species: every corpse was logged as an Elite (0) and a
     * still-settling Grunt corpse needed two hands to pick up. */
    species=unit_species(u,index);
    if(!interaction_profile(species,u,index,&hands,&mobility) ||
       !vr_articulated_native_capture(index,&npc.rig)) {reset_one();npc_current=saved;return;}
    {
        real_vector3d velocity=u->object.translational_velocity;
        int torso=biped_definition_get(u->definition_index)->biped.runtime_pelvis_node_index;
        real capture_limit=.30f;
        /* Test59: DEATH FORCE keeps more of a blast's own throw: the engine
         * gave a body near the blast more than 9 m/s, which was clipped to it
         * (owner's 05:37 log: speed_mps=9.00 for every explosion death) */
        {
            real_point3d peek_point;real_vector3d peek_direction;
            struct vr_npc_hit peek={0,0,0};
            int peek_area=FALSE;
            if(npc_death_force()>VR_NPC_FORCE_CLASSIC &&
               npc_recent_damage(index,&peek_point,&peek_direction,&peek,&peek_area) && peek_area)
                capture_limit=.40f;
        }
        if(!vr_world_limit(velocity.n,capture_limit*units))velocity=*global_zero_vector3d;
        npc.active=1;npc.started=1;npc.death=1;npc.index=index;npc.player=NONE;npc.tick=game_time_get();
        npc.species_type=species;npc.minimum_hands=hands;npc.mobility=mobility;
        npc.root=u->object.position;npc.settling=1;
        npc.torso_node=torso>=0&&torso<npc.rig.body.count?torso:0;
        {
            real_matrix4x3 inverse;
            matrix4x3_inverse(&npc.rig.captured[npc.torso_node],&inverse);
            matrix4x3_transform_vector(&inverse,&u->object.forward,&npc.body_forward_local);
        }
        for(int n=0;n<npc.rig.body.count;++n) for(int k=0;k<3;++k)
            npc.rig.body.nodes[n].previous[k]=npc.rig.body.nodes[n].position[k]-velocity.n[k];
        /* Test55: the killing blow lands where it hit. The joints nearest the
         * impact take a kick along the shot (falling off over ~35 cm), so a
         * shot leg buckles, a head shot snaps back and the body turns about
         * the hit instead of the whole body sliding as one piece. Test56: as
         * hard as the weapon (vr_npc_impulse.h): a sniper round snaps harder
         * than a rifle bullet, a melee blow shoves the body, an explosion
         * throws it away from the blast with some lift. */
        {
            real_point3d hit;real_vector3d direction;
            struct vr_npc_hit blow={0,0,0};
            int hit_node=NONE,area=FALSE;
            if(npc_recent_damage(index,&hit,&direction,&blow,&area)) {
                real kick,falloff=.35f*units,nearest=INFINITY;
                real_vector3d push;
                /* Test59: DEATH FORCE: a shot body goes back along the shots,
                 * as hard as the burst that killed it */
                if(!area) {
                    real burst=vr_npc_burst_body(npc_burst_damage(index),npc_death_force());
                    if(burst>blow.body) blow.body=burst;
                    if(vr_npc_burst_lift(burst)>blow.lift) blow.lift=vr_npc_burst_lift(burst);
                }
                kick=blow.local*units/(real)TICKS_PER_SECOND;
                if(area) {
                    /* away from the blast, through the body's middle */
                    real_vector3d away;
                    for(int axis=0;axis<3;++axis) away.n[axis]=npc.rig.body.nodes[npc.torso_node].position[axis]-hit.n[axis];
                    if(normalize3d(&away)>=0.0001f) direction=away;
                }
                /* the whole body: what the blow adds beyond the momentum the
                 * engine already gave it (its own acceleration for melee and
                 * explosions), never taking any away */
                {
                    real along=dot_product3d(&velocity,&direction),want=blow.body*units/(real)TICKS_PER_SECOND;
                    real lift=blow.lift*units/(real)TICKS_PER_SECOND;
                    for(int axis=0;axis<3;++axis) push.n[axis]=direction.n[axis]*MAX(want-along,0.0f);
                    push.k+=MAX(lift-velocity.k,0.0f);
                }
                for(int joint=0;joint<npc.rig.body.count;++joint) for(int axis=0;axis<3;++axis) npc.rig.body.nodes[joint].previous[axis]-=push.n[axis];
                for(int n=0;n<npc.rig.body.count;++n) {
                    real_vector3d to;real distance;
                    for(int k=0;k<3;++k) to.n[k]=npc.rig.body.nodes[n].position[k]-hit.n[k];
                    distance=magnitude3d(&to);
                    if(distance<nearest){nearest=distance;hit_node=n;}
                    if(!(distance<2.0f*falloff)) continue;
                    {
                        real weight=expf(-(distance*distance)/(falloff*falloff))*kick;
                        for(int k=0;k<3;++k) npc.rig.body.nodes[n].previous[k]-=direction.n[k]*weight;
                    }
                }
                if(!(nearest<.6f*units)) hit_node=NONE;
            }
            npc.was_garbage=TEST_FLAG(u->object.flags,_object_garbage_bit);
            object_activate(index);object_set_garbage(index,FALSE);
            npc_begin_root_follow();
            platform_log("VR NPC: death ragdoll actor=%08lx species=%d nodes=%d speed_mps=%.2f hit_node=%d kick_mps=%.1f push_mps=%.1f lift_mps=%.1f explosion=%d force=%d",
                index,npc.species_type,npc.rig.body.count,(float)(magnitude3d(&velocity)*TICKS_PER_SECOND/units),hit_node,
                (float)blow.local,(float)blow.body,(float)blow.lift,area,npc_death_force());
        }
    }
    npc_current=saved;
#else
    (void)index;
#endif
}
