"""Test the solo-only native active-garbage thresholds used for corpse retention."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
objects = (ROOT / "source/objects/objects.c").read_text(encoding="utf-8-sig")
header = ROOT / "source/objects/active_garbage_limit_math.h"
config = (ROOT / "port/linux/src/port_config.c").read_text(encoding="utf-8-sig")
menu = (ROOT / "port/linux/game/vr_menu.c").read_text(encoding="utf-8-sig")

assert '#include "active_garbage_limit_math.h"' in objects
assert 'config_integer("vr.ragdoll_retention")' in objects
assert "game_connection() == _game_connection_local && !game_engine_running()" in objects
assert '"vr.ragdoll_retention", _config_integer, "75"' in config
assert '"BODY RETENTION", "vr.ragdoll_retention"' in menu

code = r'''
#include <assert.h>
#include "source/objects/active_garbage_limit_math.h"
int main(void) {
    /* OpenCE stock thresholds remain 50 trigger / 30 target when disabled. */
    assert(objects_vr_active_garbage_limit(50, 0, 0, 1) == 50);
    assert(objects_vr_active_garbage_limit(30, 0, 1, 1) == 30);
    /* New solo default raises retention moderately; optional level is bounded. */
    assert(objects_vr_active_garbage_limit(50, 75, 0, 1) == 75);
    assert(objects_vr_active_garbage_limit(30, 75, 1, 1) == 45);
    assert(objects_vr_active_garbage_limit(50, 100, 0, 1) == 100);
    assert(objects_vr_active_garbage_limit(30, 100, 1, 1) == 60);
    /* Network, local multiplayer, replay, or any non-solo context uses stock. */
    assert(objects_vr_active_garbage_limit(50, 100, 0, 0) == 50);
    assert(objects_vr_active_garbage_limit(30, 100, 1, 0) == 30);
    /* Invalid hand-edited values fail closed to upstream behavior. */
    assert(objects_vr_active_garbage_limit(50, 125, 0, 1) == 50);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as temp:
    c = Path(temp) / "retention.c"
    exe = Path(temp) / "retention"
    c.write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-I", str(ROOT),
                    str(c), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print("VR corpse retention: 75/45 default and 100/60 option are solo-only; stock 50/30 retained online/MP")
