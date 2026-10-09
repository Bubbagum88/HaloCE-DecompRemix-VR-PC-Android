#ifndef VR_PARKOUR_H
#define VR_PARKOUR_H
#ifdef HALO_VR
union real_point3d;
union real_vector3d;
void vr_parkour_reset(void);
void vr_parkour_note_unit(long unit_index);
int vr_parkour_hand(int hand, float position[3]);
void vr_parkour_velocity(long unit_index, union real_point3d const *position,
    float height, float radius, union real_vector3d *velocity);
#endif
#endif
