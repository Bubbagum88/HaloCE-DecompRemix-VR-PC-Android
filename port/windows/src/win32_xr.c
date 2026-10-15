/*
WIN32_XR.C

Test72: the Windows PCVR game's host glue (halo-vr.exe; tools/windows_build.py).
The OpenXR host itself is the Android one, port/android/host/host_xr.c, built
here on WGL and desktop OpenGL; this gives it the log, and gives the game
(port/linux/src/vr_frame.c) the one other host call it makes, the GL
extension query. Built only into halo-vr.exe.
*/

#ifdef HALO_VR

#include <stdarg.h>
#include <stdio.h>

#include <SDL3/SDL.h>

#include "win32_xr_host.h"

void platform_log(const char *format, ...);

void host_logf(int priority, const char *format, ...)
{
	char text[1024];
	va_list arguments;

	va_start(arguments, format);
	vsnprintf(text, sizeof(text), format, arguments);
	va_end(arguments);
	platform_log("%s%s", priority >= HOST_LOG_ERROR ? "error: " : priority == HOST_LOG_WARN ? "warning: " : "", text);
}

void host_debug_frame_shown(void)
{
}

int host_gl_quiet_trace_markers(void)
{
	return 0;
}

/* the game's current context (SDL's) */
int host_gl_has_extension(const char *name)
{
	return name && SDL_GL_ExtensionSupported(name) ? 1 : 0;
}

#endif
