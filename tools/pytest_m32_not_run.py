"""Test67: a pytest plugin for GulchCE's MCC tests on a machine that cannot
run 32-bit programs (WSL1 has no 32-bit execution).

Those tests compile the real sources with -m32 -Werror (so `long` and
pointers are 4 bytes, as in the game) and then run the program. Here the
compile still happens and must succeed; only *starting* the 32-bit program
fails, with ENOEXEC ("Exec format error"). This plugin then runs exactly that
program under qemu-i386, as test_test31_menu_startup runs its ILP32 programs
(on WSL1 with its scoped reservation shim, tools/test_support/qemu_wsl_mmap.c,
preloaded into QEMU only and unset for the program). The test judges the
result as usual, and the summary counts these as M32-QEMU-RUN. Without
qemu-i386 (or with HALO_M32_QEMU=0) the start failure becomes a skip that says
so, counted as M32-NOT-RUN, so a summary never presents a compiled-but-not-run
test as a pass. Any other error, and every program that does start, is left
alone: on a machine that runs 32-bit programs nothing changes.

Loaded with `-p pytest_m32_not_run` (tools/ on PYTHONPATH).
"""
import errno
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REASON = "compiled with -m32 but not run: this machine cannot run 32-bit programs (WSL1)"
SHIM = Path(__file__).resolve().parent / 'test_support' / 'qemu_wsl_mmap.c'
not_run = []
qemu_run = []
current = [None]
_qemu = []
_popen_init = subprocess.Popen.__init__


def _qemu_runner():
    """(QEMU's command prefix, the shim to preload into QEMU or None), or None"""
    if not _qemu:
        runner = None
        qemu = shutil.which('qemu-i386')
        if qemu and os.environ.get('HALO_M32_QEMU', '1') != '0':
            preload = None
            release = Path('/proc/sys/kernel/osrelease').read_text().lower()
            if 'microsoft' in release and 'wsl2' not in release:
                shim = Path(tempfile.mkdtemp(prefix='m32-qemu-shim-')) / 'qemu_wsl_mmap.so'
                subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror', str(SHIM), '-ldl',
                                '-o', str(shim)], check=True)
                preload = str(shim)
            runner = ([qemu, '-B', '0x10000000000', '-R', os.environ.get('HALO_M32_QEMU_RESERVE', '1G'),
                       '-U', 'LD_PRELOAD'], preload)
        _qemu.append(runner)
    return _qemu[0]


def _popen_init_m32(self, *args, **kwargs):
    try:
        _popen_init(self, *args, **kwargs)
    except OSError as error:
        if error.errno != errno.ENOEXEC:
            raise
        command = args[0] if args else kwargs.get('args')
        runner = None
        if isinstance(command, (list, tuple)) and not kwargs.get('shell') and not kwargs.get('executable'):
            runner = _qemu_runner()
        if runner is None:
            raise pytest.skip.Exception(REASON, _use_item_location=True) from None
        prefix, preload = runner
        if preload:
            environment = dict(kwargs.get('env') if kwargs.get('env') is not None else os.environ)
            environment['LD_PRELOAD'] = preload
            kwargs['env'] = environment
        if args:
            args = (prefix + [str(part) for part in command],) + args[1:]
        else:
            kwargs['args'] = prefix + [str(part) for part in command]
        if current[0] and current[0] not in qemu_run:
            qemu_run.append(current[0])
        _popen_init(self, *args, **kwargs)


subprocess.Popen.__init__ = _popen_init_m32


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    current[0] = item.nodeid
    yield
    current[0] = None


def pytest_runtest_logreport(report):
    if report.skipped and isinstance(report.longrepr, tuple) and REASON in str(report.longrepr[2]):
        if report.nodeid not in not_run:
            not_run.append(report.nodeid)


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line("M32-QEMU-RUN: %d" % len(qemu_run))
    terminalreporter.write_line("M32-NOT-RUN: %d" % len(not_run))
