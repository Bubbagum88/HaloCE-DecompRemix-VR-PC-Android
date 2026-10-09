"""Execute production finger-volume gathering/cache with a counted native query.

This proves rejection/cache policy, not native scene collision or headset feel.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/test38-contact-volume"
OUT.mkdir(parents=True, exist_ok=True)
render = (ROOT / "port/linux/game/vr_render.c").read_text()
start = render.rfind("static struct {", 0, render.index("} vr_finger_volume[2];"))
end = render.index("static boolean vr_finger_reload_only", start)
production = render[start:end]
prefix = r'''
#include <assert.h>
#include <math.h>
#include <string.h>
typedef float real;
typedef int boolean;
typedef struct { float n[3]; } real_point3d, real_vector3d;
typedef struct { real_point3d position; } real_matrix4x3;
struct animation_graph { int unused; };
struct collision_feature_list { int count[3]; };
#define TRUE 1
#define FALSE 0
#define NONE -1
#define MAX(a,b) ((a)>(b)?(a):(b))
#define NUMBER_OF_COLLISION_FEATURE_TYPES 3
#define VR_HAND_TOUCH_FLAGS 123
static unsigned long vr_contact_epoch;
static struct { int gathers, maximum_features; } vr_contact_stats;
static float units = 1;
static double time_now = 1;
static int enabled = 1, calls, feature_count = 1;
static float vr_units_per_metre(void) { return units; }
static double vr_pose_time(void) { return time_now; }
static int config_boolean(char const *key) { assert(!strcmp(key,"vr.contact_volumes")); return enabled; }
static int valid_real_point3d(real_point3d const *p) { return isfinite(p->n[0])&&isfinite(p->n[1])&&isfinite(p->n[2]); }
static void vr_point_minus(real_point3d const *a, real_point3d const *b, real_vector3d *v) {
    for(int i=0;i<3;i++)v->n[i]=a->n[i]-b->n[i];
}
static float vr_length(real_vector3d const *v) { return sqrtf(v->n[0]*v->n[0]+v->n[1]*v->n[1]+v->n[2]*v->n[2]); }
static void collision_get_features_in_sphere(int flags, real_point3d const *center,
    float radius, float height, float width, long ignore, struct collision_feature_list *out) {
    assert(flags==VR_HAND_TOUCH_FLAGS && valid_real_point3d(center));
    assert(isfinite(radius)&&radius>0&&height==0&&width>0&&ignore>=0);
    calls++; memset(out,0,sizeof(*out));out->count[0]=feature_count;
}
'''
main = r'''
int main(void) {
    real_matrix4x3 m[4]={0}; short j[5][3]; struct animation_graph graph={0}, other={0};
    memset(j,255,sizeof(j));j[0][0]=1;j[0][1]=2;j[0][2]=3;
    m[1].position.n[0]=.03f;m[2].position.n[0]=.06f;m[3].position.n[0]=.09f;
#define PREP() vr_finger_volume_prepare(0,10,20,&graph,m,0,j)
    PREP();assert(calls==1&&vr_finger_volume[0].usable);
    PREP();assert(calls==1); /* same-pose second eye */
    vr_finger_volume_prepare(0,10,21,&graph,m,0,j);assert(calls==2); /* parent changed */
    vr_contact_epoch++;PREP();assert(calls==3);
    time_now++;PREP();assert(calls==4);
    vr_finger_volume_prepare(0,11,20,&graph,m,0,j);assert(calls==5);
    vr_finger_volume_prepare(0,10,20,&other,m,0,j);assert(calls==6);
    PREP();assert(calls==7);
    m[0].position.n[1]=.001f;PREP();assert(calls==8); /* moved hand */
    m[3].position.n[0]=.12f;PREP();assert(calls==9); /* larger candidate bound */
    m[0].position.n[0]=NAN;PREP();assert(calls==9&&vr_finger_volume_hand==-1);
    m[0].position.n[0]=0;
    for(int node=1;node<4;node++) {
        float old=m[node].position.n[1];m[node].position.n[1]=NAN;
        PREP();assert(calls==9&&vr_finger_volume_hand==-1);m[node].position.n[1]=old;
    }
    units=NAN;PREP();assert(calls==9&&vr_finger_volume_hand==-1);units=1;
    enabled=0;PREP();assert(calls==9&&vr_finger_volume_hand==-1);enabled=1;
    feature_count=96;time_now++;PREP();assert(calls==10&&vr_finger_volume[0].usable);
    feature_count=97;time_now++;PREP();assert(calls==11&&!vr_finger_volume[0].usable);
    feature_count=256;time_now++;PREP();assert(calls==12&&!vr_finger_volume[0].usable);
    PREP();assert(calls==12&&!vr_finger_volume[0].usable); /* dense cached fallback */
    m[3].position.n[0]=10;time_now++;PREP();assert(calls==12&&!vr_finger_volume[0].usable);
    vr_finger_volume_prepare(-1,10,20,&graph,m,0,j);assert(calls==12&&vr_finger_volume_hand==-1);
    return 0;
}
'''
p = OUT / "contact_volume.c"
p.write_text(prefix + production + main)
subprocess.run(["clang", "-std=c11", "-O1", "-Wall", "-Wextra", "-Werror",
                "-fsanitize=address,undefined", str(p), "-lm", "-o", str(OUT / "contact_volume")], check=True)
subprocess.run([str(OUT / "contact_volume")], check=True)
print("PASS: production finger volume finite guards, both-eye cache, identity invalidation, 96/97 feature boundary and saturation fallback")
