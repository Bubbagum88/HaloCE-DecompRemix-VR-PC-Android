package com.halo.decomp;

/**
 * Test73, the Steam Frame: the game's activity in the app's main process. Lepton (SteamOS's Android container)
 * watches the process named as the package and ends the container when it ends; the VR build's HaloActivity runs
 * in a process of its own (:halo_game, src/vr/AndroidManifest.xml), right on the Quest and PICO, where it keeps the
 * launcher's process apart, but on the Frame the launcher's process is the one watched: trimmed, it took the game
 * with it, and the game's end left the container running. The launcher starts this one there (Lepton.running).
 */
public class HaloFrameActivity extends HaloActivity {
}
