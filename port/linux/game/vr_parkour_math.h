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
/* Test70: the wall jump, where the player looks (the owner: "the intended
 * wall-jump behavior should still primarily use head/view direction"; a
 * player's report of launches in directions not expected). The level look
 * sets the way (the head's pitch no longer shortens it), turned only as far
 * as needed to leave the wall (at least 35% of it away from the wall), the
 * stick bending it a fifth; the speed the body has is kept (up to 1.5x the
 * jump's), the way it goes is the look's; the height is the jump's, more
 * when looking up. `stick` world horizontal (zero: none) */
static void vr_pk_wall_leap(float const look[3], float const normal[3], float const velocity[3],
    float const stick[2], float speed, float upward, float out[3])
{
    float h[2] = { look[0], look[1] }, n[2] = { normal[0], normal[1] }, length, away, carried, s2;
    length = sqrtf(n[0]*n[0]+n[1]*n[1]);
    if (!(length > 0.1f) || !isfinite(length)) { vr_pk_leap(look, normal, speed, upward, out); return; }
    n[0] /= length; n[1] /= length;
    length = sqrtf(h[0]*h[0]+h[1]*h[1]);
    /* (looking straight up or down: away from the wall) */
    if (!(length > 0.15f) || !isfinite(length)) { h[0] = n[0]; h[1] = n[1]; }
    else { h[0] /= length; h[1] /= length; }
    s2 = stick ? sqrtf(stick[0]*stick[0]+stick[1]*stick[1]) : 0.0f;
    if (s2 > 0.3f && isfinite(s2)) {
        h[0] = h[0]*0.8f + stick[0]/s2*0.2f;
        h[1] = h[1]*0.8f + stick[1]/s2*0.2f;
        length = sqrtf(h[0]*h[0]+h[1]*h[1]);
        if (length > 0.001f) { h[0] /= length; h[1] /= length; }
    }
    away = h[0]*n[0]+h[1]*n[1];
    if (away < 0.35f) {
        /* the look's way along the wall kept, 35% of it away from the wall */
        float t[2] = { h[0]-away*n[0], h[1]-away*n[1] };
        length = sqrtf(t[0]*t[0]+t[1]*t[1]);
        if (length > 0.001f) {
            t[0] /= length; t[1] /= length;
            h[0] = 0.35f*n[0] + 0.9367497f*t[0];
            h[1] = 0.35f*n[1] + 0.9367497f*t[1];
        }
        /* (looking straight at the wall: straight off it) */
        else { h[0] = n[0]; h[1] = n[1]; }
    }
    carried = velocity ? sqrtf(velocity[0]*velocity[0]+velocity[1]*velocity[1]) : 0.0f;
    if (!isfinite(carried)) carried = 0.0f;
    carried = carried > speed ? carried : speed;
    if (carried > speed*1.5f) carried = speed*1.5f;
    out[0] = h[0]*carried;
    out[1] = h[1]*carried;
    out[2] = upward + (look[2] > 0.0f && isfinite(look[2]) ? look[2]*speed*0.5f : 0.0f);
}
/* the leap held against air control for a moment (VR_PK_LEAP_HOLD_TICKS
 * after a wall jump, until landing, a new wall run or a climbing hold): the
 * horizontal velocity across the leap's way (`direction`, level and of unit
 * length) taken out, and along it no less than the leap's speed. The game's
 * air control turned a leap back toward the stick held along the wall the run
 * went (the owner: the leap did not always go where the head looked). The
 * height is left to the jump and gravity. */
#define VR_PK_LEAP_HOLD_TICKS 12
static void vr_pk_leap_hold(float const direction[2], float speed, float velocity[3])
{
    float along;
    if (!isfinite(direction[0]) || !isfinite(direction[1]) || !isfinite(speed) ||
        !isfinite(velocity[0]) || !isfinite(velocity[1]))
        return;
    along = velocity[0]*direction[0] + velocity[1]*direction[1];
    if (!(along >= speed)) along = speed;
    velocity[0] = direction[0]*along;
    velocity[1] = direction[1]*along;
}
/* the leap's level way and speed from its velocity (0: none, too slow to
 * hold) */
static int vr_pk_leap_start(float const velocity[3], float direction[2], float *speed)
{
    float h = sqrtf(velocity[0]*velocity[0] + velocity[1]*velocity[1]);
    if (!(h > 0.001f) || !isfinite(h)) return 0;
    direction[0] = velocity[0]/h;
    direction[1] = velocity[1]/h;
    *speed = h;
    return 1;
}
static int vr_pk_vertical(float const normal[3])
{
    float length=normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2];
    return isfinite(length)&&length>0.9f&&length<1.1f&&fabsf(normal[2])<0.35f;
}
/* Test66: a wall to run along need not be a vertical plane (the owner's
 * Test65 run failed on Silent Cartographer's rock walls): any face steeper
 * than ~53 degrees, an overhang as much; the knee-high probe still wants a
 * real wall, so a steep hill underfoot is never one */
static int vr_pk_runnable(float const normal[3],int low)
{
    float length=normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2];
    if(!(isfinite(length)&&length>0.9f&&length<1.1f))return 0;
    return low?fabsf(normal[2])<0.35f:fabsf(normal[2])<0.6f;
}
/* Test66: the wall followed round a bend or over a seam: the facing run along
 * eases toward the face met (a sharp corner, past ~80 degrees, is taken whole) */
static void vr_pk_blend_normal(float normal[3],float const met[3])
{
    float dot=normal[0]*met[0]+normal[1]*met[1]+normal[2]*met[2],length;
    int k;
    if(!(dot>0.17f)){normal[0]=met[0];normal[1]=met[1];normal[2]=met[2];return;}
    for(k=0;k<3;k++)normal[k]=normal[k]*0.6f+met[k]*0.4f;
    length=sqrtf(normal[0]*normal[0]+normal[1]*normal[1]+normal[2]*normal[2]);
    if(length>0.001f)for(k=0;k<3;k++)normal[k]/=length;
    else{normal[0]=met[0];normal[1]=met[1];normal[2]=met[2];}
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
