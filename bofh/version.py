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
""" bofh versioning utils """
import os
import pkg_resources


DISTRIBUTION_NAME = 'pybofh'


def get_distribution():
    """ Get a distribution object for pybofh. """
    try:
        return pkg_resources.get_distribution(DISTRIBUTION_NAME)
    except pkg_resources.DistributionNotFound:
        return pkg_resources.Distribution(
            project_name=DISTRIBUTION_NAME,
            version='0.0.0',
            location=os.path.dirname(__file__))


version = get_distribution().version
