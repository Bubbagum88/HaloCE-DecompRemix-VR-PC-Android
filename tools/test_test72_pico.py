"""Test72: PICO in the universal VR APK (Quest, PICO, Steam Frame), adapted
from pull request #4 (lucahttp, written against 1.0.16).

- Its binding table is kept; its profile name /interaction_profiles/
  bytedance/pico4s_controller is not a registered profile, so the registered
  ones are suggested instead, each only when the runtime offers the
  extension that defines it (XR_BD_controller_interaction: PICO 4, Neo 3;
  XR_BD_ultra_controller_interaction: PICO 4 Ultra).
- Manifest: PICO's documented pvr.app.type=vr, the PICO VR launch category,
  and the PR's two input keys; not its eye-tracking feature (it can prompt on
  Quest) nor its unverified device list.
- Its host_memory.c change ("try munmap, trust the kernel") is not taken: ours
  already falls back to mincore and smaps when pagemap is hidden, and munmap
  unmaps live pages without error.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
host = read("port/android/host/host_xr.c")
manifest = read("port/android/app/src/vr/AndroidManifest.xml")
memory = read("port/android/host/host_memory.c")
profiles = json.loads(read("tools/openxr_profiles.json"))["profiles"]

# the profiles, by their registered names and their extensions
assert "pico4s_controller" not in host
for profile, extension in (("bytedance/pico4_controller", "XR_BD_controller_interaction"),
                           ("bytedance/pico_neo3_controller", "XR_BD_controller_interaction"),
                           ("bytedance/pico_ultra_controller_bd", "XR_BD_ultra_controller_interaction")):
    assert extension in profiles["/interaction_profiles/" + profile]["requires"], profile
    assert '"/interaction_profiles/%s", pico' % profile in host, profile
assert '#define BD_CONTROLLER_EXTENSION "XR_BD_controller_interaction"' in host
assert '#define BD_ULTRA_CONTROLLER_EXTENSION "XR_BD_ultra_controller_interaction"' in host
for flag, macro in (("bd_controller", "BD_CONTROLLER_EXTENSION"), ("bd_ultra_controller", "BD_ULTRA_CONTROLLER_EXTENSION")):
    assert "if (!strcmp(available[index].extensionName, %s))\n\t\t\txr.%s = 1;" % (macro, flag) in host
    assert "if (xr.%s)\n\t\textensions[count++] = %s;" % (flag, macro) in host
# suggested only with their extension; Quest's, Index's and the Frame's as before
suggestions = host[host.index('suggest("/interaction_profiles/oculus/touch_controller"'):host.index("attach.countActionSets")]
assert suggestions.index("if (xr.bd_controller)") < suggestions.index("pico4_controller")
assert suggestions.index("if (xr.bd_ultra_controller)") < suggestions.index("pico_ultra_controller_bd")
assert 'if (xr.frame_controller)\n\t\tsuggest("/interaction_profiles/valve/frame_controller_valve"' in host
assert "const char *extensions[12];" in host  # room for every optional extension at once

# the manifest: one APK for every headset
for needle in ('android:name="pvr.app.type"\n            android:value="vr"', 'android:name="pvr.app.inputType"',
               'android:name="pvr.app.handtrackingSupport"\n            android:value="0"',
               '<category android:name="com.picovr.intent.category.VR" />',
               '<category android:name="com.oculus.intent.category.VR" />',
               '<category android:name="org.khronos.openxr.intent.category.IMMERSIVE_HMD" />',
               'android:value="quest|quest2|questpro|quest3|quest3s"'):
    assert needle in manifest, needle
for absent in ("oculus.software.eye_tracking", "enable_shared_context", "pvr.supportedDevices"):
    assert absent not in manifest, absent

# the PR's memory change is not taken: the careful fallback stays
assert "trying mincore/smaps" in memory and "_range_unknown" in memory
assert "trusting the kernel" not in memory
print("PASS: Test72 PICO: registered PICO 4 / Neo 3 / 4 Ultra profiles behind their extensions, manifest entries, "
      "PR #4's memory change left out")
