# -*- coding: utf-8 -*-
#
# Copyright 2014-2018 University of Oslo, Norway
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
"""Patches for httplib to offer certificate and hostname validation."""
# TODO: Rename file to transport.py?

import logging
import socket
import httplib
from warnings import warn
from xmlrpclib import (SafeTransport, Transport)
from sys import version_info as _py_version

DEFAULT_TIMEOUT = socket.getdefaulttimeout()
""" Default global timeout. """

logger = logging.getLogger(__name__)


def _create_connection(address, timeout=DEFAULT_TIMEOUT,
                       source_address=None):
    """ Python 2.5 socket creation.

    This is an implementation of `socket.create_connection' from PY>=26 for use
    in PY<26.
    """
    host, port = address
    err = socket.error(u"getaddrinfo returns an empty list")

    for res in socket.getaddrinfo(host, port, 0,
                                  socket.SOCK_STREAM):
        family, socktype, proto, canonname, sockaddr = res
        sock = None
        try:
            sock = socket.socket(family, socktype, proto)
            sock.connect(sockaddr)
            if timeout is not DEFAULT_TIMEOUT:
                sock.timeout(timeout)
            if source_address:
                sock.bind(source_address)
            return sock
        except socket.error, e:
            err = e
            if sock is not None:
                sock.close()
            continue
    raise err


try:
    import ssl

    try:
        # PY3 backport
        from backports.ssl_match_hostname import match_hostname
    except ImportError:
        # TODO: When going away from python 2.5, 2.6, remove support for this?
        #       Or, alternatively, use setuptools and proper requirements.
        from .ext.ssl_match_hostname import match_hostname
        warn(ImportWarning(u'Using extlib ssl_match_hostname backport'))

    class ValidatedHTTPSConnection(httplib.HTTPSConnection, object):

        """ Re-implementation of HTTPSConnection.connect to support cert validation

        This class re-implements the connect method of httplib.HTTPSConnection,
        so that it can perform certificate validation, and hostname validation.

        """

        ca_file = None
        """ Set ca_file to validate server certificate.

        This should be a file containing all the certificates, in PEM format,
        for all the chains-of-trust that is accepted.

        """

        do_match_hostname = True
        """ Whether to match hostname when validating server certificate. """

        def connect(self):
            """ Wrap socket properly. """
            sock = None
            source_addr = getattr(self, 'source_address', None)
            timeout = getattr(self, 'timeout', DEFAULT_TIMEOUT)

            makesock = getattr(socket, 'create_connection', _create_connection)
            if source_addr:
                # TODO: socket.create_connection doesn't support source_address
                #       in Python 2.6
                warn(RuntimeWarning,
                     "No support for binding a source address, will ignore")
            sock = makesock((self.host, self.port), timeout)

            if (getattr(self, '_tunnel_host', None)
                    and hasattr(self, '_tunnel')):
                self.sock = sock
                self._tunnel()

            # this will throw NameError if we call the function without ssl
            # support
            self.sock = ssl.wrap_socket(sock,
                                        keyfile=self.key_file,
                                        certfile=self.cert_file,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ca_certs=self.ca_file)

            if self.ca_file and self.do_match_hostname:
                match_hostname(self.sock.getpeercert(), self.host)

    class HTTPS(httplib.HTTPS, object):
        """New-style HTTPS class"""
        # This will give us the object.mro() type method
        pass

except ImportError:
    # ImportWarnings are ignored by default
    warn(ImportWarning, u"No `ssl' module, will not support https")


class BofhTransport(SafeTransport, object):
    """
    A transport object that supports proper ssl.
    """

    def __init__(self, cert, *rest, **kw):
        self._cert = cert
        try:
            self._validate = bool(kw.pop(u'validate_hostname'))
        except KeyError:
            self._validate = True
        self.timeout = kw.pop('timeout', None)
        super(BofhTransport, self).__init__(*rest, **kw)

    def make_connection(self, host):
        try:
            cls = ValidatedHTTPSConnection
        except NameError:
            raise NotImplementedError(
                u"Your version of httplib doesn't support HTTPS")

        cls.ca_file = self._cert
        cls.do_match_hostname = self._validate

        chost, extra_headers, x509 = self.get_host_info(host)

        if _py_version[0:2] < (2, 7):
            # Note – Starting with the release of 2.7, make_connection returns
            #        an HTTPSConnection object
            validated_https_cls = type('ValidatedHTTPS',
                                       tuple(HTTPS.mro()),
                                       dict(_connection_class=cls))
            r = validated_https_cls(chost, None, **(x509 or {}))
            r.timeout = self.timeout
            return r

        # Only newer versions of xmlrpclib
        if self._connection and host == self._connection[0]:
            return self._connection[1]

        self._extra_headers = extra_headers
        self._connection = host, cls(chost, None, **(x509 or {}))
        self._connection[1].timeout = self.timeout
        return self._connection[1]


class UnsafeBofhTransport(Transport, object):
    """
    A transport object that does NOT use ssl.
    """
    def __init__(self, timeout=None, use_datetime=0):
        self.timeout = timeout
        Transport.__init__(self, use_datetime)

    def make_connection(self, host):
        conn = Transport.make_connection(self, host)
        if self.timeout:
            conn.timeout = self.timeout
        return conn
