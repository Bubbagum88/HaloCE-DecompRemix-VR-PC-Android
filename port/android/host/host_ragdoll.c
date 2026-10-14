/*
HOST_RAGDOLL.C

The ragdolls' physics engine for the Android guest (Test66). OpenCE's dynamic
ragdolls (port/linux/game/ragdoll.c, game.death_physics "ragdoll") run Jolt
Physics (port/third_party/JoltPhysics) behind a small C interface
(port/linux/physics/ragdoll_physics.cpp). Jolt is C++, which the ILP32 guest
cannot build, so on Android it runs here, in the 64-bit host, and the guest
calls it through these imports (port/linux/game/ragdoll_physics_guest.c).

Only types that cross the boundary as they are: 32-bit integers, floats and
pointers into the guest's memory (the low 4 GB of this process, which the
host reads as it is). The interface's `long` (a vehicle's key) is 32 bits in
the guest: it is an int here, and a contact goes back in the guest's layout.
*/

#include <stdint.h>
#include <string.h>

#include "../../linux/game/ragdoll_physics.h"

/* a contact as the guest lays it out (its long is 32 bits) */
struct host_ragdoll_contact
{
	int32_t slot;
	int32_t vehicle;
	float point[3];
	float normal[3];
	float speed;
};

int32_t host_ragdoll_initialize(void)
{
	return ragdoll_physics_initialize();
}

void host_ragdoll_reset(void)
{
	ragdoll_physics_reset();
}

int32_t host_ragdoll_create(int32_t slot, const void *bones, int32_t bone_count, const void *settings)
{
	return ragdoll_physics_create(slot, (struct ragdoll_physics_bone const *)bones, bone_count,
		(struct ragdoll_physics_settings const *)settings);
}

void host_ragdoll_destroy(int32_t slot)
{
	ragdoll_physics_destroy(slot);
}

int32_t host_ragdoll_exists(int32_t slot)
{
	return ragdoll_physics_exists(slot);
}

void host_ragdoll_set_environment(int32_t slot, int32_t layer, const float *triangles, int32_t triangle_count)
{
	ragdoll_physics_set_environment(slot, layer, triangles, triangle_count);
}

void host_ragdoll_step(int32_t collision_steps, float gravity)
{
	ragdoll_physics_step(collision_steps, gravity);
}

void host_ragdoll_get_bone(int32_t slot, int32_t bone, float *position, float *rotation)
{
	ragdoll_physics_get_bone(slot, bone, position, rotation);
}

void host_ragdoll_get_bone_velocity(int32_t slot, int32_t bone, float *velocity)
{
	ragdoll_physics_get_bone_velocity(slot, bone, velocity);
}

int32_t host_ragdoll_active(int32_t slot)
{
	return ragdoll_physics_active(slot);
}

void host_ragdoll_hit(int32_t slot, int32_t bone, const float *point, const float *velocity, float share)
{
	ragdoll_physics_hit(slot, bone, point, velocity, share);
}

void host_ragdoll_add_velocity(int32_t slot, const float *velocity)
{
	ragdoll_physics_add_velocity(slot, velocity);
}

void host_ragdoll_add_spin(int32_t slot, const float *spin)
{
	ragdoll_physics_add_spin(slot, spin);
}

void host_ragdoll_translate(int32_t slot, const float *offset)
{
	ragdoll_physics_translate(slot, offset);
}

void host_ragdoll_bounds(int32_t slot, float *center, float *radius)
{
	ragdoll_physics_bounds(slot, center, radius);
}

void host_ragdoll_vehicles_begin(void)
{
	ragdoll_physics_vehicles_begin();
}

void host_ragdoll_vehicle(int32_t key, const float *points, int32_t point_count, const float *position,
	const float *rotation, const float *velocity, const float *angular_velocity)
{
	ragdoll_physics_vehicle((long)key, points, point_count, position, rotation, velocity, angular_velocity);
}

void host_ragdoll_vehicles_end(void)
{
	ragdoll_physics_vehicles_end();
}

int32_t host_ragdoll_vehicle_contacts(void *contacts, int32_t maximum)
{
	struct ragdoll_physics_contact found[64];
	struct host_ragdoll_contact *out = (struct host_ragdoll_contact *)contacts;
	int count, index;

	if (!contacts || maximum <= 0)
		return 0;
	if (maximum > 64)
		maximum = 64;
	count = ragdoll_physics_vehicle_contacts(found, maximum);
	for (index = 0; index < count; index++)
	{
		out[index].slot = found[index].slot;
		out[index].vehicle = (int32_t)found[index].vehicle;
		memcpy(out[index].point, found[index].point, sizeof(out[index].point));
		memcpy(out[index].normal, found[index].normal, sizeof(out[index].normal));
		out[index].speed = found[index].speed;
	}
	return count;
}

/* Test67: the items Jolt moves (item_physics.c, the OpenCE fork jcompto95-tech's) */
int32_t host_ragdoll_item_create(int32_t slot, const float *points, int32_t point_count, const float *position,
	const float *rotation, const float *velocity, const float *spin, float gravity_factor)
{
	return ragdoll_physics_item_create(slot, points, point_count, position, rotation, velocity, spin, gravity_factor);
}

void host_ragdoll_item_destroy(int32_t slot)
{
	ragdoll_physics_item_destroy(slot);
}

int32_t host_ragdoll_item_exists(int32_t slot)
{
	return ragdoll_physics_item_exists(slot);
}

int32_t host_ragdoll_item_get(int32_t slot, float *position, float *rotation, float *velocity, float *spin)
{
	return ragdoll_physics_item_get(slot, position, rotation, velocity, spin);
}

void host_ragdoll_item_add_velocity(int32_t slot, const float *velocity, const float *spin)
{
	ragdoll_physics_item_add_velocity(slot, velocity, spin);
}

void host_ragdoll_item_set_environment(int32_t slot, const float *triangles, int32_t triangle_count)
{
	ragdoll_physics_item_set_environment(slot, triangles, triangle_count);
}

int32_t host_ragdoll_items_any(void)
{
	return ragdoll_physics_items_any();
}
