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
    /* Test56: the parent-relative solver's rest data from this pose */
    if(!vr_articulated_native_prepare(&result)) return FALSE;
    *rig=result;
    return TRUE;
}
/* Test60: what a moving joint's impact is tested against: the line of sight's
 * surfaces (structure, scenery, machines, vehicles) and bodies, back faces
 * too; and, for the body-to-body test, bodies and vehicles alone */
#define VR_IMPACT_TEST_FLAGS (_collision_test_for_line_of_sight_flags|FLAG(_collision_test_back_facing_surfaces_bit)| \
    FLAG(_collision_test_objects_bipeds_bit))
#define VR_IMPACT_BODY_TEST_FLAGS (FLAG(_collision_test_front_facing_surfaces_bit)|FLAG(_collision_test_objects_bit)| \
    FLAG(_collision_test_objects_bipeds_bit)|FLAG(_collision_test_objects_vehicles_bit))
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
    if(rig->impact_enabled && rig->impact_units>0 && magnitude3d(&delta)>rig->impact_units*(2.f/30.f)) {
        struct collision_result hit;
        int found=FALSE;
        if(collisions>0) {
            /* Only a confirmed native hit can submit damage. Test55: a floor
             * counts too, but only for a violent landing (over 6 m/s): a hard
             * Spartan throw into the ground hurts; ordinary falls stay with
             * native falling damage (the damage itself is by the speed into
             * the surface, vr_interaction_impact_scale). Test60: a joint whose
             * sphere met a surface its centre's path missed (a body slammed
             * flat onto the floor, glancing off a wall: the Test59 log had no
             * impact at all) is probed straight into the face it met. */
            found=collision_test_vector(VR_IMPACT_TEST_FLAGS,&from,&delta,rig->unit_index,&hit);
            if(!found) {
                int p,best=0;
                real_vector3d into;
                real depth;
                for(p=1;p<collisions&&p<4;++p)
                    if(dot_product3d(&planes[p].plane.n,&delta)<dot_product3d(&planes[best].plane.n,&delta)) best=p;
                depth=radius*1.5f+MAX(-dot_product3d(&planes[best].plane.n,&delta),0.0f);
                scale_vector3d(&planes[best].plane.n,-depth,&into);
                if(valid_real_vector3d(&into))
                    found=collision_test_vector(VR_IMPACT_TEST_FLAGS,&from,&into,rig->unit_index,&hit);
            }
            if(found && !((hit.type==_collision_result_structure || hit.type==_collision_result_object) &&
               (hit.plane.n.k<.65f || magnitude3d(&delta)>rig->impact_units*(6.f/30.f))))
                found=FALSE;
        }
        if(!found) {
            /* Test60: another body (an ally or an enemy) or a vehicle in the
             * way. The ragdoll's own sweep passes through living bodies (the
             * engine's dead-body collision), so a thrown or slammed body never
             * struck one: a fast joint now meets it, stops at it and hurts it.
             * Not a player (the hands holding it). */
            real_vector3d reach=delta;
            real length=magnitude3d(&delta);
            struct unit_datum *struck;
            if(length>0.000001f) scale_vector3d(&reach,(length+radius)/length,&reach);
            if(collision_test_vector(VR_IMPACT_BODY_TEST_FLAGS,&from,&reach,rig->unit_index,&hit) &&
               hit.type==_collision_result_object && hit.object_index!=NONE && hit.object_index!=rig->unit_index &&
               (!(struck=(struct unit_datum *)object_try_and_get_and_verify_type(hit.object_index,_object_mask_unit)) ||
                struck->unit.player_index==NONE)) {
                real stop=MAX(hit.t*magnitude3d(&reach)-radius,0.0f);
                real_vector3d moved;
                found=TRUE;
                vector_from_points3d(&from,&to,&moved);
                if(length>0.000001f && stop<dot_product3d(&moved,&delta)/length)
                    for(int axis=0;axis<3;++axis) to.n[axis]=from.n[axis]+delta.n[axis]*stop/length;
            }
        }
        if(found) vr_interaction_impact_collision(rig->unit_index,&hit,&delta);
    }
    memcpy(next,to.n,sizeof(to.n));
    return TRUE;
}

/* ---------- Test56: the parent-relative joint solver

The authored joint metadata (the limp-noodle tag: flags, base vector, range)
belongs to each joint J and describes J's own frame relative to its parent G:
bit 0x4 no movement (J is one rigid piece with G), 0x2 a hinge about G's up
axis, 0x1 a ball joint whose forward axis (J's bone, toward its child) stays
within `range` of `base_vector` (J's rest forward in G's frame). The Test54/55
pass compared world-space bone directions against those limits, so a joint
under a rigid one (an Elite's spine1 and neck) could never turn at all while
the rest of the body fell: the constraints fought every tick and bodies
jittered and never settled.

Each tick, after a damped Verlet move under gravity (and any hand pins), a few
passes of:
1. bone lengths, mass-weighted;
2. each rigid piece (a joint and the rigid joints under it) shape-matched,
   mass-weighted, to its rest shape, keeping its centre of mass and momentum;
3. every frame fitted from the joint positions around it: a joint with one
   bone below it follows that bone exactly (a leaf the bone above it), its
   rest pose relative to its parent deciding only the twist; the root and
   joints with several bones below are fitted to them all (iterative rotation
   extraction, warm-started from the last tick);
4. each ball or hinge joint held in its authored cone or arc relative to its
   parent's frame (hinges also no further than straight: the
   anti-hyperextension bound; a hinge's angle is followed from its last one,
   so it never flips across its forbidden arc) by turning that joint's whole
   subtree about it;
5. on the last pass, limbs kept out of the body (self contact).
Then every joint is swept once against the world (with ground friction), two
more passes put back together whatever the ground stopped, and anything those
moved is swept again. Nothing depends on a humanoid layout: Hunters, Flood
forms and custom graphs use their own authored flags.
tools/test_test56_ragdoll.py drops every stock character five ways: all come
to rest (most in 1-2 s, all inside the NPC code's 5 s hand-back); Test55's
solver left most of them moving 1-15 cm a tick until then. Where the ground
holds a limb a joint can stay up to ~25 degrees past its limit, and a Jackal's
flaps up to ~7 cm off. */
enum { VRJ_EXTRACT_ITERATIONS=6 };
static inline void vrj_to_local(real_matrix4x3 const *m,real_vector3d const *v,real_vector3d *out)
{
    real_vector3d t;
    t.i=dot_product3d(v,&m->forward);t.j=dot_product3d(v,&m->left);t.k=dot_product3d(v,&m->up);
    *out=t;
}
static inline void vrj_to_world(real_matrix4x3 const *m,real_vector3d const *v,real_vector3d *out)
{
    real_vector3d t;
    int k;
    for(k=0;k<3;++k) t.n[k]=m->forward.n[k]*v->i+m->left.n[k]*v->j+m->up.n[k]*v->k;
    *out=t;
}
static inline int vrj_orthonormalize(real_matrix4x3 *m)
{
    real dot;
    int k;
    if(normalize3d(&m->forward)<0.000001f) return FALSE;
    dot=dot_product3d(&m->up,&m->forward);
    for(k=0;k<3;++k) m->up.n[k]-=m->forward.n[k]*dot;
    if(normalize3d(&m->up)<0.000001f) return FALSE;
    cross_product3d(&m->up,&m->forward,&m->left);
    return TRUE;
}
static inline void vrj_rotate_frame(real_matrix4x3 *m,real_vector3d const *axis,real angle)
{
    real s=sinf(angle),c=cosf(angle);
    rotate_vector_about_axis(&m->forward,axis,s,c);
    rotate_vector_about_axis(&m->left,axis,s,c);
    rotate_vector_about_axis(&m->up,axis,s,c);
}
/* Muller et al. 2016: the rotation nearest the covariance A (its columns,
 * one per local axis), from a warm start. */
static inline int vrj_extract(real_matrix4x3 *m,real_vector3d const covariance[3])
{
    int iteration,k;
    for(iteration=0;iteration<VRJ_EXTRACT_ITERATIONS;++iteration) {
        real_vector3d omega={{0,0,0}},cross;
        real denominator=0,angle;
        real_vector3d const *column[3];
        column[0]=&m->forward;column[1]=&m->left;column[2]=&m->up;
        for(k=0;k<3;++k) {
            cross_product3d(column[k],&covariance[k],&cross);
            omega.i+=cross.i;omega.j+=cross.j;omega.k+=cross.k;
            denominator+=dot_product3d(column[k],&covariance[k]);
        }
        denominator=fabsf(denominator)+1e-12f;
        omega.i/=denominator;omega.j/=denominator;omega.k/=denominator;
        angle=magnitude3d(&omega);
        if(!isfinite(angle)) return FALSE;
        if(angle<1e-6f) break;
        omega.i/=angle;omega.j/=angle;omega.k/=angle;
        vrj_rotate_frame(m,&omega,MIN(angle,1.0f));
    }
    return vrj_orthonormalize(m);
}
static inline void vrj_accumulate(real_vector3d covariance[3],real weight,real_vector3d const *world,real_vector3d const *rest)
{
    int k;
    for(k=0;k<3;++k) {
        covariance[k].i+=weight*world->i*rest->n[k];
        covariance[k].j+=weight*world->j*rest->n[k];
        covariance[k].k+=weight*world->k*rest->n[k];
    }
}
static inline real vrj_wrap(real angle)
{
    if(!isfinite(angle)) return 0;
    if(angle>3.14159265f || angle< -3.14159265f) angle-=6.2831853f*floorf((angle+3.14159265f)/6.2831853f);
    return angle;
}
/* the joint's forward in its parent's frame: hinge bend (about the parent's
 * up, from its forward toward its left) and ball deviation from rest */
static inline real vrj_hinge_angle(real_vector3d const *local)
{
    return atan2f(local->j,local->i);
}
int vr_articulated_native_prepare(struct vr_articulated_native *rig)
{
    int n;
    real const degree=0.017453293f;
    if(!rig || rig->body.count<1 || rig->body.count>VR_ARTICULATED_NODES) return FALSE;
    /* one root, and every parent before its children (the solver's passes
     * and the bone walks below rely on it) */
    for(n=0;n<rig->body.count;++n)
        if(n?(rig->body.nodes[n].parent<0 || rig->body.nodes[n].parent>=n):rig->body.nodes[n].parent!=-1) return FALSE;
    for(n=0;n<rig->body.count;++n) {
        real_matrix4x3 frame=rig->captured[n];
        if(!vrj_orthonormalize(&frame) || !valid_real_point3d(&frame.position)) return FALSE;
        rig->captured[n].forward=frame.forward;rig->captured[n].left=frame.left;rig->captured[n].up=frame.up;
    }
    for(n=0;n<rig->body.count;++n) {
        int parent=rig->body.nodes[n].parent;
        unsigned long flags=rig->joint_flags[n];
        real_vector3d base=rig->joint_axis[n];
        if(parent<0) rig->joint_kind[n]=VR_JOINT_FREE;
        else if(flags&4) rig->joint_kind[n]=VR_JOINT_RIGID;
        else if((flags&2) && fabsf(base.k)<0.3f) rig->joint_kind[n]=VR_JOINT_HINGE;
        else if(flags&3) rig->joint_kind[n]=VR_JOINT_BALL;
        else rig->joint_kind[n]=VR_JOINT_FREE;
        rig->group[n]=rig->joint_kind[n]==VR_JOINT_RIGID?rig->group[parent]:n;
    }
    for(n=0;n<rig->body.count;++n) {
        int parent=rig->body.nodes[n].parent,root=rig->group[n];
        real_matrix4x3 const *own=&rig->captured[n];
        real_vector3d offset;
        memset(&rig->rest_parent[n],0,sizeof(rig->rest_parent[n]));
        memset(&rig->rest_in_parent[n],0,sizeof(rig->rest_in_parent[n]));
        memset(&rig->rest_group[n],0,sizeof(rig->rest_group[n]));
        rig->relative[n][0].i=1;rig->relative[n][0].j=0;rig->relative[n][0].k=0;
        rig->relative[n][1].i=0;rig->relative[n][1].j=1;rig->relative[n][1].k=0;
        rig->relative[n][2].i=0;rig->relative[n][2].j=0;rig->relative[n][2].k=1;
        if(parent>=0) {
            vector_from_points3d(&own->position,&rig->captured[parent].position,&offset);
            vrj_to_local(own,&offset,&rig->rest_parent[n]);
            vector_from_points3d(&rig->captured[parent].position,&own->position,&offset);
            vrj_to_local(&rig->captured[parent],&offset,&rig->rest_in_parent[n]);
        }
        {
            /* a piece member: its axes and place in the piece root's frame; a
             * piece root (or a single joint): its axes in the parent's frame
             * and its place in the parent's piece root's frame */
            int frame_of=root!=n?root:parent;
            int place_of=root!=n?root:(parent>=0?rig->group[parent]:-1);
            if(frame_of>=0) {
                vrj_to_local(&rig->captured[frame_of],&own->forward,&rig->relative[n][0]);
                vrj_to_local(&rig->captured[frame_of],&own->left,&rig->relative[n][1]);
                vrj_to_local(&rig->captured[frame_of],&own->up,&rig->relative[n][2]);
            }
            if(place_of>=0) {
                vector_from_points3d(&rig->captured[place_of].position,&own->position,&offset);
                vrj_to_local(&rig->captured[place_of],&offset,&rig->rest_group[n]);
            }
        }
        rig->joint_low[n]=0;rig->joint_high[n]=0;rig->joint_bend[n]=0;
        if(rig->joint_kind[n]==VR_JOINT_HINGE || rig->joint_kind[n]==VR_JOINT_BALL) {
            real_vector3d base=rig->joint_axis[n],now;
            real range=rig->joint_range[n];
            if(normalize3d(&base)<0.0001f) {rig->joint_kind[n]=VR_JOINT_FREE;continue;}
            rig->joint_axis[n]=base;
            vrj_to_local(&rig->captured[parent],&own->forward,&now);
            if(!isfinite(range) || range<0) range=0;
            if(rig->joint_kind[n]==VR_JOINT_HINGE) {
                real centre=vrj_hinge_angle(&base),angle=vrj_hinge_angle(&now);
                real low=centre-range,high=centre+range;
                /* anti-hyperextension: a knee or elbow bends one way only,
                 * from nearly straight (10 degrees past) to 165 degrees */
                if(centre< -5*degree) {low=MAX(low,-165*degree);high=MIN(high,10*degree);}
                else if(centre>5*degree) {low=MAX(low,-10*degree);high=MIN(high,165*degree);}
                /* the captured pose is always allowed (no snap at the start) */
                angle=centre+vrj_wrap(angle-centre);
                if(angle<low) low=angle-2*degree;
                if(angle>high) high=angle+2*degree;
                rig->joint_low[n]=low;rig->joint_high[n]=high;rig->joint_bend[n]=angle;
            } else {
                real deviation=acosf(PIN(dot_product3d(&base,&now),-1.0f,1.0f));
                rig->joint_high[n]=MAX(range,deviation+2*degree);
            }
        }
    }
    /* self contact: joints at least four bones apart, not in one rigid piece,
     * and not coincident helper joints */
    {
        int depth[VR_ARTICULATED_NODES],other;
        for(n=0;n<rig->body.count;++n) {
            int parent=rig->body.nodes[n].parent;
            depth[n]=parent>=0?depth[parent]+1:0;
            rig->self_mask[n]=0;
        }
        for(n=0;n<rig->body.count;++n) for(other=n+1;other<rig->body.count;++other) {
            int a=n,b=other,hops=0;
            if(rig->group[n]==rig->group[other] || rig->body.nodes[n].radius<0.002f ||
               rig->body.nodes[other].radius<0.002f) continue;
            while(a!=b && a>=0 && b>=0) {
                if(depth[a]>=depth[b]) a=rig->body.nodes[a].parent; else b=rig->body.nodes[b].parent;
                ++hops;
            }
            if(a>=0 && b>=0 && hops>=4) rig->self_mask[n]|=1ull<<other;
        }
    }
    rig->prepared=TRUE;
    return TRUE;
}
/* solver passes per tick, after the sweep, and the pull of each frame toward
 * its rest pose relative to its parent (host simulator, all stock skeletons) */
enum { VRJ_ITERATIONS=6, VRJ_POST_ITERATIONS=2 };
#define VRJ_TWIST 1.0f
/* a rigid piece's root fitted to its points (root, members, the joints hung
 * from them), mass-weighted; the points then put back on the rigid shape.
 * Momentum is kept: the centre of mass does not move. */
static int vrj_piece(struct vr_articulated_native *rig,int root,int const pinned[])
{
    real_vector3d covariance[3];
    real_point3d centre={{0,0,0}},rest_centre={{0,0,0}};
    real total=0;
    int point,pass,k,count=rig->body.count;
    for(pass=0;pass<2;++pass) {
        if(pass) {
            memset(covariance,0,sizeof(covariance));
            for(k=0;k<3;++k) {centre.n[k]/=total;rest_centre.n[k]/=total;}
        }
        for(point=root;point<count;++point) {
            int parent=rig->body.nodes[point].parent;
            real weight;
            real_vector3d rest,world;
            if(!(rig->group[point]==root || (parent>=0 && rig->group[parent]==root && rig->group[point]==point))) continue;
            rest=point==root?(real_vector3d){{0,0,0}}:rig->rest_group[point];
            weight=rig->body.nodes[point].inverse_mass>0?1.0f/rig->body.nodes[point].inverse_mass:1.0f;
            if(pinned[point]) weight*=1000.0f;
            if(!pass) {
                for(k=0;k<3;++k) {centre.n[k]+=weight*rig->body.nodes[point].position[k];rest_centre.n[k]+=weight*rest.n[k];}
                total+=weight;
            } else {
                for(k=0;k<3;++k) {world.n[k]=rig->body.nodes[point].position[k]-centre.n[k];rest.n[k]-=rest_centre.n[k];}
                vrj_accumulate(covariance,weight,&world,&rest);
            }
        }
        if(!(total>0)) return FALSE;
    }
    if(!vrj_extract(&rig->captured[root],covariance)) return FALSE;
    for(point=root;point<count;++point) {
        int parent=rig->body.nodes[point].parent;
        real_vector3d rest,world;
        if(!(rig->group[point]==root || (parent>=0 && rig->group[parent]==root && rig->group[point]==point)) || pinned[point]) continue;
        rest=point==root?(real_vector3d){{0,0,0}}:rig->rest_group[point];
        for(k=0;k<3;++k) rest.n[k]-=rest_centre.n[k];
        vrj_to_world(&rig->captured[root],&rest,&world);
        for(k=0;k<3;++k) rig->body.nodes[point].position[k]=centre.n[k]+world.n[k];
    }
    return TRUE;
}
/* a joint's frame from its rest pose relative to its parent, swung by the
 * smallest turn that puts one of its bones (rest: in the joint's own frame)
 * where that bone is now: the bone is followed exactly, and the rest pose only
 * decides the twist about it */
static int vrj_swing(struct vr_articulated_native *rig,int n,real_vector3d const *rest,real_vector3d const *now)
{
    real_matrix4x3 *frame=&rig->captured[n];
    real_vector3d from,to,axis;
    real sine,cosine,along;
    int parent=rig->body.nodes[n].parent,k;
    vrj_to_world(&rig->captured[parent],&rig->relative[n][0],&frame->forward);
    vrj_to_world(&rig->captured[parent],&rig->relative[n][1],&frame->left);
    vrj_to_world(&rig->captured[parent],&rig->relative[n][2],&frame->up);
    if(!vrj_orthonormalize(frame)) return FALSE;
    vrj_to_world(frame,rest,&from);
    to=*now;
    if(normalize3d(&from)<0.000001f || normalize3d(&to)<0.000001f) return TRUE;
    cross_product3d(&from,&to,&axis);
    sine=normalize3d(&axis);cosine=dot_product3d(&from,&to);
    if(sine<0.000001f) {
        if(cosine>0) return TRUE;
        /* turned right round: about any axis across the bone */
        axis=fabsf(dot_product3d(&from,&frame->up))<0.9f?frame->up:frame->left;
        along=dot_product3d(&axis,&from);
        for(k=0;k<3;++k) axis.n[k]-=from.n[k]*along;
        if(normalize3d(&axis)<0.000001f) return TRUE;
        sine=0;cosine=-1;
    }
    vrj_rotate_frame(frame,&axis,atan2f(sine,cosine));
    return vrj_orthonormalize(frame);
}
/* every frame from the joints around it, parents before children: a piece
 * member turns with its piece root; a joint with one bone below it follows
 * that bone and a leaf the bone above it (vrj_swing); the root and any joint
 * with several bones below it are fitted to them all with a pull toward the
 * rest pose relative to the parent */
static int vrj_frames(struct vr_articulated_native *rig,int const members[])
{
    int n,k,count=rig->body.count;
    for(n=0;n<count;++n) {
        int parent=rig->body.nodes[n].parent,root=rig->group[n],child,bones=0,only=-1;
        real_vector3d covariance[3],world,target;
        real scale=0,weight;
        int vectors=0;
        if(root!=n) {
            vrj_to_world(&rig->captured[root],&rig->relative[n][0],&rig->captured[n].forward);
            vrj_to_world(&rig->captured[root],&rig->relative[n][1],&rig->captured[n].left);
            vrj_to_world(&rig->captured[root],&rig->relative[n][2],&rig->captured[n].up);
            if(!vrj_orthonormalize(&rig->captured[n])) return FALSE;
            continue;
        }
        if(members[n]) continue;
        for(child=n+1;child<count;++child) {
            if(rig->body.nodes[child].parent!=n ||
               dot_product3d(&rig->rest_in_parent[child],&rig->rest_in_parent[child])<0.000001f) continue;
            ++bones;only=child;
        }
        if(parent>=0 && bones<=1) {
            int other=bones?only:parent;
            for(k=0;k<3;++k) world.n[k]=rig->body.nodes[other].position[k]-rig->body.nodes[n].position[k];
            if(!vrj_swing(rig,n,bones?&rig->rest_in_parent[only]:&rig->rest_parent[n],&world)) return FALSE;
            continue;
        }
        memset(covariance,0,sizeof(covariance));
        if(parent>=0) {
            for(k=0;k<3;++k) world.n[k]=rig->body.nodes[parent].position[k]-rig->body.nodes[n].position[k];
            vrj_accumulate(covariance,1.0f,&world,&rig->rest_parent[n]);
            scale+=dot_product3d(&rig->rest_parent[n],&rig->rest_parent[n]);++vectors;
        }
        for(child=n+1;child<count;++child) {
            if(rig->body.nodes[child].parent!=n) continue;
            for(k=0;k<3;++k) world.n[k]=rig->body.nodes[child].position[k]-rig->body.nodes[n].position[k];
            vrj_accumulate(covariance,1.0f,&world,&rig->rest_in_parent[child]);
            scale+=dot_product3d(&rig->rest_in_parent[child],&rig->rest_in_parent[child]);++vectors;
        }
        if(parent>=0) {
            weight=VRJ_TWIST*(vectors?scale/(real)vectors:1.0f);
            for(k=0;k<3;++k) {
                vrj_to_world(&rig->captured[parent],&rig->relative[n][k],&target);
                covariance[k].i+=weight*target.i;covariance[k].j+=weight*target.j;covariance[k].k+=weight*target.k;
            }
        }
        if(!vrj_extract(&rig->captured[n],covariance)) return FALSE;
    }
    return TRUE;
}
/* each ball and hinge joint J within its authored limits relative to its
 * parent's frame: J's children are turned about J toward the allowed bone
 * direction (the bones below follow through the length constraints) */
static void vrj_limits(struct vr_articulated_native *rig,int const pinned[],int leaves_only)
{
    int n,k,count=rig->body.count;
    for(n=1;n<count;++n) {
        int parent=rig->body.nodes[n].parent,kind=rig->joint_kind[n],child;
        real_vector3d local,goal,goal_world,axis;
        real angle,sine,cosine;
        if(leaves_only) {
            for(child=n+1;child<count&&rig->body.nodes[child].parent!=n;++child);
            if(child<count) continue;
        }
        if(parent<0 || rig->group[n]!=n || (kind!=VR_JOINT_BALL && kind!=VR_JOINT_HINGE)) continue;
        vrj_to_local(&rig->captured[parent],&rig->captured[n].forward,&local);
        if(kind==VR_JOINT_HINGE) {
            /* followed continuously from the hinge's last angle, so a joint
             * pushed past one limit is held there and never flips across its
             * forbidden arc to the other limit (the angle is not read while
             * the bone points along the hinge axis) */
            real bend=rig->joint_bend[n],clamped;
            if(local.i*local.i+local.j*local.j>0.04f) bend+=vrj_wrap(vrj_hinge_angle(&local)-bend);
            clamped=PIN(bend,rig->joint_low[n],rig->joint_high[n]);
            rig->joint_bend[n]=clamped;
            if(fabsf(clamped-bend)<0.0005f && fabsf(local.k)<0.02f) continue;
            goal.i=cosf(clamped);goal.j=sinf(clamped);goal.k=0;
        } else {
            real_vector3d base=rig->joint_axis[n],side;
            real deviation=acosf(PIN(dot_product3d(&base,&local),-1.0f,1.0f)),limit=rig->joint_high[n];
            if(deviation<=limit) continue;
            for(k=0;k<3;++k) side.n[k]=local.n[k]-base.n[k]*cosf(deviation);
            if(normalize3d(&side)<0.000001f) continue;
            for(k=0;k<3;++k) goal.n[k]=base.n[k]*cosf(limit)+side.n[k]*sinf(limit);
        }
        vrj_to_world(&rig->captured[parent],&goal,&goal_world);
        cross_product3d(&rig->captured[n].forward,&goal_world,&axis);
        sine=normalize3d(&axis);cosine=dot_product3d(&rig->captured[n].forward,&goal_world);
        angle=atan2f(sine,cosine);
        if(!(angle>0.0005f) || !isfinite(angle)) continue;
        sine=sinf(angle);cosine=cosf(angle);
        for(child=n+1;child<count;++child) {
            real_vector3d arm;
            int up=rig->body.nodes[child].parent;
            while(up>n) up=rig->body.nodes[up].parent;
            if(up!=n || pinned[child]) continue;
            for(k=0;k<3;++k) arm.n[k]=rig->body.nodes[child].position[k]-rig->body.nodes[n].position[k];
            rotate_vector_about_axis(&arm,&axis,sine,cosine);
            for(k=0;k<3;++k) rig->body.nodes[child].position[k]=rig->body.nodes[n].position[k]+arm.n[k];
        }
        rotate_vector_about_axis(&rig->captured[n].forward,&axis,sine,cosine);
        rotate_vector_about_axis(&rig->captured[n].left,&axis,sine,cosine);
        rotate_vector_about_axis(&rig->captured[n].up,&axis,sine,cosine);
        vrj_orthonormalize(&rig->captured[n]);
    }
}
/* bone lengths, mass-weighted (pinned joints do not move) */
static void vrj_lengths(struct vr_articulated_native *rig,real const weight[])
{
    int n,k,count=rig->body.count;
    for(n=1;n<count;++n) {
        struct vr_articulated_node *a=&rig->body.nodes[n],*b=&rig->body.nodes[a->parent];
        real delta[3],length=0,total=weight[n]+weight[a->parent],correction;
        for(k=0;k<3;++k) {delta[k]=a->position[k]-b->position[k];length+=delta[k]*delta[k];}
        length=sqrtf(length);
        if(total<=0 || length<0.000001f) continue;
        correction=(length-a->length)/(length*total);
        for(k=0;k<3;++k) {a->position[k]-=delta[k]*correction*weight[n];b->position[k]+=delta[k]*correction*weight[a->parent];}
    }
}
/* limbs do not pass through the body: joints at least four bones apart (and
 * not in the same rigid piece) keep apart by half their spheres */
static void vrj_self(struct vr_articulated_native *rig,real const weight[])
{
    int n,other,k,count=rig->body.count;
    for(n=0;n<count;++n) for(other=n+1;other<count;++other) {
        struct vr_articulated_node *a=&rig->body.nodes[n],*b=&rig->body.nodes[other];
        real delta[3],distance=0,minimum,total=weight[n]+weight[other],correction;
        if(!(rig->self_mask[n]&(1ull<<other)) || total<=0) continue;
        minimum=(a->radius+b->radius)*0.5f;
        for(k=0;k<3;++k) {delta[k]=b->position[k]-a->position[k];distance+=delta[k]*delta[k];}
        if(distance>=minimum*minimum) continue;
        distance=sqrtf(distance);
        if(distance<0.000001f) continue;
        correction=(minimum-distance)/(distance*total);
        for(k=0;k<3;++k) {a->position[k]-=delta[k]*correction*weight[n];b->position[k]+=delta[k]*correction*weight[other];}
    }
}
/* Test56: one tick of the parent-relative solver (see above): Verlet
 * integration, then a few passes of bone lengths, rigid pieces, joint limits
 * and self-contact, then one swept move per joint against the world. */
int vr_articulated_native_step(struct vr_articulated_native *rig,float dt,float gravity,
    struct vr_articulated_pin const *pins,int pin_count)
{
    struct vr_articulated_native work;
    real start[VR_ARTICULATED_NODES][3],weight[VR_ARTICULATED_NODES];
    int pinned[VR_ARTICULATED_NODES],members[VR_ARTICULATED_NODES];
    int n,k,count,iteration;
    if(!rig || !rig->prepared || !isfinite(dt) || dt<0.001f || dt>0.05f || !isfinite(gravity) ||
       fabsf(gravity)>100 || pin_count<0 || pin_count>2 || (pin_count && !pins)) return FALSE;
    work=*rig;
    count=work.body.count;
    if(count<1 || count>VR_ARTICULATED_NODES) return FALSE;
    memset(pinned,0,sizeof(pinned));memset(members,0,sizeof(members));
    for(n=0;n<count;++n) if(work.group[n]!=n) ++members[work.group[n]];
    for(n=0;n<count;++n) {
        struct vr_articulated_node *p=&work.body.nodes[n];
        real velocity[3],speed;
        memcpy(start[n],p->position,sizeof(start[n]));
        weight[n]=p->inverse_mass;
        for(k=0;k<3;++k) velocity[k]=(p->position[k]-p->previous[k])*0.985f;
        speed=sqrtf(velocity[0]*velocity[0]+velocity[1]*velocity[1]+velocity[2]*velocity[2]);
        if(!isfinite(speed)) return FALSE;
        if(speed>dt*12) for(k=0;k<3;++k) velocity[k]*=dt*12/speed;
        memcpy(p->previous,p->position,sizeof(p->previous));
        for(k=0;k<3;++k) p->position[k]+=velocity[k];
        p->position[2]-=gravity*dt*dt;
    }
    for(n=0;n<pin_count;++n) {
        int node=pins[n].node;
        real distance=0;
        if(node<0 || node>=count || (n && node==pins[0].node)) return FALSE;
        for(k=0;k<3;++k) {
            real d=pins[n].position[k]-start[node][k];
            if(!isfinite(pins[n].position[k])) return FALSE;
            distance+=d*d;
        }
        if(sqrtf(distance)>0.5f) return FALSE; /* tracking teleport: reject the tick */
        weight[node]=0;pinned[node]=TRUE;
        memcpy(work.body.nodes[node].position,pins[n].position,sizeof(pins[n].position));
        memcpy(work.body.nodes[node].previous,pins[n].position,sizeof(pins[n].position));
    }
    for(iteration=0;iteration<VRJ_ITERATIONS;++iteration) {
        vrj_lengths(&work,weight);
        for(n=0;n<count;++n) if(work.group[n]==n && members[n] && !vrj_piece(&work,n,pinned)) return FALSE;
        if(!vrj_frames(&work,members)) return FALSE;
        vrj_limits(&work,pinned,FALSE);
        if(work.body.self_collision && iteration==VRJ_ITERATIONS-1) vrj_self(&work,weight);
    }
    /* one swept move per joint from where it started the tick, with ground
     * friction (Test55) */
    work.friction=TRUE;
    for(n=0;n<count;++n) {
        if(pinned[n]) continue;
        if(!vr_articulated_native_sweep(&work,start[n],work.body.nodes[n].radius,work.body.nodes[n].position)) return FALSE;
    }
    work.friction=FALSE;
    {
        /* the sweep stopped some joints at the ground: a final pass puts the
         * bones and rigid pieces back together, each joint swept once more for
         * whatever that moved */
        real swept[VR_ARTICULATED_NODES][3];
        for(n=0;n<count;++n) memcpy(swept[n],work.body.nodes[n].position,sizeof(swept[n]));
        for(iteration=0;iteration<VRJ_POST_ITERATIONS;++iteration) {
            vrj_lengths(&work,weight);
            for(n=0;n<count;++n) if(work.group[n]==n && members[n] && !vrj_piece(&work,n,pinned)) return FALSE;
            if(!vrj_frames(&work,members)) return FALSE;
            vrj_limits(&work,pinned,FALSE);
        }
        for(n=0;n<count;++n) {
            real moved=0;
            if(pinned[n]) continue;
            for(k=0;k<3;++k) {real d=work.body.nodes[n].position[k]-swept[n][k];moved+=d*d;}
            if(moved<1e-10f) continue;
            if(!vr_articulated_native_sweep(&work,swept[n],work.body.nodes[n].radius,work.body.nodes[n].position)) return FALSE;
        }
    }
    if(!vrj_frames(&work,members)) return FALSE;
    /* a joint with nothing below it (a hand, a jaw) has only its frame to
     * hold in its limits */
    vrj_limits(&work,pinned,TRUE);
    for(n=0;n<count;++n) {
        for(k=0;k<3;++k) if(!isfinite(work.body.nodes[n].position[k])) return FALSE;
        memcpy(work.captured[n].position.n,work.body.nodes[n].position,sizeof(work.body.nodes[n].position));
        if(!valid_real_matrix4x3(&work.captured[n])) return FALSE;
    }
    *rig=work;
    return TRUE;
}
