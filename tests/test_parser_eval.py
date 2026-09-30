# -*- coding: utf-8 -*-
"""
Tests for running a parsed bofh command, :meth:`bofh.parser.BofhCommand.eval`.
"""
from __future__ import print_function, unicode_literals

import pytest

from bofh import parser
from bofh import readlineui


def run(bofh, line):
    return parser.parse(bofh, line).eval(prompter=None)


def test_run_command(commands_bofh):
    assert run(commands_bofh, 'user info alice') == 'user_info alice'


def test_run_command_with_list(commands_bofh):
    assert run(commands_bofh, 'user info (bob alice)') == [
        'user_info bob', 'user_info alice']


@pytest.mark.parametrize('line', ['user nosuch', 'user nosuch alice',
                                  'misc e'])
def test_unknown_command(commands_bofh, line):
    with pytest.raises(parser.NoGroup) as exc_info:
        run(commands_bofh, line)
    assert str(exc_info.value) == "Unknown command"
    assert commands_bofh._connection.run_command_calls == []


@pytest.mark.parametrize('line', ['user info alice',
                                  'user info (bob alice)'])
def test_attribute_error_in_command(commands_bofh, line):
    # e.g. a bug somewhere while running the command - not "Unknown command"
    commands_bofh._connection.error = AttributeError("some bug")
    with pytest.raises(AttributeError):
        run(commands_bofh, line)


def test_repl_unknown_command(commands_bofh, scripted_input, capsys):
    scripted_input('user nosuch', 'user info alice', EOFError)
    readlineui.repl(commands_bofh)
    out = capsys.readouterr()[0]
    assert out.startswith("Unknown command\nuser_info alice\n")


def test_repl_attribute_error_with_list(commands_bofh, scripted_input,
                                        caplog):
    # the error is logged, and the next command runs
    commands_bofh._connection.error = AttributeError("some bug")
    feeder = scripted_input('user info (bob alice)', 'user info alice',
                            EOFError)
    readlineui.repl(commands_bofh)
    assert feeder.items == []
    assert "Unhandled exception" in caplog.text
    assert commands_bofh._connection.run_command_calls[-1] == (
        'user_info', 'alice')
