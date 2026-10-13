/* Test62: opt-in chest grenades and enemy-only assisted fist combat.
 * Transient state only. Native projectile/damage/capsule code owns gameplay.
 * No protocol extensions, network clients/PvP never enter this path. */
#ifdef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "game/players.h"
#include "game/game_allegiance.h"
#include "units/units.h"
#include "units/bipeds.h"
#include "ai/actors.h"
#include "ai/actor_types.h"
#include "objects/object_definitions.h"
#include "models/model_definitions.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "physics/collisions.h"
#include "render/render_debug.h"
#include "render/render.h"
#include "render/render_cameras_internal.h"
#include "models/models.h"
#include "scenario/scenario.h"
#include "game/game_globals.h"
#include "vr_manual_reload.h"
#include "rasterizer/rasterizer.h"
#include "network_coop.h"
#include "network_interaction.h"
#include "vr_npc_interaction.h"
#include "vr_extra_interaction.h"
#include "halo_vr.h"
#include "../src/vr.h"
#include "../src/port_config.h"
void platform_log(char const *format,...);
static struct {
    long unit,tick,target,lock_until,approach_until,stun_until,flash_until,grenade_release_tick;
    /* Test63: the target slowed (not frozen) while the lunge closes and just
     * after a hit; the last punch diagnostic (rate-limited) */
    long hold_until,punch_logged;
    int hit_count;
    real_point3d hit_point;
    struct { int down,held,type,samples,hover; real_point3d point,last;
        real_vector3d velocity[3]; } hand[2];
    /* Test65: Arkham Shadow's freeflow: the combo meter (hits in a row, each
     * within two seconds, broken when the player is hit), a blow carried by a
     * lunge or a counter (struck on arrival), the counter window an enemy's
     * swing opens, the enemy countered (its swing undone, staggered), and a
     * knockdown to give the NPC module after the blow */
    int combo,strike_pending,strike_hand,strike_counter,knock_pending;
    long combo_until,last_strike_tick,strike_issued,counter_enemy,counter_until,countered,countered_until,
        knock_target,reason_logged;
    real strike_scale,lunge_metres,knock_speed;
    real_vector3d strike_dir,knock_dir;
    real_point3d knock_point;
    /* Test66: the fist blow's damage share (ENEMY HEALTH, the combo, a
     * takedown, the enemy's armour) for this tick's blow (the native damage
     * multiplier: the damage scale only bends the blow between the effect's
     * minimum and its roll, and a Grunt died to the minimum alone); a hand's
     * last fast swipe while an enemy swings (a parry); the guard tiring
     * under blows; an Elite answering a flurry with its own swing */
    real damage_share;
    long share_tick,parry_tick[2],guard_strain_until,answer_unit,answer_at,answer_ready,flurry_unit,flurry_until;
    int guard_strain,flurry_hits;
} extra={.unit=NONE,.tick=NONE,.target=NONE,.grenade_release_tick=NONE,.counter_enemy=NONE,.countered=NONE,.knock_target=NONE,
    .damage_share=1,.share_tick=NONE,.answer_unit=NONE,.flurry_unit=NONE};
/* Brief semantic pulses must finish before continuous surface contact resumes. */
static double extra_feedback_start[2],extra_feedback_until[2];
static void extra_pulse(int hand,float amplitude,float seconds)
{
    double now=vr_pose_time();
    if(hand<0||hand>1||!isfinite(now)||!(seconds>0&&seconds<=.1f))return;
    extra_feedback_start[hand]=now;extra_feedback_until[hand]=now+seconds;
    vr_haptic(hand,amplitude,seconds);
}
int vr_extra_feedback_active(int hand)
{
    double now=vr_pose_time();
    return hand>=0&&hand<2&&isfinite(now)&&now>=extra_feedback_start[hand]&&now<extra_feedback_until[hand];
}
static real extra_bound(char const *key,real fallback,real low,real high)
{
    real v=(real)config_real(key);return isfinite(v)?PIN(v,low,high):fallback;
}
static long extra_player(boolean input)
{
    unsigned int buttons;float triggers[2],thumbs[4];
    short local=local_player_get_next(NONE);
    long player=local!=NONE?local_player_get_player_index(local):NONE;
    long unit=player!=NONE?player_get(player)->unit_index:NONE;
    struct biped_datum *b=unit!=NONE?biped_try_and_get(unit):NULL;
    struct unit_datum *u=(struct unit_datum *)b;
    if(!vr_active()||!b||TEST_FLAG(b->biped.flags,_biped_no_collision_bit)||
        TEST_FLAG(u->unit.flags,_unit_suspended_bit)||u->object.parent_object_index!=NONE||
        TEST_FLAG(u->object.damage_flags,_object_dead_bit)||cinematic_in_progress()||
        !(game_connection()==_game_connection_local||
          (game_connection()==_game_connection_network_server&&network_coop_active()&&
           config_boolean("net.host_vr_actions")&&network_interaction_host_ready())))return NONE;
    if(input&&(game_time_get_paused()||director_inhibited_input(local)||
        !vr_controller(&buttons,triggers,thumbs)))return NONE;
    return unit;
}
/* Combat enters the physical-melee sweep even when network gesture mode
 * normally disables it. Preserve the normal OFF/invalid-threshold guard. */
static boolean extra_combat_on(void)
{
    real speed=vr_melee_speed();
    return config_boolean("vr.assisted_combat")&&!strcmp(config_string("vr.melee"),"impact")&&isfinite(speed)&&speed>0;
}
int vr_combat_enabled(void)
{
    return extra_combat_on()&&extra_player(TRUE)!=NONE;
}
/* Test65: LUNGE (how far a punch carries the player to an enemy; 0: FIST
 * REACH's short step only), ENEMY HEALTH (enemies take this many more
 * punches; takedowns and guns as they were), COUNTERS */
static real combat_lunge_reach(void){return extra_bound("vr.combat_lunge_reach",6.0f,0.0f,10.0f);}
static real combat_reach(void){return MAX(extra_bound("vr.combat_reach",2.5f,.75f,3),combat_lunge_reach());}
static real combat_health(void){return extra_bound("vr.combat_enemy_health",3.0f,1.0f,6.0f);}
static boolean combat_counters_on(void){return config_boolean("vr.combat_counters");}
/* combo hits for a takedown (Arkham's full meter) */
#define COMBAT_SPECIAL 8
/* level gap between two bodies' roots, and where a blow is in reach */
static real combat_gap(long unit,long target)
{
    real_vector3d d;
    vector_from_points3d(&unit_get(unit)->object.position,&unit_get(target)->object.position,&d);d.k=0;
    return magnitude3d(&d);
}
static real combat_stop(long unit,long target)
{
    real_point3d unused_base;real unused_height,player_width,target_width,units=vr_units_per_metre();
    biped_get_physics_pill(unit,&unused_base,&unused_height,&player_width);
    biped_get_physics_pill(target,&unused_base,&unused_height,&target_width);
    if(!isfinite(player_width)||!isfinite(target_width))return .55f*units;
    return MAX(.55f*units,player_width+target_width+.05f*units);
}
static void combat_reason(char const *reason)
{
    long now=game_time_get();
    if(now>=extra.reason_logged&&now-extra.reason_logged<TICKS_PER_SECOND)return;
    extra.reason_logged=now;
    platform_log("VR fist combat: punch not assisted: %s",reason);
}
/* Test66: each kind fights its own way (Arkham Shadow's thug types, after
 * Halo's own): Grunts are staggered in two blows and knocked down easily;
 * Jackals take a front punch on their shield unless staggered; Elites take
 * four blows to stagger, are knocked down only by a takedown or a counter,
 * and answer a flurry with a swing of their own; Hunters are armoured in
 * front (the back is soft), never staggered by fists and never knocked
 * down. Blocking a Hunter's blow saves less. */
struct combat_kind {short type;int stun_hits;real front_share,back_share,block_share;boolean knocked,answers;};
static struct combat_kind const combat_kinds[]={
    {_actor_grunt,2,1.0f,1.0f,.30f,TRUE,FALSE},
    {_actor_jackal,2,.45f,1.15f,.30f,TRUE,FALSE},
    {_actor_elite,4,1.0f,1.0f,.35f,FALSE,TRUE},
    {_actor_hunter,99,.40f,1.6f,.60f,FALSE,FALSE},
};
static struct combat_kind const combat_kind_default={NONE,3,1.0f,1.0f,.35f,TRUE,FALSE};
static struct combat_kind const *combat_kind(long target)
{
    struct unit_datum *u=target!=NONE?unit_try_and_get(target):NULL;
    struct actor_datum *a=u&&u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
    if(a)for(unsigned k=0;k<NUMBEROF(combat_kinds);k++)if(combat_kinds[k].type==a->meta.type)return &combat_kinds[k];
    return &combat_kind_default;
}
/* Test66: an enemy's head and chest from its own bones (the owner's Test65:
 * the target lights floated off the bodies: they were the tick's camera
 * point and the bounding sphere's centre, which takes in a Hunter's cannon,
 * while the body is drawn a tick behind). While a frame is drawn the node
 * matrices are the pose drawn (objects.c), in a tick the tick's. */
static boolean combat_regions(long target,real_point3d *head,real_point3d *chest)
{
    struct unit_datum *u=target!=NONE?unit_try_and_get(target):NULL;
    struct object_definition *definition;struct model *model;real_matrix4x3 *nodes;
    short count,h=NONE,c=NONE;
    if(!u)return FALSE;
    definition=object_definition_get(u->definition_index);
    if(definition->object.model.index!=NONE&&(nodes=object_get_node_matrices(target))!=NULL){
        model=model_definition_get(definition->object.model.index);
        count=(short)(u->object.node_matrices.size/sizeof(real_matrix4x3));
        if(count>0&&count<=MAXIMUM_NODES_PER_MODEL&&model->nodes.count==count){
            for(short n=0;n<count;n++){
                char const *name=TAG_BLOCK_GET_ELEMENT(&model->nodes,n,struct model_node)->name;
                if(h==NONE&&strstr(name,"head"))h=n;
                if(strstr(name,"spine"))c=n; /* the last: the upper chest */
            }
            if(h!=NONE&&c!=NONE&&valid_real_point3d(&nodes[h].position)&&valid_real_point3d(&nodes[c].position)){
                real_vector3d neck;real units=vr_units_per_metre();
                *chest=nodes[c].position;
                /* the head node is the neck joint: the face is a little above it */
                vector_from_points3d(chest,&nodes[h].position,&neck);
                if(normalize3d(&neck)<.0001f)neck=*global_up3d;
                point_from_line3d(&nodes[h].position,&neck,.08f*units,head);
                return TRUE;
            }
        }
    }
    unit_get_camera_position(target,head);*chest=u->object.bounding_sphere_center;
    return valid_real_point3d(head)&&valid_real_point3d(chest);
}
static real_point3d combat_chest(long target)
{
    real_point3d head,chest;
    if(!combat_regions(target,&head,&chest))chest=unit_get(target)->object.bounding_sphere_center;
    return chest;
}
void vr_extra_reset(void)
{
    for(int h=0;h<2;h++)vr_interaction_release(h,VR_INTERACTION_GRENADE);
    memset(&extra,0,sizeof(extra));extra.unit=extra.tick=extra.target=extra.grenade_release_tick=NONE;
    extra.counter_enemy=extra.countered=extra.knock_target=NONE;
    extra.damage_share=1;extra.share_tick=extra.answer_unit=extra.flurry_unit=NONE;
    extra.hand[0].down=extra.hand[1].down=1;
    memset(extra_feedback_start,0,sizeof(extra_feedback_start));
    memset(extra_feedback_until,0,sizeof(extra_feedback_until));
}
int vr_physical_grenade_busy(void)
{
    /* Native button input is filtered after this tick's physical release. Keep
     * that one tick reserved too, so a held button cannot spend a second grenade. */
    return config_boolean("vr.physical_grenades")&&(extra.hand[0].held||extra.hand[1].held||
        (extra.grenade_release_tick!=NONE&&extra.grenade_release_tick==game_time_get()));
}
static boolean extra_enemy(long owner,long target)
{
    struct unit_datum *u=target!=NONE?unit_try_and_get(target):NULL;
    struct unit_datum *p=owner!=NONE?unit_try_and_get(owner):NULL;
    struct actor_datum *a=u&&u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
    return p&&u&&a&&a->meta.active&&u->object.type==_object_type_biped&&
        u->unit.player_index==NONE&&u->object.parent_object_index==NONE&&
        !TEST_FLAG(u->object.damage_flags,_object_dead_bit)&&
        !TEST_FLAG(u->unit.flags,_unit_suspended_bit)&&
        game_team_is_enemy(p->object.owner_team_index,a->meta.team_index);
}
static boolean extra_visible(long owner,long target,real_point3d const *from,real_point3d const *to)
{
    real_vector3d ray;struct collision_result hit;
    vector_from_points3d(from,to,&ray);
    return !collision_test_vector(_collision_test_for_projectiles_flags,from,&ray,owner,&hit)||
        (hit.type==_collision_result_object&&hit.object_index==target);
}
/* Test63: the slots in the torso's chest frame (vr_torso_place), not the
 * head's: the owner's Test62 grenades orbited with every glance. Frag on the
 * left, plasma on the right; CHEST FWD/DOWN/SPACING move them. */
static boolean chest_points(long unit,real_point3d const *camera,real_point3d points[2])
{
    real units=vr_units_per_metre();
    (void)unit;
    if(!(units>0&&units<10)||!camera)return FALSE;
    for(int type=0;type<2;type++){
        float offset[3];
        offset[0]=(float)((type?1.0f:-1.0f)*extra_bound("vr.grenade_chest_spread",.14f,.06f,.3f));
        offset[1]=-(float)extra_bound("vr.grenade_chest_down",.30f,.15f,.6f);
        offset[2]=-(float)extra_bound("vr.grenade_chest_forward",.16f,.08f,.4f);
        if(!vr_torso_place(offset,camera->n,points[type].n)||!valid_real_point3d(&points[type]))return FALSE;
    }
    return TRUE;
}
/* the chest frame's level forward in the world */
static boolean chest_forward(real_point3d const *camera,real_vector3d *forward)
{
    float a[3]={0,0,0},b[3]={0,0,-1};real_point3d p,q;
    if(!camera||!vr_torso_place(a,camera->n,p.n)||!vr_torso_place(b,camera->n,q.n))return FALSE;
    vector_from_points3d(&p,&q,forward);forward->k=0;
    return normalize3d(forward)>.0001f;
}
/* Test65: each tick of the fight: the combo meter runs out two seconds
 * after the last hit; a blow a lunge or counter carries lands when the
 * player arrives (unit_vr_combat_strike: the same fist blow, at the enemy),
 * or is given up a second on (blocked, cancelled); a knockdown the blow
 * earned is handed to the NPC module (vr_npc_interaction_knock: a short
 * ragdoll, up within NPC RECOVERY); the counter window closes */
static void combat_tick(long unit)
{
    long now=game_time_get();real units=vr_units_per_metre();
    if(extra.combo&&now>extra.combo_until){
        if(extra.combo>=3)platform_log("VR fist combat: combo of %d ended",extra.combo);
        extra.combo=0;
    }
    if(extra.counter_enemy!=NONE&&(now>extra.counter_until||!extra_enemy(unit,extra.counter_enemy)))extra.counter_enemy=NONE;
    if(extra.guard_strain&&now>extra.guard_strain_until)extra.guard_strain=0;
    /* Test66: an Elite answers a flurry with its own (native) swing a fifth
     * of a second on, unless staggered, held or out of reach: the swing
     * opens the counter window like any other (blocked, parried, countered) */
    if(extra.answer_unit!=NONE&&now>=extra.answer_at){
        long elite=extra.answer_unit;
        extra.answer_unit=NONE;
        if(extra_enemy(unit,elite)&&!vr_combat_stunned(elite)&&!vr_npc_interaction_owned(elite)&&
           combat_gap(unit,elite)<=2.2f*units&&unit_melee_attack_begin(elite,FALSE,NULL)){
            extra.answer_ready=now+(5*TICKS_PER_SECOND)/2;
            platform_log("VR fist combat: enemy=%ld answers the flurry with a swing (block, parry or counter it)",elite);
        }
    }
    if(extra.countered!=NONE&&now>=extra.countered_until)extra.countered=NONE;
    if(extra.strike_pending){
        if(!extra_enemy(unit,extra.target)){extra.strike_pending=0;}
        else{
            real gap=combat_gap(unit,extra.target),stop=combat_stop(unit,extra.target);
            if(gap<=stop+.35f*units){
                real_vector3d along;
                vector_from_points3d(&unit_get(unit)->object.position,&unit_get(extra.target)->object.position,&along);
                along.k=0;
                if(normalize3d(&along)<.0001f)along=extra.strike_dir;
                int was_counter=extra.strike_counter;real metres=extra.lunge_metres;long target=extra.target;
                extra.strike_dir=along;
                extra.strike_pending=0;extra.approach_until=0;
                if(unit_vr_combat_strike(unit,target,&along,extra.strike_scale)){
                    extra_pulse(extra.strike_hand,1.0f,.08f);
                    platform_log("VR fist combat: %s landed enemy=%ld hand=%d after a %.1f m lunge (combo %d)",
                        was_counter?"counter":"lunge blow",target,extra.strike_hand,(float)metres,extra.combo);
                }else platform_log("VR fist combat: the %s found nothing at enemy=%ld",was_counter?"counter":"lunge blow",target);
                extra.strike_counter=0;
            }else if(now>extra.strike_issued+TICKS_PER_SECOND||(extra.approach_until<=now&&now>extra.strike_issued+3)){
                extra.strike_pending=0;
                platform_log("VR fist combat: the lunge stopped %.1f m short of enemy=%ld (blocked or cancelled)",
                    (float)((gap-stop)/units),extra.target);
            }
        }
    }
    if(extra.knock_pending){
        long target=extra.knock_target;
        extra.knock_pending=0;extra.knock_target=NONE;
        /* (a body knocked down is the NPC module's while it lies there: its
         * controls held, up within NPC RECOVERY; no stun of its own, which
         * would make every knockdown a rear takedown) */
        if(target!=NONE&&unit_try_and_get(target)&&!TEST_FLAG(unit_get(target)->object.damage_flags,_object_dead_bit))
            vr_npc_interaction_knock(target,&extra.knock_point,&extra.knock_dir,extra.knock_speed);
    }
}
void vr_extra_tick(long unit)
{
    long now=game_time_get();real units=vr_units_per_metre();real_point3d camera,slots[2];
    if(unit==NONE||unit!=extra_player(TRUE)||!(units>0&&units<10)||
        (!config_boolean("vr.physical_grenades")&&!extra_combat_on())){vr_extra_reset();return;}
    if(extra.unit!=unit||now<extra.tick||now>extra.tick+1)vr_extra_reset();
    if(extra.tick==now)return;
    extra.unit=unit;extra.tick=now;
    /* Test63: the camera the hands and slots are drawn from (manual reload's
     * walking fix); the tick's own camera when no frame is recent */
    if(!vr_render_drawn_camera(camera.n))unit_get_camera_position(unit,&camera);
    if(extra.target!=NONE){
        real_point3d head;real_vector3d gaze,up,delta;
        boolean keep=extra_combat_on()&&extra_enemy(unit,extra.target)&&now<=extra.lock_until;
        if(keep){
            /* Test65: the head as the last frame saw it (this tick runs
             * before the frame's own: vr_head_view_recent), within the lunge's
             * reach and a metre */
            real_point3d chest=combat_chest(extra.target);
            vector_from_points3d(&camera,&chest,&delta);
            keep=magnitude3d(&delta)<(combat_reach()+1.0f)*units&&normalize3d(&delta)>0.001f&&
                vr_head_view_recent(camera.n,unit_get(unit)->object.forward.n,head.n,gaze.n,up.n)&&
                dot_product3d(&gaze,&delta)>.25f&&
                extra_visible(unit,extra.target,&camera,&chest);
        }
        if(!keep){extra.target=NONE;extra.hit_count=0;extra.stun_until=extra.approach_until=extra.hold_until=0;extra.strike_pending=0;}
        /* Test63: a hand that grabs or climbs takes over from the assist */
        for(int h=0;h<2;h++){
            int o=vr_interaction_owner(h);
            if(o==VR_INTERACTION_NPC||o==VR_INTERACTION_WORLD||o==VR_INTERACTION_PARKOUR){
                if(extra.approach_until||extra.hold_until)platform_log("VR fist combat: hand %d grabbed; the assist lets go",h);
                extra.approach_until=extra.hold_until=0;
            }
        }
    }
    if(extra_combat_on()){
        combat_tick(unit);
        /* Test66: PARRY: a hand swiped hard (an open hand or the forearm;
         * a closed fist toward the attacker is a COUNTER) while an enemy's
         * swing is coming; the blow it meets in the next fifth of a second
         * is parried (vr_combat_defend) */
        if(extra.counter_enemy!=NONE&&now<=extra.counter_until)
            for(int h=0;h<2;h++){
                real speed=vr_hand_speed(h),threshold=vr_melee_speed();
                if(!(isfinite(threshold)&&threshold>0))threshold=2.0f;
                if(isfinite(speed)&&speed>=MAX(1.8f,.6f*threshold))extra.parry_tick[h]=now;
            }
    }
    if(!config_boolean("vr.physical_grenades")||!chest_points(unit,&camera,slots)){
        for(int h=0;h<2;h++){extra.hand[h].held=extra.hand[h].samples=0;extra.hand[h].down=1;vr_interaction_release(h,VR_INTERACTION_GRENADE);}return;
    }
    for(int h=0;h<2;h++){
        real_point3d point;real_vector3d f,u;
        int held=vr_interaction_grip(h,NULL,NULL),press=held&&!extra.hand[h].down;
        int release=!held&&extra.hand[h].down;
        int owner=vr_interaction_owner(h);
        extra.hand[h].down=held;
        /* Ownership clears when tracking/recentering/menu state invalidates the
         * hold. A lost claim is cancellation, never a physical release. */
        if((h==vr_weapon_hand()&&!vr_hand_empty())||
            (extra.hand[h].held&&owner!=VR_INTERACTION_GRENADE)||
            (owner!=VR_INTERACTION_NONE&&owner!=VR_INTERACTION_GRENADE)||
            !vr_hand_pose(h,camera.n,point.n,f.n,u.n)){
            extra.hand[h].held=extra.hand[h].samples=0;extra.hand[h].down=1;
            vr_interaction_release(h,VR_INTERACTION_GRENADE);continue;
        }
        /* Three cm into the palm includes rotational release momentum. */
        point_from_line3d(&point,&f,.03f*units,&point);
        if(extra.hand[h].held){
            real_vector3d step;vector_from_points3d(&extra.hand[h].last,&point,&step);
            if(magnitude3d(&step)>.65f*units||!valid_real_vector3d(&step)){
                extra.hand[h].held=extra.hand[h].samples=0;extra.hand[h].down=1;
                vr_interaction_release(h,VR_INTERACTION_GRENADE);continue;
            }
            extra.hand[h].velocity[2]=extra.hand[h].velocity[1];
            extra.hand[h].velocity[1]=extra.hand[h].velocity[0];extra.hand[h].velocity[0]=step;
            extra.hand[h].samples=MIN(3,extra.hand[h].samples+1);
            extra.hand[h].point=extra.hand[h].last=point;
            if(release){
                real_vector3d velocity={0};real total=0;
                real weights[3]={.6f,.3f,.1f};
                for(int s=0;s<extra.hand[h].samples;s++){
                    total+=weights[s];for(int k=0;k<3;k++)velocity.n[k]+=extra.hand[h].velocity[s].n[k]*weights[s];
                }
                if(total>0)scale_vector3d(&velocity,extra_bound("vr.grenade_throw_scale",1,.5f,2)/total,&velocity);
                real speed=magnitude3d(&velocity),cap=15.0f*units/TICKS_PER_SECOND;
                if(speed>cap)scale_vector3d(&velocity,cap/speed,&velocity);
                if(unit_vr_throw_grenade(unit,(short)extra.hand[h].type,&point,&velocity)){
                    extra.grenade_release_tick=now;
                    extra_pulse(h,.7f,.065f);
                    platform_log("VR physical grenade: released hand=%d type=%d speed=%.2f m/s count=%d",h,extra.hand[h].type,
                        (float)magnitude3d(&velocity)*TICKS_PER_SECOND/units,unit_get_grenade_count(unit,(short)extra.hand[h].type));
                }else platform_log("VR physical grenade: cancelled release; native state/count/collision rejected; ammo preserved");
                extra.hand[h].held=extra.hand[h].samples=0;vr_interaction_release(h,VR_INTERACTION_GRENADE);
            }
        }else{
            /* Test63: reached for with the palm drawn on screen (the owner's
             * Test62 hand closed on the slot and never took it: the test was
             * the controller's grip point), 12 cm round the slot's centre;
             * a light tick when a hand enters a slot; a near miss is logged */
            real_point3d palm=point;int best=-1;real nearest=1e9f;
            if(!vr_render_palm_point(h,unit,palm.n))palm=point;
            for(int type=0;type<2;type++){
                real_vector3d delta;vector_from_points3d(&palm,&slots[type],&delta);
                int reserved=extra.hand[1-h].held&&extra.hand[1-h].type==type;
                real distance=magnitude3d(&delta);
                if(unit_get_grenade_count(unit,(short)type)>reserved&&distance<nearest){nearest=distance;best=type;}
            }
            {
                int hover=best>=0&&nearest<=.12f*units;
                if(hover&&!extra.hand[h].hover&&!held)vr_haptic(h,.18f,.02f); /* a hint, not an event */
                extra.hand[h].hover=hover;
            }
            if(press&&best>=0&&nearest<=.12f*units&&vr_interaction_claim(h,VR_INTERACTION_GRENADE)){
                extra.hand[h].held=1;extra.hand[h].type=best;extra.hand[h].samples=0;extra.hand[h].hover=0;
                extra.hand[h].last=extra.hand[h].point=point;extra_pulse(h,.45f,.04f);
                platform_log("VR physical grenade: grabbed chest slot type=%d hand=%d %.1f cm from it (unarmed until released)",
                    best,h,(float)(nearest/units*100.0f));
            }else if(press&&best>=0&&nearest<=.35f*units)
                platform_log("VR physical grenade: not taken by hand %d: %.1f cm from the %s slot (reach 12 cm)%s",
                    h,(float)(nearest/units*100.0f),best?"plasma":"frag",
                    owner!=VR_INTERACTION_NONE&&owner!=VR_INTERACTION_GRENADE?" (hand busy)":"");
        }
    }
}
/* Test65: Arkham Shadow's fist combat. Camouflaj's design rule was that
 * Batman "punches across the room": the opening punch, a closed fist aimed
 * at a thug, carries the player to him and lands; then a flurry of lefts and
 * rights builds a combo meter, which a hit taken breaks; an attacker's
 * swing shows a blue warning and a punch toward him counters it; a full
 * meter's hard punch is a takedown. Here: a deliberate punch (a closed fist
 * faster than MELEE SPEED) picks the enemy the head looks at or the fist is
 * thrown at, within LUNGE (6 m by default; FIST REACH's short step when
 * off), in sight; out of reach, a Spartan dash (up to 10 m/s) carries the
 * player there and the blow lands on arrival. Test63 never acquired: the
 * head was refused to this tick (vr_head_view_recent). */
static void combat_engage(long unit,long target,int hand,boolean counter)
{
    long now=game_time_get();real units=vr_units_per_metre();
    real gap=combat_gap(unit,target),stop=combat_stop(unit,target);
    real speed=vr_hand_speed(hand),threshold=vr_melee_speed(),scale;
    real_vector3d along;
    if(!(isfinite(threshold)&&threshold>0))threshold=2.0f;
    scale=PIN(speed/(2.0f*threshold)+.25f,.5f,1.5f);
    if(extra.target!=target)extra.hit_count=0;
    extra.target=target;extra.lock_until=now+3*TICKS_PER_SECOND;
    vector_from_points3d(&unit_get(unit)->object.position,&unit_get(target)->object.position,&along);along.k=0;
    if(normalize3d(&along)<.0001f)along=unit_get(unit)->object.forward;
    extra.strike_dir=along;extra.strike_hand=hand;extra.strike_counter=counter;
    extra.strike_scale=scale*(counter?1.5f:1.0f);
    if(counter){
        extra.countered=target;extra.countered_until=now+TICKS_PER_SECOND;extra.counter_enemy=NONE;
        extra_pulse(hand,.8f,.05f);
    }
    if(isfinite(gap)&&gap-stop>.15f*units){
        real metres=(gap-stop)/units;
        extra.lunge_metres=metres;
        extra.approach_until=now+(long)ceilf(PIN(metres/10.0f+.15f,.25f,.9f)*(real)TICKS_PER_SECOND);
        extra.hold_until=extra.approach_until+TICKS_PER_SECOND/2;
        extra.strike_pending=1;extra.strike_issued=now;
        platform_log("VR fist combat: %s enemy=%ld hand=%d, a %.1f m lunge (combo %d)",counter?"COUNTER, lunging to":"lunge to",
            target,hand,(float)metres,extra.combo);
    }else{
        extra.lunge_metres=0;
        /* in reach: the fist's own sweep strikes; a counter lands at once */
        if(counter){extra.strike_pending=1;extra.strike_issued=now;}
        platform_log("VR fist combat: %s enemy=%ld hand=%d at %.2f m (in reach, combo %d)",counter?"COUNTER":"punch acquired",
            target,hand,(float)(gap/units),extra.combo);
    }
}
void vr_combat_punch(long unit,int hand,real_point3d const *point,real_vector3d const *sweep)
{
    struct object_iterator it;struct unit_datum *u;real_point3d camera,head;
    real_vector3d gaze,up,punch=*sweep,level;real units=vr_units_per_metre();
    long choice=NONE,now=game_time_get();real best=-1e9f,reach=combat_reach()*units;
    int seen=0;real nearest=1e9f,nearest_angle=0;int nearest_visible=0;
    boolean level_punch;
    if(!extra_combat_on()||unit!=extra_player(TRUE)||!(units>0))return;
    if(unit!=extra.unit){combat_reason("the combat tick has not run for this body yet");return;}
    if(hand<0||hand>1||!vr_physical_melee_hand_allowed(hand)||(hand==vr_weapon_hand()&&!vr_hand_empty()))return;
    /* one acquisition per punch: the sweep runs every tick of it */
    if(extra.target!=NONE&&now<extra.approach_until)return;
    if(!vr_render_drawn_camera(camera.n))unit_get_camera_position(unit,&camera);
    if(!vr_head_view_recent(camera.n,unit_get(unit)->object.forward.n,head.n,gaze.n,up.n)){combat_reason("no tracked head");return;}
    level=punch;level.k=0;
    level_punch=normalize3d(&level)>.0001f&&magnitude3d(sweep)>.0001f;
    /* COUNTERS: a punch toward the attacker whose swing is warned counters it */
    if(combat_counters_on()&&extra.counter_enemy!=NONE&&now<=extra.counter_until&&extra_enemy(unit,extra.counter_enemy)){
        real_vector3d to,to_level;real_point3d chest=combat_chest(extra.counter_enemy);
        vector_from_points3d(&head,&chest,&to);
        to_level=to;to_level.k=0;
        if(normalize3d(&to)>.001f&&normalize3d(&to_level)>.001f&&
           ((level_punch&&dot_product3d(&level,&to_level)>.2f)||dot_product3d(&gaze,&to)>.5f)){
            combat_engage(unit,extra.counter_enemy,hand,TRUE);
            return;
        }
    }
    object_iterator_new(&it,_object_mask_biped,0);
    while((u=object_iterator_next(&it))!=NULL){
        real_vector3d delta,from_hand,delta_level;real distance,facing,thrown=-1,score;boolean visible;
        real_point3d chest;
        if(!extra_enemy(unit,it.index))continue;
        chest=combat_chest(it.index);
        vector_from_points3d(&head,&chest,&delta);distance=normalize3d(&delta);
        if(distance<.001f||distance>reach+.75f*units)continue;
        facing=dot_product3d(&gaze,&delta);
        delta_level=delta;delta_level.k=0;
        if(level_punch&&normalize3d(&delta_level)>.001f)thrown=dot_product3d(&level,&delta_level);
        visible=extra_visible(unit,it.index,&head,&chest);
        seen++;
        if(distance<nearest){nearest=distance;nearest_angle=acosf(PIN(facing,-1,1))*57.29578f;nearest_visible=visible;}
        /* looked at (45 degrees), or the fist thrown at it (37) and not
         * behind the head (70) */
        if(distance>reach||!visible||!(facing>=.70f||(thrown>=.80f&&facing>=.35f)))continue;
        /* not behind the punch: a hook or a hand past the target's centre
         * still counts; a punch back and away does not */
        vector_from_points3d(point,&chest,&from_hand);from_hand.k=0;
        if(level_punch&&normalize3d(&from_hand)>.0001f&&dot_product3d(&level,&from_hand)<-.2f)continue;
        score=2.0f*MAX(facing,thrown)-distance/reach+(it.index==extra.target?.35f:0);
        if(score>best){best=score;choice=it.index;}
    }
    if(choice!=NONE)combat_engage(unit,choice,hand,FALSE);
    else if(now-extra.punch_logged>=TICKS_PER_SECOND||now<extra.punch_logged){
        extra.punch_logged=now;
        if(seen)platform_log("VR fist combat: punch took no target (nearest enemy %.2f m from the eyes, %.0f deg from the gaze, %s; reach %.2f m, cone 45 deg)",
            (float)(nearest/units),(float)nearest_angle,nearest_visible?"in sight":"not in sight",(float)(reach/units));
        else platform_log("VR fist combat: punch took no target (no enemy within %.1f m)",(float)(reach/units));
    }
}
/* Test65: an enemy's swing (units.c unit_melee_attack_begin) at the player,
 * within 4 m and facing him, opens a counter window until its blow lands
 * (three quarters of a second): a blue warning over its head and a double
 * tap in both hands; a punch toward it counters (vr_combat_punch) */
void vr_combat_note_melee(long attacker)
{
    long unit=extra.unit,now=game_time_get();real units=vr_units_per_metre();
    real_vector3d to;
    if(!extra_combat_on()||!combat_counters_on()||unit==NONE||unit!=extra_player(FALSE)||!(units>0)||
       !extra_enemy(unit,attacker))return;
    vector_from_points3d(&unit_get(attacker)->object.position,&unit_get(unit)->object.position,&to);
    if(magnitude3d(&to)>4.0f*units||normalize3d(&to)<.001f||dot_product3d(&to,&unit_get(attacker)->object.forward)<.3f)return;
    extra.counter_enemy=attacker;extra.counter_until=now+(3*TICKS_PER_SECOND)/4;
    extra_pulse(0,.35f,.03f);extra_pulse(1,.35f,.03f);
    platform_log("VR fist combat: counter window enemy=%ld at %.1f m (punch toward it)",attacker,
        (float)(combat_gap(unit,attacker)/units));
}
/* Test65: a hit taken breaks the combo (Arkham's meter) */
void vr_combat_note_damage(long object)
{
    if(object==NONE||object!=extra.unit||!extra.combo)return;
    if(extra.combo>=3)platform_log("VR fist combat: combo of %d broken (the player was hit)",extra.combo);
    extra.combo=0;
}
real vr_combat_hit(long unit,long target,real_point3d const *point,real_vector3d const *direction,real scale,boolean armed)
{
    real units=vr_units_per_metre();real_point3d head;real_vector3d delta,behind,along;
    long now=game_time_get();real result;
    boolean takedown=FALSE,special_ready,rear;
    struct combat_kind const *kind;real_point3d target_head,target_chest;real front;
    if(armed||!extra_combat_on()||unit!=extra_player(TRUE)||
        !extra_enemy(unit,target)||!(units>0))return 1;
    kind=combat_kind(target);
    combat_regions(target,&target_head,&target_chest);
    if(extra.target!=target){extra.hit_count=0;extra.stun_until=0;}
    extra.target=target;extra.lock_until=now+3*TICKS_PER_SECOND;
    extra.hold_until=MAX(extra.hold_until,now+TICKS_PER_SECOND/2);
    extra.hit_point=*point;extra.flash_until=now+6;
    special_ready=extra.combo>=COMBAT_SPECIAL;
    /* the combo meter: one count a punch (the sweep's probes strike in one tick) */
    if(now-extra.last_strike_tick>=3||now<extra.last_strike_tick){
        extra.combo=now<=extra.combo_until?extra.combo+1:1;
        extra.last_strike_tick=now;
        if(extra.combo==COMBAT_SPECIAL){extra_pulse(0,.5f,.04f);extra_pulse(1,.5f,.04f);
            platform_log("VR fist combat: combo %d, takedown ready (a hard punch)",extra.combo);}
    }
    extra.combo_until=now+2*TICKS_PER_SECOND;
    along=direction?*direction:unit_get(unit)->object.forward;
    if(normalize3d(&along)<.0001f)along=unit_get(unit)->object.forward;
    vector_from_points3d(&unit_get(target)->object.position,&unit_get(unit)->object.position,&behind);
    normalize3d(&behind);
    /* where the blow meets the enemy: from its front (1), its back (-1) */
    front=dot_product3d(&behind,&unit_get(target)->object.forward);
    rear=now<extra.stun_until&&front<-.55f;
    if(rear&&kind->type==_actor_hunter&&now>=extra.countered_until)rear=FALSE; /* a Hunter: a parried one only */
    if(rear||(special_ready&&scale>=1.0f&&(kind->type!=_actor_hunter||front<0))){
        takedown=TRUE;
        platform_log("VR fist combat: %s TAKEDOWN enemy=%ld (combo %d; native melee damage x6)",rear?"rear":"combo",target,extra.combo);
        extra.combo=0;extra.stun_until=0;extra.hit_count=0;
        extra_pulse(0,1.0f,.09f);extra_pulse(1,1.0f,.09f);
        extra.damage_share=6.0f;
    }else{
        /* ENEMY HEALTH: enemies take that many more punches; the combo
         * builds the blows back up (8% a hit, at most +80%); a Jackal's
         * shield and a Hunter's armour take most of a blow from the front */
        real armour=front>.35f?kind->front_share:front<-.35f?kind->back_share:1.0f;
        if(kind->type==_actor_jackal&&now<extra.stun_until)armour=1.0f;
        extra.damage_share=(1.0f+.08f*(real)MIN(extra.combo-1,10))/combat_health()*armour;
        head=target_head;vector_from_points3d(point,&head,&delta);
        if(kind->stun_hits<99&&(++extra.hit_count>=kind->stun_hits||
            (magnitude3d(&delta)<.22f*units&&(kind->type!=_actor_elite||unit_get(target)->object.shield_vitality<=0)))){
            extra.stun_until=now+(9*TICKS_PER_SECOND)/10;extra.hit_count=0;
            platform_log("VR fist combat: enemy=%ld stunned 0.9 s; rear hit or physical grab available",target);
        }
        /* an Elite struck twice in a second and a half answers */
        if(kind->answers&&now>=extra.answer_ready&&now>=extra.stun_until){
            if(extra.flurry_unit!=target||now>extra.flurry_until){extra.flurry_unit=target;extra.flurry_hits=0;}
            extra.flurry_until=now+(3*TICKS_PER_SECOND)/2;
            if(++extra.flurry_hits>=2){extra.answer_unit=target;extra.answer_at=now+6;extra.flurry_hits=0;}
        }
    }
    extra.share_tick=now;
    result=1.0f; /* the swing's own strength stays the damage scale */
    /* the body answers the blow: knocked down by a takedown, a counter, a
     * long lunge's blow or a hard punch to a stunned enemy (a short
     * ragdoll); otherwise shoved along the punch */
    {
        real knock=takedown?6.0f:(extra.strike_counter&&target==extra.countered)?3.5f:
            (extra.lunge_metres>=3.0f&&now-extra.strike_issued<=TICKS_PER_SECOND)?3.0f:
            (now<extra.stun_until&&scale>=1.2f)?3.0f:
            (kind->type==_actor_grunt&&extra.lunge_metres>=2.0f)?2.5f:0.0f;
        /* Test66: Elites only by a takedown or a counter; Hunters never */
        if(kind->type==_actor_hunter||(!kind->knocked&&!takedown&&!(extra.strike_counter&&target==extra.countered)))knock=0;
        if(knock>0&&config_boolean("vr.active_ragdoll")){
            extra.knock_pending=1;extra.knock_target=target;extra.knock_speed=knock;
            extra.knock_dir=along;extra.knock_point=*point;
        }else{
            struct object_definition *definition=object_definition_get(unit_get(target)->definition_index);
            real mobility=definition&&isfinite(definition->object.acceleration_scale)?PIN(definition->object.acceleration_scale,.2f,1.0f):.5f;
            real_vector3d shove;
            scale_vector3d(&along,PIN(scale,.5f,1.5f)*1.2f*mobility*units/(real)TICKS_PER_SECOND,&shove);
            shove.k=0;
            biped_accelerate(target,&shove);
        }
    }
    extra.lunge_metres=0;extra.strike_counter=0;
    return result;
}
/* Test66: the damage multiplier of this tick's fist blow (units.c), once */
real vr_combat_damage_share(void)
{
    real share=extra.share_tick==game_time_get()&&isfinite(extra.damage_share)&&extra.damage_share>0?extra.damage_share:1.0f;
    extra.damage_share=1.0f;extra.share_tick=NONE;
    return share;
}
/* Test66: BLOCK and PARRY, after Arkham Shadow's: an enemy's melee blow on
 * the player (damage.c, before it is dealt) meets a hand or forearm held up
 * between the face and the attacker (a guard: the blow is mostly stopped,
 * the guard tiring under blows in a row; never the whole of it), or a hand
 * swiped hard just before it lands (a parry: no damage, the attacker
 * staggered a second and open to a rear takedown or a grab). Returns the
 * share of the blow dealt (0: none). Only the assisted fists' player. */
real vr_combat_defend(long victim,long attacker)
{
    long now=game_time_get();real units=vr_units_per_metre();
    struct unit_datum *a;struct combat_kind const *kind;
    real_point3d camera,head,chest;real_vector3d to;int guard=-1,parry=-1;
    if(victim==NONE||victim!=extra.unit||attacker==NONE||!extra_combat_on()||!(units>0)||!extra_enemy(victim,attacker))return 1;
    a=unit_get(attacker);
    if(!a->unit.melee_attack_state&&!(attacker==extra.counter_enemy&&now<=extra.counter_until+3))return 1;
    if(!vr_render_drawn_camera(camera.n))unit_get_camera_position(victim,&camera);
    if(!combat_regions(attacker,&head,&chest))return 1;
    vector_from_points3d(&camera,&chest,&to);
    if(magnitude3d(&to)>3.5f*units||normalize3d(&to)<.001f)return 1;
    kind=combat_kind(attacker);
    for(int h=0;h<2;h++){
        real_point3d p;real_vector3d f,u,d;real distance;
        if(!vr_hand_pose(h,camera.n,p.n,f.n,u.n))continue;
        vector_from_points3d(&camera,&p,&d);distance=normalize3d(&d);
        if(distance<.10f*units||distance>.60f*units||dot_product3d(&d,&to)<.35f)continue;
        if(extra.parry_tick[h]>0&&now>=extra.parry_tick[h]&&now-extra.parry_tick[h]<=6)parry=h;
        /* a guard: raised to the face (within 30 cm of the eyes' height), squarely between */
        if(p.z>camera.z-.30f*units&&distance<=.55f*units&&dot_product3d(&d,&to)>=.5f)guard=h;
    }
    if(parry>=0){
        extra.countered=attacker;extra.countered_until=now+TICKS_PER_SECOND;extra.counter_enemy=NONE;
        extra.target=attacker;extra.lock_until=now+3*TICKS_PER_SECOND;extra.stun_until=now+TICKS_PER_SECOND;extra.hit_count=0;
        extra.parry_tick[0]=extra.parry_tick[1]=0;
        extra_pulse(parry,1.0f,.07f);extra_pulse(1-parry,.5f,.04f);
        if(kind->knocked&&config_boolean("vr.active_ragdoll")){
            real_vector3d back=to;back.k=0;
            if(normalize3d(&back)>.001f){extra.knock_pending=1;extra.knock_target=attacker;extra.knock_speed=2.5f;extra.knock_dir=back;extra.knock_point=chest;}
        }
        platform_log("VR fist combat: PARRY enemy=%ld hand=%d; its blow undone, staggered a second (punch, grab or go behind it)",attacker,parry);
        return 0;
    }
    if(guard>=0){
        real share=PIN(kind->block_share+.15f*(real)extra.guard_strain,0,1);
        real_vector3d push=to;
        extra.guard_strain=MIN(extra.guard_strain+1,4);extra.guard_strain_until=now+3*TICKS_PER_SECOND;
        extra_pulse(guard,.75f,.05f);
        /* the attacker rocked back a little by the guard */
        push.k=0;
        if(normalize3d(&push)>.001f&&kind->type!=_actor_hunter){
            scale_vector3d(&push,1.2f*units/(real)TICKS_PER_SECOND,&push);biped_accelerate(attacker,&push);
        }
        platform_log("VR fist combat: BLOCKED enemy=%ld with hand %d; %.0f%% of the blow taken (guard strain %d)",
            attacker,guard,(float)(share*100.0f),extra.guard_strain);
        return share;
    }
    return 1;
}
/* Both fresh attacks and already-running animation callbacks consult this
 * same bounded authority/target check. No AI animation state is frozen.
 * Test65: a countered attacker too (its swing undone, a second's stagger). */
int vr_combat_stunned(long unit)
{
    long now=game_time_get();
    if(!extra_combat_on()||extra.unit!=extra_player(TRUE)||extra.tick==NONE||now<extra.tick||now>extra.tick+1||
       !extra_enemy(extra.unit,unit)||vr_npc_interaction_restrained(unit))return FALSE;
    if(unit==extra.countered&&now<extra.countered_until&&extra.countered_until-now<=TICKS_PER_SECOND)return TRUE;
    return unit==extra.target&&now<extra.stun_until&&extra.stun_until-now<=(9*TICKS_PER_SECOND)/10;
}
void vr_combat_controls(long unit)
{
    if(vr_combat_stunned(unit)){
        struct unit_datum *u=unit_get(unit);
        u->unit.throttle=*global_zero_vector3d;u->unit.primary_trigger=0;
        u->unit.control_flags&=~(FLAG(_unit_control_weapon_primary_trigger_bit)|FLAG(_unit_control_throw_grenade_bit)|
            FLAG(_unit_control_use_equipment_bit)|FLAG(_unit_control_jump_bit));
    }
}
void vr_combat_velocity(long unit,real_point3d const *position,real_vector3d *velocity)
{
    real units=vr_units_per_metre();long now=game_time_get();
    if(!extra_combat_on()||extra.unit!=extra_player(TRUE)||!extra_enemy(extra.unit,extra.target)||!(units>0))return;
    /* Test63: the target is slowed while the step closes and half a second
     * after a hit, never frozen for the whole lock (the owner: "do not
     * completely freeze the enemy"); its AI keeps running */
    if(unit==extra.target&&now<extra.hold_until&&!vr_npc_interaction_owned(unit)){
        velocity->i*=.35f;velocity->j*=.35f;return; /* gravity and native collision still run */
    }
    if(unit==extra.unit&&now<extra.approach_until){
        struct biped_datum *b=biped_try_and_get(unit);real_vector3d delta;
        char const *cancelled=NULL;
        /* Test65: the dash goes on over a bump (Test63 stopped at any
         * airborne tick) and past the stick's strafe; backing off, a grab or
         * a climb, or a target well above or below still stops it */
        if(!b)cancelled="no body";
        else if(b->unit.throttle.i<-.5f)cancelled="the stick backed off";
        else if(vr_interaction_owner(0)==VR_INTERACTION_PARKOUR||vr_interaction_owner(1)==VR_INTERACTION_PARKOUR||
            vr_interaction_owner(0)==VR_INTERACTION_NPC||vr_interaction_owner(1)==VR_INTERACTION_NPC)cancelled="a hand grabbed or climbed";
        boolean airborne=b&&TEST_FLAG(b->biped.flags,_biped_airborne_bit);
        real rise=0;
        if(!cancelled){
            vector_from_points3d(position,&unit_get(extra.target)->object.position,&delta);
            /* Test66: in the air (a jump, a wall run's leap, a climb's
             * launch) the dash also rises or dives to the enemy, up to 3 m
             * above or below; on the ground a metre and a fifth, as before */
            if(fabsf(delta.k)>(airborne?3.0f:1.2f)*units)cancelled=airborne?"the enemy is over 3 m above or below":"the enemy is over a metre above or below";
            rise=delta.k;
        }
        if(cancelled){
            extra.approach_until=0;
            platform_log("VR fist combat: lunge cancelled (%s)",cancelled);
            return;
        }
        delta.k=0;real distance=normalize3d(&delta);
        /* The render sphere includes an actor's height/equipment and may
         * stop a punch out of reach. Use the same pill widths as Halo's
         * body collision, including the player's optional close-contact width. */
        real_point3d unused_base;real unused_height,player_width,target_width;
        biped_get_physics_pill(extra.unit,&unused_base,&unused_height,&player_width);
        biped_get_physics_pill(extra.target,&unused_base,&unused_height,&target_width);
        if(!isfinite(player_width)||!isfinite(target_width)||player_width<0||target_width<0){
            extra.approach_until=0;return;
        }
        real stop=MAX(.55f*units,player_width+target_width+.05f*units);
        if(distance<=stop){extra.approach_until=0;return;}
        /* a Spartan's dash, up to 10 m/s, easing in to striking range */
        real speed=MIN(10.0f*units/TICKS_PER_SECOND,(distance-stop)*.6f);
        velocity->i=delta.i*speed;velocity->j=delta.j*speed;
        if(airborne){
            /* toward the enemy's own height (a downward blow falls at most as
             * fast as the dash, a rising one at half of it); gravity resumes
             * when the dash ends */
            velocity->k=PIN(rise*.35f,-10.0f*units/TICKS_PER_SECOND,5.0f*units/TICKS_PER_SECOND);
        }
    }
}
static void extra_shell(real_point3d const *p,real radius,real_argb_color const *color,boolean plasma)
{
    for(int ring=0;ring<5;ring++)for(int slice=0;slice<8;slice++){
        real_point3d q[4];
        for(int c=0;c<4;c++){
            real a=_pi*(real)(ring+(c==1||c==2))/5-_pi*.5f,b=2*_pi*(real)(slice+(c>=2))/8;
            q[c].x=p->x+radius*cosf(a)*cosf(b);q[c].y=p->y+radius*cosf(a)*sinf(b);
            q[c].z=p->z+radius*sinf(a)*(plasma?.9f:1.3f);
        }
        render_debug_polygon(q,4,color);
    }
}
/* Hands are posed before this pass. Hidden/unsupported rigs use tracking,
 * with the same native obstruction query as the eventual grenade release.
 * Include the shell's longest radius so its fallback cannot poke through a wall. */
static boolean extra_grenade_draw_point(long unit,int hand,real_point3d const *camera,real_point3d *point)
{
    real units=vr_units_per_metre();real_vector3d forward,up,ray;struct collision_result hit;
    if(hand<0||hand>1||!(units>0&&units<10)||!valid_real_point3d(camera))return FALSE;
    if(vr_render_palm_point(hand,unit,point->n))return TRUE;
    if(!vr_hand_pose(hand,camera->n,point->n,forward.n,up.n))return FALSE;
    point_from_line3d(point,&forward,.03f*units,point);
    vector_from_points3d(camera,point,&ray);
    if(!valid_real_vector3d(&ray))return FALSE;
    real distance=normalize3d(&ray),radius=.05f*units;
    if(distance<.0001f)return TRUE;
    real_vector3d sweep;scale_vector3d(&ray,distance+radius,&sweep);
    if(collision_test_vector(_collision_test_for_projectiles_flags,camera,&sweep,unit,&hit)){
        real incidence=fabsf(dot_product3d(&hit.plane.n,&ray));
        if(!isfinite(hit.t)||hit.t<0||hit.t>1||!isfinite(incidence)||incidence<.001f)return FALSE;
        real travel=PIN((distance+radius)*hit.t-radius/incidence,0,distance);
        point_from_line3d(camera,&ray,travel,point);
    }
    return valid_real_point3d(point);
}
/* Test63: a grenade type's own model (the globals' projectile: the frag's
 * and the plasma's), or NONE */
static long extra_grenade_model(int type)
{
    struct game_globals *globals=scenario_get_game_globals();
    struct game_globals_grenade *grenade;
    if(!globals||type<0||type>=globals->grenades.count)return NONE;
    grenade=TAG_BLOCK_GET_ELEMENT(&globals->grenades,type,struct game_globals_grenade);
    if(grenade->projectile.index==NONE)return NONE;
    return object_definition_get(grenade->projectile.index)->object.model.index;
}
static void extra_draw_grenade(long unit,int type,real_point3d const *at,real_vector3d const *forward,real_vector3d const *up,long id)
{
    real_matrix4x3 matrices[MAXIMUM_NODES_PER_MODEL];
    long model_index=extra_grenade_model(type);
    struct model *model;struct render_lighting *lighting;
    real radius=.06f*vr_units_per_metre(),pixels;
    if(model_index==NONE||!valid_real_point3d(at))return;
    model=model_definition_get(model_index);
    if(model->nodes.count<=0||model->nodes.count>MAXIMUM_NODES_PER_MODEL)return;
    model_get_node_matrices(model,matrices,at,forward,up);
    lighting=object_get_cached_render_lighting(unit,100.0f);
    if(!lighting)return;
    pixels=render_frustum_sphere_diameter_in_pixels(&render.frustum,at,radius);
    {
        /* the colours and functions an object passes: neutral (white, the
         * plasma's glow functions at rest), never NULL */
        static real_rgb_color colors[NUMBER_OF_OBJECT_CHANGE_COLORS];
        static real functions[NUMBER_OF_OUTGOING_OBJECT_FUNCTIONS];
        for(int c=0;c<NUMBER_OF_OBJECT_CHANGE_COLORS;c++)colors[c].red=colors[c].green=colors[c].blue=1.0f;
        render_model(model_index,pixels,matrices,NULL,colors,functions,lighting,at,radius,NULL,id,0,0);
    }
}
/* Drawn in the world model pass with the dropped magazines (render_objects.c):
 * the slots' grenades, and a held one in the palm, along the hand. */
void vr_extra_models_render(void)
{
    long unit=extra_player(FALSE);real units=vr_units_per_metre();
    real_point3d camera,slots[2];real_vector3d forward,up;
    up.i=0;up.j=0;up.k=1;
    if(unit==NONE||!(units>0&&units<10)||!config_boolean("vr.physical_grenades")||!VR_RENDER_EYE())return;
    if(!vr_render_drawn_camera(camera.n)||!chest_points(unit,&camera,slots)||!chest_forward(&camera,&forward))return;
    for(int type=0;type<2;type++){
        int reserved=(extra.hand[0].held&&extra.hand[0].type==type)+(extra.hand[1].held&&extra.hand[1].type==type);
        if(unit_get_grenade_count(unit,(short)type)>reserved)extra_draw_grenade(unit,type,&slots[type],&forward,&up,0x5B000000+type);
    }
    for(int h=0;h<2;h++)if(extra.unit==unit&&extra.hand[h].held&&vr_interaction_owner(h)==VR_INTERACTION_GRENADE){
        real_point3d point,grip;real_vector3d hf,hu;
        if(extra_grenade_draw_point(unit,h,&camera,&point)&&vr_hand_pose(h,camera.n,grip.n,hf.n,hu.n))
            extra_draw_grenade(unit,extra.hand[h].type,&point,&hf,&hu,0x5B000010+h);
    }
}
/* Called in the existing per-eye, depth-tested virtual-controls pass. */
int vr_extra_render(float const camera_position[3])
{
    long unit=extra_player(FALSE);real units=vr_units_per_metre();int drawn=0;
    real_point3d camera,slots[2];
    if(unit==NONE||!(units>0&&units<10))return 0;
    memcpy(camera.n,camera_position,sizeof(camera.n));
    /* Test63: the grenades are the game's own models (vr_extra_models_render,
     * in the object pass); this pass draws a placeholder shell only for a
     * map whose grenade has no model */
    if(config_boolean("vr.physical_grenades")&&chest_points(unit,&camera,slots)){
        for(int type=0;type<2;type++){
            int reserved=(extra.hand[0].held&&extra.hand[0].type==type)+(extra.hand[1].held&&extra.hand[1].type==type);
            real_argb_color color=type?(real_argb_color){1,.18f,.30f,.95f}:(real_argb_color){1,.30f,.38f,.13f};
            if(unit_get_grenade_count(unit,(short)type)>reserved&&extra_grenade_model(type)==NONE){extra_shell(&slots[type],.038f*units,&color,type);drawn=1;}
        }
        for(int h=0;h<2;h++)if(extra.unit==unit&&extra.hand[h].held&&vr_interaction_owner(h)==VR_INTERACTION_GRENADE&&
            extra_grenade_model(extra.hand[h].type)==NONE){
            real_point3d point;
            if(extra_grenade_draw_point(unit,h,&camera,&point)){
                real_argb_color color=extra.hand[h].type?(real_argb_color){1,.18f,.30f,.95f}:(real_argb_color){1,.30f,.38f,.13f};
                extra_shell(&point,.038f*units,&color,extra.hand[h].type);drawn=1;
            }
        }
    }
    /* Test65: COUNTERS: Arkham's blue warning over the attacker's head,
     * pulsing until its blow lands */
    if(extra_combat_on()&&combat_counters_on()&&extra.counter_enemy!=NONE&&game_time_get()<=extra.counter_until&&
       extra_enemy(unit,extra.counter_enemy)){
        real_point3d head;real_argb_color blue={1,.20f,.55f,1};
        real pulse=.06f+.015f*sinf((real)vr_pose_time()*18.0f);real_point3d chest;
        combat_regions(extra.counter_enemy,&head,&chest);head.z+=.25f*units;
        extra_shell(&head,pulse*units,&blue,TRUE);
        render_debug_sphere(TRUE,&head,(pulse+.05f)*units,&blue);
        drawn=1;
    }
    /* Test65: the combo meter: a light for each hit in a row over the target
     * (white, gold when a takedown is ready) */
    if(extra_combat_on()&&config_boolean("vr.combat_highlights")&&extra.combo>0&&game_time_get()<=extra.combo_until&&
       extra_enemy(unit,extra.target)){
        real_point3d head;real_vector3d to,across;int lights=MIN(extra.combo,COMBAT_SPECIAL);
        real_argb_color color=extra.combo>=COMBAT_SPECIAL?(real_argb_color){1,1,.78f,.15f}:(real_argb_color){1,.85f,.9f,1};
        real_point3d chest;
        combat_regions(extra.target,&head,&chest);head.z+=.33f*units;
        vector_from_points3d(&camera,&head,&to);to.k=0;
        cross_product3d(global_up3d,&to,&across);
        if(normalize3d(&across)>.0001f)
            for(int light=0;light<lights;light++){
                real_point3d p;
                point_from_line3d(&head,&across,((real)light-(real)(lights-1)*.5f)*.055f*units,&p);
                extra_shell(&p,.017f*units,&color,FALSE);drawn=1;
            }
    }
    if(extra_combat_on()&&config_boolean("vr.combat_highlights")&&
        extra_enemy(unit,extra.target)&&extra.tick==game_time_get()){
        real_point3d head;long now=game_time_get();
        real_argb_color color=now<extra.stun_until?(real_argb_color){.8f,1,.65f,.12f}:(real_argb_color){.6f,.18f,.8f,1};
        real_point3d chest;
        combat_regions(extra.target,&head,&chest);
        if(extra_visible(unit,extra.target,&camera,&head)){
            render_debug_sphere(TRUE,&head,.11f*units,&color);
            render_debug_sphere(TRUE,&chest,.15f*units,&color);
            if(now<extra.flash_until){real_argb_color flash={.8f,.6f,.9f,1};render_debug_sphere(TRUE,&extra.hit_point,(.04f+.012f*(6-(extra.flash_until-now)))*units,&flash);}
            drawn=1;
        }
    }
    return drawn;
}
/* Render-only additive reaction: the authored spine subtree tilts as a
 * rigid unit, so limb lengths remain unchanged. Original animation, damage
 * sounds, death/ragdoll poses and collision remain owned by Halo. */
real_matrix4x3 *vr_combat_render(long unit,real_matrix4x3 *stock)
{
    static real_matrix4x3 pose[MAXIMUM_NODES_PER_MODEL];
    struct unit_datum *u;
    struct object_definition *definition;
    struct model *model;
    short count,spine=NONE,n;
    real angle,c,s;real_vector3d axis;real_point3d pivot;
    long now=game_time_get();
    if(!stock||unit!=extra.target||!extra_combat_on()||
        extra.unit!=extra_player(FALSE)||!extra_enemy(extra.unit,unit)||vr_npc_interaction_owned(unit)||
        (now>=extra.flash_until&&now>=extra.stun_until))return stock;
    u=unit_get(unit);definition=object_definition_get(u->definition_index);
    if(definition->object.model.index==NONE)return stock;
    model=model_definition_get(definition->object.model.index);
    count=(short)(u->object.node_matrices.size/sizeof(*stock));
    if(count<=0||count>MAXIMUM_NODES_PER_MODEL||model->nodes.count!=count)return stock;
    for(n=0;n<count;n++){
        struct model_node *node=TAG_BLOCK_GET_ELEMENT(&model->nodes,n,struct model_node);
        if(strstr(node->name,"spine")){spine=n;break;}
    }
    if(spine==NONE)return stock;
    angle=now<extra.stun_until?.07f:0;
    if(now<extra.flash_until)angle+=.12f*(extra.flash_until-now)/6.0f;
    c=cosf(angle);s=sinf(angle);
    axis.i=-u->object.forward.j;axis.j=u->object.forward.i;axis.k=0;
    if(normalize3d(&axis)<.001f)return stock;
    pivot=stock[spine].position;memcpy(pose,stock,count*sizeof(*pose));
    for(n=0;n<count;n++){
        short parent=n,steps=0;
        for(;parent>=0&&parent<count&&parent!=spine&&steps<count;steps++)
            parent=TAG_BLOCK_GET_ELEMENT(&model->nodes,parent,struct model_node)->parent_node_index;
        if(parent!=spine||steps>=count)continue;
        real_vector3d p;vector_from_points3d(&pivot,&stock[n].position,&p);
        real_vector3d *vectors[4]={&p,&pose[n].forward,&pose[n].left,&pose[n].up};
        for(int v=0;v<4;v++){
            real_vector3d original=*vectors[v],cross;
            real dot=dot_product3d(&axis,&original);
            cross_product3d(&axis,&original,&cross);
            for(int k=0;k<3;k++)vectors[v]->n[k]=original.n[k]*c+cross.n[k]*s+axis.n[k]*dot*(1-c);
        }
        point_from_line3d(&pivot,&p,1,&pose[n].position);
    }
    return pose;
}
#endif
