# -*- coding: utf-8 -*-
#
# Copyright 2014-2019 University of Oslo, Norway
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
"""Patches for xmlrpc that adds timeout."""
from __future__ import absolute_import, unicode_literals
# TODO: Rename file to transport.py?

import logging
import socket

from six.moves import xmlrpc_client as _xmlrpc
from six.moves.http_client import HTTPConnection, HTTPSConnection


DEFAULT_TIMEOUT = socket.getdefaulttimeout()

logger = logging.getLogger(__name__)


class _XmlRpcTimeoutMixin(_xmlrpc.Transport, object):

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop('timeout', DEFAULT_TIMEOUT)
        super(_XmlRpcTimeoutMixin, self).__init__(*args, **kwargs)

    def _make_connection(self, host):
        # Create a HTTPConnection object, from Transport.make_connection
        chost, self._extra_headers, x509 = self.get_host_info(host)
        conn = HTTPConnection(
            chost,
            None,
            timeout=self.timeout)
        return conn

    def make_connection(self, host):
        # Re-implementation of Transport.make_connection
        if self._connection and host == self._connection[0]:
            return self._connection[1]

        conn = self._make_connection(host)

        # store the host argument along with the connection object
        self._connection = host, conn
        return conn


class Transport(_XmlRpcTimeoutMixin):
    """
    xmlrpc.client.Transport with timeout setting
    """
    pass


class SafeTransport(_XmlRpcTimeoutMixin, _xmlrpc.SafeTransport, object):
    """
    xmlrpc.client.SafeTransport with timeout setting
    """

    def _make_connection(self, host):
        chost, self._extra_headers, x509 = self.get_host_info(host)
        conn = HTTPSConnection(
            chost,
            None,
            timeout=self.timeout,
            context=self.context,
            **(x509 or {}))
        return conn


__all__ = (
    'SafeTransport',
    'Transport',
)
