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

u"""Readline user interface for PyBofh"""

import readline, parser

class bofhcompleter(object):
    """Completer functor for bofh completion"""
    def __init__(self, bofh, encoding):
        self._bofh = bofh
        self.completes = []
        self.encoding = encoding

    def __call__(self, text, num):
        if num == 0:
            self._init_matches(text)
            if len(self.completes) == 1:
                return self.completes[0] + u' '
        try:
            return self.completes[num]
        except IndexError:
            return None

    def _init_matches(self, text):
        line = readline.get_line_buffer()
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

def repl(bofh, charset=None):
    import sys, locale
    if charset == None:
        charset = locale.getpreferredencoding()
    readline.parse_and_bind("tab: complete")
    readline.set_completer(bofhcompleter(bofh, charset))
    while True:
        line = raw_input(u"pybofh >>> ".encode(charset)).decode(charset)
        if script_file is not None:
            script_file.write("pybofh >>> %s\n" % line.encode(charset))
        try:
            parse = parser.parse(bofh, line)
            result = parse.eval()
            print result.encode(charset)
            if script_file is not None:
                script_file.write(result.encode(charset))
                script_file.write(u"\n".encode(charset))
        except SystemExit:
            raise
        except:
            import traceback
            traceback.print_exc()
            if script_file is not None:
                traceback.print_exc(file=script_file)

