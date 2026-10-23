"""Test73, item 10 (the owner's: "add an option in the launcher to have the main menu projected in front of you and
not following your head like it does by default"): MENU POSITION (vr.menu_anchor, Test72's in-game row: head, the
default; world; follow) is now chosen in the launchers too, the Quest/PICO/Frame app's (Menu position, VR only:
MenuPosition.java) and the PC VR one's (SETTINGS: MENU POSITION). The main menu is a menu like the others for it
(vr_ui_pointer's menus_active), so "world" holds it still in front.

Pinned: the three values agree in the game (vr_frame.c's menu_anchor, vr_menu.c's row, port_config.c's default),
the PC launcher's row (VR build only) and the Android one's. Run here (javac): MenuPosition's read and save over
ConfigSettings, the written config read back by Python's TOML reader as the game reads it, other settings and
sections kept, an unknown value read as the default, an unknown choice refused.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'port/android/app/src/main/java/com/halo/decomp'
frame = (ROOT / 'port/linux/src/vr_frame.c').read_text(encoding='utf-8')
menu = (ROOT / 'port/linux/game/vr_menu.c').read_text(encoding='utf-8')
config = (ROOT / 'port/linux/src/port_config.c').read_text(encoding='utf-8')
desktop = (ROOT / 'port/linux/src/desktop_launcher.c').read_text(encoding='utf-8')
launcher = (JAVA / 'LauncherActivity.java').read_text(encoding='utf-8')
help_source = (JAVA / 'LauncherHelp.java').read_text(encoding='utf-8')
position = (JAVA / 'MenuPosition.java').read_text(encoding='utf-8')

VALUES = ['head', 'world', 'follow']
assert ('return !strcmp(anchor, "world") ? 1 : !strcmp(anchor, "follow") ? 2 : 0;' in frame)
assert ('{ "MENU POSITION", "vr.menu_anchor", _vr_setting_string, 3, { { "HEAD", "head" }, { "WORLD", "world" }, '
        '{ "FOLLOW", "follow" } } },') in menu
assert '{ "vr.menu_anchor", _config_string, "\\"head\\"", "HALO_VR_MENU_ANCHOR"' in config
# the main menu is a menu for it: the panel is placed while menus_active, whatever the map
pose = frame[frame.index('static int menu_world_pose(void)\n{'):]
pose = pose[:pose.index('\n}\n')]
assert 'if (!vr.menus_active || vr.mode != VR_MODE_STEREO || !anchor)' in pose
assert 'scenario' not in pose and 'map_name' not in pose  # (no exception for the main menu's map)
assert 'vr.menus_active = menus_active != 0;' in frame
# the PC VR launcher: SETTINGS' row, in the VR build only, the same values
rows = desktop[desktop.index('static const struct launcher_setting launcher_settings[] ='):]
rows = rows[:rows.index('};')]
vr_block = rows[rows.index('#ifdef HALO_VR'):]
vr_block = vr_block[:vr_block.index('#endif')]
match = re.search(r'\{ "MENU POSITION", "vr\.menu_anchor", 3, \{ "head", "world", "follow" \},', vr_block)
assert match, vr_block
assert 'MENU POSITION' not in rows.replace(vr_block, '')
assert '"also in SETTINGS here: MENU POSITION."\n#endif' in desktop
# the Android app's: VR only, through MenuPosition
assert ('if (BuildConfig.APPLICATION_ID.endsWith(".vr"))\n            menuButton(layout, "Menu position").setOnClickListener('
        'v -> { if (!busy) LauncherHelp.menuPosition(this, gameRoot()); });') in launcher
assert 'MenuPosition.save(root,MenuPosition.ANCHORS[which]);' in help_source
assert 'static final String[] ANCHORS = { "head", "world", "follow" };' in position
assert 'import android' not in position  # (plain Java: run here)

HARNESS = r'''
package com.halo.decomp;
import java.io.*;
import java.nio.file.*;
public class MenuPositionCheck {
    static void check(boolean ok, String what) { if (!ok) throw new AssertionError(what); }
    public static void main(String[] args) throws Exception {
        File root = new File(args[0]);
        File config = new File(root, "config.toml");
        // nothing saved: the default
        check(MenuPosition.read(root).equals("head"), "default " + MenuPosition.read(root));
        Files.write(config.toPath(), ("# the player's own\n[renderer]\nsafe_geometry = true\n\n[vr]\nhud_distance = 15.0\n"
            + "menu_anchor = \"follow\" # chosen in the game\n\n[network]\nonline = true\n").getBytes("UTF-8"));
        check(MenuPosition.read(root).equals("follow"), "follow " + MenuPosition.read(root));
        MenuPosition.save(root, "world");
        check(MenuPosition.read(root).equals("world"), "world " + MenuPosition.read(root));
        String text = new String(Files.readAllBytes(config.toPath()), "UTF-8");
        check(text.contains("hud_distance = 15.0") && text.contains("[network]\nonline = true") && text.startsWith("# the player's own"),
            "kept: " + text);
        Files.write(new File(root, "written.toml").toPath(), text.getBytes("UTF-8"));
        // no [vr] section yet
        Files.write(config.toPath(), "[renderer]\nsafe_geometry = false\n".getBytes("UTF-8"));
        MenuPosition.save(root, "follow");
        Files.copy(config.toPath(), new File(root, "added.toml").toPath());
        // an unknown value: the default; an unknown choice: refused, the file unchanged
        Files.write(config.toPath(), "[vr]\nmenu_anchor = \"sideways\"\n".getBytes("UTF-8"));
        check(MenuPosition.read(root).equals("head"), "unknown read " + MenuPosition.read(root));
        try { MenuPosition.save(root, "sideways"); check(false, "refused"); } catch (IOException expected) { }
        check(new String(Files.readAllBytes(config.toPath()), "UTF-8").equals("[vr]\nmenu_anchor = \"sideways\"\n"), "unchanged");
        System.out.println("ok");
    }
}
'''

with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    package = work / 'src/com/halo/decomp'
    package.mkdir(parents=True)
    for name in ('ConfigSettings.java', 'MenuPosition.java'):
        (package / name).write_text((JAVA / name).read_text(encoding='utf-8'), encoding='utf-8')
    (package / 'MenuPositionCheck.java').write_text(HARNESS, encoding='utf-8')
    subprocess.run(['javac', '-d', str(work / 'out'), *map(str, package.glob('*.java'))], check=True)
    data = work / 'data'
    data.mkdir()
    run = subprocess.run(['java', '-cp', str(work / 'out'), 'com.halo.decomp.MenuPositionCheck', str(data)],
                         capture_output=True, text=True)
    assert run.returncode == 0 and run.stdout.strip() == 'ok', run.stdout + run.stderr
    # read back as TOML, as the game's parser reads config.toml
    written = tomllib.loads((data / 'written.toml').read_text(encoding='utf-8'))
    assert written['vr'] == {'hud_distance': 15.0, 'menu_anchor': 'world'}, written
    assert written['renderer'] == {'safe_geometry': True} and written['network'] == {'online': True}, written
    added = tomllib.loads((data / 'added.toml').read_text(encoding='utf-8'))
    assert added == {'renderer': {'safe_geometry': False}, 'vr': {'menu_anchor': 'follow'}}, added
    assert all(value in VALUES for value in (written['vr']['menu_anchor'], added['vr']['menu_anchor']))

print('PASS: Test73 menu position: the launchers choose MENU POSITION (head default, world, follow) as the game reads it; '
      'the PC VR launcher\'s SETTINGS row in the VR build only; the Android app\'s VR only; other settings kept')
