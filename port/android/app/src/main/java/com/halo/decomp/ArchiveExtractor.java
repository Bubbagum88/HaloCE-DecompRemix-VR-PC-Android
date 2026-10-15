package com.halo.decomp;

import android.os.ParcelFileDescriptor;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

import me.zhanghai.android.libarchive.Archive;
import me.zhanghai.android.libarchive.ArchiveEntry;

/**
 * Test71: a mod's archive unpacked on the device, whatever its kind (RAR5,
 * RAR, 7z, zip: libarchive). The owner: every mod installs from the
 * launcher, and The Altheros Experience comes only as a RAR5 archive, which
 * Java cannot read. Each entry is matched by its file name alone, as an
 * imported folder's are (ModInstaller.importTarget), so the archive's own
 * folders do not matter and everything else in it (readmes, pictures) is
 * left out; each file kept is checked by its exact size and SHA-256
 * (ModInstaller.acceptPart) before it replaces anything.
 */
final class ArchiveExtractor {
    private ArchiveExtractor() {
    }

    /** Unpacks `archive`'s files of `mod`; returns how many were kept. */
    static int extract(ModInstaller mods, ModInstaller.Mod mod, File archive, ModInstaller.Progress progress)
            throws IOException {
        long handle = Archive.readNew();
        try {
            Archive.readSupportFilterAll(handle);
            Archive.readSupportFormatAll(handle);
            Archive.readOpenFileName(handle, archive.getAbsolutePath().getBytes(StandardCharsets.UTF_8), 1 << 16);
            return entries(mods, mod, handle, progress);
        } finally {
            close(handle);
        }
    }

    /** The same, from an archive the player picked (its open descriptor:
     * a 1.4 GB archive is read where it is, not copied first). */
    static int extract(ModInstaller mods, ModInstaller.Mod mod, ParcelFileDescriptor archive,
            ModInstaller.Progress progress) throws IOException {
        long handle = Archive.readNew();
        try {
            Archive.readSupportFilterAll(handle);
            Archive.readSupportFormatAll(handle);
            Archive.readOpenFd(handle, archive.getFd(), 1 << 16);
            return entries(mods, mod, handle, progress);
        } finally {
            close(handle);
        }
    }

    private static int entries(ModInstaller mods, ModInstaller.Mod mod, long handle, ModInstaller.Progress progress)
            throws IOException {
        int copied = 0;
        long entry;
        while ((entry = Archive.readNextHeader(handle)) != 0) {
            String path = ArchiveEntry.pathnameUtf8(entry);
            if (path == null) {
                byte[] raw = ArchiveEntry.pathname(entry);
                path = raw != null ? new String(raw, StandardCharsets.UTF_8) : "";
            }
            String name = path.replace('\\', '/');
            name = name.substring(name.lastIndexOf('/') + 1);
            long[] expected = new long[1];
            File target = (ArchiveEntry.filetype(entry) & ArchiveEntry.AE_IFMT) == ArchiveEntry.AE_IFREG ?
                mods.importTarget(mod, name, expected) : null;
            if (target == null || mods.importedValid(mod, target, expected[0])) {
                Archive.readDataSkip(handle);
                continue;
            }
            File directory = target.getParentFile();
            if (directory != null && !directory.isDirectory() && !directory.mkdirs())
                throw new IOException("cannot make " + directory);
            File partial = new File(target.getPath() + ".part");
            progress.report("Unpacking " + name + " (" + ModInstaller.megabytes(expected[0]) + ")...", -1);
            try (ParcelFileDescriptor out = ParcelFileDescriptor.open(partial, ParcelFileDescriptor.MODE_WRITE_ONLY
                    | ParcelFileDescriptor.MODE_CREATE | ParcelFileDescriptor.MODE_TRUNCATE)) {
                Archive.readDataIntoFd(handle, out.getFd());
            }
            progress.report("Checking " + name + "...", -1);
            mods.acceptPart(mod, partial, target, expected[0]);
            copied++;
        }
        return copied;
    }

    private static void close(long handle) throws IOException {
        try {
            Archive.readClose(handle);
        } finally {
            Archive.readFree(handle);
        }
    }
}
