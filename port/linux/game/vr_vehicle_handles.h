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
    /* Test56: the controls' place in the vehicle's frame (authored contacts
     * plus the player's offsets) and size; the vehicle as last drawn
     * (vr_wheel_place); steering haptics state */
    real anchor[3], scale;
    real_matrix4x3 drawn; int drawn_valid;
    double steered; int at_limit[2]; float felt[2];
    /* Test56: the plane the controls turn in: its normal toward the driver
     * (axis, in the vehicle's frame: the Warthog's wheel leans back 10
     * degrees), and the directions across and up it */
    real axis[3]; real_vector3d normal, plane_left, plane_up;
    /* Test56: the vehicle's heading as simulated (steering is measured from
     * it, not from the drawn pose a tick behind), and the steering the
     * controls give: the driver's facing (players.c, vr_vehicle_handles_facing)
     * while aiming stays with the head */
    real_vector3d simulated_forward, steer; int steer_valid;
} vr_wheel;
static char const *const vr_wheel_keys[]={"warthog","ghost","scorpion","banshee"};
static void vr_vehicle_handles_clear(void)
{
    for(int h=0;h<2;h++) { vr_interaction_release(h,VR_INTERACTION_VEHICLE); vr_wheel.grip[h].held=0; vr_wheel.down[h]=1; }
    vr_wheel.valid=0; vr_wheel.unit=vr_wheel.vehicle=NONE; vr_wheel.pitch=0; vr_wheel.steering_logged=0;
    vr_wheel.drawn_valid=0; vr_wheel.steered=0; vr_wheel.steer_valid=0;
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
    for(int i=0;i<3;i++)p.n[i]+=vr_wheel.root.forward.n[i]*x+vr_wheel.plane_left.n[i]*y+vr_wheel.plane_up.n[i]*z;
    return p;
}
/* Test56: the controls placed on the vehicle where it is drawn. The renderer
 * draws every object between its last two ticks (render_interpolation.c), and
 * the seat's view already follows that pose (test22); the controls used the
 * latest tick's, a whole tick of travel ahead and jumping 30 times a second
 * while driving: the hands came off the Warthog's wheel and the steering,
 * measured from hands seen from the drawn seat, stuttered. While a frame is
 * drawn the blended pose is read (and kept for the input between frames,
 * whose hands are placed from that frame's camera). */
static int vr_wheel_valid_frame(real_matrix4x3 const *m)
{
    for(int i=0;i<3;i++) if(!isfinite(m->position.n[i]) || !isfinite(m->forward.n[i]) ||
        !isfinite(m->left.n[i]) || !isfinite(m->up.n[i])) return 0;
    return 1;
}
static void vr_wheel_place(real_matrix4x3 const *root)
{
    vr_wheel.root=*root;
    vr_wheel.center=root->position;
    for(int axis=0;axis<3;axis++)vr_wheel.center.n[axis]+=root->forward.n[axis]*vr_wheel.anchor[0]+root->left.n[axis]*vr_wheel.anchor[1]+root->up.n[axis]*vr_wheel.anchor[2];
    {
        real along;
        for(int n=0;n<3;n++)vr_wheel.normal.n[n]=root->forward.n[n]*vr_wheel.axis[0]+root->left.n[n]*vr_wheel.axis[1]+root->up.n[n]*vr_wheel.axis[2];
        if(!(normalize3d(&vr_wheel.normal)>0.0f)) {vr_wheel.normal=root->forward;vr_wheel.normal.i=-vr_wheel.normal.i;vr_wheel.normal.j=-vr_wheel.normal.j;vr_wheel.normal.k=-vr_wheel.normal.k;}
        along=dot_product3d(&root->left,&vr_wheel.normal);
        for(int c=0;c<3;c++)vr_wheel.plane_left.n[c]=root->left.n[c]-vr_wheel.normal.n[c]*along;
        if(!(normalize3d(&vr_wheel.plane_left)>0.0f)) vr_wheel.plane_left=root->left;
        cross_product3d(&vr_wheel.plane_left,&vr_wheel.normal,&vr_wheel.plane_up);
    }
    for(int h=0;h<2;h++) {
        real sign=h?-1:1,angle=vr_wheel.angle;
        vr_wheel.target[h]=vr_wheel_point(0,sign*vr_wheel.radius*vr_wheel.scale*cosf(angle),sign*vr_wheel.radius*vr_wheel.scale*sinf(angle));
    }
}
/* while a frame is drawn: the vehicle as drawn, kept for the input after it */
static void vr_wheel_drawn_refresh(void)
{
    real_matrix4x3 *drawn;
    if(!vr_wheel.valid) return;
    drawn=render_interpolation_object_node_matrices(vr_wheel.vehicle);
    vr_wheel.drawn_valid=drawn && vr_wheel_valid_frame(&drawn[0]);
    if(vr_wheel.drawn_valid) {vr_wheel.drawn=drawn[0];vr_wheel_place(&vr_wheel.drawn);}
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
    if(!vr_wheel_valid_frame(&nodes[0])) {vr_vehicle_handles_clear();return 0;}
    vr_wheel.simulated_forward=nodes[0].forward;
    if(!vr_wheel.valid) {
        real_point3d center; real_vector3d delta;
        /* Wait for entry animation before reading authored driver contacts. */
        if(now-vr_wheel.since<0.5)return 0;
        if(kind==0) {
            if(!object_get_marker_by_name(vr_wheel.vehicle,"left hand wheel grip",&markers[0],1) ||
               !object_get_marker_by_name(vr_wheel.vehicle,"right hand wheel grip",&markers[1],1))return 0;
        } else if(!object_get_marker_by_name(unit_index,"left hand",&markers[0],1) ||
                  !object_get_marker_by_name(unit_index,"right hand",&markers[1],1))return 0;
        real_vector3d normal={{-nodes[0].forward.i,-nodes[0].forward.j,-nodes[0].forward.k}};
        for(int i=0;i<3;i++)center.n[i]=(markers[0].matrix.position.n[i]+markers[1].matrix.position.n[i])*0.5f;
        vector_from_points3d(&markers[0].matrix.position,&markers[1].matrix.position,&delta);
        vr_wheel.radius=magnitude3d(&delta)*0.5f;
        /* Test56: the Warthog's wheel turns about its own node (the grips'
         * parent, "frame steering wheel"): its centre sits ~4 cm above the
         * grips' middle (the right hand holds lower on the rim) and its up
         * axis points back at the driver, leaning 10 degrees */
        if(kind==0 && markers[0].node_index>=0 && markers[0].node_index==markers[1].node_index &&
           vr_wheel_valid_frame(&markers[0].node_matrix)) {
            real_vector3d a,b;
            center=markers[0].node_matrix.position;normal=markers[0].node_matrix.up;
            vector_from_points3d(&center,&markers[0].matrix.position,&a);vector_from_points3d(&center,&markers[1].matrix.position,&b);
            vr_wheel.radius=(magnitude3d(&a)+magnitude3d(&b))*0.5f;
        }
        vr_wheel.radius=PIN(vr_wheel.radius,0.10f*vr_units_per_metre(),0.30f*vr_units_per_metre());
        if(!(normalize3d(&normal)>0.0f)) return 0;
        vector_from_points3d(&nodes[0].position,&center,&delta);
        vr_wheel.local[0]=dot_product3d(&delta,&nodes[0].forward);
        vr_wheel.local[1]=dot_product3d(&delta,&nodes[0].left);
        vr_wheel.local[2]=dot_product3d(&delta,&nodes[0].up);
        vr_wheel.axis[0]=dot_product3d(&normal,&nodes[0].forward);
        vr_wheel.axis[1]=dot_product3d(&normal,&nodes[0].left);
        vr_wheel.axis[2]=dot_product3d(&normal,&nodes[0].up);
        if(!isfinite(vr_wheel.local[0])||!isfinite(vr_wheel.local[1])||!isfinite(vr_wheel.local[2])||!isfinite(vr_wheel.radius)||
           !isfinite(vr_wheel.axis[0])||!isfinite(vr_wheel.axis[1])||!isfinite(vr_wheel.axis[2]))return 0;
        vr_wheel.valid=1;
        vr_wheel.log_pending=1;
    }
    {
        static char const *parts[]={"forward","left","up"};char key[80];
        for(int i=0;i<3;i++) {
            double value;snprintf(key,sizeof(key),"vr.handle_%s_%s",vr_wheel_keys[kind],parts[i]);value=config_real(key);
            vr_wheel.anchor[i]=vr_wheel.local[i]+(isfinite(value)?PIN(value,-0.5,0.5):0)*vr_units_per_metre();
        }
        snprintf(key,sizeof(key),"vr.handle_%s_size",vr_wheel_keys[kind]);
        double scale=config_real(key);vr_wheel.scale=isfinite(scale)?PIN(scale,0.5,2.0):1.0;
    }
    {
        /* the vehicle as drawn this frame (or by the last frame drawn) */
        real_matrix4x3 *drawn=render_interpolation_object_node_matrices(vr_wheel.vehicle);
        if(drawn && vr_wheel_valid_frame(&drawn[0])) {vr_wheel.drawn=drawn[0];vr_wheel.drawn_valid=1;}
        vr_wheel_place(vr_wheel.drawn_valid?&vr_wheel.drawn:&nodes[0]);
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
        real along=dot_product3d(&d,&vr_wheel.normal);
        real l=dot_product3d(&d,&vr_wheel.plane_left),u=dot_product3d(&d,&vr_wheel.plane_up);
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
    /* Test56: the Warthog's rim 2 cm more forgiving (a palm closing round a
     * tilted rim lands off its plane) */
    if(vr_wheel.kind==0) contact_radius+=0.02f;
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
        vector_from_points3d(&vr_wheel.center,&hand,&d);local[0]=dot_product3d(&d,&vr_wheel.plane_left);local[1]=dot_product3d(&d,&vr_wheel.plane_up);
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
            if(!held || distance>0.65f || release) {
                vr_wheel.grip[h].held=0;vr_interaction_release(h,VR_INTERACTION_VEHICLE);
                vr_haptic(h,0.15f,0.02f); /* Test56: let go */
            } else {
                /* Test56: each hand's turn of the controls (+ turns right):
                 * the Warthog's wheel and the Banshee's yoke turn in the
                 * driver's view (the left hand rising turns right); the
                 * Ghost's handlebar also twists (the left hand pushed
                 * forward turns right); the Scorpion's sticks steer as a
                 * tank's (left stick forward, right back turns right). */
                real twist=(ahead-vr_wheel.push_start[h])/fmaxf(vr_wheel.radius*vr_wheel.scale,0.05f*vr_units_per_metre())*(h?-1.0f:1.0f);
                real turn=vr_wheel.kind==2?vr_wheel.grip[h].base+twist:vr_wheel_grip_angle(&vr_wheel.grip[h],local);
                if(vr_wheel.kind==1)turn+=twist;
                total+=PIN(turn,-VR_WHEEL_LOCK,VR_WHEEL_LOCK);push+=ahead-vr_wheel.push_start[h];count++;
            }
        }
    }
    /* Test55: the controls own the steering while they are shown (the
     * controller's aim no longer fights them); let go, they come back to
     * centre as a sprung wheel or yoke would. Test56: by time (a sixth of a
     * second), not by frame. */
    {
        double now=vr_pose_time(),seconds=vr_wheel.steered>0?now-vr_wheel.steered:0;
        if(!(seconds>0 && seconds<0.25)) seconds=1.0/72.0;
        vr_wheel.steered=now;
        if(count) {
            vr_wheel.angle=total/count;
            /* Banshee: the yoke pushed forward dives, pulled back climbs (12 cm full) */
            if(vr_wheel.kind==3) {
                real travel=push/count/(0.12f*vr_units_per_metre());
                vr_wheel.pitch=-0.70f*(travel<-1?-1:travel>1?1:travel);
            }
        } else {
            real keep=(real)exp(-seconds/0.17);
            vr_wheel.angle*=keep;
            vr_wheel.pitch*=keep;
        }
    }
    if(!isfinite(vr_wheel.angle))vr_wheel.angle=0;
    if(!isfinite(vr_wheel.pitch))vr_wheel.pitch=0;
    /* Test56: the hands feel the steering: a light tick as the controls turn
     * (stronger toward full lock) and a firm one at the stop */
    for(int hand=0;hand<2;hand++) {
        int limit;
        if(!vr_wheel.grip[hand].held) {vr_wheel.at_limit[hand]=0;vr_wheel.felt[hand]=vr_wheel.angle;continue;}
        limit=fabsf(vr_wheel.angle)>=VR_WHEEL_LOCK-0.01f;
        if(limit && !vr_wheel.at_limit[hand]) vr_haptic(hand,0.45f,0.04f);
        else if(fabsf(vr_wheel.angle-vr_wheel.felt[hand])>=0.12f) {
            vr_haptic(hand,0.06f+0.14f*fabsf(vr_wheel.angle)/VR_WHEEL_LOCK,0.015f);
            vr_wheel.felt[hand]=vr_wheel.angle;
        }
        vr_wheel.at_limit[hand]=limit;
    }
    if(vr_wheel.steering_logged!=(count?2:1)) {
        platform_log("vr: immersive %s steering from %s",vr_wheel_keys[vr_wheel.kind],count?"the gripped controls":"self-centring controls");
        vr_wheel.steering_logged=count?2:1;
    }
    /* Native driving still consumes facing, including its seat/vehicle
     * limits. Test56: a turn right (+) is a heading to the right: the yaw
     * falls (Test55 added it, so every control steered the wrong way). A
     * degree and a half each side of centre is dead. */
    real steer=fabsf(vr_wheel.angle)<=VR_WHEEL_DEAD_ZONE?0:
        (vr_wheel.angle-copysignf(VR_WHEEL_DEAD_ZONE,vr_wheel.angle))*VR_WHEEL_LOCK/(VR_WHEEL_LOCK-VR_WHEEL_DEAD_ZONE);
    real yaw=vr_yaw(&vr_wheel.simulated_forward)-steer;
    real pitch=vr_wheel.kind==3?vr_wheel.pitch:0;
    forward->i=cosf(yaw)*cosf(pitch);forward->j=sinf(yaw)*cosf(pitch);forward->k=sinf(pitch);
    vr_wheel.steer=*forward;vr_wheel.steer_valid=1;
    return 1;
}
/* Test56: where the steering goes and where the guns aim are kept apart. The
 * engine drives a vehicle from its driver's facing and aims its guns from its
 * gunner's aiming (units.c; the Ghost's, Banshee's and Scorpion's driver is
 * their gunner too). players.c builds both from one direction; with the
 * immersive controls held this replaces only the facing, so the controls
 * steer while the guns (and the Scorpion's turret) follow the head. Only where
 * this machine runs the player's unit: an online client's vehicle steers by
 * the controls and aims with them, as in Test55. */
int vr_vehicle_steering_split(void)
{
    return game_connection()!=_game_connection_network_client;
}
void vr_vehicle_handles_facing(long unit_index,float facing[3])
{
    real_vector3d steer=vr_wheel.steer;
    if(!facing || unit_index==NONE || !vr_wheel.valid || !vr_wheel.steer_valid || vr_wheel.unit!=unit_index ||
       !vr_vehicle_steering_split() || !vr_vehicle_handles_enabled(unit_index)) return;
    if(!valid_real_vector3d(&steer) || !(normalize3d(&steer)>0.5f)) return;
    for(int axis=0;axis<3;axis++) facing[axis]=steer.n[axis];
}
/* Test55: where a hand holding the controls is drawn: on the Warthog's rim
 * where it took hold (turning with the wheel), or on its handle. */
static int vr_vehicle_handles_hand(int hand,float point[3])
{
    real_point3d at;
    if(hand<0||hand>1||!vr_wheel.valid||!vr_wheel.grip[hand].held||!point)return 0;
    vr_wheel_drawn_refresh(); /* Test56: on the wheel as drawn this frame */
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
    vr_wheel_drawn_refresh(); /* Test56: the controls on the vehicle as drawn */
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
