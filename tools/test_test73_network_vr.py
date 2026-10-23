"""Test73, item 10d (the owner: one co-op VR toggle that lets the host and every player use the VR mechanics:
parkour, fist combat, physical grenades and manual reload).

VR INTERACTIONS (net.physical_interactions, the host's, on by default: the owner) covers them all now. The host says
what it allows (NI_FEATURES, after each confirmation), each client what it uses (NI_CLIENT_FEATURES, after each
acknowledgement), and a client's reload, grenade and fist blows (the owner: "make it so everyone can do advanced fist
combat") reach the host as NI_ACTION messages, which the host validates and deals as the local player's (weapons.c
weapon_vr_reload_commit, units.c unit_vr_throw_player_grenade and unit_vr_remote_strike).

Compiled and run (ASan/UBSan) on port/linux/game/network_interaction.c itself, with the guest's 32-bit long:
- the host (a flat build: the authority is common): features only from the machine's own player with the current
  nonce; nothing while VR INTERACTIONS is off or in PvP; a reload committed once for its copies, never replayed, only
  on the weapon held (by its tag), no oftener than every 500 ms, never for another machine's player, another unit,
  a dead or seated unit, or a kind the client did not say; a grenade within 1.2 m of the eyes, at most 15 m/s, of a
  known type, no oftener than every 250 ms;
- the client (a VR build): its features follow its settings (melee always); nothing is allowed before the host's
  FEATURES, after the lease, or after a new host's offer; an action is sent as three copies of one sequence, only
  to a host that confirmed it within the lease;
- mixed sessions: Test72's network_interaction.c (HEAD f77f6a11), as host and as client, ignores the three new
  kinds without any effect, so older peers keep the stock controls.
Then the host's on-foot bound and the gates that read the toggle are pinned in their sources.
"""
from pathlib import Path
import re
import subprocess

R = Path(__file__).resolve().parents[1]
O = R / 'build/test73-network-vr'
O.mkdir(parents=True, exist_ok=True)
source = (R / 'port/linux/game/network_interaction.c').read_text()
header = (R / 'port/linux/game/network_interaction.h').read_text()
old_source = subprocess.run(['git', '-C', str(R), 'show', 'f77f6a11:port/linux/game/network_interaction.c'],
                            capture_output=True, text=True, check=True).stdout
old_header = subprocess.run(['git', '-C', str(R), 'show', 'f77f6a11:port/linux/game/network_interaction.h'],
                            capture_output=True, text=True, check=True).stdout
assert 'NI_FEATURES' not in old_source and 'NI_ACTION' not in old_source


def strip(text):
    text = re.sub(r'^#include.*$', '', text, flags=re.M)
    text = text.replace('unsigned long long', 'uint64_t').replace('unsigned long', 'uint32_t')
    return re.sub(r'\blong\b', 'int32_t', text)


# the new kinds, as the old peers would read them
kinds = dict(re.findall(r'\b(NI_FEATURES|NI_CLIENT_FEATURES|NI_ACTION)=(\d+)', source))
assert kinds == {'NI_FEATURES': '10', 'NI_CLIENT_FEATURES': '11', 'NI_ACTION': '12'}, kinds
assert 'NI_NPC_CONFIRM=9' in source and 'NI_NPC_CONFIRM=9' in old_source

prefix = r"""
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
typedef float real;typedef unsigned char byte,boolean;typedef unsigned short word;
typedef union{struct{float x,y,z;};float n[3];}real_point3d;
typedef union{struct{float i,j,k;};float n[3];}real_vector3d;
typedef struct{float scale;real_vector3d forward,left,up;real_point3d position;}real_matrix4x3;
typedef struct{float q[4];}real_quaternion;
#define TRUE 1
#define FALSE 0
#define NONE -1
#define HALO_PORT_MAXIMUM_NETWORK_MACHINES 16
#define MAXIMUM_TRACKED_PLAYERS 16
#define NUMBEROF(x) (sizeof(x)/sizeof((x)[0]))
#define VALID_INDEX(i,n) ((i)>=0&&(i)<(n))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define TEST_FLAG(x,b) ((x)&(1u<<(b)))
enum{_game_connection_local=0,_game_connection_network_server=1,_game_connection_network_client=2,_object_type_biped=1,
 _object_dead_bit=1,_distributed_message_vr_pose=37,_distributed_message_vr_capability=38,_distributed_to_host=1};
enum{_object_mask_unit=3};
struct distributed_message_header{byte data[12];};
struct player_datum{int32_t unit_index;};
struct unit_datum{struct{int32_t player_index;short current_weapon_index;}unit;
 struct{int type,parent_object_index,damage_flags;struct{int size;}node_matrices;real_point3d position;}object;};
struct weapon_datum{int32_t definition_index;};
/* (a body a fist blow strikes: its sphere) */
struct object_datum{struct{real_point3d bounding_sphere_center;real bounding_sphere_radius;}object;};
static struct object_datum bodies[16];
static int connection=_game_connection_network_server,permission=1,coop=1,clients=2,world_calls,npc_calls,cancels;
static int vr_reload,vr_grenades,vr_slide,vr_wallrun,vr_walljump,vr_climb;
static uint32_t now=100;static struct player_datum players[16];static struct unit_datum units[16];
static struct weapon_datum weapons[4]={{70},{71},{72},{73}};
/* what was sent: to a client machine (the host's) and to the host (a client's) */
static struct{int32_t machine;byte type;byte body[72];word bytes;}to_clients[64],to_host[64];static int to_clients_count,to_host_count;
static uint32_t system_milliseconds(void){return now;}
static int game_connection(void){return connection;}static int network_coop_active(void){return coop;}
static int config_boolean(char const*k){
 if(!strcmp(k,"net.physical_interactions"))return permission;
 if(!strcmp(k,"vr.manual_reload"))return vr_reload;if(!strcmp(k,"vr.physical_grenades"))return vr_grenades;
 if(!strcmp(k,"vr.slide"))return vr_slide;if(!strcmp(k,"vr.parkour_wallrun"))return vr_wallrun;
 if(!strcmp(k,"vr.parkour_walljump"))return vr_walljump;if(!strcmp(k,"vr.parkour_climb"))return vr_climb;
 fprintf(stderr,"unexpected setting %s\n",k);assert(0);return 0;}
static int32_t network_game_get_random_seed(void){return 42;}static int32_t network_game_get_number_of_games_played(void){return 2;}
static int game_time_get(void){return now/33;}
static short distributed_client_machines(int32_t*m,short max){assert(max>=clients);for(int i=0;i<clients;i++)m[i]=i;return clients;}
static struct player_datum*distributed_player(short p){return p>=0&&p<clients?&players[p]:NULL;}
static int distributed_machine_has_player(int32_t m,short p){return m==p&&m<clients;}
static int32_t distributed_player_from_byte(byte p){return p;}static byte distributed_player_to_byte(int32_t p){return (byte)p;}
static int distributed_object_index_valid(int32_t u){return u>=0&&u<16;}
static struct unit_datum*unit_try_and_get(int32_t u){return distributed_object_index_valid(u)?&units[u]:NULL;}
static struct unit_datum*unit_get(int32_t u){assert(distributed_object_index_valid(u));return &units[u];}
static void*object_try_and_get_and_verify_type(int32_t o,uint32_t mask){assert(mask==_object_mask_unit);return distributed_object_index_valid(o)?&units[o]:NULL;}
static int32_t unit_inventory_get_weapon(int32_t u,short slot){(void)u;return slot>=0&&slot<4?slot:NONE;}
static struct weapon_datum*weapon_try_and_get(int32_t w){return w>=0&&w<4?&weapons[w]:NULL;}
static void unit_get_camera_position(int32_t u,real_point3d*p){*p=units[u].object.position;}
static int valid_real_point3d(real_point3d const*p){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z);}
static int valid_real_vector3d(real_vector3d const*v){return isfinite(v->i)&&isfinite(v->j)&&isfinite(v->k);}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static float magnitude3d(real_vector3d const*v){return sqrtf(v->i*v->i+v->j*v->j+v->k*v->k);}
static void scale_vector3d(real_vector3d const*v,float s,real_vector3d*out){for(int i=0;i<3;i++)out->n[i]=v->n[i]*s;}
static struct object_datum*object_try_and_get(int32_t o){return distributed_object_index_valid(o)?&bodies[o]:NULL;}
static int distributed_point_valid(real_point3d const*p,float bound){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z)&&fabsf(p->x)<=bound&&fabsf(p->y)<=bound&&fabsf(p->z)<=bound;}
static int distributed_transform_valid(real_point3d const*p,real_vector3d const*f,real_vector3d const*u,void*v,void*w,real_vector3d*outf,real_vector3d*outu){(void)v;(void)w;if(!distributed_point_valid(p,32768)||!isfinite(magnitude3d(f))||!isfinite(magnitude3d(u)))return 0;*outf=*f;*outu=*u;return 1;}
static void cross_product3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*c){*c=(real_vector3d){{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};}
static void keep(void*list,int*count,int32_t machine,void*p,byte t,word size){
 struct{int32_t machine;byte type;byte body[72];word bytes;}*l=list;
 if(size<sizeof(struct distributed_message_header)||*count>=64)return;word bytes=size-sizeof(struct distributed_message_header);
 if(bytes>72)return;l[*count].machine=machine;l[*count].type=t;l[*count].bytes=bytes;
 memcpy(l[*count].body,(byte*)p+sizeof(struct distributed_message_header),bytes);++*count;}
static void distributed_send(void*p,byte t,short c,word size,int dest){(void)c;assert(dest==_distributed_to_host);keep(to_host,&to_host_count,NONE,p,t,size);}
static void distributed_send_to_machine(int32_t m,void*p,byte t,short c,word size){(void)c;keep(to_clients,&to_clients_count,m,p,t,size);}
static real_matrix4x3 testroot,palette[64];
static real_matrix4x3*object_get_node_matrices(int32_t u){(void)u;return palette;}
static real_matrix4x3*object_get_world_matrix(int32_t u,real_matrix4x3*m){(void)u;*m=testroot;return m;}
static void matrix4x3_inverse(real_matrix4x3 const*a,real_matrix4x3*b){*b=*a;}
static void matrix4x3_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){(void)m;*out=*p;}
int vr_world_interaction_remote_contact(int32_t p,int hand,int32_t*object,float local[3]);
int vr_npc_interaction_remote_contact(int32_t p,int hand,int32_t*object,float world[3]);
static void matrix4x3_rotation_to_quaternion(real_matrix4x3 const*m,real_quaternion*q){(void)m;memset(q,0,sizeof(*q));}
static void matrix4x3_rotation_from_quaternion(real_matrix4x3*m,real_quaternion const*q){(void)q;memset(m,0,sizeof(*m));m->forward.i=1;m->left.j=1;m->up.k=1;}
static void quaternions_interpolate_and_normalize(real_quaternion const*a,real_quaternion const*b,float t,real_quaternion*q){(void)b;(void)t;*q=*a;}
"""
callbacks = r"""
boolean vr_world_interaction_remote(struct network_interaction_hand const*r){(void)r;world_calls++;return FALSE;}
void vr_world_interaction_remote_cancel(int32_t p,int h){(void)p;(void)h;cancels++;}
int vr_npc_interaction_remote(int32_t p,int h,int held,float const*w){(void)p;(void)h;(void)held;(void)w;npc_calls++;return 0;}
void vr_npc_interaction_remote_cancel(int32_t p,int h){(void)p;(void)h;cancels++;}
int vr_npc_interaction_snapshot(int32_t*i,int*c,real_matrix4x3*m,int cap){(void)i;(void)c;(void)m;(void)cap;return 0;}
void vr_interaction_client_reset(void){}void vr_interaction_client_tick(boolean b,boolean n){(void)b;(void)n;}
void vr_interaction_client_result(int32_t u,byte h,byte f,uint32_t s,int32_t object,float const local[3]){(void)u;(void)h;(void)f;(void)s;(void)object;(void)local;}
int vr_world_interaction_remote_contact(int32_t p,int hand,int32_t*object,float local[3]){(void)p;(void)hand;(void)object;(void)local;return 0;}
int vr_npc_interaction_remote_contact(int32_t p,int hand,int32_t*object,float world[3]){(void)p;(void)hand;(void)object;(void)world;return 0;}
void platform_log(char const*f,...){(void)f;}
static int reload_commits,grenade_throws,thrown_type=-1;static int32_t committed_weapon=NONE;
void weapon_vr_reload_commit(int32_t w){reload_commits++;committed_weapon=w;}
boolean unit_vr_throw_player_grenade(int32_t u,short t,real_point3d const*p,real_vector3d const*v){(void)u;(void)p;(void)v;grenade_throws++;thrown_type=t;return TRUE;}
/* (Test73, the owner: "make it so everyone can do advanced fist combat": a client's blow, dealt by the host) */
static int strikes;static int32_t struck_unit=NONE,struck_target=NONE;static float struck_scale,struck_share;static real_vector3d struck_shove;
boolean unit_vr_remote_strike(int32_t u,int32_t t,real_point3d const*p,real_vector3d const*d,real scale,real share,real_vector3d const*shove){
 (void)p;(void)d;strikes++;struck_unit=u;struck_target=t;struck_scale=scale;struck_share=share;struck_shove=*shove;return TRUE;}
static void world_reset(void){
 for(int i=0;i<16;i++){players[i].unit_index=i;units[i].unit.player_index=i;units[i].unit.current_weapon_index=1;
  units[i].object.type=_object_type_biped;units[i].object.parent_object_index=NONE;units[i].object.damage_flags=0;
  units[i].object.position=(real_point3d){{0,0,0}};
  bodies[i].object.bounding_sphere_center=(real_point3d){{0,0,0}};bodies[i].object.bounding_sphere_radius=.1f;}
 reload_commits=grenade_throws=strikes=0;thrown_type=-1;committed_weapon=struck_unit=struck_target=NONE;to_clients_count=to_host_count=0;
}
static struct ni_header body_header(void const*b){struct ni_header h;memcpy(&h,b,sizeof(h));return h;}
"""
host_main = r"""
static void ack(int machine){struct ni_header h;ni_header_init(&h,NI_ACK,ni_peers[machine].nonce,0);network_interaction_receive(machine,38,&h,1,sizeof(h));}
static void handshake_machine(int machine){network_interaction_tick();ack(machine);}
static void says(int machine,uint32_t nonce,uint32_t features){struct ni_header h;ni_header_init(&h,NI_CLIENT_FEATURES,nonce,features);network_interaction_receive(machine,38,&h,1,sizeof(h));}
static void act(int machine,uint32_t sequence,byte kind,byte player,int32_t unit,int32_t object,real_point3d p,real_vector3d v,int copies){
 struct ni_hand_wire w;memset(&w,0,sizeof(w));ni_header_init(&w.h,NI_ACTION,ni_peers[machine].nonce,sequence);
 w.features=kind;w.player=player;w.unit=unit;w.object=object;w.position=p;w.forward=v;
 for(int i=0;i<copies;i++)network_interaction_receive(machine,37,&w,1,sizeof(w));
}
static void refresh(void){ack(0);ack(1);}
/* (a fist blow: the body struck, where, along what, and the numbers: strength, share, shove) */
static void strike(uint32_t sequence,int32_t target,real_point3d p,real_vector3d d,float scale,float share,float shove,int copies){
 struct ni_hand_wire w;memset(&w,0,sizeof(w));ni_header_init(&w.h,NI_ACTION,ni_peers[0].nonce,sequence);
 w.features=NETWORK_VR_ACTION_STRIKE;w.player=0;w.unit=0;w.object=target;w.position=p;w.forward=d;
 w.up=(real_vector3d){{scale,share,shove}};
 for(int i=0;i<copies;i++)network_interaction_receive(0,37,&w,1,sizeof(w));
}
int main(void){
 world_reset();network_interaction_reset();assert(!network_interaction_host_ready());
 handshake_machine(0);handshake_machine(1);assert(network_interaction_host_ready());
 /* an ACK is answered with CONFIRM, NPC_CONFIRM and FEATURES: all of them once every client negotiated */
 assert(to_clients_count>=3);struct ni_header features=body_header(to_clients[to_clients_count-1].body);
 assert(to_clients[to_clients_count-1].machine==1&&features.kind==NI_FEATURES&&features.sequence==NETWORK_VR_FEATURES);
 int first=-1;for(int i=0;i<to_clients_count&&first<0;i++)if(to_clients[i].machine==0&&body_header(to_clients[i].body).kind==NI_FEATURES)first=i;
 assert(first>=0&&body_header(to_clients[first].body).sequence==0); /* (machine 1 had not negotiated yet: none) */
 assert(body_header(to_clients[first-2].body).kind==NI_CONFIRM&&body_header(to_clients[first-1].body).kind==NI_NPC_CONFIRM);
 /* the host's own player: its VR features are its own (the host is authoritative) */
 assert(network_interaction_vr_allowed(NETWORK_VR_RELOAD|NETWORK_VR_GRENADES|NETWORK_VR_MOVEMENT|NETWORK_VR_MELEE));
 /* a client that has not said what it uses: none */
 assert(!network_interaction_player_vr(0,NETWORK_VR_RELOAD)&&!network_interaction_unit_manual_reload(0));
 says(0,ni_peers[0].nonce+1,NETWORK_VR_FEATURES);assert(ni_peers[0].features==0); /* a stale nonce */
 says(0,ni_peers[0].nonce,0xffffffffu);assert(ni_peers[0].features==NETWORK_VR_FEATURES); /* (masked) */
 assert(network_interaction_player_vr(0,NETWORK_VR_RELOAD)&&network_interaction_player_vr(0,NETWORK_VR_MOVEMENT|NETWORK_VR_GRENADES));
 assert(!network_interaction_player_vr(1,NETWORK_VR_RELOAD)&&!network_interaction_player_vr(NONE,NETWORK_VR_RELOAD));
 assert(network_interaction_unit_manual_reload(0)&&!network_interaction_unit_manual_reload(1)&&!network_interaction_unit_manual_reload(NONE));
 /* VR INTERACTIONS off, or a PvP game: nothing, the host's own player's either */
 permission=0;assert(!network_interaction_player_vr(0,NETWORK_VR_RELOAD)&&!network_interaction_unit_manual_reload(0));
 assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD));permission=1;
 coop=0;assert(!network_interaction_player_vr(0,NETWORK_VR_MOVEMENT)&&!network_interaction_vr_allowed(NETWORK_VR_MOVEMENT));coop=1;
 /* a local game: everything; no game: nothing */
 connection=_game_connection_local;assert(network_interaction_vr_allowed(NETWORK_VR_FEATURES));
 assert(!network_interaction_player_vr(0,NETWORK_VR_RELOAD));connection=3;assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD));
 connection=_game_connection_network_server;
 /* reloads (player 0's unit 0 holds weapon 1, tag 71) */
 real_point3d at={{0,0,0}};real_vector3d still={{0,0,0}};
 act(0,10,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,3);assert(reload_commits==1&&committed_weapon==1); /* three copies, one commit */
 act(0,10,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);act(0,9,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==1);
 act(0,11,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==1); /* within 500 ms */
 now+=501;act(0,12,NETWORK_VR_ACTION_RELOAD,0,0,70,at,still,1);assert(reload_commits==1); /* another weapon's tag */
 act(0,13,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==2);
 /* a replay is refused as one, not only by the 500 ms: the same sequence, or an older one, after the interval */
 now+=501;act(0,13,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);act(0,11,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);
 assert(reload_commits==2);
 now+=501;units[0].unit.current_weapon_index=-1;act(0,14,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==2);
 units[0].unit.current_weapon_index=1;
 act(0,15,NETWORK_VR_ACTION_RELOAD,1,1,71,at,still,1);assert(reload_commits==2); /* another machine's player */
 act(0,16,NETWORK_VR_ACTION_RELOAD,0,1,71,at,still,1);assert(reload_commits==2); /* not its player's unit */
 units[0].object.damage_flags=1u<<_object_dead_bit;act(0,17,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==2);
 units[0].object.damage_flags=0;units[0].object.parent_object_index=5;act(0,18,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);
 assert(reload_commits==2);units[0].object.parent_object_index=NONE;
 says(0,ni_peers[0].nonce,NETWORK_VR_GRENADES);act(0,19,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==2); /* not said */
 says(0,ni_peers[0].nonce,NETWORK_VR_FEATURES);act(0,20,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==3);
 now+=501;permission=0;act(0,21,NETWORK_VR_ACTION_RELOAD,0,0,71,at,still,1);assert(reload_commits==3);permission=1; /* the toggle off */
 { struct ni_hand_wire w;memset(&w,0,sizeof(w));ni_header_init(&w.h,NI_ACTION,ni_peers[0].nonce,22);w.features=NETWORK_VR_ACTION_RELOAD;w.object=71;
   network_interaction_receive(0,37,&w,1,sizeof(w)-4);assert(reload_commits==3); } /* a short message */
 act(0,23,7,0,0,71,at,still,1);assert(reload_commits==3&&grenade_throws==0); /* an unknown action */
 refresh();assert(network_interaction_host_ready());
 /* grenades: the eyes at the unit's camera; 1.2 m is 0.394 units, 15 m/s 0.164 units a tick */
 units[0].object.position=(real_point3d){{1,2,3}};
 real_point3d near={{1.3f,2,3}},far={{1.4f,2,3}},bad={{NAN,2,3}};real_vector3d ok={{.15f,0,0}},fast={{.17f,0,0}},wild={{INFINITY,0,0}};
 act(0,30,NETWORK_VR_ACTION_GRENADE,0,0,0,near,ok,3);assert(grenade_throws==1&&thrown_type==0); /* three copies, one throw */
 act(0,31,NETWORK_VR_ACTION_GRENADE,0,0,1,near,ok,1);assert(grenade_throws==1); /* within 250 ms */
 now+=251;act(0,32,NETWORK_VR_ACTION_GRENADE,0,0,0,far,ok,1);assert(grenade_throws==1); /* out of reach */
 act(0,33,NETWORK_VR_ACTION_GRENADE,0,0,0,near,fast,1);act(0,34,NETWORK_VR_ACTION_GRENADE,0,0,0,bad,ok,1);
 act(0,35,NETWORK_VR_ACTION_GRENADE,0,0,0,near,wild,1);act(0,36,NETWORK_VR_ACTION_GRENADE,0,0,2,near,ok,1);
 act(0,37,NETWORK_VR_ACTION_GRENADE,0,0,-1,near,ok,1);assert(grenade_throws==1);
 act(0,38,NETWORK_VR_ACTION_GRENADE,0,0,1,near,ok,1);assert(grenade_throws==2&&thrown_type==1);
 now+=251;act(0,38,NETWORK_VR_ACTION_GRENADE,0,0,1,near,ok,1);act(0,30,NETWORK_VR_ACTION_GRENADE,0,0,0,near,ok,1);
 assert(grenade_throws==2); /* replays after the 250 ms: refused as replays */
 now+=251;says(0,ni_peers[0].nonce,NETWORK_VR_RELOAD);act(0,39,NETWORK_VR_ACTION_GRENADE,0,0,0,near,ok,1);assert(grenade_throws==2);
 says(0,ni_peers[0].nonce,NETWORK_VR_FEATURES);act(0,40,NETWORK_VR_ACTION_GRENADE,1,1,0,near,ok,1);assert(grenade_throws==2);
 act(1,41,NETWORK_VR_ACTION_GRENADE,0,0,0,near,ok,1);assert(grenade_throws==2); /* machine 1 for player 0 */
 /* fist blows (the striker's eyes at {1,2,3}: 2.5 m is 0.82 units; 0.6 m 0.197 units past a body's sphere;
    6.5 m/s 0.0711 units a tick) */
 bodies[2].object.bounding_sphere_center=(real_point3d){{1.5f,2,3}};bodies[3].object.bounding_sphere_center=(real_point3d){{2.0f,2,3}};
 real_point3d hit={{1.45f,2,3}},beyond={{1.95f,2,3}},beside={{1.1f,2,3}};real_vector3d along={{.6f,0,.8f}},nowhere={{NAN,0,0}};
 now+=1000;strike(50,2,hit,along,1.0f,1.2f,.03f,3);
 assert(strikes==1&&struck_unit==0&&struck_target==2&&struck_scale==1.0f&&struck_share==1.2f); /* three copies, one blow */
 assert(fabsf(struck_shove.i-.03f)<1e-6f&&struck_shove.j==0&&struck_shove.k==0); /* the shove along the blow, level */
 strike(51,2,hit,along,1.0f,1.0f,0,1);assert(strikes==1); /* within 60 ms */
 now+=61;strike(52,0,hit,along,1,1,0,1);assert(strikes==1); /* the striker itself */
 strike(53,20,hit,along,1,1,0,1);assert(strikes==1); /* no such body */
 strike(54,3,beyond,along,1,1,0,1);assert(strikes==1); /* on the body, but out of the striker's reach */
 strike(55,2,beside,along,1,1,0,1);assert(strikes==1); /* within reach, but not on that body */
 strike(56,2,hit,along,2.6f,1,0,1);strike(57,2,hit,along,1,6.1f,0,1);strike(58,2,hit,along,1,1,.072f,1);
 strike(59,2,hit,nowhere,1,1,0,1);strike(60,2,hit,along,-.1f,1,0,1);strike(61,2,hit,along,1,NAN,0,1);
 assert(strikes==1); /* strength, share, shove and direction out of bounds */
 says(0,ni_peers[0].nonce,NETWORK_VR_RELOAD);strike(62,2,hit,along,1,1,0,1);assert(strikes==1); /* melee not said */
 says(0,ni_peers[0].nonce,NETWORK_VR_FEATURES);strike(63,2,hit,along,2.5f,6.0f,.07f,1);
 assert(strikes==2&&struck_scale==2.5f&&struck_share==6.0f); /* a takedown at the bounds */
 now+=61;strike(63,2,hit,along,1,1,0,1);strike(50,2,hit,along,1,1,0,1);assert(strikes==2); /* replays */
 permission=0;strike(64,2,hit,along,1,1,0,1);assert(strikes==2);permission=1; /* the toggle off */
 assert(world_calls==0&&npc_calls==0); /* (actions are not hands) */
 puts("PASS: host: features from the machine's own player, nothing with VR INTERACTIONS off or in PvP; reloads once per sequence, on the held weapon's tag, every 500 ms, never another's; grenades within 1.2 m, 15 m/s, known types, every 250 ms; fist blows on another body within 2.5 m, its numbers bounded, every 60 ms, never replayed");
}
"""
client_main = r"""
static void from_host(word kind,uint32_t nonce,uint32_t sequence){struct ni_header h;ni_header_init(&h,kind,nonce,sequence);network_interaction_receive(NONE,38,&h,1,sizeof(h));}
int main(void){
 world_reset();connection=_game_connection_network_client;network_interaction_reset();
 vr_reload=vr_grenades=1;vr_climb=1;
 from_host(NI_OFFER,77,0);
 assert(to_host_count==2&&body_header(to_host[0].body).kind==NI_ACK);
 struct ni_header said=body_header(to_host[1].body);
 assert(said.kind==NI_CLIENT_FEATURES&&said.nonce==77&&said.sequence==(NETWORK_VR_RELOAD|NETWORK_VR_GRENADES|NETWORK_VR_MOVEMENT|NETWORK_VR_MELEE));
 assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD));
 from_host(NI_CONFIRM,77,1);assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD)); /* confirmed, nothing allowed yet */
 from_host(NI_FEATURES,78,NETWORK_VR_FEATURES);assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD)); /* another host's nonce */
 from_host(NI_FEATURES,77,NETWORK_VR_FEATURES);
 assert(network_interaction_vr_allowed(NETWORK_VR_RELOAD)&&network_interaction_vr_allowed(NETWORK_VR_GRENADES)&&
        network_interaction_vr_allowed(NETWORK_VR_MOVEMENT)&&network_interaction_vr_allowed(NETWORK_VR_MELEE));
 from_host(NI_FEATURES,77,NETWORK_VR_RELOAD);
 assert(network_interaction_vr_allowed(NETWORK_VR_RELOAD)&&!network_interaction_vr_allowed(NETWORK_VR_GRENADES)&&
        !network_interaction_vr_allowed(NETWORK_VR_RELOAD|NETWORK_VR_GRENADES));
 from_host(NI_CONFIRM,77,0);assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD)); /* the host withdrew */
 from_host(NI_CONFIRM,77,1);from_host(NI_FEATURES,77,NETWORK_VR_FEATURES);
 now+=6001;assert(!network_interaction_vr_allowed(NETWORK_VR_RELOAD)); /* the lease ran out */
 from_host(NI_CONFIRM,77,1);assert(network_interaction_vr_allowed(NETWORK_VR_RELOAD));
 /* an action: three copies of one sequence, to the host */
 to_host_count=0;real_point3d p={{1,2,3}};real_vector3d v={{.1f,0,0}};
 network_interaction_client_action(NETWORK_VR_ACTION_GRENADE,0,0,1,&p,&v);assert(to_host_count==3);
 for(int i=0;i<3;i++){struct ni_hand_wire w;assert(to_host[i].type==_distributed_message_vr_pose&&to_host[i].bytes==sizeof(w));
  memcpy(&w,to_host[i].body,sizeof(w));
  assert(w.h.kind==NI_ACTION&&w.h.nonce==77&&w.h.sequence==body_header(to_host[0].body).sequence);
  assert(w.features==NETWORK_VR_ACTION_GRENADE&&w.player==0&&w.unit==0&&w.object==1&&w.position.y==2&&w.forward.i==v.i);}
 network_interaction_client_action(NETWORK_VR_ACTION_RELOAD,0,0,71,NULL,NULL);assert(to_host_count==6);
 { struct ni_hand_wire a,b;memcpy(&a,to_host[0].body,sizeof(a));memcpy(&b,to_host[3].body,sizeof(b));
   assert(b.h.sequence==a.h.sequence+1&&b.features==NETWORK_VR_ACTION_RELOAD&&b.object==71&&b.position.x==0); }
 /* a fist blow: three copies, the numbers in the last vector (the shove as its speed) */
 { real_vector3d d={{.6f,0,.8f}},shove={{.03f,.04f,0}};network_interaction_client_strike(0,0,2,&p,&d,1.5f,2.0f,&shove);
   assert(to_host_count==9);struct ni_hand_wire s;memcpy(&s,to_host[8].body,sizeof(s));
   assert(s.h.kind==NI_ACTION&&s.features==NETWORK_VR_ACTION_STRIKE&&s.object==2&&s.position.z==3&&s.forward.k==.8f);
   assert(s.up.i==1.5f&&s.up.j==2.0f&&fabsf(s.up.k-.05f)<1e-6f);
   network_interaction_client_strike(0,0,2,NULL,&d,1,1,&shove);assert(to_host_count==9); } /* nowhere: nothing */
 now+=6001;network_interaction_client_action(NETWORK_VR_ACTION_RELOAD,0,0,71,NULL,NULL);assert(to_host_count==9); /* no lease */
 from_host(NI_CONFIRM,77,1);connection=_game_connection_network_server;
 network_interaction_client_action(NETWORK_VR_ACTION_RELOAD,0,0,71,NULL,NULL);assert(to_host_count==9); /* not a client */
 connection=_game_connection_network_client;
 /* a new host's offer: nothing allowed until it says so; the features follow the settings (melee always) */
 vr_reload=vr_grenades=vr_climb=0;to_host_count=0;from_host(NI_OFFER,79,0);
 assert(!network_interaction_vr_allowed(NETWORK_VR_MELEE)&&body_header(to_host[1].body).sequence==NETWORK_VR_MELEE);
 from_host(NI_CONFIRM,79,1);assert(!network_interaction_vr_allowed(NETWORK_VR_MELEE)); /* confirmed: the old host's features gone */
 from_host(NI_FEATURES,79,NETWORK_VR_MELEE);assert(network_interaction_vr_allowed(NETWORK_VR_MELEE)&&!network_interaction_vr_allowed(NETWORK_VR_RELOAD));
 vr_slide=1;from_host(NI_OFFER,79,0);assert(body_header(to_host[3].body).sequence==(NETWORK_VR_MELEE|NETWORK_VR_MOVEMENT));
 vr_slide=0;vr_wallrun=1;from_host(NI_OFFER,79,0);assert(body_header(to_host[5].body).sequence==(NETWORK_VR_MELEE|NETWORK_VR_MOVEMENT));
 vr_wallrun=0;vr_walljump=1;from_host(NI_OFFER,79,0);assert(body_header(to_host[7].body).sequence==(NETWORK_VR_MELEE|NETWORK_VR_MOVEMENT));
 puts("PASS: client: its features follow its settings, nothing allowed before the host's FEATURES, after its lease or a new host's offer; an action is three copies of one sequence, only to a confirmed host");
}
"""
flat_client_main = r"""
static void from_host(word kind,uint32_t nonce,uint32_t sequence){struct ni_header h;ni_header_init(&h,kind,nonce,sequence);network_interaction_receive(NONE,38,&h,1,sizeof(h));}
int main(void){
 world_reset();connection=_game_connection_network_client;network_interaction_reset();vr_reload=vr_grenades=vr_slide=1;
 from_host(NI_OFFER,77,0);assert(to_host_count==2&&body_header(to_host[1].body).kind==NI_CLIENT_FEATURES&&body_header(to_host[1].body).sequence==0);
 puts("PASS: a flat client uses none of the VR features (its settings are not read)");
}
"""
old_host_main = r"""
static void handshake_machine(int machine){network_interaction_tick();struct ni_header h;ni_header_init(&h,NI_ACK,ni_peers[machine].nonce,0);network_interaction_receive(machine,38,&h,1,sizeof(h));}
int main(void){
 world_reset();network_interaction_reset();handshake_machine(0);handshake_machine(1);assert(network_interaction_host_ready());
 unsigned char before[sizeof(ni_peers)];memcpy(before,ni_peers,sizeof(before));int sent=to_clients_count;
 struct ni_header h;ni_header_init(&h,11,ni_peers[0].nonce,15);network_interaction_receive(0,38,&h,1,sizeof(h)); /* NI_CLIENT_FEATURES */
 ni_header_init(&h,10,ni_peers[0].nonce,15);network_interaction_receive(0,38,&h,1,sizeof(h)); /* NI_FEATURES */
 struct ni_hand_wire w;memset(&w,0,sizeof(w));ni_header_init(&w.h,12,ni_peers[0].nonce,50);w.features=1;w.object=71; /* NI_ACTION */
 for(int i=0;i<3;i++)network_interaction_receive(0,37,&w,1,sizeof(w));
 network_interaction_tick();
 assert(!memcmp(before,ni_peers,sizeof(before))&&to_clients_count==sent&&world_calls==0&&npc_calls==0&&cancels==0);
 assert(reload_commits==0&&grenade_throws==0&&network_interaction_host_ready());
 puts("PASS: a Test72 host ignores the three new kinds: no state, no reply, no hand; its session goes on");
}
"""
old_client_main = r"""
static void from_host(word kind,uint32_t nonce,uint32_t sequence){struct ni_header h;ni_header_init(&h,kind,nonce,sequence);network_interaction_receive(NONE,38,&h,1,sizeof(h));}
int main(void){
 world_reset();connection=_game_connection_network_client;network_interaction_reset();
 from_host(NI_OFFER,77,0);assert(to_host_count==1); /* its ACK alone: it never says features */
 from_host(NI_CONFIRM,77,1);assert(ni_host_ready);uint32_t seen=ni_host_seen;now+=10;
 from_host(10,77,15);assert(ni_host_ready&&ni_host_seen==seen&&to_host_count==1); /* NI_FEATURES */
 puts("PASS: a Test72 client ignores the host's FEATURES and never says its own: the host gives it none");
}
"""


def build(name, text, defines=()):
    path = O / (name + '.c')
    path.write_text(text)
    subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Wno-unused-function', '-Wno-unused-variable',
                    '-Wno-unused-but-set-variable', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                    *defines, str(path), '-lm', '-o', str(O / name)], check=True)
    subprocess.run([str(O / name)], check=True)


new = prefix + strip(header) + strip(source) + callbacks
old = prefix + strip(old_header) + strip(old_source) + callbacks
build('host', new + host_main)
build('client_vr', new + client_main, ['-DHALO_VR'])
build('client_flat', new + flat_client_main)
build('old_host', old + old_host_main)
build('old_client', old + old_client_main)

# the host's on-foot bound: a co-op VR client's player that uses VR movement or fist combat (its lunges), which
# VR INTERACTIONS allows
dist = (R / 'port/linux/game/network_distributed.c').read_text()
bound = dist[dist.index('static void distributed_on_foot_bound('):dist.index('static real distributed_on_foot_fall_speed(')]
allow = bound[bound.index('network_interaction_player_vr('):]
assert 'network_interaction_player_vr(distributed_player_from_byte((byte)player_index), NETWORK_VR_MOVEMENT)' in allow
assert 'network_interaction_player_vr(distributed_player_from_byte((byte)player_index), NETWORK_VR_MELEE)' in allow
assert 'bound->speed = MIN(MAX(bound->speed, VR_MOVEMENT_SPEED), MAXIMUM_PREDICTED_SPEED);' in allow
assert 'bound->rise = UNIT_WORLD_BOUND;' in allow and bound.index('bound->rise_base =') < bound.index('network_interaction_player_vr(')
assert '#define VR_MOVEMENT_SPEED (12.0f / 3.048f / 30.0f)' in dist
# the gates that read the one toggle
weapons = (R / 'source/items/weapons.c').read_text()
commit = weapons[weapons.index('if (manual & VR_MANUAL_COMMIT) {'):weapons.index('Test70: the needler with MANUAL RELOAD')]
assert 'game_connection() == _game_connection_network_client' in commit and 'NETWORK_VR_ACTION_RELOAD' in commit
assert 'weapon_vr_reload_commit(weapon_index);' in commit
assert 'network_interaction_unit_manual_reload(weapon->object.parent_object_index)' in weapons
reload = (R / 'port/linux/game/vr_manual_reload.c').read_text()
assert 'network_interaction_vr_allowed(NETWORK_VR_RELOAD)' in reload
assert reload.count('reload_session_allowed()') >= 8 and 'game_connection() == _game_connection_local' not in reload
for name in ('vr_slide.c', 'vr_parkour.c'):
    assert 'network_interaction_vr_allowed(NETWORK_VR_MOVEMENT)' in (R / 'port/linux/game' / name).read_text(), name
extra = (R / 'port/linux/game/vr_extra_interaction.c').read_text()
assert 'network_interaction_vr_allowed(grenades?NETWORK_VR_GRENADES:NETWORK_VR_MELEE)' in extra
assert 'net.host_vr_actions' not in extra
# (the owner: "make it so everyone can do advanced fist combat": a client's fist combat runs, its shot deflection
# does not (the host's projectiles), and its knockdown or shove goes with the blow for the host to give)
assert 'return game_connection()==_game_connection_network_client?NONE:extra_player(TRUE);' in extra
assert 'scale_vector3d(&along,speed*units/(real)TICKS_PER_SECOND,&extra.remote_shove);' in extra
frame = (R / 'port/linux/src/vr_frame.c').read_text()
render = (R / 'port/linux/game/vr_render.c').read_text()
assert 'return vr.melee_speed > 0.0f && (!vr.network_game || vr.melee_multiplayer || vr.network_melee);' in frame
assert ('vr_set_network_melee(game_connection() != _game_connection_local &&\n'
        '\t\tnetwork_interaction_vr_allowed(NETWORK_VR_MELEE));') in render
# a client's blows: its own impact melee when the host allows it, each blow sent for the host to deal
assert ('vr_set_impact_melee_allowed(!network_game_distributed_client() ||\n'
        '\t\tnetwork_interaction_vr_allowed(NETWORK_VR_MELEE));') in render
units = (R / 'source/units/units.c').read_text()
apply = units[units.rindex('static boolean unit_vr_impact_melee_apply('):]  # (its definition, after its declaration)
apply = apply[apply.index('{'):apply.index('\n}\n')]
sent = apply[apply.index('if (game_connection() == _game_connection_network_client)'):]
sent = sent[:sent.index('return TRUE;')]
assert 'network_interaction_client_strike(unit->unit.player_index, unit_index, hit_object_index, &collision.point,' in sent
assert apply.index('vr_combat_hit(') < apply.index('if (game_connection() == _game_connection_network_client)') \
    < apply.index('object_cause_contact_damage(')  # (the combat's numbers taken, then nothing dealt here)
remote = units[units.index('boolean unit_vr_remote_strike('):]
remote = remote[:remote.index('\n}\n')]
assert units.index('boolean unit_vr_remote_strike(') < units.index('#ifdef HALO_VR\nstatic boolean unit_vr_impact_melee_target(')
assert 'damage_data.multiplier = multiplier;' in remote and 'object_cause_contact_damage(&damage_data, target_index' in remote
assert 'biped_accelerate(target_index, shove);' in remote and 'vr_combat_' not in remote
# VR INTERACTIONS on by default, and once for older configs
config = (R / 'port/linux/src/port_config.c').read_text()
assert '{ "net.physical_interactions", _config_boolean, "true",' in config
migration = config[config.index('void config_vr_interactions_default(void)'):]
migration = migration[:migration.index('\n}\n')]
assert 'if (config_boolean("net.vr_interactions_applied"))' in migration
assert 'config_write_boolean("net.physical_interactions", 1) && config_write_boolean("net.vr_interactions_applied", 1)' in migration
game = (R / 'source/game/game.c').read_text()
assert 'config_vr_interactions_default();' in game[game.index('void game_initialize('):game.index('void game_dispose(')]
print('PASS: the host\'s on-foot bound allows a VR client\'s movement and lunges only when VR INTERACTIONS does; reload, '
      'slide, parkour, grenades, melee and fist combat read the one toggle; a client\'s blow is sent, the host deals it; '
      'VR INTERACTIONS on by default (once for older configs)')
