"""Actual client adapter: lost eligibility never masquerades as release/throw."""
from pathlib import Path
import re,subprocess
R=Path(__file__).resolve().parents[1];O=R/'build/test38-network-input';O.mkdir(parents=True,exist_ok=True)
s=(R/'port/linux/game/vr_interaction_client.c').read_text().split('#ifdef HALO_VR',1)[1].split('#else',1)[0]
s=re.sub(r'^#include.*$','',s,flags=re.M)
prefix=r"""
#include <assert.h>
#include <string.h>
#include <stdint.h>
typedef unsigned char boolean,byte;typedef struct{float n[3];}real_point3d,real_vector3d;
typedef struct{real_point3d position;real_vector3d forward,left,up;float scale;}real_matrix4x3;
static real_matrix4x3 root;static unsigned long now;
static unsigned long system_milliseconds(void){return now;}
static int distributed_object_index_valid(long object){return object==12;}
static int distributed_point_valid(real_point3d const*p,float bound){return 1;}
static real_matrix4x3*object_get_world_matrix(long object,real_matrix4x3*m){*m=root;return m;}
static void matrix4x3_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){for(int i=0;i<3;i++)out->n[i]=m->position.n[i]+m->scale*(p->n[0]*m->forward.n[i]+p->n[1]*m->left.n[i]+p->n[2]*m->up.n[i]);}
#define NONE -1
#define NETWORK_INTERACTION_WORLD 1
#define NETWORK_INTERACTION_NPC 2
#define VR_INTERACTION_WORLD 3
#define VR_INTERACTION_NPC 5
struct player_datum{long unit_index;};static struct player_datum player={10};
static int focused=1,grips[2],tracked[2]={1,1},owners[2],twohanded,empty=1;
static int sends,cancels,releases,lastheld;
static short local_player_get_next(int x){return 0;}static long local_player_get_player_index(int x){return 0;}
static struct player_datum*player_get(long p){return &player;}
static int vr_aiming(void){return 1;}static int vr_controller(unsigned int*b,float*t,float*s){return focused;}
static void unit_get_camera_position(long u,real_point3d*p){memset(p,0,sizeof(*p));}
static int vr_interaction_grip(int h,void*p,void*r){return grips[h];}
static int vr_interaction_owner(int h){return owners[h];}
static int vr_weapon_hand(void){return 1;}static int vr_hand_empty(void){return empty;}
static int vr_two_handed(void){return twohanded;}
static void vr_interaction_release(int h,int o){if(owners[h]==o)owners[h]=0;releases++;}
static int vr_interaction_claim(int h,int o){if(!focused||!tracked[h]||!grips[h])return 0;owners[h]=o;return 1;}
static int vr_hand_world(int h,float*c,float*p,float*f,float*u){memset(p,0,12);memset(f,0,12);memset(u,0,12);return tracked[h];}
static int config_boolean(char const*k){return !strcmp(k,"vr.world_interaction");}
static void network_interaction_client_send(byte h,byte held,byte f,long p,long u,real_point3d const*point,real_vector3d const*fw,real_vector3d const*up){sends++;lastheld=held;}
static void network_interaction_client_cancel(byte h,long p,long u){cancels++;}
"""
main=r"""
int main(void){
 grips[0]=1;vr_interaction_client_tick(1);assert(sends==1); /* other released hand only */
 grips[0]=0;vr_interaction_client_tick(1);grips[0]=1;vr_interaction_client_tick(1);
 vr_interaction_client_result(10,0,1,1,12,(float[3]){.1f,.2f,.3f});assert(owners[0]==3);
 int before=sends;twohanded=1;vr_interaction_client_tick(1);assert(sends==before+1&&cancels==1&&owners[0]==0);
 twohanded=0;before=sends;vr_interaction_client_tick(1);assert(sends==before+1); /* held return cannot emit fake release */
 grips[0]=0;vr_interaction_client_tick(1);grips[0]=1;vr_interaction_client_tick(1);vr_interaction_client_result(10,0,1,2,12,(float[3]){.1f,.2f,.3f});
 tracked[0]=0;before=cancels;vr_interaction_client_tick(1);assert(cancels==before+1);
 tracked[0]=1;before=sends;vr_interaction_client_tick(1);assert(sends==before+1);
 focused=0;before=sends;vr_interaction_client_tick(1);assert(sends==before&&owners[0]==0);
 focused=1;before=sends;vr_interaction_client_tick(1);assert(sends==before+1);
 grips[0]=0;vr_interaction_client_tick(1);grips[0]=1;vr_interaction_client_tick(1);
 vr_interaction_client_result(10,0,1,8,12,(float[3]){.1f,.2f,.3f});assert(owners[0]==3);vr_interaction_client_result(10,0,0,7,12,(float[3]){.1f,.2f,.3f});assert(owners[0]==3);
 vr_interaction_client_result(11,0,0,9,12,(float[3]){.1f,.2f,.3f});assert(owners[0]==3);
 float point[3];root.position.n[0]=3;root.scale=2;root.forward.n[1]=1;root.left.n[0]=-1;root.up.n[2]=1;
 assert(vr_interaction_client_hand(0,point)&&point[0]>2.59f&&point[0]<2.61f&&point[1]>.19f&&point[1]<.21f);
 now=301;assert(!vr_interaction_client_hand(0,point));
 return 0;}
"""
p=O/'input.c';p.write_text(prefix+s+main)
subprocess.run(['clang','-std=gnu11','-O1','-fsanitize=address,undefined',str(p),'-o',str(O/'input')],check=True)
subprocess.run([str(O/'input')],check=True)
print('PASS: production remote input cancels on ineligibility/focus/tracking, requires fresh grip, rejects stale/wrong-unit results')
