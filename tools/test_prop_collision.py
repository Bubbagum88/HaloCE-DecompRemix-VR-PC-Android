"""Production OBB collision primitives, including face/edge/corner contacts."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/prop-collision-tests';out.mkdir(parents=True,exist_ok=True)
source=r'''
#include <assert.h>
#include <stdio.h>
#include "vr_prop_collision_math.h"
int main(void){
 float h[3]={1,1,1},v[3][3]={{-2,-2,0},{2,-2,0},{0,2,0}};
 assert(vr_prop_triangle_overlap(h,v,0));
 for(int i=0;i<3;i++)v[i][2]=2;
 assert(!vr_prop_triangle_overlap(h,v,0));
 for(int i=0;i<3;i++)v[i][2]=1;
 assert(!vr_prop_triangle_overlap(h,v,.00001f));
 for(int i=0;i<3;i++)v[i][2]=.99f;
 assert(vr_prop_triangle_overlap(h,v,.00001f));
 float a[3]={-2,0,0},b[3]={2,0,0};
 assert(vr_prop_capsule_overlap(h,a,b,0,0));
 a[1]=b[1]=1.2f;
 assert(!vr_prop_capsule_overlap(h,a,b,.1f,0));
 assert(vr_prop_capsule_overlap(h,a,b,.3f,0));
 a[1]=b[1]=1;
 assert(!vr_prop_capsule_overlap(h,a,b,0,.00001f));
 a[0]=b[0]=0;a[1]=b[1]=0;
 assert(vr_prop_capsule_overlap(h,a,b,0,0));
 assert(vr_prop_capsule_overlap(h,a,b,.1f,0));
 a[0]=NAN;assert(vr_prop_capsule_overlap(h,a,b,.1f,0));
 v[0][0]=NAN;assert(vr_prop_triangle_overlap(h,v,0));
 /* A corner triangle lies within the AABB broadphase but outside the OBB
  * on a cross-product separating axis. */
 float corner[3][3]={{.9f,1.3f,0},{1.3f,.9f,0},{1.4f,1.4f,0}};
 assert(!vr_prop_triangle_overlap(h,corner,0));
 for(int axis=0;axis<3;++axis)for(int sign=-1;sign<=1;sign+=2){
   float tri[3][3]={{-2,-2,0},{2,-2,0},{0,2,0}},rot[3][3];
   for(int i=0;i<3;++i)for(int j=0;j<3;++j)rot[i][(j+axis)%3]=tri[i][j]*sign;
   assert(vr_prop_triangle_overlap(h,rot,0));
 }
 puts("PASS: production prop OBB triangle SAT and capsule/segment tests; tangent, penetrating, corner, symmetric and invalid-input cases");
}
'''
c=out/'collision.c';c.write_text(source);binary=out/'collision'
subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
 '-I'+str(ROOT/'port/linux/game'),str(c),'-lm','-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
