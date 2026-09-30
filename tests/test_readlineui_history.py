# -*- coding: utf-8 -*-
"""
Tests for readline history handling in :func:`bofh.readlineui.prompter`.

Answers to argument prompts should not be kept in the history, but the
command itself should.
"""
from __future__ import print_function, unicode_literals

import readline

import pytest

from bofh import readlineui


def get_history():
    return [readline.get_history_item(i)
            for i in range(1, readline.get_current_history_length() + 1)]


@pytest.fixture
def history():
    """ a clean readline history, with a given list of lines. """
    def set_history(*lines):
        readline.clear_history()
        for line in lines:
            readline.add_history(line)
    yield set_history
    readline.clear_history()


@pytest.fixture
def terminal_input(monkeypatch, scripted_input):
    """
    Scripted input that updates the readline history like a terminal would.

    input() adds a non-empty line to the history, unless it is identical to
    the previous line in the history.  getpass() never does.
    """
    def install(*items):
        feeder = scripted_input(*items)

        def get_input(ioutil, prompt=None):
            line = feeder(prompt)
            length = readline.get_current_history_length()
            if line and (length == 0 or
                         readline.get_history_item(length) != line):
                readline.add_history(line)
            return line

        def get_secret(ioutil, prompt=None):
            return feeder(prompt)

        monkeypatch.setattr(readlineui.IOUtil, 'get_input', get_input)
        monkeypatch.setattr(readlineui.IOUtil, 'get_secret', get_secret)
        return feeder
    return install


def ask(argtype=None):
    return readlineui.prompter("Arg", None, None, None, argtype=argtype)


def test_answer_is_removed(history, terminal_input):
    history('misc echo first', 'user info')
    terminal_input('bob')
    assert ask() == 'bob'
    assert get_history() == ['misc echo first', 'user info']


def test_empty_answer_keeps_history(history, terminal_input):
    history('misc echo first', 'user create')
    terminal_input('')
    assert readlineui.prompter("Shell", None, None, '/bin/bash') == '/bin/bash'
    assert get_history() == ['misc echo first', 'user create']


def test_password_answer_keeps_command(history, terminal_input):
    # getpass() doesn't add the answer to the history
    history('misc echo first', 'user password bob')
    terminal_input('hunter2')
    assert ask(argtype='accountPassword') == 'hunter2'
    assert get_history() == ['misc echo first', 'user password bob']


def test_repeated_answer_keeps_command(history, terminal_input):
    # the answer is identical to the command line, so input() doesn't add it
    history('misc echo first', 'foo')
    terminal_input('foo')
    assert ask() == 'foo'
    assert get_history() == ['misc echo first', 'foo']


def test_answers_after_retry_are_removed(history, terminal_input):
    # an invalid answer, then a valid one - neither should be kept
    history('misc echo first', 'group add_member')
    terminal_input('9', '2')
    mapping = [(None, "Header"), ('key-a', "item a"), ('key-b', "item b")]
    assert readlineui.prompter("Pick", mapping, None, None) == 'key-b'
    assert get_history() == ['misc echo first', 'group add_member']
