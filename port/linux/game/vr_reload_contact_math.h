#ifndef VR_RELOAD_CONTACT_MATH_H
#define VR_RELOAD_CONTACT_MATH_H
#include <math.h>
/* Segment versus inflated authored local bounds. Starting inside reports the
 * nearest outward face; zero-length/nonfinite input cannot produce NaNs. */
static int vr_reload_box(float const from[3],float const delta[3],float const lo[3],float const hi[3],
    float radius,float *fraction,float normal[3])
{
    float enter=0,exit=1,near_distance=1e30f;int face=-1,near_face=0;float sign=0,near_sign=-1;int inside=1;
    if(!isfinite(radius)||radius<0)return 0;
    for(int a=0;a<3;a++) {
        if(!isfinite(from[a])||!isfinite(delta[a])||!isfinite(lo[a])||!isfinite(hi[a])||lo[a]>hi[a])return 0;
        float low=lo[a]-radius,high=hi[a]+radius;
        if(from[a]<low||from[a]>high)inside=0;
        float d=from[a]-low;if(d<near_distance){near_distance=d;near_face=a;near_sign=-1;}
        d=high-from[a];if(d<near_distance){near_distance=d;near_face=a;near_sign=1;}
        if(fabsf(delta[a])<1e-9f){if(from[a]<low||from[a]>high)return 0;continue;}
        float t1=(low-from[a])/delta[a],t2=(high-from[a])/delta[a],n=-1;
        if(t1>t2){float swap=t1;t1=t2;t2=swap;n=1;}
        if(t1>enter){enter=t1;face=a;sign=n;}
        if(t2<exit)exit=t2;
        if(enter>exit)return 0;
    }
    if(exit<0||enter>1)return 0;
    if(inside){face=near_face;sign=near_sign;enter=0;}
    if(face<0)return 0;
    normal[0]=normal[1]=normal[2]=0;normal[face]=sign;*fraction=enter;return 1;
}

/* A tracked palm is a sphere: contact with a model part's authored bounds is
 * based on the closest point on that box, not a large center-distance reach. */
static inline int vr_reload_sphere_touches_box(float const point[3],float const lo[3],float const hi[3],float radius)
{
    float distance2=0.0f;
    if(!isfinite(radius)||radius<0.0f)return 0;
    for(int axis=0;axis<3;axis++) {
        float delta=0.0f;
        if(!isfinite(point[axis])||!isfinite(lo[axis])||!isfinite(hi[axis])||lo[axis]>hi[axis])return 0;
        if(point[axis]<lo[axis])delta=lo[axis]-point[axis];
        else if(point[axis]>hi[axis])delta=point[axis]-hi[axis];
        distance2+=delta*delta;
    }
    return isfinite(distance2)&&distance2<=radius*radius;
}
#endif
