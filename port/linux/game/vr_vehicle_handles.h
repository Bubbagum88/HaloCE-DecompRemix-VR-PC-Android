/* Optional virtual cockpit controls (IMMERSIVE VEHICLES). Included by vr_render.c after arm solvers. */
#include "render/render_debug.h"
#include "models/models.h"
#include "models/model_definitions.h"
#include "rasterizer/rasterizer.h"
#include "rasterizer/rasterizer_console_vars.h"
#include "vr_vehicle_controls_math.h"
static struct {
    long unit, vehicle; short seat; int valid, kind, generation, log_pending, down[2], steering_logged;
    double since, settled_since; real settle_head[3]; int settle_sampled;
    real local[3]; real radius;
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
    /* Test63: the Warthog model's own "frame steering wheel" bone, drawn as
     * the virtual wheel (vr_vehicle_controls_matrices); NONE: drawn here */
    short model_wheel_node;
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
    /* Test57: where each hand took hold across the controls (the Scorpion's
     * stick tilts and the Banshee's bar slides with it), a hand within reach
     * (the controls light up), the side of centre each hand last felt */
    real side_start[2]; int near[2], side[2];
    /* Test57: the Warthog's wheel drawn (in front of the model's), or hidden
     * (on the model's own wheel exactly) */
    int wheel_front;
    /* Test57: CONTROL GLOW, STEER HAPTICS, BANSH SLIDE; Test65: GRIP GUIDE */
    int glow, steer_haptics, slide, grip_guide;
    /* Test57b: where the controls were placed and how far from the eyes */
    real head_gap; char const *anchored;
    /* Test59: the player's offsets (HOG/GHOST/TANK/BANSH REACH, LEFT,
     * HEIGHT) in the vehicle's frame; controls placed from the eyes each
     * frame (the stick, the bar, a vehicle without markers); COMFORT REACH;
     * a control found over a metre from the eyes this frame (and logged) */
    real user[3]; int head_anchored, comfort, far, far_logged;
    /* Test59: TANK DRIVE: the drive stick's push (forward +) as throttle */
    int drive; float throttle;
} vr_wheel;
static char const *const vr_wheel_keys[]={"warthog","ghost","scorpion","banshee"};
/* Test57: each vehicle's own controls. The stock Warthog gets a drawn wheel
 * over its own (Test56's grab of the model's rim never caught in the owner's
 * drive), the Ghost keeps its handlebar, the Scorpion (and a Wraith, where a
 * map lets a player drive one) a single drive stick tilted the way to go, the
 * Banshee a flight bar: rolled or slid sideways to turn, pushed or pulled to
 * dive or climb. extra: reach past HAND CONTACT, metres */
static struct {char const *name;int kind;} const vr_wheel_names[]=
    {{"warthog",0},{"ghost",1},{"scorpion",2},{"wraith",2},{"banshee",3}};
static struct {char const *control;real extra;} const vr_wheel_profiles[]=
    {{"steering wheel",0.08f},{"handlebar",0.06f},{"drive stick",0.05f},{"flight bar",0.05f}};
/* Test57: the drive stick's length and the sideways travel that is full lock
 * for the stick and the flight bar */
#define VR_STICK_LENGTH 0.16f
#define VR_BAR_SLIDE 0.12f
static void vr_vehicle_handles_clear(void)
{
    for(int h=0;h<2;h++) { vr_interaction_release(h,VR_INTERACTION_VEHICLE); vr_wheel.grip[h].held=0; vr_wheel.down[h]=1; }
    vr_wheel.valid=0; vr_wheel.unit=vr_wheel.vehicle=NONE; vr_wheel.pitch=0; vr_wheel.steering_logged=0;
    vr_wheel.drawn_valid=0; vr_wheel.steered=0; vr_wheel.steer_valid=0;
    for(int side_hand=0;side_hand<2;side_hand++) { vr_wheel.near[side_hand]=0; vr_wheel.side[side_hand]=0; }
    vr_wheel.far=vr_wheel.far_logged=0; vr_wheel.throttle=0;
}
static int vr_vehicle_handles_enabled(long unit)
{
    return config_boolean("vr.vehicle_handles") && vr_first_person_vehicles() &&
        vr_render.seat.seated && vr_render.seat.driver && vr_render.seat.unit_index==unit &&
        !vr_render.cinematic_view;
}
/* Test61: the seat's eyes held still while the immersive controls are up
 * (once the eyes settle and the controls are placed): the driver's
 * head marker leans with the steering animation and the bumps, and the eyes,
 * the hands placed from them, eased after it (vr_render.c
 * vr_seat_steady_anchor) while the controls stayed on the vehicle: turning
 * the wheel leant the driver, which moved the hands on it. The vehicle's own
 * motion is still followed whole. */
static int vr_vehicle_handles_steady(void)
{
    return vr_wheel.valid && vr_wheel.unit!=NONE && vr_wheel.vehicle==vr_render.seat.vehicle_index &&
        vr_wheel.seat==vr_render.seat.seat_index &&
        vr_vehicle_handles_enabled(vr_wheel.unit);
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
/* Test59: in front of the chest: 35 cm ahead of and 40 cm below the eyes */
#define VR_CHEST_AHEAD 0.35f
#define VR_CHEST_BELOW 0.40f
/* Test59: COMFORT REACH: no control farther than this from the eyes */
#define VR_COMFORT_REACH 0.55f
/* Test61: a control's own place farther than this from the eyes is a
 * marker gone wrong (the Scorpion's 2.2 m in Test58): in front of the chest
 * instead. Test59's metre sat on the Warthog's own wheel, 96 to 99 cm from
 * the eyes in the owner's Test60 log, so the wheel jumped between there and
 * the chest as the driver swayed. */
#define VR_FAR_REACH 1.5f
/* Test61: the controls are placed where the hands are tracked: from the
 * seat's eyes (vr_render.game_camera_position, held still while they are
 * up: vr_vehicle_handles_steady), in the hands' own level frame turned to
 * the seat's heading (vr_frame.c hand_view). Test56 to Test60 placed them on
 * the vehicle's body, which pitches and rolls under the hands (the owner's
 * Test60 video, HORIZON LEVEL: the Warthog's wheel rolled under still hands,
 * the roll read as steering and the grip slid), and the eyes they were
 * measured from swayed with the driver's steering animation. Where they sit
 * is decided once on boarding (vr_wheel.local, from the eyes, in this frame
 * then: on the vehicle's own controls at that moment), so they never jump. */
static void vr_wheel_hand_frame(real_matrix4x3 const *root,real_point3d const *head,real_matrix4x3 *frame)
{
    float heading[3],cockpit[3][3];
    *frame=*root;
    /* Test65: COCKPIT LOCK: the hands are turned by the seat's frame as the
     * vehicle is drawn (vr_frame.c); the controls are placed in the same
     * frame, so they ride the dash and stay under the hands. Measured on
     * boarding (before the lock is up), in the vehicle's own frame, which is
     * where the lock eases to: on the vehicle's own controls exactly. */
    if(vr_cockpit_frame(cockpit[0],cockpit[1],cockpit[2])) {
        for(int axis=0;axis<3;axis++) {
            frame->forward.n[axis]=cockpit[0][axis];frame->left.n[axis]=cockpit[1][axis];frame->up.n[axis]=cockpit[2][axis];
        }
        frame->position=*head;
        return;
    }
    if(config_boolean("vr.vehicle_cockpit_lock") && vr_render.seat.driver && !vr_wheel.valid) {
        real c=cosf(vr_render.seat.offset),s=sinf(vr_render.seat.offset);
        for(int axis=0;axis<3;axis++)frame->forward.n[axis]=root->forward.n[axis]*c+root->left.n[axis]*s;
        frame->up=root->up;
        cross_product3d(&frame->up,&frame->forward,&frame->left);
        if(normalize3d(&frame->left)>0.0f && normalize3d(&frame->up)>0.0f) {
            cross_product3d(&frame->left,&frame->up,&frame->forward);
            frame->position=*head;
            return;
        }
        *frame=*root;
    }
    if(vr_heading_forward(heading)) {frame->forward.i=heading[0];frame->forward.j=heading[1];}
    frame->forward.k=0.0f;
    if(!(normalize3d(&frame->forward)>0.0f)) frame->forward=root->forward;
    frame->up.i=frame->up.j=0.0f;frame->up.k=1.0f;
    cross_product3d(&frame->up,&frame->forward,&frame->left);
    if(!(normalize3d(&frame->left)>0.0f)) frame->left=root->left;
    frame->position=*head;
}
static void vr_wheel_place(real_matrix4x3 const *root)
{
    real units=vr_units_per_metre();
    real_point3d head=vr_render.game_camera_position;
    real_matrix4x3 frame;
    real offset[3];
    if(!valid_real_point3d(&head)) return;
    vr_wheel_hand_frame(root,&head,&frame);
    vr_wheel.root=frame;
    for(int part=0;part<3;part++) offset[part]=vr_wheel.local[part]+vr_wheel.user[part];
    vr_wheel.far=0;
    if(vr_wheel.head_anchored || !(sqrtf(offset[0]*offset[0]+offset[1]*offset[1]+offset[2]*offset[2])<=VR_FAR_REACH*units)) {
        vr_wheel.far=!vr_wheel.head_anchored;
        offset[0]=VR_CHEST_AHEAD*units+vr_wheel.user[0];
        offset[1]=vr_wheel.user[1];
        offset[2]=vr_wheel.user[2]-VR_CHEST_BELOW*units;
    }
    vr_wheel.center=head;
    for(int axis=0;axis<3;axis++)vr_wheel.center.n[axis]+=frame.forward.n[axis]*offset[0]+frame.left.n[axis]*offset[1]+frame.up.n[axis]*offset[2];
    {
        real along;
        for(int n=0;n<3;n++)vr_wheel.normal.n[n]=frame.forward.n[n]*vr_wheel.axis[0]+frame.left.n[n]*vr_wheel.axis[1]+frame.up.n[n]*vr_wheel.axis[2];
        if(!(normalize3d(&vr_wheel.normal)>0.0f)) {vr_wheel.normal=frame.forward;vr_wheel.normal.i=-vr_wheel.normal.i;vr_wheel.normal.j=-vr_wheel.normal.j;vr_wheel.normal.k=-vr_wheel.normal.k;}
        along=dot_product3d(&frame.left,&vr_wheel.normal);
        for(int c=0;c<3;c++)vr_wheel.plane_left.n[c]=frame.left.n[c]-vr_wheel.normal.n[c]*along;
        if(!(normalize3d(&vr_wheel.plane_left)>0.0f)) vr_wheel.plane_left=frame.left;
        cross_product3d(&vr_wheel.plane_left,&vr_wheel.normal,&vr_wheel.plane_up);
    }
    /* Test57: the Warthog's drawn wheel sits 2.5 cm in front of the model's
     * own (toward the driver), so it is seen and taken whole */
    if(vr_wheel.kind==0 && vr_wheel.wheel_front && !vr_wheel.head_anchored && !vr_wheel.far)
        for(int front=0;front<3;front++)vr_wheel.center.n[front]+=vr_wheel.normal.n[front]*0.025f*units;
    /* Test59: COMFORT REACH: past 55 cm from the eyes a control comes in
     * toward them along the same line (the Warthog's wheel ~97 cm, the
     * Ghost's bar 71 cm: arms stretched, grabs missed). A hidden Warthog
     * wheel stays on the model's wheel. */
    if(vr_wheel.comfort && !vr_wheel.head_anchored && !vr_wheel.far && !(vr_wheel.kind==0 && !vr_wheel.wheel_front)) {
        real_vector3d to;real gap;
        vector_from_points3d(&head,&vr_wheel.center,&to);
        gap=magnitude3d(&to);
        if(gap>VR_COMFORT_REACH*units)
            for(int axis=0;axis<3;axis++)vr_wheel.center.n[axis]=head.n[axis]+to.n[axis]*(VR_COMFORT_REACH*units/gap);
    }
    for(int h=0;h<2;h++) {
        real sign=h?-1:1,angle=vr_wheel.angle;
        vr_wheel.target[h]=vr_wheel_point(0,sign*vr_wheel.radius*vr_wheel.scale*cosf(angle),sign*vr_wheel.radius*vr_wheel.scale*sinf(angle));
    }
    /* Test57: the drive stick's knob, between the driver's hands, tilted
     * about its pivot below it (a turn right leans it right) */
    if(vr_wheel.kind==2) {
        real length=VR_STICK_LENGTH*vr_units_per_metre()*vr_wheel.scale;
        /* Test59: and leaning forward or back with TANK DRIVE's throttle */
        real tilt=PIN(vr_wheel.throttle,-1.0f,1.0f)*0.45f;
        vr_wheel.target[0]=vr_wheel_point(length*sinf(tilt)*cosf(vr_wheel.angle),-length*sinf(vr_wheel.angle),length*(cosf(vr_wheel.angle)*cosf(tilt)-1.0f));
        vr_wheel.target[1]=vr_wheel.target[0];
    }
}
/* the player's offsets, size and switches for this vehicle's controls */
static void vr_wheel_read_user(int kind)
{
    static char const *parts[]={"forward","left","up"};char key[80];
    if(kind<0||kind>=(int)(sizeof(vr_wheel_keys)/sizeof(vr_wheel_keys[0])))return;
    for(int i=0;i<3;i++) {
        double value;snprintf(key,sizeof(key),"vr.handle_%s_%s",vr_wheel_keys[kind],parts[i]);value=config_real(key);
        double all;
        snprintf(key,sizeof(key),"vr.handle_all_%s",parts[i]);all=config_real(key);
        value=(isfinite(value)?value:0)+(isfinite(all)?all:0);
        vr_wheel.user[i]=PIN(value,-0.5,0.5)*vr_units_per_metre();
        vr_wheel.anchor[i]=vr_wheel.local[i]+vr_wheel.user[i];
    }
    vr_wheel.comfort=config_boolean("vr.vehicle_comfort_reach");
    vr_wheel.drive=config_boolean("vr.vehicle_tank_drive");
    snprintf(key,sizeof(key),"vr.handle_%s_size",vr_wheel_keys[kind]);
    double scale=config_real(key);vr_wheel.scale=isfinite(scale)?PIN(scale,0.5,2.0):1.0;
    vr_wheel.wheel_front=config_boolean("vr.vehicle_wheel_visible");
    vr_wheel.glow=config_boolean("vr.vehicle_control_glow");
    vr_wheel.steer_haptics=config_boolean("vr.vehicle_steer_haptics");
    vr_wheel.slide=config_boolean("vr.vehicle_banshee_slide");
    vr_wheel.grip_guide=config_boolean("vr.vehicle_grip_guide");
}
/* while a frame is drawn: the vehicle as drawn, kept for the input after it */
static void vr_wheel_drawn_refresh(void)
{
    real_matrix4x3 *drawn;
    if(!vr_wheel.valid) return;
    /* Test63: while a vehicle-offset row is on screen (the game paused under
     * the menu), the offsets apply as they change: the preview shows the
     * controls exactly where the hands will take them */
    if(vr_calibration_shown(4))vr_wheel_read_user(vr_wheel.kind);
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
    for(int k=0;k<(int)(sizeof(vr_wheel_names)/sizeof(vr_wheel_names[0]));k++)
        if(name && strstr(name,vr_wheel_names[k].name))kind=vr_wheel_names[k].kind;
    if(kind<0) { vr_vehicle_handles_clear(); return 0; }
    /* Test63: an offset changed from the calibration rows moves the controls
     * (vr_wheel_read_user); it does not clear and re-measure them */
    if(vr_wheel.valid && vr_wheel.unit==unit_index && vr_wheel.vehicle==vr_render.seat.vehicle_index &&
        vr_wheel.seat==vr_render.seat.seat_index && vr_wheel.generation!=vr_settings_generation() && vr_calibration_shown(4))
        vr_wheel.generation=vr_settings_generation();
    if(vr_wheel.unit!=unit_index || vr_wheel.vehicle!=vr_render.seat.vehicle_index ||
        vr_wheel.seat!=vr_render.seat.seat_index || vr_wheel.generation!=vr_settings_generation()) {
        vr_vehicle_handles_clear();vr_wheel.unit=unit_index;vr_wheel.vehicle=vr_render.seat.vehicle_index;
        vr_wheel.seat=vr_render.seat.seat_index;vr_wheel.kind=kind;vr_wheel.generation=vr_settings_generation();
        vr_wheel.since=now;vr_wheel.settled_since=now;vr_wheel.settle_sampled=0;
        vr_wheel.angle=0;vr_wheel.pitch=0;
        {
            /* Test63: the Warthog's own wheel bone, if its model has one */
            struct object_definition *definition=object_definition_get(vehicle->definition_index);
            vr_wheel.model_wheel_node=kind==0&&definition->object.model.index!=NONE?
                model_find_node(definition->object.model.index,"frame steering wheel"):NONE;
        }
    }
    vr_wheel.root=nodes[0];
    if(!vr_wheel_valid_frame(&nodes[0])) {vr_vehicle_handles_clear();return 0;}
    vr_wheel.simulated_forward=nodes[0].forward;
    if(!vr_wheel.valid) {
        real_point3d center; real_vector3d delta;
        /* Test62: entry animations outlast a fixed half second. Measure the
         * seat eye in the vehicle frame so driving does not restart settling.
         * Require 350 ms within 1.5 cm, at least 500 ms after entry; cap at 3 s.
         * Lock the seat only when these same eyes measure the controls. */
        {
            real_vector3d relative;
            real local_eye[3], moved2=0, tolerance=.015f*vr_units_per_metre();
            if(!valid_real_point3d(&vr_render.game_camera_position)) return 0;
            vector_from_points3d(&nodes[0].position,&vr_render.game_camera_position,&relative);
            if(!(magnitude3d(&relative)<=5.0f*vr_units_per_metre())) return 0;
            local_eye[0]=dot_product3d(&relative,&nodes[0].forward);
            local_eye[1]=dot_product3d(&relative,&nodes[0].left);
            local_eye[2]=dot_product3d(&relative,&nodes[0].up);
            for(int axis=0;axis<3;axis++) {
                real movement=local_eye[axis]-vr_wheel.settle_head[axis];
                moved2+=movement*movement;
            }
            if(!vr_wheel.settle_sampled || moved2>tolerance*tolerance || now<vr_wheel.settled_since) {
                memcpy(vr_wheel.settle_head,local_eye,sizeof(local_eye));
                vr_wheel.settled_since=now;vr_wheel.settle_sampled=1;
            }
            if(now-vr_wheel.since<.5 || (now-vr_wheel.settled_since<.35 && now-vr_wheel.since<3.0)) return 0;
        }
        /* Test57b: a vehicle (or driver) without these markers still gets
         * its controls, in front of the chest (below) */
        int contacts=kind==0?
            object_get_marker_by_name(vr_wheel.vehicle,"left hand wheel grip",&markers[0],1) &&
            object_get_marker_by_name(vr_wheel.vehicle,"right hand wheel grip",&markers[1],1):
            object_get_marker_by_name(unit_index,"left hand",&markers[0],1) &&
            object_get_marker_by_name(unit_index,"right hand",&markers[1],1);
        if(!contacts) {
            markers[0].node_index=markers[1].node_index=-1;
            markers[0].matrix.position=markers[1].matrix.position=vr_render.game_camera_position;
        }
        real_vector3d normal={{-nodes[0].forward.i,-nodes[0].forward.j,-nodes[0].forward.k}};
        real units=vr_units_per_metre(),head_gap;
        long node_count=vehicle->object.node_matrices.size/(long)sizeof(real_matrix4x3);
        real_point3d head=vr_render.game_camera_position;
        char const *anchored="native contacts";
        for(int i=0;i<3;i++)center.n[i]=(markers[0].matrix.position.n[i]+markers[1].matrix.position.n[i])*0.5f;
        vector_from_points3d(&markers[0].matrix.position,&markers[1].matrix.position,&delta);
        vr_wheel.radius=magnitude3d(&delta)*0.5f;
        /* Test56: the Warthog's wheel turns about its own node (the grips'
         * parent, "frame steering wheel"): its centre sits ~4 cm above the
         * grips' middle (the right hand holds lower on the rim) and its up
         * axis points back at the driver, leaning 10 degrees. Test57b: that
         * node as it is in the world (nodes[]). Test56 and Test57 took the
         * marker's node_matrix, which is the marker's few-centimetre offset
         * from its node, not the node: the wheel sat at the map's origin,
         * 540 m from the driver in the owner's log, and never took a hand. */
        if(kind==0 && markers[0].node_index>=0 && markers[0].node_index==markers[1].node_index &&
           markers[0].node_index<node_count && vr_wheel_valid_frame(&nodes[markers[0].node_index])) {
            real_vector3d a,b;
            center=nodes[markers[0].node_index].position;normal=nodes[markers[0].node_index].up;
            vector_from_points3d(&center,&markers[0].matrix.position,&a);vector_from_points3d(&center,&markers[1].matrix.position,&b);
            vr_wheel.radius=(magnitude3d(&a)+magnitude3d(&b))*0.5f;
        }
        /* Test57b: the head (the seat's eye, where the hands are placed from)
         * must be in this vehicle: until a frame has placed it there, wait */
        vector_from_points3d(&nodes[0].position,&head,&delta);
        if(!valid_real_point3d(&head) || !(magnitude3d(&delta)<=5.0f*units)) return 0;
        /* Test57b: the Scorpion's stick and the Banshee's bar sit in front of
         * the driver's chest, 35 cm ahead of and 40 cm below the eyes (their
         * drivers' hands are inside the hull, 2 m off in the owner's log), as
         * does a control without markers. Test59: placed from the eyes each
         * frame (vr_wheel_place), not from where the eyes were at boarding;
         * any other control farther than 1.5 m from the eyes (Test61; a
         * metre before) is put there too, and past COMFORT REACH comes in
         * toward the eyes */
        vr_wheel.head_anchored=kind==2 || kind==3 || !contacts;
        if(kind!=2 && kind!=3 && !contacts)
            platform_log("vr: immersive %s %s: no authored contacts; placed in front of the chest",
                vr_wheel_keys[kind],vr_wheel_profiles[kind].control);
        {
        /* Test61: measured in the hands' frame (vr_wheel_place) */
        real_matrix4x3 hands;
        vr_wheel_hand_frame(&nodes[0],&head,&hands);
        if(vr_wheel.head_anchored) {
            for(int i=0;i<3;i++)
                center.n[i]=head.n[i]+hands.forward.n[i]*VR_CHEST_AHEAD*units-hands.up.n[i]*VR_CHEST_BELOW*units;
            normal.i=-hands.forward.i;normal.j=-hands.forward.j;normal.k=-hands.forward.k;
            if(kind!=0 || !contacts) vr_wheel.radius=(kind==0?0.17f:0.20f)*units;
            anchored="in front of the chest, from the eyes each frame";
        }
        vr_wheel.radius=PIN(vr_wheel.radius,0.10f*units,0.30f*units);
        if(!(normalize3d(&normal)>0.0f)) return 0;
        vector_from_points3d(&head,&center,&delta);
        head_gap=magnitude3d(&delta)/units;
        vr_wheel.head_gap=head_gap;vr_wheel.anchored=anchored;
        /* Test61: from the eyes, in the hands' frame as the vehicle is now
         * (on its own controls), kept there (vr_wheel_place) */
        vr_wheel.local[0]=dot_product3d(&delta,&hands.forward);
        vr_wheel.local[1]=dot_product3d(&delta,&hands.left);
        vr_wheel.local[2]=dot_product3d(&delta,&hands.up);
        vr_wheel.axis[0]=dot_product3d(&normal,&hands.forward);
        vr_wheel.axis[1]=dot_product3d(&normal,&hands.left);
        vr_wheel.axis[2]=dot_product3d(&normal,&hands.up);
        }
        if(!isfinite(vr_wheel.local[0])||!isfinite(vr_wheel.local[1])||!isfinite(vr_wheel.local[2])||!isfinite(vr_wheel.radius)||
           !isfinite(vr_wheel.axis[0])||!isfinite(vr_wheel.axis[1])||!isfinite(vr_wheel.axis[2]))return 0;
        vr_wheel.valid=1;
        vr_wheel.log_pending=1;
    }
    vr_wheel_read_user(kind);
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
        real l=dot_product3d(&d,&vr_wheel.plane_left),u=dot_product3d(&d,&vr_wheel.plane_up),out=sqrtf(l*l+u*u);
        /* Test57: anywhere on the drawn wheel's face (its spokes and rim,
         * not the hub's middle, where the turn cannot be read) */
        if(out>=0.4f*radius && out<=radius) return fabsf(along);
        return sqrtf((out-radius)*(out-radius)+along*along);
    }
    /* Test57: the drive stick, along its upper half and just over the knob */
    if(vr_wheel.kind==2) {
        real length=VR_STICK_LENGTH*vr_units_per_metre()*vr_wheel.scale,l2,t;
        real_point3d pivot=vr_wheel_point(0,0,-length);
        real_vector3d axis,ap;
        vector_from_points3d(&pivot,&vr_wheel.target[h],&axis);vector_from_points3d(&pivot,hand,&ap);
        l2=dot_product3d(&axis,&axis);
        t=l2>1e-12f?PIN(dot_product3d(&ap,&axis)/l2,0.5f,1.15f):1.0f;
        for(int k=0;k<3;k++)d.n[k]=ap.n[k]-axis.n[k]*t;
        return magnitude3d(&d);
    }
    {
        real_point3d a;real_vector3d ab,ap;real t,length2;
        for(int i=0;i<3;i++)a.n[i]=(vr_wheel.center.n[i]+vr_wheel.target[h].n[i])*0.5f;
        vector_from_points3d(&a,&vr_wheel.target[h],&ab);vector_from_points3d(&a,hand,&ap);
        length2=dot_product3d(&ab,&ab);
        /* Test59: from a quarter of the way out to just past the end (the
         * Ghost's grips were hard to take: misses of 8 to 17 cm) */
        t=length2>1e-12f?PIN(dot_product3d(&ap,&ab)/length2,-0.5f,1.15f):0.0f;
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
     * tilted rim lands off its plane). Test57: each control's own reach past
     * the palm (the Warthog's drawn wheel 4 cm more, the drive stick 1 cm
     * more; the Ghost's and Banshee's as before) */
    contact_radius+=vr_wheel_profiles[vr_wheel.kind].extra-0.04f;
    if(vr_wheel.log_pending) {
        platform_log("vr: immersive %s %s anchored at %s, %.0f cm from the eyes; grip to steer, stick throttle retained, controller steering off",vr_wheel_keys[vr_wheel.kind],vr_wheel_profiles[vr_wheel.kind].control,vr_wheel.anchored?vr_wheel.anchored:"native contacts",(double)(vr_wheel.head_gap*100.0f));
        vr_wheel.log_pending=0;
    }
    if(vr_wheel.far && !vr_wheel.far_logged) {
        platform_log("vr: immersive %s %s: its place on the vehicle is over 1.5 m from the eyes; placed in front of the chest",
            vr_wheel_keys[vr_wheel.kind],vr_wheel_profiles[vr_wheel.kind].control);
        vr_wheel.far_logged=1;
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
            /* (the drive stick's knob is the controls' centre: its turn is
             * measured from where the hand moves, not about the centre) */
            float start[2]={local[0],local[1]};
            if(vr_wheel.kind==2) {start[0]=1.0f;start[1]=0.0f;}
            vr_wheel_grip_start(&vr_wheel.grip[h],start,vr_wheel.angle);
            vr_wheel.grip_phase[h]=atan2f(local[1],local[0])-vr_wheel.angle;
            vr_wheel.push_start[h]=ahead;
            vr_wheel.side_start[h]=local[0];
            vr_haptic(h,0.35f,0.035f);
        } else if(!vr_wheel.grip[h].held && press) {
            /* Test57: a squeeze that took nothing says how far the hand was */
            platform_log("vr: immersive %s %s not taken by hand %d: %.1f cm away (reach %.1f cm)%s",
                vr_wheel_keys[vr_wheel.kind],vr_wheel_profiles[vr_wheel.kind].control,h,
                isfinite(distance)?(double)(distance*100.0f):-1.0,(double)(contact_radius*100.0f),
                isfinite(distance)&&distance<=contact_radius?"; the hand holds something else":"");
        }
        /* Test57: a free hand within reach lights the controls up */
        vr_wheel.near[h]=!vr_wheel.grip[h].held&&isfinite(distance)&&distance<=contact_radius;
        if(vr_wheel.grip[h].held) {
            if(!held || distance>0.65f || release) {
                vr_wheel.grip[h].held=0;vr_interaction_release(h,VR_INTERACTION_VEHICLE);
                vr_haptic(h,0.15f,0.02f); /* Test56: let go */
            } else {
                /* Test56: each hand's turn of the controls (+ turns right):
                 * the Warthog's wheel and the Banshee's yoke turn in the
                 * driver's view (the left hand rising turns right); the
                 * Ghost's handlebar also twists (the left hand pushed
                 * forward turns right). Test57: the drive stick tilts the
                 * way the hand moves across (right turns right); the flight
                 * bar also turns by sliding it across (12 cm is full lock). */
                real twist=(ahead-vr_wheel.push_start[h])/fmaxf(vr_wheel.radius*vr_wheel.scale,0.05f*vr_units_per_metre())*(h?-1.0f:1.0f);
                real across=local[0]-vr_wheel.side_start[h];
                real turn=vr_wheel.kind==2?vr_wheel.grip[h].base+atan2f(-across,VR_STICK_LENGTH*vr_units_per_metre()*vr_wheel.scale):
                    vr_wheel.kind==0?vr_wheel_grip_follow(&vr_wheel.grip[h],local,VR_WHEEL_TURN_LIMIT):
                    vr_wheel_grip_angle(&vr_wheel.grip[h],local);
                if(vr_wheel.kind==1)turn+=twist;
                if(vr_wheel.kind==3 && vr_wheel.slide)turn+=-across/(VR_BAR_SLIDE*vr_units_per_metre())*VR_WHEEL_LOCK;
                total+=vr_wheel.kind==0?PIN(turn,-VR_WHEEL_TURN_LIMIT,VR_WHEEL_TURN_LIMIT):PIN(turn,-VR_WHEEL_LOCK,VR_WHEEL_LOCK);push+=ahead-vr_wheel.push_start[h];count++;
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
            /* Test59: TANK DRIVE: the drive stick pushed forward drives on,
             * pulled back reverses (10 cm is full; 1.5 cm dead) */
            if(vr_wheel.kind==2) {
                real travel=push/count/(0.10f*vr_units_per_metre());
                travel=fabsf(travel)<0.15f?0.0f:(travel-copysignf(0.15f,travel))/0.85f;
                vr_wheel.throttle=vr_wheel.drive?(travel<-1?-1:travel>1?1:travel):0.0f;
            }
            /* Banshee: the yoke pushed forward dives, pulled back climbs (12 cm full) */
            if(vr_wheel.kind==3) {
                real travel=push/count/(0.12f*vr_units_per_metre());
                vr_wheel.pitch=-0.70f*(travel<-1?-1:travel>1?1:travel);
            }
        } else {
            real keep=(real)exp(-seconds/0.17);
            vr_wheel.angle*=keep;
            vr_wheel.pitch*=keep;
            vr_wheel.throttle=0.0f;
        }
    }
    if(!isfinite(vr_wheel.angle))vr_wheel.angle=0;
    if(!isfinite(vr_wheel.pitch))vr_wheel.pitch=0;
    /* Test56: the hands feel the steering: a light tick as the controls turn
     * (stronger toward full lock) and a firm one at the stop */
    real steered=PIN(vr_wheel.angle,-VR_WHEEL_LOCK,VR_WHEEL_LOCK); /* Test66: the wheel turns on past full lock */
    for(int hand=0;hand<2;hand++) {
        int limit,side=steered>VR_WHEEL_DEAD_ZONE?1:steered<-VR_WHEEL_DEAD_ZONE?-1:0;
        if(!vr_wheel.grip[hand].held || !vr_wheel.steer_haptics) {vr_wheel.at_limit[hand]=0;vr_wheel.felt[hand]=steered;vr_wheel.side[hand]=side;continue;}
        /* Test57: a soft tick crossing the centre */
        if(side && vr_wheel.side[hand] && side!=vr_wheel.side[hand]) vr_haptic(hand,0.10f,0.012f);
        if(side) vr_wheel.side[hand]=side;
        limit=fabsf(steered)>=VR_WHEEL_LOCK-0.01f;
        if(limit && !vr_wheel.at_limit[hand]) vr_haptic(hand,0.45f,0.04f);
        else if(fabsf(steered-vr_wheel.felt[hand])>=0.12f) {
            vr_haptic(hand,0.06f+0.14f*fabsf(steered)/VR_WHEEL_LOCK,0.015f);
            vr_wheel.felt[hand]=steered;
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
    real steer=fabsf(steered)<=VR_WHEEL_DEAD_ZONE?0:
        (steered-copysignf(VR_WHEEL_DEAD_ZONE,steered))*VR_WHEEL_LOCK/(VR_WHEEL_LOCK-VR_WHEEL_DEAD_ZONE);
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
/* Test57b: the immersive controls are steering and the head is aiming (the
 * mounted guns' reticle then follows the head between ticks: vr_render.c) */
static int vr_vehicle_handles_head_aims(void)
{
    return vr_wheel.valid && vr_wheel.unit!=NONE && vr_vehicle_steering_split() &&
        vr_vehicle_handles_enabled(vr_wheel.unit);
}
/* Test59: TANK DRIVE: the throttle from the drive stick while a hand holds
 * it, where it is pushed further than the thumbstick (forward and back; the
 * thumbstick's strafe untouched). Only where this machine runs the vehicle. */
void vr_vehicle_handles_throttle(long unit_index,float throttle[3])
{
    if(!throttle || unit_index==NONE || !vr_wheel.valid || vr_wheel.unit!=unit_index || vr_wheel.kind!=2 ||
       !vr_wheel.drive || !(vr_wheel.grip[0].held || vr_wheel.grip[1].held) || !isfinite(vr_wheel.throttle) ||
       !isfinite(throttle[0]) || !vr_vehicle_steering_split() || !vr_vehicle_handles_enabled(unit_index)) return;
    if(fabsf(vr_wheel.throttle)>fabsf(throttle[0])) throttle[0]=vr_wheel.throttle;
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
/* Test63: a rounded part: an eight-sided tube from a to b, each face shaded
 * by a light from above and behind the viewer, so the controls read as solid
 * shapes, not flat debug boxes */
static void vr_wheel_tube(real_point3d a,real_point3d b,real radius,real_argb_color color)
{
    real_vector3d d,u,v,ref={0,0,1},light;
    vector_from_points3d(&a,&b,&d);
    if(!(normalize3d(&d)>0.0f)||!(radius>0.0f))return;
    if(fabsf(d.k)>.9f){ref.i=1;ref.k=0;}
    cross_product3d(&d,&ref,&u);if(!(normalize3d(&u)>0.0f))return;
    cross_product3d(&d,&u,&v);
    vector_from_points3d(&a,&vr_render.game_camera_position,&light);
    if(!(normalize3d(&light)>0.0f))light=*global_up3d;
    for(int axis=0;axis<3;axis++)light.n[axis]=light.n[axis]*.55f+global_up3d->n[axis]*.8f;
    normalize3d(&light);
    for(int side=0;side<8;side++) {
        real a0=_pi*.25f*(real)side,a1=_pi*.25f*(real)(side+1),am=(a0+a1)*.5f,shade;
        real_vector3d normal;real_point3d q[4];real_argb_color c=color;
        for(int axis=0;axis<3;axis++)normal.n[axis]=u.n[axis]*cosf(am)+v.n[axis]*sinf(am);
        shade=.42f+.58f*fmaxf(0.0f,dot_product3d(&normal,&light));
        c.red*=shade;c.green*=shade;c.blue*=shade;
        for(int corner=0;corner<4;corner++) {
            real angle=(corner==1||corner==2)?a1:a0;
            real_point3d base=corner<2?a:b;
            for(int axis=0;axis<3;axis++)
                q[corner].n[axis]=base.n[axis]+(u.n[axis]*cosf(angle)+v.n[axis]*sinf(angle))*radius;
        }
        render_debug_polygon(q,4,&c);
    }
    /* end caps */
    for(int end=0;end<2;end++) {
        real_point3d cap[8];real_argb_color c=color;real shade=.42f+.58f*fmaxf(0.0f,dot_product3d(&d,&light)*(end?1:-1));
        c.red*=shade;c.green*=shade;c.blue*=shade;
        for(int side=0;side<8;side++)
            for(int axis=0;axis<3;axis++)
                cap[side].n[axis]=(end?b:a).n[axis]+(u.n[axis]*cosf(_pi*.25f*side)+v.n[axis]*sinf(_pi*.25f*side))*radius;
        render_debug_polygon(cap,8,&c);
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
    /* Test57: every vehicle's controls are drawn, the Warthog's wheel too (in
     * front of its own, which never took a hand in the owner's Test56 drive);
     * VIRTUAL WHEEL hides them */
    int controls=VR_RENDER_EYE() && vr_wheel.valid && vr_vehicle_handles_enabled(vr_wheel.unit) &&
        config_boolean("vr.vehicle_wheel_visible");
    boolean saved_debug=rasterizer_debug_options.draw_debug_geometry;
    rasterizer_debug_options.draw_debug_geometry=TRUE;
    int extras=VR_RENDER_EYE()?vr_extra_render(vr_render.game_camera_position.n):0;
    /* Test65: WEAPON PULL's glow */
    if(VR_RENDER_EYE()&&vr_weapon_pickup_render(vr_render.game_camera_position.n))extras=1;
    if(!markers && !controls && !extras){rasterizer_debug_options.draw_debug_geometry=saved_debug;return FALSE;}
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
    /* Test63: the controls redesigned after the vehicles' own (the owner:
     * "make them look intentional, game accurate"): shaded, rounded parts in
     * each vehicle's own materials (UNSC gunmetal, rubber and olive; Covenant
     * violet alloy, silver and blue lights). The Warthog's is the model's own
     * wheel (vr_vehicle_controls_matrices); drawn here only for a model
     * without a wheel bone. A preview (calibration rows on screen) is blue. */
    int preview=vr_calibration_shown(4);
    int lit=(vr_wheel.near[0]||vr_wheel.near[1]) && vr_wheel.glow;
    real_argb_color gunmetal={1,.30f,.32f,.34f},rubber={1,.09f,.09f,.10f},olive={1,.33f,.38f,.24f},
        violet={1,.34f,.17f,.52f},silver={1,.62f,.64f,.70f},cov_light={1,.35f,.62f,1.0f},
        red={1,.75f,.12f,.10f};
    if(lit) {
        olive.red=fminf(1,olive.red*1.8f);olive.green=fminf(1,olive.green*1.8f);olive.blue=fminf(1,olive.blue*1.8f);
        violet.red=fminf(1,violet.red*1.6f);violet.green=fminf(1,violet.green*1.6f);violet.blue=fminf(1,violet.blue*1.6f);
        cov_light.red=.6f;cov_light.green=.85f;cov_light.blue=1;rubber.red=rubber.green=rubber.blue=.20f;
    }
    if(preview) {
        real_argb_color blue={.45f,.25f,.55f,1};
        gunmetal=rubber=olive=violet=silver=cov_light=red=blue;
    }
    real m=0.001f*units*vr_wheel.scale; /* a millimetre, scaled with the controls */
    real_point3d left=vr_wheel.target[0],right=vr_wheel.target[1];
    if(vr_wheel.kind==0 && (vr_wheel.model_wheel_node==NONE || preview || !vr_wheel.wheel_front)) {
        /* Warthog, drawn (no wheel bone, or the preview): a padded rubber rim
         * with the hand grips at nine and three, three gunmetal spokes in a Y
         * to a hub with an olive cap, an olive mark at twelve */
        real r=vr_wheel.radius*vr_wheel.scale;
        if(!preview && !vr_wheel.wheel_front) goto controls_done;
        for(int segment=0;segment<28;segment++) {
            real a0=2.0f*_pi*(real)segment/28.0f,a1=2.0f*_pi*(real)(segment+1)/28.0f;
            real mid=atan2f(sinf((a0+a1)*.5f-vr_wheel.angle),cosf((a0+a1)*.5f-vr_wheel.angle));
            int grip=fabsf(fabsf(mid)-.5f*_pi)>1.15f; /* within ~25 degrees of nine and three */
            vr_wheel_tube(vr_wheel_point(0,r*cosf(a0),r*sinf(a0)),vr_wheel_point(0,r*cosf(a1),r*sinf(a1)),
                (grip?15.0f:12.0f)*m,grip?rubber:gunmetal);
        }
        {
            real top=vr_wheel.angle+0.5f*_pi;
            vr_wheel_tube(vr_wheel_point(0,r*cosf(top-0.09f),r*sinf(top-0.09f)),vr_wheel_point(0,r*cosf(top+0.09f),r*sinf(top+0.09f)),16.0f*m,olive);
        }
        for(int spoke=0;spoke<3;spoke++) {
            real phase=vr_wheel.angle+(spoke==0?-0.5f*_pi:spoke==1?0.25f*_pi:0.75f*_pi);
            vr_wheel_tube(vr_wheel_point(0,r*0.18f*cosf(phase),r*0.18f*sinf(phase)),
                vr_wheel_point(0,r*0.93f*cosf(phase),r*0.93f*sinf(phase)),7.0f*m,gunmetal);
        }
        {
            real_point3d hub_front=vr_wheel.center,hub_back=vr_wheel.center;
            for(int axis=0;axis<3;axis++) {
                hub_front.n[axis]+=vr_wheel.normal.n[axis]*14.0f*m;
                hub_back.n[axis]-=vr_wheel.normal.n[axis]*40.0f*m;
            }
            vr_wheel_tube(hub_back,vr_wheel.center,22.0f*m,gunmetal);
            vr_wheel_tube(vr_wheel.center,hub_front,30.0f*m,olive);
        }
    } else if(vr_wheel.kind==0) {
        /* Test65: the Warthog's own wheel (the model's bone, moved and turned
         * by vr_vehicle_controls_matrices) is the control: nothing is drawn
         * over it. Test63 fell through to the Banshee's flight yoke below, a
         * violet bar with blue tips across the Warthog's grips (the owner's
         * Test64 video: "that weird purple part"). GRIP GUIDE (off by
         * default) marks where the hands take the rim instead: a short
         * rubber pad at each grip, turning with the wheel. */
        if(vr_wheel.grip_guide) {
            real r=vr_wheel.radius*vr_wheel.scale;
            for(int h=0;h<2;h++) {
                real centre=vr_wheel.angle+(h?_pi:0.0f);
                for(int segment=0;segment<3;segment++) {
                    real a0=centre-0.21f+0.14f*(real)segment,a1=a0+0.14f;
                    vr_wheel_tube(vr_wheel_point(0,r*cosf(a0),r*sinf(a0)),vr_wheel_point(0,r*cosf(a1),r*sinf(a1)),
                        17.0f*m,lit?olive:rubber);
                }
            }
        }
    } else if(vr_wheel.kind==2) {
        /* Scorpion (a Wraith too): a UNSC drive stick: a gunmetal base with a
         * rubber gaiter, a shaft to a contoured grip with finger ridges, a
         * red thumb button and an olive collar */
        real length=VR_STICK_LENGTH*units*vr_wheel.scale;
        real_point3d pivot=vr_wheel_point(0,0,-length),knob=vr_wheel.target[0];
        real_point3d base_a=vr_wheel_point(0,0,-length-12.0f*m),base_b=vr_wheel_point(0,0,-length+6.0f*m);
        vr_wheel_tube(base_a,base_b,45.0f*m,gunmetal);
        for(int ring=0;ring<3;ring++)
            vr_wheel_tube(vr_wheel_lerp(pivot,knob,.04f+.07f*ring),vr_wheel_lerp(pivot,knob,.08f+.07f*ring),(28.0f-6.0f*ring)*m,rubber);
        vr_wheel_tube(pivot,vr_wheel_lerp(pivot,knob,.62f),9.0f*m,gunmetal);
        vr_wheel_tube(vr_wheel_lerp(pivot,knob,.58f),vr_wheel_lerp(pivot,knob,.64f),15.0f*m,olive);
        for(int ridge=0;ridge<4;ridge++)
            vr_wheel_tube(vr_wheel_lerp(pivot,knob,.64f+.09f*ridge),vr_wheel_lerp(pivot,knob,.69f+.09f*ridge),(ridge&1?19.0f:21.0f)*m,rubber);
        vr_wheel_tube(vr_wheel_lerp(pivot,knob,.99f),vr_wheel_lerp(pivot,knob,1.06f),16.0f*m,gunmetal);
        vr_wheel_tube(vr_wheel_lerp(pivot,knob,1.05f),vr_wheel_lerp(pivot,knob,1.09f),7.0f*m,red);
    } else if(vr_wheel.kind==1) {
        /* Ghost: a Covenant handlebar: a violet alloy bar arched toward the
         * rider, silver collars, dark grips, rounded end pods with blue
         * lights, and a violet stem to the hull */
        real_point3d centre=vr_wheel_lerp(left,right,.5f),raised=centre;
        for(int axis=0;axis<3;axis++)raised.n[axis]+=vr_wheel.normal.n[axis]*25.0f*m+vr_wheel.plane_up.n[axis]*12.0f*m;
        vr_wheel_tube(vr_wheel_lerp(left,right,.28f),raised,13.0f*m,violet);
        vr_wheel_tube(raised,vr_wheel_lerp(left,right,.72f),13.0f*m,violet);
        vr_wheel_tube(vr_wheel_lerp(left,right,.24f),vr_wheel_lerp(left,right,.30f),17.0f*m,silver);
        vr_wheel_tube(vr_wheel_lerp(left,right,.70f),vr_wheel_lerp(left,right,.76f),17.0f*m,silver);
        vr_wheel_tube(vr_wheel_lerp(left,right,.02f),vr_wheel_lerp(left,right,.25f),16.0f*m,rubber);
        vr_wheel_tube(vr_wheel_lerp(left,right,.75f),vr_wheel_lerp(left,right,.98f),16.0f*m,rubber);
        vr_wheel_tube(vr_wheel_lerp(left,right,-.06f),vr_wheel_lerp(left,right,.03f),23.0f*m,violet);
        vr_wheel_tube(vr_wheel_lerp(left,right,.97f),vr_wheel_lerp(left,right,1.06f),23.0f*m,violet);
        vr_wheel_tube(vr_wheel_lerp(left,right,-.075f),vr_wheel_lerp(left,right,-.06f),12.0f*m,cov_light);
        vr_wheel_tube(vr_wheel_lerp(left,right,1.06f),vr_wheel_lerp(left,right,1.075f),12.0f*m,cov_light);
        vr_wheel_tube(raised,vr_wheel_offset(vr_wheel.center,0.06f*units,-0.12f*units),15.0f*m,violet);
    } else {
        /* Banshee: a Covenant flight yoke: a curved violet crossbar, two
         * upright grips in silver cuffs with blue lights at their tips, and
         * a violet column toward the dash */
        real_point3d column=vr_wheel_offset(vr_wheel.center,0.16f*units,-0.04f*units);
        real_point3d centre=vr_wheel_lerp(left,right,.5f),bowed=centre;
        for(int axis=0;axis<3;axis++)bowed.n[axis]-=vr_wheel.root.forward.n[axis]*20.0f*m;
        vr_wheel_tube(left,bowed,12.0f*m,violet);
        vr_wheel_tube(bowed,right,12.0f*m,violet);
        for(int h=0;h<2;h++) {
            real_point3d horn=vr_wheel.target[h];
            vr_wheel_tube(vr_wheel_offset(horn,0,-0.06f*units),vr_wheel_offset(horn,0,0.05f*units),15.0f*m,rubber);
            vr_wheel_tube(vr_wheel_offset(horn,0,-0.07f*units),vr_wheel_offset(horn,0,-0.05f*units),19.0f*m,silver);
            vr_wheel_tube(vr_wheel_offset(horn,0,0.05f*units),vr_wheel_offset(horn,0,0.065f*units),12.0f*m,cov_light);
        }
        vr_wheel_tube(bowed,column,16.0f*m,violet);
    }
controls_done:
    /* Test63: the calibration preview: where each hand takes hold (the
     * reach the grab uses) and which way the controls face */
    if(preview) {
        real_argb_color ring={.35f,.4f,.7f,1},axis_color={.9f,.9f,.95f,1};
        real reach=(vr_wheel_profiles[vr_wheel.kind].extra+0.04f)*units;
        for(int h=0;h<(vr_wheel.kind==2?1:2);h++)render_debug_sphere(TRUE,&vr_wheel.target[h],reach,&ring);
        {
            real_point3d tip=vr_wheel.center,top=vr_wheel.center;
            for(int axis=0;axis<3;axis++) {
                tip.n[axis]+=vr_wheel.normal.n[axis]*0.10f*units;
                top.n[axis]+=vr_wheel.plane_up.n[axis]*0.10f*units;
            }
            vr_wheel_tube(vr_wheel.center,tip,3.0f*m,axis_color);
            vr_wheel_tube(vr_wheel.center,top,3.0f*m,axis_color);
        }
    }
    rasterizer_debug_draw();
    rasterizer_debug_options.draw_debug_geometry=saved_debug;
    return TRUE;
}
/* Test63: the Warthog's virtual wheel is its own: the model's "frame steering
 * wheel" bone, drawn where the virtual wheel is (COMFORT REACH, offsets,
 * size) and turned by the hands, instead of a drawn copy beside it. Its rest
 * pose on the hull (the model's default) is turned about the wheel's axis by
 * the hands' angle; the native steering animation is replaced, not added.
 * Only the seated driver's Warthog, with VIRTUAL WHEEL visible: hidden, the
 * hands take the model's wheel where it is, as before. */
real_matrix4x3 *vr_vehicle_controls_matrices(long object_index,real_matrix4x3 *stock)
{
    static real_matrix4x3 pose[MAXIMUM_NODES_PER_MODEL],defaults[MAXIMUM_NODES_PER_MODEL];
    struct object_datum *object;struct object_definition *definition;struct model *model;
    real_matrix4x3 inverse,relative,rest,target,delta;
    real_vector3d k,*axes[3];short wheel=vr_wheel.model_wheel_node,count;
    real_point3d origin={0,0,0};real_vector3d forward={1,0,0},up={0,0,1};
    if(!stock||!vr_render.stereo||!vr_wheel.valid||vr_wheel.kind!=0||object_index!=vr_wheel.vehicle||
        !vr_wheel.wheel_front||wheel==NONE||vr_calibration_shown(4)||!vr_vehicle_handles_enabled(vr_wheel.unit)||
        !(object=object_try_and_get(object_index)))return stock;
    definition=object_definition_get(object->definition_index);
    if(definition->object.model.index==NONE)return stock;
    model=model_definition_get(definition->object.model.index);
    count=(short)(object->object.node_matrices.size/sizeof(*stock));
    if(count<=0||count>MAXIMUM_NODES_PER_MODEL||model->nodes.count!=count||wheel<=0||wheel>=count)return stock;
    model_get_node_matrices(model,defaults,&origin,&forward,&up);
    matrix4x3_inverse(&defaults[0],&inverse);matrix4x3_multiply(&inverse,&defaults[wheel],&relative);
    matrix4x3_multiply(&stock[0],&relative,&rest);
    target=rest;
    cross_product3d(&vr_wheel.plane_left,&vr_wheel.plane_up,&k);
    if(!(normalize3d(&k)>0.0f))return stock;
    axes[0]=&target.forward;axes[1]=&target.left;axes[2]=&target.up;
    {
        real c=cosf(vr_wheel.angle),s=sinf(vr_wheel.angle);
        for(int v=0;v<3;v++) {
            real_vector3d original=*axes[v],cross;real dot=dot_product3d(&k,&original);
            cross_product3d(&k,&original,&cross);
            for(int axis=0;axis<3;axis++)axes[v]->n[axis]=original.n[axis]*c+cross.n[axis]*s+k.n[axis]*dot*(1-c);
        }
    }
    target.position=vr_wheel.center;target.scale=rest.scale*vr_wheel.scale;
    if(!vr_wheel_valid_frame(&target))return stock;
    matrix4x3_inverse(&stock[wheel],&inverse);matrix4x3_multiply(&target,&inverse,&delta);
    memcpy(pose,stock,count*sizeof(*pose));
    for(short n=0;n<count;n++) {
        short parent=n,steps=0;
        while(parent!=wheel&&parent>=0&&steps++<count)
            parent=TAG_BLOCK_GET_ELEMENT(&model->nodes,parent,struct model_node)->parent_node_index;
        if(parent==wheel)matrix4x3_multiply(&delta,&stock[n],&pose[n]);
    }
    return pose;
}
/* Test55: drivers holding immersive controls see the first-person arms and
 * hands (with finger poses) instead of the third-person body's arms, which
 * have no finger bones; the unit needs a weapon for the first-person rig. */
/* Test59: the first-person arms come with a weapon (its first-person
 * animations and the hands model), and a driver's weapon is stowed
 * (current_weapon_index NONE, the owner's log: "active_weapon=-1"): Test55's
 * check never passed, so the body's fingerless hands held the controls, moved
 * by the driver's steering animation (the free hand turned with the wheel).
 * While the immersive controls steer, the weapon carried lends its
 * first-person rig (first_person_weapons.c), the gun hidden
 * (vr_render_first_person_gun_hidden): tracked arms and fingers, gripping the
 * controls they hold. The body's arms fold only once that rig is loaded. */
long first_person_weapon_vr_weapon(short local_player_index);
long vr_render_vehicle_hands_weapon(long unit_index)
{
    if(unit_index==NONE || !vr_wheel.valid || vr_wheel.unit!=unit_index || !vr_vehicle_handles_enabled(unit_index) ||
       !unit_try_and_get(unit_index)) return NONE;
    for(short slot=0;slot<MAXIMUM_WEAPONS_PER_UNIT;slot++) {
        long weapon=unit_inventory_get_weapon(unit_index,slot);
        if(weapon!=NONE && weapon_try_and_get(weapon)) return weapon;
    }
    return NONE;
}
int vr_render_vehicle_first_person_hands(void)
{
    long weapon;
    if(!vr_render.stereo || vr_render.cinematic_view || !vr_wheel.valid || !vr_vehicle_handles_enabled(vr_wheel.unit) ||
       !unit_try_and_get(vr_wheel.unit))return 0;
    weapon=first_person_weapon_vr_weapon(0);
    return weapon!=NONE && weapon_try_and_get(weapon)!=NULL;
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
