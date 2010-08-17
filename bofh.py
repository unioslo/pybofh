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

encoding = locale.getpreferredencoding()
user = getpass.getuser()
url = bofh.get_default_url()

try:
    import argparse, sys
    argp = argparse.ArgumentParser(description=u"The Cerebrum Bofh client")
    argp.add_argument('-u', '--user', default=getpass.getuser(), help=u"user name")
    argp.add_argument('--url', default=bofh.get_default_url(), help=u"URL")
    parse = argp.parse_args()
    user, url = parse.user, parse.url
except ImportError:
    import sys
    if sys.argv[1:]:
        print u"Argparse module needed"
        sys.exit(1)

print (u"""This is PyBofh version %s

Copyright (c) 2010 University of Oslo, Norway
This is free software; see the source for copying conditions. There is NO
warranty, not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.""" 
% bofh.version).encode(
        locale.getpreferredencoding())
conn = bofh.connect(user, getpass.getpass(), url)
print conn.motd
try:
    bofh.readlineui.repl(conn)
except:
    conn.logout()

