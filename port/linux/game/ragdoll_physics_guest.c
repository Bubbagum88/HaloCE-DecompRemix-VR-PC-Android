/*
RAGDOLL_PHYSICS_GUEST.C

Test66: the Android guest's side of the ragdolls' physics engine. OpenCE's
ragdolls (ragdoll.c) call the C interface of ragdoll_physics.h; on desktop
that is Jolt itself (port/linux/physics/ragdoll_physics.cpp), in the game's
process. The ILP32 guest cannot build Jolt (C++), so the host runs it
(port/android/host/host_ragdoll.c) and these pass each call over the import
table (port/android/host_imports.list). Structures cross as they are (ints
and floats); a contact's vehicle key is 32 bits on both sides of this call.
*/

#if defined(HALO_ARM64_GUEST) && defined(HALO_JOLT)

#include "ragdoll_physics.h"

int host_ragdoll_initialize(void);
void host_ragdoll_reset(void);
int host_ragdoll_create(int slot, const void *bones, int bone_count, const void *settings);
void host_ragdoll_destroy(int slot);
int host_ragdoll_exists(int slot);
void host_ragdoll_set_environment(int slot, int layer, const float *triangles, int triangle_count);
void host_ragdoll_step(int collision_steps, float gravity);
void host_ragdoll_get_bone(int slot, int bone, float *position, float *rotation);
void host_ragdoll_get_bone_velocity(int slot, int bone, float *velocity);
int host_ragdoll_active(int slot);
void host_ragdoll_hit(int slot, int bone, const float *point, const float *velocity, float share);
void host_ragdoll_add_velocity(int slot, const float *velocity);
void host_ragdoll_add_spin(int slot, const float *spin);
void host_ragdoll_translate(int slot, const float *offset);
void host_ragdoll_bounds(int slot, float *center, float *radius);
void host_ragdoll_vehicles_begin(void);
void host_ragdoll_vehicle(int key, const float *points, int point_count, const float *position,
	const float *rotation, const float *velocity, const float *angular_velocity);
void host_ragdoll_vehicles_end(void);
int host_ragdoll_vehicle_contacts(void *contacts, int maximum);

int ragdoll_physics_initialize(void) { return host_ragdoll_initialize(); }
void ragdoll_physics_reset(void) { host_ragdoll_reset(); }
int ragdoll_physics_create(int slot, struct ragdoll_physics_bone const *bones, int bone_count,
	struct ragdoll_physics_settings const *settings)
{
	return host_ragdoll_create(slot, bones, bone_count, settings);
}
void ragdoll_physics_destroy(int slot) { host_ragdoll_destroy(slot); }
int ragdoll_physics_exists(int slot) { return host_ragdoll_exists(slot); }
void ragdoll_physics_set_environment(int slot, int layer, float const *triangles, int triangle_count)
{
	host_ragdoll_set_environment(slot, layer, triangles, triangle_count);
}
void ragdoll_physics_step(int collision_steps, float gravity) { host_ragdoll_step(collision_steps, gravity); }
void ragdoll_physics_get_bone(int slot, int bone, float position[3], float rotation[4])
{
	host_ragdoll_get_bone(slot, bone, position, rotation);
}
void ragdoll_physics_get_bone_velocity(int slot, int bone, float velocity[3])
{
	host_ragdoll_get_bone_velocity(slot, bone, velocity);
}
int ragdoll_physics_active(int slot) { return host_ragdoll_active(slot); }
void ragdoll_physics_hit(int slot, int bone, float const point[3], float const velocity[3], float share)
{
	host_ragdoll_hit(slot, bone, point, velocity, share);
}
void ragdoll_physics_add_velocity(int slot, float const velocity[3]) { host_ragdoll_add_velocity(slot, velocity); }
void ragdoll_physics_add_spin(int slot, float const spin[3]) { host_ragdoll_add_spin(slot, spin); }
void ragdoll_physics_translate(int slot, float const offset[3]) { host_ragdoll_translate(slot, offset); }
void ragdoll_physics_bounds(int slot, float center[3], float *radius) { host_ragdoll_bounds(slot, center, radius); }
void ragdoll_physics_vehicles_begin(void) { host_ragdoll_vehicles_begin(); }
void ragdoll_physics_vehicle(long key, float const *points, int point_count, float const position[3],
	float const rotation[4], float const velocity[3], float const angular_velocity[3])
{
	host_ragdoll_vehicle((int)key, points, point_count, position, rotation, velocity, angular_velocity);
}
void ragdoll_physics_vehicles_end(void) { host_ragdoll_vehicles_end(); }
int ragdoll_physics_vehicle_contacts(struct ragdoll_physics_contact *contacts, int maximum)
{
	/* (long is 32 bits here: the host fills this layout) */
	return host_ragdoll_vehicle_contacts(contacts, maximum);
}

#endif
