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
Interactive bofh client.

This module implements a REPL for implementing an interactive bofh client, and
readline command completion.
"""
from __future__ import print_function, unicode_literals

import getpass
import locale
import logging
import readline

import six
from six.moves import input as _raw_input

from . import parser, proto

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = "bofh>>> "


class IOUtil(object):
    """
    PY2 and PY3 compatible raw_input() and getpass.getpass()
    """

    def __init__(self, default_prompt=DEFAULT_PROMPT, encoding=None):
        self.encoding = encoding or locale.getpreferredencoding()
        self.default_prompt = default_prompt or ''

    def get_input(self, prompt=None):
        if prompt is None:
            prompt = self.default_prompt
        if six.PY2:
            raw_text = _raw_input(prompt.encode(self.encoding))
            return raw_text.decode(self.encoding)
        else:
            return _raw_input(prompt)

    def get_secret(self, prompt=None):
        if prompt is None:
            prompt = self.default_prompt
        if six.PY2:
            raw_text = getpass.getpass(prompt.encode(self.encoding))
            return raw_text.decode(self.encoding)
        else:
            return _raw_input(prompt)


class BofhCompleter(object):
    """
    Completer functor for bofh completion.

    An instance of this class should be usable as a completer
    to send to GNU readline.
    """

    def __init__(self, bofh, encoding):
        """
        Create a bofhcompleter object.

        :param bofh: The bofh object.
        :param encoding: The encoding used
        """
        self._bofh = bofh
        self.completes = tuple()
        self.encoding = encoding

    def __call__(self, text, num):
        """
        Complete a text.

        Readline will call this repeatedly with the
        same text parameter, and an increasing num
        parameter.

        :param text: The text to complete
        :param num: The index starting with 0
        :type num: int
        :returns: The num'th completion or None when no more completions exists
        """
        if num == 0:
            # Fetching first available completion, we'll need to initialize the
            # possible matches.
            self.completes = self._get_matches()
            if len(self.completes) == 1:
                # There is only one valid completion
                return self.completes[0] + ' '
        try:
            return self.completes[num]
        except IndexError:
            return None

    def _get_readline_buffer(self):
        """Get the current readline buffer."""
        line = readline.get_line_buffer()
        if six.PY2 and self.encoding:
            return line.decode(self.encoding)
        else:
            return line

    def _get_matches(self):
        """Fetch matches for the current readline buffer content."""
        # Get the readline buffer, parse, and lookup the parse object
        # to fill in the completions.
        # Note how the bofh.parser module carefully inserts completions.
        line = self._get_readline_buffer()
        # parse() raises exception when it could not make sense
        # of the input, but this should be fairly common for
        # completions
        try:
            parse = parser.parse(self._bofh, line)
            # Parse successful - this should mean that we matched something
            completions = tuple(
                parse.complete(readline.get_begidx(),
                               readline.get_endidx()))
        except parser.NoGroup as e:
            # Did not get a single command?
            idx = readline.get_begidx()
            if idx == 0 or line[:idx].isspace():
                completions = tuple(e.completions)
            else:
                completions = tuple()
        except parser.IncompleteParse as e:
            # Incomplete () or ""?
            completions = tuple(
                e.parse.complete(readline.get_begidx(),
                                 readline.get_endidx()))
        except Exception:
            # Unable to match anything?
            logger.error("_init_matches", exc_info=True)
            completions = tuple()
        return completions


# script_file is set to a unicode file descriptor by
# bofh.internal_commands.script()
# TODO: This should be implemented in some other way...
script_file = None


def prompter(prompt, mapping, help, default, argtype=None, optional=False):
    """
    A promter function.

    This is used for asking for more arguments, or when arguments are
    given with prompt_func in bofh.

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
    logger.debug('prompter(prompt=%s, mapping=%s, help=%s, default=%s,'
                 ' argtype=%s, optional=%s)', repr(prompt), repr(mapping),
                 repr(help), repr(default), repr(argtype), repr(optional))
    # tell the user about the default value by including it in the prompt
    if default is not None:
        _prompt = "%s [%s] > " % (prompt, default)
    else:
        _prompt = "%s > " % prompt

    # Simple method to select an inputfunc for asking user for data.
    # A dict is used to be able to extend this easily for other
    # types.
    ioutil = IOUtil(default_prompt=prompt)
    inputfunc = {'accountPassword': ioutil.get_secret}.get(argtype,
                                                           ioutil.get_input)
    map = []

    # format the mapping for the user
    if mapping:
        mapstr = [mapping[0][1]]
        i = 1
        for line in mapping[1:]:
            map.append(line[0])
            mapstr.append("%4s " % i + line[1])
            i += 1
        mapstr = "\n".join(mapstr)
    while True:
        if map:
            print(mapstr)
        # get input from user
        val = inputfunc(_prompt).strip()
        # Lines read at this stage, are params to a command.
        # We remove them from the history.
        # Note that we only do this for non-empty lines! If we do it for all
        # lines, we would remove history that should not be removed ;)
        if val:
            rlh_to_delete = readline.get_current_history_length()
            readline.remove_history_item(rlh_to_delete-1)

        # only let empty value pass if default or optional
        if not val and not default:
            if optional:
                return None
            continue
        elif not val:
            return default

        # Print some help text
        elif val == '?':
            if help is None:
                print("Sorry, no help available")
            else:
                print(help)
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
                    print("Please type a number matching one of the items")
                except IndexError:
                    print("The item you selected does not exist")
            else:
                return val


def repl(bofh, charset=None, prompt=None):
    """
    Read Eval Print Loop

    The function of this is to

    * read a line of input from the user
    * evaluate the input
    * print the result
    * loop back to start

    :param bofh: The bofh object
    :param charset: The charset for input, or None to find from system
    :param prompt: User defined prompt, if specified
    :raises: SystemExit
    """
    if not prompt:
        prompt = DEFAULT_PROMPT

    if charset is None:
        charset = locale.getpreferredencoding()

    ioutil = IOUtil(default_prompt=prompt, encoding=charset)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(BofhCompleter(bofh, charset))
    while True:
        # read input
        try:
            line = ioutil.get_input()
            logger.debug('got input %r', line)
            # If we get a blank line, we just continue
            if not line:
                continue
        except EOFError:
            logger.debug('EOFError on input()', exc_info=True)
            print("So long, and thanks for all the fish!")
            return
        except KeyboardInterrupt:
            logger.debug('KeyboardInterrupt on input()', exc_info=True)
            print("")
            raise SystemExit()
        if script_file is not None:
            script_file.write("%s %s\n" % (prompt, line))
        try:
            # eval
            parse = parser.parse(bofh, line)
            logger.debug("Got obj=%s, command=%r",
                         repr(parse), repr(getattr(parse, 'command', None)))
            result = parse.eval(prompter=prompter)
            logger.debug("Got result=%s", repr(result))

            logger.debug('before join: result=%s', repr(result))
            if isinstance(result, list):
                result = '\n\n'.join(result)
            logger.debug('after join: result=%s', repr(result))

            print(result)
            if script_file is not None:
                script_file.write(result)
                script_file.write("\n")
        except SystemExit:
            # raised in internal_commands.quit()
            logger.debug('SystemExit on parse/eval', exc_info=True)
            # TODO/TBD: Output some message?
            raise
        except proto.SessionExpiredError:
            logger.debug('session error on parse/eval', exc_info=True)
            # Session expired, relogin.
            print("Session expired, you need to reauthenticate")
            pw = getpass.getpass()
            bofh.login(None, pw, init=False)
        except proto.BofhError as e:
            logger.debug('protocol error on parse/eval', exc_info=True)
            # Error from the bofh server
            print(six.text_type(e.args[0]))
        except EOFError:
            # Sent from prompt func. Just ask for new command
            logger.debug('EOFError on parse/eval', exc_info=True)
            print()
        except parser.SynErr as e:
            logger.debug('syntax error on parse/eval', exc_info=True)
            print(six.text_type(e))
        except Exception:
            logger.error('Unhandled exception', exc_info=True)
            # Unknown exception, handle this
            # XXX: Handle parse errors
            if script_file is not None:
                import traceback
                traceback.print_exc(file=script_file)
