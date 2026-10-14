/* Test67: physical projectile deflection. No target search, damage override,
 * tag-name list, replicated state, allocation or projectile respawn. */
#ifdef HALO_VR
#include "cseries.h"
#include "game/game.h"
#include "items/projectiles.h"
#include "items/projectile_definitions.h"
#include "units/units.h"
#include "halo_vr.h"
#include "vr_extra_interaction.h"
#include "vr_manual_reload.h"
#include "vr_projectile_parry.h"
#include "../src/vr.h"
#include "../src/port_config.h"

static struct {
    long unit, tick;
    double time;
    int valid;
    real_point3d camera;
    struct { int valid, strike; long weapon; real speed; real_point3d previous, point;
        real_vector3d direction; } hand[2];
} parry;
/* Datum slot plus full salted identifier prevents one projectile repeatedly
 * meeting the same fist. Recenter resets hands, never this lifetime record. */
static long parried[MAXIMUM_OBJECTS_PER_MAP];
static unsigned char parried_valid[MAXIMUM_OBJECTS_PER_MAP];

void vr_projectile_parry_reset(void)
{
    memset(&parry,0,sizeof parry);
    parry.unit=parry.tick=NONE;
}
void vr_projectile_parry_new_map(void)
{
    vr_projectile_parry_reset();
    memset(parried_valid,0,sizeof parried_valid);
}
void vr_projectile_parry_forget(long projectile)
{
    unsigned slot=(unsigned)projectile&0xffffu;
    if(slot<MAXIMUM_OBJECTS_PER_MAP)parried_valid[slot]=0;
}

/* Fixed weapon mode reports !vr_hand_empty even when the native inventory
 * has no selected weapon. A gun gesture requires the actual salted handle;
 * dropping, holstering, switching or handing it over cancels that stroke. */
static long parry_weapon(long unit,int hand)
{
    struct unit_datum *owner;
    struct object_datum *weapon;
    long index;
    if(hand!=vr_weapon_hand()||vr_hand_empty())return NONE;
    owner=unit_try_and_get(unit);
    if(!owner||owner->unit.current_weapon_index<0||
       owner->unit.current_weapon_index>=MAXIMUM_WEAPONS_PER_UNIT)return NONE;
    index=unit_inventory_get_weapon(unit,owner->unit.current_weapon_index);
    weapon=index!=NONE?object_try_and_get(index):NULL;
    return weapon&&weapon->object.type==_object_type_weapon?index:NONE;
}

void vr_projectile_parry_tick(long unit)
{
    long owner=vr_extra_action_owner(),tick=game_time_get();
    double time=vr_pose_time(),dt=time-parry.time;
    real units=vr_units_per_metre();real_point3d camera;
    if(!config_boolean("vr.projectile_parry")||unit==NONE||unit!=owner||
       !isfinite(time)||!(isfinite(units)&&units>0&&units<10)){
        vr_projectile_parry_reset();parry.tick=tick;parry.time=time;return;
    }
    if(parry.valid&&parry.unit==unit&&parry.tick==tick)return;
    int continuous=parry.valid&&parry.unit==unit&&tick==parry.tick+1&&dt>0&&dt<=.1;
    if(!vr_render_drawn_camera(camera.n))unit_get_camera_position(unit,&camera);
    if(!valid_real_point3d(&camera)){vr_projectile_parry_reset();return;}
    for(int h=0;h<2;h++){
        real_point3d point;real_vector3d forward,up,step,motion;
        long weapon=parry_weapon(unit,h);
        int armed=weapon!=NONE;
        int tracked=vr_interaction_owner(h)==VR_INTERACTION_NONE&&
            !(h!=vr_weapon_hand()&&vr_two_handed())&&
            vr_hand_pose(h,camera.n,point.n,forward.n,up.n)&&
            valid_real_point3d(&point)&&valid_real_vector3d(&forward);
        parry.hand[h].strike=0;
        if(!tracked){parry.hand[h].valid=0;continue;}
        /* Prefer the rendered palm; current calibrated tracked wrist plus
         * 3 cm is the established physical-grenade palm fallback. */
        if(!vr_render_palm_point(h,unit,point.n))
            point_from_line3d(&point,&forward,.03f*units,&point);
        if(!valid_real_point3d(&point)){parry.hand[h].valid=0;continue;}
        vector_from_points3d(&parry.hand[h].point,&point,&step);
        for(int k=0;k<3;k++)motion.n[k]=step.n[k]-(camera.n[k]-parry.camera.n[k]);
        real travel=magnitude3d(&step),stroke=magnitude3d(&motion),speed=vr_hand_speed(h);
        if(continuous&&parry.hand[h].valid&&isfinite(travel)&&
           travel<=.5f*units&&isfinite(stroke)&&stroke/(units*(real)dt)>=1.2f&&
           speed>=1.2f&&isfinite(speed)&&speed<=15.0f&&stroke/(units*(real)dt)<=15.0f&&
           parry.hand[h].weapon==weapon&&
           (armed||(vr_interaction_grip(h,NULL,NULL)&&vr_interaction_trigger(h)))){
            parry.hand[h].previous=parry.hand[h].point;
            parry.hand[h].direction=motion;
            normalize3d(&parry.hand[h].direction);
            parry.hand[h].speed=stroke/(real)dt/TICKS_PER_SECOND;
            parry.hand[h].strike=1;
        }else parry.hand[h].previous=point;
        parry.hand[h].point=point;parry.hand[h].valid=1;parry.hand[h].weapon=weapon;
    }
    parry.valid=1;parry.unit=unit;parry.tick=tick;parry.time=time;parry.camera=camera;
}

/* Both paths share one tick interval, so a fast bullet crossing the hand
 * between its endpoints is caught without turning the fist into a ray. */
static boolean parry_contact(real_point3d const *start,real_point3d const *end,
    real_point3d const *hand_start,real_point3d const *hand_end,real radius,real *at)
{
    real_vector3d relative,step;
    for(int k=0;k<3;k++){
        relative.n[k]=start->n[k]-hand_start->n[k];
        step.n[k]=end->n[k]-start->n[k]-(hand_end->n[k]-hand_start->n[k]);
    }
    double a=dot_product3d(&step,&step),b=dot_product3d(&relative,&step);
    double c=dot_product3d(&relative,&relative)-(double)radius*radius;
    if(!isfinite(a)||!isfinite(b)||!isfinite(c))return FALSE;
    if(c<=0){*at=0;return TRUE;}
    if(a<1e-12||b>=0)return FALSE;
    double discriminant=b*b-a*c;
    if(discriminant<0||!isfinite(discriminant))return FALSE;
    double t=(-b-sqrt(discriminant))/a;
    if(!isfinite(t)||t<0||t>1)return FALSE;
    *at=(real)t;return TRUE;
}

boolean vr_projectile_parry_try(long index,real_point3d const *end,
    real_vector3d const *velocity,real solid_fraction,real tick_remaining,real *fraction)
{
    struct object_datum *object;
    struct projectile_datum *projectile;
    struct projectile_definition const *definition;
    struct unit_datum *owner;
    unsigned slot=(unsigned)index&0xffffu;
    long unit;
    real units=vr_units_per_metre(),best=1.0f;int hand=-1;
    if(!config_boolean("vr.projectile_parry")){
        vr_projectile_parry_reset();return FALSE;
    }
    /* The game tick samples two hands once. Most projectile sweeps miss them;
     * perform the live player/host authorization again only at real contact. */
    if(parry.tick!=game_time_get())
        vr_projectile_parry_tick(vr_extra_action_owner());
    unit=parry.unit;
    double age=vr_pose_time()-parry.time;
    if(!parry.valid||parry.unit!=unit||parry.tick!=game_time_get()||
       !isfinite(age)||age<0||age>.1||!isfinite(units)||units<=0||units>=10||
       !end||!velocity||!fraction||!valid_real_point3d(end)||!valid_real_vector3d(velocity)||
       !isfinite(solid_fraction)||solid_fraction<0||solid_fraction>1||
       !isfinite(tick_remaining)||tick_remaining<=0||tick_remaining>1||
       slot>=MAXIMUM_OBJECTS_PER_MAP||(parried_valid[slot]&&parried[slot]==index))return FALSE;
    object=object_try_and_get(index);
    owner=unit_try_and_get(unit);
    if(!object||object->object.type!=_object_type_projectile||!owner)return FALSE;
    projectile=(struct projectile_datum *)object;
    if(projectile->projectile.action!=_projectile_action_none||
       projectile->object.parent_object_index!=NONE||
       TEST_FLAG(projectile->object.flags,_object_at_rest_bit)||
       TEST_FLAG(projectile->projectile.flags,_projectile_attached_bit)||
       TEST_FLAG(projectile->projectile.flags,_projectile_stopped_after_collision_bit)||
       TEST_FLAG(projectile->projectile.flags,_projectile_already_super_exploded_bit)||
       TEST_FLAG(projectile->projectile.flags,_projectile_will_super_explode_bit)||
       !valid_real_point3d(&projectile->object.position)||
       !valid_real_vector3d(&projectile->object.translational_velocity)||
       !valid_real_vector3d(&projectile->object.up)||
       !isfinite(projectile->projectile.detonation_timer)||projectile->projectile.detonation_timer>=1||
       !isfinite(projectile->projectile.arming_time)||
       !isfinite(projectile->projectile.odometer))return FALSE;
    definition=projectile_definition_get(projectile->definition_index);
    real projectile_radius=definition->projectile.collision_radius;
    real palm=(real)config_real("vr.interaction_reach");
    if(!isfinite(projectile_radius)||projectile_radius<0||!isfinite(palm))return FALSE;
    real radius=PIN(palm,.02f,.08f)*units+MIN(projectile_radius,.12f*units);
    real speed=magnitude3d(velocity);
    if(!isfinite(speed)||speed<.001f*units)return FALSE;
    for(int h=0;h<2;h++)if(parry.hand[h].valid&&parry.hand[h].strike){
        real_point3d from;real at;
        long weapon=parry_weapon(unit,h);
        int armed=weapon!=NONE;
        for(int k=0;k<3;k++)from.n[k]=parry.hand[h].point.n[k]-
            (parry.hand[h].point.n[k]-parry.hand[h].previous.n[k])*tick_remaining;
        /* A reserved/regripped hand cannot act using its earlier sample. */
        if(vr_interaction_owner(h)!=VR_INTERACTION_NONE||
           (h!=vr_weapon_hand()&&vr_two_handed())||
           parry.hand[h].weapon!=weapon||
           (!armed&&(!vr_interaction_grip(h,NULL,NULL)||!vr_interaction_trigger(h))))continue;
        if(parry_contact(&projectile->object.position,end,&from,&parry.hand[h].point,radius,&at)&&
           at<solid_fraction&&at<best){best=at;hand=h;}
    }
    if(hand<0)return FALSE;
    if(unit!=vr_extra_action_owner()){
        vr_projectile_parry_reset();return FALSE;
    }
    real_vector3d reflected,at_contact;real_point3d contact;
    /* The player's actual stroke aims the returned projectile. Preserve its
     * speed for fast rounds; slow airborne grenades receive only the measured
     * fist speed. No target lookup, assisted steering or range/fuse reset. */
    for(int k=0;k<3;k++)at_contact.n[k]=projectile->object.translational_velocity.n[k]+
        (velocity->n[k]-projectile->object.translational_velocity.n[k])*best;
    speed=magnitude3d(&at_contact);
    if(!isfinite(speed))return FALSE;
    speed=MAX(speed,parry.hand[hand].speed);
    scale_vector3d(&parry.hand[hand].direction,speed,&reflected);
    if(!valid_real_vector3d(&reflected))return FALSE;
    for(int k=0;k<3;k++)contact.n[k]=projectile->object.position.n[k]+
        (end->n[k]-projectile->object.position.n[k])*best;
    projectile->object.translational_velocity=reflected;
    projectile->object.forward=parry.hand[hand].direction;
    real_vector3d left;
    cross_product3d(&projectile->object.up,&projectile->object.forward,&left);
    if(normalize3d(cross_product3d(&projectile->object.forward,&left,&projectile->object.up))==0)
        normalize3d(perpendicular3d(&projectile->object.forward,&projectile->object.up));
    projectile->object.owner_object_index=unit;
    projectile->object.owner_player_index=owner->unit.player_index;
    projectile->object.owner_team_index=owner->object.owner_team_index;
    projectile->projectile.ignore_object_index=unit;
    projectile_set_target_object_index(index,NONE);
    parried[slot]=index;parried_valid[slot]=1;
    *fraction=best;
    vr_extra_projectile_feedback(hand,&contact);
    return TRUE;
}
#endif
