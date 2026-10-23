"""Test72: the desktop launcher (Windows flat and PC VR, Linux) and the flat
PC remap UX.

The owner: one launcher for the PC builds (Play, XISO, Verify/Repair, Mods,
Updates, What's New, release notes, graphics, controls, VR and stereo), one
library shared by the flat and PC VR builds, no game data in the packages;
the remap UX with conflict warnings, None, individual reset and Reset All.

Source checks (the launcher draws a window: it is seen on a machine).
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")
launcher = read("port/linux/src/desktop_launcher.c")
header = read("port/linux/src/desktop_launcher.h")
version = read("port/linux/src/halo_port_version.h")
platform = read("port/linux/src/sdl_platform.c")
files = read("port/linux/src/xbox_files.c")
config = read("port/linux/src/port_config.c")
embed = read("tools/embed_assets.py")
menus = read("port/linux/game/menu_functions.c")
controls_xml = read("port/assets/menus/ce/main_menu.settings_select.player_setup.player_profile_edit.controls_setup.xml")
modinstaller = read("port/android/app/src/main/java/com/halo/decomp/ModInstaller.java")

# ---- desktop only; the game as before without it
assert "#if !defined(HALO_ANDROID) && !defined(HALO_WEB)" in launcher
assert "int desktop_launcher_wanted(void) { return 0; }" in launcher  # the other builds' stubs
wanted = launcher[launcher.index("int desktop_launcher_wanted(void)\n{"):]
wanted = wanted[:wanted.index("\n}\n")]
for condition in ('config_boolean("launcher.show")', '!config_boolean("debug.hidden_window")',
                  '!(config_real("debug.exit_after") > 0.0)', '!*config_string("debug.menu_open")', "network_test"):
    assert condition in wanted, condition
assert '{ "launcher.show", _config_boolean, "true", "HALO_LAUNCHER", _environment_value, _platform_desktop,' in config
assert "if (desktop_launcher_wanted())\n\t\tdesktop_launcher_run();\n\t/* found (or offered" in platform
assert "if (desktop_launcher_active() ||" in platform  # the first start's question left to the launcher
assert "platform_log(\"launcher: cannot open its window (%s); the game starts as before\"" in launcher
assert "void platform_data_root_refresh(void)" in files and "if (data_root_stale)" in files

# ---- the pages the owner listed
for page in ("PAGE_HOME", "PAGE_DATA", "PAGE_MODS", "PAGE_MOD", "PAGE_SETTINGS", "PAGE_VR", "PAGE_NEWS", "PAGE_UPDATES"):
    assert "case %s" % page in launcher or page == "PAGE_HOME", page
for label in ('"PLAY"', '"PLAY IN VR"', '"GAME DATA"', '"CUSTOM CAMPAIGNS"', '"SETTINGS"', '"WHAT\'S NEW"', '"UPDATES"',
              '"IMPORT FROM A DISC IMAGE"', '"VERIFY"', '"REPAIR"', '"IMPORT FILES FROM A FOLDER"', '"PUT IT IN THE GAME"',
              '"PUT THE ORIGINAL BACK"', '"FULL RELEASE NOTES (GITHUB)"', '"CHECK"'):
    assert label in launcher, label
# settings: graphics, stereo (flat), movement (flat), the launcher itself; controls in the game
for key in ("display.mode", "display.vsync", "display.max_fps", "display.stereo", "movement.sprint", "launcher.show"):
    assert '"%s"' % key in launcher, key
assert "Controls Setup (keyboard and mouse, with remapping)" in launcher
# updates only when asked; the fork's own releases
assert '"https://api.github.com/repos/" HALO_PORT_REPOSITORY "/releases/latest"' in launcher
assert launcher.count("job_start(JOB_UPDATES") == 1
assert '#define HALO_PORT_REPOSITORY "moistman42069/HaloCE-Quest-VR"' in version
assert 'REPOSITORY="moistman42069/HaloCE-Quest-VR"' in read("port/android/app/src/main/java/com/halo/decomp/UpdatePolicy.java")
assert re.search(r'#define HALO_PORT_VERSION "\d+\.\d+\.\d+-test\d+[a-z]?"', version)

# ---- one library: the maps beside the game; the other build started with it
assert '#define LAUNCHER_FLAT_EXE "halo.exe"' in launcher and '#define LAUNCHER_VR_EXE "halo-vr.exe"' in launcher
assert 'SDL_setenv_unsafe("HALO_LAUNCHER", "0", 1);' in launcher and 'SDL_setenv_unsafe("HALO_CUSTOM_EDITION", "1", 1);' in launcher
assert "xiso_extract_maps(image, root, job_extract_progress, NULL, error, sizeof(error))" in launcher
assert '"library.sha256"' in launcher and "# image %s\\n" in launcher
# a failed repair puts the old maps back
imp = launcher[launcher.index("static int job_import_image("):]
imp = imp[:imp.index("\n}\n")]
assert "if (had)\n\t\t\tSDL_RenamePath(aside, maps);" in imp

# ---- the campaigns: the Android app's ids, folders, markers and checks
for mod_id in ("spv1", "lumoria", "altheros"):
    assert '{ "%s", ' % mod_id in launcher and 'new Mod("%s"' % mod_id in modinstaller or mod_id != "spv1"
for folder in ('"mods", "original"', '"custom_edition.on"', '"%s.on"', '"%s.changing"', '"mods", "ce"', '"data_files"',
               '"support.properties"'):
    assert folder in launcher, folder
assert "file.%s.size" in launcher and "file.%s.sha256" in launcher
assert "done != file->size || strcmp(hex, file->hash)" in launcher  # size and SHA-256
assert "header[4] == 5" in launcher  # the original Xbox map, as isXboxMap
# the embedded recipes are the Android app's files
assert 'LAUNCHER_ASSETS = Path("port/android/app/src/main/assets")' in embed
for name in ("whats_new.txt", "campaigns/spv1.properties", "campaigns/lumoria.properties", "campaigns/altheros.properties"):
    assert '"%s"' % name in embed, name
assert "const struct desktop_launcher_file desktop_launcher_files[] =" in embed
assert "extern const struct desktop_launcher_file desktop_launcher_files[];" in header
# the maps each recipe lists are the launcher's
for mod_id in ("spv1", "lumoria", "altheros"):
    recipe = read("port/android/app/src/main/assets/campaigns/%s.properties" % mod_id)
    names = sorted(set(re.findall(r"^file\.([\w-]+)\.(?:map|yelo)\.size=", recipe, re.M)))
    block = launcher[launcher.index('{ "%s", ' % mod_id):]
    block = block[:block.index("}, %d }" % (10 if mod_id != "lumoria" else 4)) + 1]
    listed = sorted(re.findall(r'\{ "([\w]+)", [01] \}', block))
    resources = {"bitmaps", "sounds", "loc", "alsthetic-bitmaps", "alsthetic-sounds", "alsthetic-loc"}
    assert listed == sorted(n for n in names if n not in resources), (mod_id, listed, names)

# ---- the remap UX: conflict warnings, NONE, a binding's default, Reset All
assert "event->key.scancode == SDL_SCANCODE_BACKSPACE ? 4 : 1" in platform
assert "event->key.scancode == SDL_SCANCODE_DELETE ? 2 :" in platform
assert "controls_screen.moved_until = system_milliseconds() + 5000;" in menus
assert "system_milliseconds() < controls_screen.moved_until ? 3 :" in menus
assert "else if (result == 4)" in menus and "config_default(controls[control].setting, text, sizeof(text));" in menus
assert '"NONE"' in menus[menus.index("static void controls_update("):menus.index("static void controls_update(") + 3000]
assert 'text="That key was another action\'s: it is this one\'s\\nnow. One left with no key shows NONE."' in controls_xml
assert "Delete: NONE, Backspace: its default." in controls_xml
assert "DEFAULTS resets them all." in controls_xml

print("PASS: Test72 desktop launcher (play, game data import/verify/repair, the Android campaigns' recipes and folders, "
      "settings, PC VR, What's New, updates on request) and the remap UX (warnings, NONE, a binding's default, all)")
