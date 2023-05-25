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
""" bofh versioning utils """
import os
import pkg_resources


DISTRIBUTION_NAME = 'bofh'


def get_distribution():
    """Get a distribution object for bofh."""
    try:
        return pkg_resources.get_distribution(DISTRIBUTION_NAME)
    except pkg_resources.DistributionNotFound:
        return pkg_resources.Distribution(
            project_name=DISTRIBUTION_NAME,
            version='0.0.0',
            location=os.path.dirname(__file__))


version = get_distribution().version
