/* Optional campaign interaction extension. Existing distributed IDs and native
 * OpenCE payloads are unchanged. A distinct magic/version multiplexes only the
 * already reserved avatar envelopes; old avatar decoders discard this magic.
 * Clients send hand intent, never actor transforms, velocity or damage. */
#include "cseries.h"
#include "game/game.h"
#include "game/players.h"
#include "units/units.h"
#include "objects/objects.h"
#include "items/weapons.h"
#include "networking/network_game_globals.h"
#include "network_distributed.h"
#include "network_coop.h"
#include "network_interaction.h"
#include <math.h>
#include <string.h>
#include "../src/port_config.h"
#include "vr_npc_interaction.h"
#include "vr_world_interaction.h"
/* Implemented by their authoritative simulation modules. */
boolean vr_world_interaction_remote(struct network_interaction_hand const *request);
void vr_world_interaction_remote_cancel(long player,int hand);
int vr_npc_interaction_remote(long player,int hand,int held,float const world[3]);
void vr_npc_interaction_remote_cancel(long player,int hand);
int vr_npc_interaction_snapshot(long *index,int *count,real_matrix4x3 *matrices,int capacity);
/* Test73 (10d): the host's half of a client's reload and grenade (weapons.c,
units.c; every build, so a flat host serves VR clients) */
void weapon_vr_reload_commit(long weapon_index);
boolean unit_vr_throw_player_grenade(long unit_index,short type,real_point3d const *point,real_vector3d const *velocity);
boolean unit_vr_remote_strike(long unit_index,long target_index,real_point3d const *point,real_vector3d const *direction,
    real scale,real multiplier,real_vector3d const *shove);
unsigned long system_milliseconds(void);
void platform_log(char const *,...);
/* Test73: NI_FEATURES (host: the VR features it allows, as the sequence),
NI_CLIENT_FEATURES (client: the ones it uses), NI_ACTION (client: a reload's
commit, a grenade's throw or a fist blow, in a hand's wire); version 1 kept:
older peers drop kinds they do not know */
enum { NI_MAGIC=0x56494e31, NI_VERSION=1, NI_LEASE=6000, NI_INPUT_LEASE=300,
       NI_WORLD_READY=1, NI_NPC_READY=2,
       NI_NODES=64, NI_OFFER=1,NI_ACK,NI_CONFIRM,NI_HAND,NI_RESULT,NI_JOINT,NI_CANCEL,
       NI_NPC_CONFIRM=9, NI_FEATURES=10, NI_CLIENT_FEATURES=11, NI_ACTION=12,
       /* a client's action is sent this many times (the host takes one, by
       its sequence), and each kind taken no oftener than these (ms; a
       flurry's punches come a few ticks apart) */
       NI_ACTION_COPIES=3, NI_RELOAD_INTERVAL=500, NI_GRENADE_INTERVAL=250, NI_STRIKE_INTERVAL=60 };
/* (a fist blow: where it meets the body within reach of the striker's eyes
(a lunge has carried it there) and within this of the body's own sphere;
its strength, share (a takedown's six at most) and shove (6 m/s) bounded) */
#define NI_STRIKE_REACH (2.5f/3.048f)
#define NI_STRIKE_BODY (0.6f/3.048f)
#define NI_STRIKE_SCALE 2.5f
#define NI_STRIKE_SHARE 6.0f
#define NI_STRIKE_SHOVE (6.5f/3.048f/30.0f)
/* (a thrown grenade: within reach of the unit's eyes, and no faster than a
physical throw's cap, 15 m/s; world units are 10 feet, 30 ticks a second) */
#define NI_GRENADE_REACH (1.2f/3.048f)
#define NI_GRENADE_SPEED (15.0f/3.048f/30.0f)
struct ni_header { unsigned long magic,seed,nonce,sequence; long round; word version,kind; };
struct ni_hand_wire { struct ni_header h; long unit,object; byte player,hand,held,features;
    real_point3d position; real_vector3d forward,up; };
struct ni_joint { struct ni_header h; long unit; byte node,count; word cadence_ms;
    real scale; real_point3d position; real_vector3d forward,up; };
typedef char ni_header_size[sizeof(struct ni_header)==24?1:-1];
typedef char ni_hand_size[sizeof(struct ni_hand_wire)==72?1:-1];
typedef char ni_joint_size[sizeof(struct ni_joint)==72?1:-1];
static struct { unsigned long nonce,seen,features; long player; boolean ready; } ni_peers[HALO_PORT_MAXIMUM_NETWORK_MACHINES];
/* Test73: (host) each player's last action, and when each kind was taken;
(client) the VR features the host allows */
static struct { unsigned long sequence,reload_at,grenade_at,strike_at; boolean sequenced; } ni_actions[MAXIMUM_TRACKED_PLAYERS];
static unsigned long ni_host_features;
static struct { struct network_interaction_hand request; unsigned long received,sequence;
    unsigned long result_sequence; long machine; boolean valid,active,sequenced,result_sent;
    byte owner,down,result_owner; } ni_hands[MAXIMUM_TRACKED_PLAYERS][2];
static unsigned long ni_nonce_next=1,ni_offer_at,ni_host_nonce,ni_host_seen,ni_sequence;
static boolean ni_host_ready,ni_host_npc_ready,ni_peer_budget_warned;
static unsigned long ni_last_pose;
static struct ni_pose_state { real_matrix4x3 pending[NI_NODES],previous[NI_NODES],current[NI_NODES];
    unsigned long sequence,pending_sequence,received; unsigned long long mask;
    long unit,pending_unit; short count,pending_count; word cadence_ms; boolean valid,assembling; } ni_poses[4];
static void ni_cancel(short player,int hand)
{
    if(ni_hands[player][hand].active) {
        long p=distributed_player_from_byte((byte)player);
        vr_world_interaction_remote_cancel(p,hand);vr_npc_interaction_remote_cancel(p,hand);
    }
    ni_hands[player][hand].active=FALSE;ni_hands[player][hand].valid=FALSE;
    ni_hands[player][hand].owner=0;ni_hands[player][hand].down=1;ni_hands[player][hand].result_sent=FALSE;
}
void network_interaction_reset(void)
{
    for(short p=0;p<MAXIMUM_TRACKED_PLAYERS;p++)for(int h=0;h<2;h++)ni_cancel(p,h);
    ni_peer_budget_warned=FALSE;ni_host_ready=ni_host_npc_ready=FALSE; /* teardown must not emit packets */
    vr_interaction_client_reset();
    memset(ni_hands,0,sizeof(ni_hands));
    for(short player=0;player<MAXIMUM_TRACKED_PLAYERS;player++)for(int hand=0;hand<2;hand++)ni_hands[player][hand].down=1;
    memset(ni_peers,0,sizeof(ni_peers));memset(ni_poses,0,sizeof(ni_poses));
    memset(ni_actions,0,sizeof(ni_actions));ni_host_features=0;
    ni_host_ready=FALSE;ni_offer_at=ni_host_nonce=ni_host_seen=ni_last_pose=0;
}
static long ni_machine_player(long machine)
{
    for(short p=0;p<MAXIMUM_TRACKED_PLAYERS;p++)
        if(distributed_player(p)&&distributed_machine_has_player(machine,p))return distributed_player_from_byte((byte)p);
    return NONE;
}
boolean network_interaction_host_ready(void)
{
    long machines[HALO_PORT_MAXIMUM_NETWORK_MACHINES];unsigned long now=system_milliseconds();
    if(game_connection()!=_game_connection_network_server||!network_coop_active()||!config_boolean("net.physical_interactions"))return FALSE;
    short count=distributed_client_machines(machines,NUMBEROF(machines));
    if(count<0||count>HALO_PORT_MAXIMUM_NETWORK_MACHINES)return FALSE;
    for(short i=0;i<count;i++) {
        long m=machines[i];
        if(!VALID_INDEX(m,NUMBEROF(ni_peers))||!ni_peers[m].ready||now-ni_peers[m].seen>NI_LEASE||
           ni_peers[m].player!=ni_machine_player(m))return FALSE;
    }
    return TRUE;
}
boolean network_interaction_npc_ready(void)
{
    long machines[HALO_PORT_MAXIMUM_NETWORK_MACHINES];
    short count;
    if(game_connection()==_game_connection_network_client)
        return ni_host_ready&&ni_host_npc_ready&&system_milliseconds()-ni_host_seen<=NI_LEASE;
    if(!network_interaction_host_ready())return FALSE;
    /* Current per-peer, per-joint pose packets are timely only at four peers. */
    count=distributed_client_machines(machines,NUMBEROF(machines));
    return count>=0&&count<=4;
}
static void ni_header_init(struct ni_header *h,word kind,unsigned long nonce,unsigned long sequence)
{
    memset(h,0,sizeof(*h));h->magic=NI_MAGIC;h->version=NI_VERSION;h->kind=kind;
    h->nonce=nonce;h->sequence=sequence;h->seed=network_game_get_random_seed();h->round=network_game_get_number_of_games_played();
}
static void ni_send(long machine,void const *body,word bytes,byte type)
{
    struct { struct distributed_message_header header; byte body[sizeof(struct ni_joint)]; } packet;
    if(bytes>sizeof(packet.body))return;
    memset(&packet,0,sizeof(packet));memcpy(packet.body,body,bytes);
    if(machine==NONE)distributed_send(&packet,type,1,sizeof(packet.header)+bytes,_distributed_to_host);
    else distributed_send_to_machine(machine,&packet,type,1,sizeof(packet.header)+bytes);
}
static void ni_cap(long machine,word kind,unsigned long nonce,unsigned long ready)
{
    struct ni_header h;ni_header_init(&h,kind,nonce,ready);ni_send(machine,&h,sizeof(h),_distributed_message_vr_capability);
}
static boolean ni_active_npc(long unit,int count)
{
    struct unit_datum *u;
    return count>0&&count<=NI_NODES&&distributed_object_index_valid(unit)&&
        (u=unit_try_and_get(unit))&&u->unit.player_index==NONE&&u->object.type==_object_type_biped&&
        u->object.parent_object_index==NONE&&u->object.node_matrices.size==count*sizeof(real_matrix4x3);
}
/* Test73 (10d): the VR features this machine's player uses, for its host
(none in a build without VR) */
static unsigned long ni_client_features(void)
{
#ifdef HALO_VR
    unsigned long features=NETWORK_VR_MELEE;
    if(config_boolean("vr.manual_reload"))features|=NETWORK_VR_RELOAD;
    if(config_boolean("vr.physical_grenades"))features|=NETWORK_VR_GRENADES;
    if(config_boolean("vr.slide")||config_boolean("vr.parkour_wallrun")||config_boolean("vr.parkour_walljump")||
       config_boolean("vr.parkour_climb"))features|=NETWORK_VR_MOVEMENT;
    return features;
#else
    return 0;
#endif
}
/* Test73 (10d): (host) a client's reload, committed as the local player's is
(weapons.c): the weapon its unit holds, when it is the kind the client
reloaded (its tag, which every machine with the map numbers alike), at most
every NI_RELOAD_INTERVAL */
static void ni_action_reload(short player,long unit,long definition,unsigned long now)
{
    struct unit_datum *u=unit_get(unit);
    long weapon=u->unit.current_weapon_index>=0?unit_inventory_get_weapon(unit,u->unit.current_weapon_index):NONE;
    struct weapon_datum *held=weapon!=NONE?weapon_try_and_get(weapon):NULL;
    if(!held||held->definition_index!=definition||
       (ni_actions[player].reload_at&&now-ni_actions[player].reload_at<NI_RELOAD_INTERVAL))return;
    ni_actions[player].reload_at=now;
    weapon_vr_reload_commit(weapon);
    platform_log("[physical network] player %d: manual reload committed (weapon %08lx)",player,(unsigned long)weapon);
}
/* (host) a client's physical grenade, thrown as the local player's is
(units.c): within reach, no faster than a throw may be, of a kind it has */
static void ni_action_grenade(short player,long unit,long type,real_point3d const *point,
    real_vector3d const *velocity,unsigned long now)
{
    real_point3d camera;real_vector3d reach;
    if(type<0||type>1||!valid_real_point3d(point)||!valid_real_vector3d(velocity)||
       !(magnitude3d(velocity)<=NI_GRENADE_SPEED)||
       (ni_actions[player].grenade_at&&now-ni_actions[player].grenade_at<NI_GRENADE_INTERVAL))return;
    unit_get_camera_position(unit,&camera);vector_from_points3d(&camera,point,&reach);
    if(!(magnitude3d(&reach)<=NI_GRENADE_REACH))return;
    ni_actions[player].grenade_at=now;
    platform_log("[physical network] player %d: grenade %ld %s",player,type,
        unit_vr_throw_player_grenade(unit,(short)type,point,velocity)?"thrown":"refused (count, state or collision)");
}
/* (host) a client's fist blow, dealt as the local player's is (units.c):
on another body, within reach, its numbers within bounds, at most every
NI_STRIKE_INTERVAL; the shove along the blow, level */
static void ni_action_strike(short player,long unit,long target,real_point3d const *point,
    real_vector3d const *direction,real_vector3d const *numbers,unsigned long now)
{
    struct object_datum *body;real_point3d camera;real_vector3d reach,shove;
    real scale=numbers->i,share=numbers->j,push=numbers->k;
    if(target==unit||!distributed_object_index_valid(target)||!(body=object_try_and_get(target))||
       !valid_real_point3d(point)||!valid_real_vector3d(direction)||
       !(scale>=0.0f&&scale<=NI_STRIKE_SCALE)||!(share>=0.0f&&share<=NI_STRIKE_SHARE)||
       !(push>=0.0f&&push<=NI_STRIKE_SHOVE)||
       (ni_actions[player].strike_at&&now-ni_actions[player].strike_at<NI_STRIKE_INTERVAL))return;
    unit_get_camera_position(unit,&camera);vector_from_points3d(&camera,point,&reach);
    if(!(magnitude3d(&reach)<=NI_STRIKE_REACH))return;
    vector_from_points3d(&body->object.bounding_sphere_center,point,&reach);
    if(!(magnitude3d(&reach)<=body->object.bounding_sphere_radius+NI_STRIKE_BODY))return;
    ni_actions[player].strike_at=now;
    shove=*direction;shove.k=0;
    if(magnitude3d(&shove)>0.0001f)scale_vector3d(&shove,push/magnitude3d(&shove),&shove);
    else shove.i=shove.j=shove.k=0;
    platform_log("[physical network] player %d: fist blow on %08lx (strength %.2f, share %.2f) %s",player,
        (unsigned long)target,scale,share,unit_vr_remote_strike(unit,target,point,direction,scale,share,&shove)?
        "dealt":"refused");
}
void network_interaction_receive(long machine,byte type,void const *data,short count,word bytes)
{
    struct ni_header h;unsigned long now=system_milliseconds();
    boolean server=game_connection()==_game_connection_network_server;
    if(count!=1||bytes<sizeof(h)||!network_coop_active())return;
    memcpy(&h,data,sizeof(h));
    if(h.magic!=NI_MAGIC||h.version!=NI_VERSION||!h.nonce||h.seed!=(unsigned long)network_game_get_random_seed()||
        h.round!=network_game_get_number_of_games_played())return;
    if(server?(!VALID_INDEX(machine,NUMBEROF(ni_peers))):
       (machine!=NONE||game_connection()!=_game_connection_network_client))return;
    if(type==_distributed_message_vr_capability&&bytes==sizeof(h)) {
        if(server&&h.kind==NI_ACK&&ni_peers[machine].nonce==h.nonce&&ni_peers[machine].player==ni_machine_player(machine)) {
            ni_peers[machine].ready=TRUE;ni_peers[machine].seen=now;
            boolean ready=network_interaction_host_ready();
            boolean npc_ready=ready&&network_interaction_npc_ready();
            /* Preserve Test38's protocol-v1 boolean confirmation for mixed
             * installs; the additive NPC confirmation is ignored by old peers. */
            ni_cap(machine,NI_CONFIRM,h.nonce,ready?1:0);
            ni_cap(machine,NI_NPC_CONFIRM,h.nonce,npc_ready?1:0);
            /* Test73: what VR INTERACTIONS allows the clients (none while a
            client has not negotiated) */
            ni_cap(machine,NI_FEATURES,h.nonce,ready?NETWORK_VR_FEATURES:0);
        } else if(server&&h.kind==NI_CLIENT_FEATURES&&ni_peers[machine].nonce==h.nonce&&
            ni_peers[machine].player==ni_machine_player(machine)) {
            ni_peers[machine].features=h.sequence&NETWORK_VR_FEATURES;
        } else if(!server&&h.kind==NI_OFFER) {
            if(ni_host_nonce!=h.nonce){ni_host_ready=ni_host_npc_ready=FALSE;ni_host_features=0;}
            ni_host_nonce=h.nonce;ni_cap(NONE,NI_ACK,h.nonce,0);
            ni_cap(NONE,NI_CLIENT_FEATURES,h.nonce,ni_client_features());
        } else if(!server&&h.kind==NI_FEATURES&&ni_host_nonce==h.nonce) {
            ni_host_features=h.sequence&NETWORK_VR_FEATURES;
            ni_host_seen=now;
        } else if(!server&&h.kind==NI_CONFIRM&&ni_host_nonce==h.nonce) {
            ni_host_ready=h.sequence==1;
            if(!ni_host_ready)ni_host_npc_ready=FALSE;
            ni_host_seen=now;
        } else if(!server&&h.kind==NI_NPC_CONFIRM&&ni_host_nonce==h.nonce) {
            ni_host_npc_ready=h.sequence==1&&ni_host_ready;
            ni_host_seen=now;
        }
        return;
    }
    if(type!=_distributed_message_vr_pose)return;
    if(server?(!network_interaction_host_ready()||ni_peers[machine].nonce!=h.nonce):
       (!ni_host_ready||now-ni_host_seen>NI_LEASE||ni_host_nonce!=h.nonce))return;
    /* Test73 (10d): a client's reload or grenade: its own player's living
    unit, each sequence once (it sends copies), a kind it said it uses */
    if(h.kind==NI_ACTION&&server&&bytes==sizeof(struct ni_hand_wire)) {
        struct ni_hand_wire w;struct unit_datum *u;struct player_datum *p;memcpy(&w,data,sizeof(w));
        if(!VALID_INDEX(w.player,MAXIMUM_TRACKED_PLAYERS)||!distributed_machine_has_player(machine,w.player)||
           !(p=distributed_player(w.player))||p->unit_index!=w.unit||!distributed_object_index_valid(w.unit)||
           !(u=unit_try_and_get(w.unit))||u->object.parent_object_index!=NONE||
           TEST_FLAG(u->object.damage_flags,_object_dead_bit)||
           (ni_actions[w.player].sequenced&&(long)(h.sequence-ni_actions[w.player].sequence)<=0))return;
        ni_actions[w.player].sequence=h.sequence;ni_actions[w.player].sequenced=TRUE;
        if(w.features==NETWORK_VR_ACTION_RELOAD&&(ni_peers[machine].features&NETWORK_VR_RELOAD))
            ni_action_reload(w.player,w.unit,w.object,now);
        else if(w.features==NETWORK_VR_ACTION_GRENADE&&(ni_peers[machine].features&NETWORK_VR_GRENADES))
            ni_action_grenade(w.player,w.unit,w.object,&w.position,&w.forward,now);
        else if(w.features==NETWORK_VR_ACTION_STRIKE&&(ni_peers[machine].features&NETWORK_VR_MELEE))
            ni_action_strike(w.player,w.unit,w.object,&w.position,&w.forward,&w.up,now);
        return;
    }
    if(h.kind==NI_CANCEL&&server&&bytes==sizeof(struct ni_hand_wire)) {
        struct ni_hand_wire w;struct player_datum *p;memcpy(&w,data,sizeof(w));
        if(w.hand>1||!VALID_INDEX(w.player,MAXIMUM_TRACKED_PLAYERS)||!distributed_machine_has_player(machine,w.player)||
           !(p=distributed_player(w.player))||p->unit_index!=w.unit||
           (ni_hands[w.player][w.hand].sequenced&&(long)(h.sequence-ni_hands[w.player][w.hand].sequence)<=0))return;
        ni_cancel(w.player,w.hand);ni_hands[w.player][w.hand].sequence=h.sequence;ni_hands[w.player][w.hand].sequenced=TRUE;
        return;
    }
    if(h.kind==NI_HAND&&server&&bytes==sizeof(struct ni_hand_wire)) {
        struct ni_hand_wire w;struct unit_datum *u;struct player_datum *p;real_point3d camera;real_vector3d delta,f,up;
        memcpy(&w,data,sizeof(w));
        if(w.hand>1||w.held>1||!(w.features&3)||(w.features&~3)||!VALID_INDEX(w.player,MAXIMUM_TRACKED_PLAYERS)||
            !distributed_machine_has_player(machine,w.player)||!(p=distributed_player(w.player))||p->unit_index!=w.unit||
            !distributed_object_index_valid(w.unit)||!(u=unit_try_and_get(w.unit))||u->object.parent_object_index!=NONE||
            TEST_FLAG(u->object.damage_flags,_object_dead_bit)||
            !distributed_transform_valid(&w.position,&w.forward,&w.up,NULL,NULL,&f,&up))return;
        unit_get_camera_position(w.unit,&camera);vector_from_points3d(&camera,&w.position,&delta);
        /* Halo native scale: 1 world unit is 10 feet. No client-configured scale. */
        if(!isfinite(magnitude3d(&delta))||magnitude3d(&delta)>2.0f/3.048f)return;
        if(ni_hands[w.player][w.hand].sequenced&&(long)(h.sequence-ni_hands[w.player][w.hand].sequence)<=0)return;
        struct network_interaction_hand *r=&ni_hands[w.player][w.hand].request;
        r->player=distributed_player_from_byte(w.player);r->unit=w.unit;r->object=NONE;r->hand=w.hand;r->kind=w.features;r->held=w.held;
        r->pressed=w.held&&(r->pressed||!ni_hands[w.player][w.hand].down);
        ni_hands[w.player][w.hand].down=w.held;ni_hands[w.player][w.hand].sequenced=TRUE;
        r->position=w.position;r->forward=f;r->up=up;r->sequence=h.sequence;
        ni_hands[w.player][w.hand].machine=machine;ni_hands[w.player][w.hand].sequence=h.sequence;
        ni_hands[w.player][w.hand].received=now;ni_hands[w.player][w.hand].valid=TRUE;
    } else if(h.kind==NI_RESULT&&!server&&bytes==sizeof(struct ni_hand_wire)) {
        struct ni_hand_wire w;memcpy(&w,data,sizeof(w));
        if(w.hand>1||w.features>2)return;
        vr_interaction_client_result(w.unit,w.hand,w.features,h.sequence,w.object,w.position.n);

    } else if(h.kind==NI_JOINT&&!server&&bytes==sizeof(struct ni_joint)) {
        struct ni_joint j;real_matrix4x3 m;memcpy(&j,data,sizeof(j));
        if(j.cadence_ms<67||j.cadence_ms>5000||j.node>=j.count||!ni_active_npc(j.unit,j.count)||
            !(j.scale>=.25f&&j.scale<=4)||!distributed_point_valid(&j.position,8)||
            !distributed_transform_valid(&j.position,&j.forward,&j.up,NULL,NULL,&m.forward,&m.up))return;
        struct ni_pose_state *pose=NULL;
        for(int slot=0;slot<NUMBEROF(ni_poses);slot++)
            if(ni_poses[slot].unit==j.unit&&(ni_poses[slot].valid||ni_poses[slot].assembling)){pose=&ni_poses[slot];break;}
        if(!pose) {
            int oldest=0;
            for(int slot=0;slot<NUMBEROF(ni_poses);slot++) {
                if(!ni_poses[slot].valid&&!ni_poses[slot].assembling){oldest=slot;break;}
                if(now-ni_poses[slot].received>now-ni_poses[oldest].received)oldest=slot;
            }
            pose=&ni_poses[oldest];memset(pose,0,sizeof(*pose));pose->unit=j.unit;
        }
        if(pose->valid&&pose->unit==j.unit&&(long)(h.sequence-pose->sequence)<=0)return;
        if(!pose->assembling||pose->pending_unit!=j.unit||pose->pending_sequence!=h.sequence) {
            if(pose->assembling&&pose->pending_unit==j.unit&&(long)(h.sequence-pose->pending_sequence)<0)return;
            pose->mask=0;pose->pending_unit=j.unit;pose->pending_sequence=h.sequence;pose->pending_count=j.count;pose->assembling=TRUE;
        }
        if(pose->pending_count!=j.count)return;
        cross_product3d(&m.up,&m.forward,&m.left);m.scale=j.scale;m.position=j.position;
        pose->pending[j.node]=m;pose->mask|=1ULL<<j.node;
        if(pose->mask==(j.count==64?~0ULL:(1ULL<<j.count)-1)) {
            boolean smooth=pose->valid&&pose->unit==j.unit&&pose->count==j.count&&now-pose->received<250;
            memcpy(pose->previous,smooth?pose->current:pose->pending,j.count*sizeof(m));
            memcpy(pose->current,pose->pending,j.count*sizeof(m));pose->count=j.count;pose->unit=j.unit;
            pose->sequence=h.sequence;pose->cadence_ms=j.cadence_ms;pose->received=now;pose->valid=TRUE;pose->assembling=FALSE;
        }
    }
}

static void ni_send_result(short player,int hand,byte owner)
{
    struct ni_hand_wire w;memset(&w,0,sizeof(w));long machine=ni_hands[player][hand].machine;
    ni_header_init(&w.h,NI_RESULT,ni_peers[machine].nonce,ni_hands[player][hand].sequence);
    w.player=player;w.hand=hand;w.unit=ni_hands[player][hand].request.unit;w.features=owner;
    w.object=NONE;
    boolean contact=FALSE;
    if(owner==NETWORK_INTERACTION_WORLD)
        contact=vr_world_interaction_remote_contact(ni_hands[player][hand].request.player,hand,&w.object,w.position.n);
    else if(owner==NETWORK_INTERACTION_NPC)
        contact=vr_npc_interaction_remote_contact(ni_hands[player][hand].request.player,hand,&w.object,w.position.n);
    if(contact&&distributed_object_index_valid(w.object)) {
        real_matrix4x3 root,inverse;object_get_world_matrix(w.object,&root);
        matrix4x3_inverse(&root,&inverse);matrix4x3_transform_point(&inverse,&w.position,&w.position);
    } else w.object=NONE;
    ni_send(machine,&w,sizeof(w),_distributed_message_vr_pose);
}
void network_interaction_tick(void)
{
    unsigned long now=system_milliseconds();boolean server=game_connection()==_game_connection_network_server;
    long machines[HALO_PORT_MAXIMUM_NETWORK_MACHINES];
    if(!network_coop_active()){if(ni_offer_at||ni_host_nonce||ni_host_ready)network_interaction_reset();return;}
    short count=server?distributed_client_machines(machines,NUMBEROF(machines)):0;
    boolean over_budget=server&&count>4&&config_boolean("net.physical_interactions");
    if(over_budget&&!ni_peer_budget_warned)platform_log("[physical network] NPC palette sync disabled above four remote machines; bounded world-object interaction remains available (%d peers)",count);
    ni_peer_budget_warned=over_budget;
    if(server&&config_boolean("net.physical_interactions")&&(!ni_offer_at||now-ni_offer_at>=2000)) {
        boolean present[HALO_PORT_MAXIMUM_NETWORK_MACHINES]={FALSE};ni_offer_at=now;
        for(short i=0;i<count;i++) {
            long m=machines[i],player=ni_machine_player(m);
            if(!VALID_INDEX(m,NUMBEROF(ni_peers))||player==NONE)continue;
            present[m]=TRUE;
            if(!ni_peers[m].nonce||ni_peers[m].player!=player) {
                for(short p=0;p<MAXIMUM_TRACKED_PLAYERS;p++)for(int hand=0;hand<2;hand++)
                    if(ni_hands[p][hand].machine==m){ni_cancel(p,hand);ni_hands[p][hand].sequenced=FALSE;}
                memset(&ni_peers[m],0,sizeof(ni_peers[m]));ni_peers[m].player=player;
                ni_peers[m].nonce=++ni_nonce_next;if(!ni_peers[m].nonce)ni_peers[m].nonce=++ni_nonce_next;
            }
            ni_cap(m,NI_OFFER,ni_peers[m].nonce,0);
        }
        for(short m=0;m<NUMBEROF(ni_peers);m++)if(!present[m])memset(&ni_peers[m],0,sizeof(ni_peers[m]));
    }
    if(server) {
        boolean ready=network_interaction_host_ready();
        for(short player=0;player<MAXIMUM_TRACKED_PLAYERS;player++)for(int hand=0;hand<2;hand++) {
            if(!ni_hands[player][hand].valid)continue;
            long machine=ni_hands[player][hand].machine;
            struct network_interaction_hand *r=&ni_hands[player][hand].request;
            struct player_datum *p=distributed_player(player);
            if(!ready||now-ni_hands[player][hand].received>NI_INPUT_LEASE||!p||p->unit_index!=r->unit||
               !VALID_INDEX(machine,NUMBEROF(ni_peers))||!distributed_machine_has_player(machine,player)) {ni_cancel(player,hand);continue;}
            byte owner=ni_hands[player][hand].owner;
            if(owner==NETWORK_INTERACTION_NPC) {
                if(!vr_npc_interaction_remote(r->player,hand,r->held,r->position.n))owner=0;
            } else if(owner==NETWORK_INTERACTION_WORLD) {
                if(!vr_world_interaction_remote(r))owner=0;
            } else if(r->pressed||!r->held) {
                /* Modules track grip edges; one request cannot own both. */
                if((r->kind&NETWORK_INTERACTION_NPC)&&vr_npc_interaction_remote(r->player,hand,r->held,r->position.n))owner=NETWORK_INTERACTION_NPC;
                else if((r->kind&NETWORK_INTERACTION_WORLD)&&vr_world_interaction_remote(r))owner=NETWORK_INTERACTION_WORLD;
            }
            r->pressed=0;
            ni_hands[player][hand].active=owner!=0;ni_hands[player][hand].owner=owner;
            /* Clients send bounded 20 Hz samples. A result is needed for each
             * new sample and ownership transition, not every simulation tick;
             * this keeps aggregate traffic bounded in large hosted sessions. */
            if(!ni_hands[player][hand].result_sent||
               ni_hands[player][hand].result_sequence!=r->sequence||
               ni_hands[player][hand].result_owner!=owner) {
                ni_send_result(player,hand,owner);
                ni_hands[player][hand].result_sent=TRUE;
                ni_hands[player][hand].result_sequence=r->sequence;
                ni_hands[player][hand].result_owner=owner;
            }
        }
        if(ready&&!over_budget&&now-ni_last_pose>=MAX(67,(unsigned long)count*NI_NODES*100*1000/262144)) {
            static real_matrix4x3 nodes[NI_NODES];long unit;int nodes_count;
            if(vr_npc_interaction_snapshot(&unit,&nodes_count,nodes,NI_NODES)&&ni_active_npc(unit,nodes_count)) {
                /* Bound aggregate optional-pose traffic to about 256 KiB/s; 15 Hz
                 * max. Native simulation packets always retain their own cadence. */
                unsigned long interval=MAX(67,(unsigned long)count*nodes_count*100*1000/262144);
                if(now-ni_last_pose<interval)return;
                ni_last_pose=now;
                struct unit_datum *u=unit_get(unit);unsigned long sequence=++ni_sequence;
                for(short peer=0;peer<count;peer++)for(short n=0;n<nodes_count;n++) {
                    long m=machines[peer];struct ni_joint j;memset(&j,0,sizeof(j));
                    ni_header_init(&j.h,NI_JOINT,ni_peers[m].nonce,sequence);j.unit=unit;j.node=n;j.count=nodes_count;j.cadence_ms=MIN(interval*4,5000);
                    j.scale=nodes[n].scale;j.forward=nodes[n].forward;j.up=nodes[n].up;
                    for(int axis=0;axis<3;axis++)j.position.n[axis]=nodes[n].position.n[axis]-u->object.position.n[axis];
                    ni_send(m,&j,sizeof(j),_distributed_message_vr_pose);
                }
            }
        }
    } else if(game_connection()==_game_connection_network_client) {
        vr_interaction_client_tick(ni_host_ready&&now-ni_host_seen<=NI_LEASE,
            ni_host_npc_ready&&now-ni_host_seen<=NI_LEASE);
    }

}
real_matrix4x3 *network_interaction_render(long unit,real_matrix4x3 *stock)
{
    static real_matrix4x3 result[NI_NODES];struct ni_pose_state *pose=NULL;
    for(int slot=0;slot<NUMBEROF(ni_poses);slot++)if(ni_poses[slot].valid&&ni_poses[slot].unit==unit){pose=&ni_poses[slot];break;}
    if(!pose)return stock;
    unsigned long age=system_milliseconds()-pose->received;
    if(!stock||game_connection()!=_game_connection_network_client||!ni_host_ready||!ni_host_npc_ready||
       system_milliseconds()-ni_host_seen>NI_LEASE||!pose->valid||pose->unit!=unit||age>MAX(500,pose->cadence_ms*3)||!ni_active_npc(unit,pose->count))return stock;
    struct unit_datum *u=unit_get(unit);real period=MAX(67,pose->cadence_ms);
    real fade_begin=MAX(250,period*2),fade_end=MAX(500,period*3);
    real blend=MIN(age/period,1.0f),fade=age>fade_begin?(age-fade_begin)/(fade_end-fade_begin):0;
    for(short n=0;n<pose->count;n++) {
        real_quaternion a,b,q;matrix4x3_rotation_to_quaternion(&pose->previous[n],&a);
        matrix4x3_rotation_to_quaternion(&pose->current[n],&b);quaternions_interpolate_and_normalize(&a,&b,blend,&q);
        matrix4x3_rotation_from_quaternion(&result[n],&q);
        result[n].scale=pose->previous[n].scale+(pose->current[n].scale-pose->previous[n].scale)*blend;
        for(int axis=0;axis<3;axis++)result[n].position.n[axis]=u->object.position.n[axis]+pose->previous[n].position.n[axis]+(pose->current[n].position.n[axis]-pose->previous[n].position.n[axis])*blend;
        if(fade>0) {
            real scale=result[n].scale;real_point3d point=result[n].position;
            matrix4x3_rotation_to_quaternion(&result[n],&a);matrix4x3_rotation_to_quaternion(&stock[n],&b);
            quaternions_interpolate_and_normalize(&a,&b,fade,&q);matrix4x3_rotation_from_quaternion(&result[n],&q);
            result[n].scale=scale+(stock[n].scale-scale)*fade;
            for(int axis=0;axis<3;axis++)result[n].position.n[axis]=point.n[axis]+(stock[n].position.n[axis]-point.n[axis])*fade;
        }
    }
    return result;
}

void network_interaction_client_send(byte hand,byte held,byte features,long player,long unit,
    real_point3d const *position,real_vector3d const *forward,real_vector3d const *up)
{
    if(game_connection()!=_game_connection_network_client||!ni_host_ready||system_milliseconds()-ni_host_seen>NI_LEASE)return;
    struct ni_hand_wire w;memset(&w,0,sizeof(w));
    ni_header_init(&w.h,NI_HAND,ni_host_nonce,++ni_sequence);
    w.hand=hand;w.held=held;w.features=features;w.player=distributed_player_to_byte(player);w.unit=unit;
    w.position=*position;w.forward=*forward;w.up=*up;
    ni_send(NONE,&w,sizeof(w),_distributed_message_vr_pose);
}

void network_interaction_client_cancel(byte hand,long player,long unit)
{
    if(game_connection()!=_game_connection_network_client||!ni_host_ready||system_milliseconds()-ni_host_seen>NI_LEASE)return;
    struct ni_hand_wire w;memset(&w,0,sizeof(w));
    ni_header_init(&w.h,NI_CANCEL,ni_host_nonce,++ni_sequence);w.hand=hand;w.player=distributed_player_to_byte(player);w.unit=unit;
    ni_send(NONE,&w,sizeof(w),_distributed_message_vr_pose);
}

void network_interaction_palette(long unit)
{
    if(game_connection()!=_game_connection_network_client)return;
    struct unit_datum *u=unit_try_and_get(unit);
    if(!u||u->unit.player_index!=NONE)return;
    real_matrix4x3 *stock=object_get_node_matrices(unit);
    real_matrix4x3 *pose=network_interaction_render(unit,stock);
    if(pose!=stock&&stock) {
        short count=u->object.node_matrices.size/sizeof(real_matrix4x3);
        if(ni_active_npc(unit,count))memcpy(stock,pose,count*sizeof(*stock));
    }
}

boolean network_interaction_palette_owned(long unit)
{
    unsigned long now=system_milliseconds();
    if(game_connection()!=_game_connection_network_client||!ni_host_ready||!ni_host_npc_ready||now-ni_host_seen>NI_LEASE)return FALSE;
    for(int slot=0;slot<NUMBEROF(ni_poses);slot++) {
        struct ni_pose_state *pose=&ni_poses[slot];
        if(pose->valid&&pose->unit==unit&&now-pose->received<=MAX(500,pose->cadence_ms*3)&&ni_active_npc(unit,pose->count))return TRUE;
    }
    return FALSE;
}

/* ---------- Test73 (10d): VR INTERACTIONS for the host and every player */

boolean network_interaction_vr_allowed(unsigned long feature)
{
    switch(game_connection()) {
    case _game_connection_local:
        return TRUE;
    case _game_connection_network_server:
        return network_interaction_host_ready();
    case _game_connection_network_client:
        return ni_host_ready&&system_milliseconds()-ni_host_seen<=NI_LEASE&&(ni_host_features&feature)==feature;
    default:
        return FALSE;
    }
}

boolean network_interaction_player_vr(long player,unsigned long feature)
{
    long machines[HALO_PORT_MAXIMUM_NETWORK_MACHINES];short count;byte index;
    if(player==NONE||game_connection()!=_game_connection_network_server||!network_interaction_host_ready())return FALSE;
    index=distributed_player_to_byte(player);
    count=distributed_client_machines(machines,NUMBEROF(machines));
    for(short i=0;i<count;i++) {
        long m=machines[i];
        if(VALID_INDEX(m,NUMBEROF(ni_peers))&&ni_peers[m].ready&&distributed_machine_has_player(m,index))
            return (ni_peers[m].features&feature)==feature;
    }
    return FALSE;
}

boolean network_interaction_unit_manual_reload(long unit)
{
    struct unit_datum *u;
    if(unit==NONE||game_connection()!=_game_connection_network_server)return FALSE;
    u=(struct unit_datum *)object_try_and_get_and_verify_type(unit,_object_mask_unit);
    return u&&u->unit.player_index!=NONE&&network_interaction_player_vr(u->unit.player_index,NETWORK_VR_RELOAD);
}

/* (a client) an action in a hand's wire: position, vector (the forward) and
numbers (the up), each optional */
static void ni_client_action(byte kind,long player,long unit,long object,real_point3d const *position,
    real_vector3d const *vector,real_vector3d const *numbers)
{
    struct ni_hand_wire w;
    if(game_connection()!=_game_connection_network_client||!ni_host_ready||system_milliseconds()-ni_host_seen>NI_LEASE)return;
    memset(&w,0,sizeof(w));
    ni_header_init(&w.h,NI_ACTION,ni_host_nonce,++ni_sequence);
    w.features=kind;w.player=distributed_player_to_byte(player);w.unit=unit;w.object=object;
    if(position)w.position=*position;
    if(vector)w.forward=*vector;
    if(numbers)w.up=*numbers;
    /* (copies of the one sequence: one is taken, however many arrive) */
    for(int copy=0;copy<NI_ACTION_COPIES;copy++)ni_send(NONE,&w,sizeof(w),_distributed_message_vr_pose);
}

void network_interaction_client_action(byte kind,long player,long unit,long object,
    real_point3d const *position,real_vector3d const *vector)
{
    ni_client_action(kind,player,unit,object,position,vector,NULL);
}

void network_interaction_client_strike(long player,long unit,long target,real_point3d const *point,
    real_vector3d const *direction,real scale,real multiplier,real_vector3d const *shove)
{
    real_vector3d numbers;
    if(!point||!direction)return;
    /* (in the hand wire's last vector: strength, share, the shove's speed) */
    numbers.i=scale;numbers.j=multiplier;numbers.k=shove?magnitude3d(shove):0.0f;
    if(!isfinite(numbers.k))numbers.k=0.0f;
    ni_client_action(NETWORK_VR_ACTION_STRIKE,player,unit,target,point,direction,&numbers);
}
