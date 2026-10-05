# -*- coding: utf-8 -*-
"""
Tests for keyboard interrupt (Ctrl+C) and end-of-file (Ctrl+D) handling in
:func:`bofh.cli.main`.
"""
from __future__ import print_function, unicode_literals

import pytest

import bofh
import bofh.cli
import bofh.readlineui


class FakeConnection(object):
    motd = None

    def __init__(self):
        self.logged_in = False
        self.logged_out = False
        self.logout_error = None

    def login(self, user, password):
        self.logged_in = True

    def logout(self):
        if self.logout_error:
            raise self.logout_error
        self.logged_out = True


@pytest.fixture
def conn(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(bofh, 'connect', lambda **kwargs: connection)
    return connection


def set_password_input(monkeypatch, exc=None):
    def get_secret(ioutil, prompt=None):
        if exc:
            raise exc
        return 'secret'
    monkeypatch.setattr(bofh.readlineui.IOUtil, 'get_secret', get_secret)


def set_repl(monkeypatch, exc=None):
    def repl(*args, **kwargs):
        if exc:
            raise exc
    monkeypatch.setattr(bofh.readlineui, 'repl', repl)


def set_eval(monkeypatch, exc):
    def bofh_eval(*args, **kwargs):
        raise exc
    monkeypatch.setattr(bofh.cli, 'bofh_eval', bofh_eval)


ARGS = ['--url', 'https://localhost:8000', '--user', 'foo', '--quiet']


@pytest.mark.parametrize('exc, code', [(KeyboardInterrupt, 130),
                                       (EOFError, None)])
def test_abort_password_prompt(monkeypatch, conn, capsys, exc, code):
    set_password_input(monkeypatch, exc)
    with pytest.raises(SystemExit) as exc_info:
        bofh.cli.main(ARGS)
    assert exc_info.value.code == code
    assert not conn.logged_in
    assert capsys.readouterr()[0].endswith("\n\n")


def test_repl_exits(monkeypatch, conn):
    set_password_input(monkeypatch)
    set_repl(monkeypatch, SystemExit(0))
    with pytest.raises(SystemExit) as exc_info:
        bofh.cli.main(ARGS)
    assert exc_info.value.code == 0
    assert conn.logged_out


def test_interrupt_in_repl_exits(monkeypatch, conn):
    # e.g. Ctrl+C when asked to re-authenticate after session expiry
    set_password_input(monkeypatch)
    set_repl(monkeypatch, KeyboardInterrupt)
    with pytest.raises(SystemExit) as exc_info:
        bofh.cli.main(ARGS)
    assert exc_info.value.code == 130
    assert conn.logged_out


def test_interrupt_in_cmd_exits(monkeypatch, conn):
    set_password_input(monkeypatch)
    set_eval(monkeypatch, KeyboardInterrupt)
    with pytest.raises(SystemExit) as exc_info:
        bofh.cli.main(ARGS + ['--cmd', 'foo'])
    assert exc_info.value.code == 130
    assert conn.logged_out


# How a session can end, and how main() should exit (None: return normally)
ENDINGS = {
    'eof': (None, None),
    'quit': (SystemExit(0), 0),
    'interrupt': (KeyboardInterrupt, 130),
    'error': (RuntimeError('boom'), 'Error: boom'),
}


def run_main():
    """ run main(), and return how it exited. """
    try:
        bofh.cli.main(ARGS)
    except SystemExit as e:
        return ('exit', e.code)
    except BaseException as e:
        return ('raised', type(e))
    return ('returned', None)


@pytest.mark.parametrize('ending', sorted(ENDINGS))
def test_logout_on_exit(monkeypatch, conn, ending):
    exc, code = ENDINGS[ending]
    set_password_input(monkeypatch)
    set_repl(monkeypatch, exc)
    expected = ('returned', None) if ending == 'eof' else ('exit', code)
    assert run_main() == expected
    assert conn.logged_out


@pytest.mark.parametrize('logout_error', [
    OSError(113, 'No route to host'),
    bofh.proto.BofhError('Session expired'),
    KeyboardInterrupt(),
])
@pytest.mark.parametrize('ending', sorted(ENDINGS))
def test_logout_error_on_exit(monkeypatch, conn, ending, logout_error):
    # e.g. the server can't be reached - exit as if logout succeeded
    exc, code = ENDINGS[ending]
    set_password_input(monkeypatch)
    set_repl(monkeypatch, exc)
    conn.logout_error = logout_error
    expected = ('returned', None) if ending == 'eof' else ('exit', code)
    assert run_main() == expected
