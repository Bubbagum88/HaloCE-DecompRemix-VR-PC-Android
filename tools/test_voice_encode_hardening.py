"""voice_audio_encode against the vendored Opus, under ASan/UBSan.

Test51/v1.0.19 closed on Quest as soon as a player spoke: a corrupted CELT
pulse-cache table (the guest assembly converter, tools/test_android_asm_convert.py)
sent the encoder past CELT_PVQ_U_ROW. That table is fixed; this suite keeps the
encoder's own entry robust regardless: the production voice_audio_encode is
extracted from port/linux/src/voice_audio.c and driven, with Opus built from
port/third_party/opus with assertions, by speech-like frames plus non-finite,
out-of-range and denormal samples, at every network.voice_kbps step and at
garbage bitrates such as Test51's misread kbps=995719466. Every call must
return a packet length within the caller's limit, and no sanitizer may fire.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "voice-encode-test"
OPUS = ROOT / "port/third_party/opus"


def extract_function(text, signature):
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        if depth == 0:
            return text[start:index + 1]
    raise AssertionError("unterminated " + signature)


clang = shutil.which("clang")
if not clang:
    print("SKIP: no host clang")
    sys.exit(0)

audio = (ROOT / "port/linux/src/voice_audio.c").read_text(encoding="utf-8")
encode = extract_function(audio, "int voice_audio_encode(const float *frame, int bitrate, unsigned char *packet, int maximum)")
for marker in ("isfinite(sample)", "VOICE_MINIMUM_BITRATE", "VOICE_MAXIMUM_BITRATE",
               "opus_encode_float(encoder, clean,", "maximum > VOICE_MAXIMUM_PACKET"):
    assert marker in encode, "voice_audio_encode lost its input/bitrate hardening: " + marker

OUT.mkdir(parents=True, exist_ok=True)
sanitize = ["-fsanitize=address,undefined", "-fno-sanitize-recover=undefined", "-g", "-O1"]
opus_flags = ["-std=gnu11", "-DOPUS_BUILD", "-DVAR_ARRAYS", "-DHAVE_LRINTF", "-DHAVE_LRINT", "-DENABLE_ASSERTIONS",
              *(f"-I{OPUS / name}" for name in ("include", "celt", "silk", "silk/float")), "-w"]
objects = []
for line in (OPUS / "sources.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    source = OPUS / line.strip()
    obj = OUT / (line.strip().replace("/", "_") + ".o")
    if not obj.is_file() or obj.stat().st_mtime < source.stat().st_mtime:
        subprocess.run([clang, *sanitize, *opus_flags, "-c", str(source), "-o", str(obj)], check=True)
    objects.append(str(obj))

harness = OUT / "voice_encode_test.c"
harness.write_text(r'''
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include "opus.h"
#include "voice_audio.h"
typedef int BOOL;
''' + re.search(r"^#define VOICE_RATE .*$", audio, re.M).group(0) + r'''
#define TRUE 1
#define FALSE 0
static OpusEncoder *encoder;
static int encoder_bitrate;
static int logged;
void platform_log(const char *format, ...)
{
	va_list arguments;
	va_start(arguments, format);
	vprintf(format, arguments);
	va_end(arguments);
	putchar('\n');
	logged++;
}
''' + encode + r'''
static unsigned seed = 1;
static float noise(void) { seed = seed * 1664525u + 1013904223u; return ((seed >> 8) / 16777216.0f) * 2.0f - 1.0f; }
int main(void)
{
	static const int bitrates[] = { 8000, 12000, 16000, 20000, 24000, 28000, 32000, 40000, 48000, 56000, 64000,
		0, -1, -2147483647 - 1, 2147483647, 995719466, 6000, 1000000 };
	float frame[VOICE_FRAME_SAMPLES];
	unsigned char packet[VOICE_MAXIMUM_PACKET + 64];
	double phase = 0.0;
	int b, f, total = 0;
	for (b = 0; b < (int)(sizeof(bitrates) / sizeof(bitrates[0])); b++)
	{
		for (f = 0; f < 200; f++)
		{
			int i, length, maximum = (f % 7 == 3) ? VOICE_MAXIMUM_PACKET + 64 : (bitrates[b] > 0 && bitrates[b] <= 64000 ? bitrates[b] / 400 * 2 + 16 : 400);
			int mode = (f / 9) % 6;
			double pitch = 110.0 + 60.0 * sin(f * 0.05);
			for (i = 0; i < VOICE_FRAME_SAMPLES; i++)
			{
				double s = 0.0;
				int h;
				phase += 2.0 * 3.14159265358979 * pitch / 48000.0;
				for (h = 1; h <= 30; h++)
					s += sin(phase * h) / h;
				frame[i] = (float)(0.5 * s) + (mode == 1 ? noise() : 0.0f);
				if (mode == 2 && i % 13 == 0) frame[i] = NAN;
				if (mode == 3 && i % 17 == 0) frame[i] = (i & 1) ? INFINITY : -INFINITY;
				if (mode == 4) frame[i] *= 1e30f;
				if (mode == 5) frame[i] = 1e-41f * (float)(i % 3);
			}
			length = voice_audio_encode(frame, bitrates[b], packet, maximum);
			if (length < 0 || length > maximum || length > VOICE_MAXIMUM_PACKET)
			{
				printf("FAIL: bitrate %d frame %d returned %d (maximum %d)\n", bitrates[b], f, length, maximum);
				return 1;
			}
			if (length > 0) total++;
			if (encoder_bitrate < VOICE_MINIMUM_BITRATE || encoder_bitrate > VOICE_MAXIMUM_BITRATE)
			{
				printf("FAIL: encoder left at %d bps\n", encoder_bitrate);
				return 1;
			}
		}
	}
	if (voice_audio_encode(NULL, 24000, packet, 100) != 0 || voice_audio_encode(frame, 24000, NULL, 100) != 0 ||
		voice_audio_encode(frame, 24000, packet, 0) != 0)
	{
		printf("FAIL: invalid arguments were encoded\n");
		return 1;
	}
	printf("encoded %d packets\n", total);
	return total > 3000 ? 0 : 1;
}
''', encoding="utf-8")
binary = OUT / "voice_encode_test"
built = subprocess.run([clang, *sanitize, f"-I{OPUS / 'include'}", f"-I{ROOT / 'port/linux/src'}", str(harness),
                        *objects, "-lm", "-o", str(binary)], capture_output=True, text=True)
assert built.returncode == 0, built.stderr[-3000:]
result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=600)
sys.stdout.write(result.stdout[-2000:])
assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-4000:]
assert "runtime error" not in result.stderr and "AddressSanitizer" not in result.stderr, result.stderr[-4000:]
print("PASS: voice_audio_encode sanitizes non-finite/out-of-range input, clamps garbage bitrates and stays "
      "within the packet limit (vendored Opus, assertions, ASan/UBSan)")
