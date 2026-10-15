package com.halo.decomp;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Mods made of Halo Custom Edition campaign maps, which replace the
 * campaign's own: downloaded, swapped in with the originals kept aside, and
 * swapped back out.
 *
 * Under the game's data root (the folder holding maps/):
 * <ul>
 * <li>mods/&lt;mod&gt;/maps: the mod's maps while it is not in, and their
 * converted sounds (&lt;map&gt;.map.audio, which the game writes beside a
 * Custom Edition map the first time it loads it,
 * port/linux/game/custom_edition_cache.c);</li>
 * <li>mods/original: the campaign maps the mod's took the place of;</li>
 * <li>mods/&lt;mod&gt;.on while the mod is in, and mods/custom_edition.on,
 * which has the game load Custom Edition maps
 * (port/android/host/host_main.c).</li>
 * </ul>
 * Maps move between those folders by renaming, on one file system, so
 * swapping is instant and nothing is stored twice.
 */
final class ModInstaller {
    interface Progress {
        void report(String text, int permille);
    }

    /** A map of a mod: its file, halomaps.org's file id (0: an extra level,
     * with no campaign map of that name to put aside; -1: imported, not
     * downloaded), its exact size. */
    static final class ModMap {
        final String name;
        final int fid;
        final long size;

        ModMap(String name, int fid, long size) {
            this.name = name;
            this.fid = fid;
            this.size = size;
        }
    }

    static final class Mod {
        final String id;
        final String title;
        final String description;
        final ModMap[] maps;
        /** Test66: ".map" (Custom Edition) or ".yelo" (an OpenSauce cache,
         * which the game takes when no .map of that name is there) */
        final String extension;
        /** Test66: its maps are imported from a folder the player copied to
         * the headset (not downloaded) */
        final boolean imported;
        /** Test66: the name of its own resource maps (OpenSauce mod data
         * files, maps/data_files/&lt;name&gt;-bitmaps.map ...), or null: it
         * takes Custom Edition's own (mods/ce) */
        final String dataFiles;
        /** a note shown first in its panel, or null */
        final String note;
        /** Test70: how well it plays in this build, shown on its button and
         * in its panel (STATUS_SUPPORTED or STATUS_EXPERIMENTAL) */
        final String status;
        /** Test70: what the player brings, for the setup steps */
        final String requirement;

        Mod(String id, String title, String description, ModMap[] maps, String status, String requirement) {
            this(id, title, description, maps, ".map", false, null, null, status, requirement);
        }

        Mod(String id, String title, String description, ModMap[] maps, String extension, boolean imported,
                String dataFiles, String note, String status, String requirement) {
            this.id = id;
            this.title = title;
            this.description = description;
            this.maps = maps;
            this.extension = extension;
            this.imported = imported;
            this.dataFiles = dataFiles;
            this.note = note;
            this.status = status;
            this.requirement = requirement;
        }

        boolean needsResources() {
            return dataFiles == null;
        }

        /** Test70: only levels of its own (Lumoria): no campaign map is
         * replaced, and the original campaign still plays beside it */
        boolean addsLevelsOnly() {
            for (ModMap map : maps)
                if (map.fid != 0)
                    return false;
            return true;
        }

        boolean supported() {
            return STATUS_SUPPORTED.equals(status);
        }

        /** the launcher's button: its title and status */
        String buttonLabel() {
            return title + " — " + status;
        }

        long totalBytes() {
            long total = 0;
            for (ModMap map : maps)
                total += map.size;
            return total;
        }
    }

    /** Test70: the launcher's honest status labels (the owner's words) */
    static final String STATUS_SUPPORTED = "Supported";
    static final String STATUS_EXPERIMENTAL = "Experimental — currently not working";

    /**
     * SPV1: the Custom Mapping Team's single player campaign for Halo Custom
     * Edition (2006), from halomaps.org ("CMT Version - Single Player"
     * levels). Its maps are "protected", which the game's Custom Edition
     * loader undoes (cache_file_formats.c), and keep most sounds as Ogg
     * Vorbis, which the game converts the first time each level loads.
     */
    static final Mod SPV1 = new Mod("spv1", "SPV1 - CMT Single Player Campaign",
        // (counted from the maps' tags against the original levels': weapons,
        // vehicles, AI characters)
        "The Custom Mapping Team's 2006 remake of all ten campaign levels, made for Halo Custom Edition.\n\n"
            + "• New weapons: about twice the kinds in every level (29 on Halo, where the original has 10)\n"
            + "• New and redesigned enemies and characters, with more kinds in every level\n"
            + "• Many more vehicles (17 on Halo against 6, 23 on The Silent Cartographer against 7, "
            + "and vehicles in The Library)\n"
            + "• Added detail to the levels' environments, and visual changes throughout\n\n"
            + "Download: about 960 MB from halomaps.org; 2.2 GB once installed, and up to 1.1 GB more as "
            + "each level converts its sounds the first time it loads (a minute or two, once). Needs Halo "
            + "Custom Edition's own bitmaps.map, sounds.map and loc.map. Restoring puts the original "
            + "campaign back; SPV1 stays downloaded to switch back in at once.",
        new ModMap[] {
            new ModMap("a10", 1921, 264601050L),
            new ModMap("a30", 1920, 202016403L),
            new ModMap("a50", 1919, 206788649L),
            new ModMap("b30", 1918, 201578087L),
            new ModMap("b40", 1917, 265311261L),
            new ModMap("c10", 1916, 231297155L),
            new ModMap("c20", 1915, 164865081L),
            new ModMap("c40", 1914, 247495074L),
            new ModMap("d20", 1913, 183851031L),
            new ModMap("d40", 1912, 264367517L),
        }, STATUS_SUPPORTED,
        "CMT's 2006 SPV1 maps (import your copy or use Download and install) and the original PC Halo Custom "
            + "Edition bitmaps.map, sounds.map and loc.map.");

    /** Test66: an OpenSauce mod's own resource maps (data_files), by type */
    static final String[] DATA_FILE_NAMES = { "bitmaps", "sounds", "loc" };

    /**
     * Test66: The Altheros Experience (Altheros/Eric's Halo 1 campaign mod,
     * private beta of 2019-10-24, moddb.com): ten OpenSauce caches (.yelo,
     * with OpenSauce's memory upgrades) and their own resource maps, which
     * its download names -bitmaps.map, -sounds.map, -loc.map and its maps
     * look for as alsthetic-bitmaps.map and so on (their header's mod name).
     * Not downloadable from here: the player copies its extracted folder to
     * the headset and imports it once.
     */
    static final long[] ALTHEROS_DATA_SIZES = { 613838703L, 333893198L, 447783L };
    static final Mod ALTHEROS = new Mod("altheros", "The Altheros Experience",
        "Altheros's Halo 1 campaign mod (private beta, October 2019): reworked encounters, weapons, effects "
            + "and scripts across the campaign, as OpenSauce maps with their own textures and sounds, plus F10 "
            + "(a reworked Stockade).\n\n"
            + "Not downloaded by the app: get \"Latest Altheros Experience 10.24.2019\" from moddb.com, extract it on "
            + "a computer, and copy its folder (the .yelo files and data_files) to this headset's Download folder "
            + "over USB or SideQuest. Then tap Import and choose that folder. About 3.4 GB once imported; up to "
            + "about 1 GB more as each level converts its sounds the first time it loads. It does not need Halo "
            + "Custom Edition's resource maps. Restoring puts the original campaign back; the mod stays imported "
            + "to switch back in at once.",
        new ModMap[] {
            new ModMap("a10", -1, 445975615L),
            new ModMap("a30", -1, 265656975L),
            new ModMap("a50", -1, 282819945L),
            new ModMap("b30", -1, 203202172L),
            new ModMap("b40", -1, 286599712L),
            new ModMap("c10", -1, 288881469L),
            new ModMap("c20", -1, 130631356L),
            new ModMap("c40", -1, 280472000L),
            new ModMap("d20", -1, 225382362L),
            new ModMap("f10", 0, 275791328L),
        }, ".yelo", true, "alsthetic",
        "A work-in-progress beta, as its author says (its ReadMe): in A10 do not skip the opening or closing "
            + "cinematics; A30's first Banshees do not spawn and some areas load late; clear encounters before "
            + "moving on in A30 and B30; B40's effects stop if many encounters are skipped; the C40 flamethrower "
            + "is weak; D20's encounters are hard. A50, C10, C20 and D20 keep mostly stock encounters.",
        // Test70: the owner's Test67 headset log still ends in game_load()
        // failing (the blue screen); kept available for future work
        STATUS_EXPERIMENTAL,
        "the author's Latest Altheros Experience 10.24.2019 files (.yelo and data_files), from your own copy.");

    /**
     * Test70: Project Lumoria (TM Mapping Team, 2012): a campaign of its own
     * in four Halo Custom Edition levels (lumoria_a to lumoria_d), made under
     * Microsoft's Game Content Usage Rules. Not downloaded by the app (its
     * authors gave no permission to redistribute it): the player imports
     * their copy of the Lumoria_Full_Campaign archive or its extracted
     * folder. Its maps replace none of the campaign's (file id 0), so the
     * original campaign still plays beside it; its own ui.map and Windows
     * sound DLLs are not used (the game keeps the Xbox's menus). Like SPV1
     * it takes Custom Edition's own resource maps.
     */
    static final Mod LUMORIA = new Mod("lumoria", "Project Lumoria",
        "The TM Mapping Team's 2012 campaign for Halo Custom Edition: May, a female SPARTAN-II, and a squad of "
            + "ODSTs on the Forerunner world of Lumoria. Two episodes in four new levels, with their own story, "
            + "voice acting, music and encounters.\n\n"
            + "Not downloaded by the app: import your copy of Lumoria_Full_Campaign.zip (halomaps.org, moddb.com) "
            + "straight from this device's Download folder, or its extracted folder. About 860 MB once imported, "
            + "and more as each level converts its sounds the first time it loads. Needs Halo Custom Edition's "
            + "own bitmaps.map, sounds.map and loc.map, as SPV1 does. Installing adds Lumoria's levels; the "
            + "original campaign stays playable. In the game: New Game, map kind CUSTOM SINGLEPLAYER, lumoria_a.",
        new ModMap[] {
            new ModMap("lumoria_a", 0, 274873434L),
            new ModMap("lumoria_b", 0, 228054210L),
            new ModMap("lumoria_c", 0, 198269022L),
            new ModMap("lumoria_d", 0, 191220134L),
        }, ".map", true, null, null, STATUS_SUPPORTED,
        "your Lumoria_Full_Campaign.zip (or its extracted folder) and the original PC Halo Custom Edition "
            + "bitmaps.map, sounds.map and loc.map. Lumoria's own ui.map and sound DLLs are not used.");

    /** Every campaign mod the launcher offers. */
    static final Mod[] MODS = { SPV1, LUMORIA, ALTHEROS };

    private static final String DETAIL_URL = "https://www.halomaps.org/hce/detail.cfm";
    private static final String USER_AGENT = "Mozilla/5.0 (Android; Halo CE VR launcher)";
    private static final Pattern HASH = Pattern.compile("name=\"hash\" value=\"([0-9A-Fa-f]{32})\"");

    private final File root;

    ModInstaller(File root) {
        this.root = root;
    }

    private File modsDirectory() {
        return new File(root, "mods");
    }

    private File modMaps(Mod mod) {
        return new File(new File(modsDirectory(), mod.id), "maps");
    }

    private File originals() {
        return new File(modsDirectory(), "original");
    }

    private File gameMaps() {
        return new File(root, "maps");
    }

    private File marker(Mod mod) {
        return new File(modsDirectory(), mod.id + ".on");
    }

    private File pendingMarker(Mod mod) {
        return new File(modsDirectory(), mod.id + ".changing");
    }

    boolean recoveryNeeded(Mod mod) {
        return pendingMarker(mod).isFile();
    }

    private File customEditionMarker() {
        return new File(modsDirectory(), "custom_edition.on");
    }

    boolean installed(Mod mod) {
        return marker(mod).isFile() || recoveryNeeded(mod);
    }

    /** Test66: the campaign mod in the game now, or null (the original). */
    Mod installedMod() {
        for (Mod mod : MODS)
            if (installed(mod))
                return mod;
        return null;
    }

    /** Test66: an interrupted change of any mod. */
    Mod recoveryMod() {
        for (Mod mod : MODS)
            if (recoveryNeeded(mod))
                return mod;
        return null;
    }

    private File modDataFiles(Mod mod) {
        return new File(new File(modsDirectory(), mod.id), "data_files");
    }

    private File gameDataFiles() {
        return new File(gameMaps(), "data_files");
    }

    private String dataFileName(Mod mod, int type) {
        return mod.dataFiles + "-" + DATA_FILE_NAMES[type] + ".map";
    }

    // ---------- Halo Custom Edition's resource maps

    /**
     * Custom Edition maps take some of their textures' pixels and sounds'
     * samples from Custom Edition's own bitmaps.map, sounds.map and loc.map,
     * which come with the game (not with the mods, and not with the Xbox's
     * data): the player brings them once, from a Custom Edition installation's
     * maps folder (its stock ones), into mods/ce. Their headers' first word
     * says which they are.
     */
    static final String[] RESOURCE_NAMES = { "bitmaps", "sounds", "loc" };

    /**
     * The original resource maps' sizes, as Halo Custom Edition installs
     * them (its patches leave them alone). Custom Edition maps name their
     * resources by index into these exact files: a modified bitmaps.map
     * (Halo Refined's, say) loads, but shows the wrong textures, so only
     * the original is taken.
     */
    static final long[] RESOURCE_SIZES = { 123547749L, 41718640L, 391996L };

    /** "117.8 MB" and the like. */
    static String megabytes(long bytes) {
        return String.format(java.util.Locale.ROOT, "%.1f MB", bytes / 1048576.0);
    }

    /** Whether a resource map of that type is the original, by its size. */
    static boolean resourceOriginal(int type, long size) {
        return size == RESOURCE_SIZES[type - 1];
    }

    private File resourceDirectory() {
        return new File(modsDirectory(), "ce");
    }

    /** The resource map type (1 bitmaps, 2 sounds, 3 loc) of a file's first bytes, or 0. */
    static int resourceType(byte[] header) {
        if (header.length < 4)
            return 0;
        int type = (header[0] & 0xff) | ((header[1] & 0xff) << 8) | ((header[2] & 0xff) << 16) | ((header[3] & 0xff) << 24);
        return type >= 1 && type <= 3 ? type : 0;
    }

    /** Where a resource map of that type is kept (whether or not it is there). */
    File resourceFile(int type) {
        return new File(resourceDirectory(), RESOURCE_NAMES[type - 1] + ".map");
    }

    /** The resource map of that type the mods have (kept aside, or in the game's maps), or null. */
    private File presentResource(int type) {
        File kept = resourceFile(type);
        File game = new File(gameMaps(), RESOURCE_NAMES[type - 1] + ".map");

        return kept.isFile() ? kept : game.isFile() ? game : null;
    }

    /** Every resource map present, and the original. */
    boolean haveResources() {
        for (int type = 1; type <= 3; type++) {
            File file = presentResource(type);

            if (file == null || !resourceOriginal(type, file.length()))
                return false;
        }
        return true;
    }

    /** What is still wanted of the resource maps, for the player. */
    String missingResources() {
        StringBuilder missing = new StringBuilder();

        for (int type = 1; type <= 3; type++) {
            File file = presentResource(type);
            String name = RESOURCE_NAMES[type - 1] + ".map";

            if (file == null)
                missing.append(missing.length() > 0 ? ", " : "").append(name);
            else if (!resourceOriginal(type, file.length()))
                missing.append(missing.length() > 0 ? ", " : "").append(name).append(" (the one there is ")
                    .append(megabytes(file.length())).append(", not the original's ")
                    .append(megabytes(RESOURCE_SIZES[type - 1])).append(")");
        }
        return missing.toString();
    }

    /** The resource maps go in with a Custom Edition mod, and out with it. */
    private void resourcesIn() throws IOException {
        for (int type = 1; type <= 3; type++) {
            File game = new File(gameMaps(), RESOURCE_NAMES[type - 1] + ".map");
            File original = new File(originals(), RESOURCE_NAMES[type - 1] + ".map");

            if (!resourceFile(type).isFile())
                continue;
            if (game.exists() && !original.exists())
                move(game, original);
            move(resourceFile(type), game);
        }
    }

    private void resourcesOut() throws IOException {
        File directory = resourceDirectory();

        if (!directory.isDirectory() && !directory.mkdirs())
            throw new IOException("cannot make " + directory);
        for (int type = 1; type <= 3; type++) {
            File game = new File(gameMaps(), RESOURCE_NAMES[type - 1] + ".map");
            File original = new File(originals(), RESOURCE_NAMES[type - 1] + ".map");

            if (game.exists() && !resourceFile(type).exists())
                move(game, resourceFile(type));
            if (original.exists())
                move(original, game);
        }
    }

    /** Where the player can put the resource maps with a computer instead. */
    String resourcePath() {
        return resourceDirectory().getAbsolutePath();
    }

    File resourceDirectoryMade() throws IOException {
        File directory = resourceDirectory();

        if (!directory.isDirectory() && !directory.mkdirs())
            throw new IOException("cannot make " + directory);
        return directory;
    }

    /** Every map of the mod downloaded whole (in or out of the game). */
    boolean downloaded(Mod mod) {
        for (ModMap map : mod.maps) {
            File out = new File(modMaps(mod), map.name + mod.extension);
            File in = new File(gameMaps(), map.name + mod.extension);
            boolean whole = (out.isFile() && out.length() == map.size) ||
                (installed(mod) && in.isFile() && in.length() == map.size);
            if (!whole)
                return false;
        }
        if (mod.dataFiles != null)
            for (int type = 0; type < DATA_FILE_NAMES.length; type++) {
                File out = new File(modDataFiles(mod), dataFileName(mod, type));
                File in = new File(gameDataFiles(), dataFileName(mod, type));
                long size = ALTHEROS_DATA_SIZES[type];
                if (!((out.isFile() && out.length() == size) || (installed(mod) && in.isFile() && in.length() == size)))
                    return false;
            }
        return true;
    }

    /** Include interrupted downloads so the launcher can offer cleanup. */
    boolean hasDownloadFiles(Mod mod) {
        File directory = modMaps(mod);
        for (ModMap map : mod.maps) {
            if (new File(directory, map.name + mod.extension).exists()
                    || new File(directory, map.name + mod.extension + ".part").exists()
                    || new File(directory, map.name + mod.extension + ".audio").exists()) return true;
        }
        return mod.dataFiles != null && modDataFiles(mod).isDirectory();
    }

    /** Test67: app-authored recipes carry provenance and hashes, never game assets.
     * Preparation is idempotent and only touches this mod's support directories. */
    void prepare(Mod mod, InputStream bundledRecipe, Progress progress) throws IOException {
        prepare(mod, bundledRecipe, progress, true);
    }

    void prepare(Mod mod, InputStream bundledRecipe, Progress progress, boolean verifyPresent) throws IOException {
        java.util.Properties recipe = new java.util.Properties();
        recipe.load(new java.io.InputStreamReader(bundledRecipe, StandardCharsets.UTF_8));
        if (!mod.id.equals(recipe.getProperty("mod.id")) || !"1".equals(recipe.getProperty("recipe.version")))
            throw new IOException("unsupported campaign setup recipe");
        for (String name : requiredFiles(mod)) {
            long[] size = new long[1];
            if (importTarget(mod, name, size) == null ||
                !Long.toString(size[0]).equals(recipe.getProperty("file." + name + ".size")) ||
                !recipe.getProperty("file." + name + ".sha256", "").matches("[0-9a-f]{64}"))
                throw new IOException("incomplete setup recipe for " + name);
        }
        File folder = modMaps(mod);
        if (!folder.isDirectory() && !folder.mkdirs()) throw new IOException("cannot prepare " + folder);
        if (mod.needsResources()) resourceDirectoryMade();
        else if (!modDataFiles(mod).isDirectory() && !modDataFiles(mod).mkdirs())
            throw new IOException("cannot prepare resource folder");
        File recipeFile = recipeFile(mod), partial = new File(recipeFile.getPath() + ".part");
        try (java.io.Writer out = new java.io.OutputStreamWriter(new FileOutputStream(partial), StandardCharsets.UTF_8)) {
            recipe.store(out, "HaloCE-Quest-VR setup metadata only; no game assets");
        }
        Files.move(partial.toPath(), recipeFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
        if (verifyPresent) validatePrepared(mod, false, progress);
        progress.report("Setup prepared. Included: folder setup, file checks and installation support. "
            + "Game/mod assets are supplied separately. Still needed: " + missingForSetup(mod), 1000);
    }

    private File recipeFile(Mod mod) {
        return new File(new File(modsDirectory(), mod.id), "support.properties");
    }

    private String[] requiredFiles(Mod mod) {
        java.util.ArrayList<String> names = new java.util.ArrayList<>();
        for (ModMap map : mod.maps) names.add(map.name + mod.extension);
        for (int t = 0; t < 3; t++) names.add(mod.needsResources() ? RESOURCE_NAMES[t] + ".map" : dataFileName(mod, t));
        return names.toArray(new String[0]);
    }

    String missingForSetup(Mod mod) {
        String missing = missingImports(mod);
        if (mod.needsResources() && !missingResources().isEmpty())
            missing += (missing.isEmpty() ? "" : ", ") + missingResources();
        return missing.isEmpty() ? "none" : missing;
    }

    private String expectedHash(Mod mod, String name) throws IOException {
        if (!recipeFile(mod).isFile()) return null; // older installations remain supported
        java.util.Properties recipe = new java.util.Properties();
        try (java.io.Reader in = new java.io.InputStreamReader(new FileInputStream(recipeFile(mod)), StandardCharsets.UTF_8)) {
            recipe.load(in);
        }
        String hash = recipe.getProperty("file." + name + ".sha256");
        if (hash == null || !hash.matches("[0-9a-f]{64}")) throw new IOException("prepare mod files again: missing hash for " + name);
        return hash;
    }

    private static boolean hashMatches(File file, String expected) throws IOException {
        if (expected == null) return true;
        try {
            java.security.MessageDigest digest = java.security.MessageDigest.getInstance("SHA-256");
            try (InputStream in = new BufferedInputStream(new FileInputStream(file), 1 << 16)) {
                byte[] buffer = new byte[1 << 16]; int count;
                while ((count = in.read(buffer)) != -1) digest.update(buffer, 0, count);
            }
            StringBuilder actual = new StringBuilder();
            for (byte b : digest.digest()) actual.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
            return actual.toString().equals(expected);
        } catch (java.security.NoSuchAlgorithmException exception) { throw new IOException(exception); }
    }

    void validatePrepared(Mod mod, boolean requireAll, Progress progress) throws IOException {
        for (String name : requiredFiles(mod)) {
            long[] expected = new long[1]; File file = importTarget(mod, name, expected);
            if (!file.isFile() && installed(mod)) file = new File(
                mod.dataFiles != null && name.startsWith(mod.dataFiles + "-") ? gameDataFiles() : gameMaps(), name);
            if (mod.needsResources()) for (int t = 1; t <= 3; t++)
                if (name.equals(RESOURCE_NAMES[t - 1] + ".map") && presentResource(t) != null) file = presentResource(t);
            if (!file.isFile()) {
                if (requireAll) throw new IOException("missing " + name);
                continue;
            }
            progress.report("Checking " + name + "...", -1);
            if (file.length() != expected[0] || !hashMatches(file, expectedHash(mod, name)))
                throw new IOException(name + " does not match the supported version (size/SHA-256). Import the complete original mod file again.");
        }
    }

    /** Downloads what is missing, then swaps the mod's maps in. */
    void install(Mod mod, Progress progress) throws IOException {
        File maps = modMaps(mod);
        long total = mod.totalBytes(), done = 0;

        if (installed(mod))
            return;
        // Test66: one campaign mod at a time: another in the game goes back out first
        Mod other = installedMod();
        if (mod.imported) {
            if (!downloaded(mod))
                throw new IOException("import " + mod.title + "'s folder first");
            if (mod.needsResources() && !haveResources())
                throw new IOException("Custom Edition's resource maps are needed first (" + missingResources() + ")");
            progress.report("Swapping the campaign's maps for " + mod.title + "...", 1000);
            validatePrepared(mod, true, progress);
            if (other != null && other != mod) restore(other, progress);
            swapIn(mod);
            return;
        }
        if (mod.needsResources() && !haveResources())
            throw new IOException("Custom Edition's resource maps are needed first (" + missingResources() + ")");
        if (!maps.isDirectory() && !maps.mkdirs())
            throw new IOException("cannot make " + maps);
        for (int index = 0; index < mod.maps.length; index++) {
            ModMap map = mod.maps[index];
            File file = new File(maps, map.name + ".map");

            if (!(file.isFile() && file.length() == map.size))
                download(map, file, index, mod.maps.length, done, total, progress);
            done += map.size;
        }
        progress.report("Swapping the campaign's maps for " + mod.title + "...", 1000);
        validatePrepared(mod, true, progress);
        if (other != null && other != mod) restore(other, progress);
        swapIn(mod);
    }

    private void download(ModMap map, File file, int index, int count, long done, long total, Progress progress)
        throws IOException {
        String label = "Downloading " + map.name + " (" + (index + 1) + " of " + count + ")";
        String detail = DETAIL_URL + "?fid=" + map.fid;
        File partial = new File(file.getPath() + ".part");

        progress.report(label + "...", (int) (done * 1000 / total));
        String page = get(detail);
        Matcher matcher = HASH.matcher(page);
        if (!matcher.find())
            throw new IOException("halomaps.org's page for " + map.name + " has no download");

        HttpURLConnection connection = (HttpURLConnection) new URL(DETAIL_URL).openConnection();
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        connection.setConnectTimeout(30000);
        connection.setReadTimeout(60000);
        connection.setRequestProperty("User-Agent", USER_AGENT);
        connection.setRequestProperty("Referer", detail);
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        try (OutputStream out = connection.getOutputStream()) {
            out.write(("fid=" + map.fid + "&action=dl&hash=" + matcher.group(1) + "&submit=download")
                .getBytes(StandardCharsets.US_ASCII));
        }
        if (connection.getResponseCode() != 200)
            throw new IOException("halomaps.org answered " + connection.getResponseCode() + " for " + map.name);

        // the archive is read as it arrives, its map written straight out
        try (CountingStream counted = new CountingStream(new BufferedInputStream(connection.getInputStream()));
             ZipInputStream zip = new ZipInputStream(counted)) {
            long archive = connection.getContentLengthLong();
            ZipEntry entry;
            boolean found = false;

            while ((entry = zip.getNextEntry()) != null) {
                String name = new File(entry.getName()).getName();

                if (!name.equalsIgnoreCase(map.name + ".map"))
                    continue;
                found = true;
                try (OutputStream out = new FileOutputStream(partial)) {
                    byte[] buffer = new byte[1 << 16];
                    long written = 0, reported = 0;
                    int read;

                    while ((read = zip.read(buffer)) > 0) {
                        out.write(buffer, 0, read);
                        written += read;
                        if (written - reported > (4 << 20)) {
                            reported = written;
                            long fraction = archive > 0 ? counted.count * map.size / archive : written;
                            progress.report(label + ": " + (counted.count >> 20) + " of "
                                    + (archive > 0 ? (archive >> 20) + " MB" : "? MB"),
                                (int) ((done + Math.min(fraction, map.size)) * 1000 / total));
                        }
                    }
                }
                break;
            }
            if (!found)
                throw new IOException("the download of " + map.name + " holds no " + map.name + ".map");
        } finally {
            connection.disconnect();
        }
        if (partial.length() != map.size) {
            long size = partial.length();
            partial.delete();
            throw new IOException(map.name + ".map is " + size + " bytes, not the " + map.size + " expected");
        }
        if (!partial.renameTo(file))
            throw new IOException("cannot keep " + file);
    }

    private static String get(String address) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(30000);
        connection.setReadTimeout(60000);
        connection.setRequestProperty("User-Agent", USER_AGENT);
        try (InputStream in = connection.getInputStream()) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[1 << 14];
            int read;

            while ((read = in.read(buffer)) > 0)
                bytes.write(buffer, 0, read);
            return bytes.toString("ISO-8859-1");
        } finally {
            connection.disconnect();
        }
    }

    private static void move(File from, File to) throws IOException {
        if (!from.exists())
            return;
        // Same-filesystem atomic replacement: a failed move must not first
        // delete the only surviving destination copy.
        Files.move(from.toPath(), to.toPath(), StandardCopyOption.ATOMIC_MOVE,
                StandardCopyOption.REPLACE_EXISTING);
    }

    /** The originals aside, the mod's maps (and their converted sounds) in. */
    private void swapIn(Mod mod) throws IOException {
        File originals = originals();

        if (!originals.isDirectory() && !originals.mkdirs())
            throw new IOException("cannot make " + originals);
        for (ModMap map : mod.maps) {
            if (map.fid != 0 && !new File(originals, map.name + ".map").isFile()
                    && !isXboxMap(new File(gameMaps(), map.name + ".map")))
                throw new IOException("original Xbox campaign map missing: " + map.name);
        }
        touch(pendingMarker(mod));
        for (ModMap map : mod.maps) {
            File game = new File(gameMaps(), map.name + ".map");
            File original = new File(originals, map.name + ".map");
            File modded = new File(gameMaps(), map.name + mod.extension);

            // (an original already aside stays; the game's file is then a
            // mod's, from an interrupted swap). Test66: a .yelo goes in beside
            // where the original was: the game takes it when no .map is there
            if (map.fid != 0 && !original.exists())
                move(game, original);
            move(new File(modMaps(mod), map.name + mod.extension), modded);
            move(new File(modMaps(mod), map.name + mod.extension + ".audio"),
                new File(gameMaps(), map.name + mod.extension + ".audio"));
        }
        if (mod.dataFiles != null) {
            if (!gameDataFiles().isDirectory() && !gameDataFiles().mkdirs())
                throw new IOException("cannot make " + gameDataFiles());
            for (int type = 0; type < DATA_FILE_NAMES.length; type++)
                move(new File(modDataFiles(mod), dataFileName(mod, type)), new File(gameDataFiles(), dataFileName(mod, type)));
        }
        if (mod.needsResources())
            resourcesIn();
        touch(marker(mod));
        touch(customEditionMarker());
        deleteChecked(pendingMarker(mod));
    }

    /** The mod's maps out (kept, to go back in at once), the originals back. */
    void restore(Mod mod, Progress progress) throws IOException {
        File maps = modMaps(mod);

        progress.report("Putting the original campaign back...", 0);
        // A retry after an interrupted restore may already have returned a
        // stock map. Missing backup + a mod still active is not success.
        for (ModMap map : mod.maps) {
            File original = new File(originals(), map.name + ".map");
            if (map.fid != 0 && !original.isFile() && !isXboxMap(new File(gameMaps(), map.name + ".map")))
                throw new IOException("original backup missing for " + map.name
                        + "; mod files kept. Restore this map from your original Halo disc before retrying.");
        }
        touch(pendingMarker(mod));
        if (!maps.isDirectory() && !maps.mkdirs())
            throw new IOException("cannot make " + maps);
        for (ModMap map : mod.maps) {
            File game = new File(gameMaps(), map.name + ".map");
            File original = new File(originals(), map.name + ".map");
            File modded = new File(gameMaps(), map.name + mod.extension);

            if (original.exists() || map.fid == 0 || !mod.extension.equals(".map")) {
                // (Test66: a .yelo is the mod's whether or not an original was put aside)
                if (mod.extension.equals(".map") ? original.exists() || map.fid == 0 : modded.exists())
                    move(modded, new File(maps, map.name + mod.extension));
                move(new File(gameMaps(), map.name + mod.extension + ".audio"),
                    new File(maps, map.name + mod.extension + ".audio"));
                if (original.exists())
                    move(original, game);
            }
        }
        if (mod.dataFiles != null) {
            if (!modDataFiles(mod).isDirectory() && !modDataFiles(mod).mkdirs())
                throw new IOException("cannot make " + modDataFiles(mod));
            for (int type = 0; type < DATA_FILE_NAMES.length; type++)
                move(new File(gameDataFiles(), dataFileName(mod, type)), new File(modDataFiles(mod), dataFileName(mod, type)));
        }
        if (mod.needsResources())
            resourcesOut();
        deleteChecked(customEditionMarker());
        deleteChecked(marker(mod));
        deleteChecked(pendingMarker(mod));
        progress.report("The original campaign is back.", 1000);
    }

    private static boolean isXboxMap(File file) throws IOException {
        if (!file.isFile()) return false;
        byte[] header = new byte[8];
        try (InputStream in = new FileInputStream(file)) {
            int read = 0, count;
            while (read < header.length && (count = in.read(header, read, header.length - read)) > 0)
                read += count;
            // Cache header 'head', little-endian fourcc, version 5 (Xbox).
            return read == 8 && header[0] == 'd' && header[1] == 'a'
                    && header[2] == 'e' && header[3] == 'h'
                    && header[4] == 5 && header[5] == 0 && header[6] == 0 && header[7] == 0;
        }
    }

    private static void deleteChecked(File file) throws IOException {
        if (file.exists() && !file.delete()) throw new IOException("cannot delete " + file);
    }

    /** Uninstall restores first; a restoration failure never deletes the mod. */
    void delete(Mod mod, Progress progress) throws IOException {
        if (installed(mod)) restore(mod, progress);
        File[] files = modMaps(mod).listFiles();
        if (files == null && modMaps(mod).exists())
            throw new IOException("cannot list downloaded maps in " + modMaps(mod));
        if (files != null) for (File file : files) {
            // Delete only files owned by this mod, never originals/CE resources
            // or an unexpected directory supplied by the user.
            for (ModMap map : mod.maps) {
                String name = file.getName();
                if (name.equals(map.name + mod.extension) || name.equals(map.name + mod.extension + ".audio")
                        || name.equals(map.name + mod.extension + ".part")) {
                    if (file.isDirectory()) throw new IOException("unexpected directory: " + file);
                    deleteChecked(file);
                    break;
                }
            }
        }
        if (mod.dataFiles != null)
            for (int type = 0; type < DATA_FILE_NAMES.length; type++) {
                deleteChecked(new File(modDataFiles(mod), dataFileName(mod, type)));
                deleteChecked(new File(modDataFiles(mod), dataFileName(mod, type) + ".part"));
            }
        progress.report("Original campaign restored; downloaded mod maps removed.", 1000);
    }

    /**
     * Test66: where an imported mod's file goes, by its name as the player's
     * folder has it: a map (a10.yelo) or one of its resource maps (the
     * download's -bitmaps.map, or alsthetic-bitmaps.map), else null.
     * expected: its exact size.
     */
    File importTarget(Mod mod, String name, long[] expected) {
        String lower = name.toLowerCase(java.util.Locale.ROOT);
        for (ModMap map : mod.maps)
            if (lower.equals(map.name + mod.extension)) {
                expected[0] = map.size;
                return new File(modMaps(mod), map.name + mod.extension);
            }
        if (mod.dataFiles != null)
            for (int type = 0; type < DATA_FILE_NAMES.length; type++)
                if (lower.equals("-" + DATA_FILE_NAMES[type] + ".map") || lower.equals(dataFileName(mod, type))) {
                    expected[0] = ALTHEROS_DATA_SIZES[type];
                    return new File(modDataFiles(mod), dataFileName(mod, type));
                }
        if (mod.needsResources())
            for (int type = 1; type <= 3; type++)
                if (lower.equals(RESOURCE_NAMES[type - 1] + ".map")) {
                    expected[0] = RESOURCE_SIZES[type - 1];
                    return resourceFile(type);
                }
        return null;
    }

    /** Test66: an imported file copied in (to .part, kept only when whole). */
    void importFile(Mod mod, InputStream in, File target, long expected, String label, Progress progress)
            throws IOException {
        File directory = target.getParentFile();
        File partial = new File(target.getPath() + ".part");

        if (target.isFile() && target.length() == expected && hashMatches(target, expectedHash(mod, target.getName())))
            return;
        if (installed(mod))
            throw new IOException(mod.title + " is in the game: restore the original campaign before importing again");
        if (!directory.isDirectory() && !directory.mkdirs())
            throw new IOException("cannot make " + directory);
        try (OutputStream out = new FileOutputStream(partial)) {
            byte[] buffer = new byte[1 << 16];
            long written = 0, reported = 0;
            int read;

            while ((read = in.read(buffer)) > 0) {
                out.write(buffer, 0, read);
                written += read;
                if (written > expected) throw new IOException(label + " exceeds the supported file size");
                if (written - reported > (8 << 20)) {
                    reported = written;
                    progress.report(label + ": " + (written >> 20) + " of " + (expected >> 20) + " MB",
                        (int) Math.min(1000, written * 1000 / Math.max(1, expected)));
                }
            }
        }
        if (partial.length() != expected) {
            long size = partial.length();
            partial.delete();
            throw new IOException(target.getName() + " is " + size + " bytes, not the " + expected + " expected");
        }
        if (!hashMatches(partial, expectedHash(mod, target.getName()))) {
            partial.delete();
            throw new IOException(target.getName() + " failed SHA-256 verification; existing files preserved");
        }
        Files.move(partial.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING);
    }

    /**
     * Test70: an imported mod's files taken straight out of its archive (a
     * .zip as its authors published it): each entry is matched by its file
     * name alone, as a folder's are (importTarget), so the archive's own
     * folders do not matter, and anything else in it (a mod's ui.map, its
     * Windows DLLs, readmes) is left out. Returns how many files it kept.
     */
    int importZip(Mod mod, InputStream archive, Progress progress) throws IOException {
        int copied = 0;
        try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(archive, 1 << 16))) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (entry.isDirectory())
                    continue;
                String name = entry.getName().replace('\\', '/');
                name = name.substring(name.lastIndexOf('/') + 1);
                long[] expected = new long[1];
                File target = importTarget(mod, name, expected);
                if (target == null)
                    continue;
                // (importFile reads to the entry's end, which ZipInputStream
                // gives as the end of its stream, and leaves it open)
                importFile(mod, zip, target, expected[0], "Importing " + name, progress);
                copied++;
            }
        }
        return copied;
    }

    /** Test66: what an imported mod still lacks, for the player. */
    String missingImports(Mod mod) {
        StringBuilder missing = new StringBuilder();
        for (ModMap map : mod.maps) {
            File out = new File(modMaps(mod), map.name + mod.extension);
            File in = new File(gameMaps(), map.name + mod.extension);
            if (!((out.isFile() && out.length() == map.size) || (installed(mod) && in.isFile() && in.length() == map.size)))
                missing.append(missing.length() > 0 ? ", " : "").append(map.name).append(mod.extension);
        }
        if (mod.dataFiles != null)
            for (int type = 0; type < DATA_FILE_NAMES.length; type++) {
                File out = new File(modDataFiles(mod), dataFileName(mod, type));
                File in = new File(gameDataFiles(), dataFileName(mod, type));
                long size = ALTHEROS_DATA_SIZES[type];
                if (!((out.isFile() && out.length() == size) || (installed(mod) && in.isFile() && in.length() == size)))
                    missing.append(missing.length() > 0 ? ", " : "").append("data_files/-")
                        .append(DATA_FILE_NAMES[type]).append(".map");
            }
        return missing.toString();
    }

    private static void touch(File file) throws IOException {
        File parent = file.getParentFile();

        if (parent != null && !parent.isDirectory())
            parent.mkdirs();
        try (OutputStream out = new FileOutputStream(file)) {
            out.write('\n');
        }
    }

    /** Counts the bytes read through it (the archive's, for progress). */
    private static final class CountingStream extends FilterInputStream {
        long count;

        CountingStream(InputStream in) {
            super(in);
        }

        @Override
        public int read() throws IOException {
            int value = super.read();
            if (value >= 0)
                count++;
            return value;
        }

        @Override
        public int read(byte[] buffer, int offset, int length) throws IOException {
            int read = super.read(buffer, offset, length);
            if (read > 0)
                count += read;
            return read;
        }
    }
}
