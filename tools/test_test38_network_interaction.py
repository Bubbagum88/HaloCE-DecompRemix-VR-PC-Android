"""Replay actual optional decoder/host tick with counted authority callbacks.
Guest long32 wire ABI is reproduced explicitly on the host sanitizer target.
"""
from pathlib import Path
import re, subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/test38-network-interaction';O.mkdir(parents=True,exist_ok=True)
s=(R/'port/linux/game/network_interaction.c').read_text()
h=(R/'port/linux/game/network_interaction.h').read_text()
def strip(t):
 t=re.sub(r'^#include.*$','',t,flags=re.M)
 t=t.replace('unsigned long long','uint64_t').replace('unsigned long','uint32_t')
 return re.sub(r'\blong\b','int32_t',t)
prefix=r"""
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
#define HALO_PORT_MAXIMUM_NETWORK_MACHINES 128
#define MAXIMUM_TRACKED_PLAYERS 128
#define NUMBEROF(x) (sizeof(x)/sizeof((x)[0]))
#define VALID_INDEX(i,n) ((i)>=0&&(i)<(n))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define TEST_FLAG(x,b) ((x)&(1u<<(b)))
enum{_game_connection_network_server=1,_game_connection_network_client=2,_object_type_biped=1,_object_dead_bit=1,_distributed_message_vr_pose=37,_distributed_message_vr_capability=38,_distributed_to_host=1};
struct distributed_message_header{byte data[12];};
struct player_datum{int32_t unit_index;};
struct unit_datum{struct{int32_t player_index;}unit;struct{int type,parent_object_index,damage_flags;struct{int size;}node_matrices;real_point3d position;}object;};
static int connection=1,permission=1,coop=1,clients=1,sent,world_calls,npc_calls,cancels,accepted=1;
static uint32_t now=100;static struct player_datum players[128];static struct unit_datum units[128];
static byte sent_body[128],sent_caps[4][128];static int cap_count;static byte sent_type;
static uint32_t system_milliseconds(void){return now;}
static int game_connection(void){return connection;}static int network_coop_active(void){return coop;}
static int config_boolean(char const*k){assert(!strcmp(k,"net.physical_interactions"));return permission;}
static int32_t network_game_get_random_seed(void){return 42;}static int32_t network_game_get_number_of_games_played(void){return 2;}
static int game_time_get(void){return now/33;}
static short distributed_client_machines(int32_t*m,short max){assert(max>=clients);for(int i=0;i<clients;i++)m[i]=i;return clients;}
static struct player_datum*distributed_player(short p){return p>=0&&p<clients?&players[p]:NULL;}
static int distributed_machine_has_player(int32_t m,short p){return m==p&&m<clients;}
static int32_t distributed_player_from_byte(byte p){return p;}static byte distributed_player_to_byte(int32_t p){return p;}
static int distributed_object_index_valid(int32_t u){return u>=0&&u<128;}
static struct unit_datum*unit_try_and_get(int32_t u){return distributed_object_index_valid(u)?&units[u]:NULL;}
static struct unit_datum*unit_get(int32_t u){assert(distributed_object_index_valid(u));return &units[u];}
static void unit_get_camera_position(int32_t u,real_point3d*p){*p=units[u].object.position;}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static float magnitude3d(real_vector3d const*v){return sqrtf(v->i*v->i+v->j*v->j+v->k*v->k);}
static int distributed_point_valid(real_point3d const*p,float bound){return isfinite(p->x)&&isfinite(p->y)&&isfinite(p->z)&&fabsf(p->x)<=bound&&fabsf(p->y)<=bound&&fabsf(p->z)<=bound;}
static int distributed_transform_valid(real_point3d const*p,real_vector3d const*f,real_vector3d const*u,void*v,void*w,real_vector3d*outf,real_vector3d*outu){if(!distributed_point_valid(p,32768)||!isfinite(magnitude3d(f))||!isfinite(magnitude3d(u)))return 0;*outf=*f;*outu=*u;return 1;}
static void cross_product3d(real_vector3d const*a,real_vector3d const*b,real_vector3d*c){*c=(real_vector3d){{a->j*b->k-a->k*b->j,a->k*b->i-a->i*b->k,a->i*b->j-a->j*b->i}};}
static void distributed_send(void*p,byte t,short c,word size,int dest){sent++;}
static void distributed_send_to_machine(int32_t m,void*p,byte t,short c,word size){sent++;sent_type=t;if(size>=sizeof(struct distributed_message_header)&&size-sizeof(struct distributed_message_header)<=sizeof(sent_body)){byte*body=(byte*)p+sizeof(struct distributed_message_header);memcpy(sent_body,body,size-sizeof(struct distributed_message_header));if(t==_distributed_message_vr_capability&&size-sizeof(struct distributed_message_header)==24)memcpy(sent_caps[cap_count++%4],body,24);}}
static real_matrix4x3 testroot,palette[64];
static real_matrix4x3*object_get_node_matrices(int32_t u){return palette;}
static real_matrix4x3*object_get_world_matrix(int32_t u,real_matrix4x3*m){*m=testroot;return m;}
static void matrix4x3_inverse(real_matrix4x3 const*a,real_matrix4x3*b){*b=*a;}
static void matrix4x3_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){*out=*p;}
int vr_world_interaction_remote_contact(int32_t p,int hand,int32_t*object,float local[3]);
int vr_npc_interaction_remote_contact(int32_t p,int hand,int32_t*object,float world[3]);
static void matrix4x3_rotation_to_quaternion(real_matrix4x3 const*m,real_quaternion*q){memset(q,0,sizeof(*q));}
static void matrix4x3_rotation_from_quaternion(real_matrix4x3*m,real_quaternion const*q){memset(m,0,sizeof(*m));m->forward.i=1;m->left.j=1;m->up.k=1;}
static void quaternions_interpolate_and_normalize(real_quaternion const*a,real_quaternion const*b,float t,real_quaternion*q){*q=*a;}
"""
callbacks=r"""
boolean vr_world_interaction_remote(struct network_interaction_hand const*r){world_calls++;return r->held&&accepted;}
void vr_world_interaction_remote_cancel(int32_t p,int h){cancels++;}
int vr_npc_interaction_remote(int32_t p,int h,int held,float const*w){npc_calls++;return 0;}
void vr_npc_interaction_remote_cancel(int32_t p,int h){cancels++;}
int vr_npc_interaction_snapshot(int32_t*i,int*c,real_matrix4x3*m,int cap){return 0;}
void vr_interaction_client_reset(void){}void vr_interaction_client_tick(boolean b,boolean n){}
void vr_interaction_client_result(int32_t u,byte h,byte f,uint32_t s,int32_t object,float const local[3]){}
int vr_world_interaction_remote_contact(int32_t p,int hand,int32_t*object,float local[3]){return 0;}
int vr_npc_interaction_remote_contact(int32_t p,int hand,int32_t*object,float world[3]){return 0;}
void platform_log(char const*f,...){}
"""
main=r"""
static void handshake_machine(int machine){network_interaction_tick();struct ni_header ack;ni_header_init(&ack,NI_ACK,ni_peers[machine].nonce,0);network_interaction_receive(machine,38,&ack,1,sizeof(ack));}
static void handshake(void){handshake_machine(0);assert(network_interaction_host_ready());assert(network_interaction_npc_ready());}
static void input(uint32_t seq,int held){struct ni_hand_wire w={0};ni_header_init(&w.h,NI_HAND,ni_peers[0].nonce,seq);w.unit=0;w.player=0;w.hand=0;w.held=held;w.features=3;w.forward.i=1;w.up.k=1;network_interaction_receive(0,37,&w,1,sizeof(w));}
int main(void){
 for(int i=0;i<128;i++){players[i].unit_index=i;units[i].unit.player_index=i;units[i].object.type=1;units[i].object.parent_object_index=NONE;}
 network_interaction_reset();assert(!network_interaction_host_ready());handshake();
 input(1,1);network_interaction_tick();assert(world_calls==0); /* held at join no press */
 input(2,0);network_interaction_tick();assert(world_calls==1);
 input(3,1);input(4,1);network_interaction_tick();assert(world_calls==2&&ni_hands[0][0].active); /* edge survives batching */
 int old=world_calls;input(4,0);network_interaction_tick();assert(world_calls==old+1&&ni_hands[0][0].request.held); /* replay rejected */
 now+=301;network_interaction_tick();assert(cancels==2&&!ni_hands[0][0].valid);
 old=world_calls;input(5,1);network_interaction_tick();assert(world_calls==old); /* timeout requires real release */
 input(6,0);network_interaction_tick();input(7,1);network_interaction_tick();assert(ni_hands[0][0].active);
 clients=5;now+=2000;network_interaction_tick();for(int i=1;i<5;i++)handshake_machine(i);
 assert(network_interaction_host_ready());assert(!network_interaction_npc_ready());
 assert(sent_type==_distributed_message_vr_capability&&cap_count>=2);
 struct ni_header confirm,npc_confirm;
 memcpy(&confirm,sent_caps[(cap_count-2)%4],sizeof(confirm));
 memcpy(&npc_confirm,sent_caps[(cap_count-1)%4],sizeof(npc_confirm));
 assert(confirm.kind==NI_CONFIRM&&confirm.sequence==1&&npc_confirm.kind==NI_NPC_CONFIRM&&npc_confirm.sequence==0);
 connection=_game_connection_network_client;ni_host_nonce=confirm.nonce;ni_host_ready=ni_host_npc_ready=FALSE;
 network_interaction_receive(NONE,_distributed_message_vr_capability,&confirm,1,sizeof(confirm));
 network_interaction_receive(NONE,_distributed_message_vr_capability,&npc_confirm,1,sizeof(npc_confirm));
 assert(ni_host_ready&&!ni_host_npc_ready&&!network_interaction_npc_ready());connection=_game_connection_network_server;
 int world_before=world_calls;input(8,0);network_interaction_tick();input(9,1);network_interaction_tick();
 assert(world_calls==world_before+2&&npc_calls>0&&ni_hands[0][0].active); /* NPC denied; world remains available above four peers */
 ni_peers[1].ready=FALSE;assert(!network_interaction_host_ready());ni_peers[1].ready=TRUE;
 clients=2;assert(network_interaction_host_ready()&&network_interaction_npc_ready());
 now+=301;network_interaction_tick();assert(!ni_hands[0][0].active);clients=1;
 clients=128;now+=2000;network_interaction_tick();for(int i=5;i<128;i++)handshake_machine(i);
 assert(network_interaction_host_ready()&&!network_interaction_npc_ready()); /* bounded world authority handles full native machine limit */
 permission=0;assert(!network_interaction_host_ready());permission=1;
 struct ni_hand_wire w={0};ni_header_init(&w.h,NI_HAND,ni_peers[0].nonce,100);w.unit=0;w.features=1;w.forward.i=1;w.up.k=1;
 uint32_t seq=ni_hands[0][0].sequence;
 w.position.x=NAN;network_interaction_receive(0,37,&w,1,sizeof(w));assert(ni_hands[0][0].sequence==seq);
 w.position.x=10;network_interaction_receive(0,37,&w,1,sizeof(w));assert(ni_hands[0][0].sequence==seq);
 w.position.x=0;w.player=1;network_interaction_receive(0,37,&w,1,sizeof(w));assert(ni_hands[0][0].sequence==seq);
 w.player=0;w.h.nonce++;network_interaction_receive(0,37,&w,1,sizeof(w));assert(ni_hands[0][0].sequence==seq);
 connection=2;network_interaction_reset();ni_host_nonce=99;ni_host_ready=TRUE;ni_host_seen=now;
 units[2].unit.player_index=NONE;units[2].object.type=1;units[2].object.parent_object_index=NONE;units[2].object.node_matrices.size=2*sizeof(real_matrix4x3);
 struct ni_joint j={0};ni_header_init(&j.h,NI_JOINT,99,1);j.unit=2;j.count=2;j.cadence_ms=67;j.scale=1;j.forward.i=1;j.up.k=1;
 network_interaction_receive(NONE,37,&j,1,sizeof(j));assert(!ni_poses[0].valid);
 j.node=1;network_interaction_receive(NONE,37,&j,1,sizeof(j));assert(ni_poses[0].valid&&ni_poses[0].count==2);
 j.h.sequence=2;j.node=64;network_interaction_receive(NONE,37,&j,1,sizeof(j));assert(ni_poses[0].sequence==1);
 j.node=0;j.count=65;network_interaction_receive(NONE,37,&j,1,sizeof(j));assert(ni_poses[0].sequence==1);
 j.count=2;j.position.x=NAN;network_interaction_receive(NONE,37,&j,1,sizeof(j));assert(ni_poses[0].sequence==1);
 j.position.x=0;j.h.seed++;network_interaction_receive(NONE,37,&j,1,sizeof(j));assert(ni_poses[0].sequence==1);
 ni_host_ready=ni_host_npc_ready=TRUE;assert(network_interaction_palette_owned(2));network_interaction_palette(2);
 real_matrix4x3 stock[2]={0};assert(network_interaction_render(2,stock)!=stock);now+=501;assert(!network_interaction_palette_owned(2));assert(network_interaction_render(2,stock)==stock);
 puts("PASS: actual network handshake, sender/epoch/lease/range/replay validation, fresh grips, mixed-peer fallback and bounded joint assembly");
}
"""
p=O/'network.c';p.write_text(prefix+strip(h)+strip(s)+callbacks+main)
subprocess.run(['clang','-std=gnu11','-O1','-fsanitize=address,undefined',str(p),'-lm','-o',str(O/'network')],check=True)
subprocess.run([str(O/'network')],check=True)

import xml.etree.ElementTree as ET
xml=ET.parse(R/'port/assets/menus/ce/main_menu.multiplayer_type_select.server_settings.xml').getroot()
# Test66: OpenCE Build 201's Server Setup groups co-op's options on their own
# CO-OP OPTIONS screen (shown only when hosting co-op); VR INTERACTIONS and
# HOST VR ACTIONS are its last two rows, after Build 201's own five, so the
# upstream rows keep their label and help indices.
strings={n.attrib['name'].rsplit('/',1)[-1]:n for n in xml.findall('strings')}
widgets={n.attrib['name'].rsplit('/',1)[-1]:n for n in xml.findall('widget')}
labels=strings['coop_options_labels']
assert [n.attrib['text'] for n in labels][:5]==['FRIENDLY FIRE:','EXTRA ENEMIES:','PER PLAYER:','MULTIPLIER:','PLAYER COLLISIONS:']
assert labels[5].attrib['text']=='VR INTERACTIONS:' and labels[6].attrib['text']=='HOST VR ACTIONS:'
coop_menu=widgets['coop_options_menu']
assert coop_menu.find('data').attrib['input']=='game settings lists text update'
rows=[c.attrib['widget'].rsplit('/',1)[-1] for c in coop_menu.findall('child')]
assert rows.index('op_coop_player_collisions')<rows.index('op_physical_interactions')<rows.index('op_host_vr_actions')<rows.index('coop_options_button_bar')
row=widgets['physical_interactions_spinner']
assert row.attrib['setting']=='net.physical_interactions' and row.attrib['values']=='false|true'
assert widgets['physical_interactions_label'].attrib['string_index']=='5'
assert 'NI_MAGIC=0x56494e31' in s and 'VR_POSE_MAGIC = 0x56525031' in (R/'port/linux/game/network_vr_pose.c').read_text()
assert '#ifdef HALO_VR' not in s
print('PASS: separate magic, common flat/VR authority and the host setting appended to CO-OP OPTIONS (upstream indices kept)')

# Test62: the new permission is an appended native co-op setup row; preserve
# original indices, mouse navigation, persistence and PvP visibility.
row=widgets['host_vr_actions_spinner']
assert row.attrib['setting']=='net.host_vr_actions' and row.attrib['values']=='false|true'
for name in ('physical_interactions_spinner','host_vr_actions_spinner'):
    assert {(n.attrib['event'],n.attrib['run']) for n in widgets[name].findall('on')} >= {
        ('created','port setting load'),('deleted','port setting save'),
        ('left_mouse','mouse spinner 1wide click')}, name
assert widgets['host_vr_actions_label'].attrib['string_index']=='6'
# (the screen's help is each row's values' helps in turn: Build 201's five
# rows have 4+3+5+5+2 values, so VR INTERACTIONS' are 19-20, HOST's 21-22)
help_strings=strings['cap_coop_options']
assert len(help_strings)==23
assert 'physical co-op' in help_strings[19].attrib['text'].lower() and 'physical co-op' in help_strings[20].attrib['text'].lower()
assert 'host' in help_strings[21].attrib['text'].lower() and 'host' in help_strings[22].attrib['text'].lower()
assert 'VR interactions' in strings['help_strings'][12].attrib['text']
menu=(R/'port/linux/game/menu_functions.c').read_text()
assert 'visible_set(named(list, "op_coop_options", 0), cooperative);' in menu
assert 'index += spinner->parameters.list.number_of_items;' in menu
print('PASS: Test62 host permission native row, help, saved setting, mouse and co-op visibility wiring')
