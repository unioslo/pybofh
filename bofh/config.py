# -*- coding: utf-8 -*-
#
# Copyright 2010-2018 University of Oslo, Norway
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
"""
bofh config utilities.
"""
import logging


LOGGING_VERBOSITY = tuple((
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
))
LOGGING_FORMAT = "%(levelname)s - %(name)s - %(message)s"


def get_verbosity(verbose):
    level = LOGGING_VERBOSITY[min(len(LOGGING_VERBOSITY) - 1, verbose)]
    return level


def configure_logging(level):
    logging.basicConfig(level=level, format=LOGGING_FORMAT)
