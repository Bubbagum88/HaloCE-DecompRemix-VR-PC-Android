"""Exercise the production voice packet cap against its one-byte wire length."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "voice-protocol-test"
OUT.mkdir(parents=True, exist_ok=True)
source = (ROOT / "port/linux/game/network_voice.c").read_text()
match = re.search(
    r"static long voice_packet_limit\(\s*short kbps\s*\)\s*\{.*?\n\}",
    source,
    re.S,
)
assert match, "could not extract production voice_packet_limit"

harness = OUT / "voice_packet_limit.c"
binary = OUT / "voice_packet_limit"
harness.write_text(
    r'''#include <assert.h>
#define MIN(a, b) ((a) < (b) ? (a) : (b))
enum { VOICE_FRAMES_PER_SECOND = 50, VOICE_MAXIMUM_PACKET = 400,
       VOICE_WIRE_MAXIMUM_PACKET = 255 };
'''
    + match.group(0)
    + r'''
int main(void)
{
    short kbps;
    long prior = 0;
    for (kbps = 8; kbps <= 64; kbps++)
    {
        long limit = voice_packet_limit(kbps);
        assert(limit > 0 && limit <= 255);
        assert(limit >= prior);
        prior = limit;
    }
    assert(voice_packet_limit(8) == 56);
    assert(voice_packet_limit(64) == 255);
    return 0;
}
''',
    encoding="utf-8",
)
subprocess.run(
    ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
     "-fsanitize=address,undefined", str(harness), "-o", str(binary)],
    check=True,
)
subprocess.run([str(binary)], check=True)
print("PASS: production Opus packet limit fits the Build167 one-byte voice length at 8–64 kbps")
