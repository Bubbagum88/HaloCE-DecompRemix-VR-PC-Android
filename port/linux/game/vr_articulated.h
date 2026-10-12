/* Bounded articulated-position solver. No engine state or network mutation.
 * The live-NPC adapter must supply verified joints, collision and recovery. */
#ifndef HALO_VR_ARTICULATED_H
#define HALO_VR_ARTICULATED_H
#define VR_ARTICULATED_NODES 64
struct vr_articulated_node {
    float position[3], previous[3];
    float inverse_mass, radius, length, max_bend;
    int parent;
};
struct vr_articulated_body {
    int count,self_collision;
    struct vr_articulated_node nodes[VR_ARTICULATED_NODES];
};
struct vr_articulated_pin { int node; float position[3]; };
/* Sweep old->new; returns a corrected finite position. Caller owns BSP/object
 * filtering. Invoked for each free node after each constraint iteration. */
typedef int (*vr_articulated_sweep)(void *context, float const old[3], float radius, float next[3]);
int vr_articulated_step(struct vr_articulated_body *body, float dt, float gravity,
    struct vr_articulated_pin const *pins, int pin_count, vr_articulated_sweep sweep, void *context);
int vr_articulated_recovery(struct vr_articulated_body *body, float const target[][3],
    float amount, vr_articulated_sweep sweep, void *context);
#endif
