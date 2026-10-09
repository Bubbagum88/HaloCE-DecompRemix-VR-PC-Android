/* Offline VR-only motion assist for cooling an overheated held weapon.
 * It multiplies the authored cooling rate; weapon state and thresholds remain native. */
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
#include <math.h>

static struct {
    long weapon, unit;
    double sample_time;
    real_vector3d relative;
    real_vector3d velocity;
    float speed;
    double last_reversal_time;
    int reversal_count;
    int valid;
} shake;

unsigned long system_milliseconds(void);

static void vr_cooldown_shake_reset(void)
{
    shake.weapon=shake.unit=NONE;
    shake.sample_time=0;
    shake.velocity=*global_zero_vector3d;
    shake.speed=0;
    shake.last_reversal_time=0;
    shake.reversal_count=0;
    shake.valid=0;
}

float vr_cooldown_shake_rate(long weapon_index)
{
    short local;
    long player,unit_index;
    struct weapon_datum *weapon;
    struct unit_datum *unit;
    struct player_datum *player_datum;
    unsigned int buttons;
    float triggers[2],sticks[4],position[3],forward[3],up[3];
    real_point3d camera;
    real_vector3d relative,delta;
    double now,elapsed;
    float units,speed,previous_speed,direction_cosine;
    int axis;
    short current_slot;
    long current_weapon;
    if(!config_boolean("vr.cooldown_shake") || game_connection()!=_game_connection_local ||
       !vr_active() || !vr_aiming() || !vr_controller(&buttons,triggers,sticks)) {
        vr_cooldown_shake_reset();return 1.0f;
    }
    local=local_player_get_next(NONE);
    player=local!=NONE?local_player_get_player_index(local):NONE;
    player_datum=player!=NONE?player_try_and_get(player):NULL;
    unit_index=player_datum?player_datum->unit_index:NONE;
    unit=unit_index!=NONE?unit_try_and_get(unit_index):NULL;
    if(unit_index==NONE || !unit ||
       unit->object.parent_object_index!=NONE ||
       TEST_FLAG(unit->object.damage_flags,_object_dead_bit) ||
       !(units=vr_units_per_metre())) {
        vr_cooldown_shake_reset();return 1.0f;
    }
    current_slot=unit->unit.current_weapon_index;
    if(current_slot<0 || current_slot>=MAXIMUM_WEAPONS_PER_UNIT) {
        vr_cooldown_shake_reset();return 1.0f;
    }
    current_weapon=unit_inventory_get_weapon(unit_index,current_slot);
    if(current_weapon==NONE) {vr_cooldown_shake_reset();return 1.0f;}
    /* weapon_update runs for every world weapon. An NPC weapon update must
     * never erase the sample for the local player's currently selected gun. */
    if(shake.valid && (shake.unit!=unit_index || shake.weapon!=current_weapon))
        vr_cooldown_shake_reset();
    if(weapon_index!=current_weapon)return 1.0f;
    weapon=weapon_try_and_get(weapon_index);
    if(!weapon) {vr_cooldown_shake_reset();return 1.0f;}
    unit_get_camera_position(unit_index,&camera);
    if(!vr_hand_world(vr_weapon_hand(),camera.n,position,forward,up)) {
        vr_cooldown_shake_reset();return 1.0f;
    }
    /* Subtract head translation so walking or room-scale drift alone does not
     * count as shaking the weapon. */
    for(axis=0;axis<3;axis++) relative.n[axis]=position[axis]-camera.n[axis];
    now=(double)system_milliseconds()*0.001;
    if(!isfinite(now) || shake.weapon!=weapon_index || shake.unit!=unit_index || !shake.valid ||
       now<=shake.sample_time || now-shake.sample_time>0.15) {
        shake.weapon=weapon_index;shake.unit=unit_index;shake.relative=relative;
        shake.sample_time=now;shake.velocity=*global_zero_vector3d;shake.speed=0;
        shake.last_reversal_time=0;shake.reversal_count=0;shake.valid=1;return 1.0f;
    }
    elapsed=now-shake.sample_time;
    for(axis=0;axis<3;axis++)delta.n[axis]=(relative.n[axis]-shake.relative.n[axis])/units;
    scale_vector3d(&delta,1.0f/(real)elapsed,&delta);
    speed=magnitude3d(&delta);
    previous_speed=magnitude3d(&shake.velocity);
    direction_cosine=previous_speed>0.0001f&&speed>0.0001f?
        dot_product3d(&shake.velocity,&delta)/(previous_speed*speed):1.0f;
    /* A shake must reverse direction. Fast one-way movement and head motion
     * alone do not accelerate cooling; finite tracking noise is thresholded. */
    if(vr_cooldown_shake_is_reversal(previous_speed,speed,direction_cosine)) {
        if(shake.last_reversal_time>0&&now-shake.last_reversal_time<=0.5)
            shake.reversal_count=MIN(2,shake.reversal_count+1);
        else shake.reversal_count=1;
        shake.last_reversal_time=now;
        if(shake.reversal_count>=2)
            shake.speed=shake.speed*.55f+(previous_speed+speed)*.225f;
    } else {
        shake.speed=vr_cooldown_shake_decay(shake.speed,(float)elapsed);
        if(shake.last_reversal_time>0&&now-shake.last_reversal_time>0.5) {
            shake.speed=0;
            shake.reversal_count=0;
        }
    }
    shake.speed=MIN(shake.speed,2.7f);
    if(!isfinite(shake.speed))shake.speed=0;
    shake.velocity=delta;
    shake.relative=relative;shake.sample_time=now;
    return TEST_FLAG(weapon->weapon.flags,_weapon_overheated_bit)?
        vr_cooldown_shake_multiplier(shake.speed):1.0f;
}
#else
#include "cseries.h"
#include "vr_cooldown_shake.h"
float vr_cooldown_shake_rate(long weapon_index){return 1.0f;}
#endif
