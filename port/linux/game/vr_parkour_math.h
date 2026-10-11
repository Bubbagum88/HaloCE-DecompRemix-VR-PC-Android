#ifndef VR_PARKOUR_MATH_H
#define VR_PARKOUR_MATH_H
#include <math.h>
static float vr_pk_bound(float value, float fallback, float low, float high)
{
    if (!isfinite(value)) return fallback;
    return value < low ? low : value > high ? high : value;
}
static void vr_pk_cap(float v[3], float maximum)
{
    float length = sqrtf(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);
    if (!isfinite(length)) { v[0]=v[1]=v[2]=0; return; }
    if (length>maximum && length>0) for(int i=0;i<3;i++) v[i]*=maximum/length;
}
/* Reject inward-looking impulses and provide a deliberate outward departure. */
static void vr_pk_leap(float const look[3], float const normal[3], float speed,
    float upward, float out[3])
{
    float into=look[0]*normal[0]+look[1]*normal[1]+look[2]*normal[2];
    for(int i=0;i<3;i++) out[i]=(look[i]-(into<0?into:0)*normal[i]+normal[i]*0.40f)*speed;
    if(out[2]<upward)out[2]=upward;
    vr_pk_cap(out,speed*1.5f);
}
static int vr_pk_vertical(float const normal[3])
{
    float length=normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2];
    return isfinite(length)&&length>0.9f&&length<1.1f&&fabsf(normal[2])<0.35f;
}
/* Test54: what a free hand may grip to climb: walls, rock faces steeper than
 * about 40 degrees, overhangs and ceilings, and any surface (a ledge's top)
 * at or above the waist. The floor under the feet is never a hold. */
static inline int vr_pk_climbable(float const normal[3], int above_waist)
{
    float length=normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2];
    if(!(isfinite(length)&&length>0.9f&&length<1.1f))return 0;
    return normal[2]<0.75f||above_waist;
}
/* A grip squeezed just before the hand meets the surface still takes hold
 * within this many ticks (a reaching hand closes as it arrives). */
#define VR_PK_GRIP_GRACE_TICKS 6
#endif
