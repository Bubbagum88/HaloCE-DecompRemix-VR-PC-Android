/* Optional virtual cockpit controls. Included by vr_render.c after arm solvers. */
#include "render/render_debug.h"
#include "rasterizer/rasterizer.h"
#include "rasterizer/rasterizer_console_vars.h"
#include "vr_vehicle_controls_math.h"
static struct {
    long unit, vehicle; short seat; int valid, kind, generation, log_pending, down[2];
    double since; real local[3]; real radius;
    struct vr_wheel_grip grip[2];
    real_matrix4x3 root; real_point3d center, target[2];
    float angle;
} vr_wheel;
static char const *const vr_wheel_keys[]={"warthog","ghost","scorpion","banshee"};
static void vr_vehicle_handles_clear(void)
{
    for(int h=0;h<2;h++) { vr_interaction_release(h,VR_INTERACTION_VEHICLE); vr_wheel.grip[h].held=0; vr_wheel.down[h]=1; }
    vr_wheel.valid=0; vr_wheel.unit=vr_wheel.vehicle=NONE;
}
static int vr_vehicle_handles_enabled(long unit)
{
    return config_boolean("vr.vehicle_handles") && vr_first_person_vehicles() &&
        vr_render.seat.seated && vr_render.seat.driver && vr_render.seat.unit_index==unit &&
        !vr_render.cinematic_view;
}
static real_point3d vr_wheel_point(real x,real y,real z)
{
    real_point3d p=vr_wheel.center;
    for(int i=0;i<3;i++)p.n[i]+=vr_wheel.root.forward.n[i]*x+vr_wheel.root.left.n[i]*y+vr_wheel.root.up.n[i]*z;
    return p;
}
static int vr_vehicle_handles_prepare(long unit_index)
{
    struct unit_datum *unit=unit_try_and_get(unit_index);
    struct object_datum *vehicle;
    real_matrix4x3 *nodes;
    struct object_marker markers[2];
    char const *name; int kind=-1; double now=vr_pose_time();
    if(!vr_vehicle_handles_enabled(unit_index) || !unit || TEST_FLAG(unit->object.damage_flags,_object_dead_bit) ||
        !(vehicle=object_try_and_get(vr_render.seat.vehicle_index)) ||
        vehicle->object.node_matrices.size < (long)sizeof(real_matrix4x3) ||
        !(nodes=object_get_node_matrices(vr_render.seat.vehicle_index))) { vr_vehicle_handles_clear(); return 0; }
    name=tag_get_name(vehicle->definition_index);
    for(int k=0;k<4;k++)if(name && strstr(name,vr_wheel_keys[k]))kind=k;
    if(kind<0) { vr_vehicle_handles_clear(); return 0; }
    if(vr_wheel.unit!=unit_index || vr_wheel.vehicle!=vr_render.seat.vehicle_index ||
        vr_wheel.seat!=vr_render.seat.seat_index || vr_wheel.generation!=vr_settings_generation()) {
        vr_vehicle_handles_clear();vr_wheel.unit=unit_index;vr_wheel.vehicle=vr_render.seat.vehicle_index;
        vr_wheel.seat=vr_render.seat.seat_index;vr_wheel.kind=kind;vr_wheel.generation=vr_settings_generation();
        vr_wheel.since=now;vr_wheel.angle=0;
    }
    vr_wheel.root=nodes[0];
    for(int i=0;i<3;i++) if(!isfinite(nodes[0].position.n[i]) || !isfinite(nodes[0].forward.n[i]) ||
        !isfinite(nodes[0].left.n[i]) || !isfinite(nodes[0].up.n[i])) {vr_vehicle_handles_clear();return 0;}
    if(!vr_wheel.valid) {
        real_point3d center; real_vector3d delta;
        /* Wait for entry animation before reading authored driver contacts. */
        if(now-vr_wheel.since<0.5)return 0;
        if(kind==0) {
            if(!object_get_marker_by_name(vr_wheel.vehicle,"left hand wheel grip",&markers[0],1) ||
               !object_get_marker_by_name(vr_wheel.vehicle,"right hand wheel grip",&markers[1],1))return 0;
        } else if(!object_get_marker_by_name(unit_index,"left hand",&markers[0],1) ||
                  !object_get_marker_by_name(unit_index,"right hand",&markers[1],1))return 0;
        for(int i=0;i<3;i++)center.n[i]=(markers[0].matrix.position.n[i]+markers[1].matrix.position.n[i])*0.5f;
        vector_from_points3d(&nodes[0].position,&center,&delta);
        vr_wheel.local[0]=dot_product3d(&delta,&nodes[0].forward);
        vr_wheel.local[1]=dot_product3d(&delta,&nodes[0].left);
        vr_wheel.local[2]=dot_product3d(&delta,&nodes[0].up);
        vector_from_points3d(&markers[0].matrix.position,&markers[1].matrix.position,&delta);
        vr_wheel.radius=PIN(magnitude3d(&delta)*0.5f,0.10f*vr_units_per_metre(),0.30f*vr_units_per_metre());
        if(!isfinite(vr_wheel.local[0])||!isfinite(vr_wheel.local[1])||!isfinite(vr_wheel.local[2])||!isfinite(vr_wheel.radius))return 0;
        vr_wheel.valid=1;
        vr_wheel.log_pending=1;
    }
    {
        static char const *parts[]={"forward","left","up"};char key[80];real local[3];
        vr_wheel.center=nodes[0].position;
        for(int i=0;i<3;i++) {
            double value;snprintf(key,sizeof(key),"vr.handle_%s_%s",vr_wheel_keys[kind],parts[i]);value=config_real(key);
            local[i]=vr_wheel.local[i]+(isfinite(value)?PIN(value,-0.5,0.5):0)*vr_units_per_metre();
        }
        for(int axis=0;axis<3;axis++)vr_wheel.center.n[axis]+=nodes[0].forward.n[axis]*local[0]+nodes[0].left.n[axis]*local[1]+nodes[0].up.n[axis]*local[2];
        snprintf(key,sizeof(key),"vr.handle_%s_size",vr_wheel_keys[kind]);
        double scale=config_real(key);scale=isfinite(scale)?PIN(scale,0.5,2.0):1.0;
        for(int h=0;h<2;h++) {
            real sign=h?-1:1,angle=vr_wheel.angle;
            vr_wheel.target[h]=vr_wheel_point(0,sign*vr_wheel.radius*scale*cosf(angle),sign*vr_wheel.radius*scale*sinf(angle));
        }
    }
    return 1;
}
static int vr_vehicle_handles_update(long unit,real_vector3d *forward)
{
    real total=0;int count=0;
    double configured_contact=config_real("vr.interaction_reach");
    real contact_radius=(real)(isfinite(configured_contact)?PIN(configured_contact,0.02,0.08):0.04);
    unsigned int buttons;float triggers[2],thumbs[4];
    if(!vr_controller(&buttons,triggers,thumbs)) { vr_vehicle_handles_clear(); return 0; }
    if(!vr_vehicle_handles_prepare(unit))return 0;
    if(vr_wheel.log_pending) {
        platform_log("vr: virtual %s controls anchored to native %s contacts; grip to steer, stick throttle retained",vr_wheel_keys[vr_wheel.kind],vr_wheel.kind==0?"wheel":"driver hand");
        vr_wheel.log_pending=0;
    }
    for(int h=0;h<2;h++) {
        real_point3d hand;real_vector3d f,u,d;int press=0,release=0;
        int held=vr_interaction_grip(h,&press,&release),tracked=vr_hand_world(h,vr_render.game_camera_position.n,hand.n,f.n,u.n);
        if(!tracked) {
            vr_wheel.down[h]=1;vr_wheel.grip[h].held=0;
            vr_interaction_release(h,VR_INTERACTION_VEHICLE);continue;
        }
        /* Input ticks need their own edge history; XR frame edges can be skipped. */
        press=held&&!vr_wheel.down[h];release=!held&&vr_wheel.down[h];vr_wheel.down[h]=held;
        float local[2],distance=999;
        if(tracked) {
            vector_from_points3d(&vr_wheel.center,&hand,&d);local[0]=dot_product3d(&d,&vr_wheel.root.left);local[1]=dot_product3d(&d,&vr_wheel.root.up);
            vector_from_points3d(&vr_wheel.target[h],&hand,&d);distance=magnitude3d(&d)/vr_units_per_metre();
        } else local[0]=local[1]=0;
        if(vr_wheel.grip[h].held && vr_interaction_owner(h)!=VR_INTERACTION_VEHICLE)vr_wheel.grip[h].held=0;
        /* The virtual wheel is a target surface, so Grip acquires it only when
         * the tracked hand's contact sphere reaches the configured contact
         * radius. Keep the larger distance only as a post-grab release guard. */
        if(!vr_wheel.grip[h].held && press && tracked && isfinite(distance) &&
            distance<=contact_radius && vr_interaction_claim(h,VR_INTERACTION_VEHICLE)) {
            vr_wheel_grip_start(&vr_wheel.grip[h],local,vr_wheel.angle);vr_haptic(h,0.35f,0.035f);
        }
        if(vr_wheel.grip[h].held) {
            if(!held || !tracked || distance>0.65f || release) {vr_wheel.grip[h].held=0;vr_interaction_release(h,VR_INTERACTION_VEHICLE);}
            else {total+=vr_wheel_grip_angle(&vr_wheel.grip[h],local);count++;}
        }
    }
    if(!count)return 0;
    vr_wheel.angle=total/count;
    /* Native driving still consumes facing, including its seat/vehicle limits. */
    real yaw=vr_yaw(&vr_wheel.root.forward)+vr_wheel.angle;
    real pitch=vr_wheel.kind==3?atan2f(forward->k,sqrtf(forward->i*forward->i+forward->j*forward->j)):0;
    forward->i=cosf(yaw)*cosf(pitch);forward->j=sinf(yaw)*cosf(pitch);forward->k=sinf(pitch);
    return 1;
}
/* Low-poly, solid cockpit geometry, emitted through the engine's depth-tested
 * triangle batch; no image overlay or external assets. */
static void vr_wheel_bar(real_point3d a,real_point3d b,real width,real_argb_color color)
{
    static const int faces[6][4]={{0,1,3,2},{4,6,7,5},{0,4,5,1},{2,3,7,6},{0,2,6,4},{1,5,7,3}};
    real_point3d corners[8];real_vector3d d,side;vector_from_points3d(&a,&b,&d);
    cross_product3d(&vr_wheel.root.forward,&d,&side);if(normalize3d(&side)==0)return;
    for(int vertex=0;vertex<8;vertex++) {
        corners[vertex]=(vertex&4)?b:a;
        for(int axis=0;axis<3;axis++)corners[vertex].n[axis]+=side.n[axis]*width*((vertex&2)?1:-1)+vr_wheel.root.forward.n[axis]*width*((vertex&1)?1:-1);
    }
    for(int face=0;face<6;face++) {
        real_point3d q[4];
        for(int corner=0;corner<4;corner++)q[corner]=corners[faces[face][corner]];
        render_debug_polygon(q,4,&color);
    }
}
boolean vr_render_vehicle_controls(void)
{
    if(!VR_RENDER_EYE() || !vr_wheel.valid || !vr_vehicle_handles_enabled(vr_wheel.unit) || !config_boolean("vr.vehicle_wheel_visible"))return FALSE;
    boolean saved_debug=rasterizer_debug_options.draw_debug_geometry;
    rasterizer_debug_options.draw_debug_geometry=TRUE;
    real_argb_color color={1,0.20f,0.28f,0.20f},accent={1,0.1f,0.8f,0.9f};
    if(vr_wheel.kind==1) {color.red=.32f;color.green=.17f;color.blue=.48f;}
    if(vr_wheel.kind==3) {color.red=.22f;color.green=.20f;color.blue=.52f;}
    int segments=vr_wheel.kind==0?16:vr_wheel.kind==2?8:12;
    real radius=vr_wheel.radius, width=0.015f*vr_units_per_metre();
    /* Targets already include size; use their actual radius for matching art. */
    real_vector3d span;vector_from_points3d(&vr_wheel.center,&vr_wheel.target[0],&span);radius=magnitude3d(&span);
    for(int i=0;i<segments;i++) {
        if(vr_wheel.kind!=0 && (i==segments/4 || i==segments/4-1))continue;
        real a=2*_pi*i/segments+vr_wheel.angle,b=2*_pi*(i+1)/segments+vr_wheel.angle;
        real_point3d p=vr_wheel_point(0,radius*cosf(a),radius*sinf(a));
        real_point3d q=vr_wheel_point(0,radius*cosf(b),radius*sinf(b));
        vr_wheel_bar(p,q,width,color);
    }
    for(int h=0;h<2;h++)vr_wheel_bar(vr_wheel.center,vr_wheel.target[h],width*.7f,color);
    vr_wheel_bar(vr_wheel_point(-width, -radius*.15f,0),vr_wheel_point(-width,radius*.15f,0),width,accent);
    rasterizer_debug_draw();
    rasterizer_debug_options.draw_debug_geometry=saved_debug;
    return TRUE;
}
static real_matrix4x3 *vr_vehicle_handles_body(struct animation_graph *graph,real_matrix4x3 *m,short count)
{
    for(int h=0;h<2;h++) {
        short chain[3]={vr_find_node(graph,h?" r ":" l ","upperarm"),vr_find_node(graph,h?" r ":" l ","forearm"),vr_find_node(graph,h?" r ":" l ","hand")};
        real_point3d target;real_vector3d f,u,pole;
        if(chain[0]<0||chain[1]<0||chain[2]<0||chain[2]>=count||!vr_node_under(graph,chain[1],chain[0])||!vr_node_under(graph,chain[2],chain[1]))continue;
        if(vr_wheel.grip[h].held) target=vr_wheel.target[h];
        else if(!vr_hand_pose(h,vr_render.game_camera_position.n,target.n,f.n,u.n))continue;
        vector_from_points3d(&m[chain[0]].position,&m[chain[1]].position,&pole);
        vr_solve_arm(graph,m,chain,m[chain[0]].position,&target,&pole,FALSE,NULL);
    }
    short head=vr_find_node(graph,"","head");
    for(int i=0;head>=0&&i<count;i++)if(vr_node_under(graph,i,head))m[i].scale=0;
    return m;
}
