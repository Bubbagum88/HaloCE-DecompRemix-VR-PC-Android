#ifndef VR_PROJECTILE_PARRY_H
#define VR_PROJECTILE_PARRY_H
#include "math/real_math.h"
#ifdef HALO_VR
void vr_projectile_parry_reset(void);
void vr_projectile_parry_new_map(void);
void vr_projectile_parry_forget(long projectile);
void vr_projectile_parry_tick(long unit);
/* Native movement owns collision, elapsed travel, gravity and fuse. This
 * commits only a physical contact earlier than its first solid collision. */
boolean vr_projectile_parry_try(long projectile, real_point3d const *end,
    real_vector3d const *velocity, real solid_fraction, real tick_remaining,
    real *contact_fraction);
#endif
#endif
