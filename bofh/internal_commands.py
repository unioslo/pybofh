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

from __future__ import with_statement

_helptexts = {
        u'help': u"help | help command | help command1 command2 -- Get help",
        u'source': u"source [--ignore-errors] file -- Read commands from file",
        u'script': u"script | script filename -- log to file",
        u'quit': u"quit -- quit bofh",
        u'commands': u"commands -- list commands"
        }

def help(bofh, *args):
    if not args:
        return bofh.help()
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, list):
            return u"\n".join(map(lambda x: help(bofh, x), arg))
        if arg in _helptexts:
            return _helptexts[arg]
        return bofh.help(arg)
    return bofh.help(*args)

def source(bofh, ignore_errors=False, script=None):
    """Read lines from file, parse, and execute each line"""
    from bofh.parser import parse
    with open(script) as src:
        for line in src:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            try:
                parsed = parse(bofh, line)
                parsed.eval()
            except:
                if not ignore_errors:
                    raise

def script(bofh, file=None):
    """Open file, and set it as script file for reader"""
    import bofh.readlineui
    bofh.readlineui = open(file, "wa")

def quit(bofh):
    """Quit"""
    import sys
    sys.exit(0)

def commands(bofh):
    ret = []
    wide = 0
    for grpname in sorted(bofh.get_bofh_command_keys()):
        grp = getattr(bofh, grpname)
        for cmdname in sorted(grp.get_bofh_command_keys()):
            cmd = getattr(grp, cmdname)
            fullname = cmd._fullname
            wide = max(wide, len(fullname))
            ret.append([fullname, [grpname, cmdname] + map(unicode, cmd.args)])
    return u"\n".join(map(lambda x: "%-*s -> %s" % tuple([wide] + x), ret))

