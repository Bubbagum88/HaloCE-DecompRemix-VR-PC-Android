"""Production scenery solver with authored-box and native-feature fixtures."""
from pathlib import Path
import re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'port/linux/game/vr_world_props.c').read_text()
s=re.sub(r'^#include[^\n]*\n','',s,flags=re.M)
stub=r'''
#include <assert.h>
#include <math.h>
#include <string.h>
#include <stdarg.h>
#include <stddef.h>
#include "port/linux/game/vr_prop_collision_math.h"
#include "port/linux/game/vr_world_math.h"
typedef float real;typedef int boolean;typedef unsigned char byte;
typedef union real_point3d{float n[3];struct{float x,y,z;};}real_point3d;
typedef union real_vector3d{float n[3];struct{float i,j,k;};}real_vector3d;
typedef struct{float n[2];}real_point2d;
typedef struct{real_vector3d n;float d;}real_plane3d;
typedef struct{float scale;real_vector3d forward,left,up;real_point3d position;}real_matrix4x3;
#define NONE (-1)
#define NULL ((void*)0)
#define NUMBEROF(a) ((int)(sizeof(a)/sizeof(*(a))))
#define FLAG(a) (1u<<(a))
#define TEST_FLAG(a,b) (!!((a)&FLAG(b)))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define PIN(a,l,h) ((a)<(l)?(l):(a)>(h)?(h):(a))
#define MAXIMUM_REGIONS_PER_OBJECT 8
#define MAXIMUM_COLLISION_FEATURES_PER_TEST 256
#define TAG_BLOCK_GET_ELEMENT(b,i,t) (&((t*)(b)->data)[i])
enum{_object_movie_star_bit,_object_no_collisions_bit,_object_connected_to_map_bit,_object_outside_of_map_bit};
enum{_object_mask_scenery=8,_game_connection_local=0,_collision_test_structure_bit=0,_collision_test_objects_bit=1,_collision_test_objects_all_types_flags=255};
enum{_collision_feature_sphere,_collision_feature_cylinder,_collision_feature_prism,NUMBER_OF_COLLISION_FEATURE_TYPES};
enum{_collision_result_structure=1,_collision_result_object=2};
struct collision_result{int type,location;float t;long object_index,surface_index;int node_index,region_index,bsp_index,plane_designator,material_type,flags,breakable_surface_index,material_index;real_point3d point;real_plane3d plane;};
struct object_datum{long definition_index;struct{long parent_object_index,first_child_object_index,name_index;int location;unsigned flags;real_point3d position;real_vector3d forward,up,translational_velocity,angular_velocity;real scale,bounding_sphere_radius;}object;};
struct item_datum{long definition_index;};
struct reference{long index;};
struct object_definition{struct{struct reference animation_graph,physics,collision_model;real acceleration_scale;}object;};
struct block{int count;void*data;};
struct collision_vertex{real_point3d point;};
struct collision_bsp{struct block vertices;};
struct collision_node{int region_index;struct block bsps;};
struct collision_model{struct block nodes;};
struct collision_model_instance{struct collision_model*model;int node_count;byte*region_permutation_indices;real_matrix4x3*matrices;};
#define FEATURE long object_index,surface_index;byte flags,breakable_surface_index;short material_index
struct collision_feature{FEATURE;};
struct collision_prism{FEATURE;real_plane3d plane;float height;int projection_axis,projection_sign,point_count;real_point2d points[8];};
struct collision_sphere{FEATURE;real_point3d center;float radius;};
struct collision_cylinder{FEATURE;real_point3d base;real_vector3d height;float width;};
struct collision_feature_list{int count[3];struct collision_sphere spheres[256];struct collision_cylinder cylinders[256];struct collision_prism prisms[256];};
static real_vector3d zero,*global_zero_vector3d=&zero;
static float global_gravity=.003f;static int tick,paused,network,host,enabled=1,custom_scenery,sets,impacts,mode;
static struct object_datum object;
static struct object_definition definition;
static char const*name="scenery\\c_storage\\c_storage";
static struct collision_vertex vertices[8];static struct collision_bsp bsp;
static struct collision_node node;static struct collision_model model;
static real_matrix4x3 model_matrix;static byte permutation[1];
static int game_time_get(void){return tick;}
static int game_time_get_paused(void){return paused;}
static int game_connection(void){return network;}
static int network_interaction_host_ready(void){return host;}
static int config_boolean(char const*k){return !strcmp(k,"vr.custom_scenery_grab")?custom_scenery:enabled;}
void platform_log(char const*f,...){(void)f;}
static char const*tag_get_name(long i){(void)i;return name;}
static struct object_definition*object_definition_get(long i){(void)i;return &definition;}
static struct item_datum*item_vr_grabbable(long i){(void)i;return NULL;}
static void item_vr_world_velocity(long i,real_vector3d const*v,real_vector3d const*a){(void)i;(void)v;(void)a;assert(0);}
static struct object_datum*object_try_and_get_and_verify_type(long i,int mask){return i==2&&mask==8?&object:NULL;}
static int valid_real_vector3d(real_vector3d const*v){return vr_prop_finite(v->n);}
static float dot_product3d(real_vector3d const*a,real_vector3d const*b){return vr_prop_dot(a->n,b->n);}
static float magnitude3d(real_vector3d const*v){return sqrtf(dot_product3d(v,v));}
static float normalize3d(real_vector3d*v){float n=magnitude3d(v);if(n>0)for(int a=0;a<3;a++)v->n[a]/=n;return n;}
static int valid_real_vector3d_axes2(real_vector3d const*a,real_vector3d const*b){return valid_real_vector3d(a)&&valid_real_vector3d(b)&&fabsf(magnitude3d(a)-1)<.01f&&fabsf(magnitude3d(b)-1)<.01f&&fabsf(dot_product3d(a,b))<.01f;}
static void scale_vector3d(real_vector3d const*a,float s,real_vector3d*b){for(int i=0;i<3;i++)b->n[i]=a->n[i]*s;}
static void vector_from_points3d(real_point3d const*a,real_point3d const*b,real_vector3d*v){for(int i=0;i<3;i++)v->n[i]=b->n[i]-a->n[i];}
static void matrix4x3_from_point_and_vectors(real_matrix4x3*m,real_point3d const*p,real_vector3d const*f,real_vector3d const*u){m->scale=1;m->position=*p;m->forward=*f;m->up=*u;vr_prop_cross(u->n,f->n,m->left.n);}
static void matrix4x3_transform_vector(real_matrix4x3 const*m,real_vector3d const*v,real_vector3d*out){real_vector3d copy=*v;for(int i=0;i<3;i++)out->n[i]=m->scale*(m->forward.n[i]*copy.i+m->left.n[i]*copy.j+m->up.n[i]*copy.k);}
static void matrix4x3_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){matrix4x3_transform_vector(m,(real_vector3d const*)p,(real_vector3d*)out);for(int i=0;i<3;i++)out->n[i]+=m->position.n[i];}
static void matrix4x3_inverse_transform_vector(real_matrix4x3 const*m,real_vector3d const*v,real_vector3d*out){real_vector3d copy=*v;out->i=dot_product3d(&copy,&m->forward)/m->scale;out->j=dot_product3d(&copy,&m->left)/m->scale;out->k=dot_product3d(&copy,&m->up)/m->scale;}
static void matrix4x3_inverse_transform_point(real_matrix4x3 const*m,real_point3d const*p,real_point3d*out){real_vector3d d;for(int i=0;i<3;i++)d.n[i]=p->n[i]-m->position.n[i];matrix4x3_inverse_transform_vector(m,&d,(real_vector3d*)out);}
static void rotate_vector_about_axis(real_vector3d*v,real_vector3d const*a,float sn,float cs){real_vector3d cross;vr_prop_cross(a->n,v->n,cross.n);float dot=dot_product3d(a,v);for(int i=0;i<3;i++)v->n[i]=v->n[i]*cs+cross.n[i]*sn+a->n[i]*dot*(1-cs);}
static int collision_model_instance_new(struct collision_model_instance*i,long index){assert(index==2);matrix4x3_from_point_and_vectors(&model_matrix,&object.object.position,&object.object.forward,&object.object.up);i->model=&model;i->node_count=1;i->matrices=&model_matrix;i->region_permutation_indices=permutation;return 1;}
static void object_set_position(long i,real_point3d const*p,real_vector3d const*f,real_vector3d const*u){assert(i==2);sets++;object.object.position=*p;object.object.forward=*f;object.object.up=*u;}
static int collision_test_point(int flags,real_point3d const*p,long ignore){(void)flags;(void)p;assert(ignore==2);return mode==4;}
static void project_point2d(real_point2d const*p,real_plane3d const*plane,int axis,int sign,real_point3d*out){(void)sign;assert(axis==2||axis==0);if(axis==2){out->x=p->n[0];out->y=p->n[1];out->z=plane->d/plane->n.k;}else{out->y=p->n[0];out->z=p->n[1];out->x=plane->d/plane->n.i;}}
static void collision_get_features_in_sphere(int flags,real_point3d const*p,float radius,float height,float width,long ignore,struct collision_feature_list*out){(void)flags;(void)p;assert(radius>0&&height==0&&width==0&&ignore==2);memset(out,0,sizeof(*out));if(mode==3){out->count[2]=256;return;}if(!mode)return;out->count[2]=mode==2?2:1;for(int i=0;i<out->count[2];i++){struct collision_prism*q=&out->prisms[i];q->object_index=NONE;q->point_count=4;q->projection_axis=i?0:2;q->plane.n.n[i?0:2]=1;q->plane.d=i?.15f:0;q->points[0]=(real_point2d){{-5,-5}};q->points[1]=(real_point2d){{5,-5}};q->points[2]=(real_point2d){{5,5}};q->points[3]=(real_point2d){{-5,5}};}}
static void vr_interaction_impact_collision(long i,struct collision_result const*h,real_vector3d const*v){assert(i==2&&magnitude3d(&h->plane.n)>.5f);(void)v;impacts++;}
void vr_world_props_freeze(void);
'''
cases=r'''
int main(void){
 (void)vr_world_authority(1,0,0);float dummy[3];assert(vr_world_spring(zero.n,zero.n,1,1,1,0,dummy));
 object.definition_index=44;object.object.parent_object_index=object.object.first_child_object_index=object.object.name_index=NONE;
 object.object.flags=FLAG(_object_connected_to_map_bit);object.object.forward.i=object.object.up.k=1;object.object.scale=1;object.object.position.z=.05f;object.object.bounding_sphere_radius=.1f;
 definition.object.animation_graph.index=definition.object.physics.index=NONE;definition.object.collision_model.index=9;
 for(int v=0;v<8;v++)for(int a=0;a<3;a++)vertices[v].point.n[a]=(v&(1<<a))?.05f:-.05f;
 bsp.vertices=(struct block){8,vertices};node.region_index=0;node.bsps=(struct block){1,&bsp};model.nodes=(struct block){1,&node};
 vr_world_props_reset();tick++;vr_world_props_tick();assert(!sets); /* OFF/unactivated baseline */
 assert(vr_world_object_get(2)==&object);
 object.object.name_index=1;assert(vr_world_object_get(2)==&object);object.object.name_index=NONE; /* Test55: script-named scenery too */
 name="scenery\\trees\\tree_stump\\tree_stump";assert(!vr_world_object_get(2));
 custom_scenery=1;assert(vr_world_object_get(2)==&object);custom_scenery=0;
 name="scenery\\c_storage\\c_storage";
 definition.object.animation_graph.index=1;assert(!vr_world_object_get(2));definition.object.animation_graph.index=NONE;
 real_vector3d velocity={.1f,0,0};mode=1;
 vr_world_object_velocity(2,&velocity,&zero);assert(props[0].active&&fabsf(props[0].half.x-.05f)<1e-6f);
 tick++;vr_world_props_tick();assert(fabsf(object.object.position.x-.1f)<1e-6f&&fabsf(object.object.position.z-.05f)<1e-6f&&impacts);
 mode=2;vr_world_object_velocity(2,&velocity,&zero);tick++;vr_world_props_tick();assert(fabsf(object.object.position.x-.1f)<1e-6f); /* cannot tunnel wall */
 enabled=0;tick++;vr_world_props_tick();assert(!props[0].active&&magnitude3d(&object.object.translational_velocity)==0);
 vr_world_object_velocity(2,&velocity,&zero);assert(!props[0].active);enabled=1;
 mode=3;vr_world_object_velocity(2,&velocity,&zero);tick++;vr_world_props_tick();assert(fabsf(object.object.position.x-.1f)<1e-6f); /* saturated list blocks */
 vr_world_props_freeze();assert(!props[0].active&&magnitude3d(&object.object.angular_velocity)==0);
 network=1;host=0;vr_world_object_velocity(2,&velocity,&zero);assert(!props[0].active);
 host=1;mode=0;vr_world_object_velocity(2,&velocity,&zero);assert(props[0].active);host=0;tick++;vr_world_props_tick();assert(!props[0].active&&magnitude3d(&object.object.translational_velocity)==0);
 network=0;host=0;vr_world_object_velocity(2,&velocity,&zero);object.object.position.x+=1;tick++;vr_world_props_tick();assert(!props[0].active); /* script relocation wins */
 vr_world_props_reset();object.object.position=(real_point3d){0,0,.5f};
 for(int v=0;v<8;v++)vertices[v].point.x+=.2f;
 vr_world_object_velocity(2,&zero,&zero);assert(props[0].swing_radius>props[0].radius+.1f);
 real_matrix4x3 box;real_point3d origin={0};matrix4x3_from_point_and_vectors(&box,&origin,&object.object.forward,&object.object.up);
 float half[3]={.05f,.05f,.05f};struct collision_result hit;
 memset(&prop_features,0,sizeof prop_features);prop_features.count[0]=1;
 prop_features.spheres[0].object_index=7;prop_features.spheres[0].center.x=.075f;prop_features.spheres[0].radius=.03f;
 assert(prop_overlap(&box,half,&hit)&&hit.object_index==7&&hit.plane.n.i<-.99f&&fabsf(hit.point.x-.045f)<1e-5f);
 prop_features.spheres[0].center.x=0;
 assert(prop_overlap(&box,half,&hit)&&magnitude3d(&hit.plane.n)==0); /* deep contact blocks, no invented damage normal */
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'props.c';exe=Path(tmp)/'props';c.write_text(stub+s+cases)
    subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-Wno-missing-braces','-Wno-macro-redefined','-fsanitize=address,undefined','-I',str(ROOT),str(c),'-lm','-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('production scenery eligibility, sweeps, collision saturation, authority and freeze passed (ASan/UBSan)')
