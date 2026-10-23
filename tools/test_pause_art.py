"""Check the shipped pause artwork at its logical widget coordinates."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[1]
MENUS = ROOT / 'port/assets/menus'


@pytest.mark.parametrize('piece', ['left', 'center', 'right'])
@pytest.mark.parametrize('frame,height', [(0, 194), (1, 229), (2, 195), (3, 225), (4, 255)])
def test_button_strip(piece, frame, height):
    image = Image.open(MENUS / f'ce/port/pause/pausebox_{piece}__{frame}.png').convert('RGBA')
    scale = image.height // 256
    x = image.width // 2
    # Stock Xbox footer alpha is 191/255, with no blue body underneath.
    assert image.getpixel((x, (height - 15) * scale)) == (0, 0, 0, 191)
    assert_campaign_gradient(image, 2, height - 29, piece)
    # (port: the 255-unit frame is the texture's whole height: nothing below it)
    if height + 1 < 256:
        assert image.getpixel((x, (height + 1) * scale))[3] == 0
    assert image.getpixel((x, (height - 28) * scale))[:3] == (40, 150, 255)


# (port: a frame for each campaign box height, OpenCE 244's 225 and this port's 255 after the stock 195)
OBJECTIVES_HEIGHTS = [195, 225, 255]


@pytest.mark.parametrize('piece', ['left', 'center', 'right'])
@pytest.mark.parametrize('frame', range(len(OBJECTIVES_HEIGHTS)))
def test_objective_header(piece, frame):
    height = OBJECTIVES_HEIGHTS[frame]
    name = f'ce/port/pause/objectives_{piece}__{frame}.png'
    image = Image.open(MENUS / name).convert('RGBA')
    scale = image.height // 256
    x = image.width // 2
    assert image.getpixel((x, 15 * scale)) == (0, 0, 0, 255)
    assert image.getpixel((x, 28 * scale))[:3] == (40, 150, 255)
    assert_campaign_gradient(image, 29, height - 3, piece)
    if height + 1 < 256:
        assert image.getpixel((x, (height + 1) * scale))[3] == 0
    if piece != 'center':
        assert image.getpixel((0 if piece == 'left' else image.width - 1, 0))[3] == 0
    definitions = ET.parse(MENUS / 'ce/bitmaps.xml').getroot()
    bitmap = definitions.find(f"bitmap[@name='pause/objectives_{piece}']")
    assert [frame.get('png') for frame in bitmap] == \
        [f'ce/port/pause/objectives_{piece}__{index}.png' for index in range(len(OBJECTIVES_HEIGHTS))]
    assert name in json.loads((MENUS / 'menus.json').read_text())['files']


def assert_campaign_gradient(image, top, bottom, piece):
    scale = image.height // 256
    x = image.width // 2
    x = image.width - 1 if piece == "left" else 0 if piece == "right" else x
    samples = [image.getpixel((x, y * scale)) for y in range(top, bottom + 1)]
    assert samples[0] == pytest.approx((10, 38, 73, 191), abs=2)
    assert samples[-1] == pytest.approx((5, 13, 28, 191), abs=2)
    assert all(pixel[3] == 191 for pixel in samples)
    for a, b in zip(samples, samples[1:]):
        assert all(b[channel] <= a[channel] for channel in range(3))
