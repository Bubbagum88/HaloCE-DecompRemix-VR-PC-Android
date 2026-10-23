"""Every OpenXR binding the hosts suggest is a path its interaction profile
defines (tools/openxr_profiles.json, from the Khronos registry and vendor
documentation), and every profile is suggested only with what enables it.

A single path a profile lacks makes the runtime discard the whole suggestion
for that profile (XR_ERROR_PATH_UNSUPPORTED): that controller then gives no
input at all. Pull request #4's PICO table had such a path
(/input/thumbstick/touch on a profile that, in its own words, has none) and a
profile name no runtime knows (bytedance/pico4s_controller); this check keeps
such tables out.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = json.loads((ROOT / "tools/openxr_profiles.json").read_text(encoding="utf-8"))["profiles"]
# the hosts that suggest bindings, and the shared tables they suggest (Test72)
HOSTS = [ROOT / "port/android/host/host_xr.c"]
SHARED = ROOT / "port/android/include/halo_xr_bindings.h"


def tables(source):
    """name -> [(action, user path, subpath)] for each `static const struct binding NAME[] = {...};`"""
    found = {}
    for match in re.finditer(r"static const struct binding (\w+)\[\]\s*=\s*\{(.*?)\n\t?\};", source, re.S):
        name, body = match.groups()
        entries = []
        # the POSES(hand) macro: grip, aim and haptic of that hand
        for hand in re.findall(r'POSES\("(left|right)"\)', body):
            for sub in ("/input/grip/pose", "/input/aim/pose", "/output/haptic"):
                entries.append(("pose", "/user/hand/" + hand, sub))
        for action, path in re.findall(r'\{\s*(_action_\w+),\s*"([^"]+)"\s*\}', body):
            user = "/".join(path.split("/")[:4])
            entries.append((action, user, path[len(user):]))
        found[name] = entries
    return found


checked = 0
for host in HOSTS:
    source = host.read_text(encoding="utf-8")
    bindings = tables(source)
    bindings.update(tables(SHARED.read_text(encoding="utf-8")))
    suggestions = re.findall(r'suggest\("(/interaction_profiles/[^"]+)",\s*(\w+),', source)
    # Test73: a table with its fingers' touches (suggest_pair): both are checked, each against the profile
    pairs = re.findall(r'suggest_pair\("(/interaction_profiles/[^"]+)",\s*(\w+),\s*sizeof\(\2\)\s*/\s*sizeof\(\2\[0\]\),'
                       r'\s*(\w+),\s*sizeof\(\3\)\s*/\s*sizeof\(\3\[0\]\)\);', source)
    assert len(pairs) == source.count("\tsuggest_pair(") == 2, pairs
    for profile, table, fingers in pairs:
        suggestions += [(profile, table), (profile, fingers)]
        # a refused pair falls back to the table alone
        assert fingers.endswith("_fingers") and table + "_fingers" == fingers, (table, fingers)
    assert "if (XR_SUCCEEDED(suggest(profile, both, count + finger_count)))\n\t\t\treturn;" in source
    assert source.count("suggest(profile, bindings, count);") == 1
    assert suggestions, host
    for profile, table in suggestions:
        assert profile in SNAPSHOT, profile + " is not a known interaction profile (registry or vendor documentation)"
        assert table in bindings, table
        defined = SNAPSHOT[profile]["paths"]
        for action, user, sub in bindings[table]:
            assert user in defined, (profile, user)
            assert sub in defined[user], "%s: %s%s (%s) is not in the profile" % (profile, user, sub, action)
            checked += 1
        # its enabling extension is asked for before the suggestion (core 1.0 needs none)
        needs = [r for r in SNAPSHOT[profile]["requires"] if not r.startswith("XR_VERSION_")]
        core = "XR_VERSION_1_0" in SNAPSHOT[profile]["requires"]
        if needs and not core:
            assert any(n in source or n.upper() + "_EXTENSION_NAME" in source for n in needs), (profile, needs)
print("PASS: %d OpenXR bindings in %d suggested profiles are paths their profiles define" % (checked, len(suggestions)))
