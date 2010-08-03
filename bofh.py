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

import getpass, bofh, locale, bofh.readlineui
print (u"""This is PyBofh version %s

Copyright (c) 2010 University of Oslo, Norway
This is free software; see the source for copying conditions. There is NO
warranty, not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.""" 
% bofh.version).encode(
        locale.getpreferredencoding())
a = bofh.connect(getpass.getuser(), getpass.getpass())
print a.motd
try:
    bofh.readlineui.repl(a)
except:
    a.logout()

