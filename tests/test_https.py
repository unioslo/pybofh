# -*- coding: utf-8 -*-
""" Tests for :mod:`bofh.https`. """
from __future__ import unicode_literals

import pytest

from bofh import https


class FakeHttpConnection(object):
    closed = False

    def close(self):
        self.closed = True


@pytest.fixture
def transport(monkeypatch):
    transport = https.Transport()
    conn = FakeHttpConnection()
    transport._connection = ('localhost', conn)
    return transport


def test_interrupted_request_resets_connection(monkeypatch, transport):
    conn = transport._connection[1]

    def send_request(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(transport, 'send_request', send_request)
    with pytest.raises(KeyboardInterrupt):
        transport.single_request('localhost', '/RPC2', b'')
    assert transport._connection == (None, None)
    assert conn.closed
