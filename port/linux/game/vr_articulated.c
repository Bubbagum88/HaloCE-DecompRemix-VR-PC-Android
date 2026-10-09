#include "vr_articulated.h"
#include <math.h>
#include <string.h>

static int finite3(float const p[3]) { return isfinite(p[0]) && isfinite(p[1]) && isfinite(p[2]); }
static float length3(float const p[3]) { return sqrtf(p[0]*p[0]+p[1]*p[1]+p[2]*p[2]); }
static int valid_body(struct vr_articulated_body const *b)
{
    int n;
    if (!b || b->count<1 || b->count>VR_ARTICULATED_NODES || b->self_collision<0 || b->self_collision>1) return 0;
    for (n=0;n<b->count;++n) {
        struct vr_articulated_node const *p=&b->nodes[n];
        if (p->parent>=n || p->parent < -1 || !finite3(p->position) || !finite3(p->previous) ||
            !isfinite(p->inverse_mass) || p->inverse_mass<0 || p->inverse_mass>100 ||
            !isfinite(p->radius) || p->radius<0 || p->radius>10 ||
            !isfinite(p->length) || p->length<0 || p->length>10 ||
            !isfinite(p->max_bend) || p->max_bend<0 || p->max_bend>3.141593f) return 0;
    }
    return 1;
}
int vr_articulated_step(struct vr_articulated_body *body, float dt, float gravity,
    struct vr_articulated_pin const *pins, int pin_count, vr_articulated_sweep sweep, void *context)
{
    struct vr_articulated_body work;
    float weight[VR_ARTICULATED_NODES];
    float old[VR_ARTICULATED_NODES][3];
    int n,k,iteration;
    if (!valid_body(body) || !isfinite(dt) || dt<0.001f || dt>0.05f || !isfinite(gravity) ||
        fabsf(gravity)>100 || pin_count<0 || pin_count>2 || (pin_count && !pins) || !sweep) return 0;
    work=*body;
    for (n=0;n<work.count;++n) {
        struct vr_articulated_node *p=&work.nodes[n];
        float velocity[3],speed;
        weight[n]=p->inverse_mass;
        memcpy(old[n],p->position,sizeof(old[n]));
        if (!weight[n]) continue;
        for(k=0;k<3;++k) velocity[k]=(p->position[k]-p->previous[k])*0.985f;
        speed=length3(velocity);
        if (speed>dt*12) for(k=0;k<3;++k) velocity[k]*=dt*12/speed;
        memcpy(p->previous,p->position,sizeof(p->previous));
        for(k=0;k<3;++k) p->position[k]+=velocity[k];
        p->position[2]-=gravity*dt*dt;
    }
    for(n=0;n<pin_count;++n) {
        float distance[3];
        int node=pins[n].node;
        if(node<0 || node>=work.count || !finite3(pins[n].position) || (n && node==pins[0].node)) return 0;
        for(k=0;k<3;++k) distance[k]=pins[n].position[k]-old[node][k];
        if(length3(distance)>0.5f) return 0; /* tracking teleport: reject transaction */
        weight[node]=0;
        memcpy(work.nodes[node].position,pins[n].position,sizeof(pins[n].position));
        memcpy(work.nodes[node].previous,pins[n].position,sizeof(pins[n].position));
    }
    for(iteration=0;iteration<8;++iteration) {
        for(n=0;n<work.count;++n) {
            struct vr_articulated_node *a=&work.nodes[n], *b;
            float delta[3],length,total,correction;
            if(a->parent<0) continue;
            b=&work.nodes[a->parent]; total=weight[n]+weight[a->parent];
            for(k=0;k<3;++k) delta[k]=a->position[k]-b->position[k];
            length=length3(delta);
            if(total<=0 || length<0.000001f) continue;
            correction=(length-a->length)/(length*total);
            for(k=0;k<3;++k) {
                a->position[k]-=delta[k]*correction*weight[n];
                b->position[k]+=delta[k]*correction*weight[a->parent];
            }
            /* Cone about the parent's bone direction, avoiding unlimited
             * folding. Adapter supplies anatomical max_bend, not a guessed
             * global human angle for every Halo species. */
            if(b->parent>=0 && weight[n]>0 && a->max_bend<3.14159f) {
                float axis[3],dir[3],side[3],al,dl,dot,sl,limit=cosf(a->max_bend);
                for(k=0;k<3;++k) {
                    axis[k]=b->position[k]-work.nodes[b->parent].position[k];
                    dir[k]=a->position[k]-b->position[k];
                }
                al=length3(axis); dl=length3(dir);
                if(al<0.000001f || dl<0.000001f) continue;
                dot=0;
                for(k=0;k<3;++k) {axis[k]/=al;dir[k]/=dl;dot+=axis[k]*dir[k];}
                if(dot<limit) {
                    for(k=0;k<3;++k) side[k]=dir[k]-dot*axis[k];
                    sl=length3(side);
                    if(sl<0.000001f) {
                        side[0]=-axis[1];side[1]=axis[0];side[2]=0;
                        sl=length3(side);
                        if(sl<0.000001f) {side[0]=1;side[1]=0;side[2]=0;sl=1;}
                    }
                    for(k=0;k<3;++k) a->position[k]=b->position[k]+a->length*(axis[k]*limit+side[k]/sl*sinf(a->max_bend));
                }
            }
        }
        if(work.self_collision) for(n=0;n<work.count;++n) for(int other=n+1;other<work.count;++other) {
            struct vr_articulated_node *a=&work.nodes[n],*b=&work.nodes[other];
            float delta[3],distance,penetration,correction,minimum=a->radius+b->radius,total=weight[n]+weight[other];
            /* Neighbouring joint spheres deliberately overlap at bends.
             * Their own limb-length constraints, not self-collision, own that. */
            if(a->parent==other || b->parent==n ||
               (a->parent>=0&&work.nodes[a->parent].parent==other) ||
               (b->parent>=0&&work.nodes[b->parent].parent==n) || total<=0) continue;
            for(k=0;k<3;++k) delta[k]=b->position[k]-a->position[k];
            distance=length3(delta);
            if(distance>=minimum) continue;
            penetration=minimum-distance;
            if(distance<.000001f) {delta[0]=1;delta[1]=delta[2]=0;distance=1;}
            correction=penetration/(distance*total);
            for(k=0;k<3;++k) {a->position[k]-=delta[k]*correction*weight[n];b->position[k]+=delta[k]*correction*weight[other];}
        }
        /* Solve constraints in memory, then sweep each node's complete old
         * to proposed displacement once. Never tunnel by testing only an end
         * point. Bounded to one broadphase query per free node, not eight. */
        if(iteration==7) for(n=0;n<work.count;++n) if(weight[n]>0) {
            struct vr_articulated_node *p=&work.nodes[n];
            if(!sweep(context,old[n],p->radius,p->position) || !finite3(p->position)) return 0;
        }
    }
    if(!valid_body(&work)) return 0;
    *body=work;
    return 1;
}
int vr_articulated_recovery(struct vr_articulated_body *body, float const target[][3],
    float amount, vr_articulated_sweep sweep, void *context)
{
    struct vr_articulated_body work;
    int n,k;
    if(!valid_body(body) || !target || !sweep || !isfinite(amount) || amount<0 || amount>1) return 0;
    work=*body;
    for(n=0;n<work.count;++n) {
        if(!finite3(target[n])) return 0;
        for(k=0;k<3;++k) work.nodes[n].position[k]+=amount*(target[n][k]-work.nodes[n].position[k]);
        if(!sweep(context,body->nodes[n].position,work.nodes[n].radius,work.nodes[n].position) || !finite3(work.nodes[n].position)) return 0;
        memcpy(work.nodes[n].previous,work.nodes[n].position,sizeof(work.nodes[n].previous));
    }
    *body=work;
    return 1;
}
