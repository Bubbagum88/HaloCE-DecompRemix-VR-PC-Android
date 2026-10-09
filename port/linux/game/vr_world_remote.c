/* Negotiated co-op grip input. The host runs native item physics; clients
 * supply tracked intent, never object transforms or damage. */
#include "cseries.h"
#include "game/game.h"
#include "game/players.h"
#include "items/items.h"
#include "objects/object_definitions.h"
#include "units/units.h"
#include "physics/collisions.h"
#include "physics/collision_models.h"
#include "physics/collision_bsp.h"
#include "physics/physics.h"
#include "network_interaction.h"
#include "vr_world_interaction.h"
#include "vr_world_math.h"
#include "vr_world_props.h"
#include "vr_interaction_impact.h"
#include "../src/port_config.h"
#include <float.h>
#include <string.h>
static struct remote_grip {
    boolean active;
    long player, unit, object, tick;
    int hand;
    real_point3d local, target, previous;
    real_vector3d velocity, forward, up, local_forward, local_up;
} remote[256];
static real units(void)
{
    real u=config_real("vr.world_scale");
    return isfinite(u) && u>0 && u<100 ? u : 1.f/3.048f;
}
static void local_vector(real_vector3d const *f,real_vector3d const *u,
    real_vector3d const *v,real_vector3d *out)
{
    real_vector3d left; cross_product3d(u,f,&left);
    out->i=dot_product3d(f,v);out->j=dot_product3d(&left,v);out->k=dot_product3d(u,v);
}
static void world_vector(real_vector3d const *f,real_vector3d const *u,
    real_vector3d const *v,real_vector3d *out)
{
    real_vector3d left; int n; cross_product3d(u,f,&left);
    for(n=0;n<3;++n) out->n[n]=f->n[n]*v->i+left.n[n]*v->j+u->n[n]*v->k;
}
void vr_world_interaction_remote_cancel(long player,int hand)
{
    int i; for(i=0;i<256;++i) if(remote[i].active && remote[i].player==player &&
        (hand<0 || remote[i].hand==hand)) memset(&remote[i],0,sizeof(remote[i]));
}
void vr_world_interaction_remote_reset(void) { memset(remote,0,sizeof(remote)); }
static boolean remote_owner_valid(long player_index,long unit_index)
{
    struct player_datum *player=player_try_and_get(player_index);
    struct unit_datum *unit=unit_try_and_get(unit_index);
    return player && player->unit_index==unit_index && unit &&
        unit->object.parent_object_index==NONE && !TEST_FLAG(unit->object.damage_flags,_object_dead_bit);
}
static long find_candidate(struct network_interaction_hand const *request)
{
    struct object_iterator it; struct object_datum *item;
    real contact_radius=(real)vr_world_hand_contact_radius((float)config_real("vr.interaction_reach"),(float)units());
    real best=FLT_MAX; long result=NONE; int count=0;
    real_vector3d stationary={0};
    object_iterator_new(&it,_object_mask_weapon|_object_mask_equipment|_object_mask_scenery,0);
    while((item=object_iterator_next(&it))!=NULL) {
        real_vector3d delta; real distance;
        struct collision_model_instance model;
        struct collision_model_test_pill_result model_hit;
        if(!vr_world_object_get(it.index)) continue;
        vector_from_points3d(&request->position,&item->object.bounding_sphere_center,&delta);
        distance=magnitude3d(&delta);
        if(distance>item->object.bounding_sphere_radius+contact_radius || distance>=best) continue;
        if(++count>32) break;
        /* The sphere is broad phase only. Host acquisition requires overlap
         * between the client's tracked palm volume and this native model. */
        if(!collision_model_instance_new(&model,it.index) ||
            !collision_model_test_pill(&model,&request->position,&stationary,contact_radius,&model_hit)) continue;
        best=distance;result=it.index;
    }
    return result;
}
boolean vr_world_interaction_remote(struct network_interaction_hand const *request)
{
    struct network_interaction_hand resolved;
    int i, slot=-1, other=-1;
    struct object_datum *item;
    struct remote_grip *r;
    real_vector3d vector;
    real_point3d camera, contact;
    struct collision_result hit;
    real u=units();
    real contact_radius=(real)vr_world_hand_contact_radius((float)config_real("vr.interaction_reach"),(float)u);
    if(!request || request->hand>1 || !network_interaction_host_ready()) return FALSE;
    if(!remote_owner_valid(request->player,request->unit)) {
        vr_world_interaction_remote_cancel(request->player,request->hand);return FALSE;
    }
    for(i=0;i<256;++i) {
        if(remote[i].active && remote[i].player==request->player && remote[i].hand==request->hand) {slot=i;break;}
        if(!remote[i].active) slot=i;
    }
    if(slot<0) return FALSE;
    r=&remote[slot];
    resolved=*request;
    if(resolved.object==NONE) resolved.object=r->active?r->object:find_candidate(request);
    request=&resolved;
    if(!request->held) {
        if(r->active && (item=vr_world_object_get(r->object))) {
            for(i=0;i<256;++i) if(i!=slot && remote[i].active && remote[i].object==r->object) other=i;
            if(other<0 && vr_world_limit(r->velocity.n,u*.24f))
                vr_world_object_velocity(r->object,&r->velocity,&item->object.angular_velocity);
        }
        memset(r,0,sizeof(*r));return TRUE;
    }
    if(r->active) {
        if(r->object!=request->object || !(item=vr_world_object_get(r->object))) {memset(r,0,sizeof(*r));return FALSE;}
        vector_from_points3d(&r->previous,&request->position,&vector);
        if(magnitude3d(&vector)>.45f*u) {memset(r,0,sizeof(*r));return FALSE;}
        if(game_time_get()>r->tick) for(i=0;i<3;++i)
            r->velocity.n[i]=r->velocity.n[i]*.55f+vector.n[i]*.45f/(game_time_get()-r->tick);
    } else {
        struct collision_model_instance model;
        struct collision_model_test_pill_result model_hit;
        real_vector3d stationary={0};
        if(!request->pressed) return FALSE;
        if(!(item=vr_world_object_get(request->object))) return FALSE;
        for(i=0;i<256;++i) if(remote[i].active && remote[i].object==request->object && remote[i].player!=request->player) return FALSE;
        if(vr_world_interaction_object(0)==request->object || vr_world_interaction_object(1)==request->object) return FALSE;
        vector_from_points3d(&request->position,&item->object.bounding_sphere_center,&vector);
        if(magnitude3d(&vector)>item->object.bounding_sphere_radius+contact_radius ||
            !collision_model_instance_new(&model,request->object) ||
            !collision_model_test_pill(&model,&request->position,&stationary,contact_radius,&model_hit)) return FALSE;
        /* The palm is the contact anchor. LOS below only prevents gripping
         * through an intervening wall; a ray never selects the object. */
        contact=request->position;
        unit_get_camera_position(request->unit,&camera);vector_from_points3d(&camera,&contact,&vector);
        if(collision_test_vector(_collision_test_for_line_of_sight_flags,&camera,&vector,request->unit,&hit) &&
            !(hit.type==_collision_result_object && hit.object_index==request->object)) return FALSE;
        memset(r,0,sizeof(*r));r->active=TRUE;r->object=request->object;r->player=request->player;
        r->unit=request->unit;r->hand=request->hand;
        vector_from_points3d(&item->object.position,&contact,&vector);
        local_vector(&item->object.forward,&item->object.up,&vector,(real_vector3d*)&r->local);
        local_vector(&request->forward,&request->up,&item->object.forward,&r->local_forward);
        local_vector(&request->forward,&request->up,&item->object.up,&r->local_up);
    }
    r->previous=r->target=request->position;r->forward=request->forward;r->up=request->up;r->tick=game_time_get();
    return TRUE;
}
void vr_world_interaction_remote_tick(void)
{
    int i,j,n; real u=units();
    if(!network_interaction_host_ready()) {vr_world_interaction_remote_reset();return;}
    for(i=0;i<256;++i) if(remote[i].active) {
        struct remote_grip *r=&remote[i];
        struct object_datum *item=vr_world_object_get(r->object);
        real_vector3d offset,error={0},velocity,angular,second,forward,up;
        int count=0;
        if(!item || !remote_owner_valid(r->player,r->unit) || game_time_get()<r->tick || game_time_get()-r->tick>9) {memset(r,0,sizeof(*r));continue;}
        for(j=0;j<i;++j) if(remote[j].active && remote[j].object==r->object) break;
        if(j<i) continue;
        for(j=i;j<256;++j) if(remote[j].active && remote[j].object==r->object) {
            world_vector(&item->object.forward,&item->object.up,(real_vector3d*)&remote[j].local,&offset);
            for(n=0;n<3;++n) error.n[n]+=remote[j].target.n[n]-item->object.position.n[n]-offset.n[n];
            ++count;
        }
        scale_vector3d(&error,1.f/count,&error);
        if(magnitude3d(&error)>.65f*u) {vr_world_interaction_remote_cancel(r->player,-1);continue;}
        real mobility=vr_world_object_mobility(r->object);
        if(!vr_world_spring(error.n,item->object.translational_velocity.n,mobility,count,u,global_gravity,velocity.n)) continue;
        world_vector(&r->forward,&r->up,&r->local_forward,&forward);
        world_vector(&r->forward,&r->up,&r->local_up,&up);
        cross_product3d(&item->object.forward,&forward,&angular);cross_product3d(&item->object.up,&up,&second);
        add_vectors3d(&angular,&second,&angular);scale_vector3d(&angular,.12f,&angular);
        if(vr_world_limit(angular.n,.15f)) vr_world_object_velocity(r->object,&velocity,&angular);
        vr_interaction_impact_track(r->object,r->unit,mobility,u);
    }
}

boolean vr_world_interaction_remote_owned(long object)
{ int i; for(i=0;i<256;++i) if(remote[i].active && remote[i].object==object) return TRUE; return FALSE; }

boolean vr_world_interaction_remote_contact(long player,int hand,long *object,float point[3])
{
    int i,n; struct object_datum *item; real_vector3d offset;
    if(!object||!point)return FALSE;
    for(i=0;i<256;++i)if(remote[i].active&&remote[i].player==player&&remote[i].hand==hand){
        item=vr_world_object_get(remote[i].object);
        if(!item)return FALSE;
        *object=remote[i].object;
        world_vector(&item->object.forward,&item->object.up,(real_vector3d*)&remote[i].local,&offset);
        for(n=0;n<3;++n)point[n]=item->object.position.n[n]+offset.n[n];
        return TRUE;
    }
    return FALSE;
}
