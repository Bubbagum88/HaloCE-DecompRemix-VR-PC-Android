/* Test67: physical projectile deflection. No target search, damage override,
 * tag-name list, replicated state, allocation or projectile respawn.
 *
 * Test72 (the owner: "Shot Deflection does not appear to work"; "it should
 * also work if im just holding a gun against the projectiles. i shouldnt have
 * to do a motion for that"). Found:
 * - a held gun counted only while swung at 1.2 m/s or more: a gun held up in
 *   a projectile's path never deflected it. Now the gun is a solid body
 *   (BLOCK): from the grip along its aim, as long as the weapon's model,
 *   with no motion needed; a projectile meeting it glances off its surface.
 *   A gun swung (1.2 m/s) still bats the projectile along the stroke.
 * - an empty hand had to hold the grip AND the trigger; a closed hand (the
 *   grip, as FIST COMBAT's fist) now suffices, swung at 1.2 m/s.
 * - every projectile was treated alike. Each is now sorted by its tag's own
 *   data (impact damage or a detonation, speed, fuse, gravity, range: SPV1's
 *   names are hidden, so never by name): BOLTS (plasma, needles, the Ghost's,
 *   the Banshee's, the Shade's) deflect by fist, swing and block; BULLETS
 *   (pellets, bullets, sniper rounds) only off a gun, never a bare fist;
 *   GRENADES are batted by fist or swing and bounce off a held gun; light
 *   EXPLOSIVES (rockets, fuel rods) only by a hard deliberate swing (2.5
 *   m/s), never by holding a gun into them (they burst on it, as natively);
 *   heavy shells (the Scorpion's, the Wraith's mortar, beams) and short
 *   streams (flame) never.
 * - nothing was logged: deflections, and near misses with the reason they
 *   did not deflect, are now (rate-limited).
 * - feedback: a deflection is a sharp crack and a ring after it in the hand
 *   (both hands on a two-handed gun), the armour's metal sound, and the
 *   highlight where it met (vr_extra_projectile_feedback).
 * DEFLECT AID adds to the contact (0, 3 or 6 cm); DEFLECT FORCE scales
 * the returned speed (0.75, 1, 1.25). */
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

void platform_log(char const *format, ...);

enum {
    DEFLECT_NEVER,
    DEFLECT_BOLT,
    DEFLECT_BULLET,
    DEFLECT_GRENADE,
    DEFLECT_EXPLOSIVE
};
static char const *const deflect_category_names[]={"never","bolt","bullet","grenade","explosive"};

enum { DEFLECT_BY_FIST, DEFLECT_BY_SWING, DEFLECT_BY_BLOCK };
static char const *const deflect_way_names[]={"fist","gun swing","gun block"};

static struct {
    long unit, tick;
    double time;
    int valid;
    real_point3d camera;
    struct { int valid, strike, gun; long weapon; real speed; real_point3d previous, point;
        real_vector3d direction; real_point3d gun_back, gun_front; } hand[2];
} parry;
/* Datum slot plus full salted identifier prevents one projectile repeatedly
 * meeting the same fist. Recenter resets hands, never this lifetime record. */
static long parried[MAXIMUM_OBJECTS_PER_MAP];
static unsigned char parried_valid[MAXIMUM_OBJECTS_PER_MAP];
static long deflect_log_tick=-1000,near_log_tick=-1000;

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
static long parry_weapon(long unit,int hand);
long vr_parry_hand_weapon(long unit,int hand)
{
    return parry_weapon(unit,hand);
}
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

/* Test72: what a projectile is, from its tag's own data (the stock maps'
 * values: tools/test_test72_deflection.py) */
static int deflect_category(struct projectile_definition const *definition)
{
    real speed=definition->projectile.initial_velocity,gravity=definition->projectile.air_gravity_scale;
    real range=definition->projectile.maximum_range;
    boolean impact=definition->projectile.impact_damage.index!=NONE;
    boolean detonates=definition->projectile.effect.index!=NONE;
    if(!isfinite(speed)||!isfinite(gravity)||!isfinite(range))return DEFLECT_NEVER;
    /* flame and cinematic effects live a few units only */
    if(range>0.0f&&range<10.0f)return DEFLECT_NEVER;
    if(definition->projectile.timer_upper_bound>0.0f&&gravity>0.0f&&!impact)return DEFLECT_GRENADE;
    if(impact)return speed>=3.0f?DEFLECT_BULLET:speed>.01f?DEFLECT_BOLT:DEFLECT_NEVER;
    if(detonates){
        if(speed>=2.0f||definition->projectile.collision_radius>=.3f)return DEFLECT_NEVER; /* shells, mortars, beams */
        return speed>.01f||gravity>0.0f?DEFLECT_EXPLOSIVE:DEFLECT_NEVER;
    }
    return DEFLECT_NEVER;
}
static boolean deflect_allowed(int category,int way,real stroke_speed)
{
    switch(category){
    case DEFLECT_BOLT:return TRUE;
    case DEFLECT_BULLET:return way!=DEFLECT_BY_FIST;
    case DEFLECT_GRENADE:return TRUE;
    case DEFLECT_EXPLOSIVE:return way!=DEFLECT_BY_BLOCK&&stroke_speed>=2.5f;
    default:return FALSE;
    }
}
static real deflect_assist(void)
{
    real v=(real)config_real("vr.deflect_assist");
    return isfinite(v)?PIN(v,0.0f,.10f):.03f;
}
static real deflect_strength(void)
{
    real v=(real)config_real("vr.deflect_strength");
    return isfinite(v)?PIN(v,.5f,1.5f):1.0f;
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
        parry.hand[h].strike=0;parry.hand[h].gun=0;
        if(!tracked){parry.hand[h].valid=0;continue;}
        /* Test72: the gun in hand is a body: from a little behind the grip
         * along the gun's aim, as long as its model (the weapon's bounds) */
        if(armed){
            real_point3d aim_at;real_vector3d aim=forward,aim_up;
            struct object_datum *gun=object_try_and_get(weapon);
            real size=gun&&isfinite(gun->object.bounding_sphere_radius)?gun->object.bounding_sphere_radius/units:.3f;
            real ahead=PIN(1.5f*size,.25f,.75f),behind=PIN(.4f*size,.06f,.25f);
            if(!(vr_weapon_view(camera.n,aim_at.n,aim.n,aim_up.n)&&valid_real_vector3d(&aim)&&normalize3d(&aim)>.0001f))
                aim=forward;
            point_from_line3d(&point,&aim,-behind*units,&parry.hand[h].gun_back);
            point_from_line3d(&point,&aim,ahead*units,&parry.hand[h].gun_front);
            parry.hand[h].gun=valid_real_point3d(&parry.hand[h].gun_back)&&valid_real_point3d(&parry.hand[h].gun_front);
        }
        /* Prefer the rendered palm; current calibrated tracked wrist plus
         * 3 cm is the established physical-grenade palm fallback. */
        if(!vr_render_palm_point(h,unit,point.n))
            point_from_line3d(&point,&forward,.03f*units,&point);
        if(!valid_real_point3d(&point)){parry.hand[h].valid=0;continue;}
        vector_from_points3d(&parry.hand[h].point,&point,&step);
        for(int k=0;k<3;k++)motion.n[k]=step.n[k]-(camera.n[k]-parry.camera.n[k]);
        real travel=magnitude3d(&step),stroke=magnitude3d(&motion),speed=vr_hand_speed(h);
        /* (Test72: a closed hand, the grip, as FIST COMBAT's fist; the
         * trigger as well was asked before) */
        if(continuous&&parry.hand[h].valid&&isfinite(travel)&&
           travel<=.5f*units&&isfinite(stroke)&&stroke/(units*(real)dt)>=1.2f&&
           speed>=1.2f&&isfinite(speed)&&speed<=15.0f&&stroke/(units*(real)dt)<=15.0f&&
           parry.hand[h].weapon==weapon&&
           (armed||vr_interaction_grip(h,NULL,NULL))){
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

/* Test72: the projectile's path (start to end) against the gun (a capsule,
 * back to front, `radius` round): where along the path it first meets it,
 * and the gun's point nearest that */
static boolean gun_contact(real_point3d const *start,real_point3d const *end,
    real_point3d const *back,real_point3d const *front,real radius,real *at,real_point3d *on_gun)
{
    real_vector3d d1,d2,r;
    real a,e,f,b,c,s,t,denominator;
    vector_from_points3d(start,end,&d1);vector_from_points3d(back,front,&d2);vector_from_points3d(back,start,&r);
    a=dot_product3d(&d1,&d1);e=dot_product3d(&d2,&d2);f=dot_product3d(&d2,&r);
    if(!(a>1e-12f)||!(e>1e-12f))return FALSE;
    c=dot_product3d(&d1,&r);b=dot_product3d(&d1,&d2);denominator=a*e-b*b;
    s=denominator>1e-12f?PIN((b*f-c*e)/denominator,0.0f,1.0f):0.0f;
    t=(b*s+f)/e;
    if(t<0.0f){t=0.0f;s=PIN(-c/a,0.0f,1.0f);}
    else if(t>1.0f){t=1.0f;s=PIN((b-c)/a,0.0f,1.0f);}
    {
        real_point3d p1,p2;real_vector3d gap;real distance;
        point_from_line3d(start,&d1,s,&p1);point_from_line3d(back,&d2,t,&p2);
        vector_from_points3d(&p2,&p1,&gap);distance=magnitude3d(&gap);
        if(!isfinite(distance)||distance>radius)return FALSE;
        /* back along the path to where its edge first touched */
        s-=sqrtf(MAX(radius*radius-distance*distance,0.0f))/sqrtf(a);
        *at=PIN(s,0.0f,1.0f);*on_gun=p2;
        return isfinite(*at);
    }
}

/* why a projectile passing a hand was not deflected, once a second */
static void deflect_near_miss(int category,char const *reason)
{
    long now=game_time_get();
    if(now-near_log_tick<TICKS_PER_SECOND)return;
    near_log_tick=now;
    platform_log("VR shot deflection: a %s met a hand, not deflected: %s",deflect_category_names[category],reason);
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
    real units=vr_units_per_metre(),best=1.0f;int hand=-1,way=DEFLECT_BY_FIST,category;
    real_point3d best_on_gun;
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
    /* (the player's own shots are never stopped by the player's own gun) */
    if(projectile->object.owner_object_index==unit)return FALSE;
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
    category=deflect_category(definition);
    if(category==DEFLECT_NEVER)return FALSE;
    real projectile_radius=definition->projectile.collision_radius;
    real palm=(real)config_real("vr.interaction_reach");
    if(!isfinite(projectile_radius)||projectile_radius<0||!isfinite(palm))return FALSE;
    real assist=deflect_assist()*units;
    real radius=PIN(palm,.02f,.08f)*units+MIN(projectile_radius,.12f*units)+assist;
    real gun_radius=.04f*units+MIN(projectile_radius,.12f*units)+assist;
    real speed=magnitude3d(velocity);
    if(!isfinite(speed)||speed<.001f*units)return FALSE;
    {
        char const *miss_reason=NULL;
        for(int h=0;h<2;h++){
            real_point3d from;real at;real_point3d on_gun;
            long weapon;int armed,this_way;
            if(!parry.hand[h].valid)continue;
            weapon=parry_weapon(unit,h);armed=weapon!=NONE;
            /* A reserved/regripped hand cannot act using its earlier sample. */
            if(vr_interaction_owner(h)!=VR_INTERACTION_NONE||
               (h!=vr_weapon_hand()&&vr_two_handed())||
               parry.hand[h].weapon!=weapon)continue;
            if(armed&&parry.hand[h].gun){
                /* the gun: swung, it bats along the stroke; held, it blocks */
                this_way=parry.hand[h].strike?DEFLECT_BY_SWING:DEFLECT_BY_BLOCK;
                if(gun_contact(&projectile->object.position,end,&parry.hand[h].gun_back,&parry.hand[h].gun_front,
                    gun_radius,&at,&on_gun)){
                    if(!deflect_allowed(category,this_way,parry.hand[h].speed*TICKS_PER_SECOND/units)){
                        miss_reason=category==DEFLECT_EXPLOSIVE?"an explosive is only batted away by a hard swing (2.5 m/s)":
                            "this kind is not deflected that way";
                        continue;
                    }
                    if(at<solid_fraction&&at<best){best=at;hand=h;way=this_way;best_on_gun=on_gun;}
                }
                continue;
            }
            if(armed)continue;
            for(int k=0;k<3;k++)from.n[k]=parry.hand[h].point.n[k]-
                (parry.hand[h].point.n[k]-parry.hand[h].previous.n[k])*tick_remaining;
            if(parry_contact(&projectile->object.position,end,&from,&parry.hand[h].point,radius,&at)){
                if(!parry.hand[h].strike){
                    miss_reason=vr_interaction_grip(h,NULL,NULL)?"the fist was not swung (1.2 m/s)":
                        "the hand was open (close it on the grip and swing)";
                    continue;
                }
                if(!deflect_allowed(category,DEFLECT_BY_FIST,parry.hand[h].speed*TICKS_PER_SECOND/units)){
                    miss_reason=category==DEFLECT_BULLET?"bullets only glance off a gun, not a bare fist":
                        "an explosive is only batted away by a hard swing (2.5 m/s)";
                    continue;
                }
                if(at<solid_fraction&&at<best){best=at;hand=h;way=DEFLECT_BY_FIST;}
            }
        }
        if(hand<0){
            if(miss_reason)deflect_near_miss(category,miss_reason);
            return FALSE;
        }
    }
    if(unit!=vr_extra_action_owner()){
        vr_projectile_parry_reset();return FALSE;
    }
    {
        real_vector3d reflected,at_contact,direction;real_point3d contact;
        real strength=deflect_strength(),incoming;
        for(int k=0;k<3;k++)at_contact.n[k]=projectile->object.translational_velocity.n[k]+
            (velocity->n[k]-projectile->object.translational_velocity.n[k])*best;
        incoming=magnitude3d(&at_contact);
        if(!isfinite(incoming))return FALSE;
        for(int c=0;c<3;c++)contact.n[c]=projectile->object.position.n[c]+
            (end->n[c]-projectile->object.position.n[c])*best;
        if(way==DEFLECT_BY_BLOCK){
            /* glanced off the gun's surface: the velocity mirrored about the
             * surface's normal there (from the gun's axis toward the contact),
             * a grenade bouncing slower than a bolt or a round */
            real_vector3d normal;real along,keep=category==DEFLECT_GRENADE?.45f:category==DEFLECT_BULLET?.70f:.85f;
            vector_from_points3d(&best_on_gun,&contact,&normal);
            if(!(normalize3d(&normal)>.0001f)){normal=at_contact;scale_vector3d(&normal,-1.0f,&normal);normalize3d(&normal);}
            along=dot_product3d(&at_contact,&normal);
            if(along>0.0f){normal.i=-normal.i;normal.j=-normal.j;normal.k=-normal.k;along=-along;}
            for(int k=0;k<3;k++)reflected.n[k]=(at_contact.n[k]-2.0f*along*normal.n[k])*keep*strength;
        }else{
            /* The player's actual stroke aims the returned projectile. Preserve
             * its speed for fast rounds; slow airborne grenades receive only the
             * measured stroke's speed. No target lookup or steering. */
            speed=MAX(incoming,parry.hand[hand].speed)*strength;
            scale_vector3d(&parry.hand[hand].direction,speed,&reflected);
        }
        if(!valid_real_vector3d(&reflected))return FALSE;
        direction=reflected;
        if(!(normalize3d(&direction)>.0001f))return FALSE;
        projectile->object.translational_velocity=reflected;
        projectile->object.forward=direction;
        {
            real_vector3d left;
            cross_product3d(&projectile->object.up,&projectile->object.forward,&left);
            if(normalize3d(cross_product3d(&projectile->object.forward,&left,&projectile->object.up))==0)
                normalize3d(perpendicular3d(&projectile->object.forward,&projectile->object.up));
        }
        projectile->object.owner_object_index=unit;
        projectile->object.owner_player_index=owner->unit.player_index;
        projectile->object.owner_team_index=owner->object.owner_team_index;
        projectile->projectile.ignore_object_index=unit;
        projectile_set_target_object_index(index,NONE);
        parried[slot]=index;parried_valid[slot]=1;
        *fraction=best;
        vr_extra_projectile_feedback(hand,&contact,way==DEFLECT_BY_BLOCK,category==DEFLECT_BULLET);
        if(game_time_get()-deflect_log_tick>=TICKS_PER_SECOND/2){
            deflect_log_tick=game_time_get();
            platform_log("VR shot deflection: a %s deflected by the %s (hand %d), %.0f m/s in, %.0f m/s out",
                deflect_category_names[category],deflect_way_names[way],hand,
                (float)(incoming*TICKS_PER_SECOND/units),(float)(magnitude3d(&reflected)*TICKS_PER_SECOND/units));
        }
    }
    return TRUE;
}
#endif
