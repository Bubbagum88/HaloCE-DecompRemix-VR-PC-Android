#ifndef VR_VEHICLE_CONTROLS_MATH_H
#define VR_VEHICLE_CONTROLS_MATH_H
#include <math.h>
struct vr_wheel_grip {int held;float start,base;};
static void vr_wheel_grip_start(struct vr_wheel_grip *s,const float p[2],float base)
{ s->held=isfinite(p[0])&&isfinite(p[1])&&hypotf(p[0],p[1])>0.001f;s->start=atan2f(p[1],p[0]);s->base=base; }
static float vr_wheel_grip_angle(const struct vr_wheel_grip *s,const float p[2])
{
 if(!s->held||!isfinite(p[0])||!isfinite(p[1])||hypotf(p[0],p[1])<0.001f)return s->base;
 float d=atan2f(p[1],p[0])-s->start;
 while(d>3.14159265f)d-=6.2831853f;while(d< -3.14159265f)d+=6.2831853f;
 return fminf(1.04719755f,fmaxf(-1.04719755f,s->base+d));
}
#endif
