/* Test65: WEAPON PULL (vr.weapon_pull_reach). The owner: "weapons should have
 * an optional highlight that appears when they are in hand range and a grip
 * will pull them to your hand and equip them", kept as a choice. A free hand
 * (not holding a gun, nothing in it, not at the gun's support grip) pointed at
 * a weapon lying within reach, or right by one, marks it (PULL GLOW); its
 * grip pulls the weapon to the palm (a third of the way each tick, about a
 * fifth of a second) and, there, equips it (players.c
 * player_vr_take_weapon: as the action button takes it, into a free slot or in
 * place of the gun held) in that hand. Let go first, the weapon drops where it
 * is. Local play only (a co-op client's pickups are the host's); on foot, in
 * control. Fixed state, no allocation. */
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

static struct {
    long candidate[2],pulling[2],pull_start[2],unit;
    int down[2];
} pickup={{NONE,NONE},{NONE,NONE},{0,0},NONE,{1,1}};

void vr_weapon_pickup_reset(void)
{
    for(int h=0;h<2;h++){pickup.candidate[h]=pickup.pulling[h]=NONE;pickup.down[h]=1;pickup.pull_start[h]=0;}
    pickup.unit=NONE;
}

int vr_weapon_pickup_busy(int hand)
{
    return hand>=0&&hand<2&&pickup.pulling[hand]!=NONE;
}

static real pickup_reach(void)
{
    double reach=config_real("vr.weapon_pull_reach");
    return isfinite(reach)?(real)PIN(reach,0.0,2.5):1.0f;
}

/* a weapon lying in the world that this unit could take */
static struct weapon_datum *pickup_weapon(long index,long unit)
{
    struct weapon_datum *weapon=(struct weapon_datum *)object_try_and_get_and_verify_type(index,_object_mask_weapon);
    if(!weapon||weapon->object.parent_object_index!=NONE||
       !TEST_FLAG(weapon->object.flags,_object_connected_to_map_bit)||
       weapon->item.ignore_object_index==unit||!unit_can_use_weapon(unit,index))return NULL;
    return weapon;
}

/* the weapon a hand points at within reach (32 degrees), or one right by it */
static long pickup_candidate(long unit,real_point3d const *camera,real_point3d const *hand,real_vector3d const *forward,real units)
{
    struct object_iterator it;struct object_datum *object;
    real reach=pickup_reach()*units,best=1e30f;long choice=NONE;
    object_iterator_new(&it,_object_mask_weapon,0);
    while((object=object_iterator_next(&it))!=NULL){
        real_vector3d to,ray;real distance,facing,score;struct collision_result hit;
        if(!pickup_weapon(it.index,unit))continue;
        vector_from_points3d(hand,&object->object.bounding_sphere_center,&to);
        distance=magnitude3d(&to);
        if(distance>reach+object->object.bounding_sphere_radius)continue;
        facing=distance>.0001f?dot_product3d(&to,forward)/distance:1.0f;
        if(!(distance<=.35f*units||facing>=.85f))continue;
        /* in sight of the eyes (never through a wall) */
        vector_from_points3d(camera,&object->object.bounding_sphere_center,&ray);
        if(collision_test_vector(_collision_test_for_line_of_sight_flags,camera,&ray,unit,&hit)&&
           !(hit.type==_collision_result_object&&hit.object_index==it.index))continue;
        score=distance*(2.0f-facing);
        if(score<best){best=score;choice=it.index;}
    }
    return choice;
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
    if(!vr_active()||!(pickup_reach()>0.0f)||!u||game_connection()!=_game_connection_local||
       u->object.parent_object_index!=NONE||TEST_FLAG(u->object.damage_flags,_object_dead_bit)||
       cinematic_in_progress()||director_inhibited_input(local_player_index)||game_time_get_paused()||
       !vr_controller(&buttons,triggers,thumbs)||!(units>0)){
        vr_weapon_pickup_reset();return;
    }
    if(pickup.unit!=unit){vr_weapon_pickup_reset();pickup.unit=unit;}
    unit_get_camera_position(unit,&camera);
    for(int each=0;each<2;each++)tracked[each]=vr_hand_world(each,camera.n,hands[each].n,forwards[each].n,up.n);
    for(int h=0;h<2;h++){
        int press,release,held=vr_interaction_grip(h,&press,&release);
        int free_hand=tracked[h]&&!(h==vr_weapon_hand()&&!vr_hand_empty())&&
            vr_interaction_owner(h)==VR_INTERACTION_NONE;
        press=held&&!pickup.down[h];pickup.down[h]=held;
        /* the off hand at the gun's support grip steadies the gun: no pull */
        if(free_hand&&h!=vr_weapon_hand()&&!vr_hand_empty()&&tracked[1-h]&&
           distance3d(&hands[0],&hands[1])<.30f*units)free_hand=0;
        if(pickup.pulling[h]!=NONE){
            struct weapon_datum *weapon=pickup_weapon(pickup.pulling[h],unit);
            real_vector3d to;real distance;
            if(!weapon||!held||!tracked[h]){
                if(weapon)platform_log("VR pickup: hand %d let go of the pull; the weapon drops",h);
                pickup.pulling[h]=NONE;continue;
            }
            vector_from_points3d(&weapon->object.bounding_sphere_center,&hands[h],&to);
            distance=magnitude3d(&to);
            if(distance<=.22f*units||now-pickup.pull_start[h]>=TICKS_PER_SECOND){
                long index=pickup.pulling[h];
                char const *name=tag_get_name(weapon->definition_index);
                pickup.pulling[h]=NONE;
                if(player_vr_take_weapon(player,index)){
                    vr_haptic(h,.8f,.06f);
                    if(h!=vr_weapon_hand())vr_set_weapon_hand(h);
                    platform_log("VR pickup: %s pulled into hand %d and equipped",name?name:"a weapon",h);
                }else platform_log("VR pickup: %s reached hand %d but could not be taken",name?name:"a weapon",h);
                continue;
            }
            {
                /* toward the palm: a third of the way a tick, at least 15 cm */
                real step=MAX(distance*.35f,MIN(distance,.15f*units));
                real_point3d position=weapon->object.position;
                for(int axis=0;axis<3;axis++)position.n[axis]+=to.n[axis]/distance*step;
                object_set_position(pickup.pulling[h],&position,NULL,NULL);
                weapon->object.translational_velocity=*global_zero_vector3d;
                weapon->object.angular_velocity=*global_zero_vector3d;
            }
            continue;
        }
        pickup.candidate[h]=free_hand?pickup_candidate(unit,&camera,&hands[h],&forwards[h],units):NONE;
        if(press&&pickup.candidate[h]!=NONE){
            pickup.pulling[h]=pickup.candidate[h];pickup.pull_start[h]=now;pickup.candidate[h]=NONE;
            object_activate(pickup.pulling[h]);
            vr_haptic(h,.35f,.04f);
            platform_log("VR pickup: hand %d pulls %s (%.1f m away)",h,
                tag_get_name(object_get(pickup.pulling[h])->definition_index),
                (float)(distance3d(&hands[h],&object_get(pickup.pulling[h])->object.bounding_sphere_center)/units));
        }
    }
}

int vr_weapon_pickup_render(float const camera[3])
{
    int drawn=0;real units=vr_units_per_metre();
    (void)camera;
    if(!config_boolean("vr.weapon_pull_glow")||!(units>0))return 0;
    for(int h=0;h<2;h++){
        long index=pickup.pulling[h]!=NONE?pickup.pulling[h]:pickup.candidate[h];
        struct object_datum *object=index!=NONE?object_try_and_get_and_verify_type(index,_object_mask_weapon):NULL;
        real pulse;
        real_argb_color glow={1,.55f,.85f,1};
        if(!object||object->object.parent_object_index!=NONE)continue;
        pulse=.5f+.5f*sinf((real)vr_pose_time()*6.0f);
        if(pickup.pulling[h]!=NONE){glow.red=.8f;glow.green=.95f;glow.blue=1;}
        render_debug_sphere(TRUE,&object->object.bounding_sphere_center,
            object->object.bounding_sphere_radius*(1.05f+.08f*pulse)+.02f*units,&glow);
        render_debug_sphere(TRUE,&object->object.bounding_sphere_center,.025f*units,&glow);
        drawn=1;
    }
    return drawn;
}
#endif
