/* Original optional fist actions over Halo's native attacks and contacts.
 * No damage creation, camera attachment, teleport, collision flag, protocol,
 * animation-state write or heap allocation belongs to this module. */
#ifdef HALO_VR
#include "cseries.h"
#include "game/game.h"
#include "game/players.h"
#include "game/game_allegiance.h"
#include "units/units.h"
#include "units/bipeds.h"
#include "ai/actors.h"
#include "ai/actor_types.h"
#include "models/model_definitions.h"
#include "models/model_animation_definitions.h"
#include "objects/object_definitions.h"
#include "physics/collisions.h"
#include "vr_extra_interaction.h"
#include "vr_npc_interaction.h"
#include "vr_combat_moves.h"
#include "vr_combat_pose.h"
#include "../src/vr.h"
#include "../src/port_config.h"

#define MOVE_SLOTS VR_COMBAT_MOVE_TARGETS
#define MOVE_EVENTS 8
struct combat_move_state {
    long target,seen,attack_start,attack_until,graph,clip;
    short frames,key,key2;
    int kind,side,attacks,dodged;
    real_point3d head_start;
    real head_height;
    real_vector3d attack_right;
    long opening_start,opening_until,arm_pending_until,last_hit;
    int opening_kind,arm_hand,arm_side,pummelling;
    short arm_node;
    real_point3d arm_contact;
};
static struct {
    long owner,tick,airborne_at;
    struct combat_move_state slot[MOVE_SLOTS];
    struct vr_combat_move_event event[MOVE_EVENTS];
    int events;
    long consumed_object[2];
    short consumed_node[2];
} moves={.owner=NONE,.tick=NONE,.airborne_at=NONE};

static boolean move_authority(long owner)
{
    short local=local_player_get_next(NONE);
    long player=local!=NONE?local_player_get_player_index(local):NONE;
    return owner!=NONE&&config_boolean("vr.combat_moves")&&vr_combat_enabled()&&
        player!=NONE&&player_get(player)->unit_index==owner;
}
static boolean move_current(void)
{
    long now=game_time_get();
    return moves.tick!=NONE&&now>=moves.tick&&now<=moves.tick+1&&move_authority(moves.owner);
}
static boolean move_enemy(long target)
{
    struct unit_datum *p=unit_try_and_get(moves.owner),*u=unit_try_and_get(target);
    struct actor_datum *a=u&&u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
    return p&&u&&a&&a->meta.active&&u->object.type==_object_type_biped&&
        u->unit.player_index==NONE&&u->object.parent_object_index==NONE&&
        !TEST_FLAG(u->object.damage_flags,_object_dead_bit)&&!TEST_FLAG(u->unit.flags,_unit_suspended_bit)&&
        game_team_is_enemy(p->object.owner_team_index,a->meta.team_index);
}
static int move_species(long target)
{
    struct unit_datum *u=unit_try_and_get(target);
    struct actor_datum *a=u&&u->unit.actor_index!=NONE?actor_try_and_get(u->unit.actor_index):NULL;
    return a?a->meta.type:NONE;
}
static struct combat_move_state *move_slot(long target,boolean create)
{
    long now=game_time_get();int oldest=-1;
    if(target==NONE)return NULL;
    for(int i=0;i<MOVE_SLOTS;i++){
        struct combat_move_state *s=&moves.slot[i];
        if(s->target==target)return s;
        if(s->target==NONE){oldest=i;continue;}
        /* An idle entry may be replaced; an active opening/attack never loses
         * ownership because an unrelated crowd exhausted this optional pool. */
        if(s->attack_until>=now||s->opening_until>now||s->arm_pending_until>now)continue;
        if(oldest<0||(moves.slot[oldest].target!=NONE&&s->seen<moves.slot[oldest].seen))oldest=i;
    }
    if(!create||oldest<0)return NULL;
    struct combat_move_state *s=&moves.slot[oldest];
    memset(s,0,sizeof(*s));s->target=target;s->seen=now;s->arm_hand=-1;s->last_hit=NONE;
    return s;
}
static void move_event(int type,long target,int hand)
{
    if(moves.events<MOVE_EVENTS)moves.event[moves.events++]=(struct vr_combat_move_event){type,hand,target};
}
void vr_combat_moves_reset(void)
{
    memset(&moves,0,sizeof(moves));moves.owner=moves.tick=moves.airborne_at=NONE;
    for(int i=0;i<MOVE_SLOTS;i++){moves.slot[i].target=NONE;moves.slot[i].arm_hand=-1;}
    for(int h=0;h<2;h++){moves.consumed_object[h]=NONE;moves.consumed_node[h]=NONE;}
}
static boolean move_head(long owner,real_point3d *head)
{
    real_point3d camera;real_vector3d gaze,up;
    unit_get_camera_position(owner,&camera);
    return valid_real_point3d(&camera)&&
        vr_head_view_recent(camera.n,unit_get(owner)->object.forward.n,head->n,gaze.n,up.n)&&valid_real_point3d(head);
}
static boolean move_visible(long owner,long target,real_point3d const *from,real_point3d const *to)
{
    real_vector3d ray;struct collision_result hit;
    if(!valid_real_point3d(from)||!valid_real_point3d(to))return FALSE;
    vector_from_points3d(from,to,&ray);
    return !collision_test_vector(_collision_test_for_projectiles_flags,from,&ray,owner,&hit)||
        (hit.type==_collision_result_object&&hit.object_index==target);
}
static boolean move_clip(struct combat_move_state const *s,short *frame)
{
    struct unit_datum *u=unit_try_and_get(s->target);
    if(!u||u->object.animation.animation_graph_index!=s->graph||u->object.animation.state.index!=s->clip||
       (u->unit.animation.state!=_unit_state_melee_attack&&u->unit.animation.state!=_unit_state_melee_airborne&&
        u->unit.animation.state!=_unit_state_leap_melee))return FALSE;
    *frame=u->object.animation.state.frame_index;
    return *frame>=0&&*frame<s->frames;
}
/* Species policy applies only to these new arm/pummel openings. Native fists,
 * firearms, heavy requirements and native NPC physical ownership stay intact. */
static boolean move_control_allowed(long target)
{
    struct unit_datum *u=unit_get(target);int species=move_species(target);
    if(species==_actor_grunt)return TRUE;
    if(species==_actor_elite)return u->object.shield_vitality<=0||vr_combat_control_opening(target);
    if(species==_actor_jackal){
        real_vector3d to;vector_from_points3d(&u->object.position,&unit_get(moves.owner)->object.position,&to);
        to.k=0;
        return valid_real_vector3d(&to)&&normalize3d(&to)>.001f&&
            (dot_product3d(&to,&u->object.forward)<=.35f||vr_combat_control_opening(target));
    }
    return FALSE; /* Hunters and unsupported actor layouts keep native rules. */
}
/* Validate the exact acquired node by following its own authored ancestry.
 * A torso or leg hold never becomes arm control because a hand is nearby. */
static boolean move_arm(long target,short node,int *side)
{
    struct unit_datum *u=unit_try_and_get(target);struct object_definition *def;
    struct model *model;long count;boolean arm=FALSE,anchored=FALSE;
    if(!u)return FALSE;
    def=object_definition_get(u->definition_index);
    if(!def||def->object.model.index==NONE)return FALSE;
    model=model_definition_get(def->object.model.index);
    count=u->object.node_matrices.size/sizeof(real_matrix4x3);
    if(!model||count<=0||count>MAXIMUM_NODES_PER_MODEL||model->nodes.count!=count||node<=0||node>=count)return FALSE;
    *side=-1;
    for(short n=node,steps=0;n>0&&n<count&&steps<count;steps++){
        struct model_node *part=TAG_BLOCK_GET_ELEMENT(&model->nodes,n,struct model_node);
        char const *name=part->name;
        if(!memchr(name,0,sizeof(part->name)))return FALSE;
        if(strstr(name,"pelvis")||strstr(name,"spine")){anchored=TRUE;break;}
        if(strstr(name,"thigh")||strstr(name,"calf"))break;
        if(strstr(name,"upperarm")||strstr(name,"forearm")||strstr(name,"hand"))arm=TRUE;
        if(strstr(name," l "))*side=0;
        if(strstr(name," r "))*side=1;
        if(part->parent_node_index==n)return FALSE;
        n=part->parent_node_index;
    }
    return arm&&anchored&&*side>=0;
}
/* A missing NPC contact is cancellation unless the same tracked hand has
 * actually let go. Tracking, feature and interaction-owner loss are not a
 * release gesture, even when the physical rig drops its contact first. */
static boolean move_arm_input(long owner,int hand,int *grip)
{
    real_point3d camera,point;real_vector3d forward,up;
    if(hand<0||hand>1||!config_boolean("vr.npc_interaction")||!vr_hand_empty())return FALSE;
    unit_get_camera_position(owner,&camera);
    if(!valid_real_point3d(&camera)||!vr_hand_pose(hand,camera.n,point.n,forward.n,up.n)||
       !valid_real_point3d(&point)||!valid_real_vector3d(&forward)||!valid_real_vector3d(&up))return FALSE;
    *grip=vr_interaction_grip(hand,NULL,NULL);
    return TRUE;
}
void vr_combat_moves_tick(long owner)
{
    long now=game_time_get();real units=vr_units_per_metre();
    long held[2]={NONE,NONE};short nodes[2]={NONE,NONE};real_point3d contact[2];
    if(!move_authority(owner)||!(units>0&&units<10)){vr_combat_moves_reset();return;}
    if(owner!=moves.owner||moves.tick==NONE||now<moves.tick||now>moves.tick+1)vr_combat_moves_reset();
    if(moves.tick==now)return;
    moves.owner=owner;moves.tick=now;
    struct biped_datum *b=biped_try_and_get(owner);
    if(b&&TEST_FLAG(b->biped.flags,_biped_airborne_bit))moves.airborne_at=now;
    for(int h=0;h<2;h++){
        if(!vr_npc_interaction_contact(h,&held[h],&nodes[h],contact[h].n))held[h]=NONE;
        if(held[h]!=moves.consumed_object[h]||nodes[h]!=moves.consumed_node[h]){
            moves.consumed_object[h]=NONE;moves.consumed_node[h]=NONE;
        }
    }
    for(int i=0;i<MOVE_SLOTS;i++){
        struct combat_move_state *s=&moves.slot[i];short frame;
        if(s->target==NONE)continue;
        if(!move_enemy(s->target)){memset(s,0,sizeof(*s));s->target=NONE;s->arm_hand=-1;continue;}
        if(s->attack_until&&(!move_clip(s,&frame)||now>s->attack_until))s->attack_until=0;
        if(s->arm_pending_until){
            if(now>s->arm_pending_until){s->arm_pending_until=0;s->arm_hand=-1;}
            else{
                int h=s->arm_hand,grip=1;
                boolean input=move_arm_input(owner,h,&grip);
                int hand_owner=h>=0&&h<2?vr_interaction_owner(h):VR_INTERACTION_NONE;
                boolean same=h>=0&&h<2&&held[h]==s->target&&nodes[h]==s->arm_node;
                if(input&&grip&&same&&hand_owner==VR_INTERACTION_NPC)s->arm_contact=contact[h];
                else{
                    boolean released=input&&!grip&&(hand_owner==VR_INTERACTION_NONE||hand_owner==VR_INTERACTION_NPC)&&
                        (held[h]==NONE||same);
                    s->arm_pending_until=0;s->arm_hand=-1;
                    if(released){
                        s->opening_start=now;s->opening_until=now+TICKS_PER_SECOND;
                        s->opening_kind=VR_COMBAT_POSE_CLUTCH_KNEEL;
                    }
                }
            }
        }
        if(now>=s->opening_until)s->pummelling=0;
    }
}
void vr_combat_moves_note_melee(long owner,long attacker)
{
    struct unit_datum *u;struct animation_graph *graph;struct animation *clip;
    real_point3d head;real_vector3d to;real units=vr_units_per_metre();long now=game_time_get();int species,kind;
    if(!move_current()||owner!=moves.owner||!move_enemy(attacker)||!vr_hand_empty()||!(units>0&&units<10))return;
    species=move_species(attacker);
    if(species!=_actor_grunt&&species!=_actor_jackal&&species!=_actor_elite&&species!=_actor_hunter)return;
    u=unit_get(attacker);
    if(u->object.animation.animation_graph_index==NONE||!move_head(owner,&head))return;
    vector_from_points3d(&u->object.position,&unit_get(owner)->object.position,&to);to.k=0;
    real distance=normalize3d(&to);
    if(!isfinite(distance)||distance<.001f||distance>4*units||dot_product3d(&to,&u->object.forward)<.3f||
       !move_visible(owner,attacker,&head,&u->object.bounding_sphere_center))return;
    graph=animation_graph_definition_get(u->object.animation.animation_graph_index);
    if(!graph||u->object.animation.state.index<0||u->object.animation.state.index>=graph->animations.count)return;
    clip=TAG_BLOCK_GET_ELEMENT(&graph->animations,u->object.animation.state.index,struct animation);
    if(clip->frame_count<2||clip->frame_count>3*TICKS_PER_SECOND||clip->private_key_frame_index<0||
       clip->private_key_frame_index>=clip->frame_count)return;
    struct combat_move_state *s=move_slot(attacker,TRUE);
    if(!s)return;
    if(s->attack_start==now&&s->attack_until>now)return;
    kind=s->attacks++%3;
    if(species==_actor_hunter)kind=1;
    if(species==_actor_grunt&&kind==1)kind=2;
    s->kind=kind==0?VR_COMBAT_POSE_SWEEP:kind==1?VR_COMBAT_POSE_OVERHEAD:VR_COMBAT_POSE_JAB;
    s->side=(s->attacks&1);s->seen=s->attack_start=now;s->attack_until=now+clip->frame_count+2;s->dodged=0;
    s->graph=u->object.animation.animation_graph_index;s->clip=u->object.animation.state.index;
    s->frames=clip->frame_count;s->key=clip->private_key_frame_index;s->key2=clip->private_second_key_frame_index;
    s->head_start=head;s->head_height=head.z-unit_get(owner)->object.position.z;
    cross_product3d(global_up3d,&to,&s->attack_right);
    move_event(kind==0?VR_COMBAT_MOVE_ATTACK_SWEEP:kind==1?VR_COMBAT_MOVE_ATTACK_OVERHEAD:VR_COMBAT_MOVE_ATTACK_JAB,attacker,-1);
}
real vr_combat_moves_defend(long owner,long attacker)
{
    long now=game_time_get();real units=vr_units_per_metre();real_point3d head;real_vector3d delta;short frame;
    if(!move_current()||owner!=moves.owner||!move_enemy(attacker)||!vr_hand_empty()||!(units>0&&units<10))return 1;
    struct combat_move_state *s=move_slot(attacker,FALSE);
    if(!s||!s->attack_until||now>s->attack_until||!move_clip(s,&frame)||
       !unit_get(attacker)->unit.melee_attack_state||
       (abs(frame-s->key)>1&&(s->key2<0||abs(frame-s->key2)>1))||!move_head(owner,&head))return 1;
    if(vr_interaction_owner(0)!=VR_INTERACTION_NONE||vr_interaction_owner(1)!=VR_INTERACTION_NONE)return 1;
    /* Native contact damage may invoke more than one callback at its hit
     * keyframe. The same dodged swing stays avoided, without another reward. */
    if(s->dodged)return 0;
    vector_from_points3d(&s->head_start,&head,&delta);
    if(!valid_real_vector3d(&delta)||magnitude3d(&delta)>1.5f*units)return 1;
    real drop=s->head_height-(head.z-unit_get(owner)->object.position.z);
    real lateral=fabsf(dot_product3d(&delta,&s->attack_right));
    boolean dodge=s->kind==VR_COMBAT_POSE_SWEEP?drop>=.20f*units:
        (s->kind==VR_COMBAT_POSE_OVERHEAD||s->kind==VR_COMBAT_POSE_JAB)?lateral>=.22f*units:FALSE;
    if(!dodge)return 1;
    s->dodged=1;s->opening_start=now;s->opening_until=now+TICKS_PER_SECOND/2;
    s->opening_kind=VR_COMBAT_POSE_RECOIL;
    move_event(s->kind==VR_COMBAT_POSE_SWEEP?VR_COMBAT_MOVE_DUCK:VR_COMBAT_MOVE_SIDESTEP,attacker,-1);
    return 0;
}
void vr_combat_moves_note_hit(long owner,long target,real_point3d const *point,real_vector3d const *direction,real scale)
{
    real units=vr_units_per_metre();long now=game_time_get();real_point3d camera;
    if(!move_current()||owner!=moves.owner||!move_enemy(target)||!vr_hand_empty()||!(units>0&&units<10)||
       !point||!valid_real_point3d(point)||!direction||!valid_real_vector3d(direction)||!isfinite(scale)||
       scale<=0||!move_control_allowed(target))return;
    struct combat_move_state *s=move_slot(target,TRUE);
    if(!s||s->last_hit==now)return;
    s->last_hit=s->seen=now;
    unit_get_camera_position(owner,&camera);
    /* A real second-hand fist contact against the arm the first hand owns.
     * The acquired contact is stable; no enemy-root radius can authorize it. */
    for(int h=0;h<2;h++){
        long held;short node;int side;real_point3d contact,hand;real_vector3d f,u,to;
        int free_hand=1-h,grip=0;real speed=vr_hand_speed(free_hand),threshold=vr_melee_speed();
        if(vr_interaction_owner(h)!=VR_INTERACTION_NPC||!move_arm_input(owner,h,&grip)||!grip||
           !vr_npc_interaction_contact(h,&held,&node,contact.n)||held!=target||!move_arm(target,node,&side)||
           (moves.consumed_object[h]==target&&moves.consumed_node[h]==node)||
           !vr_physical_melee_hand_allowed(free_hand)||!isfinite(speed)||!isfinite(threshold)||
           threshold<=0||speed<threshold||!vr_hand_pose(free_hand,camera.n,hand.n,f.n,u.n)||!valid_real_point3d(&hand))continue;
        vector_from_points3d(&contact,point,&to);if(magnitude3d(&to)>.18f*units)continue;
        vector_from_points3d(point,&hand,&to);if(magnitude3d(&to)>.20f*units)continue;
        s->arm_hand=h;s->arm_node=node;s->arm_side=side;s->arm_contact=contact;
        s->arm_pending_until=now+2*TICKS_PER_SECOND;s->opening_start=now;s->opening_until=0;s->pummelling=0;
        moves.consumed_object[h]=target;moves.consumed_node[h]=node;
        move_event(VR_COMBAT_MOVE_ARM_OPENING,target,free_hand);return;
    }
    /* A leap-to-front pummel opening is earned by an actual downward contact
     * during a native jump/landing. Never seat/attach the player to an NPC. */
    if(vr_interaction_owner(0)!=VR_INTERACTION_NONE||vr_interaction_owner(1)!=VR_INTERACTION_NONE)return;
    real_vector3d along=*direction;
    if(normalize3d(&along)<.001f||along.k>-.25f||scale<.8f)return;
    real_vector3d separation;
    vector_from_points3d(&unit_get(target)->object.position,&unit_get(owner)->object.position,&separation);
    if(!valid_real_vector3d(&separation)||magnitude3d(&separation)>2.2f*units)return;
    boolean continuing=s->pummelling&&now<s->opening_until;
    struct biped_datum *b=biped_try_and_get(owner);
    if(!continuing&&(!b||moves.airborne_at==NONE||now<moves.airborne_at||now-moves.airborne_at>3||
       !valid_real_vector3d(&b->object.translational_velocity)||b->object.translational_velocity.k>0||separation.k<.25f*units))return;
    s->opening_start=now;s->opening_until=now+TICKS_PER_SECOND;s->opening_kind=VR_COMBAT_POSE_CLUTCH_KNEEL;s->pummelling=1;
    move_event(continuing?VR_COMBAT_MOVE_PUMMEL_HIT:VR_COMBAT_MOVE_PUMMEL_OPENING,target,-1);
}
int vr_combat_moves_opening(long target)
{
    long now=game_time_get();
    if(!move_current()||!move_enemy(target))return FALSE;
    struct combat_move_state *s=move_slot(target,FALSE);
    return s&&s->opening_until>now&&s->opening_until-now<=TICKS_PER_SECOND;
}
int vr_combat_moves_pose(long target,struct vr_combat_pose_request *out)
{
    long now=game_time_get();short frame;
    if(!out||!move_current()||!move_enemy(target)||vr_npc_interaction_owned(target))return FALSE;
    struct combat_move_state *s=move_slot(target,FALSE);
    if(!s)return FALSE;
    memset(out,0,sizeof(*out));out->forward=unit_get(target)->object.forward;
    if(!valid_real_vector3d(&out->forward))return FALSE;
    if(s->arm_pending_until>now||(s->opening_until>now&&s->opening_until-now<=TICKS_PER_SECOND)){
        out->mode=s->arm_pending_until>now?VR_COMBAT_POSE_CLUTCH_KNEEL:s->opening_kind;
        out->side=s->arm_side;
        out->weight=PIN((real)(now-s->opening_start+1)/4,0,1);
        if(!s->arm_pending_until)out->weight*=PIN((real)(s->opening_until-now)/6,0,1);
        out->phase=PIN((real)(now-s->opening_start)/(real)TICKS_PER_SECOND,0,1);
        if(s->arm_pending_until>now){out->has_control_target=1;out->control_target=s->arm_contact;}
        return TRUE;
    }
    if(s->attack_until>now&&move_clip(s,&frame)){
        out->mode=s->kind;out->side=s->side;
        out->weight=PIN((real)(frame+1)/3,0,1)*PIN((real)(s->frames-frame)/5,0,1);
        /* The pose's contact phase follows this clip's own native hit frame. */
        out->phase=frame<=s->key?(s->key>0?VR_COMBAT_POSE_CONTACT_PHASE*(real)frame/(real)s->key:VR_COMBAT_POSE_CONTACT_PHASE):
            VR_COMBAT_POSE_CONTACT_PHASE+(1-VR_COMBAT_POSE_CONTACT_PHASE)*(real)(frame-s->key)/(real)MAX(1,s->frames-s->key-1);
        return TRUE;
    }
    return FALSE;
}
int vr_combat_moves_cue(long target)
{
    long now=game_time_get();short frame;
    if(!move_current()||!move_enemy(target))return 0;
    struct combat_move_state *s=move_slot(target,FALSE);
    if(!s)return 0;
    if(s->arm_pending_until>now)return VR_COMBAT_MOVE_ARM_OPENING;
    if(s->opening_until>now&&s->opening_until-now<=TICKS_PER_SECOND){
        if(s->pummelling)return VR_COMBAT_MOVE_PUMMEL_OPENING;
        if(s->opening_kind==VR_COMBAT_POSE_CLUTCH_KNEEL)return VR_COMBAT_MOVE_ARM_OPENING;
        return s->kind==VR_COMBAT_POSE_SWEEP?VR_COMBAT_MOVE_DUCK:VR_COMBAT_MOVE_SIDESTEP;
    }
    if(s->attack_until>now&&!s->dodged&&move_clip(s,&frame)&&frame<=s->key+1)
        return s->kind==VR_COMBAT_POSE_SWEEP?VR_COMBAT_MOVE_ATTACK_SWEEP:
            s->kind==VR_COMBAT_POSE_OVERHEAD?VR_COMBAT_MOVE_ATTACK_OVERHEAD:VR_COMBAT_MOVE_ATTACK_JAB;
    return 0;
}
int vr_combat_moves_poll_event(struct vr_combat_move_event *out)
{
    if(!out||!move_current()||!moves.events)return FALSE;
    *out=moves.event[0];
    for(int i=1;i<moves.events;i++)moves.event[i-1]=moves.event[i];
    --moves.events;return TRUE;
}
long vr_combat_moves_cue_target(int slot)
{
    if(slot<0||slot>=MOVE_SLOTS||!move_current())return NONE;
    long target=moves.slot[slot].target;
    return target!=NONE&&vr_combat_moves_cue(target)?target:NONE;
}
#endif
