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
} extra={.unit=NONE,.tick=NONE,.target=NONE,.grenade_release_tick=NONE};
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
void vr_extra_reset(void)
{
    for(int h=0;h<2;h++)vr_interaction_release(h,VR_INTERACTION_GRENADE);
    memset(&extra,0,sizeof(extra));extra.unit=extra.tick=extra.target=extra.grenade_release_tick=NONE;
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
            vector_from_points3d(&camera,&unit_get(extra.target)->object.bounding_sphere_center,&delta);
            keep=magnitude3d(&delta)<2.5f*units&&normalize3d(&delta)>0.001f&&
                vr_head_view(camera.n,unit_get(unit)->object.forward.n,head.n,gaze.n,up.n)&&
                dot_product3d(&gaze,&delta)>.25f&&extra_visible(unit,extra.target,&camera,&unit_get(extra.target)->object.bounding_sphere_center);
        }
        if(!keep){extra.target=NONE;extra.hit_count=0;extra.stun_until=extra.approach_until=extra.hold_until=0;}
        /* Test63: a hand that grabs or climbs takes over from the assist */
        for(int h=0;h<2;h++){
            int o=vr_interaction_owner(h);
            if(o==VR_INTERACTION_NPC||o==VR_INTERACTION_WORLD||o==VR_INTERACTION_PARKOUR){
                if(extra.approach_until||extra.hold_until)platform_log("VR fist combat: hand %d grabbed; the assist lets go",h);
                extra.approach_until=extra.hold_until=0;
            }
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
/* Test63: a deliberate punch (closed fist above MELEE SPEED) picks the
 * enemy the head looks at: within FIST REACH (2.5 m by default) of the
 * eyes, within ~45 degrees of the gaze, in sight, not behind the punch;
 * nearer to the gaze and nearer in distance wins, the current target a
 * little more (combo continuity, never a lock-out). Short of striking range
 * it starts a short Spartan step toward it (vr_combat_velocity). The owner's
 * Test62 punches never acquired (1.5 m reach, the punch's own line to the
 * target's centre required): why a punch takes nothing is logged now. */
void vr_combat_punch(long unit,int hand,real_point3d const *point,real_vector3d const *sweep)
{
    struct object_iterator it;struct unit_datum *u;real_point3d camera,head;
    real_vector3d gaze,up,punch=*sweep;real units=vr_units_per_metre();
    long choice=NONE,now=game_time_get();real best=-1e9f,choice_distance=0;
    int seen=0;real nearest=1e9f,nearest_angle=0;int nearest_visible=0;
    if(!extra_combat_on()||unit!=extra_player(TRUE)||unit!=extra.unit||
        hand<0||hand>1||!vr_physical_melee_hand_allowed(hand)||
        (hand==vr_weapon_hand()&&!vr_hand_empty())||!(units>0))return;
    /* one acquisition per punch: the sweep runs every tick of it */
    if(extra.target!=NONE&&now<extra.approach_until)return;
    if(!vr_render_drawn_camera(camera.n))unit_get_camera_position(unit,&camera);
    if(!vr_head_view(camera.n,unit_get(unit)->object.forward.n,head.n,gaze.n,up.n))return;
    {
        real reach=extra_bound("vr.combat_reach",2.5f,.75f,3)*units;
        real_vector3d level=punch;level.k=0;
        boolean level_punch=normalize3d(&level)>.0001f&&magnitude3d(sweep)>.0001f;
        object_iterator_new(&it,_object_mask_biped,0);
        while((u=object_iterator_next(&it))!=NULL){
            real_vector3d delta,from_hand;real distance,facing,score;boolean visible;
            if(!extra_enemy(unit,it.index))continue;
            vector_from_points3d(&head,&u->object.bounding_sphere_center,&delta);distance=normalize3d(&delta);
            if(distance<.001f||distance>reach+.75f*units)continue;
            facing=dot_product3d(&gaze,&delta);
            visible=extra_visible(unit,it.index,&head,&u->object.bounding_sphere_center);
            seen++;
            if(distance<nearest){nearest=distance;nearest_angle=acosf(PIN(facing,-1,1))*57.29578f;nearest_visible=visible;}
            if(distance>reach||facing<.70f||!visible)continue;
            /* not behind the punch: a hook or a hand past the target's centre
             * still counts; a punch back and away does not */
            vector_from_points3d(point,&u->object.bounding_sphere_center,&from_hand);from_hand.k=0;
            if(level_punch&&normalize3d(&from_hand)>.0001f&&dot_product3d(&level,&from_hand)<-.2f)continue;
            score=2.0f*facing-distance/reach+(it.index==extra.target?.35f:0);
            if(score>best){best=score;choice=it.index;choice_distance=distance;}
        }
    }
    if(choice!=NONE){
        real_point3d unused_base;real unused_height,player_width,target_width,stop,gap;
        real_vector3d level_delta;
        if(extra.target!=choice)extra.hit_count=0;
        extra.target=choice;extra.lock_until=now+2*TICKS_PER_SECOND;
        vector_from_points3d(&unit_get(unit)->object.position,&unit_get(choice)->object.position,&level_delta);
        level_delta.k=0;gap=magnitude3d(&level_delta);
        biped_get_physics_pill(unit,&unused_base,&unused_height,&player_width);
        biped_get_physics_pill(choice,&unused_base,&unused_height,&target_width);
        stop=MAX(.55f*units,player_width+target_width+.05f*units);
        if(isfinite(gap)&&gap-stop>.15f*units){
            extra.approach_until=now+(2*TICKS_PER_SECOND)/5;
            extra.hold_until=extra.approach_until+TICKS_PER_SECOND/2;
        }
        platform_log("VR fist combat: punch acquired enemy=%ld hand=%d at %.2f m (%s)",choice,hand,
            (float)(choice_distance/units),extra.approach_until>now?"short step in":"in reach");
    }else if(now-extra.punch_logged>=TICKS_PER_SECOND){
        extra.punch_logged=now;
        if(seen)platform_log("VR fist combat: punch took no target (nearest enemy %.2f m from the eyes, %.0f deg from the gaze, %s; reach %.2f m, cone 45 deg)",
            (float)(nearest/units),(float)nearest_angle,nearest_visible?"in sight":"not in sight",
            (float)extra_bound("vr.combat_reach",2.5f,.75f,3));
        else platform_log("VR fist combat: punch took no target (no enemy within reach)");
    }
}
real vr_combat_hit(long unit,long target,real_point3d const *point,boolean armed)
{
    real units=vr_units_per_metre();real_point3d head;real_vector3d delta,behind;
    long now=game_time_get();
    if(armed||!extra_combat_on()||unit!=extra_player(TRUE)||
        !extra_enemy(unit,target)||!(units>0))return 1;
    if(extra.target!=target){extra.hit_count=0;extra.stun_until=0;}
    extra.target=target;extra.lock_until=now+2*TICKS_PER_SECOND;
    extra.hold_until=MAX(extra.hold_until,now+TICKS_PER_SECOND/2);
    extra.hit_point=*point;extra.flash_until=now+6;
    vector_from_points3d(&unit_get(target)->object.position,&unit_get(unit)->object.position,&behind);
    normalize3d(&behind);
    if(now<extra.stun_until&&dot_product3d(&behind,&unit_get(target)->object.forward)<-.55f){
        extra.stun_until=0;extra.hit_count=0;
        platform_log("VR fist combat: rear takedown enemy=%ld (native melee damage x3; protected actors retain engine rules)",target);
        return 3;
    }
    unit_get_camera_position(target,&head);vector_from_points3d(point,&head,&delta);
    if(magnitude3d(&delta)<.22f*units||++extra.hit_count>=3){
        extra.stun_until=now+(9*TICKS_PER_SECOND)/10;extra.hit_count=0;
        platform_log("VR fist combat: enemy=%ld stunned 0.9 s; rear hit or physical grab available",target);
    }
    return 1;
}
/* Both fresh attacks and already-running animation callbacks consult this
 * same bounded authority/target check. No AI animation state is frozen. */
int vr_combat_stunned(long unit)
{
    long now=game_time_get();
    return unit==extra.target&&extra_combat_on()&&extra.unit==extra_player(TRUE)&&
        extra.tick!=NONE&&now>=extra.tick&&now<=extra.tick+1&&now<extra.stun_until&&
        extra.stun_until-now<=(9*TICKS_PER_SECOND)/10&&extra_enemy(extra.unit,unit)&&
        !vr_npc_interaction_restrained(unit);
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
        if(!b||TEST_FLAG(b->biped.flags,_biped_airborne_bit)||
            b->unit.throttle.i<-.2f||fabsf(b->unit.throttle.j)>.5f||
            vr_interaction_owner(0)==VR_INTERACTION_PARKOUR||vr_interaction_owner(1)==VR_INTERACTION_PARKOUR||
            vr_interaction_owner(0)==VR_INTERACTION_NPC||vr_interaction_owner(1)==VR_INTERACTION_NPC){
            extra.approach_until=0;return;
        }
        vector_from_points3d(position,&unit_get(extra.target)->object.position,&delta);
        if(fabsf(delta.k)>.45f*units){extra.approach_until=0;return;}
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
        /* Test63: a Spartan step, up to 5 m/s, easing in to striking range */
        real speed=MIN(5.0f*units/TICKS_PER_SECOND,(distance-stop)*.45f);
        velocity->i=delta.i*speed;velocity->j=delta.j*speed;
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
    render_model(model_index,pixels,matrices,NULL,NULL,NULL,lighting,at,radius,NULL,id,0,0);
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
    if(extra_combat_on()&&config_boolean("vr.combat_highlights")&&
        extra_enemy(unit,extra.target)&&extra.tick==game_time_get()){
        real_point3d head;long now=game_time_get();
        real_argb_color color=now<extra.stun_until?(real_argb_color){.8f,1,.65f,.12f}:(real_argb_color){.6f,.18f,.8f,1};
        unit_get_camera_position(extra.target,&head);
        if(extra_visible(unit,extra.target,&camera,&head)){
            render_debug_sphere(TRUE,&head,.13f*units,&color);
            render_debug_sphere(TRUE,&unit_get(extra.target)->object.bounding_sphere_center,.16f*units,&color);
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
