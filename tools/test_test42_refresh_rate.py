"""Exercise production Quest refresh selection, including reset to runtime AUTO."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def function(source: str, name: str) -> str:
    match = re.search(r"^(?:static )?[\w *]+\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", source, re.M)
    assert match, name
    end = match.end()
    depth = 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end] + "\n"


host = (ROOT / "port/android/host/host_xr.c").read_text(encoding="utf-8")
frame = (ROOT / "port/linux/src/vr_frame.c").read_text(encoding="utf-8")
menu = (ROOT / "port/linux/game/vr_menu.c").read_text(encoding="utf-8")
config = (ROOT / "port/linux/src/port_config.c").read_text(encoding="utf-8")

assert '{ "REFRESH", "vr.refresh_rate", _vr_setting_real, 5, { { "AUTO", "0" }' in menu
assert '"vr.refresh_rate", _config_real, "72.0"' in config
assert 'hertz >= 0.0 && hertz != asked' in function(frame, "choose_refresh_rate")

test = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
typedef int XrResult;
typedef void (*PFN_xrVoidFunction)(void);
typedef XrResult (*PFN_xrEnumerateDisplayRefreshRatesFB)(int, uint32_t, uint32_t *, float *);
typedef XrResult (*PFN_xrRequestDisplayRefreshRateFB)(int, float);
#define XR_FAILED(r) ((r) < 0)
#define HOST_LOG_WARN 1
#define HOST_LOG_INFO 2
struct { int initialized, refresh_rate_extension, instance, session, refresh_misses; float refresh_rate; } xr = {1, 1, 4, 5, 7, 72.0f};
static float current_setting;
static float requested[16];
static int requests, enumerations;
static float offered[] = {72.0f, 80.0f, 90.0f, 120.0f};
static XrResult fake_enumerate(int session, uint32_t capacity, uint32_t *count, float *rates)
{
    assert(session == 5); enumerations++; *count = 4;
    if (capacity) { assert(capacity >= 4); memcpy(rates, offered, sizeof(offered)); }
    return 0;
}
static XrResult fake_request(int session, float rate)
{
    assert(session == 5); assert(requests < 16); requested[requests++] = rate; return 0;
}
static XrResult xrGetInstanceProcAddr(int instance, const char *name, PFN_xrVoidFunction *function)
{
    assert(instance == 4);
    if (!strcmp(name, "xrRequestDisplayRefreshRateFB")) *function = (PFN_xrVoidFunction)fake_request;
    else if (!strcmp(name, "xrEnumerateDisplayRefreshRatesFB")) *function = (PFN_xrVoidFunction)fake_enumerate;
    else return -1;
    return 0;
}
static int check(XrResult result, const char *name) { (void)name; return result >= 0; }
static void host_logf(int level, const char *format, ...) { (void)level; (void)format; }
static void platform_log(const char *format, ...) { (void)format; }
static double config_real(const char *key) { assert(!strcmp(key, "vr.refresh_rate")); return current_setting; }
'''
test += function(host, "host_xr_set_refresh_rate")
test += function(frame, "choose_refresh_rate")
test += r'''
int main(void)
{
    current_setting = 72; choose_refresh_rate();
    assert(requests == 1 && requested[0] == 72 && xr.refresh_rate == 72);
    current_setting = 120; choose_refresh_rate();
    assert(requests == 2 && requested[1] == 120 && xr.refresh_rate == 120);
    int before_auto_enumeration = enumerations;
    current_setting = 0; choose_refresh_rate();
    assert(requests == 3 && requested[2] == 0 && xr.refresh_rate == 0 && xr.refresh_misses == 0);
    assert(enumerations == before_auto_enumeration); /* 0 is no preference, not an enumerated mode */
    choose_refresh_rate(); assert(requests == 3); /* no per-frame duplicate request */
    current_setting = 80; choose_refresh_rate();
    assert(requests == 4 && requested[3] == 80 && xr.refresh_rate == 80);
    assert(host_xr_set_refresh_rate(-1) == 0 && requests == 4);
    xr.refresh_rate_extension = 0;
    assert(host_xr_set_refresh_rate(0) == 0 && requests == 4);
    puts("PASS: production refresh request, selectable AUTO reset, supported-rate selection, invalid values and extension fallback");
    return 0;
}
'''

with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "refresh.c"
    binary = Path(directory) / "refresh"
    source.write_text(test, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-fsanitize=address,undefined", str(source), "-lm", "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
