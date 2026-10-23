"""Test72: the Windows builds (flat halo.exe and PCVR halo-vr.exe), as built
and run on this project's Windows machine.

- The fork's tree builds for Windows again: the port's expat and zlib on its
  include path and compiled (menu files, HUD, post-processing, updater).
- It runs: two halts its first start found are fixed. blood_update read the
  game time while a map's precache drew the loading screen, before there is
  one (every build; the release builds only logged it). And the weak
  placeholder of light_cluster_partition (halo_linker_common.c) kept the
  January image's 12 bytes: the Windows link let it stand for the port's
  24-byte partition, whose own fields overwrote light_data, which the
  first map's dispose then found bad (the Android image was right: 24).
- PCVR: halo-vr.exe, the same game with HALO_VR on the shared OpenXR host
  (port/android/host/host_xr.c on WGL and desktop OpenGL), its glue
  (win32_xr.c), the Khronos loader 1.1.63 checked by SHA-256, beside the
  flat game in one folder with its own config-vr.toml and halo-vr.log.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
build = read("tools/windows_build.py")
host = read("port/android/host/host_xr.c")
glue = read("port/windows/src/win32_xr.c")
config = read("port/linux/src/port_config.c")
posix = read("port/windows/src/win32_posix.c")
common = read("port/linux/src/halo_linker_common.c")
blood = read("port/linux/game/blood.c")
partition = read("source/structures/cluster_partitions.h")

# --- the flat build's third-party sources
assert "EXPAT_DIR, EXPAT_SOURCES, ZLIB_DIR, ZLIB_SOURCES, ZLIB_DEFINES" in build
assert 'f"-I{EXPAT_DIR}", f"-I{ZLIB_DIR}",' in build and '"random_rand_s.c"' in build
assert "#include <stdio.h>" in read("port/linux/src/voice_audio.c")

# --- the two halts
body = blood[blood.index("void blood_update(\n\tvoid)\n{"):]
body = body[:body.index("\n}\n")]
assert body.index("if (!game_time_initialized())\n\t\treturn;") < body.index("now = game_time_get();")
fields = re.search(r"struct cluster_partition\n\{(.*?)\n\};", partition, re.S).group(1)
members = re.findall(r"^\t[^/\n]*?(\w+);", fields, re.M)
assert len(members) == 6, members  # three pointers, two port pointers, a count: 24 bytes on 32-bit builds
assert "HALO_COMMON(light_cluster_partition, 24);" in common
assert "HALO_COMMON(light_cluster_partition, 12);" not in common

# --- PCVR: one host for both platforms, Android's lines intact
for needle in ("#ifdef _WIN32\n/* Test72: the Windows PCVR build", "#define XR_USE_PLATFORM_WIN32",
               "#define XR_USE_GRAPHICS_API_OPENGL\n#else", "#include <unknwn.h>",
               "XrGraphicsBindingOpenGLWin32KHR binding", "binding.hDC = wglGetCurrentDC();",
               "XrSwapchainImageOpenGLKHR images[HALO_XR_MAXIMUM_IMAGES];",
               "extensions[count++] = XR_KHR_OPENGL_ENABLE_EXTENSION_NAME;",
               "the runtime has no %s; choose SteamVR or the Meta runtime"):
    assert needle in host, needle
for android in ("XrGraphicsBindingOpenGLESAndroidKHR binding", "XR_TYPE_SWAPCHAIN_IMAGE_OPENGL_ES_KHR",
                "extensions[count++] = XR_KHR_ANDROID_CREATE_INSTANCE_EXTENSION_NAME;", "SDL_GetAndroidJNIEnv()",
                "#define XR_USE_PLATFORM_ANDROID", "#define XR_USE_GRAPHICS_API_OPENGL_ES"):
    assert android in host, android
assert "#ifdef HALO_VR" in glue and "int host_gl_has_extension(const char *name)" in glue
assert "void host_logf(int priority, const char *format, ...)" in glue
assert 'OPENXR_VERSION = "1.1.63"' in build
assert 'OPENXR_VERSION = "1.1.63"' in read("tools/android_build.py")  # the same loader release on both
assert re.search(r'OPENXR_SHA256 = "[0-9a-f]{64}"', build)
assert 'n.build(outputs="windows_vr", rule="phony", inputs=[vr_output, vr_sdl, vr_loader])' in build
assert '"-DHALO_VR=1"' in build and "[Path(\"port/android/host/host_xr.c\")]" in build
assert "#elif defined(_WIN32) && defined(HALO_VR)\n/* Test72: the Windows PCVR build (halo-vr.exe): VR settings and Windows ones */\n#define CONFIG_PLATFORM (_platform_windows | _platform_vr)" in config
# the line editors, which VR's migration uses; since the PC VR fixes (docs/HANDOFF-2026-10-18.md item 1) every
# build's but the web's, the desktop's Safe-geometry migration among them (tools/test_test32_geometry.py)
assert config.count("#if !defined(HALO_WEB)\n#define CONFIG_GEOMETRY_MIGRATION 1") == 1
assert '#define GEOMETRY_REVISION_KEY "desktop_geometry_revision"' in config
assert 'snprintf(path, size, "%sconfig-vr.toml", base ? base : "");' in config
assert 'static const char name[] = "halo-vr.log";' in posix
print("PASS: Test72 Windows: flat build (expat/zlib), its two start-up halts fixed (blood's game time, the 24-byte "
      "light partition), PCVR halo-vr.exe on the shared OpenXR host, one folder with its own settings and log")
