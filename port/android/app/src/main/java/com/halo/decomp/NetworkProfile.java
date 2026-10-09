package com.halo.decomp;

import android.content.Context;
import java.io.File;
import java.io.IOException;
import java.util.Collections;

/** Compatible host targets, selected between game processes. Hosting stays on current protocol 24. */
final class NetworkProfile {
    static final int DEFAULT = 24;
    static final int[] SUPPORTED = {24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11};
    private static volatile int runningVersion;
    private static volatile boolean gameRunning;

    // Native exit ends the process. Never clear this on pause/backgrounding.
    static void gameStarted(File root) { runningVersion = configured(root); gameRunning = true; }

    static boolean supported(int version) { return version == 0 || (version >= 11 && version <= 24); }
    static String label(int version) { return version == 0 ? "All compatible networks" : "Network v" + version; }
    static int minimum(int target) { return target == 0 ? 11 : target; }
    static int maximum(int target) { return target == 0 ? 24 : target; }

    static int selected(Context context) {
        int version = context.getSharedPreferences("network_profile", Context.MODE_PRIVATE)
            .getInt("version", DEFAULT);
        return supported(version) ? version : DEFAULT;
    }

    static int configured(File root) {
        try {
            int version = Integer.parseInt(ConfigSettings.read(root, "network", "protocol_version", "24"));
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
        + "Prefer network 15-24 for campaign. Network 11 has no campaign co-op. Custom Edition still requires 23 or 24. "
        + "Enhanced physical interactions stay disabled unless the host and all peers negotiate support. Hosting remains network 24.";

    static boolean legacyCoop(File root) {
        return "true".equalsIgnoreCase(ConfigSettings.read(root, "network", "legacy_coop", "false"));
    }

    static boolean campaignCompatible(int version, boolean legacy) {
        return version >= 15 && version <= 24 || legacy && version >= 12 && version <= 14;
    }

    static void setLegacyCoop(File root, boolean enabled) throws IOException {
        if (gameRunning) throw new IOException("Close the game fully before changing legacy co-op compatibility.");
        ConfigSettings.write(root, "network", Collections.singletonMap("legacy_coop", Boolean.toString(enabled)));
        RunLog.line("Legacy network 12-14 co-op consent: " + enabled);
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
