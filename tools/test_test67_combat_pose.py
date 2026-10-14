"""Executable tests of the production additive pose helper; synthetic geometry.

Names/topology exercise the verified Halo human and digitigrade layouts; no
game animation/mesh or model data is embedded. Native feet and every bone edge
must survive every mode, phase, side and weight. No game is launched.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef union {struct {float x,y,z;};struct {float i,j,k;};float n[3];} real_point3d,real_vector3d;
typedef struct {float scale;union {float n[4][3];struct {real_vector3d forward,left,up;real_point3d position;};};} real_matrix4x3;
struct model_node {char name[32];short next_sibling_node_index,first_child_node_index,parent_node_index,pad;};
#include "port/linux/game/vr_combat_pose.h"
static struct model_node nodes[64];
static real_matrix4x3 native[64],out[64],saved[64];
static struct vr_combat_pose_request request;
static int count;
static void fixture(int digitigrade)
{
 static char const *names[]={"bip01 pelvis","bip01 l thigh","bip01 r thigh","bip01 spine","bip01 l calf","bip01 r calf","bip01 spine1","bip01 l clavicle","bip01 l foot","bip01 neck","bip01 r clavicle","bip01 r foot","bip01 head","bip01 l upperarm","bip01 r upperarm","bip01 l forearm","bip01 r forearm","bip01 l hand","bip01 r hand","left toe","right toe","weapon attachment"};
 static short const parents[]={-1,0,0,0,1,2,3,6,4,6,6,5,9,7,10,13,14,15,16,8,11,18};
 static float const positions[][3]={{0,0,1},{0,.13f,1},{0,-.13f,1},{0,0,1.2f},{.15f,.13f,.55f},{.15f,-.13f,.55f},{0,0,1.5f},{0,.15f,1.6f},{0,.13f,.12f},{0,0,1.65f},{0,-.15f,1.6f},{0,-.13f,.12f},{0,0,1.8f},{0,.28f,1.6f},{0,-.28f,1.6f},{.3f,.36f,1.42f},{.3f,-.36f,1.42f},{.55f,.34f,1.48f},{.55f,-.34f,1.48f},{.18f,.13f,.08f},{.18f,-.13f,.08f},{.7f,-.34f,1.48f}};
 memset(nodes,0,sizeof(nodes));memset(native,0,sizeof(native));count=22;
 for(int i=0;i<count;i++){
  strcpy(nodes[i].name,names[i]);nodes[i].parent_node_index=parents[i];native[i].scale=1;
  native[i].forward.i=native[i].left.j=native[i].up.k=1;
  memcpy(native[i].position.n,positions[i],sizeof(positions[i]));
 }
 if(digitigrade){
  strcpy(nodes[8].name,"bip01 l horselink");strcpy(nodes[11].name,"bip01 r horselink");
  native[8].position.z=native[11].position.z=.24f;
  for(int side=0;side<2;side++){
   int at=22+side,horse=side?11:8;
   nodes[at].parent_node_index=horse;strcpy(nodes[at].name,side?"bip01 r foot":"bip01 l foot");
   native[at]=native[horse];native[at].position.z=.07f;native[at].position.x=.08f;
  }
  count=24;
 }
 memset(&request,0,sizeof(request));request.forward.i=1;request.weight=1;request.phase=.35f;
}
static void unchanged_failure(void)
{
 memset(out,0x5a,sizeof(out));memcpy(saved,out,sizeof(out));
 assert(!vr_combat_pose_apply(native,nodes,count,&request,out));assert(!memcmp(out,saved,sizeof(out)));
}
static void invariant(void)
{
 for(int i=0;i<count;i++){
  int parent=nodes[i].parent_node_index;
  assert(vr_combat_pose_matrix_valid(&out[i]));assert(out[i].scale==native[i].scale);
  if(parent>=0){
   float before=vr_combat_pose_distance(&native[i].position,&native[parent].position);
   float after=vr_combat_pose_distance(&out[i].position,&out[parent].position);
   assert(fabsf(before-after)<2e-5f*(1+before));
  }
 }
 for(int i=0;i<count;i++)if(strstr(nodes[i].name,"foot")||strstr(nodes[i].name,"toe"))
  assert(!memcmp(&out[i],&native[i],sizeof(out[i])));
}
int main(void)
{
 int applied=0;
 for(int rig=0;rig<2;rig++)for(int yaw=0;yaw<2;yaw++)for(int mode=0;mode<VR_COMBAT_POSE_MODE_COUNT;mode++)
 for(int side=0;side<2;side++)for(int weight=1;weight<=5;weight++)for(int phase=1;phase<10;phase++){
  fixture(rig);request.mode=mode;request.side=side;request.weight=weight*.2f;request.phase=phase*.1f;
  if(yaw){float up[3]={0,0,1};vr_combat_pose_subtree(nodes,count,native,0,up,.7f);request.forward.i=cosf(.7f);request.forward.j=sinf(.7f);}
  assert(vr_combat_pose_apply(native,nodes,count,&request,out));invariant();applied++;
  if(mode==VR_COMBAT_POSE_CLUTCH_KNEEL)assert(out[0].position.z<native[0].position.z);
  else assert(!memcmp(&out[0],&native[0],sizeof(out[0])));
 }
 /* Weight zero never alters even an aliased input. Near-zero remains close
  * to the animated elbow/knee plane rather than snapping onto a new pole. */
 for(int mode=0;mode<VR_COMBAT_POSE_MODE_COUNT;mode++){
  fixture(0);request.mode=mode;request.weight=0;unchanged_failure();
  memcpy(saved,native,sizeof(native));assert(!vr_combat_pose_apply(native,nodes,count,&request,native));assert(!memcmp(saved,native,sizeof(native)));
  request.weight=.0001f;assert(vr_combat_pose_apply(native,nodes,count,&request,out));invariant();
  for(int i=0;i<count;i++)for(int k=0;k<13;k++)assert(fabsf(((float*)&out[i])[k]-((float*)&native[i])[k])<.0001f);
 }
 /* A bent native pose with the opposite swivel follows an arc as weight
  * changes; linear pole blending would flip abruptly around half weight. */
 for(int side=0;side<2;side++)for(int mode=VR_COMBAT_POSE_JAB;mode<=VR_COMBAT_POSE_CLUTCH_KNEEL;mode++){
  fixture(0);request.side=side;request.mode=mode;
  for(int step=1;step<=1000;step++){
   request.weight=step*.001f;assert(vr_combat_pose_apply(native,nodes,count,&request,out));
   if(step>1)for(int i=0;i<count;i++)for(int k=0;k<13;k++)assert(fabsf(((float*)&out[i])[k]-((float*)&saved[i])[k])<.025f);
   memcpy(saved,out,sizeof(out));
  }
 }
 fixture(0);request.mode=VR_COMBAT_POSE_CLUTCH_KNEEL;request.has_control_target=1;request.control_target.x=100;
 assert(vr_combat_pose_apply(native,nodes,count,&request,out));invariant();
 /* Aliasing is supported on success, too. */
 memcpy(saved,out,sizeof(out));assert(vr_combat_pose_apply(native,nodes,count,&request,native));assert(!memcmp(saved,native,count*sizeof(*native)));
 fixture(0);request.weight=NAN;unchanged_failure();request.weight=INFINITY;unchanged_failure();request.weight=1.01f;unchanged_failure();
 fixture(0);request.phase=NAN;unchanged_failure();request.phase=-.1f;unchanged_failure();request.phase=1.1f;unchanged_failure();
 fixture(0);request.side=2;unchanged_failure();request.side=-1;unchanged_failure();
 fixture(0);request.mode=VR_COMBAT_POSE_MODE_COUNT;unchanged_failure();
 for(int mode=VR_COMBAT_POSE_SWEEP;mode<=VR_COMBAT_POSE_JAB;mode++){
  fixture(0);request.mode=mode;request.phase=VR_COMBAT_POSE_CONTACT_PHASE;unchanged_failure();
  request.phase=0;unchanged_failure();request.phase=1;unchanged_failure();
 }
 fixture(0);request.forward.i=NAN;unchanged_failure();request.forward.i=0;unchanged_failure();
 fixture(0);request.has_control_target=1;request.control_target.z=NAN;unchanged_failure();
 fixture(0);native[15].position.x=NAN;unchanged_failure();
 fixture(0);native[15].forward.i=0;unchanged_failure();
 fixture(0);native[15].scale=0;unchanged_failure();
 fixture(0);native[15].position=native[13].position;unchanged_failure();
 fixture(0);native[17].position=native[15].position;unchanged_failure();
 fixture(0);nodes[0].parent_node_index=0;unchanged_failure();
 fixture(0);nodes[3].parent_node_index=4;nodes[4].parent_node_index=3;unchanged_failure();
 fixture(0);nodes[3].parent_node_index=-1;unchanged_failure();
 fixture(0);nodes[3].parent_node_index=64;unchanged_failure();
 fixture(0);memset(nodes[3].name,'x',sizeof(nodes[3].name));unchanged_failure();
 fixture(0);strcpy(nodes[3].name,"unsupported custom spine");unchanged_failure();
 fixture(0);strcpy(nodes[14].name,nodes[13].name);unchanged_failure();
 fixture(0);count=0;unchanged_failure();count=65;unchanged_failure();
 /* Grunt terminal forearms permit attacks; missing wrists reject control. */
 fixture(0);strcpy(nodes[17].name,"terminal left");strcpy(nodes[18].name,"terminal right");
 request.mode=VR_COMBAT_POSE_JAB;assert(vr_combat_pose_apply(native,nodes,count,&request,out));invariant();
 request.mode=VR_COMBAT_POSE_CLUTCH_KNEEL;unchanged_failure();
 /* Unreachable planted legs fail atomically, never slide the feet. */
 fixture(0);request.mode=VR_COMBAT_POSE_CLUTCH_KNEEL;native[8].position.x=50;unchanged_failure();
 /* Different attack modes generate distinguishable motion on both sides. */
 for(int side=0;side<2;side++){
  fixture(0);request.side=side;request.mode=VR_COMBAT_POSE_SWEEP;
  assert(vr_combat_pose_apply(native,nodes,count,&request,out));memcpy(saved,out,sizeof(out));
  request.mode=VR_COMBAT_POSE_OVERHEAD;assert(vr_combat_pose_apply(native,nodes,count,&request,out));assert(memcmp(saved,out,count*sizeof(*out)));
 }
 printf("PASS: %d combat poses + 4000 continuity samples, feet and every bone length, finite frames, aliasing and malformed-rig guards\n",applied);
 return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="test67-combat-pose-") as directory:
    work = Path(directory)
    source = work / "pose.c"
    source.write_text(SOURCE)
    executable = work / "pose"
    subprocess.run(["clang", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-I", str(ROOT),
                    str(source), "-lm", "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
