# Test52 voice crash: root cause and fix

## Report

On v1.0.19 / Test51 (code62/63) the owner joined a voice-enabled game, spoke,
and the Quest app closed. Three Test51 logs were supplied (2026-10-10 14:56,
14:58 and 15:12). Two end in the same fault:

```
voice chat: host configuration received lobby=1068677315 route=0 kbps=995719466 ...
voice chat: microphone open
voice chat: first local Opus frame encoded and handed to the network path (22022600 bytes)
signal 11 at address 0xbc90: pc 00000000883937b4 lr 00000000883a22d8
```

The third session (no crash) never had a host that sent voice settings.

## Symbolized stack (exact Test51 guest, sha256 3257aadb…77c2)

`encode_pulses ← alg_quant ← quant_partition ← quant_partition ← quant_band ←
quant_all_bands ← celt_encode_with_ec ← opus_encode_frame_native ←
opus_encode_native ← opus_encode_float ← voice_audio_encode ←
network_voice_update ← main_loop`

The faulting load is `CELT_PVQ_U_ROW[min(n,k)][max(n,k)]`. The row table
(15 valid pointers) is intact, but the encoder used row 15: the next word in
`.data` is `0xbb80` (48000), which it dereferenced (`0xbb80 + 70*4 = 0xbc98`,
the reported fault address). `alg_quant` had received K=240 pulses; Opus
bounds K to 128 through its pulse-cache table, so that table was wrong.

## Root cause: the arm64_32 → ELF assembly converter

`tools/android_asm_convert.py` ran Darwin symbol "undecoration" (dropping a
leading `_`) over every directive operand, including `.ascii`/`.asciz` data.
Its quoted-string token ignored backslash escapes, so after a `\"` inside a
byte table the rest was read as identifiers and a lone `_` (byte 95) was
deleted. A string that began with `_` also lost that character. clang emits
byte tables as `.ascii`, so Opus's `cache_bits50` lost byte 338 and its tail
shifted by one — exactly the bytes `bits2pulses` reads for the larger CELT
bands. Silence and quiet frames rarely reach those bands, which is why the
crash appeared when someone actually spoke and why a low host bitrate could
appear to work.

Verification (all reproducible in-repo):

- The real Test51 guest image was run under qemu-aarch64 with a minimal loader
  driving its own `opus_encode_float` with `voice_audio.c`'s settings: it
  crashed with the identical PC/LR/fault pattern (28–32 kbps on synthetic
  speech). Patching only the correct table bytes into that image made all
  bitrates 8–64 kbps × 1500 frames encode cleanly.
- `modes.c` compiled through the pipeline with the old converter reproduces the
  same first mismatch (byte 338); the fixed converter is byte-identical to the
  source.
- `tools/test_android_asm_convert.py` (now in the check suite) fails on the old
  converter and on the Test51 image, and passes with the fix.

Other data the old converter altered (25 of 1640 guest objects): Opus
`silk_rate_levels_BITS_Q5` and the analysis MLP bias; the progress-bar monk
tone ADPCM data; the DirectSound effects image; tomlc17's number-parsing
charsets (`_` digit separators); musl `iswalpha`/`iswpunct`/`towctrans`/iconv
tables; `menu_functions.c`'s `"_lan_"` (no behavior change: no Internet widget
name contains `lan_`); and assertion/debug strings. All are corrected.

## Second defect: implicit declarations on the guest ABI

`network_voice.c` called `platform_log` without a prototype. The guest uses the
Darwin arm64_32 convention: variadic arguments go on the stack, while an
undeclared call passes them in registers. Every logged voice value was stack
garbage (hence `kbps=995719466`), and Test50's `%s` read a garbage pointer —
the real cause of the Test50 join crash; Test51's integer-only formats only
removed the `%s`. A guest-wide scan found the same defect elsewhere:

| Call | Effect on the guest |
|---|---|
| `collision_test_sphere` (vr_npc_interaction.c, new after v1.0.18) | float radius garbage: NPC release/recovery clearance test meaningless |
| `platform_log` (vr_world_remote.c, new after v1.0.18) | garbage logs |
| `rasterizer_text_set_scale` (game_engine.c) | scoreboard text scale/origin garbage (clamped to 1.0) |
| `game_engine_vehicle_placement_allowed` (object_types.c) | 1-byte boolean read as int |
| `main_get_solo_level_from_name`, `playlist_profile_get_options`, `player_handle_powerup` | narrow return values read as int |

All now have exact prototypes. The Android guest build replaces `-w` with
`-Wno-everything -Werror=implicit-function-declaration` for game, port and
platform units (in C89, `-w` silences the warning even when promoted), so any
future undeclared call fails the build. The unmodified v1.0.19 tree fails this
gate in 19 units; the fixed tree passes all 1640 (flat and VR).
`tools/test_android_guest_prototypes.py` guards the wiring.

## Toolchain

Public v1.0.18 was built in WSL with clang 18 (no PGO). Test47–Test51/v1.0.19
used clang 22 with the committed PGO profiles in a separate environment. Test52
is built with the v1.0.18 setup and the same debug signing key
(53d416f7…2aa4), so it installs over v1.0.19 and keeps data.

## Boundary

Host checks, the qemu reproduction and the build gates cannot prove headset
voice end-to-end. A Quest test must confirm: speaking in a lobby and a match no
longer closes the game; another player hears you; you hear them.

## Test53: independent reproduction and hardening

Test52 was committed but never built. Test53 (which supersedes it) re-proved
the cause without the earlier session's qemu loader:

- The shipped Test51 guest images (Quest `3257aadb…`, Android `f86d1193…`)
  both hold a `cache_bits50` whose byte 338 (95) is missing and whose tail is
  shifted by one (54 mismatching bytes); `cache_index50` and `cache_caps50`
  match the source. v1.0.18 shipped no Opus at all: voice is entirely
  post-1.0.18 work.
- The vendored Opus built for the PC host with only that byte dropped, driven
  as `voice_audio.c` drives it (48 kHz mono VOIP, complexity 5, in-band FEC,
  10% loss, SIGNAL_VOICE, 20 ms frames) on synthetic speech: AddressSanitizer
  reports a global-buffer-overflow past `cache_bits50` in `quant_partition`,
  from `quant_band` / `quant_all_bands` / `celt_encode_with_ec` /
  `opus_encode_float`, the device crash's own chain. Without sanitizers the
  encoder runs at 8–24 kbps and fails at 28 kbps (on the device the same read
  became the SIGSEGV). With the correct table every bitrate from 8 to 64 kbps
  encodes 1,500 frames cleanly.

Hardening added in Test53: `voice_audio_encode` replaces non-finite samples,
clamps to full scale, clamps the bitrate to 8–64 kbps and the packet limit,
and logs an encoder failure once (`tools/test_voice_encode_hardening.py`
runs it against the vendored Opus with assertions under ASan/UBSan, including
Test51's misread kbps=995719466). Every guest unit, libtiff, musl and Opus
included, now rejects implicit declarations; libtiff's K&R `long lseek()`
(a 32-bit offset into a 64-bit `off_t` on the guest) uses the C library's
prototype; `tools/android_guest_abi_lint.py` links all guest units as LLVM
bitcode after each build and fails on any call whose argument count, types,
return type or integer extension differ from the definition (it found and
fixed mismatched rasterizer, keyboard and libtiff declarations). The
post-build image check requires the built guest's Opus tables to match the
source. The "VR manual reload gate: weapon=-303103938" line was not garbage:
it is a valid weapon datum handle printed as signed decimal (now hex).
