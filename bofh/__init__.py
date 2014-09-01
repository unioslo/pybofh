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

__all__ = ['internal_commands', 'parser', 'proto', 'readlineui',
           'version', 'get_default_url', 'get_default_cert', 'connect']
import xmlrpclib as _rpc
import sys
import os.path
from . import proto

def get_default_url():
    """Get default url for connecting to bofh"""
    # TODO: This should be configurable
    return "https://cerebrum-uio.uio.no:8000"

def get_default_cert():
    """Get default certificate"""
    # TODO: Should this be configurable? It depends on setup.py
    return os.path.join(sys.prefix, 'etc/pybofh/ca.pem')

def connect(username, password, url=None, cert=None):
    u"""Connect to the bofh server, log in, and return a bofh object

    :param username: Your username
    :param password: Your password
    :url: None for default url, or some https url
    :cert: None for default cert, or some cert
    :return: New bofh communication object
    :rtype: bofh.proto.Bofh

    """
    return proto.Bofh(username,
                      password,
                      url or get_default_url(),
                      cert or get_default_cert())
