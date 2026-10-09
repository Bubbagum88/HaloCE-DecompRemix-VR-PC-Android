/* Optional bounded articulated NPC interaction. Native sphere collision owns
 * ordinary NPC root motion; joint palettes own limb collision. Local play or
 * negotiated co-op host authority only; actor metadata is never recreated. */
#include "cseries.h"
#include "game/game.h"
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
#include "physics/physics.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_npc_interaction.h"
#include "vr_articulated_native.h"
#include "vr_world_math.h"
#include "network_interaction.h"
#include "vr_interaction_impact.h"
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

enum { NPC_POOL_SIZE=4, NPC_REMOTE_PLAYERS=128 };
static struct npc_state {
    int active,recovery,settling,minimum_hands,started,is_remote,getting_up,torso_node,species_type;
    real mobility;
    long index,tick,player;
    struct vr_articulated_native rig;
    int node[2],held[2],edge[2],sample[2];
    real_vector3d offset[2],root_anchor[2],velocity[2];
    real_vector3d body_forward_local;
    real_point3d target[2],previous[2],root;
} npc_pool[NPC_POOL_SIZE],*npc_current=&npc_pool[0];
#define npc (*npc_current)
static struct remote_state {long player,candidate[2];int valid,held[2],seen[2],edge[2];real_point3d point[2];} remote_pool[NPC_REMOTE_PLAYERS],*remote_current=&remote_pool[0];
#define remote (*remote_current)
static int local_edges[2]={1,1};
static struct {long definition;short type;int valid;} species_cache[64];
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
static int authority(void)
{
    return game_connection()==_game_connection_local ||
        (config_boolean("net.physical_interactions") && network_interaction_host_ready());
}
int vr_npc_interaction_remote(long player_index,int hand,int held,const float world[3])
{
    struct player_datum *player;
    struct unit_datum *unit;
    real_point3d camera,point;
    real_vector3d delta;
    unsigned int slot=(unsigned int)player_index&0xffff;
    if(hand<0 || hand>1 || !world || !config_boolean("net.physical_interactions") ||
       !network_interaction_host_ready() || slot>=NPC_REMOTE_PLAYERS || !select_owner(player_index,TRUE,hand)) return FALSE;
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
    default:return FALSE; /* flying/swarm/non-biped actors need separate rigs */
    }
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
    struct weapon_datum *w;
    int required_hands;
    real mobility;
    long weapon;
    struct npc_state *state=state_for_object(index);
    int dead=u&&TEST_FLAG(u->object.damage_flags,_object_dead_bit);
    if(!u || u->unit.player_index!=NONE || (!dead&&u->unit.actor_index==NONE) ||
       u->object.parent_object_index!=NONE || u->object.name_index!=NONE ||
       TEST_FLAG(u->object.flags,_object_movie_star_bit) ||
       TEST_FLAG(u->object.flags,_object_no_collisions_bit) ||
       !TEST_FLAG(u->object.flags,_object_connected_to_map_bit) ||
       TEST_FLAG(u->object.flags,_object_outside_of_map_bit) ||
       TEST_FLAG(u->unit.flags,_unit_possessed_by_recording_bit) ||
       unit_is_playing_custom_animation(index) ||
       u->unit.grenade_throw_state!=_unit_grenade_throw_idle ||
       (!dead&&u->unit.animation.state>_unit_state_land_hard && !(state&&state->getting_up&&
        (u->unit.animation.state==_unit_state_resurrect_front||u->unit.animation.state==_unit_state_resurrect_back)))) return NULL;
    a=u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
    if(!species(unit_species(u,index),&required_hands,&mobility) ||
       (!dead&&(!a || !a->meta.active || a->state.command_list_index!=NONE || a->state.command_list_immediate))) return NULL;
    weapon=unit_inventory_get_weapon(index,u->unit.current_weapon_index);
    w=weapon!=NONE?weapon_try_and_get(weapon):NULL;
    /* Match native weapon_busy: a burst/charge/reload already in progress
     * cannot safely be cancelled by merely zeroing next-frame unit inputs. */
    if(!dead && w && (w->weapon.state!=_weapon_state_idle ||
             w->weapon.triggers[0].state!=_trigger_idle || w->weapon.triggers[1].state!=_trigger_idle ||
             w->weapon.magazines[0].state!=_magazine_idle || w->weapon.magazines[1].state!=_magazine_idle)) return NULL;
    return u;
}
static long probe_remote(real_point3d const *point,real_point3d const *camera,long player_unit,long required,int hand)
{
    struct object_iterator it;
    struct unit_datum *unit;
    struct collision_result hit;
    struct vr_articulated_native capture;
    real_vector3d delta;
    int budget=0;
    object_iterator_new(&it,_object_mask_biped,0);
    while((unit=object_iterator_next(&it))!=NULL) {
        struct npc_state *existing=state_for_object(it.index);
        real_point3d contact;
        real_point3d ray_start;
        int node;
        if((required!=NONE&&required!=it.index) || (existing&&existing!=npc_current&&(existing->held[0]||existing->held[1])&&
           !(existing->is_remote&&existing->player==remote.player)) || !eligible(it.index)) continue;
        vector_from_points3d(point,&unit->object.bounding_sphere_center,&delta);
        if(magnitude3d(&delta)>unit->object.bounding_sphere_radius+.12f*.32808399f) continue;
        if(++budget>16) break;
        if(normalize3d(&delta)<.00001f) continue;
        point_from_line3d(point,&delta,-.12f*.32808399f,&ray_start);
        vector_from_points3d(&ray_start,&unit->object.bounding_sphere_center,&delta);
        if(!collision_test_vector(_collision_test_for_line_of_sight_flags|FLAG(_collision_test_back_facing_surfaces_bit),&ray_start,&delta,player_unit,&hit) ||
           hit.type!=_collision_result_object || hit.object_index!=it.index) continue;
        contact=hit.point;node=hit.node_index;
        vector_from_points3d(point,&contact,&delta);
        if(magnitude3d(&delta)>.12f*.32808399f) continue;
        vector_from_points3d(camera,&contact,&delta);
        if(collision_test_vector(_collision_test_for_line_of_sight_flags,camera,&delta,player_unit,&hit) &&
           !(hit.type==_collision_result_object&&hit.object_index==it.index)) continue;
        if(!vr_articulated_native_capture(it.index,&capture) || node<=0 || node>=capture.body.count) continue;
        if(existing&&existing->held[1-hand]&&existing->node[1-hand]==node) continue;
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
    reset_one();
    /* Before-save/cancellation occurs while IDs are valid. No persistent AI
     * flag was altered; regenerate a native pose before serialization. */
    if(index!=NONE && object_try_and_get_and_verify_type(index,_object_mask_biped))
        object_compute_node_matrices(index);
}
void vr_npc_interaction_reset(void)
{
    for(int n=0;n<NPC_POOL_SIZE;++n) {npc_current=&npc_pool[n];reset_one();}
    memset(remote_pool,0,sizeof(remote_pool));local_edges[0]=local_edges[1]=1;
    memset(species_cache,0,sizeof(species_cache));
}
void vr_npc_interaction_cancel(void)
{
    for(int n=0;n<NPC_POOL_SIZE;++n) {npc_current=&npc_pool[n];cancel_one();}
    memset(remote_pool,0,sizeof(remote_pool));local_edges[0]=local_edges[1]=1;
}
static void release(int hand,int throwing)
{
    int was_held=npc.held[hand];
    npc.held[hand]=0;if(!npc.is_remote) vr_interaction_release(hand,VR_INTERACTION_NPC);
    if(npc.active && npc.started && npc.held[0]+npc.held[1]<npc.minimum_hands) {
        npc.held[1-hand]=0;if(!npc.is_remote) vr_interaction_release(1-hand,VR_INTERACTION_NPC);
    }
    if(npc.active && !npc.held[0] && !npc.held[1] && !npc.recovery) {
        if(!npc.started) {cancel_one();return;}
        npc.settling=1;
        if(throwing && was_held && npc.started) {
            real_vector3d velocity=npc.velocity[hand];
            if(vr_world_limit(velocity.n,.24f*interaction_units())) {
                struct unit_datum *u=eligible(npc.index);
                if(u) u->object.translational_velocity=velocity;
                for(int n=0;n<npc.rig.body.count;++n) for(int k=0;k<3;++k)
                    npc.rig.body.nodes[n].previous[k]=npc.rig.body.nodes[n].position[k]-velocity.n[k];
            }
        }
    }
}
static int owns(long index)
{
    int found=0;
    for(int n=0;n<NPC_POOL_SIZE;++n) if(npc_pool[n].active&&npc_pool[n].index==index) {npc_current=&npc_pool[n];found=1;break;}
    if(!found) return FALSE;
    if(!authority() || (!npc.is_remote&&!config_boolean("vr.npc_interaction")) || !eligible(index)) {
        cancel_one();return FALSE;
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
    if(!found || !eligible(npc.index)) return FALSE;
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
        npc_current=&npc_pool[n];if(!eligible(npc.index)) return FALSE;
        surface_offset(hand,&offset);*object=npc.index;
        for(int k=0;k<3;++k) point[k]=npc.rig.body.nodes[npc.node[hand]].position[k]+offset.n[k];
        return TRUE;
    }
    return FALSE;
}
void vr_npc_interaction_controls(long index)
{
    struct unit_datum *u;
    if(!owns(index) || !npc.started) return;
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
    for(h=0;h<2;++h) if(npc.held[h]) {
        real_vector3d offset;
        surface_offset(h,&offset);
        /* The initial root-to-grab anchor is independent of the solver's
         * current pinned node. Otherwise pinning consumes the error and the
         * root never follows a lift. Only native capsule accepts this move. */
        for(k=0;k<3;++k) error.n[k]+=npc.target[h].n[k]-offset.n[k]-npc.root_anchor[h].n[k]-unit_get(index)->object.position.n[k];
        ++count;
    }
    if(count<npc.minimum_hands) return;
    for(k=0;k<3;++k) error.n[k]/=count;
    if(vr_world_spring(error.n,velocity,npc.mobility,count,interaction_units(),global_gravity,result.n))
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
       !vr_controller(&buttons,triggers,thumbs) || !vr_aiming())) ||
       !u || u->object.parent_object_index!=NONE || TEST_FLAG(u->object.damage_flags,_object_dead_bit) ||
       cinematic_in_progress() || (!use_remote&&director_inhibited_input(local)) || !(units>0)) {
        cancel_one();return;
    }
    if(tick==npc.tick && player==npc.player) return;
    if(tick<npc.tick || tick>npc.tick+1 || player!=npc.player) {
        cancel_one();
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
        real_vector3d forward,up,delta;
        pressed=grip&&!edges[h];edges[h]=grip;
        if(use_remote) point=remote.point[h];
        if((use_remote&&!remote.seen[h]) || (!use_remote&&((h==vr_weapon_hand()&&!vr_hand_empty()) || !vr_hand_world(h,camera.n,point.n,forward.n,up.n)))) {
            release(h,FALSE);npc.sample[h]=0;continue;
        }
        if(npc.sample[h]) {
            vector_from_points3d(&npc.previous[h],&point,&delta);
            if(magnitude3d(&delta)>0.45f*units) {release(h,FALSE);npc.sample[h]=0;continue;}
            for(int k=0;k<3;++k) npc.velocity[h].n[k]=npc.velocity[h].n[k]*.55f+delta.n[k]*.45f;
        }
        npc.target[h]=npc.previous[h]=point;npc.sample[h]=1;
        if(npc.held[h]) {
            real_vector3d offset;
            surface_offset(h,&offset);
            for(int k=0;k<3;++k) delta.n[k]=npc.rig.body.nodes[npc.node[h]].position[k]+offset.n[k]-point.n[k];
            if(magnitude3d(&delta)>.65f*units) {release(h,FALSE);continue;}
        }
        if(npc.held[h] && (!grip || (!use_remote&&vr_interaction_owner(h)!=VR_INTERACTION_NPC))) {
            release(h,!grip&&(use_remote||vr_interaction_owner(h)==VR_INTERACTION_NPC));continue;
        }
        if(!pressed || npc.held[h] || npc.recovery || (!use_remote&&vr_interaction_owner(h)!=VR_INTERACTION_NONE)) continue;
        {
            struct object_iterator it;
            struct unit_datum *candidate;
            struct collision_result hit;
            int budget=0;
            object_iterator_new(&it,_object_mask_biped,0);
            while((candidate=object_iterator_next(&it))!=NULL) {
                int node;
                real_point3d ray_start;
                struct npc_state *existing=state_for_object(it.index),*destination;
                if((npc.active&&npc.minimum_hands>1&&npc.index!=it.index) ||
                   (existing&&existing!=npc_current&&(existing->held[0]||existing->held[1])&&
                    !(existing->is_remote==use_remote&&existing->player==player)) ||
                   (use_remote&&remote.candidate[h]!=it.index) || !eligible(it.index)) continue;
                destination=existing?existing:(!npc.active?npc_current:free_state());
                if(!destination) continue;
                vector_from_points3d(&point,&candidate->object.bounding_sphere_center,&delta);
                if(magnitude3d(&delta)>candidate->object.bounding_sphere_radius+.12f*units) continue;
                if(++budget>16) break;
                if(normalize3d(&delta)<.00001f) continue;
                point_from_line3d(&point,&delta,-.12f*units,&ray_start);
                vector_from_points3d(&ray_start,&candidate->object.bounding_sphere_center,&delta);
                if(!collision_test_vector(_collision_test_for_line_of_sight_flags|FLAG(_collision_test_back_facing_surfaces_bit),&ray_start,&delta,unit,&hit) ||
                   hit.type!=_collision_result_object || hit.object_index!=it.index) continue;
                vector_from_points3d(&point,&hit.point,&delta);
                if(magnitude3d(&delta)>.12f*units) continue;
                node=hit.node_index;
                real_point3d contact=hit.point;
                vector_from_points3d(&camera,&contact,&delta);
                if(collision_test_vector(_collision_test_for_line_of_sight_flags,&camera,&delta,unit,&hit) &&
                   !(hit.type==_collision_result_object && hit.object_index==it.index)) continue;
                if(!existing && !vr_articulated_native_capture(it.index,&destination->rig)) continue;
                if(node<=0 || node>=destination->rig.body.count || (destination->held[1-h]&&destination->node[1-h]==node)) continue;
                if(!use_remote&&!vr_interaction_claim(h,VR_INTERACTION_NPC)) break;
                {
                    real_vector3d velocity=npc.velocity[h];
                    npc_current=destination;npc.player=player;npc.is_remote=use_remote;npc.tick=tick;
                    npc.target[h]=npc.previous[h]=point;npc.velocity[h]=velocity;npc.sample[h]=1;npc.recovery=0;
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
                species((short)npc.species_type,&npc.minimum_hands,&npc.mobility);
                npc.settling=0;
                if(npc.held[0]+npc.held[1]>=npc.minimum_hands) npc.started=1;
                {
                    real_matrix4x3 inverse;
                    for(int k=0;k<3;++k) {
                        delta.n[k]=contact.n[k]-npc.rig.body.nodes[node].position[k];
                        npc.root_anchor[h].n[k]=npc.rig.body.nodes[node].position[k]-candidate->object.position.n[k];
                    }
                    matrix4x3_inverse(&npc.rig.captured[node],&inverse);
                    matrix4x3_transform_vector(&inverse,&delta,&npc.offset[h]);
                }
                platform_log("VR NPC: grabbed actor=%08lx species=%d hand=%d node=%d requires=%d",it.index,
                    npc.species_type,h,node,npc.minimum_hands);
                if(!use_remote) vr_haptic(h,.25f,.035f);break;
            }
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
    int count=0,n,k;
    unsigned long started;
    if(!owns(index)) return;
    started=system_milliseconds();
    {
        struct player_datum *owner=player_try_and_get(npc.player);
        if(owner) vr_interaction_impact_track(index,owner->unit_index,npc.mobility,interaction_units());
    }
    if(TEST_FLAG(unit_get(index)->object.damage_flags,_object_dead_bit)) {npc.getting_up=0;npc.recovery=0;}
    npc.rig.impact_enabled=npc.started&&!npc.recovery;
    npc.rig.impact_units=interaction_units();
    u=unit_get(index);native=object_get_node_matrices(index);
    if(!native || npc.rig.body.count>u->object.node_matrices.size/(long)sizeof(*native)) {cancel_one();return;}
    /* Translate by accepted native root motion. Ordinary NPCs already use a
     * zero-height root sphere (biped_get_physics_pill); every articulated node,
     * including the rig root, remains free and swept against world geometry. */
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
        if(!vr_articulated_recovery(&npc.rig.body,targets,1.0f/npc.recovery,vr_articulated_native_sweep,&npc.rig)) {cancel_one();return;}
        for(n=0;n<npc.rig.body.count;++n) {
            real t=1.0f/npc.recovery;
            real_matrix4x3 *m=&npc.rig.captured[n];
            vectors_interpolate(&m->forward,&native[n].forward,t,&m->forward);
            vectors_interpolate(&m->up,&native[n].up,t,&m->up);
            normalize3d(&m->forward);cross_product3d(&m->up,&m->forward,&m->left);normalize3d(&m->left);
            cross_product3d(&m->forward,&m->left,&m->up);
            memcpy(m->position.n,npc.rig.body.nodes[n].position,sizeof(m->position.n));
            if(!valid_real_matrix4x3(m)) {cancel_one();return;}
        }
        if(npc.recovery==1) {
            int clear=1;
            for(n=0;n<npc.rig.body.count;++n) {
                real_vector3d difference;
                vector_from_points3d(&native[n].position,&npc.rig.captured[n].position,&difference);
                if(magnitude3d(&difference)>.005f || collision_test_sphere(&native[n].position,npc.rig.body.nodes[n].radius,index)) {clear=0;break;}
            }
            if(clear) {cancel_one();return;}
        } else --npc.recovery;
    } else {
        for(n=0;n<2;++n) if(npc.held[n]) {
            real_vector3d offset;
            surface_offset(n,&offset);
            pins[count].node=npc.node[n];
            for(k=0;k<3;++k) pins[count].position[k]=npc.target[n].n[k]-offset.n[k];
            if(!vr_articulated_native_sweep(&npc.rig,npc.rig.body.nodes[npc.node[n]].position,
                    npc.rig.body.nodes[npc.node[n]].radius,pins[count].position)) {cancel_one();return;}
            ++count;
        }
        if(!vr_articulated_native_step(&npc.rig,1.f/30.f,global_gravity*900.f,pins,count)) {cancel_one();return;}
        if(npc.settling) {
            real maximum=0;
            for(n=0;n<npc.rig.body.count;++n) {
                real_vector3d motion;
                for(k=0;k<3;++k) motion.n[k]=npc.rig.body.nodes[n].position[k]-npc.rig.body.nodes[n].previous[k];
                maximum=MAX(maximum,magnitude3d(&motion));
            }
            npc.settling=MIN(npc.settling+1,300);
            if(npc.settling>=30 && maximum<.02f*interaction_units()) {
                if(TEST_FLAG(u->object.damage_flags,_object_dead_bit)) {
                    /* A corpse never enters live get-up or AI recovery. Give
                     * the actual settled palette back to native dead-body
                     * relaxation when its root has reached rest. */
                    if(TEST_FLAG(u->object.flags,_object_at_rest_bit)) {
                        for(n=0;n<npc.rig.body.count;++n) native[n]=npc.rig.captured[n];
                        reset_one();biped_start_limp_body_physics(index);return;
                    }
                } else {
                int clear=1;
                for(n=0;n<npc.rig.body.count;++n) if(collision_test_sphere(&native[n].position,npc.rig.body.nodes[n].radius,index)) {clear=0;break;}
                if(clear) {
                    real_vector3d body_forward;
                    matrix4x3_transform_vector(&npc.rig.captured[npc.torso_node],&npc.body_forward_local,&body_forward);
                    npc.getting_up=unit_interaction_recover(index,body_forward.k<0);
                    npc.settling=0;npc.recovery=18;
                    platform_log("VR NPC: recovery object=%08lx front=%d authored=%d",index,body_forward.k<0,npc.getting_up);
                }
                }
            }
        }
    }
    for(n=0;n<npc.rig.body.count;++n) native[n]=npc.rig.captured[n];
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
