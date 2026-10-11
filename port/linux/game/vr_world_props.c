/* Native scenery has no item physics and cannot be cast to item_datum.
 * Only audited loose, unnamed, unanimated scenery opts into this bounded
 * authoritative OBB solver. Original map objects remain unchanged until grabbed. */
#include "cseries.h"
#include "game/game.h"
#include "items/items.h"
#include "objects/objects.h"
#include "objects/object_definitions.h"
#include "physics/physics.h"
#include "physics/collisions.h"
#include "physics/collision_features.h"
#include "physics/collision_models.h"
#include "physics/collision_model_definitions.h"
#include "physics/collision_bsp_definitions.h"
#include "network_interaction.h"
#include "vr_world_props.h"
#include "vr_prop_collision_math.h"
#include "vr_world_math.h"
#include "vr_interaction_impact.h"
#include "../src/port_config.h"
#include <string.h>
void platform_log(char const *format,...);

#define PROP_FLAGS (FLAG(_collision_test_structure_bit)|FLAG(_collision_test_objects_bit)|_collision_test_objects_all_types_flags)
#define PROP_CAPACITY 64
static struct prop_state {
    int active,asleep;
    long index,definition,touched;
    real_point3d center,half,expected;
    real_vector3d forward,up;
    real radius,swing_radius;
} props[PROP_CAPACITY];
static long prop_tick=NONE;
static struct collision_feature_list prop_features;

static int prop_name(char const *name)
{
    static char const *names[]={
        "scenery\\c_storage\\c_storage",
        "scenery\\c_storage_large\\c_storage_large",
        "scenery\\h_barricade_small\\h_barricade_small",
        "scenery\\h_barricade_large\\h_barricade_large",
        "scenery\\h_barricade_large_gap\\h_barricade_large_gap",
        "scenery\\h_barricade_small_visor\\h_barricade_small_visor",
        "scenery\\trees\\tree_leafy_fallentrunk\\tree_leafy_fallentrunk",
        "scenery\\trees\\tree_leafy_fallentrunk_short\\tree_leafy_fallentrunk_short"
    };
    if(!name)return 0;
    for(int i=0;i<NUMBEROF(names);i++)if(!strcmp(name,names[i]))return 1;
    return 0;
}
static struct object_datum *prop_get(long index)
{
    struct object_datum *o=object_try_and_get_and_verify_type(index,_object_mask_scenery);
    struct object_definition *definition;
    /* (Test55: script-named scenery too; movie stars stay stock) */
    if(!o || o->object.parent_object_index!=NONE || o->object.first_child_object_index!=NONE ||
        TEST_FLAG(o->object.flags,_object_movie_star_bit) ||
        TEST_FLAG(o->object.flags,_object_no_collisions_bit) ||
        !TEST_FLAG(o->object.flags,_object_connected_to_map_bit) || TEST_FLAG(o->object.flags,_object_outside_of_map_bit) ||
        !valid_real_vector3d_axes2(&o->object.forward,&o->object.up) ||
        !(o->object.scale>.001f && o->object.scale<100) ||
        (!prop_name(tag_get_name(o->definition_index))&&!config_boolean("vr.custom_scenery_grab")))return NULL;
    definition=object_definition_get(o->definition_index);
    if(definition->object.animation_graph.index!=NONE || definition->object.physics.index!=NONE ||
        definition->object.collision_model.index==NONE)return NULL;
    return o;
}
struct object_datum *vr_world_object_get(long index)
{
    struct item_datum *item=item_vr_grabbable(index);
    return item?(struct object_datum *)item:prop_get(index);
}
float vr_world_object_mobility(long index)
{
    struct item_datum *item=item_vr_grabbable(index);
    if(item)return object_definition_get(item->definition_index)->object.acceleration_scale;
    struct object_datum *o=prop_get(index);
    if(!o)return 0;
    /* Authored physical volume/radius determines bounded heavy-object response;
     * native scenery acceleration is zero, not a usable mass measurement. */
    real radius=o->object.bounding_sphere_radius;
    return radius>.6f?.25f:radius>.25f?.5f:.8f;
}
static void prop_root(struct object_datum *o,real_matrix4x3 *root)
{
    matrix4x3_from_point_and_vectors(root,&o->object.position,&o->object.forward,&o->object.up);
    root->scale=o->object.scale;
}
static int prop_bounds(long index,struct object_datum *o,struct prop_state *state)
{
    struct collision_model_instance instance;
    real_matrix4x3 root;real_point3d lo,hi;int found=0,budget=16384;
    if(!collision_model_instance_new(&instance,index) || instance.node_count<=0 || instance.node_count>64)return 0;
    prop_root(o,&root);
    for(short n=0;n<instance.node_count;n++) {
        struct collision_node *node=TAG_BLOCK_GET_ELEMENT(&instance.model->nodes,n,struct collision_node);
        if(node->region_index<0 || node->region_index>=MAXIMUM_REGIONS_PER_OBJECT || node->bsps.count<=0 || node->bsps.count>256)return 0;
        short permutation=instance.region_permutation_indices[node->region_index];
        if(permutation==NONE)continue;
        if(permutation<0 || permutation>=node->bsps.count)return 0;
        struct collision_bsp *bsp=TAG_BLOCK_GET_ELEMENT(&node->bsps,permutation,struct collision_bsp);
        if(bsp->vertices.count<0 || bsp->vertices.count>budget)return 0;
        budget-=bsp->vertices.count;
        for(long v=0;v<bsp->vertices.count;v++) {
            struct collision_vertex *vertex=TAG_BLOCK_GET_ELEMENT(&bsp->vertices,v,struct collision_vertex);
            real_point3d world,local;
            matrix4x3_transform_point(&instance.matrices[n],&vertex->point,&world);
            matrix4x3_inverse_transform_point(&root,&world,&local);
            if(!vr_prop_finite(local.n))return 0;
            for(int a=0;a<3;a++) {
                if(!found || local.n[a]<lo.n[a])lo.n[a]=local.n[a];
                if(!found || local.n[a]>hi.n[a])hi.n[a]=local.n[a];
            }
            found++;
        }
    }
    if(!found)return 0;
    for(int axis=0;axis<3;axis++) {
        state->center.n[axis]=(lo.n[axis]+hi.n[axis])*.5f;
        state->half.n[axis]=(hi.n[axis]-lo.n[axis])*.5f;
        if(state->half.n[axis]<.002f || state->half.n[axis]>3)return 0;
    }
    state->radius=sqrtf(vr_prop_dot(state->half.n,state->half.n))*root.scale;
    float swing[3];for(int s=0;s<3;s++)swing[s]=fabsf(state->center.n[s])+state->half.n[s];
    state->swing_radius=sqrtf(vr_prop_dot(swing,swing))*root.scale;
    return isfinite(state->radius)&&state->radius<4;
}
static struct prop_state *prop_state_for(long index)
{
    for(int i=0;i<PROP_CAPACITY;i++)if(props[i].active&&props[i].index==index)return &props[i];
    return NULL;
}
static struct prop_state *prop_activate(long index,struct object_datum *o)
{
    struct prop_state *state=prop_state_for(index);
    if(state)return state;
    for(int i=0;i<PROP_CAPACITY;i++)if(!props[i].active) {
        state=&props[i];memset(state,0,sizeof(*state));
        if(!prop_bounds(index,o,state))return NULL;
        state->active=1;state->index=index;state->definition=o->definition_index;
        state->expected=o->object.position;state->forward=o->object.forward;state->up=o->object.up;
        platform_log("VR props: activated %s object=%ld half=(%.4f %.4f %.4f)",tag_get_name(o->definition_index),index,state->half.x,state->half.y,state->half.z);
        return state;
    }
    return NULL;
}
void vr_world_object_velocity(long index,real_vector3d const *linear,real_vector3d const *angular)
{
    if(item_vr_grabbable(index)){item_vr_world_velocity(index,linear,angular);return;}
    if((game_connection()==_game_connection_local&&!config_boolean("vr.world_interaction")&&!config_boolean("vr.custom_scenery_grab")) ||
        (game_connection()!=_game_connection_local&&!network_interaction_host_ready()))return;
    struct object_datum *o=prop_get(index);struct prop_state *state;
    if(!o || !linear || !angular || !valid_real_vector3d(linear) || !valid_real_vector3d(angular) || !(state=prop_activate(index,o)))return;
    real_vector3d bounded=*linear,spin=*angular;
    if(!vr_world_limit(bounded.n,.15f)||!vr_world_limit(spin.n,.15f))return;
    o->object.translational_velocity=bounded;o->object.angular_velocity=spin;
    state->asleep=0;state->touched=game_time_get();
}
static void prop_obb(struct prop_state const *state,real_matrix4x3 const *root,real_matrix4x3 *box)
{
    *box=*root;matrix4x3_transform_point(root,&state->center,&box->position);
}
static void prop_hit_metadata(struct collision_result *hit,struct collision_feature const *feature)
{
    memset(hit,0,sizeof(*hit));hit->object_index=feature->object_index;hit->surface_index=feature->surface_index;
    hit->flags=feature->flags;hit->breakable_surface_index=feature->breakable_surface_index;hit->material_index=feature->material_index;
    hit->node_index=hit->region_index=hit->bsp_index=hit->plane_designator=hit->material_type=NONE;
}
static void prop_capsule_contact(real_matrix4x3 const *box,float const half[3],float const a[3],float const b[3],real radius,struct collision_result *hit)
{
    float low=0,high=1;
    for(int n=0;n<24;n++) {
        float left=low+(high-low)/3,right=high-(high-low)/3;
        if(vr_prop_segment_distance2(a,b,half,left)<vr_prop_segment_distance2(a,b,half,right))high=right;else low=left;
    }
    real_point3d axis,nearest,world;real_vector3d normal;
    for(int component=0;component<3;component++) {
        axis.n[component]=a[component]+(b[component]-a[component])*(low+high)*.5f;
        nearest.n[component]=PIN(axis.n[component],-half[component],half[component]);
        normal.n[component]=nearest.n[component]-axis.n[component];
    }
    /* Deep/degenerate intersections have no uniquely evidenced impact normal.
     * They block motion but must not fabricate damage from an upward normal. */
    if(normalize3d(&normal)<.00001f)return;
    matrix4x3_transform_vector(box,&normal,&hit->plane.n);normalize3d(&hit->plane.n);
    matrix4x3_transform_point(box,&axis,&world);
    for(int coordinate=0;coordinate<3;coordinate++)hit->point.n[coordinate]=world.n[coordinate]+hit->plane.n.n[coordinate]*radius;
    hit->plane.d=dot_product3d((real_vector3d const*)&hit->point,&hit->plane.n);
}
static int prop_overlap(real_matrix4x3 const *box,float const half[3],struct collision_result *hit)
{
    real skin=.0001f/box->scale;
    for(int type=0;type<NUMBER_OF_COLLISION_FEATURE_TYPES;type++)
        if(prop_features.count[type]<0||prop_features.count[type]>=MAXIMUM_COLLISION_FEATURES_PER_TEST){memset(hit,0,sizeof(*hit));hit->object_index=NONE;return 1;}
    for(int p=0;p<prop_features.count[_collision_feature_prism];p++) {
        struct collision_prism *prism=&prop_features.prisms[p];real_point3d vertices[8];
        if(prism->point_count<3||prism->point_count>8||prism->projection_axis<0||prism->projection_axis>2||prism->projection_sign>1)return 1;
        for(int v=0;v<prism->point_count;v++) {
            real_point3d world;project_point2d(&prism->points[v],&prism->plane,prism->projection_axis,prism->projection_sign,&world);
            matrix4x3_inverse_transform_point(box,&world,&vertices[v]);
        }
        for(int t=1;t+1<prism->point_count;t++) {
            float triangle[3][3];memcpy(triangle[0],vertices[0].n,12);memcpy(triangle[1],vertices[t].n,12);memcpy(triangle[2],vertices[t+1].n,12);
            if(vr_prop_triangle_overlap(half,triangle,skin)) {
                prop_hit_metadata(hit,(struct collision_feature const*)prism);hit->plane=prism->plane;
                real distance=dot_product3d((real_vector3d const*)&box->position,&hit->plane.n)-hit->plane.d;
                real length2=dot_product3d(&hit->plane.n,&hit->plane.n);
                if(length2>.00001f)for(int axis=0;axis<3;axis++)hit->point.n[axis]=box->position.n[axis]-hit->plane.n.n[axis]*distance/length2;
                else hit->plane.n=*global_zero_vector3d;
                return 1;
            }
        }
    }
    for(int s=0;s<prop_features.count[_collision_feature_sphere];s++) {
        struct collision_sphere *sphere=&prop_features.spheres[s];real_point3d point;
        matrix4x3_inverse_transform_point(box,&sphere->center,&point);
        if(vr_prop_capsule_overlap(half,point.n,point.n,sphere->radius/box->scale,skin)) {
            prop_hit_metadata(hit,(struct collision_feature const*)sphere);
            prop_capsule_contact(box,half,point.n,point.n,sphere->radius,hit);return 1;
        }
    }
    for(int c=0;c<prop_features.count[_collision_feature_cylinder];c++) {
        struct collision_cylinder *cylinder=&prop_features.cylinders[c];real_point3d start,end,world;
        matrix4x3_inverse_transform_point(box,&cylinder->base,&start);
        for(int a=0;a<3;a++)world.n[a]=cylinder->base.n[a]+cylinder->height.n[a];
        matrix4x3_inverse_transform_point(box,&world,&end);
        if(vr_prop_capsule_overlap(half,start.n,end.n,cylinder->width/box->scale,skin)) {
            prop_hit_metadata(hit,(struct collision_feature const*)cylinder);
            prop_capsule_contact(box,half,start.n,end.n,cylinder->width,hit);return 1;
        }
    }
    return 0;
}
static int prop_translation(struct prop_state const *state,real_matrix4x3 const *from,real_matrix4x3 const *to,struct collision_result *hit)
{
    real_matrix4x3 box;real_vector3d world,local;float swept[3];
    prop_obb(state,from,&box);
    for(int a=0;a<3;a++)world.n[a]=to->position.n[a]-from->position.n[a];
    matrix4x3_inverse_transform_vector(&box,&world,&local);
    for(int axis=0;axis<3;axis++){box.position.n[axis]+=world.n[axis]*.5f;swept[axis]=state->half.n[axis]+fabsf(local.n[axis])*.5f;}
    if(prop_overlap(&box,swept,hit))return 0;
    prop_obb(state,to,&box);
    return !collision_test_point(PROP_FLAGS,&box.position,state->index);
}
static void prop_step(struct prop_state *state,struct object_datum *o)
{
    real_matrix4x3 root,next,box;struct collision_result hit;real_vector3d velocity=o->object.translational_velocity;
    memset(&hit,0,sizeof(hit));hit.object_index=NONE;
    prop_root(o,&root);prop_obb(state,&root,&box);
    velocity.k-=global_gravity;
    if(!vr_world_limit(velocity.n,.15f)){state->asleep=1;return;}
    real_vector3d incoming=velocity;
    real rotation_travel=state->swing_radius*MIN(magnitude3d(&o->object.angular_velocity),.15f);
    real travel=magnitude3d(&velocity),radius=state->radius+travel+rotation_travel+.002f;
    collision_get_features_in_sphere(PROP_FLAGS,&box.position,radius,0,0,state->index,&prop_features);
    next=root;for(int a=0;a<3;a++)next.position.n[a]+=velocity.n[a];
    int blocked=0;
    if(prop_translation(state,&root,&next,&hit))root=next;
    else {
        /* Axis-separated sweeps preserve sliding without accepting a blocked diagonal. */
        for(int axis=0;axis<3;axis++) {
            next=root;next.position.n[axis]+=velocity.n[axis];
            if(prop_translation(state,&root,&next,&hit))root=next;
            else{velocity.n[axis]=0;blocked=1;}
        }
    }
    real_vector3d angular=o->object.angular_velocity;real angle=magnitude3d(&angular);
    if(isfinite(angle)&&angle>.00001f&&angle<=.15f) {
        /* A swept spherical expansion bounds every corner during rotation. */
        real_vector3d axis=angular;scale_vector3d(&axis,1/angle,&axis);
        next=root;rotate_vector_about_axis(&next.forward,&axis,sinf(angle),cosf(angle));
        rotate_vector_about_axis(&next.up,&axis,sinf(angle),cosf(angle));
        real_matrix4x3 swept_box;prop_obb(state,&next,&swept_box);
        float expanded[3];real margin=state->swing_radius*angle/root.scale;
        for(int coordinate=0;coordinate<3;coordinate++)expanded[coordinate]=state->half.n[coordinate]+margin;
        if(!prop_overlap(&swept_box,expanded,&hit))root=next;
        else{angular=*global_zero_vector3d;blocked=1;}
    }
    if(blocked) {
        hit.type=hit.object_index==NONE?_collision_result_structure:_collision_result_object;
        hit.location=o->object.location;
        hit.t=0;
        if(magnitude3d(&hit.plane.n)>.5f)vr_interaction_impact_collision(state->index,&hit,&incoming);
        velocity.i*=.85f;velocity.j*=.85f;scale_vector3d(&angular,.8f,&angular);
    }
    object_set_position(state->index,&root.position,&root.forward,&root.up);
    o->object.translational_velocity=velocity;o->object.angular_velocity=angular;
    state->expected=root.position;state->forward=root.forward;state->up=root.up;
    if(blocked&&magnitude3d(&velocity)<.0001f&&magnitude3d(&angular)<.0001f&&game_time_get()>state->touched+1)state->asleep=1;
}
void vr_world_props_tick(void)
{
    long tick=game_time_get();
    if(tick==prop_tick||game_time_get_paused())return;
    prop_tick=tick;
    if((game_connection()==_game_connection_local&&!config_boolean("vr.world_interaction")&&!config_boolean("vr.custom_scenery_grab")) ||
        (game_connection()!=_game_connection_local&&!network_interaction_host_ready())){vr_world_props_freeze();return;}
    for(int i=0;i<PROP_CAPACITY;i++)if(props[i].active) {
        struct prop_state *state=&props[i];struct object_datum *o=prop_get(state->index);
        if(!o||o->definition_index!=state->definition){state->active=0;continue;}
        real_vector3d external;vector_from_points3d(&state->expected,&o->object.position,&external);
        if(magnitude3d(&external)>.0001f||dot_product3d(&state->forward,&o->object.forward)<.9999f||dot_product3d(&state->up,&o->object.up)<.9999f){state->active=0;continue;}
        if(!state->asleep)prop_step(state,o);
    }
}
void vr_world_props_reset(void){memset(props,0,sizeof(props));prop_tick=NONE;}
void vr_world_props_freeze(void)
{
    /* Before save only: persist stable native transforms, no transient velocity
     * that restored static scenery has no native solver to consume. */
    for(int i=0;i<PROP_CAPACITY;i++)if(props[i].active) {
        struct object_datum *o=prop_get(props[i].index);
        if(o && o->definition_index==props[i].definition) {
            o->object.translational_velocity=*global_zero_vector3d;
            o->object.angular_velocity=*global_zero_vector3d;
        }
    }
    vr_world_props_reset();
}
