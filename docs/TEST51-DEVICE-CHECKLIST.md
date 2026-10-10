# Test51 device checklist

## Highest priority: Quest multiplayer join

1. Install Test51 over Test50 without uninstalling, then launch the same Quest
   build and game-data set used for the failing report.
2. Join the same Wi-Fi server/network that previously closed the game. Confirm
   the match loads and stays active for at least several minutes.
3. Leave and rejoin once, then try a second available server. Check that a
   server list refresh, multiplayer menu navigation and returning to the main
   menu still work.
4. Save the newest game log. There must be no SIGSEGV around receipt of voice
   settings. If it still closes, preserve the full log and note headset OS,
   network target, game revision, server and match type.

## Voice chat regression

1. Use a host and a second voice-capable client. On the host, enable lobby
   voice and choose an in-game voice route that includes both players.
2. On the listener, set in-game receive volume above zero. Test hearing the
   other player while local microphone mode is Off; then test Push to Talk and
   Open Mic from the speaking client.
3. Check logs for numeric `host configuration received`, an encoded frame on
   the speaker, a host-accepted/relayed frame and a decoded incoming frame on
   the listener. Do not include or share recorded audio.
4. If the log says host settings were not received, first verify the host's
   voice options and Build167 voice support. A missing host config prevents
   client capture by design.

## Flat Android

1. Launch the flat APK and confirm touch/gamepad controls still work.
2. Join the same server if available; verify a multiplayer join does not close
   the app and the match finishes loading.
3. Confirm existing Audio settings remain available in-game; the launcher has
   no new voice controls.

Automated tests and packaging verify source invariants and APK metadata. Only
these device checks can establish runtime stability and audible voice chat.
