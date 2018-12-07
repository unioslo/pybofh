from __future__ import unicode_literals
import datetime

import pytest

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
    assert get_formatted_field(response_data, select) == expect


def test_format_item_empty():
    strval = "hello world"
    item = FormatItem(strval)
    assert item({'foo': 'asd', 'bar': 'bsd'}) == strval


def test_format_item():
    fmt = "foo:%s bar=%s"
    fields = ["foo", "bar"]
    data = {'foo': 'asd', 'bar': 'bsd'}

    expect = fmt % tuple((data[k] for k in fields))

    item = FormatItem(fmt, names=fields)
    assert item(data) == expect


def test_get_string_formatter():
    f = get_formatter(None)
    assert isinstance(f, StringFormatter)


def test_get_sugg_formatter():
    fs = {'str_vars': 'foo'}
    f = get_formatter(fs)
    assert isinstance(f, SuggestionFormatter)
