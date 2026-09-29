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

    def login(self, user, password):
        self.logged_in = True

    def logout(self):
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


def set_repl(monkeypatch, exc):
    def repl(*args, **kwargs):
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
