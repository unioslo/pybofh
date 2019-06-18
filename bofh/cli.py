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
An interactive Cerebrum XMLRPC cli client.
"""
from __future__ import print_function, unicode_literals

import getpass
import logging

from six.moves.urllib.parse import urlparse

import bofh
import bofh.config
import bofh.proto
import bofh.readlineui
import bofh.version

try:
    import argparse
except ImportError:
    from bofh.ext import argparse


logger = logging.getLogger(__name__)
dist_info = bofh.version.get_distribution()


def complete_url(url):
    """Add default protocol and port number to url if these were omitted
    when entered from the command line. This is not meant to handle all
    url-variants that users may enter, but for allowing short-hand urls
    when developing/testing, (like: cere-utv01:8962, or cerebrum-uio.uio.no)

    :type: url: str
    :param url: Some url to a bofhd-instance.

    :rtype: str
    :return: An url with protocol and port.

    """
    if url is not None:
        # Pre-2.7 versions of urlparse will fail if no protocol
        # prefix is present.
        if '://' not in url:
            url = ''.join((bofh.get_default_protocol(), '://', url))

        url_parts = urlparse(url)
        if url_parts.port is None:
            url = ''.join((url, ':', bofh.get_default_port()))
    return url


def prompt_password(user):
    """ password prompt for `user` """
    return getpass.getpass('Password for {}:'.format(user))


def setup_logging(verbosity):
    """ configure logging if verbosity is not None """
    if verbosity is None:
        root = logging.getLogger()
        root.addHandler(logging.NullHandler())
    else:
        level = bofh.config.get_verbosity(int(verbosity) - 1)
        bofh.config.configure_logging(level)


def main(inargs=None):
    parser = argparse.ArgumentParser(
        description="The Cerebrum Bofh client")

    parser.add_argument(
        '--version',
        action='version',
        version=str(dist_info))

    connect_args = parser.add_argument_group('connection settings')
    connect_args.add_argument(
        '--url',
        default=bofh.config.get_default_url(),
        help="connect to bofhd server at %(metavar)s"
             " (default: %(default)s)",
        metavar='URL',
    )
    connect_args.add_argument(
        '-u', '--user',
        default=getpass.getuser(),
        help="authenticate as %(metavar)s (default: %(default)s)",
        metavar='USER',
    )
    connect_args.add_argument(
        '-c', '--cert',
        default=bofh.config.get_default_cafile(),
        help="use ca certificates from %(metavar)s (default: %(default)s)",
        metavar='PEM',
    )
    connect_args.add_argument(
        '--insecure',
        default=False,
        action='store_true',
        help="skip certificate hostname validation",
    )
    connect_args.add_argument(
        '--timeout',
        type=float,
        default=None,
        help="set connection timeout to %(metavar)s seconds"
             " (default: no timeout)",
        metavar="N",
    )

    output_args = parser.add_argument_group('output settings')
    output_args.add_argument(
        '-p', '--prompt',
        default=bofh.readlineui.DEFAULT_PROMPT,
        help="use a custom prompt (default: %(default)r)",
        metavar='PROMPT',
    )
    output_args.add_argument(
        '-v', '--verbosity',
        dest='verbosity',
        action='count',
        default=None,
        help="show debug messages on stderr")

    args = parser.parse_args(inargs)
    setup_logging(args.verbosity)
    logger.debug('args: %r', args)

    print("Connecting to {}\n".format(complete_url(args.url)))
    try:
        conn = bofh.connect(url=complete_url(args.url),
                            cert=args.cert,
                            insecure=args.insecure,
                            timeout=args.timeout)
        if conn.motd:
            print(conn.motd)
        conn.login(args.user, prompt_password(args.user))
    except (KeyboardInterrupt, EOFError):
        print("")
        raise SystemExit()
    except bofh.proto.BofhError as e:
        raise SystemExit('{}'.format(e.args[0]))

    # Start the interactive REPL
    try:
        bofh.readlineui.repl(conn, prompt=args.prompt)
    except Exception as e:
        logger.error('Unhandled error', exc_info=True)
    finally:
        conn.logout()


if __name__ == '__main__':
    main()
