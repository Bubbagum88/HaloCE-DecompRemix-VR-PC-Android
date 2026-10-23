#!/usr/bin/env python3
"""Makes the desktop builds' icons from this port's launcher artwork (the Android launcher icon's full-colour layer,
port/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_background_art.png, 432x432; its foreground layer is
transparent):

    python tools/desktop_icon.py

- port/assets/icon/haloce-quest-vr-256.png: the window's icon on the desktop builds (tools/embed_assets.py embeds it,
  port/linux/src/sdl_platform.c gives it to the window);
- port/windows/haloce-quest-vr.ico: halo.exe's and halo-vr.exe's own icon, which Explorer and the taskbar show
  (port/windows/halo.rc, compiled by tools/windows_build.py), in the sizes Windows asks for.

OpenCE's tools/app_icon.py makes its icons from its helmet artwork; this port keeps its own. Run it again when the
artwork changes. Needs Pillow (pinned at 12.0.0 for this repository's art: tools/button_assets.py)."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ARTWORK = ROOT / "port/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_background_art.png"
WINDOW_ICON = ROOT / "port/assets/icon/haloce-quest-vr-256.png"
WINDOWS_ICON = ROOT / "port/windows/haloce-quest-vr.ico"
WINDOWS_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def main() -> None:
    artwork = Image.open(ARTWORK).convert("RGBA")
    WINDOW_ICON.parent.mkdir(parents=True, exist_ok=True)
    artwork.resize((256, 256), Image.LANCZOS).save(WINDOW_ICON, optimize=True)
    # (each size scaled from the artwork itself, not from the next larger)
    largest = artwork.resize((256, 256), Image.LANCZOS)
    largest.save(WINDOWS_ICON, format="ICO", sizes=[(size, size) for size in WINDOWS_SIZES])
    print(f"wrote {WINDOW_ICON.relative_to(ROOT)} and {WINDOWS_ICON.relative_to(ROOT)} ({len(WINDOWS_SIZES)} sizes)")


if __name__ == "__main__":
    main()
