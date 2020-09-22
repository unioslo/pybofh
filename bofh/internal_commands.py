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
from __future__ import absolute_import, unicode_literals, with_statement

import io
import logging
import os

from bofh.readlineui import DEFAULT_PROMPT

# Helptexts for the help() function
_helptexts = {
    'commands': "commands -- list commands",
    'help': "help | help command | help command1 command2 -- Get help",
    'quit': "quit -- quit bofh",
    'script': "script | script filename -- log to file",
    'source': "source [--ignore-errors] file -- Read commands from file",
}
logger = logging.getLogger(__name__)


def help(bofh, *args, **kw):
    """
    The help command.

    Different uses:

    * ``help``: Return bofh.help()
    * ``help internal_command``: Returns a help text for internal command.
    * ``help group``: Returns bofh.help('group')
    * ``help group cmd``: Returns bofh.help('group', 'cmd')

    :type bofh: bofh.proto.Bofh.
    :param args: command to look up.

    :returns: The help for the args
    """
    logger.debug('help(%r, *%r)', bofh, args)
    if not args:
        return bofh.help()
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, (list, tuple, set)):
            return "\n".join(map(lambda x: help(bofh, x), arg))
        if arg in _helptexts:
            return _helptexts[arg]
        return bofh.help(arg)
    return bofh.help(*args)


def source(bofh, ignore_errors=False, script=None, encoding='utf-8',
           prompt=None):
    """
    Read lines from file, parse, and execute each line.

    Empty lines and line starting with # is ignored.

    :type bofh: bofh.proto.Bofh
    :param ignore_errors: Do not propagate an exception, but continue.
    :param script: The script fie to execute.
    :param prompt: Prompt string given as argument to bofh
    """
    logger.debug('source(%s, ignore_errors=%r, script=%r, encoding=%r)',
                 repr(bofh), ignore_errors, script, encoding)

    # TODO: Should probably raise some exception here to indicate an error,
    # rather than returning an error string...
    if not script:
        return 'Source file not given'
    if script.startswith('~'):
        script = os.path.expanduser(script)
    if not os.path.isfile(script):
        return 'Filename "{}" does not exist.'.format(script)
    if not prompt:
        prompt = DEFAULT_PROMPT

    ret = []

    from .parser import parse
    with io.open(script, mode='r', encoding=encoding) as src:
        for line_no, line in enumerate(src, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            try:
                parsed = parse(bofh, stripped)
                logger.info("Running %r (from %s:%d)",
                            stripped, script, line_no)
                result = '%s%s\n' % (prompt, stripped) + parsed.eval()
                if isinstance(result, (list, tuple)):
                    # result may be a list of formatted responses if using
                    # tuples in the command itself ("user info (foo bar)")
                    ret.extend(result)
                    logger.info("Got %d results", len(result))
                else:
                    ret.append(result)
                    logger.info("Got 1 result")
            except BaseException as e:
                logger.error("Error running %r (%s:%d)", stripped, script,
                             line_no, exc_info=True)
                if not ignore_errors:
                    ret.append('Error: %s' % str(e))
                    ret.append('Sourcing of %s aborted on line %d' % (script,
                                                                      line_no))
                    ret.append(
                        'Hint: Use \'source --ignore-errors file\' to '
                        'ignore errors')
                    break
                ret.append('Error: %s (on line %d)' % (str(e), line_no))
    return ret


def script(bofh, file=None, replace=False, encoding='utf-8', **kw):
    """
    Open file, and set it as log file for reader

    :param bofh: The bofh communicator
    :type bofh: bofh.proto.Bofh
    :param file:
    """
    logger.debug('script(%s, file=%r, replace=%r, encoding=%r)',
                 repr(bofh), file, replace, encoding)
    from . import readlineui
    mode = 'w' if replace else 'a'
    if file:
        readlineui.script_file = io.open(file, mode=mode, encoding=encoding)
        return "Copying output to %s" % repr(file)
    elif readlineui.script_file:
        ret = "Closing current scriptfile, {file}".format(
            file=readlineui.script_file.name)
        readlineui.script_file.close()
        readlineui.script_file = None
        return ret
    else:
        return "No scriptfile currently open"


def quit(bofh):
    """
    Quit the programme

    :type bofh: bofh.proto.Bofh
    :raises: SystemExit (always)
    """
    logger.debug('quit(%r)', bofh)
    raise SystemExit(0)


def commands(bofh):
    """List the commands available in bofh

    :type bofh: bofh.proto.Bofh
    :returns: A prettyprinted list of commands from bofh with args
    """
    logger.debug('commands(%r)', bofh)
    ret = []
    wide = 0
    for grpname in sorted(bofh.get_bofh_command_keys()):
        grp = getattr(bofh, grpname)
        for cmdname in sorted(grp.get_bofh_command_keys()):
            cmd = getattr(grp, cmdname)
            fullname = cmd._fullname
            wide = max(wide, len(fullname))
            ret.append([fullname, [grpname, cmdname] + map(unicode, cmd.args)])
    return "\n".join(map(lambda x: "%-*s -> %s" % tuple([wide] + x), ret))
