/* Native graph joint adapter. The NPC transaction owns activation, recovery,
 * authority and checkpoint state; this module handles bounded joint motion. */
#include "cseries.h"
#include "objects/objects.h"
#include "objects/object_definitions.h"
#include "units/units.h"
#include "models/model_animation_definitions.h"
#include "physics/collisions.h"
#include "physics/collision_features.h"
#include "vr_articulated_native.h"
#include "vr_interaction_impact.h"
#include <math.h>
#include <string.h>

/* Exact64-byte tag-node layout used by native biped_limp_noodle.c. */
struct vr_articulated_tag_node {
    char name[32];
    short sibling,child,parent;
    unsigned short pad;
    unsigned long flags;
    real_vector3d base_vector;
    real range;
    long padding;
};
typedef char vr_articulated_tag_node_layout[(sizeof(struct vr_articulated_tag_node)==64)?1:-1];

int vr_articulated_native_capture(long unit_index,struct vr_articulated_native *rig)
{
    struct unit_datum *unit=(struct unit_datum *)object_try_and_get_and_verify_type(unit_index,_object_mask_biped);
    struct animation_graph *graph;
    struct object_definition *definition;
    struct vr_articulated_native result;
    real_matrix4x3 *matrices;
    real radius;
    int n;
    /* (Test55: script-named bodies are captured too; cutscene/custom
     * animations still are not) */
    if(!unit || !rig || unit->unit.player_index!=NONE || unit->object.parent_object_index!=NONE ||
        TEST_FLAG(unit->object.flags,_object_movie_star_bit) || unit_is_playing_custom_animation(unit_index)) return FALSE;
    definition=object_definition_get(unit->definition_index);
    if(definition->object.animation_graph.index==NONE) return FALSE;
    graph=animation_graph_definition_get(definition->object.animation_graph.index);
    if(!graph || graph->nodes.count<=0 || graph->nodes.count>VR_ARTICULATED_NODES ||
        graph->nodes.count>unit->object.node_matrices.size/(long)sizeof(real_matrix4x3)) return FALSE;
    matrices=object_get_node_matrices(unit_index);
    if(!matrices) return FALSE;
    memset(&result,0,sizeof(result));
    result.unit_index=unit_index;result.graph_index=definition->object.animation_graph.index;
    result.body.count=graph->nodes.count;
    result.body.self_collision=1;
    radius=graph->limp_body_node_collision_radius;
    if(!isfinite(radius) || radius<=0 || radius>0.07f) radius=0.03f; /* native default */
    for(n=0;n<result.body.count;++n) {
        struct vr_articulated_tag_node *tag=TAG_BLOCK_GET_ELEMENT(&graph->nodes,n,struct vr_articulated_tag_node);
        struct vr_articulated_node *node=&result.body.nodes[n];
        real_vector3d edge;
        if(!valid_real_matrix4x3(&matrices[n]) || (n && (tag->parent<0 || tag->parent>=n)) ||
            !valid_real_vector3d(&tag->base_vector) || !isfinite(tag->range) || tag->range<0) return FALSE;
        node->parent=n?tag->parent:-1;node->radius=radius;node->inverse_mass=1;
        /* Do not reinterpret native joint axes as parent-bone cone limits.
         * Those semantics differ. Preserve authored metadata for the owning
         * adapter, keep generic solver cone unrestricted in this snapshot. */
        node->max_bend=3.1415926f;
        memcpy(node->position,matrices[n].position.n,sizeof(node->position));
        memcpy(node->previous,node->position,sizeof(node->previous));
        if(n) {vector_from_points3d(&matrices[tag->parent].position,&matrices[n].position,&edge);node->length=magnitude3d(&edge);}
        if(n && node->length<radius*.25f) node->radius=.001f; /* coincident helper joints */
        result.joint_flags[n]=tag->flags;result.joint_axis[n]=tag->base_vector;result.joint_range[n]=tag->range;
        result.captured[n]=matrices[n];
    }
    /* Test54: mass by what each joint carries. The pelvis and spine (with the
     * most joints below them) are heavy, hands and feet light, so a thrown or
     * shot body swings about its torso instead of every joint weighing the
     * same as a fingertip. Pins still override any mass. */
    {
        int below[VR_ARTICULATED_NODES];
        memset(below,0,sizeof(below));
        for(n=result.body.count-1;n>0;--n) below[result.body.nodes[n].parent]+=below[n]+1;
        for(n=0;n<result.body.count;++n) result.body.nodes[n].inverse_mass=1.0f/(1.0f+0.35f*(real)below[n]);
    }
    *rig=result;
    return TRUE;
}
int vr_articulated_native_sweep(void *context,float const old[3],float radius,float next[3])
{
    struct vr_articulated_native *rig=context;
    real_vector3d delta,clipped_velocity;
    real_point3d from,to;
    struct collision_plane planes[4];
    short collisions;
    if(!rig || !old || !next || !isfinite(radius) || radius<=0 || radius>0.07f) return FALSE;
    memcpy(from.n,old,sizeof(from.n));memcpy(to.n,next,sizeof(to.n));
    if(!valid_real_point3d(&from) || !valid_real_point3d(&to)) return FALSE;
    vector_from_points3d(&from,&to,&delta);
    collisions=collision_move_sphere(_collision_test_for_bipeds_dead_flags,&from,&delta,radius,rig->unit_index,
        &to,&clipped_velocity,4,planes);
    if(!valid_real_point3d(&to)) return FALSE;
    /* Test55: a joint resting on the ground (an upward face) slides with
     * friction, about 0.8 g of braking, instead of skating on: bodies used to
     * slide across floors after landing. Fast flight is barely touched (the
     * same fixed braking is a small share of a large step). */
    if(rig->friction && collisions>0 && isfinite(rig->impact_units) && rig->impact_units>0) {
        int floor=FALSE;
        for(int p=0;p<collisions&&p<4;++p) if(planes[p].plane.n.k>.6f) floor=TRUE;
        if(floor) {
            real slide[2]={to.x-from.x,to.y-from.y},length=sqrtf(slide[0]*slide[0]+slide[1]*slide[1]);
            real braking=rig->impact_units*7.8f/(30.0f*30.0f);
            if(isfinite(length) && length>0.0f) {
                real keep=length>braking?(length-braking)/length:0.0f;
                to.x=from.x+slide[0]*keep;to.y=from.y+slide[1]*keep;
            }
        }
    }
    if(collisions>0 && rig->impact_enabled && rig->impact_units>0 && magnitude3d(&delta)>rig->impact_units*(2.f/30.f)) {
        struct collision_result hit;
        /* Only a confirmed native hit can submit damage. Grazing sphere-only
         * contacts without a center ray hit remain physical, not damaging.
         * Test55: a floor counts too, but only for a violent landing (over 6
         * m/s): a hard Spartan throw into the ground hurts; ordinary falls stay
         * with native falling damage. */
        if(collision_test_vector(_collision_test_for_line_of_sight_flags|FLAG(_collision_test_back_facing_surfaces_bit),
                &from,&delta,rig->unit_index,&hit) &&
           (hit.type==_collision_result_structure || hit.type==_collision_result_object) &&
           (hit.plane.n.k<.65f || magnitude3d(&delta)>rig->impact_units*(6.f/30.f)))
            vr_interaction_impact_collision(rig->unit_index,&hit,&delta);
    }
    memcpy(next,to.n,sizeof(to.n));
    return TRUE;
}

/* Native graph joint semantics are taken from biped_limp_noodle, including
 * hinge plane (parent up) and ball/socket base_vector in the grandparent
 * frame. This is an explicit adapter, not a humanoid hardcoded skeleton. */
static int joint_allows(struct vr_articulated_native const *rig,int node,
    real_vector3d const *old_direction,real_vector3d const *direction)
{
    int parent=rig->body.nodes[node].parent;
    int grandparent=parent>=0?rig->body.nodes[parent].parent:-1;
    real_matrix4x3 inverse;
    real_vector3d axis,local_axis,parent_axis;
    real cosine,angle;
    if(parent<=0 || grandparent<0) return TRUE;
    cosine=PIN(dot_product3d(old_direction,direction),-1.0f,1.0f);
    if(cosine>0.999999f) return TRUE;
    if(TEST_FLAG(rig->joint_flags[parent],2)) return FALSE;
    cross_product3d(old_direction,direction,&axis);
    if(normalize3d(&axis)<0.00001f) return FALSE;
    angle=acosf(cosine);
    if(angle>0.7853982f) return FALSE; /* native orientation per-step limit */
    if(TEST_FLAG(rig->joint_flags[parent],1)) return TRUE; /* projected below */
    matrix4x3_inverse(&rig->captured[parent],&inverse);
    matrix4x3_transform_vector(&inverse,&axis,&local_axis);
    parent_axis=rig->captured[parent].forward;
    matrix4x3_inverse(&rig->captured[grandparent],&inverse);
    matrix4x3_transform_vector(&inverse,&parent_axis,&parent_axis);
    rotate_vector_about_axis(&parent_axis,&local_axis,sinf(angle),cosine);
    return acosf(PIN(dot_product3d(&rig->joint_axis[parent],&parent_axis),-1.0f,1.0f))<=rig->joint_range[parent];
}
int vr_articulated_native_step(struct vr_articulated_native *rig,float dt,float gravity,
    struct vr_articulated_pin const *pins,int pin_count)
{
    struct vr_articulated_native work;
    int n,k;
    if(!rig) return FALSE;
    work=*rig;
    work.friction=TRUE;
    if(!vr_articulated_step(&work.body,dt,gravity,pins,pin_count,vr_articulated_native_sweep,&work)) return FALSE;
    work.friction=FALSE;
    for(n=0;n<work.body.count;++n) {
        int parent=work.body.nodes[n].parent;
        real_vector3d old_direction,direction,axis;
        real cosine,angle,length=work.body.nodes[n].length;
        real_point3d desired;
        if(parent<0) continue;
        vector_from_points3d(&rig->captured[parent].position,&rig->captured[n].position,&old_direction);
        for(k=0;k<3;++k) direction.n[k]=work.body.nodes[n].position[k]-work.body.nodes[parent].position[k];
        if(normalize3d(&old_direction)<0.00001f || normalize3d(&direction)<0.00001f) continue;
        if(TEST_FLAG(work.joint_flags[parent],1)) {
            real projection=dot_product3d(&direction,&work.captured[parent].up);
            for(k=0;k<3;++k) direction.n[k]-=projection*work.captured[parent].up.n[k];
            if(normalize3d(&direction)<0.00001f) direction=old_direction;
        }
        if(!joint_allows(&work,n,&old_direction,&direction)) {
            /* Seek the largest valid fraction of requested joint motion. */
            real lower=0,upper=1;
            real_vector3d candidate=old_direction;
            for(k=0;k<8;++k) {
                real fraction=(lower+upper)*0.5f;
                real_vector3d test;
                vectors_interpolate(&old_direction,&direction,fraction,&test);
                if(normalize3d(&test)>0.00001f && joint_allows(&work,n,&old_direction,&test)) {candidate=test;lower=fraction;}
                else upper=fraction;
            }
            direction=candidate;
        }
        for(k=0;k<3;++k) desired.n[k]=work.body.nodes[parent].position[k]+direction.n[k]*length;
        if(!vr_articulated_native_sweep(&work,work.body.nodes[n].position,work.body.nodes[n].radius,desired.n)) return FALSE;
        memcpy(work.body.nodes[n].position,desired.n,sizeof(desired.n));
        cross_product3d(&old_direction,&direction,&axis);
        cosine=PIN(dot_product3d(&old_direction,&direction),-1.0f,1.0f);
        if(cosine<0.999999f && normalize3d(&axis)>0.00001f) {
            angle=acosf(cosine);
            rotate_vector_about_axis(&work.captured[parent].forward,&axis,sinf(angle),cosine);
            rotate_vector_about_axis(&work.captured[parent].up,&axis,sinf(angle),cosine);
            cross_product3d(&work.captured[parent].up,&work.captured[parent].forward,&work.captured[parent].left);
            if(!valid_real_vector3d_axes3(&work.captured[parent].forward,&work.captured[parent].left,&work.captured[parent].up)) return FALSE;
        }
    }
    /* Test55: a joint with no child (the head, hands, feet) has no bone of
     * its own to turn it, so it kept its captured orientation while its limb
     * swung: heads stayed upright on falling bodies (the puppet look). It now
     * turns with its parent, keeping its pose relative to it. */
    {
        int has_child[VR_ARTICULATED_NODES];
        memset(has_child,0,sizeof(has_child));
        for(n=1;n<work.body.count;++n) if(work.body.nodes[n].parent>=0) has_child[work.body.nodes[n].parent]=TRUE;
        for(n=1;n<work.body.count;++n) {
            int parent=work.body.nodes[n].parent;
            real_matrix4x3 const *before=&rig->captured[parent],*after=&work.captured[parent];
            real_vector3d forward,up;
            if(parent<0 || has_child[n]) continue;
            for(k=0;k<3;++k) {
                real f_forward=dot_product3d(&rig->captured[n].forward,&before->forward);
                real f_left=dot_product3d(&rig->captured[n].forward,&before->left);
                real f_up=dot_product3d(&rig->captured[n].forward,&before->up);
                real u_forward=dot_product3d(&rig->captured[n].up,&before->forward);
                real u_left=dot_product3d(&rig->captured[n].up,&before->left);
                real u_up=dot_product3d(&rig->captured[n].up,&before->up);
                forward.n[k]=after->forward.n[k]*f_forward+after->left.n[k]*f_left+after->up.n[k]*f_up;
                up.n[k]=after->forward.n[k]*u_forward+after->left.n[k]*u_left+after->up.n[k]*u_up;
            }
            if(normalize3d(&forward)<0.00001f || normalize3d(&up)<0.00001f) continue;
            {
                real dot=dot_product3d(&forward,&up);
                for(k=0;k<3;++k) up.n[k]-=forward.n[k]*dot;
                if(normalize3d(&up)<0.00001f) continue;
            }
            work.captured[n].forward=forward;work.captured[n].up=up;
            cross_product3d(&up,&forward,&work.captured[n].left);
            if(!valid_real_vector3d_axes3(&work.captured[n].forward,&work.captured[n].left,&work.captured[n].up)) {
                work.captured[n]=rig->captured[n];
            }
        }
    }
    for(n=0;n<work.body.count;++n) {
        memcpy(work.captured[n].position.n,work.body.nodes[n].position,sizeof(work.body.nodes[n].position));
        if(!valid_real_matrix4x3(&work.captured[n])) return FALSE;
    }
    *rig=work;
    return TRUE;
}
