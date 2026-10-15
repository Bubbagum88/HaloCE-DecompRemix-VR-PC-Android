"""Test66: CUSTOM CAMPAIGNS (the owner: SPV1 works now; add The Altheros
Experience, a .yelo campaign mod, and make switching between it, SPV1 and the
original easy).

Compiles the launcher's ModInstaller (plain Java) with a check that drives it
on a game folder of sparse files of the mods' exact sizes: Altheros imported
and installed (its .yelo maps beside where the originals were, which go
aside; its resource maps as maps/data_files/alsthetic-*.map, the name its
maps ask for), restored, SPV1 installed over it (Altheros goes back out
first: one campaign at a time), and the original back. Also: the engine and
the map reader take OpenSauce's upgraded script nodes (a10 needs them).
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "port/android/app/src/main/java/com/halo/decomp"
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

installer = read("port/android/app/src/main/java/com/halo/decomp/ModInstaller.java")
launcher = read("port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java")
assert "static final Mod[] MODS = { SPV1, LUMORIA, ALTHEROS };" in installer  # Test70: Lumoria added
assert '".yelo", true, "alsthetic"' in installer
assert "Mod other = installedMod();" in installer and "restore(other, progress);" in installer
assert '"CUSTOM CAMPAIGNS"' in launcher and '"Play the original campaign"' in launcher
assert "Intent.ACTION_OPEN_DOCUMENT_TREE" in launcher and "PICK_MOD_FOLDER" in launcher
assert "(experimental; unverified)" not in launcher

hs = read("source/hs/hs.c")
assert "#define MAXIMUM_HS_SYNTAX_NODES_PER_SCENARIO_UPGRADED 28501" in hs
assert "static unsigned long hs_syntax_nodes_marked[BIT_VECTOR_SIZE_IN_LONGS(MAXIMUM_HS_SYNTAX_NODES_PER_SCENARIO_UPGRADED)];" in hs
schema = read("port/linux/game/tag_schema_scenario.c")
assert "TAG_SCHEMA_DATA(struct scenario, hs_syntax_data, HS_SYNTAX_DATA_SIZE_UPGRADED)" in schema
formats = read("port/linux/game/cache_file_formats.c")
assert "the upgraded array is kept as it is" in formats

check = r'''
package com.halo.decomp;

import java.io.File;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;

public class CampaignCheck {
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
    public static void main(String[] arguments) throws Exception {
        File root = new File(arguments[0]);
        byte[] xbox = { 'd', 'a', 'e', 'h', 5, 0, 0, 0 };
        String[] levels = { "a10", "a30", "a50", "b30", "b40", "c10", "c20", "c40", "d20", "d40" };
        for (String level : levels) sparse(new File(root, "maps/" + level + ".map"), 4096, xbox);
        ModInstaller mods = new ModInstaller(root);
        ModInstaller.Progress quiet = (text, permille) -> { };
        ModInstaller.Mod altheros = ModInstaller.ALTHEROS, spv1 = ModInstaller.SPV1;

        // imported: each file of the player's folder by its own name
        long[] expected = new long[1];
        File target = mods.importTarget(altheros, "-bitmaps.map", expected);
        check(target.getName().equals("alsthetic-bitmaps.map") && expected[0] == 613838703L, "data file name");
        check(mods.importTarget(altheros, "ReadMe.txt", expected) == null, "other files ignored");
        check(!mods.downloaded(altheros) && mods.missingImports(altheros).contains("a10.yelo"), "nothing yet");
        for (ModInstaller.ModMap map : altheros.maps) {
            File file = mods.importTarget(altheros, map.name + ".yelo", expected);
            sparse(file, expected[0], null);
        }
        for (String name : new String[] { "-bitmaps.map", "-sounds.map", "-loc.map" }) {
            File file = mods.importTarget(altheros, name, expected);
            sparse(file, expected[0], null);
        }
        check(mods.downloaded(altheros) && mods.missingImports(altheros).isEmpty(), "imported");

        // installed: the .yelo maps in, the originals aside, its resources in data_files
        mods.install(altheros, quiet);
        check(mods.installedMod() == altheros, "Altheros in");
        check(new File(root, "maps/a10.yelo").length() == 445975615L && !new File(root, "maps/a10.map").exists(), "a10.yelo replaces a10.map");
        check(new File(root, "mods/original/a10.map").isFile(), "the original kept aside");
        check(new File(root, "maps/d40.map").isFile(), "a level the mod lacks stays the original's");
        check(new File(root, "maps/f10.yelo").isFile(), "an extra level goes in");
        check(new File(root, "maps/data_files/alsthetic-bitmaps.map").length() == 613838703L, "its resource maps");
        check(new File(root, "mods/custom_edition.on").isFile(), "Custom Edition maps load");

        // restored: the original back, the mod kept to switch in again
        mods.restore(altheros, quiet);
        check(mods.installedMod() == null && new File(root, "maps/a10.map").isFile() && !new File(root, "maps/a10.yelo").exists(), "original back");
        check(!new File(root, "maps/f10.yelo").exists() && !new File(root, "maps/data_files/alsthetic-bitmaps.map").exists(), "all of the mod out");
        check(mods.downloaded(altheros), "still imported");

        // SPV1 over Altheros: one campaign at a time
        mods.install(altheros, quiet);
        for (ModInstaller.ModMap map : spv1.maps) sparse(new File(root, "mods/spv1/maps/" + map.name + ".map"), map.size, null);
        for (int type = 1; type <= 3; type++) sparse(mods.resourceFile(type), ModInstaller.RESOURCE_SIZES[type - 1], null);
        mods.install(spv1, quiet);
        check(mods.installedMod() == spv1 && !mods.installed(altheros), "SPV1 in, Altheros out");
        check(!new File(root, "maps/a10.yelo").exists() && new File(root, "maps/a10.map").length() == 264601050L, "SPV1's a10");
        check(new File(root, "mods/original/a10.map").length() == 4096, "the Xbox original still aside");
        mods.restore(spv1, quiet);
        check(mods.installedMod() == null && new File(root, "maps/a10.map").length() == 4096, "the Xbox a10 back");
        // deleting the imported mod removes only its files
        mods.delete(altheros, quiet);
        check(!new File(root, "mods/altheros/maps/a10.yelo").exists() && new File(root, "maps/a10.map").isFile(), "deleted");
        System.out.println("PASS: Test66 custom campaigns: Altheros imported (data files renamed), installed beside the originals, restored, replaced by SPV1, deleted; one campaign at a time");
    }
}
'''
with tempfile.TemporaryDirectory(prefix="test66-campaigns-") as temp:
    out = Path(temp)
    (out / "CampaignCheck.java").write_text(check, encoding="utf-8")
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(out), str(JAVA / "ModInstaller.java"),
                    str(out / "CampaignCheck.java")], check=True)
    game = out / "game"
    game.mkdir()
    subprocess.run(["java", "-cp", str(out), "com.halo.decomp.CampaignCheck", str(game)], check=True)
print("PASS: Test66 custom campaigns wiring (CUSTOM CAMPAIGNS, folder import, SPV1 warnings gone, upgraded script nodes)")
