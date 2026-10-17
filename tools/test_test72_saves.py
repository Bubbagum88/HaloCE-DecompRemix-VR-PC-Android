"""Test72: a player's suggestion, "ability to import savefiles from zip or
folder": the launcher's Game files & versions brings the selected set's
saves in from a .zip or a folder and takes them out as a .zip
(SaveTransfer.java, compiled and run here with javac: its plan, a round
trip, the backup made first, and what is never taken)."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "port/android/app/src/main/java/com/halo/decomp"
source = (JAVA / "SaveTransfer.java").read_text(encoding="utf-8")
manager = (JAVA / "GameDataManager.java").read_text(encoding="utf-8")
launcher = (JAVA / "LauncherActivity.java").read_text(encoding="utf-8")
assert "import android" not in source  # plain Java: testable here

# ---- wiring
assert "static final int PICK_SAVES_ZIP=73, PICK_SAVES_FOLDER=74, EXPORT_SAVES=75;" in manager
for label in ('"Import saves from a .zip"', '"Import saves from a folder"', '"Export saves as a .zip"'):
    assert label in manager, label
assert "private File saveRoot(){return new File(GameDataLibrary.activeRoot(base),\"save\");}" in manager
assert "if(savesResult(request,result,data))return true;" in manager
assert "requestCode==GameDataManager.PICK_SAVES_ZIP||" in launcher and "requestCode==GameDataManager.EXPORT_SAVES)" in launcher

HARNESS = r'''
package com.halo.decomp;
import java.io.*;
import java.util.*;
import java.util.zip.*;
public class SaveTransferCheck {
    static void check(boolean ok, String what) { if (!ok) throw new AssertionError(what); }
    static void write(File f, String text) throws IOException { f.getParentFile().mkdirs(); try (FileOutputStream o = new FileOutputStream(f)) { o.write(text.getBytes("UTF-8")); } }
    static String read(File f) throws IOException { return new String(java.nio.file.Files.readAllBytes(f.toPath()), "UTF-8"); }
    public static void main(String[] args) throws Exception {
        // the plan
        String[][] cases = {
            {"save/z/saved/player_profiles/default_profile/00.sav", "z/saved/player_profiles/default_profile/00.sav"},
            {"files/save/z/savegame.bin", "z/savegame.bin"},
            {"z\\saved\\playlists\\default_playlist\\00\\blam.lst", "z/saved/playlists/default_playlist/00/blam.lst"},
            {"saved/recordings/r1.rec", "z/saved/recordings/r1.rec"},
            {"My Backup/player_profiles/Chief/00.sav", "z/saved/player_profiles/Chief/00.sav"},
            {"xbox/E/UDATA/4d530004/ABCDEF0123/SaveMeta.xbx", "u/UDATA/4d530004/ABCDEF0123/SaveMeta.xbx"},
            {"save/u/UDATA/4d530004/X/a.bin", "u/UDATA/4d530004/X/a.bin"},
            {"savegame.bin", "z/savegame.bin"},
            {"save/z/cache000.map", null},
            {"save/z/saved/hdmu.map", null},
            {"save/z/maps/bloodgulch.map", null},
            {"save/z/last_solo.txt", null},
            {"../evil/saved/x.sav", null},
            {"saved/../../x.sav", null},
            {"readme.txt", null},
            {"saved", null},
        };
        for (String[] c : cases) {
            String got = SaveTransfer.destination(c[0]);
            check(Objects.equals(got, c[1]), c[0] + " -> " + got + " (want " + c[1] + ")");
        }
        File base = java.nio.file.Files.createTempDirectory("saves").toFile();
        // a device's saves, exported
        File a = new File(base, "a/save");
        write(new File(a, "z/saved/player_profiles/Chief/00.sav"), "chief0");
        write(new File(a, "z/saved/player_profiles/Chief/01.sav"), "chief1");
        write(new File(a, "z/savegame.bin"), "checkpoint");
        write(new File(a, "z/cache001.map"), "cache");
        write(new File(a, "u/UDATA/4d530004/S1/SaveMeta.xbx"), "meta");
        File zip = new File(base, "export.zip");
        int exported;
        try (OutputStream out = new FileOutputStream(zip)) { exported = SaveTransfer.exportSaves(a, out); }
        check(exported == 4, "exported " + exported);
        Set<String> names = new TreeSet<>();
        try (ZipInputStream in = new ZipInputStream(new FileInputStream(zip))) { ZipEntry e; while ((e = in.getNextEntry()) != null) names.add(e.getName()); }
        check(!names.toString().contains("cache"), "caches left out: " + names);
        // another device's, with a profile of its own and one of the same name
        File b = new File(base, "b/save");
        write(new File(b, "z/saved/player_profiles/Chief/00.sav"), "old");
        write(new File(b, "z/saved/player_profiles/Arbiter/00.sav"), "arbiter");
        File backups = new File(base, "b/save-backups");
        SaveTransfer.Result r;
        try (InputStream in = new FileInputStream(zip)) { r = SaveTransfer.importSaves(SaveTransfer.zip(in), b, backups); }
        check(r.files == 4 && r.profiles.contains("Chief") && r.checkpoint, r.describe());
        check(read(new File(b, "z/saved/player_profiles/Chief/00.sav")).equals("chief0"), "replaced");
        check(read(new File(b, "z/saved/player_profiles/Arbiter/00.sav")).equals("arbiter"), "others kept");
        check(read(new File(b, "u/UDATA/4d530004/S1/SaveMeta.xbx")).equals("meta"), "udata");
        check(!new File(b, "z/cache001.map").exists(), "no cache");
        check(r.backup != null && r.backup.isFile(), "backed up first");
        Set<String> backedUp = new TreeSet<>();
        try (ZipInputStream in = new ZipInputStream(new FileInputStream(r.backup))) { ZipEntry e; while ((e = in.getNextEntry()) != null) { backedUp.add(e.getName()); if (e.getName().endsWith("Chief/00.sav")) { check(new String(in.readAllBytes(), "UTF-8").equals("old"), "the backup holds the old"); } } }
        check(backedUp.contains("save/z/saved/player_profiles/Arbiter/00.sav"), "backup " + backedUp);
        check(!new File(base, "b/save-import.tmp").exists(), "staging removed");
        // nothing in it: an error, nothing changed, no backup
        File junk = new File(base, "junk.zip");
        try (ZipOutputStream out = new ZipOutputStream(new FileOutputStream(junk))) { out.putNextEntry(new ZipEntry("readme.txt")); out.write(1); out.closeEntry(); }
        int before = backups.list().length;
        try (InputStream in = new FileInputStream(junk)) { SaveTransfer.importSaves(SaveTransfer.zip(in), b, backups); check(false, "no saves accepted"); }
        catch (IOException expected) { check(expected.getMessage().startsWith("No saves found"), expected.getMessage()); }
        check(backups.list().length == before, "no backup for nothing");
        // a hostile name
        File evil = new File(base, "evil.zip");
        try (ZipOutputStream out = new ZipOutputStream(new FileOutputStream(evil))) { out.putNextEntry(new ZipEntry("saved/../../../x.sav")); out.write(1); out.closeEntry(); }
        try (InputStream in = new FileInputStream(evil)) { SaveTransfer.importSaves(SaveTransfer.zip(in), b, backups); check(false, "traversal"); }
        catch (IOException expected) { }
        check(!new File(base, "x.sav").exists() && !new File(base, "b/x.sav").exists(), "nothing outside");
        // a folder (a Source over files) as the folder picker gives
        SaveTransfer.Source folder = v -> { try (InputStream in = new ByteArrayInputStream("folder".getBytes("UTF-8"))) { v.file("Halo/player_profiles/Folder/00.sav", in); } };
        r = SaveTransfer.importSaves(folder, b, backups);
        check(read(new File(b, "z/saved/player_profiles/Folder/00.sav")).equals("folder"), "folder");
        System.out.println("ok " + r.describe());
    }
}
'''

with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    package = work / "src/com/halo/decomp"
    package.mkdir(parents=True)
    shutil.copy(JAVA / "SaveTransfer.java", package / "SaveTransfer.java")
    (package / "SaveTransferCheck.java").write_text(HARNESS, encoding="utf-8")
    out = work / "out"
    subprocess.run(["javac", "-d", str(out), str(package / "SaveTransfer.java"), str(package / "SaveTransferCheck.java")], check=True)
    run = subprocess.run(["java", "-cp", str(out), "com.halo.decomp.SaveTransferCheck"], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert run.stdout.startswith("ok "), run.stdout

print("PASS: Test72 saves: in from a .zip or a folder (another device's save folder, z, saved, player_profiles, "
      "savegame.bin, Xbox UDATA), caches never, backed up first, same names replaced, others kept; out as a .zip")
