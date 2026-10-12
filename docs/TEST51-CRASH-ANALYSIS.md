# Test51 multiplayer join crash and voice review

## Finding

The Test50 Quest logs show that network admission succeeds before the failure.
In the two failing sessions, the client receives the server's player/game
settings, finishes loading, and joins the running match. It then exits with the
same SIGSEGV at `0x88003914` immediately after the host begins the game-load
transition. The failure is not a Wi-Fi or server-reachability timeout.

The faulting instruction is `strnlen` inside `vfprintf`/`printf_core`, called
from `platform_log`. Symbolizing the return address against the exact Test50
guest places the log call in `network_voice_handle_message`, while handling the
host's voice-configuration message. Test50 had added a diagnostic there with
mixed string and floating-point variadic arguments. The guest log formatter
interpreted a non-string value as a string pointer and faulted. This was a
logging regression on the successful join path, not a network protocol change.

## Fix

Test51 makes every `network_voice.c` log use integer-only format conversions.
The client records the host settings and their timestamp before it emits the
optional diagnostic. This keeps logging from interrupting voice initialization
and removes the exact formatter path seen in both crash logs. The host/client
voice messages, routing rules, microphone policy, audio processing and network
compatibility are otherwise unchanged.

For the compact numeric logs, `local_tx` is 0=Off, 1=Push to Talk, 2=Open Mic;
`route` is the `network_voice.h` mode (0=Off, 1=team proximity, 2=team and
enemy proximity, 3=team global, 4=team global plus enemy proximity). Receive
volume is a clamped integer percent (0-200). Diagnostic `reason` is 0=session
end or 1=ten-second interval.

## Voice evidence

The 11:39 log joins the match and continues running, but after five seconds it
reports that the host has not sent voice settings and leaves microphone capture
closed. With no host settings, that client cannot begin the configured voice
session. This is consistent with a host that has voice disabled or does not
implement the Build167 voice relay; the log does not distinguish those cases.
The two crashing logs end too early to establish whether their hosts had enabled
voice. The user reports voice chat worked in an earlier candidate, and Test50's
change to `network_voice.c` was diagnostic-only. Test51 preserves the voice
protocol and configuration behavior and fixes the new diagnostic that crashed
while receiving the host settings.

Test51 adds no Android-launcher voice controls. Use the existing in-game Audio
settings / VR Voice Chat page for local microphone mode and incoming volume;
the host controls lobby permission and in-game routing in Server Setup. A
two-client headset test is still required to confirm transmit, relay, decode and
audibility after the crash fix.

## Verification boundary

The source regression check rejects non-integer format conversions in all
voice log calls and asserts host settings are accepted before logging. Quest
and flat APK builds plus automated regression tests verify the candidate
contents, but they cannot prove the live headset join or voice test. See
[TEST51-DEVICE-CHECKLIST.md](TEST51-DEVICE-CHECKLIST.md).
