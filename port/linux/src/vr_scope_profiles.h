/* Shared scope profiles. Preserve the legacy pistol/sniper configuration keys.
 * Adjustments apply only when a weapon supplies a native zoom view. */
#ifndef VR_SCOPE_PROFILES_H
#define VR_SCOPE_PROFILES_H
#define VR_SCOPE_PROFILES(X) \
 X(pistol, "PISTOL", VR_GUN_PISTOL) \
 X(sniper, "SNIPER", VR_GUN_SNIPER_RIFLE) \
 X(rocket_launcher, "SPNKR", VR_GUN_ROCKET_LAUNCHER) \
 X(other, "OTHER", VR_GUN_OTHER) \
 X(plasma_pistol, "PL P", VR_GUN_PLASMA_PISTOL) \
 X(assault_rifle, "AR", VR_GUN_ASSAULT_RIFLE) \
 X(plasma_rifle, "PL R", VR_GUN_PLASMA_RIFLE) \
 X(shotgun, "SHOTGUN", VR_GUN_SHOTGUN) \
 X(needler, "NEEDLER", VR_GUN_NEEDLER) \
 X(fuel_rod, "FUEL ROD", VR_GUN_FUEL_ROD) \
 X(flamethrower, "FLAMER", VR_GUN_FLAMETHROWER)
#define VR_SCOPE_PROFILE_COUNT 11
#endif
