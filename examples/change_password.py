#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of bofh.
# Copyright (C) 2010-2023 University of Oslo, Norway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
import getpass
import sys
import textwrap

import bofh.proto
import bofh.version

header = textwrap.dedent(
    """
    This is bofh version {}

    Copyright (C) 2010-2023 University of Oslo, Norway
    This is free software; see the source for copying conditions. There is NO
    warranty, not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    """
).strip().format(bofh.version.version)
print(header)

try:
    bofhcom = bofh.connect(getpass.getuser(), getpass.getpass())
except bofh.proto.BofhError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(1)

newpass = getpass.getpass("New password: ")

if newpass != getpass.getpass("Repeat: "):
    print("Passwords doesn't match")
else:
    try:
        print(bofhcom.user.password(getpass.getuser(), newpass))
        print("Password changed")
    except bofh.proto.BofhError as e:
        print(e.message, file=sys.stderr)
        sys.exit(1)
