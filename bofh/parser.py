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
Implementation of the input command parsing in bofh.

This module implements the input parsing of command strings entered into the
interactive python client.

Parsing input commands are neccessary in order to e.g. provide command
completion.
"""
from __future__ import absolute_import, unicode_literals

import logging
import os

import six

logger = logging.getLogger(__name__)


@six.python_2_unicode_compatible
class SynErr(Exception):
    """Base class for all command syntax errors."""
    def __init__(self, msg, index=None):
        super(SynErr, self).__init__(msg)
        self.index = index
        self.msg = msg

    def __str__(self):
        if self.index is None:
            return "Syntax error"
        return "Syntax error at col %s: %s" % (self.index, self.msg)


class IncompleteParse(SynErr):
    """Parser ran off end without finding matching " or )"""

    def __init__(self, msg, parse, expected):
        super(IncompleteParse, self).__init__(msg, -1)
        self.parse = parse
        self.completions = expected


class NoGroup(SynErr):
    """
    The group didn't match any defined command

    Note that this error is also raised when an incomplete command with
    multiple matches are given.
    """
    # TODO: This should be renamed, e.g. to NoCommand()

    def __init__(self, parse, completions):
        super(NoGroup, self).__init__("No matching command", 0)
        self.parse = parse
        self.completions = completions


class Command(object):
    """Base class for commands returned by :func:`parse`"""

    def __init__(self, bofh, line):
        self.args = []
        self.bofh = bofh
        self.line = line

    def append(self, arg, index, complete):
        """
        Append a parsed argument.

        :param arg: argument value to add
        :param index: starting point where arg was found, or -1 for missing
        :param complete: an object to use by the completer
        """
        self.args.append((arg, index, complete))

    def complete(self, start, end):
        """Get completions for argument"""
        arg = self.findarg(start, end)
        logger.debug('%s.complete(%s, %s) -> arg=%s',
                     type(self).__name__, repr(start), repr(end), repr(arg))
        if isinstance(arg[2], (list, tuple, set)):
            return arg[2]
        else:
            return arg[2](start, end, *arg)

    def findarg(self, start, end):
        """Lookup an arg in the mentioned position"""
        for i in self.args:
            if i[1] == start:
                return i
            if isinstance(i[0], (list, tuple, set)):
                for j in i[0]:
                    if j[0] == start:
                        return j
            if i[1] == -1 and start == end == len(self.line):
                return i
        return None, -1, []

    def eval(self, prompter=None):
        """
        Evaluate the parsed expression.

        :param prompter: Callable to get single input item
        """
        return "Command: '{}' not implemented".format(
            " ".join(x[0] for x in self.args))

    def call(self):
        return self.eval()


def _prepare_args(args):
    """
    Iterate over arguments.

    :param args:
        A sequence of parsed argument tuples.
        Each tuple should contain (arg, index, completer).
    """
    for arg, pos, _ in args:
        if pos == -1:
            continue
        elif isinstance(arg, (list, tuple, set)):
            inner = []
            for j, _ in arg:
                inner.append(j)
            yield inner
        else:
            yield arg


class BofhCommand(Command):
    """Parser representation of a bofh command."""

    def set_command(self, command):
        """
        Set command implementation

        :type command: bofh.proto._Command
        """
        self.command = command

    def eval(self, prompter=None, *rest, **kw):
        """
        Evaluate the parsed expression.

        :param prompter: Callable to get single input item
        """
        # Prepare arguments -- the first two elements in self.args is the
        # command group and the command name
        args = tuple(_prepare_args(self.args[2:]))
        try:
            return self.command(prompter=prompter, *args)
        except AttributeError:
            logger.debug("unable to run %r with %r",
                         self.command, args, exc_info=True)
            # TODO: This is probably the wrong exception to re-raise
            raise NoGroup(None, args)


class InternalCommand(Command):
    """A command object for an internal command."""

    def eval(self, *rest, **kw):
        """
        Evaluate internal commands.

        Finds command in :py:mod:`bofh.internal_commands`, and calls it.
        """
        from . import internal_commands as where
        args = list(_prepare_args(self.args))
        cmdname = args.pop(0)
        cmdref = getattr(where, cmdname)
        return cmdref(self.bofh, *args)


class HelpCommand(InternalCommand):
    """Help command"""
    pass


class SingleCommand(InternalCommand):
    """An internal command taking no args"""

    def __init__(self, bofh, fullcmd, cmd, index, line):
        super(SingleCommand, self).__init__(bofh, line)
        self.command = cmd
        self.index = index
        self.args = [(cmd, index, [fullcmd])]
        from . import internal_commands as where
        self.cmdref = getattr(where, fullcmd)

    def eval(self, *rest, **kw):
        return self.cmdref(self.bofh)


class FileCompleter(object):
    """Some of the commands takes file as a param. Complete this"""
    # XXX: Is this maybe standard in readline?
    def __call__(self, start, end, arg, argstart, completions):
        return []  # glob(arg + '*') or better


class ArgCompleter(object):
    """Try to complete some arguments"""
    def __init__(self, arg):
        self.arg = arg

    def __call__(self, start, end, arg, argstart, completions):
        return []  # perhaps do something here based on arg type


def _is_file(fname):
    """Quick check if fname is the name of a readable file"""
    fname = os.path.realpath(fname)
    return os.path.exists(fname) and os.path.isfile(fname)


def _parse_bofh_command(bofh, fullgrp, group, start, lex, line):
    """
    Parse the rest of a bofh command.

    When we've identified the first argument to be a command group, this parse
    function helps parsing the command name within that group.

    :type bofh: bofh.proto.Bofh

    :type fullgrp: six.text_type
    :param fullgrp: The command group name

    :type group: six.text_type
    :param group: Partial or full name of a command within the command group

    :type start: int
    :param start: Index of the first char on the line

    :type lex: generator
    :param lex: A :func:`lexer` generator

    :type line: six.text_type
    :param line: The line to parse

    :rtype: BofhCommand
    :returns: An XMLRPC command with arguments.

    :raises: SynErr
    """
    logger.debug('_parse_bofh_command(%r, %r, %r, %r, %r, %r)',
                 bofh, fullgrp, group, start, lex, line)
    # Setup return object
    grp = getattr(bofh, fullgrp)
    ret = BofhCommand(bofh, line)  # XXX: Args
    ret.append(group, start, [fullgrp])

    # Find second half of the command
    group_cmds = get_bofh_commands(bofh, fullgrp)
    try:
        cmd, idx, fltrcmds, solematch = parse_string(lex, group_cmds)
    except IncompleteParse as e:
        ret.append("", -1, group_cmds)
        raise IncompleteParse(e.args[0], ret, e.completions)

    ret.append(cmd, idx, fltrcmds)

    # found, parse arguments
    if solematch:
        cmd_obj = getattr(grp, solematch)
        ret.set_command(cmd_obj)
        for expected in cmd_obj.args:
            try:
                arg, idx = parse_string_or_list(lex)
                ret.append(arg, idx, ArgCompleter(expected))
            except IncompleteParse as e:  # arg, idx = e.parse
                if e.parse:
                    arg, idx = e.parse
                    ret.append(arg, idx, ArgCompleter(expected))
                # TODO/TBD: use e.completions?
                ret.append("", -1, ArgCompleter(expected))
        try:
            while True:
                arg, idx = parse_string_or_list(lex)
                ret.append(arg, idx, [])
        except IncompleteParse as e:
            if e.parse:
                arg, idx = parse_string_or_list(lex)
                ret.append(arg, idx, ArgCompleter(expected))
                raise IncompleteParse(e.args[0], ret, e.completions)
    return ret


def _parse_help(bofh, fullgrp, group, start, lex, line):
    """
    Parse the help command.

    When we've identified the first argument to be the 'help' command, this
    parse function helps parsing the command or command group to get help for.

    See :func:`_parse_bofh_command` for an explanation of the arguments.

    :rtype: HelpCommand
    """
    logger.debug('_parse_help(%r, %r, %r, %r, %r, %r)',
                 bofh, fullgrp, group, start, lex, line)
    ret = HelpCommand(bofh, line)
    ret.append(group, start, [fullgrp])
    args = []
    while True:
        try:
            arg, idx = parse_string_or_list(lex)
            args.append((arg, idx))
        except IncompleteParse as e:
            # XXX: handle better
            if e.parse:
                args.append(e.parse)
            break

    localcmds = get_internal_commands()
    if len(args) > 2:
        raise SynErr("Too many arguments for help", args[2][1])

    bofhcmds = get_bofh_commands(bofh)
    allcmds = localcmds + bofhcmds

    if len(args) == 0:
        # No arguments - all commands/groups are valid completions
        ret.append('', -1, allcmds)
        return ret

    if len(args) <= 2:
        def match_item(cmd, expected):
            if isinstance(cmd[0], (list, tuple, set)):
                return (
                    tuple(map(lambda x: match_item(x, expected), cmd[0])),
                    cmd[1],
                    [],
                )
            return (
                cmd[0],
                cmd[1],
                list(filter(lambda x: x.startswith(cmd[0]), expected)),
            )

        cmd, idx, completes = match_item(args[0], allcmds)
        ret.append(cmd, idx, completes)

        if len(completes) != 1:  # no completion for second arg
            if len(args) == 2:
                ret.append(args[1][0], args[1][1], [])
        else:
            grp = bofh.get_bofh_command_value(*completes)
            if grp:
                grpcmds = tuple(sorted(grp.get_bofh_command_keys()))
                if len(args) == 2:
                    cmd, idx, completes = match_item(args[1], grpcmds)
                    ret.append(cmd, idx, completes)
                else:
                    ret.append(None, -1, grpcmds)
            elif completes[0] in _internal_cmds:
                if len(args) == 1:
                    pass
                else:
                    raise SynErr("Too many arguments for help", args[1][1])
            else:
                # incomplete, find group/internal command
                pass
    return ret


def _parse_script(bofh, fullgrp, group, start, lex, line):
    """
    Parse the 'script' internal command

    When we've identified the first argument to be the 'script' command, this
    parse function helps parsing the remaining arguments for that command.

    See :func:`_parse_bofh_command` for an explanation of the arguments.

    :rtype: InternalCommand
    """
    logger.debug('_parse_script(%r, %r, %r, %r, %r, %r)',
                 bofh, fullgrp, group, start, lex, line)
    ret = InternalCommand(bofh, line)
    ret.append(group, start, [fullgrp])
    args = []
    while True:
        try:
            arg, idx, _, _ = parse_string(lex)
            args.append((arg, idx))
        except IncompleteParse:
            # XXX: handle better
            break
    if len(args) > 1:
        raise SynErr("Too many arguments for script", args[1][1])
    elif len(args) == 1:
        if _is_file(arg):
            ret.append(arg, idx, [arg])
        else:
            ret.append(arg, idx, FileCompleter())
    else:
        ret.append(None, -1, FileCompleter())
    return ret


def _parse_source(bofh, fullgrp, group, start, lex, line):
    """
    Parse the 'source' internal command.

    When we've identified the first argument to be the 'source' command, this
    parse function helps parsing the remaining arguments for that command.

    See :func:`_parse_bofh_command` for an explanation of the arguments.

    :rtype: InternalCommand
    """
    logger.debug('_parse_source(%r, %r, %r, %r, %r, %r)',
                 bofh, fullgrp, group, start, lex, line)
    ret = InternalCommand(bofh, line)
    ret.append(group, start, [fullgrp])
    args = []
    while True:
        try:
            arg, idx = parse_string_or_list(lex)
            args.append((arg, idx))
        except IncompleteParse:
            # XXX: handle better
            break
    if len(args) == 0:
        ret.append(None, -1, FileCompleter())
    elif len(args) == 1:
        # XXX: Have a filecompleter that also expands --ignore-errors?
        if '--ignore-errors'.startswith(args[0][0]):
            ret.append(args[0][0], args[0][1], ['--ignore-errors'])
        elif _is_file(args[0][0]):
            ret.append(None, None, [])
            ret.append(args[0][0], args[0][1], [args[0][0]])
        else:
            ret.append(None, None, [])
            ret.append(arg, idx, FileCompleter())
    elif len(args) == 2:
        if '--ignore-errors'.startswith(args[0][0]):
            ret.append(args[0][0], idx, ['--ignore-errors'])
        else:
            raise SynErr("Expected --ignore-errors, found %s" %
                         args[0][0], args[0][1])
        ret.append(arg, idx, FileCompleter())
    else:
        raise SynErr("Too many arguments for source", args[2][1])
    return ret


def _parse_single(bofh, fullgrp, group, start, lex, line):
    """
    Parse (internal) commands without arguments.

    When we've identified the first argument to be an internal command that
    does not take any arguments, this function immediately returns a
    SingleCommand() reperesentation of that command.

    See :func:`_parse_bofh_command` for an explanation of the arguments.

    :rtype: SingleCommand
    """
    logger.debug('_parse_single(%r, %r, %r, %r, %r, %r)',
                 bofh, fullgrp, group, start, lex, line)
    return SingleCommand(bofh, fullgrp, group, start, line)


# table of internal commands, see also internal_commands.py
# TODO: This should probably be linked with internal_commands in some other
#       way?
_internal_cmds = {
    'commands': _parse_single,
    'help': _parse_help,
    'quit': _parse_single,
    'script': _parse_script,
    'source': _parse_source,
}


def get_bofh_commands(bofh, groupname=None):
    if groupname is not None:
        bofh = getattr(bofh, groupname)
    return tuple(sorted(bofh.get_bofh_command_keys()))


def get_internal_commands():
    return tuple(sorted(_internal_cmds.keys()))


def parse(bofh, text):
    """
    Parses a command

    :type text: six.text_type
    :param text: A text string to parse.
    """
    lex = lexer(text)
    localcmds = get_internal_commands()
    bofhcmds = get_bofh_commands(bofh)
    allcmds = localcmds + bofhcmds
    try:
        group, idx, fltrcmds, solematch = parse_string(lex, allcmds)
    except IncompleteParse:
        logger.debug("issue parsing %r", text, exc_info=True)
        raise NoGroup(None, allcmds)

    if solematch:
        fullgrp = solematch
    else:
        fullgrp = group

    if solematch and fullgrp in bofhcmds:
        return _parse_bofh_command(bofh, fullgrp, group, idx, lex, text)

    if solematch:
        _parse_match = _internal_cmds.get(fullgrp)
        return _parse_match(bofh, fullgrp, group, idx, lex, text)

    rest = [i for i in lex]
    rest.insert(0, (group, idx))
    raise NoGroup(rest, fltrcmds)


def parse_string(lex, expected=None):
    """
    Get a string from lex, fail on list, and return possible matches

    :param lex: A :func:`lexer` generator
    :param expected: A sequence of valid values

    :rtype: tuple
    :returns:
        Returns a tuple with:

        0. Parsed string
        1. Index of parsed string
        2. list of matches
        3. A match for parsed string in expected

    :raises SynErr: If read item is a paren
    """
    expected = expected or tuple()
    try:
        val, idx = next(lex)
    except StopIteration:
        raise IncompleteParse("Expected string, got nothing", "",
                              expected)
    if idx == -1:
        # XXX: Do sane stuff here
        raise IncompleteParse("Expected %r, got nothing" % (val,), "",
                              expected)
    if val in ('(', ')'):
        raise SynErr("Expected string, got %r" % (val,), idx)
    expected = tuple(value for value in expected if value.startswith(val))
    if len(expected) == 1:
        solematch = expected[0]
    elif val in expected:
        solematch = val
    else:
        solematch = False
    return val, idx, expected, solematch


def parse_string_or_list(lex):
    """Get a string or list of strings from lexer"""
    def parse_list():
        # parse until we get a )
        ret = []
        for val, idx in lex:
            if idx == -1:
                # signals missing char after \ or missing matching ".
                try:
                    # gets either ", -1 or some last token
                    val1, idx1 = next(lex)
                except StopIteration:  # no last token
                    raise IncompleteParse(
                        "Expected %s, got nothing" %
                        ("something" if val == '\\' else ')'),
                        ret, [])
                if idx1 == -1:  # signal we want both a \ ending and a "
                    try:  # check if the last token waits.
                        val1, idx1 = next(lex)
                        ret.append((val1, idx1))
                        raise IncompleteParse(
                            "Expected something and \", got nothing",
                            ret, [' ")'])
                    except StopIteration:
                        raise IncompleteParse(
                            "Expected something and \", got nothing",
                            ret, [' ")'])
                else:
                    # val1, idx1 holds the last token
                    ret.append((val1, idx1))
                    raise IncompleteParse(
                        "Expected %s, got nothing" %
                        ("something" if val == "\\" else ')'),
                        ret, [' )' if val == "\\" else '")'])
            elif val == '(':
                # we don't know what to do
                # XXX: should we continue parsing?
                raise SynErr("Nested list expression", idx)
            elif val == ')':
                return ret
            ret.append((val, idx))
        raise IncompleteParse("Expected ), got nothing", ret, [])

    try:
        val, idx = next(lex)
    except StopIteration:
        raise IncompleteParse(
            "Expected string or list, got nothing", None, [])
    if idx == -1:
        try:
            val1, idx1 = next(lex)
        except StopIteration:  # no last token
            raise IncompleteParse(
                "Expected %s, got nothing" %
                ("something" if val == '\\' else '"'),
                None, [' ' if val == '\\' else '"'])
        if idx1 == -1:  # signal we want both a \ ending and a "
            try:  # check if the last token waits.
                val1, idx1 = next(lex)
                raise IncompleteParse(
                    "Expected something and \", got nothing",
                    (val1, idx1), [' "'])
            except StopIteration:
                raise IncompleteParse(
                    "Expected something and \", got nothing",
                    None, [' "'])
        else:  # val1, idx1 holds the last token
            raise IncompleteParse(
                "Expected %s, got nothing" %
                ("something" if val == "\\" else ')'),
                (val1, idx1), [' ' if val == '\\' else '"'])
    elif val == '(':
        try:
            return parse_list(), idx
        except IncompleteParse as e:
            e.parse = (e.parse, idx)
            raise
    else:
        return val, idx


def lexer(text):
    """
    Generates tokens from the text

    :type text: six.text_type
    :param text: The text to tokenize.

    :rtype: generator
    :returns:
        A generator that yields (token, offset) pairs.

    >>> list(lexer(u'group info foo'))
    [(u'group', 0), (u'info', 6), (u'foo', 11)]
    """
    if not isinstance(text, six.text_type):
        raise TypeError("invalid type %s, expected %s" %
                        (type(text).__name__, six.text_type.__name__))
    ret = []
    start = 0
    inquotes = False
    internalquotes = False
    backslash = False
    for i, cur in enumerate(text):
        if backslash:
            if not ret:
                start = i - 1
            ret.append(cur)
            backslash = False
        elif inquotes:
            if cur == '"':
                inquotes = False
                if not internalquotes:
                    internalquotes = False
                    yield ''.join(ret), start
                    ret = []
            else:
                ret.append(cur)
        elif cur == '(' or cur == ')':
            if ret:
                yield ''.join(ret), start
                ret = []
            yield cur, i
        elif cur == '"':
            inquotes = True
            internalquotes = bool(ret)
            if not internalquotes:
                start = i
        elif cur.isspace():
            if ret:
                yield ''.join(ret), start
                ret = []
                # yield ' ', i
        elif cur == '\\':
            backslash = True
        else:
            if not ret:
                start = i
            ret.append(cur)
    if backslash:
        yield '\\', -1
    if inquotes:
        yield '"', -1
    if ret:
        yield ''.join(ret), start
