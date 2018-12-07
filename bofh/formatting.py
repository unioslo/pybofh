# -*- coding: utf-8 -*-
#
# Copyright 2010-2018 University of Oslo, Norway
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
"""
This module consists of formatting utils for displaying responses from the
XMLRPC server in a human readable form.

Most notably is the parsing and formatting according to the hints
(format suggestions) given by the server.

Not all commands will have format suggestions. A XMLRPC command will either:

- Not use format suggestions and return a pre-formatted string
- Use format suggestions and return a dictionary or list of dictionaries.

For commands with format suggestions, the formatting class
:py:class:`SuggestionFormatter` is used. For all other commands,
:py:class:`StringFormatter` is used.


Format suggestions
------------------
A format suggestion is a dictionary with the following keys and values:

hdr
    An optional header line (string)

str_vars
    Either a string, a tuple or a list of tuples.

    If str_vars is a string, it will be outputted directly.

    If str_vars is a tuple, it should contain two or three items:

    1. A format string (e.g. "foo=%s, bar=%s")
    2. A list of keys from the bofh response to use for formatting the
       string (e.g. ['foo_value', 'bar_value'])
    3. An optional sub header

    If str_vars is a list of tuples, each tuple should be on the format
    mentioned. Each tuple is only formatted and added to the output if the
    keys in the tuple exists in the bofh response.


"""
from __future__ import absolute_import, unicode_literals

import abc
import logging

logger = logging.getLogger(__name__)


def sdf2strftime(sdf_string):
    """
    Simple thing to convert java SimpleDateFormat to strftime.

    The bofhd server returns date formatting hints in a
    `java.text.SimpleDateFormat` syntax, because reasons.
    """
    conversions = (
        # (subst, with),
        ("yyyy", "%Y"),
        ("MM", "%m"),
        ("dd", "%d"),
        ("HH", "%H"),
        ("mm", "%M"),
        ("ss", "%S"),
    )
    return reduce(lambda f, r: f.replace(*r), conversions, sdf_string)


def get_formatted_field(data, selection):
    """
    Format a single field.

    :type data: dict
    :param data: the result from running a command

    :type selection: str
    :param selection: what to format ('<name>' or '<name>:date:<format>')
    """
    try:
        field_name, field_type, field_data = selection.split(":", 2)
    except ValueError:
        field_name, field_type, field_data = (selection, None, None)

    value = data[field_name]

    # Convert value according to field_type and field_data
    if field_type is None:
        pass
    elif field_type == 'date':
        format_str = sdf2strftime(field_data).encode('ascii')
        value = value.strftime(format_str) if value else value
    else:
        raise ValueError("invalid field_type %r" % (field_type, ))

    if value is None:
        return "<not set>"
    else:
        return value


class FormatItem(object):
    """
    A callable formatter for bofh response data.

    The formatter consists of a format string, a tuple of names to map into
    the format string, and an optional header.
    """
    def __init__(self, format_str, names=None, header=None):
        """
        :param str format_str:
            A format string, e.g. ``"foo: %s, bar: %s"``.
        :param tuple names:
            Names to insert into the format string, e.g. ``('foo', 'bar')``.
        :param str header:
            An optional header for the format string.
        """
        self.format_str = format_str
        self.names = tuple(names or ())
        self.header = header

    def __call__(self, data):
        """
        :param dict data:
            An item from a bofh response to format.
        """
        values = tuple(get_formatted_field(data, n)
                       for n in self.names)
        return self.format_str % values


class FormatSuggestion(object):
    """
    Format suggestion for a bofh command.

    The format suggestion is a collection of :py:class:`FormatItem` formatters
    for items returned from the command.
    """

    key_header = "hdr"
    key_string_vars = "str_vars"

    def __init__(self, string_vars, header=None):
        # TODO: Move string_vars parsing up here?
        self.string_vars = string_vars
        self.header = header

    def _get_format_strings(self):
        if isinstance(self.string_vars, basestring):
            yield FormatItem(self.string_vars, None, None)
        else:
            for row in self.string_vars:
                if len(row) == 3:
                    format_str, var_names, sub_header = row
                    # TODO: What's the deal here?
                    if "%" in sub_header:
                        format_str, sub_header = sub_header, None
                else:
                    format_str, var_names = row
                    sub_header = None
                yield FormatItem(format_str, var_names, sub_header)

    def __iter__(self):
        return iter(self._get_format_strings())

    @classmethod
    def from_dict(cls, suggestion_response):
        header = suggestion_response.get(cls.key_header)
        str_vars = suggestion_response.get(cls.key_string_vars)
        return cls(str_vars, header=header)


class ResponseFormatter(object):
    """ Abstract response formatter. """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, response):
        """
        Format servert response

        :param response:
            A response from the server.  The response should be *washed*.

        """
        raise NotImplementedError()


class StringFormatter(ResponseFormatter):
    """ Response formatter for commands without a format suggestion. """

    def __call__(self, response):
        if isinstance(response, basestring):
            return response
        else:
            return repr(response)


class SuggestionFormatter(ResponseFormatter):
    """
    Response formatter for commands with a format suggestion.
    """
    def __init__(self, format_suggestion):
        self.suggestion = format_suggestion

    def __call__(self, response):
        lines = []

        if not isinstance(response, (list, tuple)):
            response = [response]

        if self.suggestion.header:
            lines.append(self.suggestion.header)

        for fmt_item in self.suggestion:
            if fmt_item.header:
                lines.append(fmt_item.header)
            for part, data_item in enumerate(response, 1):
                if isinstance(data_item, basestring):
                    lines.append(data_item)
                    continue
                try:
                    lines.append(fmt_item(data_item))
                except Exception:
                    logger.error("unable to format response part %d",
                                 part, exc_info=True)
        return "\n".join(lines)


def get_formatter(format_spec):
    """
    Get an appropriate formatter.
    """
    default = StringFormatter()
    if not format_spec:
        return default
    else:
        try:
            return SuggestionFormatter(FormatSuggestion.from_dict(format_spec))
        except Exception:
            logger.error("unable to get SuggestionFormatter", exc_info=True)
            return default
