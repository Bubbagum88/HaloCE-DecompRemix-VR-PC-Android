"""Focused source-level checks for the OpenCE Build167 voice integration.

This verifies the wiring and safety defaults, not microphone or two-headset
runtime behavior; those checks require a Quest and an actual network lobby.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


config = read("port/linux/src/port_config.c")
assert re.search(r'\{ "audio\.voice_chat",\s*_config_string,\s*"\\"off\\""', config)
assert '"audio.voice_volume", _config_real, "1.0"' in config
assert '"controls.push_to_talk", _config_string, "\\"V\\""' in config
assert re.search(r'\{ "vr\.button_push_to_talk",\s*_config_string,\s*"\\"none\\""', config)

manifest = read("port/android/app/src/main/AndroidManifest.xml")
assert 'android.permission.RECORD_AUDIO' in manifest
host_imports = read("port/android/host_imports.list")
for item in ("host_sdl_get_audio_stream_data", "host_sdl_get_audio_stream_available",
             "host_sdl_destroy_audio_stream"):
    assert item in host_imports
guest = read("port/android/guest/runtime/guest_sdl.c")
host = read("port/android/host/host_sdl.c")
for item in ("SDL_GetAudioStreamData", "SDL_GetAudioStreamAvailable", "SDL_DestroyAudioStream"):
    assert item in guest and item in host

header = read("port/linux/src/sdl_platform.h")
platform = read("port/linux/src/sdl_platform.c")
assert "platform_audio_device(int recording, const char *name)" in header
assert "SDL_AUDIO_DEVICE_DEFAULT_RECORDING" in platform
audio_header = read("port/linux/src/voice_audio.h")
for marker in ("VOICE_AUDIO_MICROPHONE_DEVICE_FAILURE = -2",
               "VOICE_AUDIO_MICROPHONE_PERMISSION_DENIED = -1",
               "VOICE_AUDIO_MICROPHONE_NOT_READY = 0",
               "VOICE_AUDIO_MICROPHONE_READY = 1"):
    assert marker in audio_header
audio = read("port/linux/src/voice_audio.c")
audio_header = read("port/linux/src/voice_audio.h")
assert "platform_audio_device(TRUE, microphone_opening_device)" in audio
open_thread = audio.split("static void *microphone_open_thread", 1)[1].split("static BOOL voice_testing", 1)[0]
mic_control = audio.split("int voice_audio_microphone(int open)", 1)[1].split("int voice_audio_read_frame", 1)[0]
assert "SDL_OpenAudioDeviceStream" in open_thread
permission_gate = mic_control.index("platform_audio_recording_permission()")
thread_start = mic_control.index("pthread_create(&thread, NULL, microphone_open_thread, NULL)")
assert permission_gate < thread_start
assert "if (permission <= 0)\n\t\t\treturn permission < 0 ? VOICE_AUDIO_MICROPHONE_PERMISSION_DENIED : VOICE_AUDIO_MICROPHONE_NOT_READY;" in mic_control
assert "if (open && !microphone && !microphone_opening && !microphone_failed)" in mic_control
assert "if (open && microphone_failed)\n\t\tready = VOICE_AUDIO_MICROPHONE_DEVICE_FAILURE;" in mic_control
assert "microphone_failed = stream == NULL;" in open_thread
assert "microphone_failed = TRUE;" in mic_control
platform_audio = platform.split("/* ---------- audio devices (voice chat's microphone; default on Android) */", 1)[1].split("#ifndef HALO_ANDROID", 1)[1].split("/* ---------- first start without game data", 1)[0]
desktop_audio, android_audio = platform_audio.split("#else", 1)
assert "int platform_audio_recording_permission(void)\n{\n\t/* Desktop SDL owns any platform permission flow; there is no Android\n\t * runtime permission gate here. */\n\treturn 1;\n}" in desktop_audio
assert "return host_sdl_request_microphone_permission();" in android_audio
assert android_audio.index("host_sdl_request_microphone_permission()") < android_audio.index("#endif")
permission_request = host.split("int host_sdl_request_microphone_permission(void)", 1)[1].split("/* Flat touch input", 1)[0]
assert "SDL_RequestAndroidPermission" in permission_request
assert "memory_order_release" in permission_request and "memory_order_acquire" in permission_request
assert "SDL_Delay" not in permission_request and "pthread_join" not in permission_request
assert "host_sdl_request_microphone_permission" in read("port/android/guest/runtime/guest_host.h")
assert "host_sdl_request_microphone_permission" in read("port/android/host_imports.list")
assert "return host_sdl_request_microphone_permission();" in platform
assert "voice_audio_mix(output, frames)" in read("port/linux/src/dsound_sdl.c")
main = read("source/main/main.c")
network_voice = read("port/linux/game/network_voice.c")
assert "network_voice_update();" in main
# No startup path opens capture: network_voice_update is the sole caller of
# voice_audio_microphone, and its first no-network path closes then returns.
assert len(re.findall(r'\bvoice_audio_microphone\s*\(', network_voice)) == 5
assert "voice_audio_microphone(" not in main
voice_update = read("port/linux/game/network_voice.c").split("void network_voice_update(", 1)[1].split("/* ---------- the menus", 1)[0]
assert "voice_end_session();\n\t\treturn;" in voice_update
assert "if (!voice_settings_heard)" in voice_update and "voice_audio_microphone(FALSE);" in voice_update
assert "voice_microphone_permission_denied" in voice_update
assert "voice_microphone_retry_pending" in voice_update
assert "voice_microphone_retry_at - now" in voice_update
assert "VOICE_MICROPHONE_RETRY_MS = 10000" in network_voice
assert "microphone_result == VOICE_AUDIO_MICROPHONE_PERMISSION_DENIED" in voice_update
assert "microphone_result == VOICE_AUDIO_MICROPHONE_DEVICE_FAILURE" in voice_update
assert "retrying in %d ms" in voice_update
assert "held = push_to_talk && halo_push_to_talk_held() && !console_is_active();" in voice_update
assert "Keep PTT available in the network lobby, which is itself a menu" in voice_update
assert "else if (open_mic || held)" in voice_update
assert "voice_microphone_permission_denied = FALSE;" in voice_update
# Permission denial waits for explicit mode change; transient SDL device-open
# errors retry after ten seconds without re-requesting permission.
assert "else if (voice_microphone_permission_denied)\n\t\tvoice_microphone_wanted = FALSE;" in voice_update
mix = audio.split("void voice_audio_mix(float *output", 1)[1]
encode = audio.split("int voice_audio_encode(", 1)[1].split("int voice_audio_play(", 1)[0]
assert "voice_volume" in mix and "voice_volume" not in encode
assert "int voice_audio_play(" in audio_header
assert "return total;" in audio.split("int voice_audio_play(", 1)[1].split("void voice_audio_forget(", 1)[0]
server_manager = read("source/networking/network_server_manager.c")
assert "network_voice_machine_joined(machine_index);" in server_manager

distributed = read("port/linux/game/network_distributed.h")
for marker in ("_distributed_message_voice_up = 80", "_distributed_message_voice_down = 81",
               "_distributed_message_voice_config = 82"):
    assert marker in distributed
assert "VOICE_WIRE_MAXIMUM_PACKET = 255" in network_voice
assert "MIN(limit, MIN(VOICE_MAXIMUM_PACKET, VOICE_WIRE_MAXIMUM_PACKET))" in network_voice
assert "(byte)length" in network_voice
for marker in ("host configuration received", "first local Opus frame encoded",
               "first incoming frame from machine", "Opus-decoded frames",
               "host has not sent voice settings"):
    assert marker in network_voice, marker

# Android Test50 crashed inside a %s voice diagnostic. Test52 found the cause:
# platform_log had no prototype in network_voice.c, so on the guest ABI every
# variadic argument was read from the stack (see TEST52-CRASH-ANALYSIS.md and
# test_android_guest_prototypes.py). The integer-only formats and the
# settings-before-logging order are kept as harmless hardening.
voice_log_formats = re.findall(r'platform_log\("((?:[^"\\]|\\.)*)"', network_voice)
assert voice_log_formats, "voice diagnostics must remain visible in the game log"
for format_string in voice_log_formats:
    conversions = re.findall(
        r'%(?:[-+ #0]*\d*(?:\.\d*)?(?:hh|h|ll|l|z|t|j)?([a-zA-Z%]))',
        format_string,
    )
    assert all(conversion in "diuoxX%" for conversion in conversions), format_string
config_branch = network_voice.split("case _distributed_message_voice_config:", 1)[1].split("\n\t}\n\t}", 1)[0]
assert config_branch.index("voice_settings_heard = TRUE;") < config_branch.index("platform_log("), \
    "voice config must be accepted before diagnostics are emitted"
assert "voice_local_mode_id()" in network_voice and "voice_volume_percent()" in network_voice
assert "voice_diag_report(0)" in network_voice and "voice_diag_report(1)" in network_voice

vr_header = read("port/linux/src/vr.h")
vr_frame = read("port/linux/src/vr_frame.c")
vr_menu = read("port/linux/game/vr_menu.c")
assert "VR_BUTTON_ACTION_PUSH_TO_TALK" in vr_header
assert '"vr.button_push_to_talk"' in vr_frame
assert "VR_BUTTON_SOURCE_NONE\n};" in vr_frame
assert "vr_push_to_talk_held()" in read("port/linux/src/xinput_sdl.c")
assert '"MICROPHONE", "audio.voice_chat"' in vr_menu
assert '"VOICE VOLUME", "audio.voice_volume"' in vr_menu
assert '"PUSH TO TALK", "vr.button_push_to_talk"' in vr_menu
assert '{ "VOICE CHAT", vr_menu_voice, NUMBEROF(vr_menu_voice) }' in vr_menu
assert re.search(r'\{ "PUSH TO TALK", "vr\.button_push_to_talk"[^\n]*\{ "NONE", "none" \}', vr_menu)

assets = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.audio_settings.xml")
assert 'setting="audio.voice_chat"' in assets and 'setting="audio.voice_volume"' in assets
assert 'strings="OFF|PUSH TO TALK|OPEN MIC"' in assets
assert 'values="0|0.25|0.5|0.75|1|1.25|1.5|1.75|2"' in assets
profile = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.xml")
assert 'audio_settings_profile_item' in profile
assert 'open="main_menu/settings_select/player_setup/player_profile_edit/audio_settings/audio_settings_screen"' in profile
menus = read("port/assets/menus/menus.json")
assert "teamplay_options_edit.port.xml" in menus
assert "player_profile_edit.audio_settings.xml" in menus
assert (ROOT / "port/assets/menus/ce/main_menu.settings_select.multiplayer_setup.teamplay_options_edit.port.xml").is_file()

opus = read("port/third_party/opus/sources.txt").splitlines()
assert opus and all((ROOT / "port/third_party/opus" / path).is_file() for path in opus)
for build in ("tools/linux_build.py", "tools/android_build.py", "tools/windows_build.py"):
    assert "opus_sources()" in read(build), build

notes = re.sub(r"\s+", " ", read("docs/TEST45-VOICE-CHAT.md"))
assert "per-player mute controls are not wired" in notes
assert "not a claim of complete upstream" in notes
assert "no dedicated hold-to-talk touch button" in notes
package = read("tools/package-quest.py")
assert "required_candidate_code = 65 if candidate_at_least(args.label, 53) else 64 if candidate_at_least(args.label, 52) else 62 if candidate_at_least(args.label, 51) else 61 if candidate_at_least(args.label, 50) else 60 if candidate_at_least(args.label, 49)" in package
assert '"dump", "permissions"' in package and "android.permission.RECORD_AUDIO" in package
assert "OpenCE Build167 voice-chat runtime marker missing from APK" in package
assert "OpenCE Build167 voice-chat player-guide marker missing from APK" in package

print("PASS: Build167 voice chat has privacy defaults, compiled codec, Android recording bridge, mixer/network hooks, native/VR controls, and server routing assets")
print("DEVICE CHECK REQUIRED: microphone permission, capture/playback, PTT, and two-peer voice in a Quest lobby")
