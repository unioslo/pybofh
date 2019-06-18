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

.. code:: python

    import bofh
    import getpass
    conn = bofh.connect('http://localhost')
    print(conn.motd)
    conn.login(getpass.getuser(), getpass.getpass())
    print(obj.user.info('user'))

"""
import logging
import ssl

from six.moves.urllib.parse import urlparse

from . import proto
from . import version


__all__ = ['connect']
__version__ = version.version

logger = logging.getLogger(__name__)


def _is_https(url):
    parts = urlparse(url)
    return parts.scheme == 'https'


def _get_ssl_context(cert=None, ignore_hostname=False):
    context = ssl.create_default_context()
    if cert:
        context.load_verify_locations(cafile=cert)

    # TODO: Replace with a set_servername_callback() that logs a warning?
    context.check_hostname = not ignore_hostname
    return context


def connect(url, cert=None, insecure=False, timeout=None):
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
    context = None
    if (cert or insecure) and _is_https(url):
        context = _get_ssl_context(cert=cert, ignore_hostname=insecure)
    return proto.Bofh(url=url, context=context, timeout=timeout)
