#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 University of Oslo, Norway
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
u"""Patches for httplib to offer certificate and hostname validation."""

import ssl
import socket
import httplib

try:
    from backports.ssl_match_hostname import match_hostname
except ImportError:
    from .ext.ssl_match_hostname import match_hostname

class ValidatedHTTPSConnection(httplib.HTTPSConnection, object):

    """ Re-implementation of HTTPSConnection.connect to support cert validation

    This class re-implements the connect method of httplib.HTTPSConnection,
    so that it can perform certificate validation, and hostname validation.

    """

    ca_file = None
    """ Set ca_file to validate server certificate. """

    validate_hostname = True
    """ Whether to match hostname when validating server certificate. """

    def connect(self):
        """ Wrap socket properly. """
        sock = socket.create_connection((self.host, self.port),
                                        self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = ssl.wrap_socket(sock,
                                    keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    ca_certs=self.ca_file)

        if self.ca_file and self.validate_hostname:
            match_hostname(self.sock.getpeercert(), self.host)


def get_httpsconn(ca_file=None, validate=True):
    """ Get HTTPSConnection object.

    This fetches the ValidatedHTTPSConnection object from this module, and
    applies the CA certificate `ca_file', and selects whether hostname
    validation should be used.
    """
    ValidatedHTTPSConnection.ca_file = ca_file
    ValidatedHTTPSConnection.validate_hostname = validate
    return ValidatedHTTPSConnection


def get_https(ca_file=None, validate=True):
    """ This fetches a httplib.HTTPS-like object.

    The object supports certificate validation and hostname_match.

    NOTE: Only older versions of xmlrpclib expects this object.

    """
    try:
        connection_class = get_httpsconn(ca_file=ca_file, validate=validate)
        connection_class.ca_file = ca_file
        connection_class.validate_hostname = validate
        ValidatedHTTPS = type('ValidatedHTTPS',
                              (httplib.HTTPS, object, ),
                              dict(_connection_class=connection_class))
        return ValidatedHTTPS
    except AttributeError:
        # httplib.HTTPS does not exist, which also means socket.ssl does not
        # exist. This means that the socket module was not compiled with ssl
        # support, and we aren't able to do ssl-wrapped sockets at all
        raise NotImplementedError(
            "Your version of httplib doesn't support HTTPS")
