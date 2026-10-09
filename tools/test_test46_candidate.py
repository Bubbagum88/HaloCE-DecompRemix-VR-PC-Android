"""Guard Test46's candidate identity and the issues found during final audit."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


gradle = read("port/android/app/build.gradle")
assert "versionCode Math.max(57, buildNumber)" in gradle
assert '"1.0.27-test46"' in gradle
frame = read("port/linux/src/vr_frame.c")
identity = (
    "HaloCE Quest test46 candidate 1.0.27-test46 code57 "
    "(OpenCE Build 157 base / network 24; selected Build167 compatibility "
    "fixes and host-relayed voice; contact-driven NPC/ally interaction; "
    "bounded vehicle lifting; persistent same-map magazine visuals; prior "
    "launcher, calibration, reload, climbing, VR and Android work retained; "
    "device acceptance pending)"
)
assert identity in frame
package = read("tools/package-quest.py")
assert identity.encode("ascii") in package.encode("utf-8")
assert "57 if candidate_at_least(args.label, 46)" in package
assert '"TEST46-DELIVERY-STATUS.md"' in package
assert '"TEST46-VOICE-CHAT.md"' in package

# The old source-only record is deliberately historical; the active Test46
# disposition must say that the two follow-ups are included in its candidate.
requirements = read("docs/TEST46-REQUIREMENT-DISPOSITION.md")
assert "**Included in the Test46 source and candidate build.**" in requirements
assert "Source-only follow-up; not present in the Test46 APK hashes" not in requirements
for marker in ("Whole-vehicle physical lifting", "Persistent discarded magazines",
               "Selected Build167 voice chat", "Ragdoll-on-death and retention",
               "Automatic recovery of fallen mission actors"):
    assert marker in requirements

rescue = read("port/linux/game/vr_npc_rescue.c")
assert "check.script_state_resumable" in rescue
assert "check.no_script_ownership" not in rescue
rescue_test = read("tools/test_vr_npc_rescue.py")
assert "check.no_script_ownership" in rescue_test

manifest = read("port/android/app/src/main/AndroidManifest.xml")
assert "android.permission.RECORD_AUDIO" in manifest
voice_menu = read("port/linux/game/vr_menu.c")
assert '"MICROPHONE", "audio.voice_chat"' in voice_menu
assert '"VOICE VOLUME", "audio.voice_volume"' in voice_menu
guide = read("docs/TEST46-PLAYER-NOTES.md").lower()
for marker in ("1.0.27-test46", "build167 voice chat", "microphone permission",
               "voice volume", "same-map checkpoint", "lift vehicles", "npc rescue"):
    assert marker in guide, marker

print("PASS: Test46 version/signature identity, packaging gates, rescue predicate, retained source features, and Build167 voice controls are aligned")
