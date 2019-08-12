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

import argparse
import getpass
import locale
import logging
import sys

import six
from six.moves.urllib.parse import urlparse

import bofh
import bofh.config
import bofh.parser
import bofh.proto
import bofh.readlineui
import bofh.version


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


def setup_logging(verbosity):
    """ configure logging if verbosity is not None """
    if verbosity is None:
        root = logging.getLogger()
        root.addHandler(logging.NullHandler())
    else:
        level = bofh.config.get_verbosity(int(verbosity) - 1)
        bofh.config.configure_logging(level)


def get_default_encoding():
    """ guess encoding for arguments. """

    def _iter_encodings():
        yield locale.getdefaultlocale()[1]
        yield sys.getfilesystemencoding()
        yield sys.getdefaultencoding()

    for encoding in _iter_encodings():
        if encoding:
            return encoding


def bofh_eval(conn, line):
    parse = bofh.parser.parse(conn, line)
    logger.debug("Got obj=%s, command=%r",
                 repr(parse), repr(getattr(parse, 'command', None)))
    result = parse.eval(prompter=None)
    logger.debug("Got result=%s", repr(result))
    if isinstance(result, list):
        result = '\n\n'.join(result)
    return result


class UnicodeType(object):
    """ Argparse transform for non-unicode input. """

    def __init__(self, encoding=None):
        self.encoding = encoding

    def __call__(self, value):
        if isinstance(value, bytes):
            value = value.decode(self.encoding)
        return six.text_type(value)

    def __repr__(self):
        return 'UnicodeType(encoding={0})'.format(repr(self.encoding))


def main(inargs=None):
    parser = argparse.ArgumentParser(
        description="The Cerebrum Bofh client",
    )
    default_encoding = get_default_encoding()

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
        type=UnicodeType(default_encoding),
        help="use a custom prompt (default: %(default)r)",
        metavar='PROMPT',
    )
    output_args.add_argument(
        '-v', '--verbosity',
        dest='verbosity',
        action='count',
        default=None,
        help="show debug messages on stderr",
    )

    parser.add_argument(
        '--cmd',
        action='append',
        dest='commands',
        type=UnicodeType(default_encoding),
        help="run command %(metavar)s and exit",
        metavar='CMD',
    )

    args = parser.parse_args(inargs)
    setup_logging(args.verbosity)
    logger.debug('args: %r', args)

    prompt_pass = bofh.readlineui.IOUtil(encoding=default_encoding).get_secret

    print("Connecting to {}\n".format(complete_url(args.url)))
    try:
        conn = bofh.connect(url=complete_url(args.url),
                            cert=args.cert,
                            insecure=args.insecure,
                            timeout=args.timeout)
        if conn.motd:
            print(conn.motd)
        conn.login(args.user,
                   prompt_pass('Password for {}:'.format(args.user)))
    except (KeyboardInterrupt, EOFError):
        print("")
        raise SystemExit()
    except bofh.proto.BofhError as e:
        raise SystemExit('{}'.format(e.args[0]))

    # Start the interactive REPL
    try:
        if args.commands:
            for command in args.commands:
                print(args.prompt + command)
                # ugh
                sys.stdout.flush()
                print(bofh_eval(conn, command))
        else:
            bofh.readlineui.repl(conn, prompt=args.prompt)
    except Exception as e:
        logger.error("Unhandled error", exc_info=True)
        raise SystemExit('Error: {}'.format(e))
    finally:
        conn.logout()


if __name__ == '__main__':
    main()
