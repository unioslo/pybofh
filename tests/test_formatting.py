from __future__ import unicode_literals
import datetime

import pytest

from bofh.formatting import FieldRef
from bofh.formatting import FormatItem
# from bofh.formatting import FormatSuggestion
from bofh.formatting import StringFormatter
from bofh.formatting import SuggestionFormatter
from bofh.formatting import get_formatted_field
from bofh.formatting import get_formatter
from bofh.formatting import sdf2strftime


response_data = {
    'intval': 1,
    'strval': 'hello',
    'noneval': None,
    'dateval': datetime.datetime(2020, 1, 1, 13, 37, 00),
}


@pytest.mark.parametrize("sdf,strftime", (
    ('yyyy MM dd HH mm ss', '%Y %m %d %H %M %S'),
    ("foo yyyy bar", "foo %Y bar"),
    ("yyyy yy yyyy", "%Y yy %Y"),

))
def test_sdf_formats(sdf, strftime):
    assert sdf2strftime(sdf) == strftime


@pytest.mark.parametrize("select,expect", (
    ('dateval:date:yyyy', format(response_data['dateval'].year, '04d')),
    ('noneval', '<not set>'),
    ('intval', response_data['intval']),

))
def test_get_formatted_field(select, expect):
    field = FieldRef.from_str(select)
    assert get_formatted_field(field, response_data) == expect


def test_field_ref():
    ref = FieldRef('foo', 'bar', 'baz')
    assert ref.name == 'foo'
    assert ref.type == 'bar'
    assert ref.params == 'baz'


def test_field_ref_defaults():
    ref = FieldRef('foo')
    assert ref.name == 'foo'
    assert ref.type is None
    assert ref.params is None


def test_field_ref_parse_simple():
    ref = FieldRef.from_str('foo')
    assert ref.name == 'foo'
    assert ref.type is None
    assert ref.params is None


def test_field_ref_parse_type():
    ref = FieldRef.from_str('foo:bar:baz')
    assert ref.name == 'foo'
    assert ref.type == 'bar'
    assert ref.params == 'baz'


def test_get_field_none():
    ref = FieldRef('foo')
    data = {'foo': None, }
    value = get_formatted_field(ref, data)
    assert value == '<not set>'


def test_get_field_simple():
    ref = FieldRef('foo')
    data = {'foo': 'bar', }
    value = get_formatted_field(ref, data)
    assert value == 'bar'


def test_format_item_empty():
    strval = "hello world"
    item = FormatItem(strval)
    assert item.format({'foo': 'asd', 'bar': 'bsd'}) == strval


def test_format_item():
    fmt = "foo:%s bar=%s"
    fields = tuple(map(FieldRef, ("foo", "bar")))
    data = {'foo': 'asd', 'bar': 'bsd'}

    expect = fmt % tuple((data[k.name] for k in fields))

    item = FormatItem(fmt, fields=fields)
    assert item.format(data) == expect


def test_get_string_formatter():
    f = get_formatter(None)
    assert isinstance(f, StringFormatter)


def test_get_sugg_formatter():
    fs = {'str_vars': 'foo'}
    f = get_formatter(fs)
    assert isinstance(f, SuggestionFormatter)
