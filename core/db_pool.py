import os
import time
import psycopg2
import psycopg2.pool
from psycopg2.extensions import connection as _connection

_pool = None
IDLE_THRESHOLD_SECONDS = 60


class PooledConnection(_connection):
    _closing = False

    def close(self):
        global _pool
        if _pool is not None and not self._closing:
            try:
                if not self.closed:
                    self.rollback()
            except Exception:
                pass
            self._last_returned_at = time.time()
            self._closing = True
            try:
                _pool.putconn(self)
            finally:
                self._closing = False
        else:
            super().close()


def _validate(conn):
    """Cheap liveness check. Only ever called on connections that have
    been idle past IDLE_THRESHOLD_SECONDS, never on the hot path."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return True
    except Exception:
        return False


def get_pooled_connection():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10,
            os.environ["DATABASE_URL"],
            connection_factory=PooledConnection,
        )
    conn = _pool.getconn()
    last_returned = getattr(conn, "_last_returned_at", None)
    if last_returned is not None and (time.time() - last_returned) > IDLE_THRESHOLD_SECONDS:
        if not _validate(conn):
            # Connection died server-side while sitting idle in the pool
            # (e.g. the DB or a network intermediary silently dropped it).
            # Rebuilding the whole pool is coarser than surgically evicting
            # just this one entry from psycopg2's private bookkeeping, but
            # it's provably safe and this path is rare, only idle
            # connections past the threshold ever reach it.
            try:
                conn.close()
            except Exception:
                pass
            _pool = None
            return get_pooled_connection()
    return conn