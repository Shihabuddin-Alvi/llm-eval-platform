"""
Phase 6 tests for the connection pool.

Skips entirely if DATABASE_URL isn't set, so this stays out of the
hermetic CI suite the same way live-DB tests always have. Run it
locally with a real .env loaded.
"""

import os
import concurrent.futures

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="DATABASE_URL not set, skipping live pool tests"
)


def _run_with_timeout(fn, timeout=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn)
        return future.result(timeout=timeout)


def test_pool_connection_executes_query():
    from core.runner import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    assert result[0] == 1


def test_pool_does_not_deadlock_on_discard():
    """
    Regression test for a real bug: ThreadedConnectionPool sometimes calls
    conn.close() internally to discard a connection beyond minconn. Our
    PooledConnection.close() override calls putconn(), which without a
    re-entrancy guard causes infinite recursion / a lock deadlock. This
    must complete well under the timeout, not hang.
    """
    from core.runner import get_db_connection

    def open_and_close_more_than_minconn():
        conns = [get_db_connection() for _ in range(3)]
        for c in conns:
            c.close()
        return True

    result = _run_with_timeout(open_and_close_more_than_minconn, timeout=10)
    assert result is True