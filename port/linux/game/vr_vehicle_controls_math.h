#ifndef VR_VEHICLE_CONTROLS_MATH_H
#define VR_VEHICLE_CONTROLS_MATH_H
#include <math.h>
/* Test56: full lock of the immersive controls (60 degrees each way) and the
 * dead zone about centre (1.5 degrees) */
#define VR_WHEEL_LOCK 1.04719755f
#define VR_WHEEL_DEAD_ZONE 0.0261799f
/* Test66: the Warthog's wheel turns with the hands past full lock (to 120
 * degrees each way); the steering still reaches full lock at 60 */
#define VR_WHEEL_TURN_LIMIT 2.0943951f
struct vr_wheel_grip {int held;float start,base,last,turned;};
static void vr_wheel_grip_start(struct vr_wheel_grip *s,const float p[2],float base)
{ s->held=isfinite(p[0])&&isfinite(p[1])&&hypotf(p[0],p[1])>0.001f;s->start=atan2f(p[1],p[0]);s->base=base;s->last=s->start;s->turned=0; }
static float vr_wheel_grip_angle(const struct vr_wheel_grip *s,const float p[2])
{
 if(!s->held||!isfinite(p[0])||!isfinite(p[1])||hypotf(p[0],p[1])<0.001f)return s->base;
 float d=atan2f(p[1],p[0])-s->start;
 while(d>3.14159265f)d-=6.2831853f;while(d< -3.14159265f)d+=6.2831853f;
 return fminf(VR_WHEEL_LOCK,fmaxf(-VR_WHEEL_LOCK,s->base+d));
}
/* Test66: the hand's turn followed frame to frame, so a turn past half a
 * circle from where the hand took the wheel never wraps to the other side
 * (the owner's Test65 drive: turned far, the wheel snapped to the opposite
 * lock and the Warthog twitched). Past `limit` the hand slides on the rim:
 * turned back, the wheel follows at once. */
static float vr_wheel_grip_follow(struct vr_wheel_grip *s,const float p[2],float limit)
{
 if(s->held&&isfinite(p[0])&&isfinite(p[1])&&hypotf(p[0],p[1])>=0.001f) {
  float a=atan2f(p[1],p[0]),d=a-s->last;
  while(d>3.14159265f)d-=6.2831853f;while(d< -3.14159265f)d+=6.2831853f;
  s->last=a;s->turned+=d;
  if(s->base+s->turned>limit)s->turned=limit-s->base;
  if(s->base+s->turned< -limit)s->turned=-limit-s->base;
 }
 return fminf(limit,fmaxf(-limit,s->base+s->turned));
}
#endif
