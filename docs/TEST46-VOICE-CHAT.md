# Test46 voice chat integration

OpenCE Build167 includes upstream voice chat based on host-relayed Opus audio.
The shared game-side integration is built into both Quest/Android APK flavors;
PC/Steam Frame packaging remains deferred. It preserves upstream routing
controls and message identifiers 80, 81, and 82. Voice payload lengths are
capped at the protocol's one-byte maximum of 255 bytes; the local codec buffers
remain larger. The port deliberately defaults the local microphone mode to Off
as a privacy choice, even though upstream Build167 defaults it to Push to Talk.

## Player controls

- Voice transmission defaults to **Off**. The microphone is not opened at game
  startup. Choose **Push to Talk** or **Open Mic** in the normal Audio settings
  or the VR menu's **Voice Chat** page to enable transmission.
- In VR, use **Buttons > Push to Talk** to bind a Quest controller button. It
  defaults to **None** so it cannot take an existing gameplay input.
- **Voice Volume** controls incoming player voices from 0 to 200 percent. Set
  it to **Muted** (0) to silence incoming voice. The microphone mode controls
  outgoing voice separately; OpenCE's `Off` mode disables transmission but
  still allows hearing teammates when voice volume is above zero.
- For keyboard play, the default PTT key is `V`; remap it in Controls Setup.
  Flat Android has no dedicated hold-to-talk touch button or gamepad PTT
  binding, so use Open Mic or connect a keyboard for PTT. Open Mic uses voice
  activation and does not transmit continuous silence.
- Hosts configure lobby voice, in-game routing, bitrate, and proximity range
  under the existing in-game Server Setup options. Routing follows the host's
  settings. The lobby may show who is speaking, but per-player mute controls
  are not wired into this candidate yet; Voice Volume at 0 mutes everyone.

## Android microphone permission

The APK declares `RECORD_AUDIO`. After the player enables PTT/Open Mic, a host
permits voice, and (for PTT) the button is held, the Android host requests
permission asynchronously. The game polls the result and opens SDL capture only
after permission is granted and transmission is still wanted; the permission
dialog does not block the game thread or a waiting microphone worker. Declining
permission disables capture for the current voice mode without repeated
frame-by-frame prompts; gameplay, incoming audio, and the game audio mixer
remain available. To retry after granting permission in Android settings,
switch voice mode Off and enable it again. After permission is granted, a
transient SDL recording-device open failure is retried after 10 seconds,
matching Build167's retry interval; this retry does not request permission
again. Android/Quest capture uses the system default recording device.

## Validation boundary

This is a selected Build167 voice integration, not a claim of complete upstream
menu parity. In particular, upstream's per-player scoreboard mute action is
not exposed here yet. Voice itself requires every participating peer to
understand Build167's voice messages; compatibility with older clients has not
been runtime-tested, and the game does not negotiate voice capability as a
separate feature.

`tools/test_voice_chat_integration.py` checks source/config/build wiring,
protocol IDs, UI settings, and the Android stream bridge. It does not establish
that headset permission prompts, microphone capture, Bluetooth/headset routing,
or host-relayed voice are working at runtime. Those require testing on a Quest
with two clients in a lobby and in a match. Do not claim device-verified voice
until that test has passed and its log confirms capture, transmission, and
playback.

Upstream references: [OpenCE Build 167](https://github.com/OpenCommunityEdition/OpenCE/releases/tag/build-167)
and the [voice chat implementation](https://github.com/OpenCommunityEdition/OpenCE/commit/f97b33391bfcb69b38006c1ffe93740f2d19c70d).
