#ifndef VR_COMBAT_POSE_H
#define VR_COMBAT_POSE_H

/* Original procedural presentation, composed on the current Halo animation.
 * The caller owns combat timing and excludes NPC/Jolt-owned palettes. This
 * layer never changes animation state, collision, damage or object position.
 * CLUTCH_KNEEL lowers only the drawn pelvis: gameplay openings are separate.
 * Include after real_math.h and models/model_definitions.h. */
#include <math.h>
#include <string.h>
#include "vr_arm_ik_math.h"

/* Gameplay maps the native clip's hit frame here. Attack overlays are neutral
 * at contact, keeping the drawn hand on Halo's actual contact geometry. */
#define VR_COMBAT_POSE_CONTACT_PHASE .65f

enum {
    VR_COMBAT_POSE_SWEEP,
    VR_COMBAT_POSE_OVERHEAD,
    VR_COMBAT_POSE_JAB,
    VR_COMBAT_POSE_CLUTCH_KNEEL,
    VR_COMBAT_POSE_RECOIL,
    VR_COMBAT_POSE_MODE_COUNT,
    VR_COMBAT_POSE_MAX_NODES = 64
};

struct vr_combat_pose_request {
    int mode, side; /* side 0 left, 1 right */
    float weight, phase; /* finite 0..1; native hit at CONTACT_PHASE */
    real_vector3d forward; /* world-space facing, projected onto the floor */
    int has_control_target;
    real_point3d control_target; /* world-space wrist contact; reach is bounded */
};

struct vr_combat_pose_rig {
    int pelvis, spine, upper[2], fore[2], hand[2];
    int thigh[2], calf[2], ankle[2], foot[2];
};

static float vr_combat_pose_dot(float const *a, float const *b)
{
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
}

static void vr_combat_pose_cross(float const *a, float const *b, float *out)
{
    float v[3]={a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};
    memcpy(out,v,sizeof(v));
}

static float vr_combat_pose_distance(real_point3d const *a, real_point3d const *b)
{
    float v[3];int k;
    for(k=0;k<3;k++)v[k]=a->n[k]-b->n[k];
    return sqrtf(vr_combat_pose_dot(v,v));
}

static int vr_combat_pose_unit(float *v)
{
    float length=sqrtf(vr_combat_pose_dot(v,v));int k;
    if(!isfinite(length)||length<1e-6f)return 0;
    for(k=0;k<3;k++)v[k]/=length;
    return 1;
}

static int vr_combat_pose_matrix_valid(real_matrix4x3 const *m)
{
    int i,k;
    if(!isfinite(m->scale)||m->scale<=0||m->scale>100)return 0;
    for(i=0;i<4;i++)for(k=0;k<3;k++)if(!isfinite(m->n[i][k]))return 0;
    for(i=0;i<3;i++){
        float length=vr_combat_pose_dot(m->n[i],m->n[i]);
        if(length<.9f||length>1.1f)return 0;
        for(k=0;k<i;k++)if(fabsf(vr_combat_pose_dot(m->n[i],m->n[k]))>.05f)return 0;
    }
    return 1;
}

static int vr_combat_pose_find(struct model_node const *nodes,int count,char const *name)
{
    int i,found=-1;
    for(i=0;i<count;i++)if(!strcmp(nodes[i].name,name)){
        if(found!=-1)return -1;
        found=i;
    }
    return found;
}

static int vr_combat_pose_under(struct model_node const *nodes,int node,int root)
{
    /* The public entry point validates strict parent-before-child ordering. */
    while(node>=0){if(node==root)return 1;node=nodes[node].parent_node_index;}
    return 0;
}

/* Names and direct parent relationships were checked against stock a50 model
 * tags. Elite/Jackal digitigrade legs insert a horselink before the foot;
 * Grunts have terminal forearms, so they cannot use wrist-controlled IK. */
static int vr_combat_pose_resolve(struct model_node const *nodes,int count,struct vr_combat_pose_rig *rig)
{
    static char const *const names[2][8]={
        {"bip01 l upperarm","bip01 l forearm","bip01 l hand","bip01 l thigh","bip01 l calf","bip01 l horselink","bip01 l foot","bip01 l clavicle"},
        {"bip01 r upperarm","bip01 r forearm","bip01 r hand","bip01 r thigh","bip01 r calf","bip01 r horselink","bip01 r foot","bip01 r clavicle"}
    };
    int side;
    rig->pelvis=vr_combat_pose_find(nodes,count,"bip01 pelvis");
    rig->spine=vr_combat_pose_find(nodes,count,"bip01 spine");
    if(rig->pelvis!=0||rig->spine<0||nodes[rig->spine].parent_node_index!=rig->pelvis)return 0;
    for(side=0;side<2;side++){
        int horse,clavicle;
        rig->upper[side]=vr_combat_pose_find(nodes,count,names[side][0]);
        rig->fore[side]=vr_combat_pose_find(nodes,count,names[side][1]);
        rig->hand[side]=vr_combat_pose_find(nodes,count,names[side][2]);
        rig->thigh[side]=vr_combat_pose_find(nodes,count,names[side][3]);
        rig->calf[side]=vr_combat_pose_find(nodes,count,names[side][4]);
        horse=vr_combat_pose_find(nodes,count,names[side][5]);
        rig->foot[side]=vr_combat_pose_find(nodes,count,names[side][6]);
        clavicle=vr_combat_pose_find(nodes,count,names[side][7]);
        rig->ankle[side]=horse>=0?horse:rig->foot[side];
        if(rig->upper[side]<0||rig->fore[side]<0||clavicle<0||
           nodes[rig->upper[side]].parent_node_index!=clavicle||
           nodes[rig->fore[side]].parent_node_index!=rig->upper[side]||
           !vr_combat_pose_under(nodes,clavicle,rig->spine))return 0;
        if(rig->hand[side]>=0&&nodes[rig->hand[side]].parent_node_index!=rig->fore[side])return 0;
    }
    return 1;
}

static void vr_combat_pose_rotate(float const *axis,float angle,float const *v,float *out)
{
    float cross[3],c=cosf(angle),s=sinf(angle),d=vr_combat_pose_dot(axis,v);int k;
    vr_combat_pose_cross(axis,v,cross);
    for(k=0;k<3;k++)out[k]=v[k]*c+cross[k]*s+axis[k]*d*(1-c);
}

static void vr_combat_pose_subtree(struct model_node const *nodes,int count,
    real_matrix4x3 *pose,int root,float const *axis,float angle)
{
    real_point3d pivot=pose[root].position;int n,k;
    for(n=0;n<count;n++)if(vr_combat_pose_under(nodes,n,root)){
        float relative[3],rotated[3];
        for(k=0;k<3;k++)relative[k]=pose[n].position.n[k]-pivot.n[k];
        vr_combat_pose_rotate(axis,angle,relative,rotated);
        for(k=0;k<3;k++)pose[n].position.n[k]=pivot.n[k]+rotated[k];
        for(k=0;k<3;k++){
            vr_combat_pose_rotate(axis,angle,pose[n].n[k],rotated);
            memcpy(pose[n].n[k],rotated,sizeof(rotated));
        }
    }
}

static int vr_combat_pose_aim(struct model_node const *nodes,int count,
    real_matrix4x3 *pose,int root,int end,real_point3d const *target)
{
    float from[3],to[3],axis[3],s,c;int k;
    for(k=0;k<3;k++){
        from[k]=pose[end].position.n[k]-pose[root].position.n[k];
        to[k]=target->n[k]-pose[root].position.n[k];
    }
    if(!vr_combat_pose_unit(from)||!vr_combat_pose_unit(to))return 0;
    vr_combat_pose_cross(from,to,axis);s=sqrtf(vr_combat_pose_dot(axis,axis));c=vr_combat_pose_dot(from,to);
    if(s<1e-6f){
        float basis[3]={0,0,1};
        if(c>0)return 1;
        if(fabsf(from[2])>.9f){basis[0]=1;basis[2]=0;}
        vr_combat_pose_cross(from,basis,axis);
    }
    if(!vr_combat_pose_unit(axis))return 0;
    vr_combat_pose_subtree(nodes,count,pose,root,axis,atan2f(s,c));
    return 1;
}

/* Two rotations, with the same reach bounds as the player's arm IK. Every
 * child follows its nearest moved bone, preserving fingers/armor/attachments.
 * Legs require an exactly reachable endpoint; arms clamp distant targets. */
static int vr_combat_pose_limb(struct model_node const *nodes,int count,
    real_matrix4x3 *pose,int upper,int fore,int end,real_point3d const *target,
    float const *pole,int exact,float bend_weight)
{
    float upper_length,fore_length,minimum,maximum,distance,reach[3],bend[3],old[3];
    float dot,along,across;real_point3d elbow,wrist;int k;
    upper_length=vr_combat_pose_distance(&pose[upper].position,&pose[fore].position);
    fore_length=vr_combat_pose_distance(&pose[fore].position,&pose[end].position);
    if(upper_length<1e-5f||fore_length<1e-5f||
       !vr_arm_ik_reach_bounds(upper_length,fore_length,0,&minimum,&maximum))return 0;
    for(k=0;k<3;k++){
        reach[k]=target->n[k]-pose[upper].position.n[k];
        old[k]=pose[fore].position.n[k]-pose[upper].position.n[k];
    }
    distance=sqrtf(vr_combat_pose_dot(reach,reach));
    if(!isfinite(distance)||distance<1e-5f||!vr_combat_pose_unit(reach))return 0;
    if(exact&&(distance<minimum||distance>maximum))return 0;
    distance=vr_arm_ik_clamp_distance(distance,minimum,maximum);
    dot=vr_combat_pose_dot(pole,reach);
    for(k=0;k<3;k++)bend[k]=pole[k]-dot*reach[k];
    if(!vr_combat_pose_unit(bend)){
        dot=vr_combat_pose_dot(old,reach);
        for(k=0;k<3;k++)bend[k]=old[k]-dot*reach[k];
        if(!vr_combat_pose_unit(bend)){
            float basis[3]={0,0,1};if(fabsf(reach[2])>.9f){basis[0]=1;basis[2]=0;}
            vr_combat_pose_cross(reach,basis,bend);if(!vr_combat_pose_unit(bend))return 0;
        }
    }else{
        /* At low weights retain the animated elbow/knee swivel. Moving the
         * endpoint by a millimetre must not jump to a different bend plane. */
        dot=vr_combat_pose_dot(old,reach);
        for(k=0;k<3;k++)old[k]-=dot*reach[k];
        if(vr_combat_pose_unit(old)){
            float mixed[3],cross[3],angle;
            vr_combat_pose_cross(old,bend,cross);
            angle=atan2f(vr_combat_pose_dot(cross,reach),vr_combat_pose_dot(old,bend));
            vr_combat_pose_rotate(reach,angle*bend_weight,old,mixed);
            if(vr_combat_pose_unit(mixed))memcpy(bend,mixed,sizeof(mixed));
        }
    }
    along=(upper_length*upper_length+distance*distance-fore_length*fore_length)/(2*distance);
    across=upper_length*upper_length-along*along;
    across=sqrtf(across>0?across:0);
    for(k=0;k<3;k++){
        elbow.n[k]=pose[upper].position.n[k]+reach[k]*along+bend[k]*across;
        wrist.n[k]=pose[upper].position.n[k]+reach[k]*distance;
    }
    return vr_combat_pose_aim(nodes,count,pose,upper,fore,&elbow)&&
           vr_combat_pose_aim(nodes,count,pose,fore,end,&wrist);
}

/* Return 1 only on a complete, finite pose. Return 0 leaves out untouched,
 * including when out aliases native. Unknown topology keeps Halo's pose. */
static int vr_combat_pose_apply(real_matrix4x3 const *native,struct model_node const *nodes,
    int count,struct vr_combat_pose_request const *request,real_matrix4x3 *out)
{
    real_matrix4x3 pose[VR_COMBAT_POSE_MAX_NODES];struct vr_combat_pose_rig rig;
    float forward[3],left[3],up[3]={0,0,1},weight,phase,envelope,sign;int n,k,side;
    if(!native||!nodes||!request||!out||count<1||count>VR_COMBAT_POSE_MAX_NODES||
       request->mode<0||request->mode>=VR_COMBAT_POSE_MODE_COUNT||request->side<0||request->side>1||
       !isfinite(request->weight)||request->weight<=0||request->weight>1||
       !isfinite(request->phase)||request->phase<0||request->phase>1)return 0;
    for(n=0;n<count;n++){
        int parent=nodes[n].parent_node_index;
        if((n==0?parent!=-1:parent<0||parent>=n)||
           !memchr(nodes[n].name,0,sizeof(nodes[n].name))||!vr_combat_pose_matrix_valid(&native[n]))return 0;
    }
    for(k=0;k<3;k++)if(!isfinite(request->forward.n[k])||
       (request->has_control_target&&!isfinite(request->control_target.n[k])))return 0;
    forward[0]=request->forward.i;forward[1]=request->forward.j;forward[2]=0;
    if(!vr_combat_pose_unit(forward)||!vr_combat_pose_resolve(nodes,count,&rig))return 0;
    for(n=0;n<2;n++){
        float length=vr_combat_pose_distance(&native[rig.upper[n]].position,&native[rig.fore[n]].position);
        if(!isfinite(length)||length<1e-5f||length>16)return 0;
        if(rig.hand[n]>=0){
            length=vr_combat_pose_distance(&native[rig.fore[n]].position,&native[rig.hand[n]].position);
            if(!isfinite(length)||length<1e-5f||length>16)return 0;
        }
    }
    vr_combat_pose_cross(up,forward,left);
    weight=request->weight*request->weight*(3-2*request->weight);
    phase=request->phase;side=request->side;sign=side?-1.0f:1.0f;
    envelope=sinf(3.14159265358979323846f*phase);
    if(request->mode<=VR_COMBAT_POSE_JAB&&
       (envelope<1e-6f||fabsf(phase-VR_COMBAT_POSE_CONTACT_PHASE)<1e-6f))return 0;
    memcpy(pose,native,count*sizeof(*pose));
    if(request->mode==VR_COMBAT_POSE_RECOIL){
        vr_combat_pose_subtree(nodes,count,pose,rig.spine,left,-.18f*weight);
        vr_combat_pose_subtree(nodes,count,pose,rig.spine,up,sign*.08f*weight);
    }else if(request->mode==VR_COMBAT_POSE_CLUTCH_KNEEL){
        float leg_length=1000,lower;real_point3d target;
        if(rig.hand[side]<0)return 0;
        for(n=0;n<2;n++){
            float length;
            if(rig.thigh[n]<0||rig.calf[n]<0||rig.ankle[n]<0||rig.foot[n]<0||
               nodes[rig.thigh[n]].parent_node_index!=rig.pelvis||
               nodes[rig.calf[n]].parent_node_index!=rig.thigh[n]||
               nodes[rig.ankle[n]].parent_node_index!=rig.calf[n]||
               (rig.ankle[n]!=rig.foot[n]&&nodes[rig.foot[n]].parent_node_index!=rig.ankle[n]))return 0;
            length=vr_combat_pose_distance(&native[rig.thigh[n]].position,&native[rig.calf[n]].position)+
                   vr_combat_pose_distance(&native[rig.calf[n]].position,&native[rig.ankle[n]].position);
            if(!isfinite(length)||length<1e-4f||length>16)return 0;
            if(length<leg_length)leg_length=length;
        }
        lower=.28f*leg_length*weight;
        for(n=0;n<count;n++)pose[n].position.z-=lower;
        for(n=0;n<2;n++){
            if(!vr_combat_pose_limb(nodes,count,pose,rig.thigh[n],rig.calf[n],rig.ankle[n],
                &native[rig.ankle[n]].position,forward,1,weight))return 0;
            /* Keep each foot's entire authored frame, including toes and the
             * Elite/Jackal's extra hock segment; neither slides nor twists. */
            for(k=0;k<count;k++)if(vr_combat_pose_under(nodes,k,rig.ankle[n]))pose[k]=native[k];
        }
        vr_combat_pose_subtree(nodes,count,pose,rig.spine,left,.16f*weight);
        target=pose[rig.spine].position;
        for(k=0;k<3;k++){
            float goal=request->has_control_target?request->control_target.n[k]:
                target.n[k]+forward[k]*leg_length*.15f-left[k]*sign*leg_length*.08f;
            target.n[k]=pose[rig.hand[side]].position.n[k]+weight*(goal-pose[rig.hand[side]].position.n[k]);
        }
        {
            float pole[3];for(k=0;k<3;k++)pole[k]=left[k]*sign;
            if(!vr_combat_pose_limb(nodes,count,pose,rig.upper[side],rig.fore[side],rig.hand[side],&target,pole,0,weight))return 0;
        }
    }else{
        float amount=weight*envelope;
        float stroke=1-phase/VR_COMBAT_POSE_CONTACT_PHASE;
        if(request->mode==VR_COMBAT_POSE_SWEEP){
            vr_combat_pose_subtree(nodes,count,pose,rig.spine,up,sign*.12f*amount*stroke);
            vr_combat_pose_subtree(nodes,count,pose,rig.upper[side],up,sign*.8f*amount*stroke);
            vr_combat_pose_subtree(nodes,count,pose,rig.upper[side],left,-.18f*amount*stroke);
        }else if(request->mode==VR_COMBAT_POSE_OVERHEAD){
            vr_combat_pose_subtree(nodes,count,pose,rig.upper[side],left,-.9f*amount*stroke);
            vr_combat_pose_subtree(nodes,count,pose,rig.fore[side],left,.35f*amount*stroke);
        }else if(rig.hand[side]>=0){
            real_point3d target=pose[rig.hand[side]].position;float length;
            length=vr_combat_pose_distance(&pose[rig.upper[side]].position,&pose[rig.fore[side]].position)+
                   vr_combat_pose_distance(&pose[rig.fore[side]].position,&pose[rig.hand[side]].position);
            for(k=0;k<3;k++)target.n[k]-=forward[k]*length*.18f*amount*stroke;
            {
                float pole[3];for(k=0;k<3;k++)pole[k]=left[k]*sign;
                if(!vr_combat_pose_limb(nodes,count,pose,rig.upper[side],rig.fore[side],rig.hand[side],&target,pole,0,amount*fabsf(stroke)))return 0;
            }
        }else vr_combat_pose_subtree(nodes,count,pose,rig.upper[side],left,-.28f*amount*stroke);
    }
    for(n=0;n<count;n++){
        int parent=nodes[n].parent_node_index;
        if(!vr_combat_pose_matrix_valid(&pose[n]))return 0;
        if(parent>=0){
            float before=vr_combat_pose_distance(&native[n].position,&native[parent].position);
            float after=vr_combat_pose_distance(&pose[n].position,&pose[parent].position);
            if(!isfinite(before)||!isfinite(after)||fabsf(before-after)>1e-4f*(1+before))return 0;
        }
    }
    memcpy(out,pose,count*sizeof(*out));
    return 1;
}

/* A point on the body as drawn (out of vr_combat_pose_apply) carried to the
 * same place on the native pose, which collision and the NPC rigs use: into
 * the frame of the drawn node nearest the point and out of that node's native
 * frame. Rigid (both frames orthonormal, their scales kept), so the point
 * keeps its place on the bone it is nearest. 0, and out a copy of point, for
 * a malformed input. */
static int vr_combat_pose_map_point(real_matrix4x3 const *drawn,real_matrix4x3 const *native,int count,
    real_point3d const *point,real_point3d *out)
{
    int n,nearest=-1,k;float best=0,local[3],offset[3];
    if(!point||!out)return 0;
    *out=*point;
    if(!drawn||!native||count<1||count>VR_COMBAT_POSE_MAX_NODES)return 0;
    for(k=0;k<3;k++)if(!isfinite(point->n[k]))return 0;
    for(n=0;n<count;n++){
        float distance;
        if(!vr_combat_pose_matrix_valid(&drawn[n])||!vr_combat_pose_matrix_valid(&native[n]))return 0;
        distance=vr_combat_pose_distance(&drawn[n].position,point);
        if(!isfinite(distance))return 0;
        if(nearest<0||distance<best){nearest=n;best=distance;}
    }
    for(k=0;k<3;k++)offset[k]=point->n[k]-drawn[nearest].position.n[k];
    local[0]=vr_combat_pose_dot(offset,drawn[nearest].forward.n)/drawn[nearest].scale;
    local[1]=vr_combat_pose_dot(offset,drawn[nearest].left.n)/drawn[nearest].scale;
    local[2]=vr_combat_pose_dot(offset,drawn[nearest].up.n)/drawn[nearest].scale;
    for(k=0;k<3;k++){
        float value=native[nearest].position.n[k]+native[nearest].scale*
            (native[nearest].forward.n[k]*local[0]+native[nearest].left.n[k]*local[1]+native[nearest].up.n[k]*local[2]);
        if(!isfinite(value)){*out=*point;return 0;}
        out->n[k]=value;
    }
    return 1;
}
#endif
