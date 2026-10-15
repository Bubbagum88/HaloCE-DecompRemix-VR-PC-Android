"""Test67: Halo 1 MCC custom maps (GulchCE's loader), solo only.

Compiles the launcher's MccMaps (plain Java) with a check that drives it on a
game folder: MCC version-13 headers recognized (campaign / multiplayer) and a
Custom Edition header refused; a chosen folder's maps grouped into packages
(a "maps" folder counting as the one above it), names made safe, levels too
long for the game skipped, MCC's resource maps placed in _shared by the folder
they came from, a non-MCC level not kept, counts and removal.

Then the engine side: GulchCE's loader is dispatched from cache_files.c, the
network stays OpenCE network 28 with no MCC messages or advertisement
fingerprint (MCC sends compiled out, MCC hosting/joining refused, the host's
map chooser skips the MCC kinds), and the stb_vorbis/bcdec dependencies are
the port's own copies.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "port/android/app/src/main/java/com/halo/decomp"
read = lambda path: (ROOT / path).read_text(encoding="utf-8", errors="replace")

CHECK = r'''
package com.halo.decomp;
import java.io.*;
import java.util.*;
public class MccCheck {
    static byte[] header(boolean mcc, int version, int type, String name) {
        byte[] h = new byte[0x800];
        if (mcc) {
            h[0] = 'd'; h[1] = 'a'; h[2] = 'e'; h[3] = 'h';
            h[0x7FC] = 't'; h[0x7FD] = 'o'; h[0x7FE] = 'o'; h[0x7FF] = 'f';
        }
        h[4] = (byte)version;
        byte[] n = name.getBytes();
        System.arraycopy(n, 0, h, 0x20, n.length);
        h[0x60] = (byte)type;
        return h;
    }
    static void check(boolean condition, String what) { if (!condition) throw new AssertionError(what); }
    public static void main(String[] args) throws Exception {
        File game = new File(args[0]);
        MccMaps maps = new MccMaps(game);
        check(MccMaps.header(header(true, 13, 0, "mercury_falling")).mcc, "MCC v13");
        check(MccMaps.header(header(true, 13, 0, "mercury_falling")).scenarioType == 0, "campaign type");
        check(MccMaps.header(header(true, 13, 1, "x")).scenarioType == 1, "multiplayer type");
        check(MccMaps.header(header(true, 13, 0, "mercury_falling")).name.equals("mercury_falling"), "name");
        check(!MccMaps.header(header(true, 609, 0, "x")).mcc, "Custom Edition's version refused");
        check(!MccMaps.header(header(false, 13, 0, "x")).mcc, "no head/foot refused");
        check(!MccMaps.header(new byte[16]).mcc, "short refused");

        File a = maps.target("solar_flare", Arrays.asList(), "m0.map");
        check(a.equals(new File(game, "mcc_maps/solar_flare/m0.map")), "top level: the chosen folder's package " + a);
        File b = maps.target("Download", Arrays.asList("Solar Flare", "maps"), "m1.map");
        check(b.equals(new File(game, "mcc_maps/Solar_Flare/m1.map")), "a maps folder counts as the one above " + b);
        check(maps.target("x", Arrays.asList("pack"), "sounds.map").equals(new File(game, "mcc_maps/pack/sounds.map")), "package resources");
        check(maps.target("x", Arrays.asList("pack"), "m0.txt") != null, "descriptions kept");
        check(maps.target("x", Arrays.asList("pack"), "readme.pdf") == null, "other files skipped");
        check(maps.target("x", Arrays.asList("_shared"), "bitmaps.map") == null, "never into _shared as a package");
        StringBuilder longName = new StringBuilder();
        for (int i = 0; i < 50; i++) longName.append('a');
        check(maps.target("x", Arrays.asList("pack"), longName + ".map") == null, "too long for a level name");
        check(maps.target("x", Arrays.asList("p"), longName + ".map") != null, "54 characters in all fit");
        check(MccMaps.safe("my map (v2)!").equals("my_map__v2__"), "safe names");
        check(MccMaps.safe("..evil").equals("evil"), "no leading dots");

        check(maps.sharedTarget(Arrays.asList("halo1", "maps", "custom_edition"), "sounds.map")
            .equals(new File(game, "mcc_maps/_shared/multiplayer/sounds.map")), "multiplayer sounds");
        check(maps.sharedTarget(Arrays.asList("halo1", "maps", "custom_edition"), "bitmaps.map")
            .equals(new File(game, "mcc_maps/_shared/multiplayer/bitmaps.map")), "multiplayer bitmaps");
        check(maps.sharedTarget(Arrays.asList("halo1", "maps"), "bitmaps.map")
            .equals(new File(game, "mcc_maps/_shared/singleplayer/bitmaps.map")), "singleplayer bitmaps");
        check(maps.sharedTarget(Arrays.asList("halo1", "maps"), "sounds.map") == null, "singleplayer sounds not MCC's set");
        check(maps.sharedTarget(Arrays.asList("halo1", "maps"), "a10.map") == null, "levels are not shared resources");

        MccMaps.copy(new ByteArrayInputStream(header(true, 13, 0, "m0")), a);
        MccMaps.copy(new ByteArrayInputStream(header(true, 13, 1, "mp")), new File(game, "mcc_maps/loose_mp.map"));
        File ce = maps.target("ce", Arrays.asList(), "bloodgulch2.map");
        MccMaps.copy(new ByteArrayInputStream(header(true, 609, 1, "ce")), ce);
        check(MccMaps.keepLevel(a), "an MCC level kept");
        check(!MccMaps.keepLevel(ce) && !ce.exists(), "a Custom Edition level not kept");
        File res = maps.target("x", Arrays.asList("pack"), "bitmaps.map");
        MccMaps.copy(new ByteArrayInputStream(new byte[100]), res);
        check(MccMaps.keepLevel(res) && res.exists(), "resource maps kept");
        check(!new File(a.getPath() + ".part").exists(), "no .part left");
        int[] counts = maps.levels();
        check(counts[0] == 1 && counts[1] == 1, "counts " + counts[0] + "/" + counts[1]);
        check(!maps.sharedSingleplayer() && !maps.sharedMultiplayer(), "no shared yet");
        MccMaps.copy(new ByteArrayInputStream(new byte[10]), new File(game, "mcc_maps/_shared/singleplayer/bitmaps.map"));
        check(maps.sharedSingleplayer() && maps.levels()[0] == 1, "shared is not a package");
        check(maps.summary().contains("1 campaign and 1 multiplayer"), maps.summary());
        File keep = new File(game, "maps/a10.map");
        keep.getParentFile().mkdirs(); new FileOutputStream(keep).close();
        maps.removeAll();
        check(!new File(game, "mcc_maps").exists() && keep.exists(), "remove takes mcc_maps only");
        System.out.println("PASS: Test67 MCC maps launcher: headers, packages, safe names, level-name limit, MCC's shared resources, non-MCC levels refused, counts and removal");

        // A downloaded Workshop item: ModInfo.json, halo1/maps with a level, its
        // resources and description, and another game's map; installed as a
        // package with its Workshop details
        File item = new File(args[0], "download");
        File h1 = new File(item, "halo1/maps");
        h1.mkdirs();
        new FileOutputStream(new File(item, "ModInfo.json")).close();
        MccMaps.copy(new ByteArrayInputStream(header(true, 13, 0, "mercury_falling")), new File(h1, "a10.map"));
        MccMaps.copy(new ByteArrayInputStream(new byte[300]), new File(h1, "sounds.map"));
        MccMaps.copy(new ByteArrayInputStream("A reworked Pillar of Autumn".getBytes()), new File(h1, "a10.txt"));
        File h2 = new File(item, "halo2/maps");
        h2.mkdirs();
        MccMaps.copy(new ByteArrayInputStream(new byte[0x800]), new File(h2, "zanzibar.map"));
        MccMaps.Installed installed = maps.installWorkshop(item, 123456789L, "Mercury Rising: The Pillar (v2)!", 1000L);
        check(installed.packageName.equals("Mercury_Rising__The_Pill"), "package name " + installed.packageName);
        check(installed.levels == 1 && installed.resources == 2, "levels/resources " + installed.levels + "/" + installed.resources);
        check(installed.skipped.contains("zanzibar.map"), "another game's map skipped");
        File folder = new File(game, "mcc_maps/" + installed.packageName);
        check(new File(folder, "a10.map").isFile() && new File(folder, "sounds.map").isFile() &&
            new File(folder, "a10.txt").isFile() && new File(folder, MccMaps.WORKSHOP_FILE).isFile(), "package files");
        check(!new File(game, "mcc_maps/" + installed.packageName + ".installing").exists() &&
            !maps.stagingRoot().exists(), "no staging left");
        List<MccMaps.Package> list = maps.packages();
        check(list.size() == 1 && list.get(0).workshopId == 123456789L && list.get(0).workshopUpdated == 1000L &&
            list.get(0).title.equals("Mercury Rising: The Pillar (v2)!") && list.get(0).enabled && list.get(0).levels == 1 &&
            list.get(0).bytes > 0, "package listed");
        check(maps.levels()[0] == 1, "counted");
        maps.setEnabled(list.get(0), false);
        check(new File(game, "mcc_maps_disabled/" + installed.packageName + "/a10.map").isFile() &&
            !folder.exists(), "disabled: moved aside, kept whole");
        check(maps.levels()[0] == 0 && !maps.packages().get(0).enabled, "a disabled package is not counted");
        // an update of a disabled package lands where it is
        MccMaps.Installed again = maps.installWorkshop(item, 123456789L, "Mercury Rising: The Pillar (v2)!", 2000L);
        check(again.packageName.equals(installed.packageName), "same package on update");
        check(maps.packages().size() == 1 && !maps.packages().get(0).enabled && maps.packages().get(0).workshopUpdated == 2000L,
            "updated in place, still disabled");
        maps.setEnabled(maps.packages().get(0), true);
        check(folder.isDirectory() && maps.levels()[0] == 1, "enabled again");
        // an install interrupted mid-copy: its half-copied files are removed;
        // a package set aside for its update, which never arrived, comes back
        File half = new File(maps.stagingRoot(), "Half_copied");
        half.mkdirs();
        MccMaps.copy(new ByteArrayInputStream(header(true, 13, 0, "half")), new File(half, "half.map"));
        check(folder.renameTo(new File(maps.stagingRoot(), installed.packageName + ".previous")), "set aside");
        check(maps.packages().size() == 1 && maps.packages().get(0).name.equals(installed.packageName) &&
            folder.isDirectory() && !maps.stagingRoot().exists(), "interrupted install recovered");
        // another item of the same title gets its own package
        MccMaps.Installed other = maps.installWorkshop(item, 987L, "Mercury Rising: The Pillar (v2)!", 5L);
        check(other.packageName.equals(installed.packageName + "_2"), "a different item numbered: " + other.packageName);
        // an item with no Halo 1 MCC map installs nothing
        File empty = new File(args[0], "empty");
        new File(empty, "halo3/maps").mkdirs();
        MccMaps.copy(new ByteArrayInputStream(new byte[0x800]), new File(empty, "halo3/maps/guardian.map"));
        boolean refused = false;
        try { maps.installWorkshop(empty, 55L, "Guardian", 1L); } catch (IOException e) { refused = e.getMessage().contains("no Halo 1 MCC maps"); }
        check(refused && maps.packages().size() == 2, "no Halo 1 maps: refused, nothing installed");
        for (MccMaps.Package each : maps.packages()) maps.delete(each);
        check(maps.packages().isEmpty() && maps.levels()[0] == 0, "deleted");
        System.out.println("PASS: Test67 MCC packages: Workshop install (Halo 1 levels, their resources and descriptions; other games skipped), listing with size and Workshop details, disable/enable kept whole, update in place, interrupted installs recovered, distinct items, refusal, delete");
    }
}
'''

with tempfile.TemporaryDirectory(prefix="test67-mcc-") as directory:
    work = Path(directory)
    (work / "src").mkdir()
    (work / "src/MccCheck.java").write_text(CHECK, encoding="utf-8")
    out = work / "out"
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(out), str(JAVA / "MccMaps.java"),
                    str(work / "src/MccCheck.java")], check=True)
    game = work / "game"
    game.mkdir()
    subprocess.run(["java", "-cp", str(out), "com.halo.decomp.MccCheck", str(game)], check=True)

# the engine side
cache = read("source/cache/cache_files.c")
assert '#include "mcc_cache.h"' in cache
assert "if (mcc_level_name(scenario_name))" in cache and "mcc_cache_tags_load(scenario_name" in cache
assert "vr_menu_tags_loaded();" in cache.split("mcc_cache_tags_load(scenario_name", 1)[1].split("return result;", 1)[0]
assert "loose_sounds" not in cache
limits = read("port/linux/include/halo_port_limits.h")
assert "#define HALO_PORT_NETWORK_VERSION 29" in limits and "MCC SHA-256" not in limits
distributed = read("port/linux/game/network_distributed.h")
assert "_distributed_message_mcc" not in distributed
assert "mcc_content_sha256" not in read("source/networking/network_game_manager.h")
offline = read("port/linux/game/mcc_offline.h")
assert "#define MCC_DISTRIBUTED_SEND(...) ((void)0)" in offline
for name in ("mcc_game_speed.c", "mcc_network.c", "mcc_object_names_network.c"):
    source = read("port/linux/game/" + name)
    assert "distributed_send(" not in source and "MCC_DISTRIBUTED_SEND(" in source, name
identity = read("port/linux/game/mcc_identity.c")
assert "MCC maps play solo in this build: they cannot be hosted online." in identity
assert "MCC maps play solo in this build: a game on one cannot be joined." in identity
assert "return game_connection()!=_game_connection_network_client &&" in identity
menus = read("port/linux/game/menu_functions.c")
assert "static boolean map_kind_unavailable(short kind)" in menus
assert "while ((!singleplayer && map_kind_singleplayer(kind)) || map_kind_unavailable(kind));" in menus
vorbis = read("port/linux/game/mcc_vorbis.c")
assert '#include "../../third_party/stb/stb_vorbis.c"' in vorbis
assert (ROOT / "port/third_party/bcdec/bcdec.h").is_file() and (ROOT / "port/third_party/bcdec/LICENSE").is_file()
workshop = read("port/android/app/src/main/java/com/halo/decomp/WorkshopActivity.java")
steam = read("port/android/app/src/main/java/com/halo/decomp/SteamWorkshop.java")
assert "requiredtags%5B%5D=Halo1Campaign" in workshop and "Download to Halo" in workshop
assert '"Disable"' in workshop and '"Enable"' in workshop and '"Delete"' in workshop and '"Check for update"' in workshop
assert "ISteamRemoteStorage/GetPublishedFileDetails/v1/" in steam and "ISteamRemoteStorage/GetCollectionDetails/v1/" in steam
assert "beginAuthSessionViaCredentials" in steam and "acceptDeviceConfirmation" in steam
assert 'putString("token", result.getRefreshToken())' in steam and '"password"' not in steam
assert "new PubFileItem(MCC_APP_ID, id, false, folder.getAbsolutePath(), false, false)" in steam
gradle = read("port/android/app/build.gradle")
assert 'implementation "in.dragonbra:javasteam:1.8.0"' in gradle and 'implementation "in.dragonbra:javasteam-depotdownloader:1.8.0"' in gradle
assert ".WorkshopActivity" in read("port/android/app/src/main/AndroidManifest.xml")
launcher = read("port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java")
assert '"Steam Workshop: download MCC maps"' in launcher and "WorkshopActivity.EXTRA_MANAGE" in launcher
assert '"HALO 1 MCC MAPS (SOLO)"' in launcher and 'ModInstaller.STATUS_EXPERIMENTAL' in launcher and "PICK_MCC_MAPS" in launcher and "PICK_MCC_SHARED" in launcher
print("PASS: Test67 MCC engine wiring: GulchCE's loader dispatched, OpenCE network 29 (Build206) unchanged by MCC (no MCC messages or "
      "fingerprint, sends compiled out, MCC hosting/joining refused, host chooser skips MCC kinds), port's stb_vorbis, bcdec")
