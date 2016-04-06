#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010-2015 University of Oslo, Norway
#
# This file is part of PyBofh.
#
# PyBofh is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBofh is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBofh; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
u"""Module to communicate with bofh server."""

import xmlrpclib as _rpc
from urlparse import urlparse
from . import version
from .https import BofhTransport
import socket
import ssl


def _sdt2strftime(format):
    """Simple thing to convert java's simple date format to strftime"""
    #       (subst, with),
    reps = ((u"yyyy", u"%Y"),
            (u"MM", u"%m"),
            (u"dd", u"%d"),
            (u"HH", u"%H"),
            (u"mm", u"%M"))
    return reduce(lambda form, rep: form.replace(*rep), reps, format)


def _washresponse(resp):
    """Wash response
    Walk down any objects in response (we can get strings, dicts and lists),
    and make sure any strings are unicode. Also, we code None as ':None',
    and escapes other colon at start of string with an extra colon

    >>> _washresponse(":None")
    >>> _washresponse("::None")
    u':None'
    >>> _washresponse(["None", ":None", "::None"])
    [u'None', None, u':None']
    """
    if isinstance(resp, basestring):
        if resp and resp[0] == ':':
            return None if resp == ':None' else resp[1:]
        return unicode(resp, "ISO-8859-1") if isinstance(resp, str) else resp
    elif isinstance(resp, (list, tuple)):
        return [_washresponse(x) for x in resp]
    elif isinstance(resp, dict):
        for i in resp.keys():
            resp[i] = _washresponse(resp[i])
        return resp
    else:
        return resp


def parse_format_suggestion(bofh_response, format_sugg):
    """Transform a response from bofh to a string after
    the spec of a format suggestion.

    :param bofh_response: Response from bofh, washed with _washresponse
    :param format_sugg: Format suggestion"""
    # XXX: Explain syntax of format suggestions
    def get_formatted_field(map, field):
        field = field.split(":", 2)
        val = map[field[0]]
        if len(field) == 3:
            if field[1] == 'date':
                format = _sdt2strftime(field[2])
            else:
                raise KeyError(field[1])
            if val is not None:
                return val.strftime(format.encode("ASCII"))
        if val is None:
            return u"<not set>"
        return val

    # Handle missing format_suggestion
    if not format_sugg:
        if isinstance(bofh_response, basestring):
            return bofh_response
        else:
            return repr(bofh_response)

    lst = []
    if "hdr" in format_sugg:
        lst.append(format_sugg["hdr"])
    st = format_sugg['str_vars']
    if isinstance(st, basestring):
        lst.append(st)
    else:
        for row in st:
            if len(row) == 3:
                format, vars, sub_hdr = row
                if u"%" in sub_hdr:
                    format, sub_hdr = sub_hdr, None
            else:
                format, vars = row
                sub_hdr = None
            if sub_hdr:
                lst.append(sub_hdr)
            if not isinstance(bofh_response, (list, tuple)):
                bofh_response = [bofh_response]
            for i in bofh_response:
                if isinstance(i, basestring):
                    lst.append(i)
                    continue
                try:
                    positions = tuple(get_formatted_field(i, j) for j in vars)
                except KeyError:
                    continue
                lst.append(format % positions)
    return u"\n".join(lst)


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

    def __unicode__(self):
        stuff = ('type', 'optional', 'default')
        return (u"{" +
                u", ".join(map(lambda x: x + u": %(" + x + u")s", stuff)) +
                u"}") % self.__dict__


class _PromptFunc(object):
    """Parameter specifier for prompt_func args"""
    def __init__(self, bofh):
        self._bofh = bofh
        self.optional = False
        self.repeat = False
        self.default = None
        self.type = False
        self.help_ref = False
        self.help = u"Prompt func"
        self.prompt = False

    def __unicode__(self):
        return u"prompt_func"


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
            except:
                pass
            return hlp
    help = property(_get_help, doc=u"Get help string for command")

    def _get_format_suggestion(self):
        """Get format suggestion for command"""
        if self._format_suggestion is None:
            self._format_suggestion = self._bofh.get_format_suggestion(self._fullname)
        return self._format_suggestion
    format_suggestion = property(_get_format_suggestion,
                                 doc=u"Get format suggestion")

    def __call__(self, *rest, **kw):
        """Call bofh with args

        :param rest: Arguments to command
        :param kw: {'prompter': promt_function, 'with_format': True or False}
        """
        promptfunc = kw.get('prompter')
        if promptfunc:
            args = self.prompt_missing_args(promptfunc, *rest)
        else:
            args = rest
        try:
            ret = self._bofh.run_command(self._fullname, *args)
        except SessionExpiredError, e:
            if not e.cont:
                raise
            pw = promptfunc(u"You need to reauthenticate\nPassword:", None,
                            u"Please type your password", None,
                            'accountPassword')
            self._bofh.login(None, pw, False)
            ret = e.cont()

        with_format = not ('with_format' in kw and not kw['with_format'])

        if with_format and not isinstance(ret, basestring):
            for i in args:
                if isinstance(i, (list, tuple)):
                    return u'\n'.join(
                        map(lambda x: parse_format_suggestion(
                            x, self.format_suggestion), ret))
            return parse_format_suggestion(ret, self.format_suggestion)
        return ret

    def prompt_missing_args(self, prompt_func, *rest, **kw):
        """Prompts the user for additional args"""
        args = self.args
        if args and isinstance(args[0], _PromptFunc):
            return self._prompt_func(prompt_func, *rest, **kw)
        if len(rest) > len(args):
            return rest
        has_prompted = False
        ret = []
        rest = list(rest)
        for i in range(len(rest), len(args)):
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
        return rest + ret

    def get_default_param(self, num, args):
        """Get default param for args[num]"""
        ret = self.args[num].default
        if isinstance(ret, basestring):
            return ret
        if ret:
            return self._bofh.get_default_param(self._fullname, args[0:num+1])
        return None

    def _prompt_func(self, prompt_func, *rest, **kw):
        # 1. call_prompt_func with *rest -> 
        #   {prompt: string, help_ref: key, last_arg: bool, default: None or value,
        #    map: None or [[["Header", None], value], [[format, *args], value], ...],
        #    raw: bool}
        # 2. if prompt is None and last_arg is true, return rest
        # 3. if map is not None, transform map into:
        #    newmap = [(None, map[0][0]),       # header
        #              (i if raw else map[i][1], map[i][0][0] % map[i][0][1]), ...]
        # 4. prompt using string, and, if set, [default], i.e. 
        #       prompt_func(prompt, newmap, help text, default)
        # 5. if last_arg is true, return args with appended ans.
        # 6. User's answer is handled by prompt func, append arg to rest and restart.
        args = list(rest)
        try:
            result = self._bofh.call_prompt_func(self._fullname, *rest)
        except SessionExpiredError, e:
            if not e.cont:
                raise
            pw = prompt_func(u"You need to reauthenticate\nPassword:", None,
                             u"Please type your password", None,
                             'accountPassword')
            self._bofh.login(None, pw, False)
            result = e.cont()
        if result.get('prompt') is None and result.get('last_arg'):
            return args
        map = result.get('map')
        newmap = []
        if map:
            newmap.append((None, map[0][0][0] % tuple(map[0][0][1:]) if u'%' in
                          map[0][0][0] else map[0][0][0]))
            i = 1
            for val, key in map[1:]:
                newmap.append((
                    i if result.get('raw') else key,
                    val[0] % tuple(val[1:]) if u'%' in val[0] else val[0]))
                i += 1
        ans = u""
        hlp = result.get('help_ref')
        if hlp:
            hlp = self._bofh.arg_help(hlp)
        while ans == u"":
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
        """Return information about each arg
        Returns a list of dicts: {
            optional: True if optional
            repeat: True if arg is repeatable
            default: string or True if get_default_param should be called
            type: arg type
            help_ref: string to send to help_ref
            prompt: Text to send to prompter for arg
        }"""
        if hasattr(self, '_fixed_args'):
            return self._fixed_args
        if isinstance(self._args, basestring):
            assert self._args == u"prompt_func"
            ret = self._fixed_args = [_PromptFunc(self._bofh)]
            return ret
        ret = self._fixed_args = map(lambda x: _Argument(self._bofh, x),
                                     self._args)
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
        u"""Get the list of group keys"""
        return self._cmds.keys()

    def get_bofh_command_value(self, key):
        return self._cmds.get(key)


class BofhError(Exception):
    u"""Exceptions from bofhd"""
    def __init__(self, message, cont=None):
        self.cont = cont
        super(BofhError, self).__init__(message)


class SessionExpiredError(BofhError):
    u"""Session has expired.

    This should probably be handled like this:

        try:
            bofh.command()
        except SessionExpiredError, e:
            bofh.login(username, getpass()) # log in again to get new session
            if e.cont:
                e.cont()  # call method again

    """
    pass


class Bofh(object):
    u"""A bofh communication object.

    Bofh performs xmlrpc calls to a remote bofhd server,
    see http://cerebrum.sourceforge.net

    """
    def __init__(self, url, cert, insecure=False):
        u"""Connect to a bofh server"""
        self._connection = None
        self._groups = dict()
        self._connect(url, cert, insecure)

    def _connect(self, url, cert=None, insecure=False):
        u"""Establish a connection with the bofh server"""
        parts = urlparse(url)

        if parts.scheme == 'https':
            self._connection = _rpc.Server(
                url,
                transport=BofhTransport(cert, use_datetime=True,
                                        validate_hostname=not insecure))
        elif parts.scheme == 'http':
            self._connection = _rpc.Server(
                url,
                transport=_rpc.Transport(use_datetime=True))
        else:
            raise BofhError("Unsupported protocol: '%s'" % parts.scheme)
        # Test for valid server connection, handle thrown exceptions.
        try:
            self.get_motd()
        except ssl.SSLError, e:
            raise BofhError(e)
        except socket.error, e:
            raise BofhError(e)

    def _run_raw_command(self, name, *args):
        u"""Run a command on the server"""
        fn = getattr(self._connection, name)

        args = self.format_args(args)

        try:
            return _washresponse(fn(*args))
        except _rpc.Fault, e:
            epkg = 'Cerebrum.modules.bofhd.errors.'
            if e.faultString.startswith(epkg + 'ServerRestartedError:'):
                self._init_commands(reset=True)
                return _washresponse(fn(*args))
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
        u"""Run a command on the server, using the session_id."""
        fn = getattr(self._connection, name)

        args = self.format_args(args)

        def run_command():
            try:
                return _washresponse(fn(self._session, *args))
            except _rpc.Fault, e:
                epkg = 'Cerebrum.modules.bofhd.errors.'
                if e.faultString.startswith(epkg + 'ServerRestartedError:'):
                    self._init_commands(reset=True)
                    return _washresponse(fn(self._session, *args))
                elif e.faultString.startswith(epkg + 'SessionExpiredError:'):
                    raise SessionExpiredError(u"Session expired",
                                              run_command)
                elif e.faultString.startswith(epkg):
                    if ':' in e.faultString:
                        _, msg = e.faultString.split(':', 1)
                        if msg.startswith("CerebrumError: "):
                            _, msg = e.faultString.split(': ', 1)
                        raise BofhError(msg)
                raise
        return run_command()

    def format_args(self, args):
        u"""Add additional ':' if an argument is a basestring and starts with 
        ':', as this will get sliced off by xmlutils.py in backend."""
        argslist = list(args)
        pos = 0
        for arg in argslist:
            if isinstance(arg, basestring) and arg.startswith(':'):
                argslist[pos] = ':' + arg
            pos += 1
        return tuple(argslist)

    # XXX: There are only a handfull of bofhd commands:
    # motd = get_motd(client_name, version)
    # session = login(user, pass)
    # logout(session)
    # get_commands(session) -- see _init_commands
    # help(session) -- general help
    # help(session, "arg_help", ref) -- help on arg type, ref found in arg['help_ref']
    # help(session, group) -- help on group
    # help(session, group, cmd) -- help on command
    # run_command(session, command, args)  # command = group_cmd
    # call_prompt_func(session, command, args) =>
    #   {prompt: string, help_ref: key, last_arg: bool, default: value,
    #    map: [[["Header", None], value], [[format, *args], value], ...],
    #    raw: bool}
    # get_default_param(session, command, args)
    # get_format_suggestion(command)

    def get_motd(self, client=u"PyBofh", version=version.version):
        u"""Get (and cache) message of the day from server"""
        self._motd = _washresponse(self._connection.get_motd(client, version))
        return self._motd

    def login(self, user, password, init=True):
        u"""Log in to server"""
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
        u"""Get commands user can operate on"""
        return self._run_raw_sess_command("get_commands")

    def help(self, *args):
        u"""Get help"""
        return self._run_raw_sess_command("help", *args)

    def arg_help(self, help_ref):
        u"""Get help on argument"""
        return self.help("arg_help", help_ref)

    def run_command(self, command, *args):
        u"""Run a regular command"""
        return self._run_raw_sess_command("run_command", command, *args)

    def call_prompt_func(self, command, *args):
        u"""Call prompt_func"""
        return self._run_raw_sess_command("call_prompt_func", command, *args)

    def get_default_param(self, command, *args):
        u"""Get default value for param.

        Gets the default value for param (where not supplied from get_commands)

        """
        return self._run_raw_sess_command("get_default_param", command, *args)

    def get_format_suggestion(self, command):
        u"""Get format suggestion for command"""
        return self._run_raw_command("get_format_suggestion", command)

    @property
    def motd(self):
        u"""Get (cached) message of the day from bofh server"""
        return getattr(self, '_motd', self.get_motd())

    def _init_commands(self, reset=False):
        u"""Initialize commands.

        This calls get_commands to get the list of available commands (note
        that the server can have hidden commands). Then a set of objects are
        built, so that a command as 'user info foo' can be called as
        bofh.user.info(u'foo')

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
        u"""Get the list of group keys"""
        return self._groups.keys()

    def get_bofh_command_value(self, key):
        u"""Lookup group key"""
        return self._groups.get(key)
