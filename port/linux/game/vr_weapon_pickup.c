/* WEAPON PULL. Test65 pulled a weapon a hand pointed at, without a flight to
 * see; the owner's Test65 session (17:37 log and video) never pulled one: the
 * line of sight was traced to the centre of a gun lying on the ground, which
 * the ground hides, the reach was a metre and nothing said why, and the hand
 * tried was the gun hand. Test66 makes it Half-Life 2 VR's and Half-Life:
 * Alyx's "gravity gloves", as the owner asked:
 * - point a free hand (one not holding the gun) at a weapon lying within PULL
 *   REACH (3 m by default) and it glows (PULL GLOW);
 * - squeeze: it locks (a tick, a brighter glow, a line to it); flick the hand
 *   back toward you (PULL STYLE FLICK, the default) or keep squeezing a little
 *   over half a second (GRIP), and it is thrown to the hand: you see it fly,
 *   in an arc, homing on where the hand is, in about half a second;
 * - a hand still closed when it arrives catches it: it is taken as the action
 *   button takes a weapon (players.c player_vr_take_weapon: into a free slot
 *   or in place of the gun held) and that hand holds it; an open hand lets it
 *   fall where it arrives.
 * WEAPON PULL turns it off. Local play only (a co-op client's pickups are the
 * host's); on foot, in control. Fixed state, no allocation. */
#ifdef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "game/players.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "objects/objects.h"
#include "items/items.h"
#include "items/weapons.h"
#include "units/units.h"
#include "physics/collisions.h"
#include "render/render_debug.h"
#include "halo_vr.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_weapon_pickup.h"
#include <math.h>
#include <string.h>
void platform_log(char const *format,...);
boolean player_vr_take_weapon(long player_index,long weapon_index);

enum { PULL_IDLE, PULL_LOCKED, PULL_FLYING };
static struct {
    long unit;
    struct {
        int state,down,held_ticks,samples;
        long candidate,target,start_tick,duration,why_logged;
        real arc;
        real_point3d start,previous_relative;
        real_vector3d velocity;
    } hand[2];
} pickup={NONE};

void vr_weapon_pickup_reset(void)
{
    for(int h=0;h<2;h++){
        memset(&pickup.hand[h],0,sizeof(pickup.hand[h]));
        pickup.hand[h].candidate=pickup.hand[h].target=NONE;pickup.hand[h].down=1;
    }
    pickup.unit=NONE;
}

int vr_weapon_pickup_busy(int hand)
{
    return hand>=0&&hand<2&&pickup.hand[hand].state!=PULL_IDLE;
}

static boolean pickup_enabled(void){return config_boolean("vr.weapon_pull");}
static real pickup_reach(void)
{
    double reach=config_real("vr.weapon_pull_reach");
    return isfinite(reach)&&reach>0?(real)PIN(reach,0.5,5.0):3.0f;
}
static boolean pickup_flick(void){return strcmp(config_string("vr.weapon_pull_style"),"grip")!=0;}

/* a weapon lying in the world that this unit could take (Test66: a weapon
 * just dropped by the player too: it may be pulled straight back) */
static struct weapon_datum *pickup_weapon(long index,long unit)
{
    struct weapon_datum *weapon=(struct weapon_datum *)object_try_and_get_and_verify_type(index,_object_mask_weapon);
    if(!weapon||weapon->object.parent_object_index!=NONE||
       !TEST_FLAG(weapon->object.flags,_object_connected_to_map_bit)||!unit_can_use_weapon(unit,index))return NULL;
    return weapon;
}

/* in sight of the eyes: aimed a little over the weapon's middle (a gun lying
 * on the ground has its middle in the ground), what the ray meets within
 * 15 cm of the weapon or past nine tenths of the way counting as clear */
static boolean pickup_in_sight(long unit,long index,real_point3d const *camera,real units)
{
    struct object_datum *object=object_get(index);
    real_point3d aim=object->object.bounding_sphere_center;
    real_vector3d ray;struct collision_result hit;real length;
    aim.z+=.06f*units;
    vector_from_points3d(camera,&aim,&ray);length=magnitude3d(&ray);
    if(!collision_test_vector(_collision_test_for_line_of_sight_flags,camera,&ray,unit,&hit))return TRUE;
    if(hit.type==_collision_result_object&&hit.object_index==index)return TRUE;
    return hit.t>=.92f||(1.0f-hit.t)*length<=.15f*units;
}

/* the weapon a hand points at within reach: within 20 degrees of where it
 * points, or kept while within 35 (the one already marked), or one right by
 * the hand; nearest the line first */
static long pickup_candidate(int h,long unit,real_point3d const *camera,real_point3d const *hand,real_vector3d const *forward,real units)
{
    struct object_iterator it;struct object_datum *object;
    real reach=pickup_reach()*units,best=1e30f;long choice=NONE,kept=pickup.hand[h].candidate;
    object_iterator_new(&it,_object_mask_weapon,0);
    while((object=object_iterator_next(&it))!=NULL){
        real_vector3d to;real distance,facing,score;
        if(!pickup_weapon(it.index,unit))continue;
        vector_from_points3d(hand,&object->object.bounding_sphere_center,&to);
        distance=magnitude3d(&to);
        if(distance>reach+object->object.bounding_sphere_radius)continue;
        facing=distance>.0001f?dot_product3d(&to,forward)/distance:1.0f;
        if(!(distance<=.30f*units||facing>=.94f||(it.index==kept&&facing>=.82f)))continue;
        if(!pickup_in_sight(unit,it.index,camera,units))continue;
        score=(1.0f-facing)*4.0f+distance/MAX(reach,.001f)-(it.index==kept?.25f:0.0f);
        if(score<best){best=score;choice=it.index;}
    }
    return choice;
}

/* why a squeeze took nothing, once a second a hand */
static void pickup_why(int h,long unit,real_point3d const *hand,real units,char const *reason)
{
    long now=game_time_get();
    struct object_iterator it;struct object_datum *object;real nearest=1e30f;
    if(now>=pickup.hand[h].why_logged&&now-pickup.hand[h].why_logged<TICKS_PER_SECOND)return;
    pickup.hand[h].why_logged=now;
    if(reason){platform_log("VR pull: hand %d squeezed: %s",h,reason);return;}
    object_iterator_new(&it,_object_mask_weapon,0);
    while((object=object_iterator_next(&it))!=NULL)if(pickup_weapon(it.index,unit)){
        real d=distance3d(hand,&object->object.bounding_sphere_center);
        if(d<nearest)nearest=d;
    }
    if(nearest<1e29f)platform_log("VR pull: hand %d squeezed at no weapon: the nearest lies %.1f m off (reach %.1f m; point within 20 degrees of it)",
        h,(float)(nearest/units),(float)pickup_reach());
    else platform_log("VR pull: hand %d squeezed at no weapon: none lying about to take",h);
}

/* where the hand catches: the palm drawn, else the hand */
static void pickup_palm(int h,long unit,real_point3d const *hand,real_point3d *palm)
{
    if(!vr_render_palm_point(h,unit,palm->n))*palm=*hand;
}

static void pickup_launch(int h,long unit,real_point3d const *hand,real units)
{
    struct object_datum *object=object_get(pickup.hand[h].target);
    real_point3d palm;real distance,seconds;
    pickup.hand[h].state=PULL_FLYING;
    pickup.hand[h].start=object->object.position;
    pickup.hand[h].start_tick=game_time_get();
    pickup_palm(h,unit,hand,&palm);
    distance=distance3d(&pickup.hand[h].start,&palm)/units;
    /* about half a second: a quarter and a flight at 8 m/s, 0.3 to 0.7 */
    seconds=PIN(.25f+distance/8.0f,.30f,.70f);
    pickup.hand[h].duration=MAX(1,(long)ceilf(seconds*(real)TICKS_PER_SECOND));
    pickup.hand[h].arc=(MIN(distance*.25f,.6f)+.10f)*units;
    object_activate(pickup.hand[h].target);
    vr_haptic(h,.55f,.05f);
    platform_log("VR pull: hand %d throws %s to itself (%.1f m, %.2f s)",h,
        tag_get_name(object->definition_index),(float)distance,(float)pickup.hand[h].duration/(real)TICKS_PER_SECOND);
}

void vr_weapon_pickup_tick(short local_player_index)
{
    long player=local_player_get_player_index(local_player_index);
    long unit=player!=NONE?player_get(player)->unit_index:NONE,now=game_time_get();
    struct unit_datum *u=unit!=NONE?unit_try_and_get(unit):NULL;
    real units=vr_units_per_metre();
    real_point3d camera,hands[2];real_vector3d forwards[2],up;
    int tracked[2];
    unsigned int buttons;float triggers[2],thumbs[4];
    if(!vr_active()||!pickup_enabled()||!u||game_connection()!=_game_connection_local||
       u->object.parent_object_index!=NONE||TEST_FLAG(u->object.damage_flags,_object_dead_bit)||
       cinematic_in_progress()||director_inhibited_input(local_player_index)||game_time_get_paused()||
       !vr_controller(&buttons,triggers,thumbs)||!(units>0)){
        vr_weapon_pickup_reset();return;
    }
    if(pickup.unit!=unit){vr_weapon_pickup_reset();pickup.unit=unit;}
    unit_get_camera_position(unit,&camera);
    for(int each=0;each<2;each++)tracked[each]=vr_hand_world(each,camera.n,hands[each].n,forwards[each].n,up.n);
    for(int h=0;h<2;h++){
        int held=vr_interaction_grip(h,NULL,NULL),press=held&&!pickup.hand[h].down;
        int gun_hand=h==vr_weapon_hand()&&!vr_hand_empty();
        int free_hand=tracked[h]&&!gun_hand&&vr_interaction_owner(h)==VR_INTERACTION_NONE;
        real_point3d relative;
        pickup.hand[h].down=held;
        /* the off hand at the gun's support grip steadies the gun: no pull */
        if(free_hand&&h!=vr_weapon_hand()&&!vr_hand_empty()&&tracked[1-h]&&
           distance3d(&hands[0],&hands[1])<.30f*units)free_hand=0;
        /* the hand's own movement (the head's taken out): the flick */
        if(tracked[h]){
            for(int axis=0;axis<3;axis++)relative.n[axis]=hands[h].n[axis]-camera.n[axis];
            if(pickup.hand[h].samples){
                real_vector3d step;vector_from_points3d(&pickup.hand[h].previous_relative,&relative,&step);
                for(int axis=0;axis<3;axis++)pickup.hand[h].velocity.n[axis]=pickup.hand[h].velocity.n[axis]*.4f+step.n[axis]*.6f;
            }
            pickup.hand[h].previous_relative=relative;pickup.hand[h].samples=1;
        }else pickup.hand[h].samples=0;

        if(pickup.hand[h].state==PULL_FLYING){
            struct weapon_datum *weapon=pickup_weapon(pickup.hand[h].target,unit);
            real_point3d palm,position;real s,eased;
            if(!weapon){platform_log("VR pull: the weapon in flight to hand %d was taken or gone",h);pickup.hand[h].state=PULL_IDLE;continue;}
            pickup_palm(h,unit,&hands[h],&palm);
            s=(real)(now-pickup.hand[h].start_tick)/(real)pickup.hand[h].duration;
            if(s>=1.0f||distance3d(&weapon->object.bounding_sphere_center,&palm)<=.22f*units){
                long index=pickup.hand[h].target;
                char const *name=tag_get_name(weapon->definition_index);
                pickup.hand[h].state=PULL_IDLE;pickup.hand[h].target=NONE;
                if(held&&tracked[h]&&player_vr_take_weapon(player,index)){
                    vr_haptic(h,.85f,.07f);
                    if(h!=vr_weapon_hand())vr_set_weapon_hand(h);
                    platform_log("VR pull: %s caught in hand %d and equipped",name?name:"a weapon",h);
                }else{
                    /* not caught: it falls where it came */
                    weapon->object.translational_velocity=*global_zero_vector3d;
                    platform_log("VR pull: %s reached hand %d %s; it drops",name?name:"a weapon",h,
                        held?"but could not be taken":"open (close the hand as it arrives to catch it)");
                }
                continue;
            }
            /* along the line to the palm as it is now, eased, and over it in an arc */
            eased=s*s*(3.0f-2.0f*s);
            for(int axis=0;axis<3;axis++)
                position.n[axis]=pickup.hand[h].start.n[axis]+(palm.n[axis]-pickup.hand[h].start.n[axis])*eased;
            position.z+=pickup.hand[h].arc*4.0f*s*(1.0f-s);
            object_set_position(pickup.hand[h].target,&position,NULL,NULL);
            weapon->object.translational_velocity=*global_zero_vector3d;
            weapon->object.angular_velocity=*global_zero_vector3d;
            SET_FLAG(weapon->object.flags,_object_at_rest_bit,FALSE);
            continue;
        }
        if(pickup.hand[h].state==PULL_LOCKED){
            struct weapon_datum *weapon=pickup_weapon(pickup.hand[h].target,unit);
            if(!weapon||!tracked[h]||!free_hand){pickup.hand[h].state=PULL_IDLE;pickup.hand[h].target=NONE;continue;}
            if(!held){
                pickup.hand[h].state=PULL_IDLE;pickup.hand[h].target=NONE;
                platform_log("VR pull: hand %d let go before the pull",h);continue;
            }
            pickup.hand[h].held_ticks++;
            {
                /* a flick: the hand snapped back toward the body or up, over 1.2 m/s */
                real_vector3d home;real speed;
                vector_from_points3d(&hands[h],&camera,&home);
                if(normalize3d(&home)<.0001f)home=*global_up3d;
                speed=MAX(dot_product3d(&pickup.hand[h].velocity,&home),pickup.hand[h].velocity.k)*(real)TICKS_PER_SECOND/units;
                if(pickup_flick()?speed>=1.2f:pickup.hand[h].held_ticks>=(6*TICKS_PER_SECOND)/10)pickup_launch(h,unit,&hands[h],units);
            }
            continue;
        }
        pickup.hand[h].candidate=free_hand?pickup_candidate(h,unit,&camera,&hands[h],&forwards[h],units):NONE;
        if(press){
            if(pickup.hand[h].candidate!=NONE){
                pickup.hand[h].target=pickup.hand[h].candidate;pickup.hand[h].state=PULL_LOCKED;pickup.hand[h].held_ticks=0;
                vr_haptic(h,.30f,.03f);
                platform_log("VR pull: hand %d locked on %s (%.1f m away; %s)",h,
                    tag_get_name(object_get(pickup.hand[h].target)->definition_index),
                    (float)(distance3d(&hands[h],&object_get(pickup.hand[h].target)->object.bounding_sphere_center)/units),
                    pickup_flick()?"flick the hand back to pull":"keep squeezing to pull");
            }else if(gun_hand&&tracked[h]){
                if(pickup_candidate(h,unit,&camera,&hands[h],&forwards[h],units)!=NONE)
                    pickup_why(h,unit,&hands[h],units,"the gun hand holds its gun (pull with the free hand)");
            }else if(free_hand)pickup_why(h,unit,&hands[h],units,NULL);
        }
    }
}

int vr_weapon_pickup_render(float const camera[3])
{
    int drawn=0;real units=vr_units_per_metre();
    long unit=pickup.unit;
    (void)camera;
    if(!pickup_enabled()||!config_boolean("vr.weapon_pull_glow")||!(units>0))return 0;
    for(int h=0;h<2;h++){
        long index=pickup.hand[h].state!=PULL_IDLE?pickup.hand[h].target:pickup.hand[h].candidate;
        struct object_datum *object=index!=NONE?object_try_and_get_and_verify_type(index,_object_mask_weapon):NULL;
        real pulse;
        real_argb_color glow={1,.55f,.85f,1};
        if(!object||object->object.parent_object_index!=NONE)continue;
        pulse=.5f+.5f*sinf((real)vr_pose_time()*6.0f);
        if(pickup.hand[h].state!=PULL_IDLE){glow.red=.8f;glow.green=.95f;glow.blue=1;}
        render_debug_sphere(TRUE,&object->object.bounding_sphere_center,
            object->object.bounding_sphere_radius*(1.05f+.08f*pulse)+.02f*units,&glow);
        render_debug_sphere(TRUE,&object->object.bounding_sphere_center,.025f*units,&glow);
        /* locked: a line from the palm to it */
        if(pickup.hand[h].state==PULL_LOCKED&&unit!=NONE){
            real_point3d palm;
            if(vr_render_palm_point(h,unit,palm.n))render_debug_line(TRUE,&palm,&object->object.bounding_sphere_center,&glow);
        }
        drawn=1;
    }
    return drawn;
}
#endif
