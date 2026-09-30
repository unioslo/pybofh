# -*- coding: utf-8 -*-
"""
Tests for parsing incomplete input, e.g. an unclosed quote, with
:func:`bofh.parser.parse`.

Incomplete input raises IncompleteParse, which should carry the parsed
command so that tab completion can use it.
"""
from __future__ import unicode_literals

import readline

import pytest

from bofh import parser
from bofh import readlineui


@pytest.fixture
def conn(commands_bofh):
    return commands_bofh


def get_args(parse):
    """ the command arguments that would be sent to the server. """
    return list(parser._prepare_args(parse.args[2:]))


def test_complete_line(conn):
    parse = parser.parse(conn, 'user info alice')
    assert get_args(parse) == ['alice']


def test_missing_argument(conn):
    # the missing argument is prompted for when running the command
    parse = parser.parse(conn, 'user info')
    assert get_args(parse) == []


def test_list_argument(conn):
    parse = parser.parse(conn, 'user info (bob "alice smith")')
    assert get_args(parse) == [['bob', 'alice smith']]


@pytest.mark.parametrize('line, message, expected', [
    ('user info "alice', 'Expected ", got nothing', ['alice']),
    ('misc echo "foo bar', 'Expected ", got nothing', ['foo bar']),
    ('user info alice\\', "Expected something, got nothing", ['alice']),
    ('user info "', 'Expected ", got nothing', []),
    ('user info \\', "Expected something, got nothing", []),
    ('user info (bob alice', "Expected ), got nothing", [['bob', 'alice']]),
    ('user info (bob "alice', "Expected ), got nothing", [['bob', 'alice']]),
    ('user info (', "Expected ), got nothing", [[]]),
])
def test_unclosed_quote_in_argument(conn, line, message, expected):
    # an error, but with the parsed command for tab completion
    with pytest.raises(parser.IncompleteParse) as exc_info:
        parser.parse(conn, line)
    assert exc_info.value.msg == message
    assert get_args(exc_info.value.parse) == expected


@pytest.mark.parametrize('text, message', [
    ('"foo', 'Expected ", got nothing'),
    ('foo\\', "Expected something, got nothing"),
])
def test_unclosed_quote_message(text, message):
    lex = parser.lexer(text)
    with pytest.raises(parser.IncompleteParse) as exc_info:
        parser.parse_string_or_list(lex)
    assert exc_info.value.msg == message


@pytest.mark.parametrize('line, message, partial', [
    ('misc error "foo', 'Expected ", got nothing', ('foo', 11)),
    ('misc error foo\\', "Expected something, got nothing", ('foo', 11)),
    ('user info alice "foo', 'Expected ", got nothing', ('foo', 16)),
])
def test_unclosed_quote_in_extra_argument(conn, line, message, partial):
    with pytest.raises(parser.IncompleteParse) as exc_info:
        parser.parse(conn, line)
    assert exc_info.value.msg == message
    parse = exc_info.value.parse
    assert isinstance(parse, parser.BofhCommand)
    assert parse.args[-1] == partial + ([],)
    # no completions for an extra argument
    assert parse.complete(partial[1], len(line)) == []


def test_tab_completion_on_extra_argument(conn, monkeypatch):
    line = 'misc error "foo'
    monkeypatch.setattr(readline, 'get_line_buffer', lambda: line)
    monkeypatch.setattr(readline, 'get_begidx', lambda: 11)
    monkeypatch.setattr(readline, 'get_endidx', lambda: len(line))
    completer = readlineui.BofhCompleter(conn, 'utf-8')
    assert completer('foo', 0) is None


def test_tab_completion_on_argument(conn, monkeypatch):
    line = 'user info "ali'
    monkeypatch.setattr(readline, 'get_line_buffer', lambda: line)
    monkeypatch.setattr(readline, 'get_begidx', lambda: 11)
    monkeypatch.setattr(readline, 'get_endidx', lambda: len(line))
    completer = readlineui.BofhCompleter(conn, 'utf-8')
    assert completer('ali', 0) is None
