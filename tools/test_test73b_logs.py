"""Test73b: where the logs are, said by every launcher (the owner: "where are logs generating for steam and pc? these
things should be clarified" / "do that for all launchers i guess. useful for log finding").

- Windows: halo.log (halo-vr.log for PC VR) beside the game was replaced at every start, so the run before (a crash,
  then the game started again) was lost. Each start now keeps it first in logs\\ beside the game as
  <stem>_<date>_<time>.log (when that run last wrote), the newest ten of each build's kept (win32_posix.c's
  log_keep_previous; a copy, as the run before may still have it open). Run here with the Windows clang (from WSL
  too), the production function, 3 negative controls.
- The PC launcher: a LOGS page (the files, what is in each, each folder opened in a press).
- The Steam Frame: its logs folder kept every run's; now its newest ten, never this run's (RunLog.pruneFolder, run
  here with javac, a negative control). The Android launcher says the Frame's folder there (Lepton), the Quest's
  elsewhere; the note in the Frame's data folder, the bundle's README and the installer's last dialog name them.
- The in-game guide, the READMEs and the player guide name every device's.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

from harness import function, mutated

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8')
posix = read('port/windows/src/win32_posix.c')
desktop = read('port/linux/src/desktop_launcher.c')
runlog = read('port/android/app/src/main/java/com/halo/decomp/RunLog.java')
launcher = read('port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java')
guide = read('port/android/app/src/main/java/com/halo/decomp/InGameNetworkGuide.java')
bundle = read('tools/steam_frame/bundle.py')
install = read('tools/steam_frame/install.sh')
readme = read('README.md')
player_guide = read('docs/PLAYER-GUIDE.md')
windows_readme = read('port/windows/README.md')
for text in (posix, desktop, runlog, launcher, guide, bundle, install):
    assert '\r' not in text


def between(text, start, end):
    return text[text.index(start):text.index(end, text.index(start))]


# ---------- Windows: the last run's log kept, the newest ten of each build's
startup = function(posix, 'windows_startup')
assert startup.index('strcpy(slash + 1, name);') < startup.index('log_keep_previous(path, (size_t)(slash + 1 - path));') \
    < startup.index('if (freopen(path, "w", stderr))')
assert startup.index('if (_fileno(stderr) < 0)') < startup.index('log_keep_previous(')  # (not when stderr goes elsewhere)
assert 'static const char name[] = "halo-vr.log";' in startup and 'static const char name[] = "halo.log";' in startup
KEEP = '#define LOGS_KEPT 10\n\n' + function(posix, 'compare_log_names') + '\n\n' + function(posix, 'log_keep_previous') + '\n'

PROGRAM = r'''
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "keep.inc"

static char folder[MAX_PATH];
#define CHECK(c, what) do { if (!(c)) { printf("FAIL %s\n", what); return 1; } } while (0)

static void path_of(char *out, const char *name) { snprintf(out, MAX_PATH, "%s%s", folder, name); }
static int exists(const char *name)
{
    char path[MAX_PATH];
    path_of(path, name);
    return GetFileAttributesA(path) != INVALID_FILE_ATTRIBUTES;
}
/* a file of the folder's written whole, its time when it last wrote set (local time) */
static int write_file(const char *name, const char *text, int year, int month, int day, int hour, int minute,
    int second, int milliseconds)
{
    char path[MAX_PATH];
    SYSTEMTIME time = { (WORD)year, (WORD)month, 0, (WORD)day, (WORD)hour, (WORD)minute, (WORD)second,
        (WORD)milliseconds };
    FILETIME local, utc;
    DWORD put;
    HANDLE file;
    int ok;

    path_of(path, name);
    file = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE)
        return 0;
    ok = WriteFile(file, text, (DWORD)strlen(text), &put, NULL) && put == strlen(text);
    if (year && SystemTimeToFileTime(&time, &local) && LocalFileTimeToFileTime(&local, &utc))
        ok = ok && SetFileTime(file, NULL, NULL, &utc);
    return CloseHandle(file) && ok;
}
static int same_text(const char *name, const char *text)
{
    char path[MAX_PATH], buffer[256];
    DWORD got = 0;
    HANDLE file;

    path_of(path, name);
    file = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE)
        return 0;
    ReadFile(file, buffer, sizeof(buffer) - 1, &got, NULL);
    CloseHandle(file);
    buffer[got] = 0;
    return !strcmp(buffer, text);
}
static long long write_time(const char *name)
{
    char path[MAX_PATH];
    WIN32_FILE_ATTRIBUTE_DATA data;

    path_of(path, name);
    if (!GetFileAttributesExA(path, GetFileExInfoStandard, &data))
        return -1;
    return ((long long)data.ftLastWriteTime.dwHighDateTime << 32) | data.ftLastWriteTime.dwLowDateTime;
}
static int count(const char *pattern)
{
    char path[MAX_PATH];
    WIN32_FIND_DATAA found;
    HANDLE search;
    int total = 0;

    path_of(path, pattern);
    search = FindFirstFileA(path, &found);
    if (search == INVALID_HANDLE_VALUE)
        return 0;
    do total++; while (FindNextFileA(search, &found));
    FindClose(search);
    return total;
}

int main(int argc, char **argv)
{
    char log[MAX_PATH], vr[MAX_PATH], name[MAX_PATH], expected[MAX_PATH];
    size_t directory;
    int index;
    HANDLE open;
    DWORD put;
    WIN32_FILE_ATTRIBUTE_DATA data;
    FILETIME local;
    SYSTEMTIME time;

    if (argc != 2)
        return 2;
    snprintf(folder, sizeof(folder), "%s\\", argv[1]);
    directory = strlen(folder);
    path_of(log, "halo.log");
    path_of(vr, "halo-vr.log");

    /* an empty log (a run that wrote nothing): nothing kept, no folder made */
    CHECK(write_file("halo.log", "", 0, 0, 0, 0, 0, 0, 0), "write");
    log_keep_previous(log, directory);
    CHECK(!exists("logs"), "an empty log kept");

    /* the last run's: copied, named by when it last wrote, the time kept */
    CHECK(write_file("halo.log", "run one\n", 2026, 10, 22, 21, 3, 15, 123), "write");
    log_keep_previous(log, directory);
    CHECK(same_text("logs\\halo_2026-10-22_21-03-15-123.log", "run one\n"), "the last run's kept, by its time");
    CHECK(write_time("logs\\halo_2026-10-22_21-03-15-123.log") == write_time("halo.log"), "its time kept");
    CHECK(same_text("halo.log", "run one\n"), "the log itself left (freopen empties it)");
    /* the same run's again (a start that ended before it wrote): kept once */
    log_keep_previous(log, directory);
    CHECK(count("logs\\halo_*.log") == 1, "the same run's kept twice");

    /* the newest ten of this build's kept; PC VR's and other files untouched */
    for (index = 0; index < 12; index++)
    {
        snprintf(name, sizeof(name), "logs\\halo_2020-01-01_00-00-%02d-000.log", index);
        CHECK(write_file(name, "old\n", 2020, 1, 1, 0, 0, index, 0), "write");
    }
    for (index = 0; index < 3; index++)
    {
        snprintf(name, sizeof(name), "logs\\halo-vr_2020-01-01_00-00-%02d-000.log", index);
        CHECK(write_file(name, "old vr\n", 2020, 1, 1, 0, 0, index, 0), "write");
    }
    CHECK(write_file("logs\\halo_notes.log", "mine\n", 0, 0, 0, 0, 0, 0, 0), "write");
    CHECK(write_file("logs\\readme.txt", "mine\n", 0, 0, 0, 0, 0, 0, 0), "write");
    CHECK(write_file("halo.log", "run two\n", 2026, 10, 22, 21, 4, 0, 0), "write");
    log_keep_previous(log, directory);
    for (index = 0; index < 12; index++)
    {
        snprintf(name, sizeof(name), "logs\\halo_2020-01-01_00-00-%02d-000.log", index);
        CHECK(exists(name) == (index >= 4), "the oldest beyond ten deleted, the rest kept");
    }
    CHECK(exists("logs\\halo_2026-10-22_21-03-15-123.log") && same_text("logs\\halo_2026-10-22_21-04-00-000.log",
        "run two\n"), "the newest kept");
    CHECK(count("logs\\halo-vr_*.log") == 3, "PC VR's touched by the screen build's");
    CHECK(exists("logs\\halo_notes.log") && exists("logs\\readme.txt"), "a file of another form touched");

    /* the log still open by the run before (the launcher starting this build anew): copied all the same */
    open = CreateFileA(log, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL, NULL);
    CHECK(open != INVALID_HANDLE_VALUE, "open");
    CHECK(WriteFile(open, "run three\n", 10, &put, NULL) && put == 10, "write");
    FlushFileBuffers(open);
    CHECK(GetFileAttributesExA(log, GetFileExInfoStandard, &data) && FileTimeToLocalFileTime(&data.ftLastWriteTime,
        &local) && FileTimeToSystemTime(&local, &time), "time");
    snprintf(expected, sizeof(expected), "logs\\halo_%04hu-%02hu-%02hu_%02hu-%02hu-%02hu-%03hu.log", time.wYear,
        time.wMonth, time.wDay, time.wHour, time.wMinute, time.wSecond, time.wMilliseconds);
    log_keep_previous(log, directory);
    CloseHandle(open);
    CHECK(same_text(expected, "run three\n"), "the log the run before has open kept");
    CHECK(count("logs\\halo_2*.log") == 10, "ten of the screen build's");

    /* PC VR's own, by its name */
    CHECK(write_file("halo-vr.log", "vr run\n", 2026, 10, 22, 21, 6, 0, 0), "write");
    log_keep_previous(vr, directory);
    CHECK(same_text("logs\\halo-vr_2026-10-22_21-06-00-000.log", "vr run\n"), "PC VR's kept by its own name");
    CHECK(count("logs\\halo-vr_*.log") == 4 && count("logs\\halo_2*.log") == 10, "each build's apart");
    printf("ok\n");
    return 0;
}
'''

if sys.platform == 'win32':
    WINDOWS_CLANG = shutil.which('clang') or 'C:/Program Files/LLVM/bin/clang.exe'
    windows_path = str
else:
    WINDOWS_CLANG = '/mnt/c/Program Files/LLVM/bin/clang.exe'
    windows_path = lambda path: subprocess.run(['wslpath', '-w', str(path)], check=True, capture_output=True,
                                               text=True).stdout.strip()
WORK = ROOT / 'build/test73b-logs'


def run_keep(keep):
    """the program built with the Windows clang (the game's target and flags) and run: (status, output)"""
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=WORK) as work:
        work = Path(work)
        (work / 'keep.inc').write_text(keep)
        (work / 'keep.c').write_text(PROGRAM)
        (work / 'folder').mkdir()
        build = subprocess.run([WINDOWS_CLANG, '--target=i686-pc-windows-msvc', '-std=gnu11', '-DWIN32_LEAN_AND_MEAN',
                                '-DNOMINMAX', '-D_WIN32_WINNT=0x0A00', '-D_USE_32BIT_TIME_T', '-D_CRT_SECURE_NO_WARNINGS',
                                '-D_CRT_NONSTDC_NO_WARNINGS', '-Wall', '-Werror', '-I', windows_path(work),
                                windows_path(work / 'keep.c'), '-o', windows_path(work / 'keep.exe')],
                               capture_output=True, text=True)
        assert build.returncode == 0, build.stdout + build.stderr
        result = subprocess.run([str(work / 'keep.exe'), windows_path(work / 'folder')], capture_output=True, text=True)
        return result.returncode, result.stdout


windows_ran = Path(WINDOWS_CLANG).exists() or (sys.platform == 'win32' and shutil.which('clang'))
if windows_ran:
    status, output = run_keep(KEEP)
    assert status == 0 and output.startswith('ok'), output
    for keep, what in [
            (mutated(KEEP, 'FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, OPEN_EXISTING',
                     'FILE_SHARE_READ | FILE_SHARE_DELETE, NULL, OPEN_EXISTING'), 'the open log not shared'),
            (mutated(KEEP, '\t\t(!data.nFileSizeHigh && !data.nFileSizeLow) ||\n', ''), 'an empty log kept'),
            (mutated(KEEP, '\t\t\tstrlen(found.cFileName) == (size_t)stem + sizeof("_YYYY-MM-DD_HH-MM-SS-mmm.log") - 1 &&\n',
                     ''), 'another file counted')]:
        status, output = run_keep(keep)
        assert status == 1 and output.startswith('FAIL'), (what, output)

# ---------- the PC launcher's LOGS page
# (CONTROLS, Test73b's other page, after it: tools/test_test73b_controls.py)
assert 'PAGE_UPDATES, PAGE_LOGS,\n\tPAGE_CONTROLS };' in desktop and 'case PAGE_LOGS: page_logs(); break;' in desktop
home = function(desktop, 'page_home')
assert 'if (button(460.0f, y, 360.0f, 56.0f, "LOGS", 1)) { ui.page = PAGE_LOGS; ui.focus = 0; }' in home
assert home.index('"QUIT"') < home.index('"LOGS"')  # (the buttons before it keep their focus order)
logs = function(desktop, 'page_logs')
for text in ('page_heading("LOGS");', '"halo.log and halo-vr.log"', 'halo_<date>_<time>.log and halo-vr_<date>_<time>.log',
             '"debug.txt"', 'debug.old.txt', '"OPEN THE GAME\'S FOLDER"', '"OPEN THE LOGS FOLDER"', '"OPEN THE DATA FOLDER"',
             'path_join(logs, sizeof(logs), game, "logs");', 'separate = !same_folder(data, game);',
             'HALO_PORT_VERSION', 'if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }'):
    assert text in logs, text
windows_part = between(logs, '#ifdef _WIN32\n\ttext_draw(&ui.body, 80.0f, y, "halo.log and halo-vr.log"', '#else')
linux_part = between(logs, '\ttext_draw(&ui.body, 80.0f, y, "The terminal"', '#endif')
assert 'halo-vr.log' not in linux_part and './halo 2> halo.log' in linux_part and 'logs' in windows_part
assert 'If the headset does not start, halo-vr.log beside the game says why (LOGS, on the first page, opens its "' \
    in desktop
whole = function(desktop, 'folder_whole')
assert 'SDL_GetCurrentDirectory()' in whole and 'SDL_free(current);' in whole
assert 'return lower_equals(x, y);' in function(desktop, 'same_folder')

# ---------- the Steam Frame's logs folder: its newest ten, never this run's
lepton_branch = between(runlog, 'if (lepton != null) {', '} else if (Build.VERSION.SDK_INT >= 29) {')
assert lepton_branch.index('destination = new File(folder, name).getAbsolutePath();') < \
    lepton_branch.index('new Thread(() -> pruneFolder(folder, name), "halo-log-retention").start();')
PRUNE = runlog[runlog.index('    static void pruneFolder(File folder, String current) {'):runlog.rindex('}')]
JAVA = r'''
import java.io.File;
final class RunLog {
    static void line(String text) { System.out.println("line " + text); }
%s
    static void check(boolean ok, String what) { if (!ok) { System.out.println("FAIL " + what); System.exit(1); } }
    static String log(int second) { return String.format("halo_log_2026-10-22_18-27-%%02d-187_1258.txt", second); }
    public static void main(String[] args) throws Exception {
        File folder = new File(args[0]);
        for (int second = 0; second < 13; second++) new File(folder, log(second)).createNewFile();
        new File(folder, "notes.txt").createNewFile();
        new File(folder, "halo_log_mine.log").createNewFile();
        pruneFolder(folder, log(12));
        for (int second = 0; second < 13; second++) check(new File(folder, log(second)).exists() == second >= 3, "the newest ten");
        check(new File(folder, "notes.txt").exists() && new File(folder, "halo_log_mine.log").exists(), "another file");
        // this run's, though its name is the oldest (the clock set back): kept
        for (int second = 0; second < 3; second++) new File(folder, log(second)).createNewFile();
        pruneFolder(folder, log(0));
        check(new File(folder, log(0)).exists(), "this run's deleted");
        check(!new File(folder, log(1)).exists() && !new File(folder, log(2)).exists() && new File(folder, log(3)).exists(),
            "the oldest others");
        pruneFolder(new File(folder, "none"), log(0));
        System.out.println("ok");
    }
}
'''


def run_prune(prune):
    with tempfile.TemporaryDirectory(prefix='test73b-prune-') as work:
        work = Path(work)
        (work / 'RunLog.java').write_text(JAVA % prune)
        (work / 'logs').mkdir()
        subprocess.run(['javac', '-d', str(work), str(work / 'RunLog.java')], check=True)
        result = subprocess.run(['java', '-cp', str(work), 'RunLog', str(work / 'logs')], capture_output=True, text=True)
        return result.returncode, result.stdout


java_ran = bool(shutil.which('javac') and shutil.which('java'))
if java_ran:
    status, output = run_prune(PRUNE)
    assert status == 0 and output.strip().endswith('ok'), output
    status, output = run_prune(mutated(PRUNE, 'if (!names[index].equals(current)) ', ''))
    assert status == 1 and 'FAIL' in output, output

# ---------- what the launchers and guides say
label = between(launcher, 'label(layout, Lepton.running()', '13, Color.rgb(150, 160, 170));')
frame_text, other_text = label.split('\n            : ', 1)
for text in ('Documents/HaloCEQuestVR/logs', 'halo_log_<date>_<time>.txt', 'the last ten are kept', 'launcher.log',
             'logcat.txt', 'install.log', 'debug.txt'):
    assert text in frame_text, text
assert 'Download' not in frame_text
for text in ('Download/HaloCE', 'the last ten are kept', 'halo_log.txt', 'debug.txt', '"headset" : "device"'):
    assert text in other_text, text
note = function(launcher.replace('    private void leptonNote', 'static void leptonNote'), 'leptonNote')
assert 'logs/halo_log_<date>_<time>.txt' in note and 'launcher.log' in note and 'logcat.txt' in note
assert 'Logs are in Download/HaloCE' in guide and 'Documents/HaloCEQuestVR/logs' in guide and 'halo-vr.log' in guide
assert 'Lepton' not in guide.replace('HaloCEQuestVR', '')  # (compiled on its own: tools/test_test32_launcher.py)
assert 'Each run\'s log is in Documents/HaloCEQuestVR/logs' in bundle and '(not yet run on a Frame)' not in bundle
assert 'each run\'s log is in\\n$GAME_DIR/logs' in install
for text in ('| Quest, PICO, Android | **Download/HaloCE**', '| Steam Frame | **Documents/HaloCEQuestVR/logs**',
             '| Windows | Beside the game: `halo.log`', "The PC launcher's **LOGS** page"):
    assert text in readme, text
assert '**Documents/HaloCEQuestVR/logs**' in player_guide and '**halo-vr.log**' in player_guide
assert '`halo-vr.log` next to `halo-vr.exe`' in windows_readme and '`logs\\`' in windows_readme

print('PASS: Windows keeps the last run\'s log in logs\\ (the newest ten of each build\'s; '
      + ('run with the Windows clang, 3 negative controls' if windows_ran else 'NOT RUN: no Windows clang here')
      + '); the PC launcher\'s LOGS page; the Steam Frame\'s logs folder its newest ten, never this run\'s ('
      + ('run with javac, a negative control' if java_ran else 'NOT RUN: no JDK here')
      + '); the Android launcher, the Frame\'s note, bundle and installer, the in-game guide and the docs name each '
      'device\'s')
