# -*- coding: utf-8 -*-
#
# This file is part of bofh.
# Copyright (C) 2018-2026 University of Oslo, Norway
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
"""
This module provides configuration and defaults for bofh.

Currently, all confguration here is related to loading configurable resources,
and specifying defaults for items that are intended to be configurable in the
future.

Configuration files and resources
---------------------------------
Config files will be loaded from one of the following directories:

 1. ${XDG_CONFIG_HOME}/pybofh/
 2. ${XDG_CONFIG_DIRS}/pybofh/
 3. /etc/pybofh/


Environment variables
---------------------

.. :data:: PYBOFH_DEFAULT_URL

The default url to use if no '--url' option is given on the command line.

.. :data:: PYBOFH_DEFAULT_CAFILE

Allows setting a custom CA certificate chain.  If not set, bofh will use the
default system certificates.


Logging
-------
This module can be used to configure basic logging to stderr, with an optional
filter level.

When prompting for user input (verbosity, debug level), log levels can be
translated according to a mapping:

.. :data:: LOGGING_VERBOSITY

    0. :const:`logging.ERROR`
    1. :const:`logging.WARNING`
    2. :const:`logging.INFO`
    3. :const:`logging.DEBUG`
"""
import logging
import os

logger = logging.getLogger(__name__)


CONFIG_SLUG = "pybofh"
"""
Subdirectory for bofh-related configs.

Config files for bofh should be placed in:

 1. ~/.config/CONFIG_SLUG/
 2. /etc/xdg/CONFIG_SLUG/
 3. /etc/CONFIG_SLUG/
"""

# Default XMLRPC server url
# TODO: Change this to https://localhost/ and put this url in a config?
DEFAULT_URL = 'https://cerebrum-uio.uio.no:8000/'

# Default logging format
LOGGING_FORMAT = "%(levelname)s - %(name)s - %(message)s"

# Verbosity count to logging level
LOGGING_VERBOSITY = tuple((
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
))


def xdg_config_dirs():
    """ XDG config lookup order. """
    # TODO: Consider using appdirs for windows support?

    # XDG_CONFIG_HOME
    paths = [os.environ.get("XDG_CONFIG_HOME")
             or os.path.expanduser("~/.config")]
    # XDG_CONFIG_DIRS
    paths.extend((os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":"))
    # /etc
    paths.append("/etc")

    # iterate in order
    seen = set()
    for d in paths:
        norm = os.path.abspath(os.path.join(d, CONFIG_SLUG))
        if norm not in seen:
            yield norm
            seen.add(norm)


def get_default_url():
    return (os.environ.get('PYBOFH_DEFAULT_URL') or DEFAULT_URL)


def get_default_cafile():
    return os.environ.get('PYBOFH_DEFAULT_CAFILE')


def get_verbosity(verbosity):
    """
    Translate verbosity to logging level.

    Levels are traslated according to :const:`LOGGING_VERBOSITY`.

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
    for path in xdg_config_dirs():
        logger.debug('looking for %r in %r', basename, path)
        if not os.path.isdir(path):
            continue
        candidate = os.path.join(path, basename)
        if os.path.exists(candidate):
            logger.debug('found %r', candidate)
            yield candidate


def get_config_file(basename):
    """
    Find the primary configuration file of a given name.

    :param basename: filename (or relative path)

    :return:
        returns the best (first) match from :func:`iter_config_files`, or
        None if no file was found.
    """
    for filename in iter_config_files(basename):
        return filename
    logger.debug('no %r found in config dirs', basename)
    return None
