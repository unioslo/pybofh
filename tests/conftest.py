""" common pytest fixtures """
from __future__ import unicode_literals

import pytest

from bofh import proto
from bofh import readlineui
from bofh.proto import Bofh


@pytest.fixture
def url():
    return 'https://localhost:8000'


class MockConnection(object):
    def __init__(self, *args, **kwargs):
        pass


class MockBofh(Bofh):
    """ bofh stub """

    def _connect(self, url, context=None, timeout=None):
        u"""Establish a connection with the bofh server"""
        self._connection = MockConnection(
            url,
            transport=MockConnection(
                context=context,
                use_datetime=True,
                timeout=timeout))

    def _run_raw_command(self, name, *args):
        getattr(self._connection, name)
        return None

    def _run_raw_sess_command(self, name, *args):
        getattr(self._connection, name)
        return None

    def format_args(self, args):
        argslist = list(args)
        return tuple(argslist)

    def get_motd(self, client="PyBofh", version='0.0.0'):
        return ''

    # def login(self, user, password, init=True)
    # def logout(self)
    # def get_commands(self)
    # def help(self, *args)
    # def arg_help(self, help_ref)
    # def run_command(self, command, *args)
    # def call_prompt_func(self, command, *args)
    # def get_default_param(self, command, *args)
    # def get_format_suggestion(self, command)

    def _init_commands(self, reset=False):
        # TODO: Mock
        pass


@pytest.fixture
def bofh(url):
    """
    a bofh.proto.Bofh object

    a lot of things needs a bofh object, but doesn't really use it. This
    provides a basic stub that can be used in tests. It should be removed, and
    the functions that needs it should be refactored.
    """
    return MockBofh(url, None)


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
            raise AssertionError("asked for more input than expected")
        item = self.items.pop(0)
        if isinstance(item, BaseException) or (
                isinstance(item, type) and issubclass(item, BaseException)):
            raise item
        return item


@pytest.fixture
def scripted_input(monkeypatch):
    """
    Replace user input with the given items.

    See :class:`ScriptedInput`.
    """
    def install(*items):
        feeder = ScriptedInput(*items)

        def get_input(ioutil, prompt=None):
            return feeder(prompt)

        monkeypatch.setattr(readlineui.IOUtil, 'get_input', get_input)
        monkeypatch.setattr(readlineui.IOUtil, 'get_secret', get_input)
        return feeder
    return install


class FakeBofhdConnection(object):
    """
    A fake bofhd XMLRPC connection, with a few commands.

    run_command() returns a text describing the call, and, like bofhd, runs
    the command once for each item in a list argument.  Set `error` to make
    it raise an exception instead.
    """

    commands = {
        'misc_error': [['misc', 'error'], []],
        'misc_echo': [['misc', 'echo'], [{'prompt': "Text"}]],
        'user_info': [['user', 'info'], [{'prompt': "Username"}]],
    }

    def __init__(self):
        self.error = None
        self.run_command_calls = []

    def get_commands(self, session):
        return self.commands

    def get_format_suggestion(self, command):
        return ''

    def run_command(self, session, command, *args):
        self.run_command_calls.append((command,) + args)
        if self.error is not None:
            raise self.error
        for n, arg in enumerate(args):
            if isinstance(arg, list):
                return ['%s %s' % (command, ' '.join(
                    args[:n] + (item,) + args[n + 1:])) for item in arg]
        return '%s %s' % (command, ' '.join(args))


@pytest.fixture
def commands_bofh():
    """ a bofh.proto.Bofh object with a FakeBofhdConnection. """
    bofh = proto.Bofh.__new__(proto.Bofh)
    bofh._groups = dict()
    bofh._connection = FakeBofhdConnection()
    bofh._session = 'session'
    bofh._init_commands()
    return bofh
