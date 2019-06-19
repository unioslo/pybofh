""" common pytest fixtures """
from __future__ import unicode_literals

import pytest

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
