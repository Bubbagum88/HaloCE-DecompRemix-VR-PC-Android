#ifndef VR_WORLD_PROPS_H
#define VR_WORLD_PROPS_H
#include "math/real_math.h"
struct object_datum;
struct object_datum *vr_world_object_get(long index);
void vr_world_object_velocity(long index,real_vector3d const *linear,real_vector3d const *angular);
float vr_world_object_mobility(long index);
void vr_world_props_tick(void);
void vr_world_props_reset(void);
void vr_world_props_freeze(void);
#endif
