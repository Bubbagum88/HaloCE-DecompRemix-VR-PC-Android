#ifndef HALO_VR_ARTICULATED_NATIVE_H
#define HALO_VR_ARTICULATED_NATIVE_H
#include "vr_articulated.h"
/* Native joint metadata and transient solver state; never serialized directly
 * into campaign saves or trusted from a network client. */
enum
{
    /* Test56: how a joint is held to its parent (vr_articulated_native_prepare) */
    VR_JOINT_FREE,      /* no authored limit */
    VR_JOINT_BALL,      /* the bone within a cone about its authored rest direction */
    VR_JOINT_HINGE,     /* the bone turns about the parent's up, within an arc */
    VR_JOINT_RIGID      /* no movement: one rigid piece with its parent */
};
struct vr_articulated_native {
    long unit_index, graph_index;
    int impact_enabled;
    real impact_units;
    /* Test55: ground friction on the solver's own integration sweeps only
     * (never recovery or pins); set by vr_articulated_native_step */
    int friction;
    struct vr_articulated_body body;
    unsigned long joint_flags[VR_ARTICULATED_NODES];
    real_vector3d joint_axis[VR_ARTICULATED_NODES];
    real joint_range[VR_ARTICULATED_NODES];
    real_matrix4x3 captured[VR_ARTICULATED_NODES];
    /* Test56: the parent-relative joint solver's rest data, from the pose at
     * capture (vr_articulated_native_prepare). Frames are fitted from joint
     * positions each tick; limits act on each joint relative to its parent. */
    int prepared;
    int joint_kind[VR_ARTICULATED_NODES];
    int group[VR_ARTICULATED_NODES];             /* rigid piece: the node it is rigid with (itself if none) */
    real joint_low[VR_ARTICULATED_NODES], joint_high[VR_ARTICULATED_NODES]; /* hinge arc (radians) or cone (high) */
    real joint_bend[VR_ARTICULATED_NODES];       /* a hinge's last angle, within its arc */
    real_vector3d rest_parent[VR_ARTICULATED_NODES];   /* the parent's place, in this node's frame */
    real_vector3d rest_in_parent[VR_ARTICULATED_NODES];/* this node's place, in its parent's frame */
    real_vector3d rest_group[VR_ARTICULATED_NODES];    /* this node's place in its rigid piece's root frame */
    real_vector3d relative[VR_ARTICULATED_NODES][3];   /* this frame's axes in the parent's (or piece root's) frame */
    unsigned long long self_mask[VR_ARTICULATED_NODES];/* later joints this one keeps clear of (self contact) */
};
int vr_articulated_native_capture(long unit_index, struct vr_articulated_native *rig);
/* Test56: computes the rest data above from rig->captured and the joint
 * metadata (capture calls it; step refuses a rig without it). */
int vr_articulated_native_prepare(struct vr_articulated_native *rig);
int vr_articulated_native_sweep(void *context,float const old[3],float radius,float next[3]);
int vr_articulated_native_step(struct vr_articulated_native *rig,float dt,float gravity,
    struct vr_articulated_pin const *pins,int pin_count);
#endif
