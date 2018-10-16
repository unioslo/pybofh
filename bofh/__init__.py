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
"""
The bofh library
----------------

The bofh library is an XMLRPC client library for Cerebrum, and the main
component of the pybofh distribution.

This library can be used to automate common use cases of the pybofh cli script.

Typical usage would look something like:

::

    >>> obj = connect('user', 'pass')
    >>> obj.motd
    Message of the day
    >>> obj.user.info('user')
    Username: user
    ...
"""
import logging

from . import config
from . import proto
from . import version


__all__ = ['internal_commands', 'parser', 'proto', 'readlineui', 'version',
           'get_default_url', 'get_default_protocol', 'get_default_host',
           'get_default_port', 'get_default_cert', 'connect']
__version__ = version.version

logger = logging.getLogger(__name__)


def get_default_url():
    """Get default url for connecting to bofh"""
    # TODO: This should be configurable
    return config.DEFAULT_URL


def get_default_cert():
    """Get default certificate"""
    return config.get_config_file('cacerts.pem')


def connect(url=None, cert=None, insecure=False, timeout=None):
    """Connect to the bofh server, log in, and return a bofh object

    :type url: None, str
    :param url: Some url, or None for default url.

    :type cert: None, str
    :param cert:
        Path to a PEM-file with CA-certificate, or None to use the default
        certificate.

    :type insecure: bool
    :param insecure: Do not perform certificate checks (hostname validation)

    :type timeout: None, float
    :param timeout: The socket timeout

    :rtype: bofh.proto.Bofh
    :return: New bofh communication object

    """
    logger.debug('connect(url=%r, cert=%r, insecure=%r, timeout=%r)',
                 url, cert, insecure, timeout)
    return proto.Bofh(url or get_default_url(),
                      cert or get_default_cert(),
                      insecure, timeout=timeout)
