# -*- coding: utf-8 -*-

# Copyright 2010 University of Oslo, Norway
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

u"""This is the PyBofh command parser"""

class SynErr(Exception):
    u"""Syntax error"""
    def __init__(self, msg, index=None):
        super(Exception, self).__init__(msg)
        self.index = index

class IncompleteParse(SynErr):
    u"""Parser ran off end without finding matching " or )"""
    def __init__(self, msg, parse, expected):
        super(SynErr, self).__init__(msg, -1)
        self.parse = parse
        self.completions = expected

class NoGroup(SynErr):
    u"""The group didn't match any defined command"""
    def __init__(self, parse, completions):
        self.parse = parse
        self.completions = completions

class Command(object):
    def __init__(self, bofh, line):
        self.args = []
        self.bofh = bofh
        self.line = line

    def append(self, arg, index, complete):
        self.args.append((arg, index, complete))

    def complete(self, start, end):
        import sys
        arg = self.findarg(start, end)
        if isinstance(arg[2], list):
            return arg[2]
        else:
            return arg[2](start, end, *arg)

    def findarg(self, start, end):
        for i in self.args:
            if i[1] == start:
                return i
            if isinstance(i[0], (list, tuple)):
                for j in i[0]:
                    if j[0] == start:
                        return j
            if i[1] == -1 and start == end == len(self.line):
                return i
        return None, -1, []

    def eval(self, prompter=None):
        """Evaluate the parsed expression.
        prompter: Callable to get single input item
        """
        return u"Command: «%s» not implemented" % u" ".join(map(lambda x: x[0], self.args))

    def call(self):
        return self.eval()


class BofhCommand(Command):
    def set_command(self, command):
        self.command = command

    def get_args(self):
        ret = []
        for arg, pos, _ in self.args[2:]:
            if pos == -1:
                pass
            elif isinstance(arg, (list, tuple)):
                inner = []
                for j, _ in arg:
                    inner.append(j)
                ret.append(inner)
            else:
                ret.append(arg)
        return ret

    def eval(self, prompter=None, *rest, **kw):
        """Evaluate the parsed expression.
        prompter: Callable to get single input item
        """
        args = self.get_args()
        return self.command(prompter=prompter, *args)

class InternalCommand(Command):
    def eval(self, *rest, **kw):
        from . import internal_commands as where
        cmdname = self.args[0][2][0]
        cmdref = getattr(where, cmdname)
        args = [x[0] for x in self.args[1:] if x[1] != -1]
        return cmdref(self.bofh, *args)

class HelpCommand(InternalCommand):
    def get_args(self):
        ret = []
        for arg, pos, _ in self.args[1:]:
            if pos == -1:
                pass
            elif isinstance(arg, (list, tuple)):
                inner = []
                for j, _, _ in arg:
                    inner.append(j)
                ret.append(inner)
            else:
                ret.append(arg)
        return ret

    def eval(self, *rest, **kw):
        from . import internal_commands as where
        cmdname = self.args[0][2][0]
        cmdref = getattr(where, cmdname)
        args = self.get_args()
        return cmdref(self.bofh, *args)

class SingleCommand(InternalCommand):
    def __init__(self, bofh, fullcmd, cmd, index, line):
        super(InternalCommand, self).__init__(bofh, line)
        self.command = cmd
        self.index = index
        self.args = [(cmd, index, [fullcmd])]
        from . import internal_commands as where
        self.cmdref = getattr(where, fullcmd)

    def eval(self, *rest, **kw):
        from . import internal_commands as where
        return self.cmdref(self.bofh)

class FileCompleter(object):
    # XXX: Is this maybe standard in readline?
    def __call__(self, start, end, arg, argstart, completions):
        return [] # glob(arg + '*') or better

class ArgCompleter(object):
    def __init__(self, arg):
        self.arg = arg

    def __call__(self, start, end, arg, argstart, completions):
        return [] # perhaps do something here based on arg type

def _r(fname):
    import os.path
    fname = os.path.realpath(fname)
    return os.path.exists(fname) and os.path.isfile(fname)

def _parse_bofh_command(bofh, fullgrp, group, start, lex, line):
    grp = getattr(bofh, fullgrp)
    ret = BofhCommand(bofh, line) # XXX: Args
    ret.append(group, start, [fullgrp])
    allcmds = grp.get_bofh_command_keys()
    try:
        cmd, idx, fltrcmds, solematch = parse_string(lex, allcmds)
    except IncompleteParse, e:
        ret.append(u"", -1, allcmds)
        raise IncompleteParse(e.message, ret, e.completions)

    ret.append(cmd, idx, fltrcmds)
    if solematch:
        cmd_obj = getattr(grp, solematch)
        ret.set_command(cmd_obj)
        for expected in cmd_obj.args:
            try:
                arg, idx = parse_string_or_list(lex)
                ret.append(arg, idx, ArgCompleter(expected))
            except IncompleteParse, e: # arg, idx = e.parse
                if e.parse:
                    arg, idx = e.parse
                    ret.append(arg, idx, ArgCompleter(expected))
                ## XXX: use e.completions?
                ret.append(u"", -1, ArgCompleter(expected))
        try:
            while True:
                arg, idx = parse_string_or_list(lex)
                ret.append(arg, idx, [])
        except IncompleteParse, e:
            if e.parse:
                arg, idx = parse_string_or_list(lex)
                ret.append(arg, idx, ArgCompleter(expected))
                raise IncompleteParse(e.message, ret, e.completions) 
    return ret

def _parse_help(bofh, fullgrp, group, start, lex, line):
    ret = HelpCommand(bofh, line)
    ret.append(group, start, [fullgrp])
    args = []
    while True:
        try:
            arg, idx = parse_string_or_list(lex)
            args.append((arg, idx))
        except IncompleteParse, e:
            # XXX: handle better
            if e.parse:
                args.append(e.parse)
            break

    localcmds = _internal_cmds.keys()
    if len(args) > 2:
        raise SynErr(u"Too many arguments for help", args[2][1])
    elif len(args) == 0:
        ret.append(u'', -1, localcmds + bofh.get_bofh_command_keys())
        return ret
    elif len(args) <= 2:
        bofhcmds = bofh.get_bofh_command_keys()
        allcmds = bofhcmds + localcmds

        def match_item(cmd, expected):
            if isinstance(cmd[0], (list, tuple)):
                return map(lambda x: match_item(x, expected), cmd[0]), cmd[1], []
            return cmd[0], cmd[1], filter(lambda x: x.startswith(cmd[0]), expected)

        cmd, idx, completes = match_item(args[0], allcmds)
        ret.append(cmd, idx, completes)

        if len(completes) != 1: # no completion for second arg
            if len(args) == 2:
                ret.append(args[1][0], args[1][1], [])
        else:
            grp = bofh.get_bofh_command_value(*completes)
            if grp:
                if len(args) == 2:
                    bofhcmds = grp.get_bofh_command_keys()
                    cmd, idx, completes = match_item(args[1], bofhcmds)
                    ret.append(cmd, idx, completes)
                    #if len(completes) == 1:
                    #    ret.set_help_for(grp.get_bofh_command_value(*completes))
                else:
                    ret.append(None, -1, grp.get_bofh_command_keys())
                    #ret.set_help_for(grp)
            elif completes[0] in _internal_cmds:
                if len(args) == 1:
                    pass
                    #ret.set_help_str(_internal_help(*completes[0]))
                else:
                    raise SynErr(u"Too many arguments for help", args[1][1])
            else:
                pass # incomplete, finn grouppe/intern kommando
    return ret

def _parse_script(bofh, fullgrp, group, start, lex, line):
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
        raise SynErr(u"Too many arguments for script", args[1][1])
    elif len(args) == 1:
        if _r(arg):
            ret.append(arg, idx, [arg])
        else:
            ret.append(arg, idx, FileCompleter())
    else:
        ret.append(None, -1, FileCompleter())
    return ret

def _parse_source(bofh, fullgrp, group, start, lex, line):
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
        if u'--ignore-errors'.startswith(args[0]):
            ret.append(args[0][0], args[0][1], [u'--ignore-errors'])
        elif _r(args[0][0]):
            ret.append(None, None, [])
            ret.append(args[0][0], args[0][1], [args[0][0]])
        else:
            ret.append(None, None, [])
            ret.append(arg, idx, FileCompleter())
    elif len(args) == 2:
        if u'--ignore-errors'.startswith(args[0][0]):
            ret.append(args[0][0], idx, [u'--ignore-errors'])
        else:
            raise SynErr(u"Expected --ignore-errors, found %s" % args[0][0], args[0][1])
        ret.append(arg, idx, FileCompleter())
    else:
        raise SynErr(u"Too many arguments for source", args[2][1])
    return ret

def _parse_single(bofh, fullgrp, group, start, lex, line):
    return SingleCommand(bofh, fullgrp, group, start, line)

_internal_cmds = {
        u'help': _parse_help,
        u'source': _parse_source,
        u'script': _parse_script,
        u'quit': _parse_single,
        u'commands': _parse_single
        }

def parse(bofh, text):
    """Parses a command
    :text: A (unicode) object to parse"""
    lex = lexer(text)
    initial = bofh.get_bofh_command_keys()
    allcmds = initial + _internal_cmds.keys()
    try:
        group, idx, fltrcmds, solematch = parse_string(lex, allcmds)
    except IncompleteParse:
        raise NoGroup(None, allcmds)

    if solematch:
        fullgrp = solematch
    else:
        fullgrp = group

    if solematch and fullgrp in initial:
        return _parse_bofh_command(bofh, fullgrp, group, idx, lex, text)

    if solematch:
        return _internal_cmds.get(fullgrp)(bofh, fullgrp, group, idx, lex, text)

    rest = [i for i in lex]
    rest.insert(0, (group, idx))
    raise NoGroup(rest, fltrcmds)

def parse_string(lex, expected=[]):
    """Get a string from lex, fail on list, and return possible matches
    Params:
    lex: lexer from lex, will pop one item from it.
    expected: list of possible parses
    Return values:
    0: Parsed string
    1: Index of parsed string
    2: list of matches
    3: A match for parsed string in expected
    Raises SynErr if read item is a paren"""
    try:
        val, idx = lex.next()
    except StopIteration:
        raise IncompleteParse(u"Expected string, got nothing", u"", expected)
    if idx == -1:
        # XXX: Do sane stuff here

        raise IncompleteParse(u"Expected %s, got nothing" % val, u"", expected)
    if val in (u'(', u')'):
        raise SynErr("Expected string, got %s" % val, idx)
    expected = filter(lambda x: x.startswith(val), expected)
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
            if idx == -1: # signals missing char after \ or missing matching ".
                try: # gets either ", -1 or some last token
                    val1, idx1 = lex.next()
                except StopIteration: # no last token
                    raise IncompleteParse(u"Expected %s, got nothing" % (u"something" if 
                        val == u'\\' else u')'), ret, [])
                if idx1 == -1: # signal we want both a \ ending and a "
                    try: # check if the last token waits.
                        val1, idx1 = lex.next()
                        ret.append((val1, idx1))
                        raise IncompleteParse(u"Expected something and \", got nothing", 
                                ret, [u' ")'])
                    except StopIteration:
                        raise IncompleteParse(u"Expected something and \", got nothing", 
                                ret, [u' ")'])
                else: # val1, idx1 holds the last token
                    ret.append((va1, idx1))
                    raise IncompleteParse(u"Expected %s, got nothing" % (u"something" if
                        val == u"\\" else u')'), ret, [u' )' if val == u"\\" else u'")'])
            elif val == u'(':
                # we don't know what to do
                # XXX: should we continue parsing?
                raise SynErr("Nested list expression", idx)
            elif val == u')':
                return ret
            ret.append((val, idx))
        raise IncompleteParse(u"Expected ), got nothing", ret, [])
    try:
        val, idx = lex.next()
    except StopIteration:
        raise IncompleteParse(u"Expected string or list, got nothing", None, [])
    if idx == -1:
        try:
            val1, idx1 = lex.next()
        except StopIteration: # no last token
            raise IncompleteParse(u"Expected %s, got nothing" % (u"something" if 
                val == u'\\' else u'"'), None, [u' ' if val == u'\\' else u'"'])
        if idx1 == -1: # signal we want both a \ ending and a "
            try: # check if the last token waits.
                val1, idx1 = lex.next()
                raise IncompleteParse(u"Expected something and \", got nothing", (val1, idx1), [u' "'])
            except StopIteration:
                raise IncompleteParse(u"Expected something and \", got nothing", None, [u' "'])
        else: # val1, idx1 holds the last token
            raise IncompleteParse(u"Expected %s, got nothing" % (u"something" if
                val == u"\\" else u')'), (val1, idx1), [u' ' if val == u'\\' else u'"'])
    elif val == u'(':
        try:
            return parse_list(), idx
        except IncompleteParse, e:
            e.parse = (e.parse, idx)
            raise
    else:
        return val, idx

def lexer(text):
    """Generates tokens from the text"""
    ret = []
    start = 0
    inquotes = False
    internalquotes = False
    backslash = False
    for i in range(len(text)):
        cur = text[i]
        if backslash:
            if not ret:
                start = i-1
            ret.append(cur)
            backslash = False
        elif inquotes:
            if cur == u'"':
                inquotes = False
                if not internalquotes:
                    internalquotes = False
                    yield u''.join(ret), start
                    ret = []
            else:
                ret.append(cur)
        elif cur == u'(' or cur == u')':
            if ret:
                yield u''.join(ret), start
                ret = []
            yield cur, i
        elif cur == u'"':
            inquotes = True
            internalquotes = bool(ret)
            if not internalquotes:
                start = i
        elif cur.isspace():
            if ret:
                yield u''.join(ret), start
                ret = []
                #yield u' ', i
        elif cur == u'\\':
            backslash = True
        else:
            if not ret:
                start = i
            ret.append(cur)
    if backslash:
        yield u'\\', -1
    if inquotes:
        yield u'"', -1
    if ret:
        yield u''.join(ret), start

