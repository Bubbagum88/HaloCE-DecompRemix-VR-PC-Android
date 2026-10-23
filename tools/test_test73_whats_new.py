"""Test73, item 11 (the owner: "make sure the new features details are more clean (the pop up that shows new
features in the laucnher is the one i mean)"): What's New, the same notes (whats_new.txt) on both launchers, shown as
they are written: the first line the title, a line in capitals a heading, "• " a point whose lines wrap after its
bullet, a blank line a small gap, anything else plain text.

- The PC launcher: desktop_launcher.c's own news_line_kind and news_layout, compiled (ASan/UBSan) over stand-ins
  for its text drawing, laid out over the real notes: every line drawn once, in its kind's place and colour (points'
  text after the bullet, the bullet drawn on its own), the measured height the drawn one, nothing cut.
- The Android launcher: WhatsNew.java compiled against the SDK's android.jar (with stand-ins for its package's
  classes), and its pure kind() run over the same lines: the same kind as the PC's for every line.
- The notes: every Test73 change named (the owner: the pop-up must not miss anything), short points, Test72's and
  Test71's since 1.0.37 (the last published), and 1.0.37's pointed to on GitHub.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73-whats-new'
OUT.mkdir(parents=True, exist_ok=True)
notes = (ROOT / 'port/android/app/src/main/assets/whats_new.txt').read_text(encoding='utf-8')
launcher = (ROOT / 'port/linux/src/desktop_launcher.c').read_text(encoding='utf-8')
java = (ROOT / 'port/android/app/src/main/java/com/halo/decomp/WhatsNew.java').read_text(encoding='utf-8')

# ---------- the notes themselves
assert '\r' not in notes and notes.startswith('NEW IN THIS UPDATE (TEST73B)\n')
lines = notes.split('\n')
headings = [l for l in lines[1:] if l.strip() and not l.startswith('\u2022 ') and not re.search('[a-z]', l)]
assert headings == ['FIXES AND ADDITIONS (TEST73B)',
                    'EVERY VR FEATURE ON (QUEST AND PC VR)', 'CO-OP: VR FOR EVERY PLAYER', 'VEHICLES',
                    'COMBAT, GRENADES AND SCOPES', 'MOVEMENT AND BODY', 'MENUS AND LAUNCHERS', 'STEAM FRAME AND PC',
                    'FROM OPENCE (BUILDS 232 TO 256)', 'ALSO NEW SINCE 1.0.37 (TEST72)',
                    'ALSO NEW SINCE 1.0.37 (TEST71)'], headings
points = [l for l in lines if l.startswith('\u2022 ')]
assert len(points) >= 40
for point in points:
    # (clean: a point is a sentence or two, three lines of the popup at most)
    assert len(point) <= 240, point
# the owner: the pop-up must not miss anything: every Test73 change is named
for feature in ('settings and saves are kept', 'turned on once', 'MAG DEBRIS', 'fist combat', 'physical grenades',
                'parkour', 'slides', 'NPC grab', 'one-hand heavies', 'BULLET TIME', 'IMMERSIVE VEHICLE',
                'VR INTERACTIONS', 'CO-OP OPTIONS', 'manual reload', 'HOST VR ACTIONS', 'full lock', 'Warthog',
                'Scorpion', 'HAND LOCK', 'VEHICLE TURN', 'snap again once you are out', '6DoF', 'GRENADE SIZE', "game's own size", 'shows in your hand', '400%',
                'wall run', 'where you look', 'ARMS FROM', 'MENU POSITION', 'IMPORT SAVES', 'EXPORT SAVES',
                'GEOMETRY', 'every level unlocked', 'FRIENDLY FIRE', 'Steam Frame', 'finger touches', 'Index',
                'middle finger', 'icon', 'TEXT CHAT', 'pings', 'MATCH TIMER', 'EXTRA PICKUPS', 'EXTRA VEHICLES',
                'gravity lift', 'TEXTURE FILTERING', 'MODEL DETAIL', 'HDR', 'New Game', 'checkpoints', '5.1',
                'AMD', 'Network 34', '11 to 34', 'once their build is on network 34', 'energy shields', 'tripmines',
                # Test73b's (its own section, Test73's after it)
                'STENCIL SHADOWS', 'back as HALOFREAK95 made them', 'is undone', 'your body casts a shadow',
                "the game's own shadows", 'BODY on LEGS or FULL', 'B goes back in the menus',
                "the Steam Frame's included", 'whether you point at the menus or not', '20 MB/s', '10 MB/s',
                'UPLOAD LIMIT', 'LOGS page', 'logs folder', 'Documents/HaloCEQuestVR/logs',
                'SPRINT TOGGLE', 'set once for everyone', 'hold the turn stick down to crouch',
                "the move stick's click sprints", 'BULLET TIME (the right stick up) works on every controller',
                "a SPRINT button on Android's touch screen", 'Left Shift sprints', 'CONTROLS in every launcher',
                'a body you hold as a shield', 'WORLD SCALE', '70% to 150%',
                "Test73's changes, in this update too:",
                # the Steam Frame ports (tools/test_test73_frame_ports.py)
                'Smoother motion', 'install it on the Frame itself', "Steam's Exit game", 'waits for SteamVR',
                # OpenCE Build 249 to 256 and its testing branch
                'ALLY FRIENDLY FIRE', 'Keyes', 'Pillar of Autumn', 'blast door', 'cursor', 'NVIDIA',
                "Custom Edition maps' textures",
                # Test72 and Test71, since 1.0.37
                'Pico', 'Windows', 'lunges', 'HIT ASSIST', 'COMBO DISPLAY', 'Shade', 'Shot deflection',
                'THIRD PERSON', 'SPRINT, SLIDE, WALL RUN and WALL JUMP', 'HALOFREAK95', 'HOLSTERED GUNS',
                'FAST DECALS', 'BLOOD LAYERS', 'RIFLE DISPLAY', 'VPN', 'Download and install', 'halomaps.org',
                'moddb.com', "launcher's own browser", 'SHA-256', '.rar', '5 GB free', 'resumes',
                '"Experimental \u2014 currently not working"', 'SPV1 included',
                "MANUAL RELOAD now works with the mods' own guns", 'shaken to reload',
                'Version 1.0.37 (Test70) and earlier: the full release notes on GitHub.'):
    assert feature in notes, feature
# (Test73b: the stencil shadows' light change undone, so its line gone; the Frame started on one since)
for gone in ('only the light it blocks', 'Not yet confirmed on a Frame'):
    assert gone not in notes, gone

# ---------- the PC launcher's layout, compiled
start = launcher.index('enum news_line { NEWS_GAP')
end = launcher.index('static void page_news(void)')
layout = launcher[start:end]
colors = ''.join(m.group(0) + '\n' for m in re.finditer(r'^#define COLOR_[A-Z]+ 0x[0-9A-F]+u$', launcher, re.M))
harness = r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned int Uint32;
#define LAUNCHER_WIDTH 1280
''' + colors + r'''
struct launcher_font { float size; };
static struct { struct launcher_font body, small; } ui = { { 20.0f }, { 16.0f } };
struct call { int kind; float x, y, width; Uint32 color; char text[2048]; };
static struct call calls[4096];
static int count, drawing;
/* stand-ins: a line of text wraps at 11 px a character (the height a line, 1.25 the font's size) */
static float text_wrapped(const struct launcher_font *font, float x, float y, float width, const char *text,
	Uint32 color, int draw, float top, float bottom)
{
	float lines = 1.0f + (float)(int)(strlen(text) * 11.0f / width);
	(void)top; (void)bottom;
	assert(font == &ui.body && !strchr(text, '\n'));
	if (draw)
	{
		assert(count < 4096);
		calls[count].kind = 0; calls[count].x = x; calls[count].y = y; calls[count].width = width;
		calls[count].color = color; snprintf(calls[count].text, sizeof(calls[count].text), "%s", text); count++;
	}
	return lines * font->size * 1.25f;
}
static float text_draw(const struct launcher_font *font, float x, float y, const char *text, Uint32 color)
{
	assert(font == &ui.body && count < 4096 && drawing);
	calls[count].kind = 1; calls[count].x = x; calls[count].y = y; calls[count].width = 0;
	calls[count].color = color; snprintf(calls[count].text, sizeof(calls[count].text), "%s", text); count++;
	return 0.0f;
}
''' + layout + r'''
int main(int argc, char **argv)
{
	FILE *file = fopen(argv[1], "rb");
	static char text[1 << 20];
	size_t size;
	float measured, drawn;
	(void)argc;
	assert(file);
	size = fread(text, 1, sizeof(text) - 1, file);
	fclose(file);
	text[size] = 0;
	measured = news_layout(text, 0.0f, 0, 0.0f, 0.0f);
	assert(count == 0);
	drawing = 1;
	drawn = news_layout(text, 110.0f, 1, -1e9f, 1e9f);
	assert(measured == drawn && measured > 0.0f);
	for (int index = 0; index < count; index++)
		printf("%d %.0f %.0f %08X %s\n", calls[index].kind, calls[index].x, calls[index].y, calls[index].color,
			calls[index].text);
	/* a line kinds' check, the same lines the Java one judges */
	{
		const char *line = text;
		int first = 1;
		FILE *kinds = fopen(argv[2], "wb");
		assert(kinds);
		while (line && *line)
		{
			const char *end = strchr(line, '\n');
			size_t length = end ? (size_t)(end - line) : strlen(line);
			enum news_line kind = news_line_kind(line, length, first);
			fprintf(kinds, "%d\n", (int)kind);
			if (kind != NEWS_GAP)
				first = 0;
			line = end ? end + 1 : NULL;
		}
		fclose(kinds);
	}
	return 0;
}
'''
source = OUT / 'news.c'
source.write_text(harness, encoding='utf-8')
binary = OUT / 'news'
subprocess.run(['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                '-fsanitize=address,undefined', '-fno-sanitize-recover=all', str(source), '-o', str(binary)], check=True)
notes_path = ROOT / 'port/android/app/src/main/assets/whats_new.txt'
c_kinds_path = OUT / 'c_kinds.txt'
drawn = subprocess.run([str(binary), str(notes_path), str(c_kinds_path)], check=True, capture_output=True,
                       text=True, encoding='utf-8').stdout.splitlines()
COLOR = {m.group(1): int(m.group(2), 16) for m in re.finditer(r'#define COLOR_([A-Z]+) 0x([0-9A-F]+)u', colors)}
records = []
for row in drawn:
    kind, x, y, color, text = row.split(' ', 4)
    records.append((int(kind), float(x), float(y), int(color, 16), text))
texts = [r for r in records if r[0] == 0]
bullets = [r for r in records if r[0] == 1]
non_empty = [l for l in lines if l.strip()]
assert len(texts) == len(non_empty), (len(texts), len(non_empty))
assert len(bullets) == len(points)
ys = [r[2] for r in records]
assert ys == sorted(ys)
for record, line in zip(texts, non_empty):
    if line.startswith('\u2022 '):
        assert record[4] == line[2:] and record[1] == 108.0 and record[3] == COLOR['TEXT'], (record, line)
    elif line == lines[0]:
        assert record[4] == line and record[1] == 80.0 and record[3] == COLOR['TEXT']
    elif line in headings:
        assert record[4] == line and record[1] == 80.0 and record[3] == COLOR['BLUE'], (record, line)
    else:
        assert record[4] == line and record[1] == 80.0 and record[3] == COLOR['DIM'], (record, line)
for bullet in bullets:
    assert bullet[4] == '\u2022' and bullet[1] == 86.0 and bullet[3] == COLOR['BLUE']
# each bullet on its point's first line
point_records = [r for r, l in zip(texts, non_empty) if l.startswith('\u2022 ')]
assert [b[2] for b in bullets] == [p[2] for p in point_records]
# page_news lays the notes out with it, measured then drawn in the clip
page = launcher[launcher.index('static void page_news(void)'):]
page = page[:page.index('\n}\n')]
assert 'height = news_layout(text, 0.0f, 0, 0.0f, 0.0f);' in page
assert 'news_layout(text, 110.0f - ui.scroll, 1, 100.0f, (float)(LAUNCHER_HEIGHT - 110));' in page
assert 'text_wrapped' not in page
print('PASS: the PC launcher lays What\'s New out by its lines: %d drawn (%d headings, %d points with their bullets), '
      'the measured height the drawn one' % (len(texts), len(headings), len(points)))

# ---------- the Android launcher: compiled against android.jar, and its kinds the PC's
sdk = Path(os.environ.get('ANDROID_HOME', str(Path.home() / 'Android/Sdk')))
android_jar = sorted((sdk / 'platforms').glob('android-*/android.jar'))
assert android_jar, 'android.jar (the Android SDK) is needed'
with tempfile.TemporaryDirectory(prefix='test73-whats-new-') as folder:
    folder = Path(folder)
    package = folder / 'src/com/halo/decomp'
    package.mkdir(parents=True)
    (package / 'WhatsNew.java').write_text(java, encoding='utf-8')
    (package / 'BuildConfig.java').write_text(
        'package com.halo.decomp;\nfinal class BuildConfig { static final int VERSION_CODE = 86; '
        'static final String VERSION_NAME = "1.0.41-test73b"; }\n', encoding='utf-8')
    (package / 'UpdatePolicy.java').write_text(
        'package com.halo.decomp;\nfinal class UpdatePolicy { static final String REPOSITORY = '
        '"moistman42069/HaloCE-Quest-VR"; }\n', encoding='utf-8')
    (package / 'GamepadNavigation.java').write_text(
        'package com.halo.decomp;\nfinal class GamepadNavigation { static final class Builder extends '
        'android.app.AlertDialog.Builder { Builder(android.content.Context c) { super(c); } } }\n', encoding='utf-8')
    classes = folder / 'classes'
    classes.mkdir()
    subprocess.run(['javac', '-encoding', 'UTF-8', '-Xlint:all', '-Werror', '-Xlint:-options', '--release', '11',
                    '-cp', str(android_jar[-1]), '-d', str(classes)] + [str(p) for p in package.glob('*.java')],
                   check=True)
    # kind() alone, from its source, run on the JVM (android.jar's classes are stubs that cannot run)
    body = java[java.index('    static final int GAP = 0'):java.index('    /** The notes styled')]
    pure = folder / 'pure/com/halo/decomp'
    pure.mkdir(parents=True)
    (pure / 'Kinds.java').write_text(
        'package com.halo.decomp;\nimport java.nio.file.*;\nimport java.util.*;\npublic final class Kinds {\n' + body +
        '    public static void main(String[] a) throws Exception {\n'
        '        String notes = new String(Files.readAllBytes(Paths.get(a[0])), "UTF-8");\n'
        '        StringBuilder out = new StringBuilder();\n'
        '        boolean first = true;\n'
        '        String[] lines = notes.split("\\n", -1);\n'
        '        for (int i = 0; i < lines.length; i++) {\n'
        '            if (i == lines.length - 1 && lines[i].isEmpty()) break;\n'
        '            int k = kind(lines[i], first);\n'
        '            if (k != GAP) first = false;\n'
        '            out.append(k).append("\\n");\n'
        '        }\n'
        '        System.out.print(out);\n'
        '    }\n}\n', encoding='utf-8')
    pure_classes = folder / 'pure_classes'
    pure_classes.mkdir()
    subprocess.run(['javac', '-encoding', 'UTF-8', '-d', str(pure_classes), str(pure / 'Kinds.java')], check=True)
    java_kinds = subprocess.run(['java', '-cp', str(pure_classes), 'com.halo.decomp.Kinds', str(notes_path)],
                                check=True, capture_output=True, text=True).stdout.split()
c_kinds = c_kinds_path.read_text().split()
assert java_kinds == c_kinds, [(i, a, b) for i, (a, b) in enumerate(zip(java_kinds, c_kinds)) if a != b][:5]
# and lines the notes may come to have, judged by both as the rule says (a reference written here)
EDGES = ['', 'THE TITLE, WHATEVER IT SAYS', '', 'ONLY CAPS 1.0.37 (TEST73) + - : , . \' "', 'CAPS AND ONE z',
         'zzz', 'Mixed Case', '• a point', '•no space after the bullet', '• ', '   ', '\r',
         'CAPS ÉTÉ', 'caps été only accented', 'éé ONLY ACCENTED LOWER',
         'TRAILING SPACE   ', '- a dash', '1234', 'y', 'a']


def reference(line, first):
    trimmed = line.rstrip(' \r')
    return (0 if not trimmed else 1 if first else 3 if trimmed.startswith('• ') else
            4 if re.search('[a-z]', trimmed) else 2)


expected, first = [], True
for line in EDGES:
    expected.append(str(reference(line, first)))
    first = first and expected[-1] == '0'
edges_path = OUT / 'edges.txt'
edges_path.write_bytes(('\n'.join(EDGES) + '\n').encode('utf-8'))
c_edges = OUT / 'c_edges.txt'
subprocess.run([str(binary), str(edges_path), str(c_edges)], check=True, capture_output=True)
with tempfile.TemporaryDirectory(prefix='test73-whats-new-') as folder:
    folder = Path(folder)
    pure = folder / 'pure/com/halo/decomp'
    pure.mkdir(parents=True)
    body = java[java.index('    static final int GAP = 0'):java.index('    /** The notes styled')]
    (pure / 'Kinds.java').write_text(
        'package com.halo.decomp;\nimport java.nio.file.*;\npublic final class Kinds {\n' + body +
        '    public static void main(String[] a) throws Exception {\n'
        '        String[] lines = new String(Files.readAllBytes(Paths.get(a[0])), "UTF-8").split("\\n", -1);\n'
        '        boolean first = true;\n'
        '        for (int i = 0; i < lines.length - 1; i++) {\n'
        '            int k = kind(lines[i], first);\n'
        '            if (k != GAP) first = false;\n'
        '            System.out.println(k);\n'
        '        }\n'
        '    }\n}\n', encoding='utf-8')
    subprocess.run(['javac', '-encoding', 'UTF-8', '-d', str(folder), str(pure / 'Kinds.java')], check=True)
    java_edges = subprocess.run(['java', '-cp', str(folder), 'com.halo.decomp.Kinds', str(edges_path)], check=True,
                                capture_output=True, text=True).stdout.split()
c_edge_kinds = c_edges.read_text().split()
assert c_edge_kinds == expected, list(zip(EDGES, c_edge_kinds, expected))
assert java_edges == expected, list(zip(EDGES, java_edges, expected))
assert java_kinds[0] == '1' and java_kinds.count('2') == len(headings) and java_kinds.count('3') == len(points)
assert 'NEWS_GAP, NEWS_TITLE, NEWS_HEADING, NEWS_POINT, NEWS_TEXT' in launcher and \
    'GAP = 0, TITLE = 1, HEADING = 2, POINT = 3, TEXT = 4' in java
# the popup uses the styled notes
show = java[java.index('    static void show(Activity activity) {'):]
assert 'text.setText(styled(text(activity), (int) Math.ceil(text.getPaint().measureText("\\u2022 "))));' in show
assert 'new LeadingMarginSpan.Standard(0, bulletWidth), start, end, Spanned.SPAN_PARAGRAPH' in java
print('PASS: the Android launcher\'s WhatsNew.java compiles against %s and judges every one of the %d lines as the PC '
      'launcher does' % (android_jar[-1].parent.name, len(java_kinds)))
