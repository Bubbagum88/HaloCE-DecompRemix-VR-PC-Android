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
#include "network_interaction.h"
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
    int walljump_age; /* Test55: ticks since the last wall jump (chained runs) */
    int lost_ticks,miss_logged; /* Test66: a run kept over a short gap; one diagnostic a jump */
    int leap_ticks; /* Test73: the wall jump's leap held against air control (vr_pk_leap_hold) */
    float leap_direction[2],leap_speed;
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
    parkour.jump_age=1000;parkour.walljump_age=1000;parkour.hand[0].down=parkour.hand[1].down=1;
}

static boolean parkour_enabled(void)
{
    return config_boolean("vr.parkour_wallrun")||config_boolean("vr.parkour_walljump")||config_boolean("vr.parkour_climb");
}
/* Local play, and a co-op host's own player: the host simulates its player
 * authoritatively and its clients take that state. A client's prediction of a
 * wall run or climb would be refused by the host's movement checks (no
 * hovering, slow falls or rises past a jump: port/linux/NETCODE.md), and in
 * PvP it would be an advantage, so PvP keeps stock movement. Test73 (10d): a
 * co-op client too when its host's VR INTERACTIONS allows VR movement, whose
 * movement checks then allow its wall runs, climbs and slides
 * (network_distributed.c distributed_on_foot_bound). */
static boolean parkour_session_allowed(void)
{
    short connection=game_connection();
    return connection==_game_connection_local ||
        (connection==_game_connection_network_server&&network_coop_active()) ||
        (connection==_game_connection_network_client&&network_coop_active()&&
         network_interaction_vr_allowed(NETWORK_VR_MOVEMENT));
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
    long unit,int low,struct collision_result *result,real *rejected_z)
{
    memset(result,0,sizeof(*result));result->object_index=NONE;
    if(!collision_test_vector(PARKOUR_WALL_FLAGS,from,vector,unit,result)||!(result->t>=0&&result->t<=1))return FALSE;
    if(vr_pk_runnable(result->plane.n.n,low))return TRUE;
    if(rejected_z&&isfinite(result->plane.n.k))*rejected_z=result->plane.n.k;
    return FALSE;
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
	return (real)(isfinite(metres)?PIN(metres,0.04,0.20):0.14)*units;
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
	if(!(radius>0.0f)||!isfinite(radius))return FALSE;
	vector_from_points3d(camera,hand,&ray);
	length=magnitude3d(&ray);
	if(!(length>0.001f)||!isfinite(length))return FALSE;
	scale_vector3d(&ray,(length+radius)/length,&ray);
	memset(&hit,0,sizeof(hit));hit.object_index=NONE;
	if(!collision_test_vector(PARKOUR_WALL_FLAGS,camera,&ray,unit,&hit)||!(hit.t>=0.0f&&hit.t<=1.0f)||
		!vr_pk_climbable(hit.plane.n.n,hit.point.z>=waist_z))return FALSE;
	/* A head-to-hand obstruction is only a contact when the hand is close
	 * to that face. A deeply penetrating tracked hand must not grab a remote
	 * wall merely because the longer ray crossed it on the way. */
	vector_from_points3d(hand,&hit.point,&ray);
	length=magnitude3d(&ray);
	if(!isfinite(length)||length>radius)return FALSE;
	*best=hit;
	if(best->type!=_collision_result_object)best->object_index=NONE;
	best->t=0.0f;
	return TRUE;
}
/* Test70: short rays from the hand to the surface beside it (the owner:
 * "if the player's hand is clearly against a solid tree trunk, rock, wall or
 * object and Grip is held, it should usually establish a grab"): along the
 * palm, ahead of the head, to either side, up and down, each the grab
 * radius long; the nearest climbable face they meet is the hold. For a thin
 * trunk or a branch the sphere's features missed (or were too many) */
static boolean parkour_grab_rays(long unit,real_point3d const *hand,real_vector3d const *palm,
	real_vector3d const *look,real_vector3d const *up,real radius,real waist_z,struct collision_result *best)
{
	real_vector3d directions[8],left;
	real nearest=2.0f;
	int count=0,found=FALSE;
	if(!(radius>0.0f)||!isfinite(radius))return FALSE;
	cross_product3d(up,look,&left);
	if(normalize3d(&left)<.001f)return FALSE;
	directions[count++]=*palm;
	directions[count++]=*look;
	directions[count++]=left;
	scale_vector3d(&left,-1.0f,&directions[count++]);
	directions[count++]=*up;
	scale_vector3d(up,-1.0f,&directions[count++]);
	{
		real_vector3d slant;
		add_vectors3d(look,&left,&slant);if(normalize3d(&slant)>.001f)directions[count++]=slant;
		scale_vector3d(&left,-1.0f,&slant);add_vectors3d(look,&slant,&slant);if(normalize3d(&slant)>.001f)directions[count++]=slant;
	}
	for(int d=0;d<count;d++){
		struct collision_result hit;real_vector3d ray;
		if(!valid_real_vector3d(&directions[d]))continue;
		scale_vector3d(&directions[d],radius,&ray);
		memset(&hit,0,sizeof(hit));hit.object_index=NONE;
		/* (strictly within the radius: a face at its very end is out of reach) */
		if(!collision_test_vector(PARKOUR_WALL_FLAGS,hand,&ray,unit,&hit)||!(hit.t>=0.0f&&hit.t<1.0f))continue;
		/* a face met head-on from outside (not the inside of the solid) */
		if(dot_product3d(&hit.plane.n,&directions[d])>-0.2f)continue;
		if(!vr_pk_climbable(hit.plane.n.n,hit.point.z>=waist_z))continue;
		if(hit.t<nearest){nearest=hit.t;*best=hit;found=TRUE;}
	}
	if(found){
		if(best->type!=_collision_result_object)best->object_index=NONE;
		best->t=0.0f;
	}
	return found;
}
static boolean parkour_grab_surface(long unit,real_point3d const *hand,real units,real waist_z,struct collision_result *best)
{
	real radius=parkour_grab_radius(units);
	struct collision_plane contact;
	int total=0,attempt,full=FALSE;
	/* Test70: a tree's upper trunk among its branches and leaves fills the
	 * features' lists (256 of a kind) within the grab radius (and the 19 cm
	 * the query adds), which refused the hold outright: the owner's report,
	 * a tree climbed low but not high. A full list is tried again at half
	 * and a quarter of the radius, which takes fewer features */
	for(attempt=0;attempt<3;attempt++){
		real r=radius*(attempt==0?1.0f:attempt==1?0.5f:0.25f);
		total=0;full=FALSE;
		if(!(r>0.0f) || !collision_get_features_in_sphere(PARKOUR_WALL_FLAGS,hand,
			r,0.0f,r,unit,&parkour_contact_features))return FALSE;
		for(int type=0;type<NUMBER_OF_COLLISION_FEATURE_TYPES;type++){
			if(parkour_contact_features.count[type]<0)return FALSE;
			if(parkour_contact_features.count[type]>=MAXIMUM_COLLISION_FEATURES_PER_TEST)full=TRUE;
			total+=parkour_contact_features.count[type];
		}
		if(!full)break;
	}
	if(full){
		static long logged;long now=game_time_get();
		if(now-logged>TICKS_PER_SECOND||now<logged){logged=now;platform_log("VR parkour: the geometry by the hand is too dense to read even at a quarter of the grab radius; trying short rays");}
		return FALSE;
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
    real rejected_z=NAN;
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
    if(parkour.walljump_age<1000)parkour.walljump_age++;
    airborne=TEST_FLAG(biped->biped.flags,_biped_airborne_bit);
    if(!airborne){parkour.run_ticks=0;parkour.jumped_wall=0;parkour.wall_valid=0;parkour.leap_ticks=0;}
    /* Test73: the leap goes where the head looked, not back along the stick */
    if(parkour.leap_ticks>0){vr_pk_leap_hold(parkour.leap_direction,parkour.leap_speed,velocity->n);parkour.leap_ticks--;}
    throttle=sqrtf(biped->unit.throttle.i*biped->unit.throttle.i+biped->unit.throttle.j*biped->unit.throttle.j);
    center=*position;center.z+=height*0.55f;
    real waist_z=position->z+height*0.55f;
    left.i=-biped->object.forward.j;left.j=biped->object.forward.i;left.k=0;
    if(config_boolean("vr.parkour_wallrun")||config_boolean("vr.parkour_walljump")){
        /* Test55: eight directions (the diagonals catch a wall met at an
         * angle), and while running a longer probe toward the wall being run
         * on, a light lock that keeps it through small gaps and bends. */
        /* Test66: at the knee, the waist and the chest (a wall that bulges
         * or falls back at the waist), nearest first */
        static real const levels[3]={0.55f,0.85f,0.30f};
        for(int level=0;level<3;level++)for(int direction=0;direction<9;direction++){
            real_vector3d ray;
            struct collision_result hit;
            real_point3d from=*position;
            real reach=radius+0.18f*units;
            from.z+=height*levels[level];
            if(direction<8){
                real angle=(real)direction*0.7853982f;
                for(int axis=0;axis<3;axis++)ray.n[axis]=biped->object.forward.n[axis]*cosf(angle)+left.n[axis]*sinf(angle);
            }else{
                if(!parkour.running||!parkour.wall_valid)continue;
                scale_vector3d(&parkour.wall_normal,-1.0f,&ray);
                reach=radius+0.35f*units;
            }
            ray.k=0;if(normalize3d(&ray)<0.001f)continue;
            scale_vector3d(&ray,reach,&ray);
            if(parkour_surface(&from,&ray,unit,level==2,&hit,&rejected_z)&&(!wall_found||hit.t<wall.t)){wall=hit;wall_found=TRUE;}
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
            /* (a run goes on round a bend: only a new wall off the ground restarts it) */
            if(magnitude3d(&separation)>0.5f*units&&!parkour.running){parkour.run_ticks=0;parkour.jumped_wall=0;changed=TRUE;}
        }
        if(!parkour.wall_valid||changed){parkour.wall_normal=wall.plane.n;parkour.wall_point=wall.point;parkour.wall_valid=1;}
        else if(parkour.running){
            /* Test66: the facing eases round a curve and over seams */
            vr_pk_blend_normal(parkour.wall_normal.n,wall.plane.n.n);parkour.wall_point=wall.point;
        }
        parkour.lost_ticks=0;
    }else if(parkour.running&&parkour.wall_valid&&airborne&&parkour.lost_ticks<6){
        /* Test66: a run keeps over a gap in the wall (a seam, a step, a
         * missing face) for a fifth of a second on the facing it had */
        memset(&wall,0,sizeof(wall));wall.object_index=NONE;
        wall.point=parkour.wall_point;wall.plane.n=parkour.wall_normal;wall_found=TRUE;
        parkour.lost_ticks++;
    }
    if(!airborne||parkour.jump_age==0)parkour.miss_logged=0;
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
			real_vector3d palm=forward;
			if((parkour_grab_surface(unit,&point,units,waist_z,&hit)||
				parkour_grab_through(unit,&camera,&point,parkour_grab_radius(units),waist_z,&hit)||
				parkour_grab_rays(unit,&point,&palm,&look,&up,parkour_grab_radius(units),waist_z,&hit))&&
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
        /* Test70: the wall run along, not the nearest face a probe met (one
         * looked at is not the one jumped from); the look leads */
        real_vector3d from_wall=parkour.running&&parkour.wall_valid?parkour.wall_normal:wall.plane.n;
        {
            /* Test73: the head alone aims the leap (no stick bend: in VR the stick
             * is held along the wall the run went), and the leap is held against
             * the air control that turned it back toward the stick */
            float carried[3]={(float)velocity->i,(float)velocity->j,(float)velocity->k};
            vr_pk_wall_leap(look.n,from_wall.n,carried,NULL,5.0f*per_second*scale,upward,velocity->n);
            parkour.leap_ticks=vr_pk_leap_start(velocity->n,parkour.leap_direction,&parkour.leap_speed)?
                VR_PK_LEAP_HOLD_TICKS:0;
        }
        platform_log("VR parkour: wall jump look=%.2f/%.2f/%.2f wall=%.2f/%.2f/%.2f%s out=%.2f/%.2f/%.2f m/s",
            look.i,look.j,look.k,from_wall.i,from_wall.j,from_wall.k,parkour.running?" (run wall)":"",
            velocity->i*30.0f/units,velocity->j*30.0f/units,velocity->k*30.0f/units);
        parkour.jumped_wall=1;parkour.running=0;parkour.run_ticks=(int)(3*TICKS_PER_SECOND);parkour.walljump_age=0;
        for(int hand=0;hand<2;hand++){parkour.hand[hand].active=0;vr_interaction_release(hand,VR_INTERACTION_PARKOUR);}
        vr_haptic(0,0.30f,0.04f);vr_haptic(1,0.30f,0.04f);
        platform_log("VR parkour: wall jump unit=%ld",unit);return;
    }
    if(contacts){
        scale_vector3d(&climb,1.0f/contacts,&climb);vr_pk_cap(climb.n,4.0f*per_second);
        *velocity=climb;parkour.running=0;parkour.leap_ticks=0;return;
    }
    if(released){
        real scale=vr_pk_bound(config_real("vr.climb_launch_scale"),1,0,1.5f);
        if(scale==0)return;
        scale_vector3d(&release_launch,scale/released,&release_launch);vr_pk_cap(release_launch.n,8.0f*per_second);
        add_vectors3d(velocity,&release_launch,velocity);vr_pk_cap(velocity->n,10.0f*per_second);
        platform_log("VR parkour: climb release unit=%ld scale=%.2f",unit,scale);return;
    }
    /* Test55: more automatic wall running. A run starts with the stick
     * pushed (over 60%) within a second of a jump, or of a wall jump two
     * seconds back (chaining wall to wall); once running, a lightly held or
     * released stick keeps it going along the wall at the speed it carries. */
    if(config_boolean("vr.parkour_wallrun")&&airborne&&!parkour.running&&!wall_found&&!parkour.miss_logged&&
        throttle>0.6f&&parkour.jump_age<=PARKOUR_WALLRUN_ENTRY_TICKS&&parkour.jump_age>=6){
        /* Test66: why a jump at a wall did not run (once a jump) */
        if(isfinite(rejected_z))platform_log("VR parkour: no wall run: the surface met faces %s (normal z %.2f; a run needs one steeper than ~53 degrees)",
            rejected_z>0?"up":"down",(float)rejected_z);
        else platform_log("VR parkour: no wall run: no wall within %.0f cm of the body",(float)((radius/units+0.18f)*100.0f));
        parkour.miss_logged=1;
    }
    if(config_boolean("vr.parkour_wallrun")&&airborne&&parkour.running&&wall_found&&throttle>0.5f){
        /* Test66: steered away from the wall: the run ends there */
        real_vector3d stick;
        stick.i=biped->object.forward.i*biped->unit.throttle.i+left.i*biped->unit.throttle.j;
        stick.j=biped->object.forward.j*biped->unit.throttle.i+left.j*biped->unit.throttle.j;stick.k=0;
        if(normalize3d(&stick)>0.001f&&dot_product3d(&stick,&wall.plane.n)>0.6f){
            platform_log("VR parkour: wall run ended unit=%ld (steered away, %d ticks)",unit,parkour.run_ticks);
            parkour.running=0;parkour.run_ticks=(int)(3*TICKS_PER_SECOND);return;
        }
    }
    if(config_boolean("vr.parkour_wallrun")&&airborne&&wall_found&&
        (parkour.running?TRUE:throttle>0.6f)&&
        (parkour.running||parkour.jump_age<=PARKOUR_WALLRUN_ENTRY_TICKS||parkour.walljump_age<=2*TICKS_PER_SECOND)&&
        parkour.run_ticks<vr_pk_bound(config_real("vr.wallrun_duration"),2.0f,0.5f,3)*TICKS_PER_SECOND){
        real speed=sqrtf(velocity->i*velocity->i+velocity->j*velocity->j);
        real into;
        if(throttle>0.3f){
            wall_move.i=biped->object.forward.i*biped->unit.throttle.i+left.i*biped->unit.throttle.j;
            wall_move.j=biped->object.forward.j*biped->unit.throttle.i+left.j*biped->unit.throttle.j;
        }else{
            /* stick released: run on the way the body is already going */
            wall_move.i=velocity->i;wall_move.j=velocity->j;
        }
        wall_move.k=0;
        into=dot_product3d(&wall_move,&wall.plane.n);
        for(int axis=0;axis<3;axis++)wall_move.n[axis]-=into*wall.plane.n.n[axis];
        wall_move.k=0;
        if(normalize3d(&wall_move)>(throttle>0.3f?0.15f:0.001f)&&speed>1.0f*per_second){
            /* forward assist: at least the entry speed or 4 m/s, times
             * WALL SPEED, at most 9 m/s */
            real multiplier=vr_pk_bound(config_real("vr.wallrun_speed"),1.25f,1,2);
            real limit=vr_pk_bound(config_real("vr.wallrun_duration"),2.0f,0.5f,3)*TICKS_PER_SECOND;
            real progress=PIN((real)parkour.run_ticks/limit,0.0f,1.0f);
            if(!parkour.running)parkour.run_speed=speed;
            speed=vr_pk_bound(fmaxf(parkour.run_speed,4.0f*per_second)*multiplier,4.0f*per_second,2.0f*per_second,9.0f*per_second);
            velocity->i=velocity->i*0.65f+wall_move.i*speed*0.35f;
            velocity->j=velocity->j*0.65f+wall_move.j*speed*0.35f;
            /* a light hold toward the wall keeps the feet on it */
            velocity->i-=wall.plane.n.i*0.3f*per_second;
            velocity->j-=wall.plane.n.j*0.3f*per_second;
            /* level for the first 60% of WALL TIME, then easing into the fall */
            if(velocity->k<0.0f){
                if(progress<0.6f)velocity->k=0.0f;
                else velocity->k*=PIN((progress-0.6f)/0.4f,0.0f,1.0f);
            }
            if(!parkour.running)platform_log("VR parkour: wall run unit=%ld chained=%d",unit,parkour.walljump_age<=2*TICKS_PER_SECOND);
            parkour.running=1;parkour.run_ticks++;parkour.leap_ticks=0;return;
        }
    }
    parkour.running=0;
}
#endif
