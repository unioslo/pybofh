# -*- coding: utf-8 -*-
#
# Copyright 2010-2018 University of Oslo, Norway
#
# This file is part of pybofh.
#
# pybofh is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pybofh is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pybofh; if not, see <https://www.gnu.org/licenses/>.
"""
Module to communicate with a bofh server.
"""
from __future__ import absolute_import, unicode_literals

import logging
import socket
import ssl

import six
from six.moves import xmlrpc_client as _xmlrpc
from six.moves.urllib.parse import urlparse

from . import https
from . import version
from .formatting import get_formatter


logger = logging.getLogger(__name__)


def wash_response(bofh_response):
    """
    Wash response data.

    Walk down any objects in response (we can get strings, dicts and lists),
    and make sure any strings are unicode.  Also, the server and client codes
    ``None`` as ``":None"``, and escapes strings starting with ``":"`` as
    ``"::"``.

    >>> wash_response(":None")
    >>> wash_response("::None")
    u':None'
    >>> wash_response(["None", ":None", "::None"])
    [u'None', None, u':None']
    """
    if isinstance(bofh_response, six.binary_type):
        # TODO: Hasn't the encoding changed?
        bofh_response = bofh_response.decode("ISO-8859-1")

    if isinstance(bofh_response, six.text_type):
        if bofh_response and bofh_response[0] == ':':
            bofh_response = (None if bofh_response == ':None'
                             else bofh_response[1:])
    elif isinstance(bofh_response, (list, tuple)):
        bofh_response = type(bofh_response)((wash_response(x)
                                             for x in bofh_response))
    elif isinstance(bofh_response, dict):
        for i in bofh_response.keys():
            bofh_response[i] = wash_response(bofh_response[i])
    return bofh_response


def format_args(args):
    """
    Format special arguments.

    Add additional ':' if an argument is a basestring and starts with ':',
    as this will get sliced off by xmlutils.py in backend.
    """
    argslist = list(args)
    for pos, arg in enumerate(argslist):
        if isinstance(arg, six.string_types) and arg.startswith(':'):
            argslist[pos] = ':' + arg
    return tuple(argslist)


@six.python_2_unicode_compatible
class _Argument(object):
    """Bofh command parameter specifier"""
    def __init__(self, bofh, map):
        self._bofh = bofh
        self.optional = map.get('optional', False)
        self.repeat = map.get('repeat', False)
        self.default = map.get('default')
        self.type = map.get('type')
        self.help_ref = map.get('help_ref', False)
        self.prompt = map.get('prompt')

    @property
    def help(self):
        """Help string from bofh"""
        if hasattr(self, '_help'):
            return self._help
        else:
            help = self._help = self._bofh.arg_help(self.help_ref)
            return help

    def __str__(self):
        stuff = ('type', 'optional', 'default')
        return ("{" +
                ", ".join(map(lambda x: x + ": %(" + x + ")s", stuff)) +
                "}") % self.__dict__


@six.python_2_unicode_compatible
class _PromptFunc(object):
    """Parameter specifier for prompt_func args"""
    def __init__(self, bofh):
        self._bofh = bofh
        self.optional = False
        self.repeat = False
        self.default = None
        self.type = False
        self.help_ref = False
        self.help = "Prompt func"
        self.prompt = False

    def __str__(self):
        return "prompt_func"


# XXX: make a metaclass for commands
class _Command(object):
    """An object representing a bofh command"""
    def __init__(self, group, name, fullname, args):
        self._group = group
        self._bofh = group._bofh
        self._args = args
        self._format_suggestion = None
        self._help = None
        self._fullname = fullname

    def _get_help(self):
        """Get help from bofh, or return cached help string"""
        hlp = self._help
        if hlp is None:
            try:
                hlp = self._help = self._bofh._run_raw_sess_command(
                    "help", self._group._name, self._name)
            except Exception:
                pass
            return hlp
    help = property(_get_help, doc="Get help string for command")

    def _get_format_suggestion(self):
        """Get format suggestion for command"""
        if self._format_suggestion is None:
            self._format_suggestion = self._bofh.get_format_suggestion(
                self._fullname)
        return self._format_suggestion
    format_suggestion = property(_get_format_suggestion,
                                 doc="Get format suggestion")

    def __call__(self, *rest, **kw):
        """Call bofh with args

        :param rest: Arguments to command
        :param kw: {'prompter': promt_function, 'with_format': True or False}
        """
        prompter = kw.pop('prompter', None)
        with_format = bool(kw.pop('with_format', True))

        if prompter:
            args = self.prompt_missing_args(prompter, *rest)
        else:
            args = rest

        try:
            ret = self._bofh.run_command(self._fullname, *args)
        except SessionExpiredError as e:
            if not e.cont:
                raise
            # TODO: What if there's no prompter?
            pw = prompter("You need to reauthenticate\nPassword:", None,
                          "Please type your password", None,
                          'accountPassword')
            self._bofh.login(None, pw, False)
            ret = e.cont()
        logger.debug('got response: %r', ret)

        if with_format:
            formatter = get_formatter(self.format_suggestion)
            logger.debug("formatting response with %r", type(formatter))
            if any(isinstance(i, (list, tuple)) for i in args):
                return [formatter(r) for r in ret]
            else:
                return formatter(ret)

        return ret

    def prompt_missing_args(self, prompt_func, *rest, **kw):
        """Prompts the user for additional args"""
        args = self.args
        logger.debug('prompt_missing_args(%s, *rest, **kw) '
                     'rest=%s, kw=%s, args=%s',
                     repr(prompt_func), repr(rest), repr(kw), repr(args))
        if args and isinstance(args[0], _PromptFunc):
            logger.debug("prompt_missing_args() using _PromptFunc=%s",
                         repr(args[0]))
            return self._prompt_func(prompt_func, *rest, **kw)
        if len(rest) > len(args):
            logger.debug("prompt_missing_args() has enough args (%d > %d)",
                         len(rest), len(args))
            return rest
        has_prompted = False
        ret = []
        rest = list(rest)
        logger.debug("prompt_missing_args() must prompt (got=%d, needs=%d)",
                     len(rest), len(args))
        for i in range(len(rest), len(args)):
            logger.debug('prompt_missing_args() getting arg=%d', i)
            if has_prompted or not args[i].optional:
                has_prompted = True
                arglst = rest + ret
                ans = prompt_func(args[i].prompt,
                                  None,
                                  args[i].help,
                                  self.get_default_param(i, arglst),
                                  args[i].type,
                                  args[i].optional)
                if not ans and args[i].optional:
                    return arglst
                ret.append(ans)
        logger.debug('prompt_missing_args() done, rest=%s, ret=%s',
                     repr(rest), repr(ret))
        return rest + ret

    def get_default_param(self, num, args):
        """Get default param for args[num]"""
        ret = self.args[num].default
        if isinstance(ret, six.string_types):
            return ret
        if ret:
            return self._bofh.get_default_param(self._fullname, args[0:num+1])
        return None

    def _prompt_func(self, prompt_func, *rest, **kw):
        # 1. call_prompt_func with *rest ->
        #   {prompt: string,
        #    help_ref: key,
        #    last_arg: bool,
        #    default: None or value,
        #    map: None or [[["Header", None], value],
        #                  [[format, *args], value],
        #                  ...],
        #    raw: bool}
        # 2. if prompt is None and last_arg is true, return rest
        # 3. if map is not None, transform map into:
        #    newmap = [
        #        (None, map[0][0]),       # header
        #        (i if raw else map[i][1], map[i][0][0] % map[i][0][1]), ...]
        # 4. prompt using string, and, if set, [default], i.e.
        #       prompt_func(prompt, newmap, help text, default)
        # 5. if last_arg is true, return args with appended ans.
        # 6. User's answer is handled by prompt func, append arg to rest and
        #    restart.
        args = list(rest)
        try:
            result = self._bofh.call_prompt_func(self._fullname, *rest)
        except SessionExpiredError as e:
            if not e.cont:
                raise
            pw = prompt_func("You need to reauthenticate\nPassword:", None,
                             "Please type your password", None,
                             'accountPassword')
            self._bofh.login(None, pw, False)
            result = e.cont()
        if result.get('prompt') is None and result.get('last_arg'):
            return args
        map = result.get('map')
        newmap = []
        if map:
            newmap.append((None, map[0][0][0] % tuple(map[0][0][1:]) if '%' in
                          map[0][0][0] else map[0][0][0]))
            i = 1
            for val, key in map[1:]:
                newmap.append((
                    i if result.get('raw') else key,
                    val[0] % tuple(val[1:]) if '%' in val[0] else val[0]))
                i += 1
        ans = ""
        hlp = result.get('help_ref')
        if hlp:
            hlp = self._bofh.arg_help(hlp)
        while ans == "":
            ans = prompt_func(result.get('prompt'),
                              newmap,
                              hlp,
                              result.get('default'))
        # Yes, I have done some functional programming lately
        # It's another way of creating a loop
        if result.get('last_arg'):
            return args + [ans]
        return self._prompt_func(prompt_func, *(args + [ans]))

    @property
    def args(self):
        """
        Return information about each arg

        :return list:
            Returns a list of dicts, where each dict has keys:

            - optional: True if optional
            - repeat: True if arg is repeatable
            - default: string or True if get_default_param should be called
            - type: arg type
            - help_ref: string to send to help_ref
            - prompt: Text to send to prompter for arg
        """
        if hasattr(self, '_fixed_args'):
            ret = self._fixed_args
        elif isinstance(self._args, six.string_types):
            assert self._args == "prompt_func"
            ret = self._fixed_args = (_PromptFunc(self._bofh),)
        else:
            ret = self._fixed_args = tuple(map(
                lambda x: _Argument(self._bofh, x),
                self._args))
        return ret


class _CommandGroup(object):
    """A command group is the first half of a bofh command"""
    def __init__(self, bofh, name):
        self._name = name
        self._bofh = bofh
        self._cmds = dict()

    def _add_command(self, cmd, full_cmd, args):
        command = _Command(self, cmd, full_cmd, args)
        self._cmds[cmd] = command
        setattr(self, cmd, command)

    def get_bofh_command_keys(self):
        """Get the list of group keys"""
        return self._cmds.keys()

    def get_bofh_command_value(self, key):
        return self._cmds.get(key)


class BofhError(Exception):
    """Exceptions from bofhd"""
    def __init__(self, message, cont=None):
        self.cont = cont
        super(BofhError, self).__init__(message)


class SessionExpiredError(BofhError):
    """
    Session has expired.

    Example:

    ::

        try:
            bofh.command()
        except SessionExpiredError as e:
            # log in again to get new session
            bofh.login(username, getpass('Re-authenticate: '))
            if e.cont:
                # call method again
                e.cont()
    """
    pass


class Bofh(object):
    """
    A bofh communication object.

    Bofh performs xmlrpc calls to a remote bofhd server,
    see `<https://www.usit.uio.no/om/tjenestegrupper/cerebrum/>`_.
    """

    def __init__(self, url, context=None, timeout=None):
        """Connect to a bofh server"""
        self._connection = None
        self._groups = dict()
        self._connect(url, context=context, timeout=timeout)

    def _connect(self, url, context=None, timeout=None):
        """Establish a connection with the bofh server"""
        parts = urlparse(url)
        args = {
            'use_datetime': True,
        }
        if timeout is not None:
            args['timeout'] = timeout

        if parts.scheme == 'https':
            args['context'] = context
            self._connection = _xmlrpc.ServerProxy(
                url,
                transport=https.SafeTransport(**args))
        elif parts.scheme == 'http':
            self._connection = _xmlrpc.ServerProxy(
                url,
                transport=https.Transport(**args))
        else:
            raise BofhError("Unsupported protocol: '%s'" % parts.scheme)
        # Test for valid server connection, handle thrown exceptions.
        try:
            self.get_motd()
        except ssl.SSLError as e:
            raise BofhError(e)
        except socket.error as e:
            raise BofhError(e)

    def _run_raw_command(self, name, *args):
        """Run a command on the server"""
        fn = getattr(self._connection, name)

        args = format_args(args)

        try:
            return wash_response(fn(*args))
        except _xmlrpc.Fault as e:
            epkg = 'Cerebrum.modules.bofhd.errors.'
            if e.faultString.startswith(epkg + 'ServerRestartedError:'):
                self._init_commands(reset=True)
                return wash_response(fn(*args))
            elif e.faultString.startswith(epkg + 'SessionExpiredError:'):
                # Should not happen, only in _run_raw_sess_command
                pass
            elif e.faultString.startswith(epkg):
                if ':' in e.faultString:
                    _, msg = e.faultString.split(':', 1)
                    if msg.startswith("CerebrumError: "):
                        _, msg = e.faultString.split(': ', 1)
                    raise BofhError(msg)
            raise

    def _run_raw_sess_command(self, name, *args):
        """Run a command on the server, using the session_id."""
        fn = getattr(self._connection, name)

        args = format_args(args)

        def run_command():
            try:
                return wash_response(fn(self._session, *args))
            except _xmlrpc.Fault as e:
                epkg = 'Cerebrum.modules.bofhd.errors.'
                if e.faultString.startswith(epkg + 'ServerRestartedError:'):
                    self._init_commands(reset=True)
                    return run_command()
                elif e.faultString.startswith(epkg + 'SessionExpiredError:'):
                    raise SessionExpiredError("Session expired",
                                              run_command)
                elif e.faultString.startswith(epkg):
                    if ':' in e.faultString:
                        _, msg = e.faultString.split(':', 1)
                        if msg.startswith("CerebrumError: "):
                            _, msg = e.faultString.split(': ', 1)
                        raise BofhError(msg)
                raise
        return run_command()

    # XXX: There are only a handfull of bofhd commands:
    # motd = get_motd(client_name, version)
    # session = login(user, pass)
    # logout(session)
    # get_commands(session) -- see _init_commands
    # help(session) -- general help
    # help(session, "arg_help", ref) -- help on arg type,
    #                                   ref found in arg['help_ref']
    # help(session, group) -- help on group
    # help(session, group, cmd) -- help on command
    # run_command(session, command, args)  # command = group_cmd
    # call_prompt_func(session, command, args) =>
    #   {prompt: string, help_ref: key, last_arg: bool, default: value,
    #    map: [[["Header", None], value], [[format, *args], value], ...],
    #    raw: bool}
    # get_default_param(session, command, args)
    # get_format_suggestion(command)

    def get_motd(self, client="PyBofh", version=version.version):
        """Get (and cache) message of the day from server"""
        self._motd = wash_response(self._connection.get_motd(client, version))
        return self._motd

    def login(self, user, password, init=True):
        """Log in to server"""
        if user is None:
            user = self._username
        else:
            self._username = user
        self._session = self._run_raw_command("login", user, password)

        if init:
            self._init_commands()

    def logout(self):
        self._run_raw_sess_command("logout")
        self._session = None
        # XXX bring down all commands

    def get_commands(self):
        """Get commands user can operate on"""
        return self._run_raw_sess_command("get_commands")

    def help(self, *args):
        """Get help"""
        return self._run_raw_sess_command("help", *args)

    def arg_help(self, help_ref):
        """Get help on argument"""
        return self.help("arg_help", help_ref)

    def run_command(self, command, *args):
        """Run a regular command"""
        return self._run_raw_sess_command("run_command", command, *args)

    def call_prompt_func(self, command, *args):
        """Call prompt_func"""
        return self._run_raw_sess_command("call_prompt_func", command, *args)

    def get_default_param(self, command, *args):
        """
        Get default value for param.

        Gets the default value for param (where not supplied from get_commands)
        """
        return self._run_raw_sess_command("get_default_param", command, *args)

    def get_format_suggestion(self, command):
        """Get format suggestion for command"""
        return self._run_raw_command("get_format_suggestion", command)

    @property
    def motd(self):
        """Get (cached) message of the day from bofh server"""
        return getattr(self, '_motd', self.get_motd())

    def _init_commands(self, reset=False):
        """
        Initialize commands.

        This calls get_commands to get the list of available commands (note
        that the server can have hidden commands). Then a set of objects are
        built, so that a command as 'user info foo' can be called as
        bofh.user.info('foo')
        """
        if reset:
            for group in self._groups:
                delattr(self, group)
            self._groups = dict()

        cmds = self._connection.get_commands(self._session)
        for key, value in cmds.items():
            # key will typically be a string, e.g. "person_info"
            # value is a list,
            # its first element is a list with the splitted command name,
            # e.g. ["person", "info"]
            group, cmd = value[0]
            args = value[1] if len(value) == 2 else []
            if group not in self._groups:
                grp = _CommandGroup(self, group)
                self._groups[group] = grp
                setattr(self, group, grp)
            self._groups[group]._add_command(cmd, key, args)

    def get_bofh_command_keys(self):
        """Get the list of group keys"""
        return self._groups.keys()

    def get_bofh_command_value(self, key):
        """Lookup group key"""
        return self._groups.get(key)
