from __future__ import unicode_literals

from bofh.parser import lexer


def test_lexer_empty():
    text = ''
    result = list(lexer(text))
    assert result == []


def test_one_token():
    text = 'foo'
    result = list(lexer(text))
    assert result == [('foo', 0)]


def test_two_tokens():
    text = 'foo bar'
    result = list(lexer(text))
    assert result == [('foo', 0), ('bar', 4)]


def test_quotes():
    text = '"foo bar"'
    result = list(lexer(text))
    assert result == [('foo bar', 0)]


def test_quotes_incomplete():
    text = 'foo "bar'
    result = list(lexer(text))
    assert result == [('foo', 0), ('"', -1), ('bar', 4)]


def test_quotes_escape():
    text = 'foo \\"bar'
    result = list(lexer(text))
    assert result == [('foo', 0), ('"bar', 4)]
