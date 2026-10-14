"""Test67: a pytest plugin for GulchCE's MCC tests on a machine that cannot
run 32-bit programs (WSL1 has no 32-bit execution).

Those tests compile the real sources with -m32 -Werror (so `long` and
pointers are 4 bytes, as in the game) and then run the program. Here the
compile still happens and must succeed; only *starting* the 32-bit program
fails, with ENOEXEC ("Exec format error"). This plugin turns exactly that
failure into a skip that says so, and counts the skips, so that a summary
never presents a compiled-but-not-run test as a pass. Any other error, and
every program that does start, is left alone: on a machine that runs 32-bit
programs nothing is skipped.

Loaded with `-p pytest_m32_not_run` (tools/ on PYTHONPATH).
"""
import errno
import subprocess

import pytest

REASON = "compiled with -m32 but not run: this machine cannot run 32-bit programs (WSL1)"
not_run = []
_popen_init = subprocess.Popen.__init__


def _popen_init_m32(self, *args, **kwargs):
    try:
        _popen_init(self, *args, **kwargs)
    except OSError as error:
        if error.errno != errno.ENOEXEC:
            raise
        raise pytest.skip.Exception(REASON, _use_item_location=True) from None


subprocess.Popen.__init__ = _popen_init_m32


def pytest_runtest_logreport(report):
    if report.skipped and isinstance(report.longrepr, tuple) and REASON in str(report.longrepr[2]):
        if report.nodeid not in not_run:
            not_run.append(report.nodeid)


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line("M32-NOT-RUN: %d" % len(not_run))
