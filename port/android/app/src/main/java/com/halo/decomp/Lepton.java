package com.halo.decomp;

import android.os.Build;

import java.io.File;

/**
 * The Steam Frame's Android container (Lepton: SteamOS's, a Waydroid fork), told apart at run time, and what this
 * app does differently there (Test73, item 8; Valve's Steamworks Steam Frame pages and Lepton's own source, and
 * ringfall-mjolnir-vr's field findings, CC0):
 * <ul>
 * <li>Lepton reinstalls the APK and empties /sdcard/Android/data whenever it starts again, and Android 11's scoped
 * storage keeps an app out of /sdcard/Documents: the game's data, settings, saves and logs live in the SteamOS
 * user's own Documents folder, bind-mounted at its host path ({@link #dataRoot});</li>
 * <li>a Steam launch is headless (no 2D window): the launcher starts the game at once, or imports a disc image it
 * finds, or leaves a note and ends;</li>
 * <li>the container ends when the process named as the package does: the VR game runs in the main process there
 * (HaloFrameActivity), not in :halo_game;</li>
 * <li>self-update makes no sense (the APK is put back at every start).</li>
 * </ul>
 * Everywhere else (Quest, PICO, phones) nothing here applies.
 */
final class Lepton {
    /** the folder in the SteamOS user's Documents (not "HaloCE": ringfall's installer takes that one over) */
    static final String FOLDER = "HaloCEQuestVR";

    private Lepton() { }

    /** an Android system property, "" when there is none (android.os.SystemProperties, by reflection) */
    static String property(String name) {
        try {
            Object value = Class.forName("android.os.SystemProperties").getMethod("get", String.class)
                .invoke(null, name);
            return value instanceof String ? (String) value : "";
        } catch (ReflectiveOperationException | RuntimeException e) {
            return "";
        }
    }

    /** whether this runs in Lepton: its launch's app id, its host user, its app container flag, or its build's model
     * (or maker, before Lepton 3: its properties.sh now says model "Lepton", maker "Valve"); host_lepton_running, the
     * same */
    static boolean running() {
        return !property("lepton.app_id").isEmpty() || !property("waydroid.host.user").isEmpty()
            || "true".equals(property("ro.steam.running_in_app_container"))
            || "Lepton".equalsIgnoreCase(Build.MODEL) || "Lepton".equalsIgnoreCase(Build.MANUFACTURER);
    }

    /** whether Lepton runs the app without a 2D window (a Steam launch; "Lepton Development" shows one) */
    static boolean headless() {
        return "true".equals(property("lepton.headless"));
    }

    /** the SteamOS user (the Frame's is "steamos"); only a plain name is taken */
    static String hostUser() {
        String user = property("waydroid.host.user");
        return user.matches("[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}") ? user : "steamos";
    }

    /** the game's data folder in the SteamOS user's Documents, made if it can be (null if it cannot be written) */
    static File dataRoot() {
        File root = new File("/home/" + hostUser() + "/Documents/" + FOLDER);
        if (!root.isDirectory())
            root.mkdirs();
        return root.isDirectory() && root.canWrite() ? root : null;
    }

    /** the SteamOS user's folders a disc image may have been put in, as Lepton shows them to apps */
    static File[] imageFolders() {
        String home = "/home/" + hostUser();
        return new File[] { new File(home, "Downloads"), new File(home, "Documents"), new File(home, "Desktop"),
            new File(home + "/Documents/" + FOLDER) };
    }

    /** the largest .iso or .xiso in those folders (not in their subfolders), or null */
    static File findDiscImage() {
        File best = null;
        for (File folder : imageFolders()) {
            File[] files = folder.listFiles();
            if (files == null)
                continue;
            for (File file : files) {
                String name = file.getName().toLowerCase(java.util.Locale.ROOT);
                if (file.isFile() && (name.endsWith(".iso") || name.endsWith(".xiso"))
                    && (best == null || file.length() > best.length()))
                    best = file;
            }
        }
        return best;
    }
}
