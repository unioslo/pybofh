#!/usr/bin/env python
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

u"""Readline user interface for PyBofh."""

import readline
from . import parser, proto

class bofhcompleter(object):
    u"""Completer functor for bofh completion.
    
    An instance of this class should be usable as a completer
    to send to GNU readline.
    """

    def __init__(self, bofh, encoding):
        u"""Create a bofhcompleter object.

        :param bofh: The bofh object.
        :param encoding: The encoding used
        """
        self._bofh = bofh
        # completes is tested and filled in __call__
        self.completes = []
        self.encoding = encoding

    def __call__(self, text, num):
        u"""Complete a text.

        Readline will call this repeatedly with the
        same text parameter, and an increasing num
        parameter.

        :param text: The text to complete
        :param num: The index starting with 0
        :type num: int
        :returns: The num'th completion or None when no more completions exists
        """
        if num == 0:
            self._init_matches(text)
            if len(self.completes) == 1:
                return self.completes[0] + u' '
        try:
            return self.completes[num]
        except IndexError:
            return None

    def _init_matches(self, text):
        u"""Init matches for text"""
        # Get the readline buffer, parse, and lookup the parse object
        # to fill in the completions.
        # Note how the bofh.parser module carefully inserts completions.
        line = readline.get_line_buffer()
        # parse() raises exception when it could not make sense
        # of the input, but this should be fairly common for
        # completions
        try:
            parse = parser.parse(self._bofh, readline.get_line_buffer())
            self.completes = parse.complete(readline.get_begidx(), readline.get_endidx())
        except parser.NoGroup, e:
            idx = readline.get_begidx()
            if idx == 0 or line[:idx].isspace():
                self.completes = e.completions 
        except parser.IncompleteParse, e:
            self.completes = e.parse.complete(readline.get_begidx(), readline.get_endidx())
        except:
            import traceback
            traceback.print_exc()

script_file = None
u"""script_file is set to a file if commands should be logged.
XXX: this should be moved elsewhere."""

def prompter(prompt, mapping, help, default, argtype=None, optional=False):
    u"""A promter function. This is used for asking for more
    arguments, or when arguments are given with prompt_func in bofh.

    This function is supplied to the evaluator returned from 
    :func:`bofh.parser.parse`, and usually called from the command
    object for the command in :class:`bofh.proto.Bofh`.

    :param prompt: The prompt suggested by bofh.
    :type prompt: unicode
    :param mapping: A list of mappings from bofh or None. This argument asks
                    the user to select a value from a list.
    :type mapping: None or list of list.
    :param help: Help text for user.
    :param default: Default argument to return if user does not make input.
    :param argtype: The argument type in bofh. Currently only 'accountPassword'
                    is recognized. (Does not echo).
    :type argtype: unicode
    :optional: True if this arg is optional
    """
    import getpass, locale

    # tell the user about the default value by including it in the prompt
    if default is not None:
        _prompt = u"%s [%s] > " % (prompt, default)
    else:
        _prompt = u"%s > " % prompt

    # Simple method to select an inputfunc for asking user for data.
    # A dict is used to be able to extend this easily for other
    # types.
    inputfunc = {
            'accountPassword': getpass.getpass,
            }.get(argtype, raw_input)
    map = []

    # format the mapping for the user
    if mapping:
        mapstr = [mapping[0][1]]
        i = 1
        for line in mapping[1:]:
            map.append(line[0])
            mapstr.append(u"%4s " % i + line[1])
            i += 1
        mapstr = u"\n".join(mapstr)
    while True:
        if map:
            print mapstr
        # get input from user
        val = inputfunc(_prompt).strip().encode(locale.getpreferredencoding())

        # only let empty value pass if default or optional
        if not val and not default:
            if optional:
                return None
            continue
        elif not val:
            return default

        # Print some help text
        elif val == u'?':
            if help is None:
                print u"Sorry, no help available"
            else:
                print help
        else:
            # if mapping, return the corresponding key,
            # else just return what the user typed.
            if map:
                try:
                    i = int(val)
                    if i < 1:
                        raise IndexError("Negative")
                    return map[i-1]
                except ValueError:
                    print u"Please type a number matching one of the items"
                except IndexError:
                    print u"The item you selected does not exist"
            else:
                return val

def repl(bofh, charset=None):
    u"""Read Eval Print Loop

    The function of this is to

    * read a line of input from the user
    * evaluate the input
    * print the result
    * loop back to start

    :param bofh: The bofh object
    :param charset: The charset for raw_input, or None to find from system
    :raises: SystemExit
    """
    import sys, locale
    if charset == None:
        charset = locale.getpreferredencoding()
    readline.parse_and_bind("tab: complete")
    readline.set_completer(bofhcompleter(bofh, charset))
    while True:
        # read input
        try:
            line = raw_input(u"bofh>>> ".encode(charset)).decode(charset)
        except EOFError:
            print "So long, and thanks for all the fish!"
            return
        if script_file is not None:
            script_file.write("bofh>>> %s\n" % line.encode(charset))
        try:
            # eval
            parse = parser.parse(bofh, line)
            result = parse.eval(prompter=prompter)

            # print
            print result.encode(charset)
            if script_file is not None:
                script_file.write(result.encode(charset))
                script_file.write(u"\n".encode(charset))
        except SystemExit: # raised in internal_commands.quit()
            # XXX: Output some message?
            raise
        except proto.SessionExpiredError, e:
            # Session expired, relogin.
            print "Session expired, you need to reauthenticate"
            import getpass
            pw = getpass.getpass()
            bofh.login(None, pw)
        except proto.BofhError, e:
            # Error from the bofh server
            print e.message.encode(charset)
        except EOFError: # Sent from prompt func. Just ask for new command
            print
        except parser.SynErr, e:
            print unicode(e).encode(charset)
        except:
            # Unknown exception, handle this
            # XXX: Handle parse errors
            import traceback
            traceback.print_exc()
            if script_file is not None:
                traceback.print_exc(file=script_file)

