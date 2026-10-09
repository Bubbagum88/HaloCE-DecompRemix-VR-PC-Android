#ifndef VR_HAND_COMPLIANCE_MATH_H
#define VR_HAND_COMPLIANCE_MATH_H
#include <math.h>
struct vr_hand_compliance { float visibility;int hidden; };
/* Arm compliance may fade the limb when its animation pose cannot follow the
 * tracked controller. Keep the hand subtree at its already collision-limited
 * pose so it remains visible and does not snap back toward the elbow. */
static float vr_hand_compliance_node_visibility(float visibility,int in_hand_subtree)
{
    if(in_hand_subtree)return 1.0f;
    if(!isfinite(visibility))return 0.0f;
    if(visibility<0.0f)return 0.0f;
    if(visibility>1.0f)return 1.0f;
    return visibility;
}
static float vr_hand_compliance_node_position(float arm_position,float node_position,
    float visibility,int in_hand_subtree)
{
    float node_visibility=vr_hand_compliance_node_visibility(visibility,in_hand_subtree);
    return arm_position+(node_position-arm_position)*node_visibility;
}
static float vr_hand_compliance_step(struct vr_hand_compliance *state,float separation,float limit,float dt,int reset)
{
    if(!isfinite(limit)||limit<.08f||limit>.40f)limit=.18f;
    if(!isfinite(separation)||separation<0)separation=limit+1;
    if(reset) {state->hidden=separation>limit;state->visibility=state->hidden?0:1;}
    if(separation>limit)state->hidden=1;
    else if(separation<limit*.75f)state->hidden=0;
    if(!isfinite(dt)||dt<0)dt=0;if(dt>.05f)dt=.05f;
    state->visibility+=(state->hidden?-1:1)*dt/.08f;
    if(state->visibility<0)state->visibility=0;
    if(state->visibility>1)state->visibility=1;
    return state->visibility;
}
#endif
