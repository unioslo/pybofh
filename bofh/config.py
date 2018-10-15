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
This module provides configuration and defaults for pybofh.

Currently, all confguration here is related to loading configurable resources,
and specifying defaults for items that are intended to be configurable in the
future.

Configuration files and resources
---------------------------------
Files will be loaded from one of the following directories:

.. py:data:: DEFAULT_CONFIG_PATH

    1. ~/.config/pybofh/
    2. /etc/pybofh/
    3. <prefix>/local/share/pybofh
    4. <prefix>/share/pybofh

The last location is where pybofh installs default configuration files and
resources.  Currently, the only file loaded from these locations are the CA
certificate bundle used by pybofh.


Logging
-------
This module can be used to configure basic logging to stderr, with an optional
filter level.

When prompting for user input (verbosity, debug level), log levels can be
translated according to a mapping:

.. py:data:: LOGGING_VERBOSITY

    0. :py:const:`logging.ERROR`
    1. :py:const:`logging.WARNING`
    2. :py:const:`logging.INFO`
    3. :py:const:`logging.DEBUG`
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)


# Config file locations
# TODO: Consider using appdirs for windows support?
# TODO: Replace default location with package_data for simplicity across
#       platforms?
DEFAULT_CONFIG_PATH = tuple((
    os.path.expanduser('~/.config/pybofh'),
    '/etc/pybofh',
    os.path.join(sys.prefix, 'local', 'share', 'pybofh'),
    os.path.join(sys.prefix, 'share', 'pybofh'),
))

# Default XMLRPC server url
# TODO: Change this to https://localhost/ and put this url in a config.
DEFAULT_URL = 'https://cerebrum-uio.uio.no:8000/'

# Default logging format
# TODO: Support logging config
LOGGING_FORMAT = "%(levelname)s - %(name)s - %(message)s"

# Verbosity count to logging level
LOGGING_VERBOSITY = tuple((
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
))


def get_verbosity(verbosity):
    """
    Translate verbosity to logging level.

    Levels are traslated according to :py:const:`LOGGING_VERBOSITY`.

    :param int verbosity: verbosity level

    :rtype: int
    """
    level = LOGGING_VERBOSITY[min(len(LOGGING_VERBOSITY) - 1, verbosity)]
    return level


def configure_logging(level):
    """
    Enable and configure logging.

    :param int level: logging level
    """
    logging.basicConfig(level=level, format=LOGGING_FORMAT)


def iter_config_files(basename):
    """
    Iterate over files in config directories.

    :param basename: filename (or relative path)

    :rtype: generator
    :return: returns matching files from :py:const:`DEFAULT_CONFIG_PATH`
    """
    for path in DEFAULT_CONFIG_PATH:
        logger.debug('looking for %r in %r', basename, os.path.abspath(path))
        if not os.path.isdir(path):
            continue
        candidate = os.path.join(path, basename)
        if os.path.exists(candidate):
            logger.info('found %r', candidate)
            yield candidate


def get_config_file(basename):
    """
    Find the primary configuration file of a given name.

    :param basename: filename (or relative path)

    :return:
        returns the best (first) match from :py:func:`iter_config_files`, or
        None if no file was found.
    """
    for filename in iter_config_files(basename):
        return filename
    logger.warn('no %r found in config dirs', basename)
    return None
