/* Optional virtual cockpit controls (IMMERSIVE VEHICLES). Included by vr_render.c after arm solvers. */
#include "render/render_debug.h"
#include "rasterizer/rasterizer.h"
#include "rasterizer/rasterizer_console_vars.h"
#include "vr_vehicle_controls_math.h"
static struct {
    long unit, vehicle; short seat; int valid, kind, generation, log_pending, down[2], steering_logged;
    double since; real local[3]; real radius;
    struct vr_wheel_grip grip[2];
    /* Test55: where each hand took hold: its phase on the Warthog's rim and
     * its forward offset (the Banshee yoke's push/pull) */
    real grip_phase[2], push_start[2];
    real_matrix4x3 root; real_point3d center, target[2];
    float angle, pitch;
} vr_wheel;
static char const *const vr_wheel_keys[]={"warthog","ghost","scorpion","banshee"};
static void vr_vehicle_handles_clear(void)
{
    for(int h=0;h<2;h++) { vr_interaction_release(h,VR_INTERACTION_VEHICLE); vr_wheel.grip[h].held=0; vr_wheel.down[h]=1; }
    vr_wheel.valid=0; vr_wheel.unit=vr_wheel.vehicle=NONE; vr_wheel.pitch=0; vr_wheel.steering_logged=0;
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
        vr_wheel.since=now;vr_wheel.angle=0;vr_wheel.pitch=0;
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
/* Test55: world-unit distance from a hand to what it can hold: anywhere on
 * the Warthog's own wheel rim, or along the outer half of a handle (a
 * handlebar sleeve, a stick, a yoke horn) */
static real vr_wheel_grip_distance(int h,real_point3d const *hand)
{
    real_vector3d d,span;
    vector_from_points3d(&vr_wheel.center,&vr_wheel.target[h],&span);
    real radius=magnitude3d(&span);
    if(vr_wheel.kind==0) {
        vector_from_points3d(&vr_wheel.center,hand,&d);
        real along=dot_product3d(&d,&vr_wheel.root.forward);
        real l=dot_product3d(&d,&vr_wheel.root.left),u=dot_product3d(&d,&vr_wheel.root.up);
        return sqrtf((sqrtf(l*l+u*u)-radius)*(sqrtf(l*l+u*u)-radius)+along*along);
    }
    {
        real_point3d a;real_vector3d ab,ap;real t,length2;
        for(int i=0;i<3;i++)a.n[i]=(vr_wheel.center.n[i]+vr_wheel.target[h].n[i])*0.5f;
        vector_from_points3d(&a,&vr_wheel.target[h],&ab);vector_from_points3d(&a,hand,&ap);
        length2=dot_product3d(&ab,&ab);
        t=length2>1e-12f?PIN(dot_product3d(&ap,&ab)/length2,0.0f,1.0f):0.0f;
        for(int k=0;k<3;k++)d.n[k]=ap.n[k]-ab.n[k]*t;
        return magnitude3d(&d);
    }
}
static int vr_vehicle_handles_update(long unit,real_vector3d *forward)
{
    real total=0,push=0;int count=0;
    double configured_contact=config_real("vr.interaction_reach");
    /* Test55: the palm's contact radius plus 4 cm: a hand on the rim or a
     * handle takes it; 10 cm away it still does not */
    real contact_radius=(real)(isfinite(configured_contact)?PIN(configured_contact,0.02,0.08):0.04)+0.04f;
    unsigned int buttons;float triggers[2],thumbs[4];
    if(!vr_controller(&buttons,triggers,thumbs)) { vr_vehicle_handles_clear(); return 0; }
    if(!vr_vehicle_handles_prepare(unit))return 0;
    if(vr_wheel.log_pending) {
        platform_log("vr: immersive %s controls anchored to native %s contacts; grip to steer, stick throttle retained, controller steering off",vr_wheel_keys[vr_wheel.kind],vr_wheel.kind==0?"wheel":"driver hand");
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
        float local[2],distance=999,ahead;
        vector_from_points3d(&vr_wheel.center,&hand,&d);local[0]=dot_product3d(&d,&vr_wheel.root.left);local[1]=dot_product3d(&d,&vr_wheel.root.up);
        ahead=dot_product3d(&d,&vr_wheel.root.forward);
        distance=vr_wheel_grip_distance(h,&hand)/vr_units_per_metre();
        if(vr_wheel.grip[h].held && vr_interaction_owner(h)!=VR_INTERACTION_VEHICLE)vr_wheel.grip[h].held=0;
        if(!vr_wheel.grip[h].held && press && isfinite(distance) &&
            distance<=contact_radius && vr_interaction_claim(h,VR_INTERACTION_VEHICLE)) {
            vr_wheel_grip_start(&vr_wheel.grip[h],local,vr_wheel.angle);
            vr_wheel.grip_phase[h]=atan2f(local[1],local[0])-vr_wheel.angle;
            vr_wheel.push_start[h]=ahead;
            vr_haptic(h,0.35f,0.035f);
        }
        if(vr_wheel.grip[h].held) {
            if(!held || distance>0.65f || release) {vr_wheel.grip[h].held=0;vr_interaction_release(h,VR_INTERACTION_VEHICLE);}
            else {total+=vr_wheel_grip_angle(&vr_wheel.grip[h],local);push+=ahead-vr_wheel.push_start[h];count++;}
        }
    }
    /* Test55: the controls own the steering while they are shown (the
     * controller's aim no longer fights them); let go, they come back to
     * centre as a sprung wheel or yoke would. */
    if(count) {
        vr_wheel.angle=total/count;
        /* Banshee: the yoke pushed forward dives, pulled back climbs (12 cm full) */
        if(vr_wheel.kind==3) {
            real travel=push/count/(0.12f*vr_units_per_metre());
            vr_wheel.pitch=-0.70f*(travel<-1?-1:travel>1?1:travel);
        }
    } else {
        vr_wheel.angle*=0.92f;
        vr_wheel.pitch*=0.92f;
    }
    if(!isfinite(vr_wheel.angle))vr_wheel.angle=0;
    if(!isfinite(vr_wheel.pitch))vr_wheel.pitch=0;
    if(vr_wheel.steering_logged!=(count?2:1)) {
        platform_log("vr: immersive %s steering from %s",vr_wheel_keys[vr_wheel.kind],count?"the gripped controls":"self-centring controls");
        vr_wheel.steering_logged=count?2:1;
    }
    /* Native driving still consumes facing, including its seat/vehicle limits. */
    real yaw=vr_yaw(&vr_wheel.root.forward)+vr_wheel.angle;
    real pitch=vr_wheel.kind==3?vr_wheel.pitch:0;
    forward->i=cosf(yaw)*cosf(pitch);forward->j=sinf(yaw)*cosf(pitch);forward->k=sinf(pitch);
    return 1;
}
/* Test55: where a hand holding the controls is drawn: on the Warthog's rim
 * where it took hold (turning with the wheel), or on its handle. */
static int vr_vehicle_handles_hand(int hand,float point[3])
{
    real_point3d at;
    if(hand<0||hand>1||!vr_wheel.valid||!vr_wheel.grip[hand].held||!point)return 0;
    if(vr_wheel.kind==0) {
        real_vector3d span;vector_from_points3d(&vr_wheel.center,&vr_wheel.target[hand],&span);
        real radius=magnitude3d(&span),phase=vr_wheel.grip_phase[hand]+vr_wheel.angle;
        at=vr_wheel_point(0,radius*cosf(phase),radius*sinf(phase));
    } else at=vr_wheel.target[hand];
    for(int i=0;i<3;i++) { if(!isfinite(at.n[i]))return 0; point[i]=at.n[i]; }
    return 1;
}
/* Low-poly, solid cockpit geometry, emitted through the engine's depth-tested
 * triangle batch; no image overlay or external assets. */
static void vr_wheel_bar(real_point3d a,real_point3d b,real width,real_argb_color color)
{
    static const int faces[6][4]={{0,1,3,2},{4,6,7,5},{0,4,5,1},{2,3,7,6},{0,2,6,4},{1,5,7,3}};
    real_point3d corners[8];real_vector3d d,side,depth;vector_from_points3d(&a,&b,&d);
    depth=vr_wheel.root.forward;
    cross_product3d(&depth,&d,&side);
    if(normalize3d(&side)==0) {
        /* a bar along the vehicle's forward axis (a column) */
        depth=vr_wheel.root.up;cross_product3d(&depth,&d,&side);if(normalize3d(&side)==0)return;
    }
    for(int vertex=0;vertex<8;vertex++) {
        corners[vertex]=(vertex&4)?b:a;
        for(int axis=0;axis<3;axis++)corners[vertex].n[axis]+=side.n[axis]*width*((vertex&2)?1:-1)+depth.n[axis]*width*((vertex&1)?1:-1);
    }
    for(int face=0;face<6;face++) {
        real_point3d q[4];
        for(int corner=0;corner<4;corner++)q[corner]=corners[faces[face][corner]];
        render_debug_polygon(q,4,&color);
    }
}
static real_point3d vr_wheel_lerp(real_point3d a,real_point3d b,real t)
{
    real_point3d p;for(int i=0;i<3;i++)p.n[i]=a.n[i]+(b.n[i]-a.n[i])*t;return p;
}
static real_point3d vr_wheel_offset(real_point3d p,real x,real z)
{
    for(int i=0;i<3;i++)p.n[i]+=vr_wheel.root.forward.n[i]*x+vr_wheel.root.up.n[i]*z;return p;
}
boolean vr_render_vehicle_controls(void)
{
    /* Test55: the pouch/holster calibration markers share this per-eye
     * depth-tested debug pass (shown only while their menu rows are) */
    float marker_points[8][3],marker_radii[8];
    int markers=VR_RENDER_EYE()?vr_calibration_markers(vr_render.game_camera_position.n,marker_points,marker_radii,8):0;
    /* Test55: the Warthog's own steering wheel is in its model: no copy */
    int controls=VR_RENDER_EYE() && vr_wheel.valid && vr_vehicle_handles_enabled(vr_wheel.unit) &&
        config_boolean("vr.vehicle_wheel_visible") && vr_wheel.kind!=0;
    if(!markers && !controls)return FALSE;
    boolean saved_debug=rasterizer_debug_options.draw_debug_geometry;
    rasterizer_debug_options.draw_debug_geometry=TRUE;
    {
        real_argb_color blue={0.35f,0.15f,0.45f,1.0f};
        for(int m=0;m<markers;m++) {
            real_point3d point;
            for(int axis=0;axis<3;axis++)point.n[axis]=marker_points[m][axis];
            render_debug_sphere(TRUE,&point,marker_radii[m],&blue);
            /* a low-poly shell (8 x 6 quads) fills the wire sphere */
            for(int ring=0;ring<6;ring++)for(int slice=0;slice<8;slice++) {
                real_point3d q[4];real_argb_color fill={0.18f,0.15f,0.45f,1.0f};
                for(int corner=0;corner<4;corner++) {
                    real a=_pi*(real)(ring+(corner==1||corner==2))/6.0f-_pi*0.5f;
                    real b=2.0f*_pi*(real)(slice+(corner>=2))/8.0f;
                    q[corner].x=point.x+marker_radii[m]*cosf(a)*cosf(b);
                    q[corner].y=point.y+marker_radii[m]*cosf(a)*sinf(b);
                    q[corner].z=point.z+marker_radii[m]*sinf(a);
                }
                render_debug_polygon(q,4,&fill);
            }
        }
    }
    if(!controls) {
        rasterizer_debug_draw();
        rasterizer_debug_options.draw_debug_geometry=saved_debug;
        return TRUE;
    }
    real units=vr_units_per_metre();
    real_argb_color metal={1,0.30f,0.32f,0.34f},dark={1,0.07f,0.07f,0.08f},trim={1,0.42f,0.30f,0.62f};
    if(vr_wheel.kind==2) {trim.red=.30f;trim.green=.36f;trim.blue=.24f;}
    if(vr_wheel.kind==3) {trim.red=.26f;trim.green=.24f;trim.blue=.58f;}
    real w=0.010f*units;
    real_point3d left=vr_wheel.target[0],right=vr_wheel.target[1];
    if(vr_wheel.kind==1) {
        /* Ghost: handlebar, rubber grip sleeves, end caps and a stem */
        vr_wheel_bar(vr_wheel_lerp(left,right,0.30f),vr_wheel_lerp(left,right,0.70f),w,metal);
        vr_wheel_bar(left,vr_wheel_lerp(left,right,0.30f),w*1.6f,dark);
        vr_wheel_bar(vr_wheel_lerp(left,right,0.70f),right,w*1.6f,dark);
        vr_wheel_bar(vr_wheel_lerp(left,right,-0.04f),left,w*2.0f,trim);
        vr_wheel_bar(right,vr_wheel_lerp(left,right,1.04f),w*2.0f,trim);
        vr_wheel_bar(vr_wheel.center,vr_wheel_offset(vr_wheel.center,0.05f*units,-0.12f*units),w*1.4f,metal);
    } else if(vr_wheel.kind==2) {
        /* Scorpion: two control sticks on bases, with knobs */
        for(int h=0;h<2;h++) {
            real_point3d top=vr_wheel.target[h],base=vr_wheel_offset(top,0.02f*units,-0.14f*units);
            vr_wheel_bar(vr_wheel_offset(base,-0.03f*units,0),vr_wheel_offset(base,0.03f*units,0),w*2.6f,dark);
            vr_wheel_bar(base,top,w*0.9f,metal);
            vr_wheel_bar(vr_wheel_offset(top,0,-0.03f*units),vr_wheel_offset(top,0,0.025f*units),w*1.9f,trim);
        }
    } else {
        /* Banshee: a yoke (crossbar, two horns) on a column toward the dash */
        real_point3d column=vr_wheel_offset(vr_wheel.center,0.16f*units,-0.04f*units);
        vr_wheel_bar(left,right,w*1.2f,metal);
        for(int h=0;h<2;h++) {
            real_point3d horn=vr_wheel.target[h];
            vr_wheel_bar(vr_wheel_offset(horn,0,-0.05f*units),vr_wheel_offset(horn,0,0.05f*units),w*1.7f,dark);
        }
        vr_wheel_bar(vr_wheel.center,column,w*1.5f,trim);
    }
    rasterizer_debug_draw();
    rasterizer_debug_options.draw_debug_geometry=saved_debug;
    return TRUE;
}
/* Test55: drivers holding immersive controls see the first-person arms and
 * hands (with finger poses) instead of the third-person body's arms, which
 * have no finger bones; the unit needs a weapon for the first-person rig. */
int vr_render_vehicle_first_person_hands(void)
{
    struct unit_datum *unit;
    if(!vr_render.stereo || vr_render.cinematic_view || !vr_wheel.valid || !vr_vehicle_handles_enabled(vr_wheel.unit) ||
       !(unit=unit_try_and_get(vr_wheel.unit)) || unit->unit.current_weapon_index==NONE)return 0;
    return unit_inventory_get_weapon(vr_wheel.unit,unit->unit.current_weapon_index)!=NONE;
}
static real_matrix4x3 *vr_vehicle_handles_body(struct animation_graph *graph,real_matrix4x3 *m,short count)
{
    int first_person_hands=vr_render_vehicle_first_person_hands();
    for(int h=0;h<2;h++) {
        short chain[3]={vr_find_node(graph,h?" r ":" l ","upperarm"),vr_find_node(graph,h?" r ":" l ","forearm"),vr_find_node(graph,h?" r ":" l ","hand")};
        real_point3d target;real_vector3d f,u,pole;
        if(chain[0]<0||chain[1]<0||chain[2]<0||chain[2]>=count||!vr_node_under(graph,chain[1],chain[0])||!vr_node_under(graph,chain[2],chain[1]))continue;
        if(first_person_hands) {
            /* the first-person arms are the hands: fold the body's away */
            for(short n=0;n<count;n++)if(vr_node_under(graph,n,chain[0])){m[n].scale=0;m[n].position=m[chain[0]].position;}
            continue;
        }
        if(vr_wheel.grip[h].held&&vr_vehicle_handles_hand(h,target.n));
        else if(!vr_hand_pose(h,vr_render.game_camera_position.n,target.n,f.n,u.n))continue;
        vector_from_points3d(&m[chain[0]].position,&m[chain[1]].position,&pole);
        vr_solve_arm(graph,m,chain,m[chain[0]].position,&target,&pole,FALSE,NULL);
    }
    short head=vr_find_node(graph,"","head");
    for(int i=0;head>=0&&i<count;i++)if(vr_node_under(graph,i,head))m[i].scale=0;
    return m;
}
