# -*- coding: utf-8 -*-
#
# This file is part of bofh.
# Copyright (C) 2010-2023 University of Oslo, Norway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
This module consists of formatting utils for displaying responses from the
XMLRPC server in a human readable form.

Most notably is the parsing and formatting according to the hints
(format suggestions) given by the server.

Not all commands will have format suggestions. An XMLRPC command will either:

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

import six
from six.moves import reduce

logger = logging.getLogger(__name__)


class FieldRef(object):
    """
    A field reference for format suggestions.

    Field references from format suggestions are strings that identify the
    expected names and types of fields in result sets.

    Each reference is a string that follow one of the following syntaxes:

    - <name>
    - <name>:<type>:<params>

    The only currently supported <type> is "date", which expects a date format
    as <params>
    """

    def __init__(self, field_name, field_type=None, field_params=None):
        self.name = field_name
        self.type = field_type or None
        self.params = field_params or None

    def __repr__(self):
        return '<{cls.__name__} {obj.name}>'.format(cls=type(self), obj=self)

    @classmethod
    def from_str(cls, field_ref):
        try:
            field_name, field_type, field_params = field_ref.split(":", 2)
        except ValueError:
            field_name, field_type, field_params = (field_ref, None, None)
        return cls(field_name,
                   field_type=field_type,
                   field_params=field_params)


def sdf2strftime(sdf_string):
    """
    Convert java SimpleDateFormat to strftime.

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


def get_formatted_field(field_ref, data_set):
    """
    Format a single field value from a data set

    :type field_ref: FieldRef
    :param field_ref:
        a reference to a field in the data set

    :type data_set: dict
    :param data_set:
        a data set in the result from running a command
    """
    value = data_set[field_ref.name]

    # Convert value according to field_type and field_data
    if field_ref.type is None:
        pass
    elif field_ref.type == 'date':
        format_str = str(sdf2strftime(field_ref.params))
        value = value.strftime(format_str) if value else value
    else:
        raise ValueError("invalid field_ref type %r" % (field_ref.type, ))

    if value is None:
        return "<not set>"
    else:
        return value


class FormatItem(object):
    """
    Formatter for a bofh response data set.

    The formatter consists of a format string, field references to map into the
    format string, and an optional header.
    """

    def __init__(self, format_str, fields=None, header=None):
        """
        :param str format_str:
            A format string, e.g. ``"foo: %s, bar: %s"``.
        :param tuple fields:
            FieldRef references to insert into the format string.
        :param str header:
            An optional header for the format string.
        """
        self.format_str = format_str
        self.fields = tuple(fields or ())
        self.header = header

    def __repr__(self):
        return '<FormatItem fields=%r>' % (tuple(f.name for f in self.fields),)

    def mismatches(self, data_set):
        """
        Get a tuple of field references missing in a data_set

        :type data_set: dict
        :param data_set: A partial reponse (item).

        :rtype: tuple
        :returns:
            Returns missing field names (keys) missing in the data_set.
        """
        return tuple(f.name for f in self.fields if f.name not in data_set)

    def match(self, data_set):
        """
        Check if this FormatItem applies to a given data set.

        :type data_set: dict
        :param data_set: A partial reponse (item).

        :rtype: bool
        :returns:
            True if the data_set contains all required field references in
            self.field.
        """
        return not bool(self.mismatches(data_set))

    def format(self, data_set):
        """
        Format a given data set with this FormatItem.

        :type data_set: dict

        :rtype: six.text_type
        """
        values = tuple(get_formatted_field(f, data_set)
                       for f in self.fields)
        return self.format_str % values


class FormatSuggestion(object):
    """
    Format suggestion for a bofh command.

    The format suggestion is a collection of :py:class:`FormatItem` formatters
    for items (usually dicts) in a bofhd server response.
    """

    key_header = "hdr"
    key_string_vars = "str_vars"

    def __init__(self, items, header=None):
        self.items = items
        self.header = header

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    @staticmethod
    def _iter_format_strings(string_vars):
        """Generate FormatItems from a sequence of str_vars."""
        if isinstance(string_vars, six.string_types):
            # For some reason, we got a single format string rather than a
            # sequence of (format, (vars, ...)) tuples.
            yield FormatItem(string_vars, None, None)
            return

        for t in string_vars:
            if len(t) == 3:
                format_str, field_refs, sub_header = t
                # TODO: What's the deal here?
                #       Looks to be a fix for an issue where a format
                #       suggestion had swapped sub_header and format_str?!
                if "%" in sub_header:
                    format_str, sub_header = sub_header, None
            elif len(t) == 2:
                format_str, field_refs = t
                sub_header = None
            else:
                raise ValueError("invalid tuple length (%d)" % (len(t), ))
            fields = map(FieldRef.from_str, field_refs or ())
            yield FormatItem(format_str, fields=fields, header=sub_header)

    @classmethod
    def from_dict(cls, suggestion_response):
        """
        Create a FormatSuggestion() from a bofhd format suggestion response.

        :type suggestion_response: dict
        :param suggestion_response:
            The format suggestion given by a bofhd server.

            The dict should at least contain a 'str_vars' key, and optionally a
            'hdr' key.

        :rtype: FormatSuggestion
        """
        header = suggestion_response.get(cls.key_header)
        string_vars = suggestion_response.get(cls.key_string_vars)
        items = tuple(cls._iter_format_strings(string_vars))
        return cls(items, header=header)


@six.add_metaclass(abc.ABCMeta)
class ResponseFormatter(object):
    """ Abstract response formatter. """

    @abc.abstractmethod
    def __call__(self, response):
        """
        Format server response

        :param response:
            A response from the server.  The response should be *washed* before
            given to formatters.
        """
        raise NotImplementedError()


class StringFormatter(ResponseFormatter):
    """Response formatter for commands without a format suggestion."""

    def __call__(self, response):
        if isinstance(response, six.string_types):
            return response
        else:
            return repr(response)


class SuggestionFormatter(ResponseFormatter):
    """
    Response formatter for commands with a format suggestion.
    """
    def __init__(self, format_suggestion):
        self.suggestion = format_suggestion

    def _generate_lines(self, response):
        if self.suggestion.header:
            yield self.suggestion.header
        for fmt_no, fmt_item in enumerate(self.suggestion, 1):
            logger.info('processing formatter %d/%d: %r',
                        fmt_no, len(self.suggestion), fmt_item)
            if fmt_item.header:
                yield fmt_item.header
            for part, data_item in enumerate(response, 1):
                if isinstance(data_item, six.string_types):
                    yield data_item
                    continue
                if fmt_item.mismatches(data_item):
                    continue
                try:
                    yield fmt_item.format(data_item)
                except Exception:
                    logger.error("unable to format response part %d",
                                 part, exc_info=True)

    def __call__(self, response):
        if not isinstance(response, (list, tuple)):
            response = [response]
        logger.info('formatting response with %d part(s)', len(response))
        return "\n".join(self._generate_lines(response))


def get_formatter(format_spec):
    """
    Get an appropriate formatter.
    """
    logger.debug('get_formatter(%r)', format_spec)
    default = StringFormatter()
    if not format_spec:
        return default
    else:
        try:
            return SuggestionFormatter(FormatSuggestion.from_dict(format_spec))
        except Exception:
            logger.error("unable to get SuggestionFormatter", exc_info=True)
            return default
