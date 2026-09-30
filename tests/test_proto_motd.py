# -*- coding: utf-8 -*-
""" Tests for the message of the day, :attr:`bofh.proto.Bofh.motd`. """
from __future__ import unicode_literals

import pytest

from bofh import proto


class FakeConnection(object):
    def __init__(self):
        self.motd_calls = 0

    def get_motd(self, client, version):
        self.motd_calls += 1
        return "Message of the day %d" % (self.motd_calls,)


@pytest.fixture
def conn():
    """ a Bofh object with a FakeConnection, not yet connected. """
    bofh = proto.Bofh.__new__(proto.Bofh)
    bofh._connection = FakeConnection()
    return bofh


def test_get_motd(conn):
    assert conn.get_motd() == "Message of the day 1"
    assert conn.get_motd() == "Message of the day 2"
    assert conn._connection.motd_calls == 2


def test_motd_after_connect(conn):
    # Bofh._connect() calls get_motd() to check the connection
    conn.get_motd()
    assert conn.motd == "Message of the day 1"
    assert conn.motd == "Message of the day 1"
    assert conn._connection.motd_calls == 1


def test_motd_without_connect(conn):
    assert conn.motd == "Message of the day 1"
    assert conn.motd == "Message of the day 1"
    assert conn._connection.motd_calls == 1


def test_get_motd_refreshes_motd(conn):
    assert conn.motd == "Message of the day 1"
    conn.get_motd()
    assert conn.motd == "Message of the day 2"
