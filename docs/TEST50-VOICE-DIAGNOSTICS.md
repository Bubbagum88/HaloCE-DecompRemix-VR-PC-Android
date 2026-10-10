# Test50 voice-chat evidence and diagnostics

## Supplied Test49 log

`halo_log_2026-10-10_10-19-00-741_26302.txt` identifies Quest VR Test49
(1.0.30-test49/code60), Wi-Fi with validated Internet, and the system playback
device at 48 kHz stereo. Audio-device statistics show no output underruns.
The game joined a 17-player network24 session (18 players after joining), then
a network11 session. The microphone opened during the first session and closed
when it left; later it opened again. No microphone-permission-denied,
microphone-device-failure, or Opus-encoder error is recorded.

This proves the microphone device was allowed to open and that the normal audio
output thread was active. It does **not** prove that speech was captured,
encoded, transmitted, received from another player, decoded, or audible. The
old build did not log voice settings or voice packet/decode events. Generic
audio mixer statistics and the absence of an output underrun cannot establish
voice-chat playback. One session also reports that the host ran another build;
that is not enough to identify whether that host implemented the optional
Build167 voice relay.

The protocol is host-relayed. The host sends settings and routes audio according
to lobby permission and its in-game voice mode. A connected client only opens
capture when its selected Push-to-Talk/Open-Mic mode is permitted; its
microphone mode does not disable incoming voice. All participating clients and
the host need the Build167 voice-message implementation. There is no distinct
voice-capability negotiation. If nobody is transmitting, a host disables the
applicable route, or peers do not implement the relay, the player can hear
nothing while ordinary multiplayer continues to work.

## Test50 diagnostic additions

- Log a host-configuration change with lobby permission, in-game route,
  bitrate, proximity, local transmit mode, and local receive volume.
- If a client does not receive host voice settings within five seconds, log
  that capture remains closed and the host must implement the Build167 relay;
  in-game routing may separately be turned off.
- Log the first local encoded Opus frame submitted to the network path.
- Log the first incoming frame from each remote machine and whether Opus
  decoded samples were queued, plus routing gain and pan.
- Emit a ten-second summary of encoded/sent, host-accepted, relay-delivery,
  incoming, and successfully decoded frame counts.
- Do not log audio data, player names, or a per-frame stream of messages.

These diagnostics identify where a future voice session stops. They do not
replace a two-client Quest test with one client speaking in a lobby and a match.
In particular, a count of zero incoming frames cannot by itself distinguish
silence from a host that did not relay voice; compare the host-configuration
line and have a known voice-enabled peer transmit during the test.

## Latest upstream

The official OpenCE release page lists Build177 (`9da2a45`) as Latest on
2026-10-10. It redraws weapon reticles from exact PC HUD sheet matches. This
artwork is already integrated behind the existing pixel-CRC gate. No newer
upstream release or network-version change was present at this check. The
candidate keeps the Build157/network24 base and already reviewed compatible
changes through Build177; this is not a full upstream rebase.
