# -*- coding: utf-8 -*-
#
# This file is part of bofh.
# Copyright (C) 2018-2023 University of Oslo, Norway
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
""" python -m bofh """
import bofh.cli


if __name__ == '__main__':
    # it really should be...
    bofh.cli.main()
