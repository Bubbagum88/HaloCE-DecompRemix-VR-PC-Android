"""Test production arm IK reach clamping and guard against bone-length scaling."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "port/linux/game/vr_render.c").read_text()
solver_start = source.index("static void vr_solve_arm(")
solver_brace = source.index("{", solver_start)
solver_end = solver_brace + 1
depth = 1
while depth:
    depth += (source[solver_end] == "{") - (source[solver_end] == "}")
    solver_end += 1
solver = source[solver_start:solver_end]
assert '#include "vr_arm_ik_math.h"' in source
assert "vr_arm_ik_reach_bounds(" in solver
assert "vr_arm_ik_clamp_distance(" in solver
assert "upper_length *=" not in solver
assert "fore_length *=" not in solver
assert "stretch" not in solver
assert "compress" not in solver
assert "MIN(travel, 0.08f * vr_units_per_metre())" in solver

code = r'''
#include <assert.h>
#include <math.h>
#include "port/linux/game/vr_arm_ik_math.h"
int main(void) {
    float minimum, maximum;
    assert(vr_arm_ik_reach_bounds(0.27f, 0.25f, 1, &minimum, &maximum));
    assert(maximum == 0.52f);
    assert(minimum > 0.0f && minimum < maximum);
    assert(fabsf(vr_arm_ik_clamp_distance(0.80f, minimum, maximum) - maximum) < 1e-6f);
    assert(fabsf(vr_arm_ik_clamp_distance(minimum * 0.4f, minimum, maximum) - minimum) < 1e-6f);
    assert(fabsf(vr_arm_ik_clamp_distance(0.31f, minimum, maximum) - 0.31f) < 1e-6f);
    assert(vr_arm_ik_reach_bounds(0.30f, 0.20f, 0, &minimum, &maximum));
    assert(fabsf(minimum - 0.101f) < 1e-6f && fabsf(maximum - 0.50f) < 1e-6f);
    assert(!vr_arm_ik_reach_bounds(NAN, 0.2f, 1, &minimum, &maximum));
    assert(!vr_arm_ik_reach_bounds(-0.1f, 0.2f, 1, &minimum, &maximum));
    assert(vr_arm_ik_clamp_distance(NAN, 0.1f, 0.5f) == 0.0f);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp) / "arm.c"
    exe = Path(tmp) / "arm"
    c.write_text(code)
    subprocess.run(
        ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
         "-I", str(ROOT), str(c), "-lm", "-o", str(exe)], check=True
    )
    subprocess.run([str(exe)], check=True)
print("arm IK keeps authored bone lengths and clamps wrist reach (ASan/UBSan)")
