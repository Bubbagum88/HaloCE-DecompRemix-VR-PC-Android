"""Verify a refused weapon drop cannot leave the gun invisible and unheld."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
frame = (ROOT / "port/linux/src/vr_frame.c").read_text()
holster = (ROOT / "port/linux/game/vr_holster_math.h").read_text()
assert '#include "../game/vr_hand_pending_math.h"' in frame
assert "vr_hand_pending_timeout_state(pending" in frame
assert "vr_holster_forget(vr.holster_weapon, weapon_index)" in frame
assert "vr.gun_held = restored == HAND_HELD" in frame
assert "weapon drop/stow timed out" in frame
assert "static inline void vr_holster_forget" in holster

code = r'''
#include <assert.h>
#include "port/linux/game/vr_hand_pending_math.h"
#include "port/linux/game/vr_holster_math.h"
enum { LOOSE, HELD, EMPTY };
int main(void) {
    long slots[VR_HOLSTER_SLOT_COUNT] = {44, 41, -1, 43};
    /* Drop/stow didn't change the selected weapon: restore the held pose. */
    assert(vr_hand_pending_timeout_state(EMPTY, EMPTY, 41, EMPTY, HELD) == HELD);
    vr_holster_forget(slots, 41);
    assert(slots[1] == -1 && slots[0] == 44 && slots[3] == 43);
    /* A real switch / drop remains governed by the observed inventory state. */
    assert(vr_hand_pending_timeout_state(EMPTY, EMPTY, -1, EMPTY, HELD) == EMPTY);
    assert(vr_hand_pending_timeout_state(HELD, LOOSE, 41, EMPTY, HELD) == LOOSE);
    vr_holster_forget(slots, 99);
    assert(slots[0] == 44 && slots[3] == 43);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="vr-pending-release-") as temp:
    c = Path(temp) / "check.c"
    binary = Path(temp) / "check"
    c.write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-I", str(ROOT),
                    str(c), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("PASS: failed weapon release restores the active held weapon and removes stale holster ownership")
