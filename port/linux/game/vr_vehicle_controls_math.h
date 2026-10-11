#ifndef VR_VEHICLE_CONTROLS_MATH_H
#define VR_VEHICLE_CONTROLS_MATH_H
#include <math.h>
/* Test56: full lock of the immersive controls (60 degrees each way) and the
 * dead zone about centre (1.5 degrees) */
#define VR_WHEEL_LOCK 1.04719755f
#define VR_WHEEL_DEAD_ZONE 0.0261799f
struct vr_wheel_grip {int held;float start,base;};
static void vr_wheel_grip_start(struct vr_wheel_grip *s,const float p[2],float base)
{ s->held=isfinite(p[0])&&isfinite(p[1])&&hypotf(p[0],p[1])>0.001f;s->start=atan2f(p[1],p[0]);s->base=base; }
static float vr_wheel_grip_angle(const struct vr_wheel_grip *s,const float p[2])
{
 if(!s->held||!isfinite(p[0])||!isfinite(p[1])||hypotf(p[0],p[1])<0.001f)return s->base;
 float d=atan2f(p[1],p[0])-s->start;
 while(d>3.14159265f)d-=6.2831853f;while(d< -3.14159265f)d+=6.2831853f;
 return fminf(VR_WHEEL_LOCK,fmaxf(-VR_WHEEL_LOCK,s->base+d));
}
#endif
