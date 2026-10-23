package com.halo.decomp;

import android.content.Context;
import java.io.File;
import java.io.IOException;
import java.util.Collections;

/** Compatible host targets, selected between game processes. Hosting stays on current protocol 34.
 * All compatible networks is the default (most servers); a selection the player made is kept. */
final class NetworkProfile {
    static final int DEFAULT = 0;
    static final int CURRENT = 34;
    static final int[] SUPPORTED = {34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11};
    private static volatile int runningVersion;
    private static volatile boolean gameRunning;

    // Native exit ends the process. Never clear this on pause/backgrounding.
    static void gameStarted(File root) { runningVersion = configured(root); gameRunning = true; }

    static boolean supported(int version) { return version == 0 || (version >= 11 && version <= CURRENT); }
    static String label(int version) { return version == 0 ? "All compatible networks" : "Network v" + version; }
    static int minimum(int target) { return target == 0 ? 11 : target; }
    static int maximum(int target) { return target == 0 ? CURRENT : target; }

    static int selected(Context context) {
        int version = context.getSharedPreferences("network_profile", Context.MODE_PRIVATE)
            .getInt("version", DEFAULT);
        return supported(version) ? version : DEFAULT;
    }

    static int configured(File root) {
        try {
            int version = Integer.parseInt(ConfigSettings.read(root, "network", "protocol_version", Integer.toString(DEFAULT)));
            return supported(version) ? version : DEFAULT;
        } catch (NumberFormatException e) { return DEFAULT; }
    }

    static void select(Context context, File root, int version) throws IOException {
        if (gameRunning) throw new IOException("Close the game fully before changing its network, then reopen the launcher.");
        if (!supported(version)) throw new IOException("This app has no implementation for network " + version);
        // Persist only after the config is writable; a failure must not claim a successful switch.
        ConfigSettings.write(root, "network", Collections.singletonMap("protocol_version", Integer.toString(version)));
        if (!context.getSharedPreferences("network_profile", Context.MODE_PRIVATE).edit()
                .putInt("version", version).commit())
            throw new IOException("Could not remember the network selection; choose it again before playing");
        RunLog.line("Network profile selected for next launch: " + version);
    }

    static final String LEGACY_WARNING = "Legacy network 12-14 co-op is optional and OFF by default. "
        + "These old hosts do not send scripted team allegiance: Marines may show hostile/red reticles and other team behavior can differ. "
        + "The client preserves the old native behavior rather than inventing host allegiance. Other old-host bugs remain. "
        + "Prefer network 15-34 for campaign. Network 11 has no campaign co-op. Custom Edition still requires 23 or newer. "
        + "Enhanced physical interactions stay disabled unless the host and all peers negotiate support. Hosting remains network 34.";

    static boolean legacyCoop(File root) {
        return "true".equalsIgnoreCase(ConfigSettings.read(root, "network", "legacy_coop", "false"));
    }

    static boolean campaignCompatible(int version, boolean legacy) {
        return version >= 15 && version <= CURRENT || legacy && version >= 12 && version <= 14;
    }

    static void setLegacyCoop(File root, boolean enabled) throws IOException {
        if (gameRunning) throw new IOException("Close the game fully before changing legacy co-op compatibility.");
        ConfigSettings.write(root, "network", Collections.singletonMap("legacy_coop", Boolean.toString(enabled)));
        RunLog.line("Legacy network 12-14 co-op consent: " + enabled);
    }

    /** Test67: the OpenCE fork jcompto95-tech's community extras (the players' Armor choices shared, votes to
     * ban with a reason): message kinds of their own, which OpenCE players without them ignore. Test73: text
     * chat is OpenCE 232's own, outside this switch; Test67-72 builds get none of them (network_extras.c). */
    static final String EXTRAS_HELP = "Community extras: players' armor, visor, lights and shield colors shared, "
        + "and votes to kick or ban with a reason (F1 yes, F2 no). They travel in messages of their own, "
        + "which OpenCE players without them simply ignore, so you join and host the same games as ever. "
        + "Text chat is OpenCE's own now, the same for everyone (Settings > Network Setup > Multiplayer HUD). "
        + "A player on an older version of this port (Test 67 to 72) gets no armor, votes or chat with you until "
        + "they update. OFF: this game sends and reads none of them.";

    static boolean communityExtras(File root) {
        return !"false".equalsIgnoreCase(ConfigSettings.read(root, "network", "community_extras", "true"));
    }

    static void setCommunityExtras(File root, boolean enabled) throws IOException {
        if (gameRunning) throw new IOException("Close the game fully before changing the community extras.");
        ConfigSettings.write(root, "network", Collections.singletonMap("community_extras", Boolean.toString(enabled)));
        RunLog.line("Community extras: " + enabled);
    }

    static void prepare(Context context, File root) throws IOException {
        int version = selected(context);
        if (gameRunning) {
            if (version != runningVersion) throw new IOException("Close the game fully to apply the selected network.");
            return; // An external invite can bring the launcher forward while the game still runs.
        }
        if (!ConfigSettings.read(root, "network", "protocol_version", "").equals(Integer.toString(version)))
            ConfigSettings.write(root, "network", Collections.singletonMap("protocol_version", Integer.toString(version)));
        RunLog.line("Launch network profile: " + version);
    }
}
