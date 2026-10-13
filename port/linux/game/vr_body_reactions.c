/* Test65: ACTIVE RAGDOLL (vr.active_ragdoll): the owner asked that touching
 * allies and NPCs move their bodies, that hits make bodies react, and that
 * bodies behave more like GTA's Euphoria. A living body touched, held by a
 * limb (not lifted) or struck gives where it was touched: the limb nearest
 * the contact swings with the push about its root (the shoulder or hip) and
 * the torso leans away, quickly, then eases back as the body recovers. Drawn
 * only (render_objects.c): its collision, animation, AI and network state stay
 * the engine's; the physical shove and the ragdolls are the NPC module's.
 * Fixed storage, no allocation; a reaction outlives nothing it names. */
#ifdef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "objects/objects.h"
#include "objects/object_definitions.h"
#include "models/models.h"
#include "models/model_definitions.h"
#include "units/units.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_body_reactions.h"
#include <math.h>
#include <string.h>
void platform_log(char const *format,...);

#define VR_BODY_REACTIONS 16
static struct body_reaction {
    long object;
    short limb,tip;           /* the limb's root and the node touched (NONE: the torso alone) */
    short torso;              /* the spine node the torso leans about (NONE: none) */
    real_vector3d push;       /* the push's direction (unit) */
    real limb_angle,lean;     /* peaks (radians) */
    double start,until;       /* vr_pose_time */
    int holding;              /* a hand holds the limb: aimed at target */
    real_point3d target;
} reactions[VR_BODY_REACTIONS];

int vr_body_reactions_enabled(void)
{
    return config_boolean("vr.active_ragdoll");
}

void vr_body_reactions_reset(void)
{
    memset(reactions,0,sizeof(reactions));
    for(int n=0;n<VR_BODY_REACTIONS;++n) reactions[n].object=NONE;
}

static struct model *reaction_model(long object,short *count)
{
    struct object_datum *o=object_try_and_get(object);
    struct object_definition *definition;
    struct model *model;
    if(!o||o->object.type!=_object_type_biped)return NULL;
    definition=object_definition_get(o->definition_index);
    if(!definition||definition->object.model.index==NONE)return NULL;
    model=model_definition_get(definition->object.model.index);
    *count=(short)(o->object.node_matrices.size/(long)sizeof(real_matrix4x3));
    if(*count<=1||*count>MAXIMUM_NODES_PER_MODEL||model->nodes.count!=*count)return NULL;
    return model;
}

static short node_parent(struct model *model,short node)
{
    return TAG_BLOCK_GET_ELEMENT(&model->nodes,node,struct model_node)->parent_node_index;
}

static boolean node_named(struct model *model,short node,char const *part)
{
    return strstr(TAG_BLOCK_GET_ELEMENT(&model->nodes,node,struct model_node)->name,part)!=NULL;
}

/* the limb a node belongs to: its highest ancestor below the torso that is
 * an upper arm, a thigh or the neck (a Grunt's "bip01 l upperarm", an
 * Elite's "frame l upperarm"); NONE for the torso itself */
static short limb_root(struct model *model,short count,short node)
{
    short limb=NONE,steps=0;
    for(short n=node;n>0&&n<count&&steps<count;n=node_parent(model,n),++steps) {
        if(node_named(model,n,"spine")||node_named(model,n,"pelvis"))break;
        if(node_named(model,n,"upperarm")||node_named(model,n,"thigh")||node_named(model,n,"neck")||
           node_named(model,n,"clavicle"))limb=n;
    }
    return limb;
}

static short torso_node(struct model *model,short count)
{
    for(short n=0;n<count;++n) if(node_named(model,n,"spine"))return n;
    return NONE;
}

static struct body_reaction *reaction_slot(long object)
{
    struct body_reaction *oldest=&reactions[0];
    double now=vr_pose_time();
    for(int n=0;n<VR_BODY_REACTIONS;++n) {
        if(reactions[n].object==object)return &reactions[n];
    }
    for(int m=0;m<VR_BODY_REACTIONS;++m) {
        if(reactions[m].object==NONE||now>reactions[m].until)return &reactions[m];
        if(reactions[m].until<oldest->until)oldest=&reactions[m];
    }
    return oldest;
}

void vr_body_reaction_hit(long object,real_point3d const *point,real_vector3d const *push,real strength)
{
    struct body_reaction *r;
    struct model *model;
    real_matrix4x3 *nodes;
    real_vector3d direction;
    short count,nearest=NONE;
    real best=1e30f;
    double now=vr_pose_time();
    if(!vr_body_reactions_enabled()||!point||!push||!valid_real_point3d(point)||!(strength>0.0f)||
       !(model=reaction_model(object,&count))||!(nodes=object_get_node_matrices(object)))return;
    if(TEST_FLAG(object_get(object)->object.damage_flags,_object_dead_bit))return;
    direction=*push;
    if(!valid_real_vector3d(&direction)||!(normalize3d(&direction)>0.0001f))return;
    strength=PIN(strength,0.0f,1.0f);
    for(short n=1;n<count;++n) {
        real d=distance_squared3d(&nodes[n].position,point);
        if(d<best){best=d;nearest=n;}
    }
    r=reaction_slot(object);
    /* a weaker blow does not cut short a stronger one still swinging */
    if(r->object==object&&now<r->until&&!r->holding&&r->limb_angle>strength*0.7f&&now-r->start<0.12)return;
    memset(r,0,sizeof(*r));
    r->object=object;
    r->tip=nearest;
    r->limb=nearest!=NONE?limb_root(model,count,nearest):NONE;
    r->torso=torso_node(model,count);
    r->push=direction;
    r->limb_angle=0.75f*strength;
    r->lean=0.08f+0.30f*strength;
    r->start=now;
    r->until=now+0.25+0.45*strength;
}

void vr_body_reaction_hold(long object,short node,real_point3d const *target)
{
    struct body_reaction *r;
    struct model *model;
    short count;
    double now=vr_pose_time();
    if(!vr_body_reactions_enabled()||!target||!valid_real_point3d(target)||
       !(model=reaction_model(object,&count))||node<=0||node>=count)return;
    r=reaction_slot(object);
    if(r->object!=object||!r->holding||r->tip!=node) {
        memset(r,0,sizeof(*r));
        r->object=object;r->tip=node;r->limb=limb_root(model,count,node);r->torso=torso_node(model,count);
        r->holding=1;r->start=now;
    }
    r->target=*target;
    /* held while refreshed (each tick); let go, it eases back */
    r->until=now+0.25;
}

/* turns the subtree under `root` about `pivot` by `angle` about `axis` */
static void turn_subtree(struct model *model,short count,real_matrix4x3 *pose,short root,
    real_point3d const *pivot,real_vector3d const *axis,real angle)
{
    real c=cosf(angle),s=sinf(angle);
    if(!(fabsf(angle)>0.0005f))return;
    for(short n=0;n<count;++n) {
        short parent=n,steps=0;
        while(parent!=root&&parent>=0&&parent<count&&steps++<count)parent=node_parent(model,parent);
        if(parent!=root)continue;
        {
            real_vector3d p;
            real_vector3d *vectors[4];
            vector_from_points3d(pivot,&pose[n].position,&p);
            vectors[0]=&p;vectors[1]=&pose[n].forward;vectors[2]=&pose[n].left;vectors[3]=&pose[n].up;
            for(int v=0;v<4;++v) {
                real_vector3d original=*vectors[v],cross;
                real dot=dot_product3d(axis,&original);
                cross_product3d(axis,&original,&cross);
                for(int k=0;k<3;++k)vectors[v]->n[k]=original.n[k]*c+cross.n[k]*s+axis->n[k]*dot*(1-c);
            }
            point_from_line3d(pivot,&p,1,&pose[n].position);
        }
    }
}

real_matrix4x3 *vr_body_reaction_render(long object,real_matrix4x3 *stock)
{
    static real_matrix4x3 pose[MAXIMUM_NODES_PER_MODEL];
    struct body_reaction *r=NULL;
    struct model *model;
    short count;
    double now,age;
    real amount;
    if(!stock||object==NONE)return stock;
    for(int n=0;n<VR_BODY_REACTIONS;++n) if(reactions[n].object==object){r=&reactions[n];break;}
    if(!r)return stock;
    now=vr_pose_time();
    if(now>r->until+0.35||now<r->start-1.0){r->object=NONE;return stock;}
    if(!vr_body_reactions_enabled()||!(model=reaction_model(object,&count))||
       TEST_FLAG(object_get(object)->object.damage_flags,_object_dead_bit))return stock;
    memcpy(pose,stock,count*sizeof(*pose));
    age=now-r->start;
    if(r->holding) {
        /* the held limb reaches toward the hand (at most ~45 degrees), the
         * torso leaning a little after it; eased in and, let go, back out */
        real in=(real)PIN(age/0.15,0.0,1.0);
        real out=now>r->until?(real)PIN(1.0-(now-r->until)/0.35,0.0,1.0):1.0f;
        amount=in*out;
        if(r->limb>0&&r->limb<count&&r->tip>0&&r->tip<count&&amount>0.0f) {
            real_vector3d from,to,axis;
            vector_from_points3d(&pose[r->limb].position,&pose[r->tip].position,&from);
            vector_from_points3d(&pose[r->limb].position,&r->target,&to);
            if(normalize3d(&from)>0.0001f&&normalize3d(&to)>0.0001f) {
                real angle=acosf(PIN(dot_product3d(&from,&to),-1.0f,1.0f));
                cross_product3d(&from,&to,&axis);
                if(normalize3d(&axis)>0.0001f)
                    turn_subtree(model,count,pose,r->limb,&stock[r->limb].position,&axis,MIN(angle,0.8f)*amount);
            }
        }
        if(r->torso>0&&r->torso<count&&amount>0.0f) {
            real_vector3d toward,axis;
            vector_from_points3d(&pose[r->torso].position,&r->target,&toward);toward.k=0;
            if(normalize3d(&toward)>0.0001f) {
                cross_product3d(global_up3d,&toward,&axis);
                if(normalize3d(&axis)>0.0001f)
                    turn_subtree(model,count,pose,r->torso,&stock[r->torso].position,&axis,0.12f*amount);
            }
        }
        return pose;
    }
    /* a blow: in over 60 ms, then out as a damped swing */
    amount=age<0.06?(real)(age/0.06):(real)(exp(-(age-0.06)/0.16)*cos((age-0.06)*7.0));
    if(now>r->until)amount*=(real)PIN(1.0-(now-r->until)/0.35,0.0,1.0);
    if(r->limb>0&&r->limb<count&&r->tip>0&&r->tip<count) {
        real_vector3d along,axis;
        vector_from_points3d(&pose[r->limb].position,&pose[r->tip].position,&along);
        if(normalize3d(&along)<0.0001f)along=r->push;
        cross_product3d(&along,&r->push,&axis);
        if(normalize3d(&axis)>0.0001f)
            turn_subtree(model,count,pose,r->limb,&stock[r->limb].position,&axis,r->limb_angle*amount);
    }
    if(r->torso>0&&r->torso<count) {
        real_vector3d level=r->push,axis;
        level.k=0;
        if(normalize3d(&level)>0.0001f) {
            cross_product3d(global_up3d,&level,&axis);
            if(normalize3d(&axis)>0.0001f)
                turn_subtree(model,count,pose,r->torso,&stock[r->torso].position,&axis,r->lean*amount);
        }
    }
    return pose;
}
#endif
