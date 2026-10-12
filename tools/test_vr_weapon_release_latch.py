"""Regression tests for physical-weapon release edges behind hand owners."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
header = ROOT / "port/linux/src/vr_weapon_release_latch.h"
source = (ROOT / "port/linux/src/vr_frame.c").read_text()
assert '#include "vr_weapon_release_latch.h"' in source
assert "vr_weapon_release_latch_step(&vr.weapon_release" in source
assert "weapon_release == VR_WEAPON_RELEASE_READY" in source
assert "vr_weapon_release_latch_reset(&vr.weapon_release)" in source
release = source[source.index("else if (weapon_release == VR_WEAPON_RELEASE_READY"):
                 source.index("/* the off hand's grip", source.index("else if (weapon_release == VR_WEAPON_RELEASE_READY"))]
assert "if (vr.in_holster)" in release and "VR_ACTION_SWITCH_WEAPON" in release
assert "VR_ACTION_DROP_WEAPON" in release and "the gun let go: it falls" in release

code = r'''
#include <assert.h>
#include "port/linux/src/vr_weapon_release_latch.h"

int main(void) {
    struct vr_weapon_release_latch latch = {-1, 0};
    const long weapon = -431815724L; /* Valid signed datum recorded in the user log. */
    /* An ordinary release immediately drops/stows/transfers exactly once. */
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 1, 0)
        == VR_WEAPON_RELEASE_READY);
    assert(!latch.pending);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE);

    /* A vehicle/world/NPC interaction may own the weapon hand at the release
       edge. Preserve it until that owner clears, then emit one release. */
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 1, 1)
        == VR_WEAPON_RELEASE_DEFERRED);
    assert(latch.pending && latch.weapon == weapon);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 0, 1)
        == VR_WEAPON_RELEASE_NONE);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_READY);
    assert(!latch.pending);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE);

    /* Regrip cancels the pending release; no late drop after interaction. */
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 1, 1)
        == VR_WEAPON_RELEASE_DEFERRED);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 1, 1, 0, 0)
        == VR_WEAPON_RELEASE_NONE && !latch.pending);

    /* Tracking/focus/recenter loss or a weapon change abandons the edge. It
       must never create an unintentional drop when the hand returns. */
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 1, 1)
        == VR_WEAPON_RELEASE_DEFERRED);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 0, 0, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE && !latch.pending);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 1, 1)
        == VR_WEAPON_RELEASE_DEFERRED);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 1, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE && !latch.pending);
    assert(vr_weapon_release_latch_step(&latch, weapon, 1, 1, 1, 0, 0, 0, 1, 1)
        == VR_WEAPON_RELEASE_DEFERRED);
    assert(vr_weapon_release_latch_step(&latch, -431750187L, 1, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE && !latch.pending);
    assert(vr_weapon_release_latch_step(&latch, -431750187L, 1, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE);

    /* Solo/online physical-setting gate off always clears the pending edge. */
    assert(vr_weapon_release_latch_step(&latch, -431750187L, 1, 1, 1, 0, 0, 0, 1, 1)
        == VR_WEAPON_RELEASE_DEFERRED);
    assert(vr_weapon_release_latch_step(&latch, -431750187L, 0, 1, 1, 0, 0, 0, 0, 0)
        == VR_WEAPON_RELEASE_NONE && !latch.pending);
    assert(vr_weapon_release_latch_step(&latch, -1, 1, 1, 1, 0, 0, 0, 1, 0)
        == VR_WEAPON_RELEASE_NONE && !latch.pending);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c_file = Path(tmp) / "latch.c"
    binary = Path(tmp) / "latch"
    c_file.write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-I", str(ROOT),
                    str(c_file), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("physical weapon release latch: owner deferral, exactly-once release and safety cancellation passed")
