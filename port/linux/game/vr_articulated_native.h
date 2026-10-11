#ifndef HALO_VR_ARTICULATED_NATIVE_H
#define HALO_VR_ARTICULATED_NATIVE_H
#include "vr_articulated.h"
/* Native joint metadata and transient solver state; never serialized directly
 * into campaign saves or trusted from a network client. */
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
};
int vr_articulated_native_capture(long unit_index, struct vr_articulated_native *rig);
int vr_articulated_native_sweep(void *context,float const old[3],float radius,float next[3]);
int vr_articulated_native_step(struct vr_articulated_native *rig,float dt,float gravity,
    struct vr_articulated_pin const *pins,int pin_count);
#endif
