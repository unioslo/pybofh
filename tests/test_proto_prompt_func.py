# -*- coding: utf-8 -*-
"""
Tests for commands that use a server side prompt function, i.e.
:meth:`bofh.proto._Command._prompt_func`.
"""
from __future__ import print_function, unicode_literals

import pytest

from bofh import proto
from bofh import readlineui


class FakeBofh(object):
    """ Returns the given call_prompt_func responses in turn. """

    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompt_func_args = []
        self.run_command_args = []

    def call_prompt_func(self, command, *args):
        self.prompt_func_args.append(args)
        return self.responses.pop(0)

    def arg_help(self, help_ref):
        return "help for %s" % (help_ref,)

    def run_command(self, command, *args):
        self.run_command_args.append(args)
        return "ok"

    def get_format_suggestion(self, command):
        return None


class FakeGroup(object):
    def __init__(self, bofh):
        self._bofh = bofh
        self._name = 'misc'


def make_command(bofh):
    return proto._Command(FakeGroup(bofh), 'print', 'misc_print',
                          'prompt_func')


def select_user(raw):
    """ a prompt func response with a map, like misc print_passwords """
    response = {
        'prompt': "Choose user(s)",
        'map': [
            [["%8s %s", "uname", "operation"], None],
            [["%-12s %s", "alice", "password"], 1],
            [["%-12s %s", "bob", "password"], 2],
            [["%-12s %s", "carol", "password"], 3],
        ],
        'last_arg': True,
    }
    if raw:
        response['raw'] = True
    return response


class RecordingPrompter(object):
    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.answer


def test_map_is_passed_to_prompter():
    bofh = FakeBofh(select_user(raw=False))
    prompter = RecordingPrompter(2)
    assert make_command(bofh).prompt_missing_args(prompter) == [2]
    assert prompter.calls == [(
        ("Choose user(s)",
         [(None, "   uname operation"),
          (1, "alice        password"),
          (2, "bob          password"),
          (3, "carol        password")],
         None,
         None),
        {},
    )]


def test_raw_map_is_passed_to_prompter():
    bofh = FakeBofh(select_user(raw=True))
    prompter = RecordingPrompter("1-3")
    assert make_command(bofh).prompt_missing_args(prompter) == ["1-3"]
    assert prompter.calls == [(
        ("Choose user(s)",
         [(None, "   uname operation"),
          (1, "alice        password"),
          (2, "bob          password"),
          (3, "carol        password")],
         None,
         None),
        {'raw': True},
    )]


@pytest.mark.parametrize('answer', ["2", "1-3", "1-2,3", "anything"])
def test_raw_answer_is_sent_as_typed(scripted_input, answer):
    # the server parses the selection itself
    bofh = FakeBofh(select_user(raw=True))
    scripted_input(answer)
    command = make_command(bofh)
    assert command.prompt_missing_args(readlineui.prompter) == [answer]


@pytest.mark.parametrize('answer, expected', [
    ("2", 2),
    ("1-3", [1, 2, 3]),
])
def test_answer_is_mapped(scripted_input, answer, expected):
    bofh = FakeBofh(select_user(raw=False))
    scripted_input(answer)
    command = make_command(bofh)
    assert command.prompt_missing_args(readlineui.prompter) == [expected]
