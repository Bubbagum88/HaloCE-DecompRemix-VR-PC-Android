/*
WIN32_XR_HOST.H

Test72: what port/android/host/host_xr.c asks of its host when it builds the
Windows PCVR game (halo-vr.exe, tools/windows_build.py): the log, and the
Android host's two debugging hooks (port/windows/src/win32_xr.c). The
structures the game and the host share are halo_android_abi.h's, the same
on both platforms (their sizes are asserted there).
*/

#ifndef WIN32_XR_HOST_H
#define WIN32_XR_HOST_H

#include <stdint.h>
#include "halo_android_abi.h"

/* port/android/host/host.h's priorities */
#define HOST_LOG_INFO 4
#define HOST_LOG_WARN 5
#define HOST_LOG_ERROR 6

void host_logf(int priority, const char *format, ...) __attribute__((format(printf, 2, 3)));
/* the Android host's hang watchdog and GPU trace hooks: nothing on Windows */
void host_debug_frame_shown(void);
int host_gl_quiet_trace_markers(void);

#endif
