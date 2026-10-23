"""Test73, item 9: the PC launcher's saves and its Safe/Normal geometry choice (docs/HANDOFF-2026-10-18.md item 9).

The desktop launcher's GAME DATA page brings saves in from a .zip or a folder and takes them out as a .zip
(save_transfer.c, Test72's, wired here: JOB_SAVES_IMPORT_ZIP / _FOLDER / JOB_SAVES_EXPORT, the saves already there
kept first in the save root's backups folder). SETTINGS has GEOMETRY: SAFE / NORMAL (renderer.safe_geometry), as
the Android launcher's Geometry compatibility, whose text now says Safe is the default on every build.

Compiled and run here (clang, AddressSanitizer) over a small POSIX stand-in for the SDL calls it makes and the port's
own prefixed zlib: save_transfer_destination against the Android launcher's own case table (test_test72_saves.py's,
SaveTransfer.java's plan); an export read back by Python's zipfile (every CRC checked); an import over saves already
there (same names replaced, others kept, the old ones in the backup, the staging folder gone, caches never taken); a
.zip with nothing in it (nothing changed, no backup); a hostile name (nothing written outside); a deflated .zip; a
folder; and a .zip the Android launcher itself writes (SaveTransfer.exportSaves, javac: deflated entries with data
descriptors) brought in by the PC's.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_desktop_saves'
launcher = (ROOT / 'port/linux/src/desktop_launcher.c').read_text(encoding='utf-8')
transfer = (ROOT / 'port/linux/src/save_transfer.c').read_text(encoding='utf-8')
help_text = (ROOT / 'port/android/app/src/main/java/com/halo/decomp/LauncherHelp.java').read_text(encoding='utf-8')
java_test = (ROOT / 'tools/test_test72_saves.py').read_text(encoding='utf-8')
JAVA = ROOT / 'port/android/app/src/main/java/com/halo/decomp'

# ---------- the launcher's wiring
assert '#include "save_transfer.h"' in launcher
for kind in ('JOB_SAVES_IMPORT_ZIP', 'JOB_SAVES_IMPORT_FOLDER', 'JOB_SAVES_EXPORT'):
    assert launcher.count(kind) >= 3, kind
assert ('\tcase JOB_SAVES_IMPORT_ZIP:\n\tcase JOB_SAVES_IMPORT_FOLDER:\n'
        '\tcase JOB_SAVES_EXPORT: ok = job_saves(job.kind, job.path, result, sizeof(result)); break;') in launcher
assert 'path_join(backups, sizeof(backups), save_root, "backups");' in launcher
assert ('return save_transfer_import(path, kind == JOB_SAVES_IMPORT_FOLDER, save_root, backups, result, size);'
        in launcher)
assert 'return save_transfer_export(save_root, zip, result, size) >= 0;' in launcher
assert 'lower_equals(path + length - 4, ".zip") ? "" : ".zip"' in launcher
assert 'SDL_ShowSaveFileDialog(dialog_answer, NULL, ui.window, filters, 1, NULL);' in launcher
page = launcher[launcher.index('static void page_data(void)'):launcher.index('static void page_mods(void)')]
for needle in ('"IMPORT SAVES (.ZIP)", !job.running))\n\t\tdialog_zip(JOB_SAVES_IMPORT_ZIP, 0);',
               '"IMPORT SAVES (FOLDER)", !job.running))\n\t\tdialog_folder(JOB_SAVES_IMPORT_FOLDER);',
               '"EXPORT SAVES (.ZIP)", !job.running))\n\t\tdialog_zip(JOB_SAVES_EXPORT, 1);',
               'platform_save_root()'):
    assert needle in page, needle
# (the buttons above the BACK row and the result line: 540 + 56 < the busy bar at 630)
assert re.findall(r'button\(\d+\.0f, (\d+)\.0f, \d+\.0f, 56\.0f, "(?:IMPORT|EXPORT) SAVES', page) == ['540'] * 3
# the geometry choice, with Safe first (the default) and the text that says so
assert '{ "GEOMETRY", "renderer.safe_geometry", 2, { "true", "false" }, { "SAFE", "NORMAL" } },' in launcher
assert '"GEOMETRY: Safe is the default on every build (PC, PC VR, Quest VR, Android).' in launcher
settings = launcher[launcher.index('static const struct launcher_setting launcher_settings[] ='):]
settings = settings[:settings.index('};')]
assert settings.index('"renderer.safe_geometry"') < settings.index('#ifdef HALO_VR')  # (both PC builds)


def rows_without(block_start):
    """the rows a build has: those outside the other build's #if block"""
    text = settings
    while block_start in text:
        start = text.index(block_start)
        text = text[:start] + text[text.index('#endif', start) + len('#endif'):]
    return len(re.findall(r'^\t\{ "', text, re.M))


for build, rows in (('flat', rows_without('#ifdef HALO_VR')), ('vr', rows_without('#ifndef HALO_VR'))):
    assert 110 + 58 * (rows - 1) + 50 < 800 - 90, (build, rows)  # (the last row above BACK)
assert ('Safe geometry is the default on every build: Quest VR, flat Android, and the PC (flat and VR), including '
        'the first upgrade to this default.') in help_text
assert 'default for Quest VR and flat Android' not in help_text

# ---------- compiled: save_transfer.c over POSIX
SHIM = r'''
#ifndef SDL_SHIM_H
#define SDL_SHIM_H
#include <dirent.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#define SDLCALL
typedef int64_t Sint64;
typedef uint64_t Uint64;
typedef int64_t SDL_Time;
typedef enum { SDL_PATHTYPE_NONE, SDL_PATHTYPE_FILE, SDL_PATHTYPE_DIRECTORY, SDL_PATHTYPE_OTHER } SDL_PathType;
typedef struct { SDL_PathType type; Uint64 size; SDL_Time create_time, modify_time, access_time; } SDL_PathInfo;
typedef enum { SDL_ENUM_CONTINUE, SDL_ENUM_SUCCESS, SDL_ENUM_FAILURE } SDL_EnumerationResult;
typedef SDL_EnumerationResult (*SDL_EnumerateDirectoryCallback)(void *userdata, const char *dirname, const char *fname);
typedef enum { SDL_IO_SEEK_SET, SDL_IO_SEEK_CUR, SDL_IO_SEEK_END } SDL_IOWhence;
typedef struct SDL_IOStream { FILE *file; const unsigned char *memory; size_t size, at; } SDL_IOStream;
typedef struct { int year, month, day, hour, minute, second, nanosecond, day_of_week, utc_offset; } SDL_DateTime;
static char shim_error[256];
static void shim_fail(void) { snprintf(shim_error, sizeof(shim_error), "%s", strerror(errno)); }
static const char *SDL_GetError(void) { return shim_error; }
static SDL_IOStream *SDL_IOFromFile(const char *path, const char *mode)
{
	SDL_IOStream *io = calloc(1, sizeof(*io));
	if (!io || !(io->file = fopen(path, mode))) { shim_fail(); free(io); return NULL; }
	return io;
}
static SDL_IOStream *SDL_IOFromConstMem(const void *memory, size_t size)
{
	SDL_IOStream *io = calloc(1, sizeof(*io));
	if (io) { io->memory = memory; io->size = size; }
	return io;
}
static size_t SDL_ReadIO(SDL_IOStream *io, void *out, size_t size)
{
	if (io->file) return fread(out, 1, size, io->file);
	if (size > io->size - io->at) size = io->size - io->at;
	memcpy(out, io->memory + io->at, size);
	io->at += size;
	return size;
}
static size_t SDL_WriteIO(SDL_IOStream *io, const void *data, size_t size)
{
	size_t written = io->file ? fwrite(data, 1, size, io->file) : 0;
	if (written != size) shim_fail();
	return written;
}
static Sint64 SDL_SeekIO(SDL_IOStream *io, Sint64 offset, SDL_IOWhence whence)
{
	if (io->file)
	{
		if (fseeko(io->file, offset, whence == SDL_IO_SEEK_SET ? SEEK_SET : whence == SDL_IO_SEEK_CUR ? SEEK_CUR : SEEK_END))
			return -1;
		return ftello(io->file);
	}
	{
		Sint64 at = (whence == SDL_IO_SEEK_SET ? 0 : whence == SDL_IO_SEEK_CUR ? (Sint64)io->at : (Sint64)io->size) + offset;
		if (at < 0 || at > (Sint64)io->size) return -1;
		io->at = (size_t)at;
		return at;
	}
}
static Sint64 SDL_GetIOSize(SDL_IOStream *io)
{
	struct stat information;
	if (!io->file) return (Sint64)io->size;
	return fstat(fileno(io->file), &information) ? -1 : (Sint64)information.st_size;
}
static bool SDL_CloseIO(SDL_IOStream *io)
{
	int ok = 1;
	if (!io) return false;
	if (io->file) ok = fclose(io->file) == 0;
	free(io);
	return ok;
}
static void *SDL_LoadFile(const char *path, size_t *size)
{
	SDL_IOStream *io = SDL_IOFromFile(path, "rb");
	Sint64 length;
	unsigned char *data;
	if (!io) return NULL;
	length = SDL_GetIOSize(io);
	data = length >= 0 ? malloc((size_t)length + 1) : NULL;
	if (!data || SDL_ReadIO(io, data, (size_t)length) != (size_t)length) { free(data); SDL_CloseIO(io); return NULL; }
	data[length] = 0;
	SDL_CloseIO(io);
	*size = (size_t)length;
	return data;
}
static void SDL_free(void *memory) { free(memory); }
static bool SDL_GetPathInfo(const char *path, SDL_PathInfo *info)
{
	struct stat information;
	if (stat(path, &information)) { shim_fail(); return false; }
	if (info)
	{
		memset(info, 0, sizeof(*info));
		info->type = S_ISDIR(information.st_mode) ? SDL_PATHTYPE_DIRECTORY : S_ISREG(information.st_mode) ?
			SDL_PATHTYPE_FILE : SDL_PATHTYPE_OTHER;
		info->size = (Uint64)information.st_size;
	}
	return true;
}
static bool SDL_CreateDirectory(const char *path)
{
	char partial[1024];
	size_t index;
	struct stat information;
	snprintf(partial, sizeof(partial), "%s", path);
	for (index = 1; partial[index]; index++)
	{
		if (partial[index] == '/')
		{
			partial[index] = 0;
			if (stat(partial, &information)) mkdir(partial, 0777);
			partial[index] = '/';
		}
	}
	if (!stat(partial, &information)) { if (S_ISDIR(information.st_mode)) return true; errno = EEXIST; shim_fail(); return false; }
	if (mkdir(partial, 0777)) { shim_fail(); return false; }
	return true;
}
static bool SDL_EnumerateDirectory(const char *path, SDL_EnumerateDirectoryCallback callback, void *userdata)
{
	DIR *folder = opendir(path);
	struct dirent *entry;
	char dirname[1024];
	bool ok = true;
	if (!folder) { shim_fail(); return false; }
	/* (as SDL: the folder with its separator) */
	snprintf(dirname, sizeof(dirname), "%s%s", path, path[strlen(path) - 1] == '/' ? "" : "/");
	while ((entry = readdir(folder)))
	{
		SDL_EnumerationResult result;
		if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
		result = callback(userdata, dirname, entry->d_name);
		if (result == SDL_ENUM_FAILURE) { ok = false; break; }
		if (result == SDL_ENUM_SUCCESS) break;
	}
	closedir(folder);
	return ok;
}
static bool SDL_RemovePath(const char *path) { if (remove(path)) { shim_fail(); return false; } return true; }
static bool SDL_RenamePath(const char *from, const char *to) { if (rename(from, to)) { shim_fail(); return false; } return true; }
static int SDL_strcasecmp(const char *a, const char *b) { return strcasecmp(a, b); }
static int SDL_strncasecmp(const char *a, const char *b, size_t length) { return strncasecmp(a, b, length); }
static bool SDL_GetCurrentTime(SDL_Time *now)
{
	struct timespec clock;
	clock_gettime(CLOCK_REALTIME, &clock);
	*now = (SDL_Time)clock.tv_sec * 1000000000LL + clock.tv_nsec;
	return true;
}
static bool SDL_TimeToDateTime(SDL_Time ticks, SDL_DateTime *date, bool local)
{
	time_t seconds = (time_t)(ticks / 1000000000LL);
	struct tm parts;
	if (!(local ? localtime_r(&seconds, &parts) : gmtime_r(&seconds, &parts))) return false;
	date->year = parts.tm_year + 1900; date->month = parts.tm_mon + 1; date->day = parts.tm_mday;
	date->hour = parts.tm_hour; date->minute = parts.tm_min; date->second = parts.tm_sec;
	return true;
}
#endif
'''

HARNESS = r'''
#include <stdio.h>
#include <string.h>
#include "save_transfer.h"

/* save_transfer_destination for each line of standard input; then, with arguments, an action */
int main(int argc, char **argv)
{
	char line[1100], out[1100], result[2048];

	if (argc == 1)
	{
		while (fgets(line, sizeof(line), stdin))
		{
			line[strcspn(line, "\n")] = 0;
			printf("%s\n", save_transfer_destination(line, out, sizeof(out)) ? out : "(none)");
		}
		return 0;
	}
	if (!strcmp(argv[1], "export"))
	{
		int files = save_transfer_export(argv[2], argv[3], result, sizeof(result));
		printf("%d %s\n", files, result);
		return files < 0;
	}
	if (!strcmp(argv[1], "import-zip") || !strcmp(argv[1], "import-folder"))
	{
		int ok = save_transfer_import(argv[2], !strcmp(argv[1], "import-folder"), argv[3], argv[4], result, sizeof(result));
		printf("%d %s\n", ok, result);
		return 0;
	}
	return 2;
}
'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'shim/SDL3').mkdir(parents=True, exist_ok=True)
(OUT / 'shim/SDL3/SDL.h').write_text(SHIM, encoding='utf-8')
(OUT / 'harness.c').write_text(HARNESS, encoding='utf-8')
zlib = ROOT / 'port/third_party/zlib'
objects = []
for name in ('adler32', 'crc32', 'inffast', 'inflate', 'inftrees', 'zutil'):
    obj = OUT / (name + '.o')
    subprocess.run(['clang', '-O1', '-g', '-w', '-DZ_PREFIX', '-fsanitize=address,undefined', '-c', str(zlib / (name + '.c')),
                    '-o', str(obj)], check=True)
    objects.append(str(obj))
BINARY = OUT / 'save_transfer'
subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-function',
                '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-DZ_PREFIX',
                '-I' + str(OUT / 'shim'), '-I' + str(zlib), '-I' + str(ROOT / 'port/linux/src'),
                str(ROOT / 'port/linux/src/save_transfer.c'), str(OUT / 'harness.c'), *objects, '-o', str(BINARY)],
               check=True)


def harness(*arguments, stdin=None):
    result = subprocess.run([str(BINARY), *map(str, arguments)], capture_output=True, text=True, input=stdin)
    assert result.returncode in (0, 1), result.stderr
    return result.stdout.strip()


# the Android launcher's plan, case for case (test_test72_saves.py's table, SaveTransfer.java's answers)
cases = []
table = java_test[java_test.index('String[][] cases = {'):java_test.index('};', java_test.index('String[][] cases = {'))]
for path, wanted in re.findall(r'\{"((?:[^"\\]|\\.)*)", (?:"((?:[^"\\]|\\.)*)"|null)\}', table):
    cases.append((path.replace('\\\\', '\\'), wanted.replace('\\\\', '\\') if wanted else None))
assert len(cases) == 16, len(cases)
cases += [('C:\\Users\\me\\Saved\\player_profiles\\P\\00.sav', 'z/saved/player_profiles/P/00.sav'),
          ('backup/saved/maps/x.bin', None), ('a/b<c/saved/x.sav', None), ('udata', None)]
answers = harness(stdin=''.join(path + '\n' for path, _ in cases)).splitlines()
for (path, wanted), got in zip(cases, answers):
    assert got == (wanted or '(none)'), (path, got, wanted)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


with tempfile.TemporaryDirectory() as temporary:
    base = Path(temporary)
    # a PC's saves, exported
    a = base / 'a'
    write(a / 'z/saved/player_profiles/Chief/00.sav', 'chief0')
    write(a / 'z/saved/player_profiles/Chief/01.sav', 'chief1')
    write(a / 'z/savegame.bin', 'checkpoint')
    write(a / 'z/cache001.map', 'cache')
    write(a / 'u/UDATA/4d530004/S1/SaveMeta.xbx', 'meta')
    write(a / 'backups/saves-old.zip', 'not a save')
    line = harness('export', a, base / 'export.zip')
    assert line.startswith('4 4 save files exported'), line
    with zipfile.ZipFile(base / 'export.zip') as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == ['save/u/UDATA/4d530004/S1/SaveMeta.xbx', 'save/z/saved/player_profiles/Chief/00.sav',
                                              'save/z/saved/player_profiles/Chief/01.sav', 'save/z/savegame.bin'], archive.namelist()
        assert archive.read('save/z/savegame.bin') == b'checkpoint'
    # another PC's, with a profile of its own and one of the same name
    b = base / 'b'
    write(b / 'z/saved/player_profiles/Chief/00.sav', 'old')
    write(b / 'z/saved/player_profiles/Arbiter/00.sav', 'arbiter')
    backups = b / 'backups'
    line = harness('import-zip', base / 'export.zip', b, backups)
    assert line.startswith('1 4 save files brought in (profiles: Chief), the campaign checkpoint. Your saves before this are in '), line
    assert (b / 'z/saved/player_profiles/Chief/00.sav').read_text() == 'chief0'
    assert (b / 'z/saved/player_profiles/Arbiter/00.sav').read_text() == 'arbiter'
    assert (b / 'u/UDATA/4d530004/S1/SaveMeta.xbx').read_text() == 'meta'
    assert not (b / 'z/cache001.map').exists() and not (b / 'import.tmp').exists()
    made = sorted(backups.glob('saves-*.zip'))
    assert len(made) == 1
    with zipfile.ZipFile(made[0]) as archive:
        assert archive.read('save/z/saved/player_profiles/Chief/00.sav') == b'old'
        assert 'save/z/saved/player_profiles/Arbiter/00.sav' in archive.namelist()
    # nothing in it: nothing changed, no backup
    with zipfile.ZipFile(base / 'junk.zip', 'w') as archive:
        archive.writestr('readme.txt', 'x')
    before = sorted(p.name for p in backups.iterdir())
    line = harness('import-zip', base / 'junk.zip', b, backups)
    assert line.startswith('0 Saves not changed: no saves found in it'), line
    assert sorted(p.name for p in backups.iterdir()) == before
    # a hostile name: nothing outside
    with zipfile.ZipFile(base / 'evil.zip', 'w') as archive:
        archive.writestr('saved/../../../x.sav', 'x')
    line = harness('import-zip', base / 'evil.zip', b, backups)
    assert line.startswith('0 '), line
    assert not (base / 'x.sav').exists() and not (b / 'x.sav').exists() and not (b.parent.parent / 'x.sav').exists()
    # deflated, from another tool, with folders
    with zipfile.ZipFile(base / 'deflated.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('Halo backup/saved/', '')
        archive.writestr('Halo backup/saved/player_profiles/Deflated/00.sav', 'deflated ' * 400)
        archive.writestr('Halo backup/saved/playlists/default/00/blam.lst', 'list')
    line = harness('import-zip', base / 'deflated.zip', b, backups)
    assert line.startswith('1 2 save files brought in (profiles: Deflated)'), line
    assert (b / 'z/saved/player_profiles/Deflated/00.sav').read_text() == 'deflated ' * 400
    # a damaged one: its checksum
    damaged = bytearray((base / 'export.zip').read_bytes())
    at = damaged.index(b'checkpoint')
    damaged[at] ^= 0x20
    (base / 'damaged.zip').write_bytes(bytes(damaged))
    line = harness('import-zip', base / 'damaged.zip', b, backups)
    assert line.startswith("0 Saves not changed: an entry's checksum is wrong"), line
    # a folder (a copy of another device's save folder)
    write(base / 'folder/Halo/player_profiles/Folder/00.sav', 'folder')
    write(base / 'folder/Halo/notes.txt', 'x')
    line = harness('import-folder', base / 'folder', b, backups)
    assert line.startswith('1 1 save file brought in (profiles: Folder); other files left out'), line
    assert (b / 'z/saved/player_profiles/Folder/00.sav').read_text() == 'folder'
    # the Android launcher's own export (Java's ZipOutputStream: deflated, data descriptors), brought in on the PC
    work = base / 'java'
    package = work / 'src/com/halo/decomp'
    package.mkdir(parents=True)
    shutil.copy(JAVA / 'SaveTransfer.java', package / 'SaveTransfer.java')
    (package / 'SaveExport.java').write_text(r'''
package com.halo.decomp;
import java.io.*;
public class SaveExport {
    public static void main(String[] args) throws Exception {
        try (OutputStream out = new FileOutputStream(args[1])) { System.out.println(SaveTransfer.exportSaves(new File(args[0]), out)); }
    }
}
''', encoding='utf-8')
    write(base / 'quest/z/saved/player_profiles/Quest/00.sav', 'from the quest ' * 50)
    write(base / 'quest/z/savegame.bin', 'quest checkpoint')
    subprocess.run(['javac', '-d', str(work / 'out'), str(package / 'SaveTransfer.java'), str(package / 'SaveExport.java')],
                   check=True)
    exported = subprocess.run(['java', '-cp', str(work / 'out'), 'com.halo.decomp.SaveExport', str(base / 'quest'),
                               str(base / 'quest.zip')], check=True, capture_output=True, text=True).stdout.strip()
    assert exported == '2', exported
    with zipfile.ZipFile(base / 'quest.zip') as archive:
        assert any(info.flag_bits & 8 for info in archive.infolist()), 'data descriptors expected from ZipOutputStream'
        assert all(info.compress_type == zipfile.ZIP_DEFLATED for info in archive.infolist())
    line = harness('import-zip', base / 'quest.zip', b, backups)
    assert line.startswith('1 2 save files brought in (profiles: Quest), the campaign checkpoint'), line
    assert (b / 'z/saved/player_profiles/Quest/00.sav').read_text() == 'from the quest ' * 50
    assert (b / 'z/savegame.bin').read_text() == 'quest checkpoint'
    # an export with no saves: none written
    (base / 'empty').mkdir()
    line = harness('export', base / 'empty', base / 'none.zip')
    assert line.startswith('0 There are no saves yet in') and not (base / 'none.zip').exists(), line

print('PASS: Test73 PC launcher saves: %d destinations as the Android launcher plans them; export read back, import over '
      'saves (backup first, same names replaced, others kept), nothing-in-it, hostile name, deflated, damaged, folder, '
      'and the Android launcher\'s own .zip; GEOMETRY SAFE/NORMAL in both PC launchers, Safe the default everywhere'
      % len(cases))
