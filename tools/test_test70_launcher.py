"""Test70: the launcher's campaigns and MCC maps, as the owner asked.

- MCC maps showed the damaged disc error on loading. The Test67 merge kept
  this port's cache_files_windows.c and with it lost GulchCE's three MCC
  hooks there: an MCC level was looked for among the Xbox maps (precache),
  not found, and display_error_damaged_media() followed. The hooks are back.
- Honest status labels: SPV1 and Project Lumoria Supported; The Altheros
  Experience and MCC maps "Experimental — currently not working", kept
  available.
- Project Lumoria: imported from the archive its authors published
  (Lumoria_Full_Campaign.zip, its own ui.map and Windows DLLs left out),
  verified by size, installed as levels of its own (no campaign map put
  aside), with Custom Edition's resource maps as SPV1 takes them, and
  swapped out by SPV1 (one campaign mod at a time).
- What's New: shown once per version, reopened from the launcher, with a
  link to the GitHub release notes.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "port/android/app/src/main/java/com/halo/decomp"
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

# --- the MCC hooks in the precache and the cache reads
windows = read("source/cache/cache_files_windows.c")
loaded = windows[windows.index("boolean cache_files_precache_map_loaded("):]
loaded = loaded[:loaded.index("\n}\n")]
assert "if (mcc_level_name(map_name))\n\t\treturn mcc_cache_available(map_name);" in loaded
begin = windows[windows.index("boolean cache_files_precache_map_begin("):]
begin = begin[:begin.index("cache_file_read_header_from_dvd")]
assert "if (mcc_level_name(map_name))\n\t\treturn mcc_cache_require(map_name, 0);" in begin
read_function = windows[windows.index("short cache_file_read("):]
read_function = read_function[:read_function.index("custom_edition_cache_tags_loaded()")]
assert "mcc_cache_read(tag_index, offset, size, buffer) ? TRUE : (boolean)-1" in read_function
assert '#include "mcc_cache.h"' in windows
header = read("port/linux/game/mcc_cache.h")
for name in ("mcc_cache_available", "mcc_cache_require", "mcc_cache_read", "mcc_cache_tags_loaded"):
    assert name in header, name

# --- the launcher's labels and What's New
installer = read("port/android/app/src/main/java/com/halo/decomp/ModInstaller.java")
launcher = read("port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java")
whats_new = read("port/android/app/src/main/java/com/halo/decomp/WhatsNew.java")
assert 'STATUS_EXPERIMENTAL = "Experimental — currently not working"' in installer
assert "STATUS_SUPPORTED," in installer and "STATUS_EXPERIMENTAL," in installer
assert "each.buttonLabel()" in launcher and "ModInstaller.STATUS_EXPERIMENTAL" in launcher
assert "PICK_MOD_ZIP" in launcher and "mods.importZip(mod, in, this::report)" in launcher
assert "WhatsNew.maybeShow(this);" in launcher and '"What\'s new in this version"' in launcher
assert 'RELEASE_NOTES_URL = "https://github.com/" + UpdatePolicy.REPOSITORY + "/releases"' in whats_new
assert "View full release notes on GitHub" in whats_new and "Intent.ACTION_VIEW" in whats_new
assert "prefs.edit().putInt(SEEN, BuildConfig.VERSION_CODE).apply();" in whats_new
notes = read("port/android/app/src/main/assets/whats_new.txt")
assert len(notes) > 400 and "GitHub" not in notes[:40]
# the owner: the pop-up must not miss anything: every Test70 change is named
# (Test73: Test70 was published as 1.0.37, so from Test73's notes on its changes are 1.0.37's release notes, which
# the notes point to; what is new since is checked in tools/test_test73_whats_new.py)
if notes.startswith(("NEW IN THIS UPDATE (TEST73)", "NEW IN THIS UPDATE (TEST73B)")):
    assert "Version 1.0.37 (Test70) and earlier: the full release notes on GitHub." in notes
else:
    for feature in ("settings and saves are kept", "What's new in this version", "Supported", "Experimental",
                    "Project Lumoria", ".zip", "problem with the disc", "Altheros", "never moves your other buttons",
                    "CANCEL, SWAP, CLEAR", "NONE", "RESET CONTROLS", "(DEFAULT)", "PUSH TO TALK", "MIRROR BUTTONS",
                    "holstered", "Needler", "SHAKE COOLING", "Rocket launcher", "tick your gun hand", "magazines now sit",
                    "read the right way round", "inside out", "SLIDE", "SLIDE DISTANCE", "SLIDE FRICTION", "SLIDE IMPACT",
                    "CROUCH SLIDES", "JUMP CANCELS", "BULLET TIME", "TIME SCALE", "Climbing", "Wall jumps", "HIT ASSIST",
                    "LUNGE HOP", "GRAB ASSIST", "15 cm", "FIST OPTIONS", "Build 206", "network 29", "HALOFREAK95",
                    "Android"):
        assert feature in notes, feature
recipe = read("port/android/app/src/main/assets/campaigns/lumoria.properties")
for level, fid, size in (("a", 6503, 274873434), ("b", 6504, 228054210), ("c", 6505, 198269022), ("d", 6506, 191220134)):
    assert "file.lumoria_%s.map.size=%d" % (level, size) in recipe
    # (Test71: downloadable from halomaps.org, by file id; still levels of its own)
    assert "lumoria_%s\", %d, %dL, true" % (level, fid, size) in installer

check = r'''
package com.halo.decomp;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class LumoriaCheck {
    static void sparse(File file, long size, byte[] header) throws Exception {
        file.getParentFile().mkdirs();
        try (RandomAccessFile out = new RandomAccessFile(file, "rw")) {
            out.setLength(size);
            if (header != null) { out.seek(0); out.write(header); }
        }
    }
    static void check(boolean condition, String what) {
        if (!condition) throw new AssertionError(what);
    }
    static void entry(ZipOutputStream zip, String name, long size) throws Exception {
        zip.putNextEntry(new ZipEntry(name));
        byte[] zeros = new byte[1 << 16];
        for (long left = size; left > 0; left -= zeros.length) zip.write(zeros, 0, (int) Math.min(left, zeros.length));
        zip.closeEntry();
    }
    public static void main(String[] arguments) throws Exception {
        File root = new File(arguments[0]);
        byte[] xbox = { 'd', 'a', 'e', 'h', 5, 0, 0, 0 };
        String[] levels = { "a10", "a30", "a50", "b30", "b40", "c10", "c20", "c40", "d20", "d40" };
        for (String level : levels) sparse(new File(root, "maps/" + level + ".map"), 4096, xbox);
        ModInstaller mods = new ModInstaller(root);
        ModInstaller.Progress quiet = (text, permille) -> { };
        ModInstaller.Mod lumoria = ModInstaller.LUMORIA, spv1 = ModInstaller.SPV1;

        check(lumoria.supported() && spv1.supported() && !ModInstaller.ALTHEROS.supported(), "status labels");
        check(lumoria.addsLevelsOnly() && !spv1.addsLevelsOnly(), "Lumoria adds levels; SPV1 replaces");
        check(ModInstaller.ALTHEROS.buttonLabel().endsWith("Experimental — currently not working"), "Altheros label");
        long[] expected = new long[1];
        check(mods.importTarget(lumoria, "ui.map", expected) == null, "Lumoria's ui.map is not taken");
        check(mods.importTarget(lumoria, "vorbis.dll", expected) == null, "its DLLs are not taken");

        // the archive as published: a folder of DLLs, readmes, ui.map; one level
        // here (the others sparse, to keep the test small), in a subfolder
        File archive = new File(root, "Lumoria_Full_Campaign.zip");
        try (ZipOutputStream zip = new ZipOutputStream(new FileOutputStream(archive))) {
            entry(zip, "Sound DLL's/vorbis.dll", 1024);
            entry(zip, "ReadMe.txt", 100);
            entry(zip, "ui.map", 8285028);
            entry(zip, "Lumoria/lumoria_a.map", 274873434L);
        }
        int copied;
        try (FileInputStream in = new FileInputStream(archive)) { copied = mods.importZip(lumoria, in, quiet); }
        check(copied == 1, "one file kept from the archive: " + copied);
        check(new File(root, "mods/lumoria/maps/lumoria_a.map").length() == 274873434L, "lumoria_a imported");
        check(!new File(root, "mods/lumoria/maps/ui.map").exists() && !new File(root, "maps/ui.map").exists(), "no ui.map");
        check(mods.missingImports(lumoria).contains("lumoria_b.map") && !mods.downloaded(lumoria), "the rest still wanted");
        for (String level : new String[] { "lumoria_b", "lumoria_c", "lumoria_d" }) {
            File file = mods.importTarget(lumoria, level + ".map", expected);
            sparse(file, expected[0], null);
        }
        check(mods.downloaded(lumoria), "imported");
        try {
            mods.install(lumoria, quiet);
            check(false, "installed without Custom Edition's resource maps");
        } catch (java.io.IOException expectedFailure) {
            check(expectedFailure.getMessage().contains("resource maps"), "asks for the resource maps");
        }
        for (int type = 1; type <= 3; type++) sparse(mods.resourceFile(type), ModInstaller.RESOURCE_SIZES[type - 1], null);
        mods.install(lumoria, quiet);
        check(mods.installedMod() == lumoria, "Lumoria in");
        check(new File(root, "maps/lumoria_a.map").length() == 274873434L, "its levels in the maps");
        check(new File(root, "maps/a10.map").length() == 4096 && !new File(root, "mods/original/a10.map").exists(),
            "the original campaign untouched");
        check(new File(root, "maps/bitmaps.map").length() == ModInstaller.RESOURCE_SIZES[0], "CE resources in");
        check(new File(root, "mods/custom_edition.on").isFile(), "Custom Edition maps load");

        // SPV1 over Lumoria: Lumoria goes back out first
        for (ModInstaller.ModMap map : spv1.maps) sparse(new File(root, "mods/spv1/maps/" + map.name + ".map"), map.size, null);
        mods.install(spv1, quiet);
        check(mods.installedMod() == spv1 && !mods.installed(lumoria), "SPV1 in, Lumoria out");
        check(!new File(root, "maps/lumoria_a.map").exists() && mods.downloaded(lumoria), "Lumoria kept aside");
        check(new File(root, "maps/bitmaps.map").length() == ModInstaller.RESOURCE_SIZES[0], "CE resources still in");
        mods.restore(spv1, quiet);
        mods.install(lumoria, quiet);
        mods.delete(lumoria, quiet);
        check(mods.installedMod() == null && !new File(root, "maps/lumoria_a.map").exists(), "deleted");
        check(new File(root, "maps/a10.map").length() == 4096, "the Xbox a10 still there");
        check(WhatsNew.due(-1, 82) && WhatsNew.due(81, 82) && !WhatsNew.due(82, 82), "What's New once per version");
        System.out.println("PASS: Test70 Lumoria: zip import (ui.map/DLLs left out), resource maps required, added beside the original campaign, swapped with SPV1, deleted");
    }
}
'''
with tempfile.TemporaryDirectory(prefix="test70-launcher-") as temp:
    out = Path(temp)
    (out / "LumoriaCheck.java").write_text(check, encoding="utf-8")
    # WhatsNew is an Android class: its pure check is compiled alone, from its source
    source = whats_new
    start = source.index("    static boolean due(")
    due = source[start:source.index("    }\n", start) + 6]
    (out / "WhatsNew.java").write_text("package com.halo.decomp;\nfinal class WhatsNew {\n" + due + "}\n",
                                       encoding="utf-8")
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(out), str(JAVA / "ModInstaller.java"),
                    str(out / "WhatsNew.java"), str(out / "LumoriaCheck.java")], check=True)
    game = out / "game"
    game.mkdir()
    subprocess.run(["java", "-cp", str(out), "com.halo.decomp.LumoriaCheck", str(game)], check=True)
print("PASS: Test70 launcher: MCC precache/read hooks restored (damaged disc error), honest status labels, What's New once per version")
