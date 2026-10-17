package com.halo.decomp;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.zip.*;

/**
 * Test72 (a player's suggestion: "ability to import savefiles from zip or
 * folder"): saves brought in from a .zip or a folder, and taken out as one.
 *
 * A game-data set's saves are its save folder (the game's z:\ and u:\):
 * z/saved (player profiles, playlists, recordings), z/savegame.bin (the
 * campaign's checkpoint) and u/UDATA (Xbox save containers). What is
 * brought in is recognised by those names wherever they lie in it: a copy of
 * another device's save folder, its z or saved folder alone, a
 * player_profiles folder, a savegame.bin, or an Xbox dump's UDATA folder.
 * The caches (z/cache*.map, z/maps, any .map) are never taken. Every import
 * first backs the current saves up (save-backups/, next to the set), then
 * puts each file in place: files of the same name are replaced, others kept.
 *
 * The plan (which file goes where) is plain Java, without Android, for the
 * tests (tools/test_test72_saves.py).
 */
final class SaveTransfer {
    static final int MAX_FILES = 4096;
    static final long MAX_BYTES = 512L * 1024 * 1024;

    private SaveTransfer() {}

    /** the place under the save folder of a file at `path` (an archive's
     * entry or a folder's file, '/' or '\' separated), or null: not a save,
     * or not a safe name */
    static String destination(String path) {
        if (path == null) return null;
        String normalized = path.replace('\\', '/');
        while (normalized.startsWith("./")) normalized = normalized.substring(2);
        if (normalized.startsWith("/") || normalized.matches("^[A-Za-z]:.*")) normalized = normalized.replaceFirst("^([A-Za-z]:)?/+", "");
        String[] parts = normalized.split("/");
        List<String> segments = new ArrayList<>();
        for (String part : parts) {
            if (part.isEmpty() || part.equals(".")) continue;
            if (part.equals("..") || part.indexOf('\0') >= 0 || part.length() > 128) return null;
            segments.add(part);
        }
        if (segments.isEmpty() || segments.size() > 16) return null;
        String file = segments.get(segments.size() - 1);
        String lower = file.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".map")) return null; /* caches */
        /* (the last anchor wins: a backup zip of a folder holding "z" ...) */
        for (int i = segments.size() - 2; i >= 0; i--) {
            String s = segments.get(i).toLowerCase(Locale.ROOT);
            String next = i + 1 < segments.size() ? segments.get(i + 1).toLowerCase(Locale.ROOT) : "";
            if (s.equals("udata")) return "u/UDATA/" + join(segments, i + 1);
            if (s.equals("player_profiles")) return "z/saved/player_profiles/" + join(segments, i + 1);
            if (s.equals("saved") && !next.equals("maps")) return "z/saved/" + join(segments, i + 1);
        }
        if (lower.equals("savegame.bin")) return "z/savegame.bin";
        return null;
    }

    private static String join(List<String> segments, int from) {
        StringBuilder out = new StringBuilder();
        for (int i = from; i < segments.size(); i++) {
            if (out.length() > 0) out.append('/');
            out.append(segments.get(i));
        }
        return out.toString();
    }

    /** a source of files to bring in: each file's path and contents */
    interface Source {
        void each(Visitor visitor) throws IOException;
    }

    interface Visitor {
        void file(String path, InputStream in) throws IOException;
    }

    /** a .zip read as it streams */
    static Source zip(InputStream in) {
        return visitor -> {
            try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(in))) {
                ZipEntry entry;
                while ((entry = zip.getNextEntry()) != null) {
                    if (!entry.isDirectory()) visitor.file(entry.getName(), zip);
                }
            }
        };
    }

    /** what an import did */
    static final class Result {
        int files;
        long bytes;
        int skipped;
        File backup;
        final Set<String> profiles = new TreeSet<>();
        boolean checkpoint;

        String describe() {
            StringBuilder out = new StringBuilder();
            out.append(files).append(files == 1 ? " file" : " files").append(" brought in");
            if (!profiles.isEmpty()) out.append(" (profiles: ").append(String.join(", ", profiles)).append(')');
            if (checkpoint) out.append(", the campaign checkpoint");
            if (skipped > 0) out.append("; ").append(skipped).append(" not saves (left out)");
            if (backup != null) out.append(". Your saves before this are in ").append(backup.getName());
            return out.toString();
        }
    }

    /** brings `source`'s saves into `saveRoot`, after backing it up into
     * `backups`; throws (having changed nothing) when it holds none */
    static Result importSaves(Source source, File saveRoot, File backups) throws IOException {
        File stage = new File(saveRoot.getParentFile(), "save-import.tmp");
        deleteTree(stage);
        if (!stage.mkdirs()) throw new IOException("Cannot prepare the import");
        Result result = new Result();
        try {
            long[] total = {0};
            source.each((path, in) -> {
                String place = destination(path);
                if (place == null) { result.skipped++; return; }
                if (++result.files > MAX_FILES) throw new IOException("More than " + MAX_FILES + " save files");
                File target = new File(stage, place);
                if (!target.getCanonicalPath().startsWith(stage.getCanonicalPath() + File.separator))
                    throw new IOException("Unsafe name: " + path);
                File parent = target.getParentFile();
                if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create " + place);
                total[0] += copy(in, target, MAX_BYTES - total[0]);
                if (place.startsWith("z/saved/player_profiles/")) {
                    String rest = place.substring("z/saved/player_profiles/".length());
                    int slash = rest.indexOf('/');
                    if (slash > 0) result.profiles.add(rest.substring(0, slash));
                }
                if (place.equals("z/savegame.bin")) result.checkpoint = true;
            });
            result.bytes = total[0];
            if (result.files == 0)
                throw new IOException("No saves found in it (looked for a save, z, saved or player_profiles folder, "
                    + "savegame.bin, or an Xbox UDATA folder)");
            result.backup = backup(saveRoot, backups);
            moveInto(stage, saveRoot);
            return result;
        } finally {
            deleteTree(stage);
        }
    }

    /** the save folder's saves (not its caches) as a .zip into `out`;
     * the number of files */
    static int exportSaves(File saveRoot, OutputStream out) throws IOException {
        int[] count = {0};
        try (ZipOutputStream zip = new ZipOutputStream(new BufferedOutputStream(out))) {
            walk(saveRoot, "", (relative, file) -> {
                if (destination(relative) == null || !destination(relative).equalsIgnoreCase(relative)) return;
                zip.putNextEntry(new ZipEntry("save/" + relative));
                try (InputStream in = new FileInputStream(file)) {
                    byte[] buffer = new byte[65536];
                    int n;
                    while ((n = in.read(buffer)) > 0) zip.write(buffer, 0, n);
                }
                zip.closeEntry();
                count[0]++;
            });
        }
        return count[0];
    }

    /** a backup of the saves (a .zip in `backups`), or null when there are none */
    static File backup(File saveRoot, File backups) throws IOException {
        if (!saveRoot.isDirectory()) return null;
        if (!backups.isDirectory() && !backups.mkdirs()) throw new IOException("Cannot create " + backups);
        String stamp = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.ROOT).format(new Date());
        File file = new File(backups, "saves-" + stamp + ".zip");
        int files;
        try (OutputStream out = new FileOutputStream(file)) {
            files = exportSaves(saveRoot, out);
        }
        if (files == 0) {
            file.delete();
            return null;
        }
        return file;
    }

    private interface FileVisitor {
        void file(String relative, File file) throws IOException;
    }

    private static void walk(File directory, String prefix, FileVisitor visitor) throws IOException {
        File[] children = directory.listFiles();
        if (children == null) return;
        Arrays.sort(children);
        for (File child : children) {
            String relative = prefix.isEmpty() ? child.getName() : prefix + "/" + child.getName();
            if (child.isDirectory()) walk(child, relative, visitor);
            else if (child.isFile()) visitor.file(relative, child);
        }
    }

    private static void moveInto(File stage, File saveRoot) throws IOException {
        walk(stage, "", (relative, file) -> {
            File target = new File(saveRoot, relative);
            File parent = target.getParentFile();
            if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot create " + parent);
            if (target.exists() && !target.delete()) throw new IOException("Cannot replace " + relative);
            if (!file.renameTo(target)) {
                try (InputStream in = new FileInputStream(file)) { copy(in, target, MAX_BYTES); }
            }
        });
    }

    static long copy(InputStream in, File target, long limit) throws IOException {
        long total = 0;
        byte[] buffer = new byte[65536];
        try (OutputStream out = new FileOutputStream(target)) {
            int n;
            while ((n = in.read(buffer)) > 0) {
                total += n;
                if (total > limit) throw new IOException("The saves are larger than " + (MAX_BYTES >> 20) + " MB");
                out.write(buffer, 0, n);
            }
        }
        return total;
    }

    static void deleteTree(File file) {
        if (file == null || !file.exists()) return;
        File[] children = file.isDirectory() ? file.listFiles() : null;
        if (children != null) for (File child : children) deleteTree(child);
        file.delete();
    }
}
