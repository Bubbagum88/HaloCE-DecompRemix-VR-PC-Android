/* Local input adapter only: all authority and decoding lives in network_interaction. */
#include "cseries.h"
#include "network_interaction.h"
#ifdef HALO_VR
#include "game/game.h"
#include "game/players.h"
#include "units/units.h"
#include "objects/objects.h"
#include "network_distributed.h"
#include "../src/vr.h"
#include "../src/port_config.h"
static long local_unit=NONE,local_player=NONE;
static int down[2]={1,1},owner[2];
static unsigned long last_result[2],contact_time[2];
static long contact_object[2]={NONE,NONE};
static real_point3d contact_local[2];
unsigned long system_milliseconds(void);
void vr_interaction_client_reset(void)
{
    for(int h=0;h<2;h++){if(local_unit!=NONE)network_interaction_client_cancel(h,local_player,local_unit);if(owner[h])vr_interaction_release(h,owner[h]);owner[h]=0;down[h]=1;last_result[h]=0;contact_object[h]=NONE;}
    local_unit=local_player=NONE;
}
void vr_interaction_client_result(long unit,byte hand,byte features,unsigned long sequence,long object,float const local[3])
{
    if(hand>1||features>2||unit!=local_unit||(last_result[hand]&&(long)(sequence-last_result[hand])<=0))return;
    last_result[hand]=sequence;
    int next=features==1?VR_INTERACTION_WORLD:features==2?VR_INTERACTION_NPC:0;
    if(owner[hand]&&next!=owner[hand])vr_interaction_release(hand,owner[hand]);
    owner[hand]=next&&vr_interaction_claim(hand,next)?next:0;
    contact_object[hand]=owner[hand]&&distributed_object_index_valid(object)?object:NONE;
    memcpy(contact_local[hand].n,local,sizeof(contact_local[hand]));contact_time[hand]=system_milliseconds();
}
long vr_interaction_client_object(int hand)
{
    if(hand<0||hand>1||!owner[hand]||vr_interaction_owner(hand)!=owner[hand]||
       system_milliseconds()-contact_time[hand]>300||!distributed_object_index_valid(contact_object[hand]))return NONE;
    return contact_object[hand];
}
int vr_interaction_client_hand(int hand,float point[3])
{
    long object=vr_interaction_client_object(hand);
    if(object==NONE)return 0;
    real_matrix4x3 root;real_point3d world;
    if(!distributed_point_valid(&contact_local[hand],8))return 0;
    object_get_world_matrix(object,&root);
    matrix4x3_transform_point(&root,&contact_local[hand],&world);
    if(!distributed_point_valid(&world,32768))return 0;
    memcpy(point,world.n,sizeof(world));return 1;
}
void vr_interaction_client_tick(boolean ready)
{
    short local=local_player_get_next(NONE);long player=local!=NONE?local_player_get_player_index(local):NONE;
    struct player_datum *p=player!=NONE?player_get(player):NULL;unsigned int buttons;float triggers[2],sticks[4];
    int valid=ready&&p&&p->unit_index!=NONE&&vr_aiming()&&vr_controller(&buttons,triggers,sticks);
    if(!valid||local_unit!=p->unit_index){vr_interaction_client_reset();if(!valid)return;local_unit=p->unit_index;local_player=player;}
    real_point3d camera;unit_get_camera_position(local_unit,&camera);
    for(int h=0;h<2;h++) {
        real_point3d point;real_vector3d forward,up;
        int held=vr_interaction_grip(h,NULL,NULL),current=vr_interaction_owner(h);
        int allowed=(!current||current==owner[h])&&(h!=vr_weapon_hand()||vr_hand_empty())&&
            !(h!=vr_weapon_hand()&&vr_two_handed());
        /* Losing eligibility is cancellation, never an intentional release throw.
         * Stop refreshing the host lease and require a new physical grip. */
        if(!allowed) {
            if(!down[h])network_interaction_client_cancel(h,player,local_unit);
            if(owner[h])vr_interaction_release(h,owner[h]);
            owner[h]=0;down[h]=1;continue;
        }
        if(!vr_hand_world(h,camera.n,point.n,forward.n,up.n)) {
            if(!down[h])network_interaction_client_cancel(h,player,local_unit);
            down[h]=1;continue;
        }
        if(held&&down[h])continue;
        if(!held)down[h]=0;
        byte features=(config_boolean("vr.world_interaction")?NETWORK_INTERACTION_WORLD:0)|
            (config_boolean("vr.npc_interaction")?NETWORK_INTERACTION_NPC:0);
        if(features)network_interaction_client_send(h,held&&!down[h],features,player,local_unit,&point,&forward,&up);
    }
}
#else
void vr_interaction_client_reset(void){}
void vr_interaction_client_result(long unit,byte hand,byte features,unsigned long sequence,long object,float const local[3]){}
void vr_interaction_client_tick(boolean ready){}
int vr_interaction_client_hand(int hand,float point[3]){return 0;}
long vr_interaction_client_object(int hand){return NONE;}
#endif
