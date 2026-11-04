import os
import threading

from dotenv import load_dotenv
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    """Lazily create a shared connection pool (one TLS handshake per pooled
    connection, reused across requests) instead of a cold connection per call."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not DATABASE_URL:
                    raise RuntimeError("DATABASE_URL is not configured")
                _pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=DATABASE_URL,
                )
    return _pool


class _PooledConnection:
    """Thin wrapper so existing `conn.close()` call sites return the
    connection to the pool instead of destroying it."""

    __slots__ = ("_conn",)

    def __init__(self, conn):
        object.__setattr__(self, "_conn", conn)

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __setattr__(self, name, value):
        setattr(self._conn, name, value)

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, *args):
        return self._conn.__exit__(*args)

    def close(self):
        pool = _pool
        if pool is not None:
            try:
                pool.putconn(self._conn)
                return
            except Exception:
                pass
        self._conn.close()


def get_db_connection():
    pool = _get_pool()
    return _PooledConnection(pool.getconn())


# Cloudinary is configured lazily in the upload-image route only when needed
# This prevents import errors if cloudinary is not installed
