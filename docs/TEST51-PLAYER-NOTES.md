# Test51 player notes

Test51 is a private owner-test build focused on the Quest crash reported while
joining multiplayer. It keeps Test50's gameplay, VR, mobile, network, sprint and
vehicle changes.

## Multiplayer join crash fix

The failing Quest sessions had already connected and loaded the match. The game
then crashed in a voice-configuration diagnostic during join. Test51 changes
those diagnostics to safe integer-only formatting and accepts host voice
settings before logging them. The voice protocol and normal multiplayer
behavior are unchanged.

Please retry the same server and network that triggered the crash, then try a
second server if available. If the game still closes, save the newest log from
the existing Downloads/log location and include the server network/version,
game revision, headset OS and whether the match was PvP or co-op.

## Voice chat

Voice controls remain in the in-game Audio settings and VR **Voice Chat** menu.
Set local microphone mode to Push to Talk or Open Mic, set receive volume above
zero, and have the host enable lobby voice or an in-game route that includes
you. The host and peers must support the Build167 voice relay. The 11:39 report
had no host voice settings, so that session could not open capture; this build
adds better numeric diagnostics to identify whether future sessions receive
host settings and transmit/decode frames. No voice option was added to the
Android launcher.

## Unchanged behavior

The voice packet protocol, host relay, routing, capture defaults and in-game
settings are unchanged. Test50's vehicle reticle alignment, optional Hold/Toggle
sprint, Safe Geometry defaults and earlier Test47-Test49 fixes are retained.
This private build is not a public release and still needs Quest and Android
device testing.
