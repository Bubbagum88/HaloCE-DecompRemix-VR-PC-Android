"""The Steam Frame bundle: HaloCEQuestVR-SteamFrame.zip, which a player unpacks in the Frame's Downloads (Desktop Mode)
and installs from with "Install HaloCE Quest VR.desktop" (tools/steam_frame/install.sh; docs/VR_ARCHITECTURE.md).

    python tools/steam_frame/bundle.py <the VR APK> <output folder>

The zip holds one folder, HaloCEQuestVR-SteamFrame, with the VR APK as HaloCEQuestVR.apk, install.sh, launch.sh (the
Steam library's launcher), the desktop file and a short README. Scripts keep their LF line ends and are marked
executable in the zip (its Unix permissions, which the Frame's Ark keeps). Writes nothing else.
"""
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
FOLDER = "HaloCEQuestVR-SteamFrame"
README = """HaloCE Quest VR for the Steam Frame

1. On the Frame, switch to Desktop Mode (Steam menu > Power > Switch to Desktop).
2. Put this zip and your own disc image of Halo: Combat Evolved for the original Xbox (.iso or .xiso)
   in Downloads.
3. Unpack the zip there (Extract here): a folder HaloCEQuestVR-SteamFrame.
4. Open "Install HaloCE Quest VR" in that folder (if you are asked whether to run it, continue)
   and answer the dialogs. It adds HaloCE Quest VR to your Steam library.
5. Back in Gaming Mode, start HaloCE Quest VR from the library (Non-Steam). Its first start copies
   what the game needs out of your disc image (a few minutes).

The game's data, settings, saves and logs: Documents/HaloCEQuestVR. To update, unpack a newer bundle
and open its installer again; your settings and saves stay. To quit: the main menu's QUIT GAME,
or Steam's Exit game.

Something wrong? Each run's log is in Documents/HaloCEQuestVR/logs (halo_log_<date>_<time>.txt, the
newest the last run; the last ten are kept). Beside that folder: launcher.log (each start from
Steam), logcat.txt (the last run's Android log) and install.log (the installer's). Send the run's
log with a few words on what happened.
"""


def main(apk, output):
    apk, output = Path(apk), Path(output)
    assert apk.is_file() and apk.suffix == ".apk", apk
    files = [("HaloCEQuestVR.apk", apk.read_bytes(), 0o644)]
    for name in ("install.sh", "launch.sh"):
        data = (HERE / name).read_bytes()
        assert b"\r" not in data and data.startswith(b"#!/bin/bash\n"), name
        files.append((name, data, 0o755))
    desktop = (HERE / "Install HaloCE Quest VR.desktop").read_bytes()
    assert b"\r" not in desktop
    files.append(("Install HaloCE Quest VR.desktop", desktop, 0o755))
    files.append(("README.txt", README.encode("utf-8"), 0o644))
    output.mkdir(parents=True, exist_ok=True)
    target = output / (FOLDER + ".zip")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data, mode in files:
            info = zipfile.ZipInfo(FOLDER + "/" + name, date_time=(2026, 10, 22, 0, 0, 0))
            info.create_system = 3  # Unix: its permissions are read
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_STORED if name.endswith(".apk") else zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(target)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
