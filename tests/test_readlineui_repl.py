# -*- coding: utf-8 -*-
"""
Tests for keyboard interrupt (Ctrl+C) and end-of-file (Ctrl+D) handling in
:func:`bofh.readlineui.repl`.
"""
from __future__ import print_function, unicode_literals

import pytest

from bofh import readlineui


class ScriptedInput(object):
    """
    Replacement for IOUtil.get_input/get_secret.

    Returns each item in turn, or raises it if it is an exception.  Raises
    AssertionError if the input is exhausted, so that a test can't loop
    forever.
    """

    def __init__(self, *items):
        self.items = list(items)
        self.prompts = []

    def __call__(self, prompt=None):
        self.prompts.append(prompt)
        if not self.items:
            raise AssertionError("repl asked for more input than expected")
        item = self.items.pop(0)
        if isinstance(item, BaseException) or (
                isinstance(item, type) and issubclass(item, BaseException)):
            raise item
        return item


class FakeParse(object):
    """ A parse result whose eval() runs a given callable. """

    def __init__(self, func):
        self.func = func

    def eval(self, prompter=None, prompt=None):
        return self.func(prompter)


@pytest.fixture
def scripted_input(monkeypatch):
    def install(*items):
        feeder = ScriptedInput(*items)

        def get_input(ioutil, prompt=None):
            return feeder(prompt)

        monkeypatch.setattr(readlineui.IOUtil, 'get_input', get_input)
        monkeypatch.setattr(readlineui.IOUtil, 'get_secret', get_input)
        return feeder
    return install


@pytest.fixture
def commands(monkeypatch):
    """ map input lines to callables that emulate command evaluation. """
    mapping = {}

    def fake_parse(bofh, line):
        return FakeParse(mapping[line])

    monkeypatch.setattr(readlineui.parser, 'parse', fake_parse)
    return mapping


def raiser(exc):
    def func(prompter):
        raise exc
    return func


def ask(prompt):
    """ a command that asks for one argument, and returns it. """
    def func(prompter):
        return prompter(prompt, None, None, None)
    return func


def test_eof_at_prompt_exits(bofh, scripted_input, capsys):
    scripted_input(EOFError)
    readlineui.repl(bofh)
    assert capsys.readouterr()[0] == (
        "\nSo long, and thanks for all the fish!\n")


def test_interrupt_at_prompt_cancels_line(bofh, scripted_input, capsys):
    feeder = scripted_input(KeyboardInterrupt, EOFError)
    readlineui.repl(bofh)
    assert feeder.prompts == [None, None]
    assert capsys.readouterr()[0] == (
        "\n"
        "\nSo long, and thanks for all the fish!\n")


def test_repeated_interrupt_at_prompt(bofh, scripted_input):
    feeder = scripted_input(KeyboardInterrupt, KeyboardInterrupt,
                            KeyboardInterrupt, EOFError)
    readlineui.repl(bofh)
    assert feeder.items == []


def test_command_output(bofh, scripted_input, commands, capsys):
    commands['foo'] = lambda prompter: "foo result"
    scripted_input('foo', EOFError)
    readlineui.repl(bofh)
    assert capsys.readouterr()[0].startswith("foo result\n")


@pytest.mark.parametrize('exc', [EOFError, KeyboardInterrupt])
def test_abort_argument_prompt(bofh, scripted_input, commands, capsys, exc):
    commands['foo'] = ask("Arg")
    feeder = scripted_input('foo', exc, EOFError)
    readlineui.repl(bofh)
    assert feeder.prompts == [None, "Arg > ", None]
    assert capsys.readouterr()[0] == (
        "\n"
        "\nSo long, and thanks for all the fish!\n")


def test_interrupt_during_command_aborts_command(bofh, scripted_input,
                                                 commands, capsys):
    # e.g. Ctrl+C while waiting for a slow server response
    commands['slow'] = raiser(KeyboardInterrupt)
    commands['foo'] = lambda prompter: "foo result"
    feeder = scripted_input('slow', 'foo', EOFError)
    readlineui.repl(bofh)
    assert feeder.items == []
    assert capsys.readouterr()[0] == (
        "\n"
        "foo result\n"
        "\nSo long, and thanks for all the fish!\n")


def test_quit_command_exits(bofh, scripted_input, commands):
    commands['quit'] = raiser(SystemExit(0))
    scripted_input('quit')
    with pytest.raises(SystemExit) as exc_info:
        readlineui.repl(bofh)
    assert exc_info.value.code == 0
