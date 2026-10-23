"""Test71: every campaign mod installs from the launcher in one tap.

The owner (2026-10-15), after Test70 shipped Lumoria as import-only: "i want
all of the mods to work like that for future reference" (like SPV1: the
launcher downloads the mod from where its authors published it, checks it
and installs it). Import stays as the fallback.

- Project Lumoria: halomaps.org file ids 6503-6506, its levels ModMap.extra
  (a level of the mod's own, which file id 0 used to mean), installed
  through SPV1's download path.
- The Altheros Experience: moddb.com refuses non-browser clients, so its
  archive is downloaded in the launcher's own WebView (ModDownloadActivity,
  the WebView's cookies and user agent, resumed by Range), kept only when
  exactly moddb's file (size and MD5), unpacked on the device
  (ArchiveExtractor: libarchive, the archive is a RAR5), each file size- and
  SHA-256-checked, the archive deleted, the mod installed.
- Import of a .zip, a folder, or now a .rar / .7z, for every mod.
- Deleting a mod's files removes its archive too.
"""
from pathlib import Path
import hashlib
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "port/android/app"
JAVA = APP / "src/main/java/com/halo/decomp"
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

installer = read("port/android/app/src/main/java/com/halo/decomp/ModInstaller.java")
launcher = read("port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java")
browser = read("port/android/app/src/main/java/com/halo/decomp/ModDownloadActivity.java")
extractor = read("port/android/app/src/main/java/com/halo/decomp/ArchiveExtractor.java")
manifest = read("port/android/app/src/main/AndroidManifest.xml")
gradle = read("port/android/app/build.gradle")

# --- every mod downloadable; Lumoria from halomaps.org, Altheros from moddb.com
assert "static final Mod[] MODS = { SPV1, LUMORIA, ALTHEROS };" in installer
for level, fid, size in (("a", 6503, 274873434), ("b", 6504, 228054210), ("c", 6505, 198269022), ("d", 6506, 191220134)):
    assert 'new ModMap("lumoria_%s", %d, %dL, true)' % (level, fid, size) in installer
lumoria = installer[installer.index("static final Mod LUMORIA"):installer.index("static final Mod[] MODS")]
assert '}, ".map", false, null, null, STATUS_SUPPORTED,' in lumoria  # no longer import-only
assert "Download and install: about 460 MB from halomaps.org" in lumoria
altheros = installer[installer.index("static final Mod ALTHEROS"):installer.index("static final Mod LUMORIA")]
assert '.webArchive("https://www.moddb.com/downloads/start/197339",' in altheros
assert '"Latest_Altheros_Experience_10.24.2019.rar", 1477832127L, "7c76889eeed3e66654f4e91e8d5101e7")' in altheros
assert "STATUS_EXPERIMENTAL," in altheros  # still honestly labelled
assert "map.fid != 0" not in installer and "map.fid == 0" not in installer  # ModMap.extra says it now
assert "this(name, fid, size, fid == 0);" in installer  # older mods' meaning kept

# --- the browser download
assert 'android:name=".ModDownloadActivity"' in manifest
assert 'implementation "me.zhanghai.android.libarchive:library:1.1.6"' in gradle
for needle in ("CookieManager.getInstance().getCookie(url)", 'setRequestProperty("User-Agent", agent)',
               '"Range", "bytes=" + have + "-"', "code == 200) have = 0", "ModInstaller.archiveMatches(partial, size, md5)",
               "partial.renameTo(target)", "setResult(RESULT_OK", "length > 0 && length != size", "if (downloading)",
               "code == 403", "web.destroy()"):
    assert needle in browser, needle

# --- unpacking: libarchive, by file name, each file checked before it is kept
for needle in ("Archive.readSupportFormatAll(handle)", "Archive.readOpenFileName(handle", "Archive.readOpenFd(handle",
               "mods.importTarget(mod, name, expected)", "mods.importedValid(mod, target, expected[0])",
               "Archive.readDataSkip(handle)", "Archive.readDataIntoFd(handle, out.getFd())",
               "mods.acceptPart(mod, partial, target, expected[0])", "Archive.readFree(handle)",
               "path.replace('\\\\', '/')"):
    assert needle in extractor, needle

# --- the launcher: one tap for every mod; import (now .rar too) as the fallback
for needle in ("MOD_WEB_DOWNLOAD = 7", "new Intent(this, ModDownloadActivity.class)",
               "startActivityForResult(intent, MOD_WEB_DOWNLOAD)", "requestCode == MOD_WEB_DOWNLOAD",
               "private void installFromArchive(ModInstaller.Mod mod)", "ArchiveExtractor.extract(mods, mod, archive, this::report)",
               "ArchiveExtractor.extract(mods, mod, in, this::report)", "getContentResolver().openFileDescriptor(archive, \"r\")",
               "magic[0] == 'P' && magic[1] == 'K'", "mods.importZip(mod, in, this::report)",
               "modImportZip.setVisibility(!installed ? View.VISIBLE : View.GONE);",
               '" from a .zip or .rar"', '"application/vnd.rar"', '"BEFORE INSTALLING: " + selectedMod.title + " needs',
               "archive.length() == mod.archiveSize", "if (!archive.delete())"):
    assert needle in launcher, needle
assert "selectedMod.imported ? View.VISIBLE" not in launcher
assert '"BEFORE INSTALLING: SPV1 needs' not in launcher

# --- credits and the What's New page
credits = read("CREDITS.md")
notices = read("THIRD-PARTY-NOTICES.txt")
assert "## Test71 additions" in credits and "libarchive-android" in credits
for name in ("libarchive-android 1.1.6", "libarchive 3.8", "zlib", "bzip2 1.0.8", "XZ Utils liblzma", "LZ4 library", "Zstandard", "Mbed TLS"):
    assert "===== Test71: " + name in notices, name
assert "Tim Kientzle" in notices and "Julian R Seward" in notices and "Jean-loup Gailly" in notices
guide_credits = read("port/android/app/src/main/assets/guide/credits.txt")
assert "===== Test71: Mbed TLS" in guide_credits
notes = read("port/android/app/src/main/assets/whats_new.txt")
# (Test72: its notes follow Test72's, under EARLIER (TEST71); Test73: under ALSO NEW SINCE 1.0.37 (TEST71), and
# Test70's are 1.0.37's own release notes)
assert notes.startswith("NEW IN THIS UPDATE (TEST71)") or (
    notes.startswith("NEW IN THIS UPDATE (TEST72)") and "EARLIER (TEST71), ALSO IN THIS UPDATE" in notes) or (
    notes.startswith("NEW IN THIS UPDATE (TEST73)") and "ALSO NEW SINCE 1.0.37 (TEST71)" in notes)
for feature in ("Download and install", "halomaps.org", "moddb.com", "launcher's own browser", "SHA-256", ".rar",
                "5 GB free", "resumes", "experimental", "SPV1 included") + (
                () if notes.startswith("NEW IN THIS UPDATE (TEST73)") else ("EARLIER (TEST70)",)):
    assert feature in notes or feature.capitalize() in notes, feature

check = r'''
package com.halo.decomp;

import java.io.File;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;

public class ModsCheck {
    static void sparse(File file, long size) throws Exception {
        file.getParentFile().mkdirs();
        try (RandomAccessFile out = new RandomAccessFile(file, "rw")) { out.setLength(size); }
    }
    static void check(boolean condition, String what) {
        if (!condition) throw new AssertionError(what);
    }
    static void write(File file, byte[] data) throws Exception {
        file.getParentFile().mkdirs();
        try (FileOutputStream out = new FileOutputStream(file)) { out.write(data); }
    }
    public static void main(String[] arguments) throws Exception {
        File root = new File(arguments[0]);
        ModInstaller mods = new ModInstaller(root);
        ModInstaller.Progress quiet = (text, permille) -> { };
        ModInstaller.Mod lumoria = ModInstaller.LUMORIA, altheros = ModInstaller.ALTHEROS, spv1 = ModInstaller.SPV1;

        for (ModInstaller.Mod mod : ModInstaller.MODS) check(mod.downloadable(), mod.id + " installs in one tap");
        check(!lumoria.imported && !lumoria.webDownload() && lumoria.addsLevelsOnly(), "Lumoria: halomaps, levels of its own");
        for (ModInstaller.ModMap map : lumoria.maps) check(map.extra && map.fid > 0, map.name + ": downloadable, extra");
        for (ModInstaller.ModMap map : spv1.maps) check(!map.extra && map.fid > 0, map.name + ": SPV1 unchanged");
        for (ModInstaller.ModMap map : altheros.maps)
            check(map.extra == map.name.equals("f10"), map.name + ": Altheros's f10 its own, as before");
        check(altheros.imported && altheros.webDownload() && !spv1.webDownload(), "Altheros: through the browser");
        check(mods.archiveFile(altheros).equals(new File(root, "mods/altheros/Latest_Altheros_Experience_10.24.2019.rar")),
            "the archive kept with the mod");

        // the host's file: exact size and MD5 (of "abc", known)
        File small = new File(root, "small.bin");
        write(small, "abc".getBytes("US-ASCII"));
        check(ModInstaller.archiveMatches(small, 3, "900150983cd24fb0d6963f7d28e17f72"), "MD5 matches");
        check(ModInstaller.archiveMatches(small, 3, "900150983CD24FB0D6963F7D28E17F72"), "MD5 case-insensitive");
        check(!ModInstaller.archiveMatches(small, 4, "900150983cd24fb0d6963f7d28e17f72"), "size differs");
        check(!ModInstaller.archiveMatches(small, 3, "00000000000000000000000000000000"), "MD5 differs");
        check(!ModInstaller.archiveMatches(new File(root, "none.bin"), 3, "900150983cd24fb0d6963f7d28e17f72"), "missing");

        // an unpacked part: kept only when its size is right (no recipe: the hash is not asked)
        long[] expected = new long[1];
        File target = mods.importTarget(altheros, "-loc.map", expected);
        check(target != null && expected[0] == ModInstaller.ALTHEROS_DATA_SIZES[2], "-loc.map is a data file");
        File part = new File(target.getPath() + ".part");
        sparse(part, expected[0] - 1);
        try {
            mods.acceptPart(altheros, part, target, expected[0]);
            check(false, "a short part kept");
        } catch (java.io.IOException refused) {
            check(!part.exists() && !target.exists(), "a short part deleted, nothing kept");
        }
        sparse(part, expected[0]);
        mods.acceptPart(altheros, part, target, expected[0]);
        check(!part.exists() && target.length() == expected[0], "a whole part kept");
        check(mods.importedValid(altheros, target, expected[0]), "and then reused");
        check(!mods.importedValid(altheros, target, expected[0] + 1), "not reused at another size");
        check(mods.importTarget(altheros, "ReadMe.txt", expected) == null && mods.importTarget(altheros, "Trailer.jpg", expected) == null,
            "readmes and pictures left in the archive");

        // a half-downloaded archive counts as files to delete, and goes with them
        File archive = mods.archiveFile(altheros);
        File partial = new File(archive.getPath() + ".part");
        sparse(partial, 1000);
        check(mods.hasDownloadFiles(altheros), "a partial archive is offered for cleanup");
        sparse(archive, 2000);
        mods.delete(altheros, quiet);
        check(!archive.exists() && !partial.exists() && !target.exists(), "delete removes the archive and the files");
        check(!mods.hasDownloadFiles(altheros), "nothing left");
        System.out.println("PASS: Test71 mods: every mod downloadable, Lumoria by file id (extra levels), "
            + "Altheros's archive by size and MD5, parts kept only whole, archive deleted with the mod");
    }
}
'''
with tempfile.TemporaryDirectory(prefix="test71-mods-") as temp:
    out = Path(temp)
    (out / "ModsCheck.java").write_text(check, encoding="utf-8")
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(out), str(JAVA / "ModInstaller.java"),
                    str(out / "ModsCheck.java")], check=True)
    game = out / "game"
    game.mkdir()
    subprocess.run(["java", "-cp", str(out), "com.halo.decomp.ModsCheck", str(game)], check=True)
assert hashlib.md5(b"abc").hexdigest() == "900150983cd24fb0d6963f7d28e17f72"
print("PASS: Test71 one-tap mods wiring: browser download (moddb), libarchive unpacking, .rar import, credits, What's New")
