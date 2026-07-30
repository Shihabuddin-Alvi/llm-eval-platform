"""
Regression test for a real production bug: a connection sitting idle in
the pool can have its underlying TCP connection silently closed server-side
(observed live: psycopg2.OperationalError: server closed the connection
unexpectedly, thrown inside verify_token after a short idle gap). The pool
was handing out dead connections without any liveness check. Fixed by
validating any connection idle past IDLE_THRESHOLD_SECONDS with a cheap
SELECT 1, and rebuilding the whole pool if that fails, rather than
surgically evicting one entry from psycopg2's private bookkeeping (which
risks re-triggering the discard-recursion bug fixed earlier in this phase).

These tests use a fake pool and fake connection, no real database needed,
so they stay in the hermetic suite.
"""

import time
from unittest.mock import MagicMock

import core.db_pool as dbmod


class FakeCursor:
    def __init__(self, alive):
        self.alive = alive

    def execute(self, q):
        if not self.alive:
            raise Exception("server closed the connection unexpectedly")

    def fetchone(self):
        return (1,)

    def close(self):
        pass


class FakeConn:
    def __init__(self, alive=True):
        self.alive = alive
        self.closed = 0
        self._last_returned_at = None
        self.closing_called = False

    def cursor(self):
        return FakeCursor(self.alive)

    def close(self):
        self.closing_called = True
        self.closed = 1


class FakePool:
    def __init__(self, conn_to_hand_out):
        self._conn = conn_to_hand_out
        self.getconn_calls = 0

    def getconn(self):
        self.getconn_calls += 1
        return self._conn


def teardown_function(_):
    dbmod._pool = None


def test_fresh_connection_skips_validation():
    conn = FakeConn(alive=True)
    dbmod._pool = FakePool(conn)
    result = dbmod.get_pooled_connection()
    assert result is conn


def test_idle_but_alive_connection_is_reused():
    conn = FakeConn(alive=True)
    conn._last_returned_at = time.time() - 120
    dbmod._pool = FakePool(conn)
    result = dbmod.get_pooled_connection()
    assert result is conn
    assert not conn.closing_called


def test_idle_and_dead_connection_triggers_pool_rebuild(monkeypatch):
    dead_conn = FakeConn(alive=False)
    dead_conn._last_returned_at = time.time() - 120
    fresh_conn = FakeConn(alive=True)

    call_count = {"n": 0}

    def fake_pool_factory(*args, **kwargs):
        call_count["n"] += 1
        return FakePool(fresh_conn)

    dbmod._pool = FakePool(dead_conn)
    monkeypatch.setattr(dbmod.psycopg2.pool, "ThreadedConnectionPool", fake_pool_factory)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")

    result = dbmod.get_pooled_connection()

    assert dead_conn.closing_called
    assert result is fresh_conn
    assert call_count["n"] == 1