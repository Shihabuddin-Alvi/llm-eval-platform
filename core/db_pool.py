import os
import psycopg2
import psycopg2.pool
from psycopg2.extensions import connection as _connection

_pool = None


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
            self._closing = True
            try:
                _pool.putconn(self)
            finally:
                self._closing = False
        else:
            super().close()


def get_pooled_connection():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10,
            os.environ["DATABASE_URL"],
            connection_factory=PooledConnection,
        )
    return _pool.getconn()