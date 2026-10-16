"""Test72: OpenCE build 208 (upstream main f90d9555, 2026-10-16) against
this port. Build 206 -> 208 is five commits:

- d9669f6e the guest's assembly conversion keeps string literals byte for
  byte: already here (tools/android_asm_convert.py's STRING_DIRECTIVES);
- 9c70f5f5 voice chat: a packet that is not one 20 ms frame is dropped
  before decoding: ported (every build of ours sends 960-sample frames);
- 4301ca88 Back from the postgame host screen restores the main menu (the
  connected map-select wrapper's main_menu_if_no_history): ported;
- 085676d8 / f90d9555: their merges; README and CI only besides.

No network file changed: network 29 stays (no protocol bump).
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")

asm = read("tools/android_asm_convert.py")
assert 'STRING_DIRECTIVES = {".ascii", ".asciz", ".string"}' in asm and "if op in STRING_DIRECTIVES:" in asm

voice = read("port/linux/src/voice_audio.c")
play = voice[voice.index("int voice_audio_play("):voice.index("void voice_audio_forget(")]
guard = "if (opus_packet_get_nb_samples(packet, length, VOICE_RATE) != VOICE_FRAME_SAMPLES)\n\t\treturn 0;"
assert guard in play
assert play.index("length > VOICE_MAXIMUM_PACKET") < play.index(guard) < play.index("pthread_mutex_lock(&voice_lock);")
# every packet this port sends is one such frame
assert "length = opus_encode_float(encoder, clean, VOICE_FRAME_SAMPLES, packet, maximum);" in voice
assert "#define VOICE_FRAME_SAMPLES 960" in read("port/linux/src/voice_audio.h")

menu = read("port/assets/menus/ce/main_menu.multiplayer_type_select.connected.xml")
wrapper = re.search(r'<widget name="main_menu/multiplayer_type_select/connected/connected_map_select_wrapper"[^>]*>', menu).group(0)
assert 'flags="pass_unhandled_to_focused_child pause_game main_menu_if_no_history tag_controller_index force_handle_mouse"' in wrapper
assert '"main_menu_if_no_history"' in read("port/linux/game/menu_tags.c")

# the network is unchanged
assert "#define HALO_PORT_NETWORK_VERSION 29" in (ROOT / "port/linux/include").joinpath("halo_port_limits.h").read_text(encoding="utf-8") \
    if (ROOT / "port/linux/include/halo_port_limits.h").exists() else True
identity = read("port/linux/src/vr_frame.c")
assert "(OpenCE Build208 merged / network29" in identity
assert "Selected fixes through Build 208 are included" in read("port/android/app/src/main/java/com/halo/decomp/Updater.java")
assert 'current_upstream_markers = ([b"OpenCE Build208 merged / network29"' in read("tools/package-quest.py")

print("PASS: OpenCE Build 208 parity: the voice frame guard and the postgame menu fix ported, the string-literal "
      "conversion already here; network 29 unchanged")
