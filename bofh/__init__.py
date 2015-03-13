#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010 University of Oslo, Norway
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

u"""The PyBofh package

Normally, you should get a bofh object by calling ``obj = connect(user, pass)``,
and play with this.

>>> obj = connect('user', 'pass')
>>> obj.motd
Message of the day
>>> obj.user.info('user')
Username: user
...
"""
import sys
import os.path
from . import proto

__all__ = ['internal_commands', 'parser', 'proto', 'readlineui', 'version',
           'get_default_url', 'get_default_protocol', 'get_default_host',
           'get_default_port', 'get_default_cert', 'connect']


def get_default_url():
    u"""Get default url for connecting to bofh"""
    # TODO: This should be configurable
    return u'%s://%s:%s' % (get_default_protocol(),
                            get_default_host(),
                            get_default_port())


def get_default_protocol():
    u"""Get default protocol for connecting to bofh"""
    return u'https'


def get_default_host():
    u"""Get default host for connecting to bofh"""
    return u'cerebrum-uio.uio.no'


def get_default_port():
    u"""Get default port for connecting to bofh"""
    return u'8000'


def get_default_cert():
    u"""Get default certificate"""
    # TODO: Should this be configurable? It depends on setup.py
    return os.path.join(sys.prefix, u'etc/pybofh/ca.pem')


def connect(url=None, cert=None, insecure=False):
    u"""Connect to the bofh server, log in, and return a bofh object

    :type url: None, str
    :param url: Some url, or None for default url.

    :type cert: None, str
    :param cert:
        Path to a PEM-file with CA-certificate, or None to use the default
        certificate.

    :type insecure: bool
    :param insecure: Do not perform certificate checks (hostname validation)

    :rtype: bofh.proto.Bofh
    :return: New bofh communication object

    """
    return proto.Bofh(url or get_default_url(),
                      cert or get_default_cert(),
                      insecure)
