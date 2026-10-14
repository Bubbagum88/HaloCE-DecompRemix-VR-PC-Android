package com.halo.decomp;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;

/**
 * Test68: Halo 1 MCC custom maps (GulchCE's loader, port/linux/game/mcc_maps.c),
 * played solo only in this build. They live in the active game set's
 * mcc_maps folder: loose maps, one level of package folders (a campaign and
 * its own bitmaps.map / sounds.map), and MCC's two standard resource sets
 * copied from the player's own MCC install:
 * mcc_maps/_shared/singleplayer/bitmaps.map (MCC's halo1/maps/bitmaps.map) and
 * mcc_maps/_shared/multiplayer/bitmaps.map, sounds.map (MCC's
 * halo1/maps/custom_edition/). Nothing of MCC's or of a map's is bundled:
 * the player imports their own files.
 */
final class MccMaps {
    /** a level's name, its package and a separator included, before .map (mcc_maps.c) */
    static final int MAXIMUM_RELATIVE = 54;
    static final int HEADER_BYTES = 0x800;
    /** MCC's map header: 'head', version 13, 'foot' (port/linux/game/mcc_cache_format.c) */
    static final int VERSION = 13;
    static final String SHARED = "_shared";

    final File root;

    MccMaps(File gameRoot) {
        root = new File(gameRoot, "mcc_maps");
    }

    /** What a map file's first 2048 bytes say. */
    static final class Header {
        final boolean mcc;
        /** 0 a campaign (solo) scenario, 1 multiplayer, 2 the user interface */
        final int scenarioType;
        final String name;

        Header(boolean mcc, int scenarioType, String name) {
            this.mcc = mcc;
            this.scenarioType = scenarioType;
            this.name = name;
        }
    }

    private static int u32(byte[] b, int at) {
        return (b[at] & 0xff) | (b[at + 1] & 0xff) << 8 | (b[at + 2] & 0xff) << 16 | (b[at + 3] & 0xff) << 24;
    }

    static Header header(byte[] h) {
        if (h == null || h.length < HEADER_BYTES)
            return new Header(false, -1, "");
        boolean mcc = u32(h, 0) == 0x68656164 /* 'head' */ && u32(h, 0x7FC) == 0x666F6F74 /* 'foot' */
            && u32(h, 4) == VERSION;
        int type = (h[0x60] & 0xff) | (h[0x61] & 0xff) << 8;
        int end = 0x20;
        while (end < 0x40 && h[end] != 0)
            end++;
        String name = new String(h, 0x20, end - 0x20, StandardCharsets.ISO_8859_1);
        return new Header(mcc, mcc ? type : -1, name);
    }

    static Header header(File file) {
        byte[] h = new byte[HEADER_BYTES];
        try (InputStream in = new FileInputStream(file)) {
            int read = 0;
            while (read < h.length) {
                int n = in.read(h, read, h.length - read);
                if (n < 0)
                    break;
                read += n;
            }
            if (read < h.length)
                return new Header(false, -1, "");
        } catch (IOException exception) {
            return new Header(false, -1, "");
        }
        return header(h);
    }

    /** A folder or file name the game reads: letters, digits, '_', '-', '.', anything else '_'. */
    static String safe(String name) {
        StringBuilder out = new StringBuilder();
        for (char c : name.toCharArray()) {
            boolean ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
                c == '_' || c == '-' || c == '.';
            out.append(ok ? c : '_');
        }
        String result = out.toString();
        while (result.startsWith("."))
            result = result.substring(1);
        return result;
    }

    static boolean resourceName(String file) {
        String lower = file.toLowerCase(Locale.ROOT);
        return lower.equals("bitmaps.map") || lower.equals("sounds.map") || lower.equals("loc.map");
    }

    /**
     * Where a file of a chosen folder goes: its package is the folder it is
     * in (a folder named "maps" counts as the one above it, as a mod's
     * download keeps its maps there), the chosen folder's own name for its
     * top level. Only .map files and .txt descriptions; NULL for anything
     * else, for a name too long for the game, and for MCC's own resource
     * maps chosen outside a package (sharedTarget takes those).
     *
     * @param chosen the chosen folder's name
     * @param folders the folders between the chosen folder and the file
     */
    File target(String chosen, List<String> folders, String file) {
        String lower = file.toLowerCase(Locale.ROOT);
        if (!lower.endsWith(".map") && !lower.endsWith(".txt"))
            return null;
        String group = chosen;
        for (int index = folders.size() - 1; index >= 0; index--) {
            String folder = folders.get(index);
            if (!folder.equalsIgnoreCase("maps")) {
                group = folder;
                break;
            }
        }
        group = safe(group);
        String name = safe(file);
        if (group.isEmpty() || name.isEmpty() || group.equalsIgnoreCase(SHARED))
            return null;
        if (lower.endsWith(".map")) {
            String stem = name.substring(0, name.length() - 4);
            if (stem.isEmpty() || group.length() + 1 + stem.length() > MAXIMUM_RELATIVE)
                return null;
        }
        return new File(new File(root, group), name);
    }

    /**
     * Where one of MCC's standard resource maps goes, by the folder it was
     * found in: MCC's halo1/maps/custom_edition/ bitmaps.map and sounds.map
     * are the multiplayer set, halo1/maps/bitmaps.map the singleplayer set.
     * NULL for anything else.
     */
    File sharedTarget(List<String> folders, String file) {
        String lower = file.toLowerCase(Locale.ROOT);
        boolean custom = !folders.isEmpty() && folders.get(folders.size() - 1).equalsIgnoreCase("custom_edition");
        File shared = new File(root, SHARED);
        if (custom && (lower.equals("bitmaps.map") || lower.equals("sounds.map")))
            return new File(new File(shared, "multiplayer"), lower);
        if (!custom && lower.equals("bitmaps.map"))
            return new File(new File(shared, "singleplayer"), lower);
        return null;
    }

    /** Copies in to target through a .part file, then checks an MCC level's header. */
    static long copy(InputStream in, File target) throws IOException {
        File parent = target.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs())
            throw new IOException("cannot make " + parent);
        File part = new File(target.getPath() + ".part");
        long total = 0;
        byte[] buffer = new byte[1 << 16];
        try (OutputStream out = new FileOutputStream(part)) {
            int n;
            while ((n = in.read(buffer)) > 0) {
                out.write(buffer, 0, n);
                total += n;
            }
        }
        if (target.exists() && !target.delete()) {
            part.delete();
            throw new IOException("cannot replace " + target.getName());
        }
        if (!part.renameTo(target)) {
            part.delete();
            throw new IOException("cannot write " + target.getName());
        }
        return total;
    }

    /** a level copied in that is not a Halo 1 MCC map (version 13) is taken out again */
    static boolean keepLevel(File target) {
        String lower = target.getName().toLowerCase(Locale.ROOT);
        if (!lower.endsWith(".map") || resourceName(target.getName()))
            return true;
        if (header(target).mcc)
            return true;
        target.delete();
        return false;
    }

    /** the MCC levels installed: [campaign, multiplayer] */
    int[] levels() {
        int[] counts = new int[2];
        File[] top = root.listFiles();
        if (top == null)
            return counts;
        for (File entry : top) {
            if (entry.isDirectory()) {
                if (entry.getName().equalsIgnoreCase(SHARED))
                    continue;
                File[] inner = entry.listFiles();
                if (inner != null)
                    for (File file : inner)
                        count(file, counts);
            } else {
                count(entry, counts);
            }
        }
        return counts;
    }

    private static void count(File file, int[] counts) {
        if (!file.isFile() || !file.getName().toLowerCase(Locale.ROOT).endsWith(".map") || resourceName(file.getName()))
            return;
        Header h = header(file);
        if (h.mcc && h.scenarioType == 0)
            counts[0]++;
        else if (h.mcc && h.scenarioType == 1)
            counts[1]++;
    }

    boolean sharedSingleplayer() {
        return new File(root, SHARED + "/singleplayer/bitmaps.map").isFile();
    }

    boolean sharedMultiplayer() {
        return new File(root, SHARED + "/multiplayer/bitmaps.map").isFile() &&
            new File(root, SHARED + "/multiplayer/sounds.map").isFile();
    }

    String summary() {
        int[] counts = levels();
        return counts[0] + " campaign and " + counts[1] + " multiplayer MCC maps installed. MCC's resources: "
            + "singleplayer " + (sharedSingleplayer() ? "yes" : "no") + ", multiplayer "
            + (sharedMultiplayer() ? "yes" : "no") + ".";
    }

    /** Takes the mcc_maps folder and its disabled packages away (the game's own maps are not in them). */
    void removeAll() throws IOException {
        delete(root);
        delete(disabledRoot());
    }

    /** packages switched off: beside mcc_maps, which is all the game reads */
    File disabledRoot() {
        return new File(root.getParentFile(), "mcc_maps_disabled");
    }

    static final String WORKSHOP_FILE = "workshop.properties";

    /** An installed package: a folder of MCC maps, enabled or not, a Workshop item's or imported. */
    static final class Package {
        final String name;
        final File folder;
        final boolean enabled;
        final long bytes;
        final int levels;
        /** the Workshop item it came from (0: imported from a folder), its title and last update (seconds) */
        final long workshopId;
        final String title;
        final long workshopUpdated;

        Package(String name, File folder, boolean enabled, long bytes, int levels, long workshopId, String title,
                long workshopUpdated) {
            this.name = name;
            this.folder = folder;
            this.enabled = enabled;
            this.bytes = bytes;
            this.levels = levels;
            this.workshopId = workshopId;
            this.title = title;
            this.workshopUpdated = workshopUpdated;
        }
    }

    /** every package, enabled first, each by name */
    List<Package> packages() {
        List<Package> result = new java.util.ArrayList<>();
        for (int pass = 0; pass < 2; pass++) {
            File base = pass == 0 ? root : disabledRoot();
            File[] folders = base.listFiles(File::isDirectory);
            if (folders == null)
                continue;
            java.util.Arrays.sort(folders, (a, b) -> a.getName().compareToIgnoreCase(b.getName()));
            for (File folder : folders) {
                if (folder.getName().equalsIgnoreCase(SHARED))
                    continue;
                long bytes = 0;
                int levels = 0;
                File[] files = folder.listFiles(File::isFile);
                if (files != null)
                    for (File file : files) {
                        bytes += file.length();
                        String lower = file.getName().toLowerCase(Locale.ROOT);
                        if (lower.endsWith(".map") && !resourceName(file.getName()) && header(file).mcc)
                            levels++;
                    }
                java.util.Properties workshop = new java.util.Properties();
                File info = new File(folder, WORKSHOP_FILE);
                if (info.isFile())
                    try (InputStream in = new FileInputStream(info)) {
                        workshop.load(in);
                    } catch (IOException ignored) {
                    }
                result.add(new Package(folder.getName(), folder, pass == 0, bytes, levels,
                    number(workshop.getProperty("id")), workshop.getProperty("title", folder.getName()),
                    number(workshop.getProperty("time_updated"))));
            }
        }
        return result;
    }

    private static long number(String text) {
        try {
            return text == null ? 0 : Long.parseLong(text.trim());
        } catch (NumberFormatException exception) {
            return 0;
        }
    }

    /** Switches a package on (into mcc_maps, where the game lists it) or off (aside, kept whole). */
    void setEnabled(Package item, boolean enabled) throws IOException {
        if (item.enabled == enabled)
            return;
        File base = enabled ? root : disabledRoot();
        if (!base.isDirectory() && !base.mkdirs())
            throw new IOException("cannot make " + base.getName());
        File target = new File(base, item.name);
        if (target.exists())
            throw new IOException("a package named " + item.name + " is already " + (enabled ? "enabled" : "disabled"));
        if (!item.folder.renameTo(target))
            throw new IOException("cannot move " + item.name);
    }

    /** Deletes a package (its maps, resources and descriptions). Saves are kept. */
    void delete(Package item) throws IOException {
        delete(item.folder);
    }

    /** the package name for a Workshop item: its title made safe, short enough for its levels' names */
    String workshopPackageName(long id, String title) {
        String name = safe(title == null ? "" : title.trim());
        if (name.length() > 24)
            name = name.substring(0, 24);
        while (name.endsWith("_") || name.endsWith("."))
            name = name.substring(0, name.length() - 1);
        if (name.isEmpty())
            name = "workshop_" + id;
        // (another item's package of that name keeps it: this one is numbered)
        for (int attempt = 1; ; attempt++) {
            String candidate = attempt == 1 ? name : name + "_" + attempt;
            boolean taken = false;
            for (File base : new File[] { root, disabledRoot() }) {
                File info = new File(new File(base, candidate), WORKSHOP_FILE);
                File folder = new File(base, candidate);
                if (folder.exists()) {
                    java.util.Properties p = new java.util.Properties();
                    if (info.isFile())
                        try (InputStream in = new FileInputStream(info)) {
                            p.load(in);
                        } catch (IOException ignored) {
                        }
                    if (number(p.getProperty("id")) != id)
                        taken = true;
                }
            }
            if (!taken)
                return candidate;
        }
    }

    /** What installing a downloaded Workshop item did. */
    static final class Installed {
        final String packageName;
        final int levels, resources;
        final List<String> skipped;

        Installed(String packageName, int levels, int resources, List<String> skipped) {
            this.packageName = packageName;
            this.levels = levels;
            this.resources = resources;
            this.skipped = skipped;
        }
    }

    /**
     * Installs a downloaded Workshop item (its files under downloaded) as a
     * package: its Halo 1 MCC levels, the bitmaps.map / sounds.map / loc.map
     * beside them and descriptions (.txt), any depth up to four. An update
     * replaces the item's package where it is (enabled or not). Nothing is
     * installed, and an IOException says why, when the item has no Halo 1
     * MCC map (an item for another game of the collection, or no maps).
     */
    Installed installWorkshop(File downloaded, long id, String title, long timeUpdated) throws IOException {
        List<File> files = new java.util.ArrayList<>();
        collect(downloaded, files, 0);
        List<File> levels = new java.util.ArrayList<>();
        List<String> skipped = new java.util.ArrayList<>();
        for (File file : files) {
            String lower = file.getName().toLowerCase(Locale.ROOT);
            if (lower.endsWith(".map") && !resourceName(file.getName())) {
                if (header(file).mcc)
                    levels.add(file);
                else
                    skipped.add(file.getName());
            }
        }
        if (levels.isEmpty())
            throw new IOException("\"" + title + "\" has no Halo 1 MCC maps"
                + (skipped.isEmpty() ? "" : " (" + skipped.size() + " maps of another Halo game or format)")
                + ": only Halo: Combat Evolved maps for MCC play here.");
        String name = workshopPackageName(id, title);
        File existing = new File(disabledRoot(), name);
        File base = existing.isDirectory() ? disabledRoot() : root;
        File folder = new File(base, name);
        File staging = new File(base, name + ".installing");
        delete(staging);
        if (!staging.mkdirs())
            throw new IOException("cannot make " + staging.getName());
        int resourceCount = 0, levelCount = 0;
        java.util.Set<String> used = new java.util.HashSet<>();
        for (File level : levels) {
            String target = safe(level.getName());
            String stem = target.substring(0, target.length() - 4);
            if (stem.isEmpty() || name.length() + 1 + stem.length() > MAXIMUM_RELATIVE ||
                    !used.add(target.toLowerCase(Locale.ROOT))) {
                skipped.add(level.getName());
                continue;
            }
            try (InputStream in = new FileInputStream(level)) {
                copy(in, new File(staging, target));
            }
            levelCount++;
            File parent = level.getParentFile();
            File[] beside = parent == null ? null : parent.listFiles(File::isFile);
            if (beside != null)
                for (File other : beside) {
                    String otherLower = other.getName().toLowerCase(Locale.ROOT);
                    boolean description = otherLower.equals(stem.toLowerCase(Locale.ROOT) + ".txt");
                    if ((resourceName(other.getName()) || description) && used.add(otherLower)) {
                        try (InputStream in = new FileInputStream(other)) {
                            copy(in, new File(staging, otherLower));
                        }
                        resourceCount++;
                    }
                }
        }
        java.util.Properties info = new java.util.Properties();
        info.setProperty("id", Long.toString(id));
        info.setProperty("title", title == null ? "" : title);
        info.setProperty("time_updated", Long.toString(timeUpdated));
        try (OutputStream out = new FileOutputStream(new File(staging, WORKSHOP_FILE))) {
            info.store(out, "Steam Workshop item (MCC, Halo 1), installed by the launcher");
        }
        delete(folder);
        if (!staging.renameTo(folder)) {
            delete(staging);
            throw new IOException("cannot install " + name);
        }
        return new Installed(name, levelCount, resourceCount, skipped);
    }

    private static void collect(File folder, List<File> files, int depth) {
        File[] inner = folder.listFiles();
        if (inner == null)
            return;
        for (File file : inner) {
            if (file.isDirectory()) {
                if (depth < 4 && !file.getName().startsWith("."))
                    collect(file, files, depth + 1);
            } else {
                files.add(file);
            }
        }
    }

    private static void delete(File file) throws IOException {
        File[] inner = file.listFiles();
        if (inner != null)
            for (File each : inner)
                delete(each);
        if (file.exists() && !file.delete())
            throw new IOException("cannot remove " + file.getName());
    }
}
