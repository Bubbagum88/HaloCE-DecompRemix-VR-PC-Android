#ifndef VR_RELOAD_GRIP_PROFILE_H
#define VR_RELOAD_GRIP_PROFILE_H
/* Test67: measurements from the stock USA Xbox first-person animation graphs,
 * decoded with Halo's own animation_get_node_orientations. These are frame
 * selectors, not copied animation assets. Unrecognized/custom graphs keep the
 * existing sampler; node/frame counts and live pose stability are checked too.
 * A part's origin can lie beyond the fingers (especially the long rocket tube).
 * The Sniper deliberately retains Test66's accepted sampling path. */
struct vr_reload_grip_profile {
    char const *model, *ammo, *charge, *animation;
    int nodes, frames, frame;
    float max_origin_distance;
};
static struct vr_reload_grip_profile const vr_reload_grip_profiles[] = {
    { "weapons\\assault rifle\\fp\\fp", "frame magazine", "frame ophandle", "first-person reload-full", 42, 87, 40, .18f },
    { "weapons\\pistol\\fp\\fp", "frame magazine", "frame slide", "first-person reload-full", 44, 65, 35, .23f },
    { "weapons\\shotgun\\fp\\fp", "frame bullet", "frame pump", "first-person reload-empty", 41, 12, 6, .18f },
    { "weapons\\rocket launcher\\fp\\fp", "frame tubes", "frame push_bar", "first-person reload-empty", 42, 125, 59, .43f },
};
static struct vr_reload_grip_profile const *vr_reload_grip_profile_for(char const *model)
{
    unsigned i;
    if (!model) return 0;
    for (i = 0; i < sizeof(vr_reload_grip_profiles) / sizeof(vr_reload_grip_profiles[0]); i++)
        if (!strcmp(model, vr_reload_grip_profiles[i].model)) return &vr_reload_grip_profiles[i];
    return 0;
}
#endif
