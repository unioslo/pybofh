# -*- coding: utf-8 -*-
"""
Tests for setting up tab completion in :func:`bofh.readlineui.repl`.

Python's readline module is built against either GNU readline or libedit
(editline), and they need different commands to bind the tab key.
"""
from __future__ import print_function, unicode_literals

import readline

import pytest

from bofh import readlineui

GNU_DOC = "Importing this module enables command line editing using GNU readline."
LIBEDIT_DOC = "Importing this module enables command line editing using libedit readline."


@pytest.fixture
def bindings(monkeypatch):
    """ record readline.parse_and_bind() calls. """
    calls = []
    monkeypatch.setattr(readline, 'parse_and_bind', calls.append)
    return calls


@pytest.fixture
def backend(monkeypatch):
    """
    Pretend readline uses a given backend.

    Python 3.13+ has readline.backend, older versions only mention libedit in
    the module docstring.
    """
    def set_backend(name, has_attribute):
        if has_attribute:
            monkeypatch.setattr(readline, 'backend', name, raising=False)
        else:
            monkeypatch.delattr(readline, 'backend', raising=False)
        doc = LIBEDIT_DOC if name == 'editline' else GNU_DOC
        monkeypatch.setattr(readline, '__doc__', doc)
    return set_backend


@pytest.mark.parametrize('has_attribute', [True, False])
def test_gnu_readline_binding(bofh, scripted_input, bindings, backend,
                              has_attribute):
    backend('readline', has_attribute)
    scripted_input(EOFError)
    readlineui.repl(bofh)
    assert bindings == ["tab: complete"]


@pytest.mark.parametrize('has_attribute', [True, False])
def test_libedit_binding(bofh, scripted_input, bindings, backend,
                         has_attribute):
    backend('editline', has_attribute)
    scripted_input(EOFError)
    readlineui.repl(bofh)
    assert bindings == ["bind ^I rl_complete"]
