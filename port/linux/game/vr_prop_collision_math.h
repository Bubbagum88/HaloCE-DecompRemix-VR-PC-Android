#ifndef VR_PROP_COLLISION_MATH_H
#define VR_PROP_COLLISION_MATH_H
#include <math.h>
/* Collision in an OBB's local frame. Half extents come from authored native
 * collision vertices, not rendered scenery or guessed sizes. */
static float vr_prop_dot(float const a[3],float const b[3])
{return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void vr_prop_cross(float const a[3],float const b[3],float c[3])
{c[0]=a[1]*b[2]-a[2]*b[1];c[1]=a[2]*b[0]-a[0]*b[2];c[2]=a[0]*b[1]-a[1]*b[0];}
static int vr_prop_finite(float const v[3])
{return isfinite(v[0])&&isfinite(v[1])&&isfinite(v[2]);}
static int vr_prop_separated(float const axis[3],float const v[3][3],float const half[3],float skin)
{
    float p[3],radius=0,lo,hi;int i;
    if(vr_prop_dot(axis,axis)<1e-16f)return 0;
    for(i=0;i<3;++i){p[i]=vr_prop_dot(axis,v[i]);radius+=fabsf(axis[i])*half[i];}
    lo=fminf(p[0],fminf(p[1],p[2]));hi=fmaxf(p[0],fmaxf(p[1],p[2]));
    /* Tangent contact is allowed; skin must be nonnegative and tiny. */
    skin*=sqrtf(vr_prop_dot(axis,axis));
    return lo>=radius-skin||hi<=-radius+skin;
}
static int vr_prop_triangle_overlap(float const half[3],float const vertices[3][3],float skin)
{
    float edges[3][3],normal[3],axis[3];int i,j,k;
    if(!vr_prop_finite(half)||!isfinite(skin)||skin<0)return 1;
    for(i=0;i<3;++i)if(half[i]<=0||!vr_prop_finite(vertices[i]))return 1;
    for(i=0;i<3;++i)for(j=0;j<3;++j)edges[i][j]=vertices[(i+1)%3][j]-vertices[i][j];
    for(i=0;i<3;++i){axis[0]=axis[1]=axis[2]=0;axis[i]=1;
        if(vr_prop_separated(axis,vertices,half,skin))return 0;}
    vr_prop_cross(edges[0],edges[1],normal);
    if(vr_prop_separated(normal,vertices,half,skin))return 0;
    for(i=0;i<3;++i)for(j=0;j<3;++j){float basis[3]={0};basis[j]=1;
        vr_prop_cross(edges[i],basis,axis);
        if(vr_prop_separated(axis,vertices,half,skin))return 0;}
    /* Degenerate triangles are still treated conservatively as contacts. */
    for(k=0;k<3;++k)if(!isfinite(normal[k]))return 1;
    return 1;
}
static float vr_prop_point_box_distance2(float const p[3],float const half[3])
{
    float sum=0;int i;
    for(i=0;i<3;++i){float d=fmaxf(0,fabsf(p[i])-half[i]);sum+=d*d;}
    return sum;
}
static float vr_prop_segment_distance2(float const a[3],float const b[3],float const half[3],float t)
{
    float p[3];int i;for(i=0;i<3;++i)p[i]=a[i]+(b[i]-a[i])*t;
    return vr_prop_point_box_distance2(p,half);
}
static int vr_prop_capsule_overlap(float const half[3],float const a[3],float const b[3],float radius,float skin)
{
    /* Squared distance from a segment to a convex box is convex in t.
     * Fixed ternary iterations plus endpoint checks bound the work. The
     * residual interval's maximum travel supplies a conservative margin. */
    float low=0,high=1,d,length=0,margin;int i;
    if(!vr_prop_finite(half)||!vr_prop_finite(a)||!vr_prop_finite(b)||
        !isfinite(radius)||radius<0||!isfinite(skin)||skin<0)return 1;
    for(i=0;i<3;++i){if(half[i]<=0)return 1;length+=(b[i]-a[i])*(b[i]-a[i]);}
    if(!isfinite(length))return 1;
    if(radius<=skin) {
        float enter=0,leave=1;
        for(i=0;i<3;++i){float extent=half[i]-skin,delta=b[i]-a[i];
            if(extent<=0)return 0;
            if(fabsf(delta)<1e-12f){if(fabsf(a[i])>=extent)return 0;}
            else {float t0=(-extent-a[i])/delta,t1=(extent-a[i])/delta;
                enter=fmaxf(enter,fminf(t0,t1));leave=fminf(leave,fmaxf(t0,t1));
                if(enter>=leave)return 0;}
        }
        return enter<leave;
    }
    for(i=0;i<24;++i){float l=(2*low+high)/3,r=(low+2*high)/3;
        if(vr_prop_segment_distance2(a,b,half,l)<vr_prop_segment_distance2(a,b,half,r))high=r;else low=l;}
    d=fminf(vr_prop_segment_distance2(a,b,half,(low+high)*.5f),
        fminf(vr_prop_point_box_distance2(a,half),vr_prop_point_box_distance2(b,half)));
    if(!isfinite(d))return 1;
    margin=fmaxf(0,radius-skin)+sqrtf(length)*(high-low)*.5f;
    return d<margin*margin;
}
#endif
