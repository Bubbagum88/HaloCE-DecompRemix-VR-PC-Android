#!/usr/bin/env python3
"""Generate density-specific adaptive launcher icon assets.

The artwork includes detailed full-colour lettering, a dark emblem and its
background. Preserve the supplied image as a whole instead of colour-keying it
into a simplified foreground. Android masks the full-colour background layer
for its adaptive icon. The transparent foreground keeps the adaptive resource
valid without covering or flattening the artwork.

Run with: python tools/android_icon.py
Requires Pillow.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ARTWORK = ROOT / "port/android/art/android-icon.png"
RESOURCES = ROOT / "port/android/app/src/main/res"
LAYER_DP = 108
DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}


def main() -> None:
    artwork = Image.open(ARTWORK).convert("RGBA")
    width, height = artwork.size
    if width != height:
        raise ValueError(f"launcher artwork must be square, got {width}x{height}")

    for density, scale in DENSITIES.items():
        size = round(LAYER_DP * scale)
        directory = RESOURCES / f"mipmap-{density}"
        directory.mkdir(parents=True, exist_ok=True)
        artwork.resize((size, size), Image.LANCZOS).save(
            directory / "ic_launcher_background_art.png", optimize=True)
        Image.new("RGBA", (size, size), (0, 0, 0, 0)).save(
            directory / "ic_launcher_foreground.png", optimize=True)
        print(f"{directory.relative_to(ROOT)}: {size}x{size}")

    adaptive = RESOURCES / "mipmap-anydpi-v26"
    adaptive.mkdir(parents=True, exist_ok=True)
    (adaptive / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!-- Full-colour source artwork is kept intact as the adaptive background. -->\n"
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@mipmap/ic_launcher_background_art" />\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
        "</adaptive-icon>\n", encoding="utf-8")
    print(f"preserved full-colour {width}x{height} artwork in adaptive background")


if __name__ == "__main__":
    main()
