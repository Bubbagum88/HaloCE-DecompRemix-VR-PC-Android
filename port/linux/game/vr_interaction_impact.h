#ifndef VR_INTERACTION_IMPACT_H
#define VR_INTERACTION_IMPACT_H
struct collision_result;
/* Game-thread only. Entries are transient and never serialized in saves. */
void vr_interaction_impact_reset(void);
void vr_interaction_impact_flush(void);
void vr_interaction_impact_track(long object, long owner_unit, float mobility, float units);
void vr_interaction_impact_collision(long object,
    struct collision_result const *collision, real_vector3d const *velocity);
#endif
