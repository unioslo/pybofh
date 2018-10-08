# -*- coding: utf-8 -*-
#
# Copyright 2010-2018 University of Oslo, Norway
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
"""
Implementation of internal pybofh commands.

Internal commands are commands that appear as regular commands in the
interactive bofh client, but aren't sent (directly) to the XMLRPC server.

Typically these functions would be called through the eval
(:meth:`bofh.parser.Command.eval`) method of the object returned from
:func:`bofh.parser.parse`.

Implemented commands
--------------------

- commands
- help
- quit
- script
- source
"""

from __future__ import with_statement
import os

# Helptexts for the help() function
_helptexts = {
    u'commands': u"commands -- list commands",
    u'help': u"help | help command | help command1 command2 -- Get help",
    u'quit': u"quit -- quit bofh",
    u'script': u"script | script filename -- log to file",
    u'source': u"source [--ignore-errors] file -- Read commands from file",
}


def help(bofh, *args):
    """
    The help command.

    Different uses:

    * ``help``: Return bofh.help()
    * ``help internal_command``: Returns a help text for internal command.
    * ``help group``: Returns bofh.help('group')
    * ``help group cmd``: Returns bofh.help('group', 'cmd')

    :param bofh: The bofh communicator
    :type bofh: bofh.proto.Bofh.
    :param args: command to look up.
    :returns: The help for the args
    """
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
    """
    Read lines from file, parse, and execute each line.

    Empty lines and line starting with # is ignored.

    :param bofh: The bofh communicator
    :type bofh: bofh.proto.Bofh
    :param ignore_errors: Do not propagate an exception, but continue.
    :param script: The script fie to execute.
    """
    if not script or not os.path.isfile(script):
        return 'Source file not given or does not exist.'

    ret = []
    line_no = 0

    from .parser import parse
    with open(script) as src:
        for line in src:
            line_no += 1
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            try:
                parsed = parse(bofh, line)
                ret.append(parsed.eval())
            except BaseException, e:
                if not ignore_errors:
                    ret.append('Error: %s' % str(e))
                    ret.append('Sourcing of %s aborted on line %d' % (script,
                                                                      line_no))
                    ret.append(
                        'Hint: Use \'source --ignore-errors file\' to '
                        'ignore errors')
                    return ret
                ret.append('Error: %s (on line %d)' % (str(e), line_no))

    return ret


def script(bofh, file=None):
    """
    Open file, and set it as log file for reader

    :param bofh: The bofh communicator
    :type bofh: bofh.proto.Bofh
    :param file:
    """
    from . import readlineui
    if file:
        readlineui.script_file = open(file, "wa")
        return u"Copying output to %s" % file
    else:
        if readlineui.script_file:
            ret = u"Closing current scriptfile, {file}".format(
                file=readlineui.script_file.name)
            readlineui.script_file.close()
            readlineui.script_file = None
            return ret
        return "No scriptfile currently open"


def quit(bofh):
    """
    Quit the programme

    :param bofh: The bofh communicator
    :type bofh: bofh.proto.Bofh
    :raises: SystemExit (always)
    """
    import sys
    sys.exit(0)


def commands(bofh):
    """List the commands available in bofh

    :param bofh: The bofh communicator
    :type bofh: bofh.proto.Bofh
    :returns: A prettyprinted list of commands from bofh with args
    """
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
