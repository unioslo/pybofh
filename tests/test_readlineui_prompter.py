# -*- coding: utf-8 -*-
"""
Tests for selecting items from a numbered list in
:func:`bofh.readlineui.prompter`.
"""
from __future__ import print_function, unicode_literals

import pytest
import six

from bofh import readlineui

# as given to the prompter by bofh.proto._Command._prompt_func
MAPPING = [
    (None, "Header"),
    ('key-a', "item a"),
    ('key-b', "item b"),
    ('key-c', "item c"),
]

LISTING = "Header\n   1 item a\n   2 item b\n   3 item c\n"


def select():
    return readlineui.prompter("Pick", MAPPING, None, None)


@pytest.mark.parametrize('answer, expected', [
    ('1', 'key-a'),
    ('3', 'key-c'),
    (' 2 ', 'key-b'),
])
def test_select_item(scripted_input, capsys, answer, expected):
    scripted_input(answer)
    assert select() == expected
    assert capsys.readouterr()[0] == LISTING


@pytest.mark.parametrize('answer, expected', [
    ('1,3', ['key-a', 'key-c']),
    ('3, 1', ['key-c', 'key-a']),
    ('2,2', ['key-b', 'key-b']),
])
def test_select_list(scripted_input, answer, expected):
    scripted_input(answer)
    assert select() == expected


@pytest.mark.parametrize('answer, expected', [
    ('1-3', ['key-a', 'key-b', 'key-c']),
    ('2 - 3', ['key-b', 'key-c']),
    ('2-2', ['key-b']),
])
def test_select_range(scripted_input, answer, expected):
    scripted_input(answer)
    assert select() == expected


@pytest.mark.parametrize('answer', ['text', '-1', '1-2x', 'a1,2'])
def test_other_text_asks_again(scripted_input, capsys, answer):
    feeder = scripted_input(answer, '1')
    assert select() == 'key-a'
    assert feeder.items == []
    assert capsys.readouterr()[0] == (
        LISTING
        + "Please type a number matching one of the items\n"
        + LISTING)


def test_unicode_digit_asks_again(scripted_input):
    # isdigit(), but not valid for int()
    feeder = scripted_input(six.unichr(0xb2), '1')
    assert select() == 'key-a'
    assert feeder.items == []


@pytest.mark.parametrize('answer', ['1-3', '1-2,5', '9', 'text'])
def test_raw_answer_is_returned_as_typed(scripted_input, capsys, answer):
    scripted_input(answer)
    assert readlineui.prompter("Pick", MAPPING, None, None,
                               raw=True) == answer
    assert capsys.readouterr()[0] == LISTING


@pytest.mark.parametrize('answer, message', [
    ('0', "The item you selected does not exist"),
    ('4', "The item you selected does not exist"),
    ('0,1', "The item you selected does not exist"),
    ('1,9', "The item you selected does not exist"),
    ('0-2', "The item you selected does not exist"),
    ('2-9', "The item you selected does not exist"),
    ('3-1', "Please specify a range, eg. 1-3"),
])
def test_invalid_selection_asks_again(scripted_input, capsys, answer,
                                      message):
    feeder = scripted_input(answer, '1')
    assert select() == 'key-a'
    assert feeder.items == []
    assert capsys.readouterr()[0] == LISTING + message + "\n" + LISTING


def test_help(scripted_input, capsys):
    scripted_input('?', '1')
    assert readlineui.prompter("Pick", MAPPING, "Some help", None) == 'key-a'
    assert capsys.readouterr()[0] == LISTING + "Some help\n" + LISTING


def test_default(scripted_input):
    scripted_input('')
    assert readlineui.prompter("Pick", MAPPING, None, 'key-b') == 'key-b'
