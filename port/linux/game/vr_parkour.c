/* Optional local-player parkour feeds native biped capsule collision (solo,
 * and a co-op host's own player). It never teleports, changes a tag's physics
 * flags, or sends custom movement packets. */
#ifdef HALO_VR
#include "cseries.h"
#include "math/real_math.h"
#include "game/game.h"
#include "game/players.h"
#include "units/bipeds.h"
#include "units/biped_definitions.h"
#include "camera/director.h"
#include "cutscene/cinematics.h"
#include "physics/collisions.h"
#include "physics/collision_features.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_parkour.h"
#include "vr_parkour_math.h"
#include "vr_world_math.h"
#include "network_coop.h"
void platform_log(char const *format,...);

/* A wall run starts on a wall reached within a second of pressing Jump (it
 * was a third of a second: a jump from more than about a metre away landed
 * on the wall too late to run along it). */
#define PARKOUR_WALLRUN_ENTRY_TICKS (TICKS_PER_SECOND)
#define PARKOUR_WALL_FLAGS (FLAG(_collision_test_structure_bit)|FLAG(_collision_test_objects_bit)|FLAG(_collision_test_objects_scenery_bit))
/* Filled only on a Grip edge; a palm-sized overlap is cheap and never uses
 * an aim ray to search for a wall. */
static struct collision_feature_list parkour_contact_features;
/* Keep diagnostic rate limiting outside the transient parkour state so an
 * online/paused gate that resets the active climb cannot spam every frame. */
static long parkour_diagnostic_tick=NONE;
static struct {
    long unit,tick;
    int jump_down,jump_age,run_ticks,running,jumped_wall,wall_valid;
    real run_speed;
    real_vector3d wall_normal;
    real_point3d wall_point;
    struct {
        int active,down,sampled,strain_logged,grace;
        long object;
        real_point3d anchor,object_position,relative;
        real_vector3d launch,normal;
    } hand[2];
} parkour;

void vr_parkour_reset(void)
{
    if(parkour.running||parkour.hand[0].active||parkour.hand[1].active)
        platform_log("VR parkour: reset unit=%ld",parkour.unit);
    vr_interaction_release(0,VR_INTERACTION_PARKOUR);
    vr_interaction_release(1,VR_INTERACTION_PARKOUR);
    memset(&parkour,0,sizeof(parkour));parkour.unit=parkour.tick=NONE;
    parkour.jump_down=1;
    parkour.jump_age=1000;parkour.hand[0].down=parkour.hand[1].down=1;
}

static boolean parkour_enabled(void)
{
    return config_boolean("vr.parkour_wallrun")||config_boolean("vr.parkour_walljump")||config_boolean("vr.parkour_climb");
}
/* Local play, and a co-op host's own player: the host simulates its player
 * authoritatively and its clients take that state. A client's prediction of a
 * wall run or climb would be refused by the host's movement checks (no
 * hovering, slow falls or rises past a jump: port/linux/NETCODE.md), and in
 * PvP it would be an advantage, so clients and PvP keep stock movement. */
static boolean parkour_session_allowed(void)
{
    short connection=game_connection();
    return connection==_game_connection_local ||
        (connection==_game_connection_network_server&&network_coop_active());
}
static char const *parkour_gate_reason(long unit,int *is_local)
{
    short local=local_player_get_next(NONE);
    long player=local!=NONE?local_player_get_player_index(local):NONE;
    struct biped_datum *biped;
    unsigned int buttons;float triggers[2],thumbs[4];
    if(is_local)*is_local=0;
    if(player==NONE)return "no-local-player";
    if(player_get(player)->unit_index!=unit)return "not-local-player";
    if(is_local)*is_local=1;
    if(unit==NONE)return "invalid-unit";
    if(!vr_active())return "vr-inactive";
    if(!vr_controller(&buttons,triggers,thumbs))return "controller-unfocused-or-invalid";
    if(!parkour_session_allowed())return "network-session";
    if(game_time_get_paused())return "paused";
    if(cinematic_in_progress())return "cinematic";
    if(director_inhibited_input(local))return "director-inhibited";
    biped=biped_try_and_get(unit);
    if(!biped)return "unit-datum-invalid";
    if(biped->object.parent_object_index!=NONE)return "seated-or-parented";
    if(TEST_FLAG(biped->object.damage_flags,_object_dead_bit))return "player-dead";
    if(TEST_FLAG(biped->biped.flags,_biped_no_collision_bit))return "no-collision";
    if(TEST_FLAG(biped->unit.flags,_unit_suspended_bit))return "unit-suspended";
    return NULL;
}
static boolean parkour_local(long unit)
{
    return parkour_gate_reason(unit,NULL)==NULL;
}
void vr_parkour_note_unit(long unit)
{
    if(!parkour_enabled()||!parkour_local(unit)||unit!=parkour.unit)vr_parkour_reset();
}
int vr_parkour_hand(int hand,float position[3])
{
    if(hand<0||hand>1||!parkour.hand[hand].active||
        vr_interaction_owner(hand)!=VR_INTERACTION_PARKOUR)return 0;
    for(int axis=0;axis<3;axis++)position[axis]=parkour.hand[hand].anchor.n[axis];
    return 1;
}
static boolean parkour_surface(real_point3d const *from,real_vector3d const *vector,
    long unit,struct collision_result *result)
{
    memset(result,0,sizeof(*result));result->object_index=NONE;
    return collision_test_vector(PARKOUR_WALL_FLAGS,from,vector,unit,result)&&
        result->t>=0&&result->t<=1&&vr_pk_vertical(result->plane.n.n);
}
static long parkour_hit_object(struct collision_result const *hit)
{
    /* BSP collision leaves object_index untouched. Never treat it as an object. */
    return hit->type==_collision_result_object?hit->object_index:NONE;
}
/* Test54: VR CLIMB GRAB, metres from a surface a squeezed hand still grips */
static real parkour_grab_radius(real units)
{
	double metres=config_real("vr.climb_grab_radius");
	return (real)(isfinite(metres)?PIN(metres,0.04,0.20):0.10)*units;
}
/* Test54: a tracked hand is not stopped by walls: pushed into a rock face it
 * is inside the solid, where no surface lies within any radius of it. The
 * line from the eyes to the hand crosses the face it went through; that
 * crossing is the hold (only for a hand within reach of the face). */
static boolean parkour_grab_through(long unit,real_point3d const *camera,real_point3d const *hand,
	real radius,real waist_z,struct collision_result *best)
{
	real_vector3d ray;
	real length;
	struct collision_result hit;
	vector_from_points3d(camera,hand,&ray);
	length=magnitude3d(&ray);
	if(!(length>0.001f)||!isfinite(length))return FALSE;
	scale_vector3d(&ray,(length+radius)/length,&ray);
	memset(&hit,0,sizeof(hit));hit.object_index=NONE;
	if(!collision_test_vector(PARKOUR_WALL_FLAGS,camera,&ray,unit,&hit)||!(hit.t>=0.0f&&hit.t<=1.0f)||
		!vr_pk_climbable(hit.plane.n.n,hit.point.z>=waist_z))return FALSE;
	*best=hit;
	if(best->type!=_collision_result_object)best->object_index=NONE;
	best->t=0.0f;
	return TRUE;
}
static boolean parkour_grab_surface(long unit,real_point3d const *hand,real units,real waist_z,struct collision_result *best)
{
	real radius=parkour_grab_radius(units);
	struct collision_plane contact;
	int total=0;
	if(!(radius>0.0f) || !collision_get_features_in_sphere(PARKOUR_WALL_FLAGS,hand,
		radius,0.0f,radius,unit,&parkour_contact_features))return FALSE;
	for(int type=0;type<NUMBER_OF_COLLISION_FEATURE_TYPES;type++){
		if(parkour_contact_features.count[type]<0 ||
			parkour_contact_features.count[type]>=MAXIMUM_COLLISION_FEATURES_PER_TEST)return FALSE;
		total+=parkour_contact_features.count[type];
	}
	if(total==0 || !collision_features_test_point(&parkour_contact_features,hand,&contact))return FALSE;
	{
		real distance=plane3d_distance_to_point(&contact.plane,hand);
		real_point3d surface;
		if(!isfinite(distance))return FALSE;
		point_from_line3d(hand,&contact.plane.n,-distance,&surface);
		if(!vr_pk_climbable(contact.plane.n.n,surface.z>=waist_z))return FALSE;
	}
	memset(best,0,sizeof(*best));
	best->type=contact.object_index==NONE?_collision_result_structure:_collision_result_object;
	best->object_index=contact.object_index;
	best->surface_index=contact.surface_index;
	best->material_index=contact.material_index;
	best->flags=contact.flags;
	best->breakable_surface_index=contact.breakable_surface_index;
	{
		real distance=plane3d_distance_to_point(&contact.plane,hand);
		if(!isfinite(distance))return FALSE;
		point_from_line3d(hand,&contact.plane.n,-distance,&best->point);
	}
	best->plane=contact.plane;
	best->t=0.0f;
	return TRUE;
}
void vr_parkour_velocity(long unit,real_point3d const *position,float height,float radius,real_vector3d *velocity)
{
    struct biped_datum *biped;
    struct collision_result wall;
    real_point3d camera,head,center;
    real_vector3d look,up,left,wall_move={0},climb={0},release_launch={0};
    real units,per_second,throttle;
    int jump,edge,airborne,contacts=0,released=0,wall_found=0;
    long tick;
    tick=game_time_get();
    if(!parkour_enabled()){
        /* Disabling an active climb must release its hand ownership promptly.
         * Avoid rewriting state for every NPC when parkour is already idle. */
        if(parkour.unit!=NONE||parkour.running||parkour.hand[0].active||parkour.hand[1].active)
            vr_parkour_reset();
        return; /* No probes or velocity changes when disabled. */
    }
    {
        int is_local=0;
        char const *reason=parkour_gate_reason(unit,&is_local);
        if(reason){
            if(is_local&&config_boolean("vr.contact_debug")&&
                (parkour_diagnostic_tick==NONE||tick<parkour_diagnostic_tick||tick-parkour_diagnostic_tick>=2*TICKS_PER_SECOND)){
                unsigned int diagnostic_buttons;
                float diagnostic_triggers[2],diagnostic_thumbs[4];
                int focused=vr_active()&&vr_controller(&diagnostic_buttons,diagnostic_triggers,diagnostic_thumbs);
                platform_log("VR parkour: gate blocked unit=%ld reason=%s connection=%d paused=%d focused=%d cinematic=%d",
                    unit,reason,game_connection(),game_time_get_paused(),
                    focused,cinematic_in_progress());
                parkour_diagnostic_tick=tick;
            }
            if(unit==parkour.unit)vr_parkour_reset();
            return; /* NPCs and network players never enter this path. */
        }
    }
    if(tick==parkour.tick&&unit==parkour.unit)return;
    if(unit!=parkour.unit||tick<parkour.tick||tick>parkour.tick+1)vr_parkour_reset();
    parkour.unit=unit;parkour.tick=tick;
    units=vr_units_per_metre();if(!(units>0&&units<10)){vr_parkour_reset();return;}
    per_second=units/(real)TICKS_PER_SECOND;
    biped=biped_get(unit);
    unit_get_camera_position(unit,&camera);
    if(!vr_head_view(camera.n,biped->object.forward.n,head.n,look.n,up.n)){vr_parkour_reset();return;}
    jump=TEST_FLAG(biped->unit.control_flags,_unit_control_jump_bit);
    edge=jump&&!parkour.jump_down;parkour.jump_down=jump;
    if(edge)parkour.jump_age=0;else if(parkour.jump_age<1000)parkour.jump_age++;
    airborne=TEST_FLAG(biped->biped.flags,_biped_airborne_bit);
    if(!airborne){parkour.run_ticks=0;parkour.jumped_wall=0;parkour.wall_valid=0;}
    throttle=sqrtf(biped->unit.throttle.i*biped->unit.throttle.i+biped->unit.throttle.j*biped->unit.throttle.j);
    center=*position;center.z+=height*0.55f;
    real waist_z=position->z+height*0.55f;
    left.i=-biped->object.forward.j;left.j=biped->object.forward.i;left.k=0;
    if(config_boolean("vr.parkour_wallrun")||config_boolean("vr.parkour_walljump")){
        for(int direction=0;direction<4;direction++){
            real_vector3d ray=direction<2?biped->object.forward:left;
            struct collision_result hit;
            ray.k=0;if(normalize3d(&ray)<0.001f)continue;
            scale_vector3d(&ray,(direction%2?-1:1)*(radius+0.18f*units),&ray);
            if(parkour_surface(&center,&ray,unit,&hit)&&(!wall_found||hit.t<wall.t)){wall=hit;wall_found=TRUE;}
        }
    }
    if(config_boolean("vr.contact_debug")&&
        (parkour_diagnostic_tick==NONE||tick<parkour_diagnostic_tick||tick-parkour_diagnostic_tick>=2*TICKS_PER_SECOND)){
        int grip0=vr_interaction_grip(0,NULL,NULL),grip1=vr_interaction_grip(1,NULL,NULL);
        platform_log("VR parkour: probe unit=%ld wallrun=%d walljump=%d climb=%d airborne=%d throttle=%.2f wall_hit=%d wall_normal=%.2f/%.2f/%.2f jump_age=%d grip=%d/%d active=%d/%d owner=%d/%d",
            unit,config_boolean("vr.parkour_wallrun"),config_boolean("vr.parkour_walljump"),
            config_boolean("vr.parkour_climb"),airborne,throttle,wall_found,
            wall_found?wall.plane.n.i:0.f,wall_found?wall.plane.n.j:0.f,wall_found?wall.plane.n.k:0.f,
            parkour.jump_age,grip0,grip1,parkour.hand[0].active,parkour.hand[1].active,
            vr_interaction_owner(0),vr_interaction_owner(1));
        parkour_diagnostic_tick=tick;
    }
    if(wall_found){
        boolean changed=FALSE;
        if(parkour.wall_valid&&dot_product3d(&parkour.wall_normal,&wall.plane.n)<0.5f){
            real_vector3d separation;vector_from_points3d(&parkour.wall_point,&wall.point,&separation);
            if(magnitude3d(&separation)>0.5f*units){parkour.run_ticks=0;parkour.jumped_wall=0;changed=TRUE;}
        }
        if(!parkour.wall_valid||changed){parkour.wall_normal=wall.plane.n;parkour.wall_point=wall.point;parkour.wall_valid=1;}
    }
    /* Grip climbing uses only free hands against real static collision. */
    for(int hand=0;hand<2;hand++){
        real_point3d point;real_vector3d forward,hand_up;
        int held=vr_interaction_grip(hand,NULL,NULL),press=held&&!parkour.hand[hand].down;
        int release=!held&&parkour.hand[hand].down;
        parkour.hand[hand].down=held;
        boolean eligible=config_boolean("vr.parkour_climb")&&
            (hand!=vr_weapon_hand()||vr_hand_empty())&&
            (vr_interaction_owner(hand)==VR_INTERACTION_NONE||vr_interaction_owner(hand)==VR_INTERACTION_PARKOUR)&&
            vr_hand_world(hand,camera.n,point.n,forward.n,hand_up.n);
        if(!eligible){
            parkour.hand[hand].active=parkour.hand[hand].sampled=0;
            /* Tracking/ownership loss is cancellation, not a physical release.
             * Require an observed released grip before another wall latch. */
            parkour.hand[hand].down=1;
            vr_interaction_release(hand,VR_INTERACTION_PARKOUR);continue;
        }
        /* Test54: a fresh squeeze keeps looking for a hold for a few ticks */
        if(press)parkour.hand[hand].grace=VR_PK_GRIP_GRACE_TICKS;
        else if(!held||parkour.hand[hand].active)parkour.hand[hand].grace=0;
        if(held&&!parkour.hand[hand].active&&parkour.hand[hand].grace>0){
            struct collision_result hit;
            parkour.hand[hand].grace--;
			if((parkour_grab_surface(unit,&point,units,waist_z,&hit)||
				parkour_grab_through(unit,&camera,&point,parkour_grab_radius(units),waist_z,&hit))&&
				vr_interaction_claim(hand,VR_INTERACTION_PARKOUR)){
                long hit_object=parkour_hit_object(&hit);
                struct object_datum *object=hit_object!=NONE?
                    object_try_and_get_and_verify_type(hit_object,_object_mask_scenery):NULL;
                if(hit_object!=NONE&&!object){vr_interaction_release(hand,VR_INTERACTION_PARKOUR);continue;}
                parkour.hand[hand].active=1;parkour.hand[hand].anchor=hit.point;parkour.hand[hand].normal=hit.plane.n;parkour.hand[hand].object=hit_object;
                if(object)parkour.hand[hand].object_position=object->object.position;
                parkour.hand[hand].launch=*global_zero_vector3d;parkour.hand[hand].sampled=0;
				vr_haptic(hand,0.35f,0.04f);platform_log("VR parkour: wall grip hand=%d object=%ld normal_z=%.2f acquisition=surface-contact-plus-fresh-grip",hand,hit_object,hit.plane.n.k);
				parkour.hand[hand].grace=0;
			} else if(parkour.hand[hand].grace==0) platform_log("VR parkour: wall grip missed hand=%d radius=%.2f cm (touch a wall, rock face or a ledge above the waist, then squeeze Grip)",
				hand,(float)parkour_grab_radius(units)*100.0f/(float)units);
        }
        if(parkour.hand[hand].active){
            real_vector3d error;real_point3d relative;
            vector_from_points3d(&point,&parkour.hand[hand].anchor,&error);
            if(parkour.hand[hand].object!=NONE){
                struct object_datum *object=object_try_and_get_and_verify_type(parkour.hand[hand].object,_object_mask_scenery);
                real_vector3d moved;
                if(!object){parkour.hand[hand].active=0;vr_interaction_release(hand,VR_INTERACTION_PARKOUR);continue;}
                vector_from_points3d(&parkour.hand[hand].object_position,&object->object.position,&moved);
				if(magnitude3d(&moved)>0.005f*units){
					/* A moving scenery target is not a supported climb anchor. This
					 * remains a safety cancellation; static BSP anchors are unaffected. */
					platform_log("VR parkour: release hand=%d reason=dynamic-anchor-moved grip=held",hand);
					parkour.hand[hand].active=0;vr_interaction_release(hand,VR_INTERACTION_PARKOUR);continue;
				}
            }
			if(magnitude3d(&error)>0.65f*units){
				if(!parkour.hand[hand].strain_logged)platform_log("VR parkour: hold strain hand=%d grip=held separation_m=%.3f action=keep-contact",
					hand,(float)magnitude3d(&error)/(float)units);
				parkour.hand[hand].strain_logged=1;
			}else if(magnitude3d(&error)<0.50f*units)parkour.hand[hand].strain_logged=0;
            for(int axis=0;axis<3;axis++){
                relative.n[axis]=point.n[axis]-camera.n[axis];
                if(parkour.hand[hand].sampled)
                    parkour.hand[hand].launch.n[axis]=parkour.hand[hand].launch.n[axis]*0.65f+
                        (parkour.hand[hand].relative.n[axis]-relative.n[axis])*0.35f;
            }
            parkour.hand[hand].relative=relative;parkour.hand[hand].sampled=1;
            if(release){
                add_vectors3d(&release_launch,&parkour.hand[hand].launch,&release_launch);released++;
                parkour.hand[hand].active=0;vr_interaction_release(hand,VR_INTERACTION_PARKOUR);
            }else{
                scale_vector3d(&error,0.35f,&error);add_vectors3d(&climb,&error,&climb);contacts++;
                if(!wall_found){
                    memset(&wall,0,sizeof(wall));wall.object_index=NONE;
                    wall.point=parkour.hand[hand].anchor;wall.plane.n=parkour.hand[hand].normal;wall_found=1;
                }
            }
        }
    }
    if(config_boolean("vr.parkour_walljump")&&edge&&(airborne||contacts)&&wall_found&&!parkour.jumped_wall){
        real scale=vr_pk_bound(config_real("vr.walljump_scale"),1,0.5f,1.5f);
        real upward=biped_definition_get(biped->definition_index)->biped.jump_velocity*scale;
        vr_pk_leap(look.n,wall.plane.n.n,5.0f*per_second*scale,upward,velocity->n);
        parkour.jumped_wall=1;parkour.running=0;parkour.run_ticks=(int)(3*TICKS_PER_SECOND);
        for(int hand=0;hand<2;hand++){parkour.hand[hand].active=0;vr_interaction_release(hand,VR_INTERACTION_PARKOUR);}
        vr_haptic(0,0.30f,0.04f);vr_haptic(1,0.30f,0.04f);
        platform_log("VR parkour: wall jump unit=%ld",unit);return;
    }
    if(contacts){
        scale_vector3d(&climb,1.0f/contacts,&climb);vr_pk_cap(climb.n,4.0f*per_second);
        *velocity=climb;parkour.running=0;return;
    }
    if(released){
        real scale=vr_pk_bound(config_real("vr.climb_launch_scale"),1,0,1.5f);
        if(scale==0)return;
        scale_vector3d(&release_launch,scale/released,&release_launch);vr_pk_cap(release_launch.n,8.0f*per_second);
        add_vectors3d(velocity,&release_launch,velocity);vr_pk_cap(velocity->n,10.0f*per_second);
        platform_log("VR parkour: climb release unit=%ld scale=%.2f",unit,scale);return;
    }
    if(config_boolean("vr.parkour_wallrun")&&airborne&&wall_found&&throttle>0.6f&&
        (parkour.running||parkour.jump_age<=PARKOUR_WALLRUN_ENTRY_TICKS)&&
        parkour.run_ticks<vr_pk_bound(config_real("vr.wallrun_duration"),1.5f,0.5f,3)*TICKS_PER_SECOND){
        real speed=sqrtf(velocity->i*velocity->i+velocity->j*velocity->j);
        real into;
        wall_move.i=biped->object.forward.i*biped->unit.throttle.i+left.i*biped->unit.throttle.j;
        wall_move.j=biped->object.forward.j*biped->unit.throttle.i+left.j*biped->unit.throttle.j;
        into=dot_product3d(&wall_move,&wall.plane.n);
        for(int axis=0;axis<3;axis++)wall_move.n[axis]-=into*wall.plane.n.n[axis];
        if(normalize3d(&wall_move)>0.15f&&speed>1.0f*per_second){
            real multiplier=vr_pk_bound(config_real("vr.wallrun_speed"),1.25f,1,2);
            if(!parkour.running)parkour.run_speed=speed;
            speed=vr_pk_bound(parkour.run_speed*multiplier,4.0f*per_second,2.0f*per_second,7.0f*per_second);
            velocity->i=velocity->i*0.65f+wall_move.i*speed*0.35f;
            velocity->j=velocity->j*0.65f+wall_move.j*speed*0.35f;
            /* Test54: the wall holds the fall off strongly at first and less
             * through the run (WALL TIME), so the run arcs down into a
             * natural fall instead of ending in a sudden drop; horizontal
             * momentum carries on past the wall either way. */
            {
                real limit=vr_pk_bound(config_real("vr.wallrun_duration"),1.5f,0.5f,3)*TICKS_PER_SECOND;
                real keep=0.7f+0.3f*PIN((real)parkour.run_ticks/limit,0.0f,1.0f);
                if(velocity->k< -0.5f*per_second)velocity->k=velocity->k*keep-0.5f*per_second*(1.0f-keep);
            }
            if(!parkour.running)platform_log("VR parkour: wall run unit=%ld",unit);
            parkour.running=1;parkour.run_ticks++;return;
        }
    }
    parkour.running=0;
}
#endif
