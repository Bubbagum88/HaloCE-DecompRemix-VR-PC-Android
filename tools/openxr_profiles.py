"""OpenXR interaction profiles from the Khronos registry (xr.xml): which paths
each profile defines, and what enables it (a core version or an extension).

``python3 tools/openxr_profiles.py path/to/xr.xml`` writes
tools/openxr_profiles.json, which test_openxr_bindings.py checks every binding
table of the hosts against: a single path a profile does not define makes the
runtime discard that profile's whole suggestion (OpenXR 1.0, 6.4,
xrSuggestInteractionProfileBindings: XR_ERROR_PATH_UNSUPPORTED), which leaves
a controller with no input at all. The registry is Apache-2.0 (Khronos);
the snapshot keeps only profile names, paths and their requirements.

Vendor profiles that are not (yet) in the registry are added from their
vendor's documentation (VENDOR_PROFILES), each with its source.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).with_name("openxr_profiles.json")

# Profiles documented by their vendors but not in the Khronos registry.
VENDOR_PROFILES = {
    # Valve, Steamworks: Steam Frame Input (partner.steamgames.com/doc/steamhardware/steamframe/input)
    "/interaction_profiles/valve/frame_controller_valve": {
        "requires": ["XR_VALVE_frame_controller_interaction"],
        "source": "Steamworks documentation, Steam Frame Input",
        "paths": {
            "/user/hand/right": ["/input/a/click", "/input/a/touch", "/input/b/click", "/input/b/touch",
                                 "/input/x/click", "/input/x/touch", "/input/y/click", "/input/y/touch",
                                 "/input/menu/click", "/input/menu/touch", "/input/system/click", "/input/system/touch",
                                 "/input/bumper/click", "/input/bumper/touch",
                                 "/input/squeeze/click", "/input/squeeze/touch", "/input/squeeze/value",
                                 "/input/trigger/click", "/input/trigger/touch", "/input/trigger/value",
                                 "/input/thumbstick", "/input/thumbstick/x", "/input/thumbstick/y",
                                 "/input/thumbstick/click", "/input/thumbstick/touch",
                                 "/input/grip/pose", "/input/aim/pose", "/output/haptic"],
            "/user/hand/left": ["/input/dpad_up/click", "/input/dpad_up/touch", "/input/dpad_down/click",
                                "/input/dpad_down/touch", "/input/dpad_left/click", "/input/dpad_left/touch",
                                "/input/dpad_right/click", "/input/dpad_right/touch",
                                "/input/view/click", "/input/view/touch", "/input/system/click", "/input/system/touch",
                                "/input/bumper/click", "/input/bumper/touch",
                                "/input/squeeze/click", "/input/squeeze/touch", "/input/squeeze/value",
                                "/input/trigger/click", "/input/trigger/touch", "/input/trigger/value",
                                "/input/thumbstick", "/input/thumbstick/x", "/input/thumbstick/y",
                                "/input/thumbstick/click", "/input/thumbstick/touch",
                                "/input/grip/pose", "/input/aim/pose", "/output/haptic"],
        },
    },
}


def profiles_from(registry):
    root = ET.parse(registry).getroot()
    profiles = {}
    for definition in root.iter("interaction_profile"):
        name = definition.get("name")
        users = [user.get("path") for user in definition.findall("user_path")]
        if not users:
            continue  # a reference inside <require>, not a definition
        paths = {user: set() for user in users}
        for component in definition.findall("component"):
            for user in ([component.get("user_path")] if component.get("user_path") else users):
                paths[user].add(component.get("subpath"))
        profiles[name] = {"requires": set(), "paths": paths, "added": []}

    # what enables each: the extensions or core versions whose <require> names it
    def walk(owner, element):
        for require in element.iter("require"):
            for reference in require.findall("interaction_profile"):
                if reference.get("name") in profiles:
                    profiles[reference.get("name")]["requires"].add(owner)
            for extend in require.findall("extend"):
                profile = extend.get("interaction_profile_path")
                if profile not in profiles:
                    continue
                for component in extend.findall("component"):
                    users = [component.get("user_path")] if component.get("user_path") else list(profiles[profile]["paths"])
                    for user in users:
                        profiles[profile]["added"].append({"by": owner, "user": user, "path": component.get("subpath")})

    for feature in root.iter("feature"):
        walk(feature.get("name"), feature)
    for extension in root.iter("extension"):
        walk(extension.get("name"), extension)
    return profiles


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    profiles = profiles_from(argv[1])
    snapshot = {}
    for name, profile in sorted(profiles.items()):
        snapshot[name] = {
            "requires": sorted(profile["requires"]),
            "paths": {user: sorted(paths) for user, paths in sorted(profile["paths"].items())},
            "added": sorted(profile["added"], key=lambda a: (a["by"], a["user"], a["path"])),
        }
    for name, profile in VENDOR_PROFILES.items():
        assert name not in snapshot, name + " is in the registry now: drop it from VENDOR_PROFILES"
        snapshot[name] = {"requires": profile["requires"], "source": profile["source"],
                          "paths": {user: sorted(paths) for user, paths in profile["paths"].items()}, "added": []}
    revision = re.search(rb'XR_CURRENT_API_VERSION XR_MAKE_VERSION\((\d+), (\d+), (\d+)\)', Path(argv[1]).read_bytes())
    document = {"registry": "KhronosGroup/OpenXR-SDK-Source specification/registry/xr.xml (Apache-2.0)",
                "version": ".".join(x.decode() for x in revision.groups()) if revision else None,
                "profiles": snapshot}
    OUT.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT, len(snapshot), "profiles, OpenXR", document["version"])


if __name__ == "__main__":
    main(sys.argv)
