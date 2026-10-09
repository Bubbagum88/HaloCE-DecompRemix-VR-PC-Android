"""Bounded finger contact search and contact-entry feedback, production math.

Host checks do not substitute for headset comfort/performance testing.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/test38-contact"
OUT.mkdir(parents=True, exist_ok=True)
source = r'''
#include <assert.h>
#include <math.h>
#include "port/linux/game/vr_contact_math.h"
struct query { int calls, mode; };
static float clearance(void *opaque, int direction, float t) {
    struct query *q = opaque;
    assert(t > 0 && t <= 1); q->calls++;
    if (q->mode == 0) return direction == -1 && t >= .3f && t <= .7f ? 1 : .2f;
    if (q->mode == 1) return direction == 1 && t >= .5f ? 1 : .2f;
    if (q->mode == 2) return NAN;
    if (q->mode == 3) return t >= .2f ? 1 : .2f;
    return .2f + .5f * (1 - fabsf(t - .6666667f));
}
int main(void) {
    struct query q = {0}; int direction = 0;
    float t = vr_contact_search(clearance, &q, 0, .2f, &direction);
    assert(direction == -1 && t >= .3f && t <= .34f && q.calls <= 8);
    q = (struct query){0, 1};
    t = vr_contact_search(clearance, &q, -1, .2f, &direction);
    assert(direction == 1 && t >= .5f && t <= .55f && q.calls <= 8);
    q = (struct query){0, 2};
    t = vr_contact_search(clearance, &q, 1, .2f, &direction);
    assert(isfinite(t) && t >= 0 && t <= 1 && q.calls <= 8);
    q = (struct query){0, 3};
    t = vr_contact_search(clearance, &q, 1, .2f, &direction);
    assert(direction == 1 && t >= .2f && t < .22f && q.calls <= 8);
    q = (struct query){0, 4};
    t = vr_contact_search(clearance, &q, 1, .2f, &direction);
    assert(fabsf(t - 2.f/3) < .001f && q.calls <= 8);
    struct vr_contact_pulse_state p = {0};
    assert(vr_contact_pulse(&p, 1, 1));
    assert(!vr_contact_pulse(&p, 1, 1)); /* second eye */
    for (int i = 1; i <= 90; ++i) assert(!vr_contact_pulse(&p, 1 + i / 90., 1));
    assert(!vr_contact_pulse(&p, 2.01, 0));
    assert(!vr_contact_pulse(&p, 2.02, 1)); /* contact noise */
    assert(!vr_contact_pulse(&p, 2.03, 0));
    assert(!vr_contact_pulse(&p, 2.08, 0));
    assert(vr_contact_pulse(&p, 2.12, 1));
    assert(!vr_contact_pulse(&p, NAN, 1));
    assert(vr_contact_pulse(&p, 3, 1));
    assert(vr_contact_pulse(&p, .1, 1)); /* reset timeline */
    return 0;
}
'''
p = OUT / "contact.c"
p.write_text(source)
subprocess.run(["clang", "-std=c11", "-O1", "-Wall", "-Wextra", "-Werror",
                "-fsanitize=address,undefined", "-I", str(ROOT), str(p), "-lm",
                "-o", str(OUT / "contact")], check=True)
subprocess.run([str(OUT / "contact")], check=True)
render = (ROOT / "port/linux/game/vr_render.c").read_text()
assert 'vr_contact_search(vr_finger_query' in render
assert 'vr_hand_contact_feedback(controller, unit, graph' in render
assert 'last_graph[controller] != graph' in render
assert 'else if (contacts && action.weight[side] == 0) vr_haptic' not in render
print("Test38 bounded contact search and haptic entry checks passed")
