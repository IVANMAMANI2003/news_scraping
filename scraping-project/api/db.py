import os
from typing import Optional

import psycopg2
from psycopg2.pool import SimpleConnectionPool


def build_conn_str() -> str:
    host = os.getenv("PGHOST", "127.0.0.1")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "noticias")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "123456")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


_pool: Optional[SimpleConnectionPool] = None


def init_pool(minconn: int = 1, maxconn: int = 5) -> None:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(minconn=minconn, maxconn=maxconn, dsn=build_conn_str())


def get_conn():
    if _pool is None:
        init_pool()
    assert _pool is not None
    return _pool.getconn()


def put_conn(conn) -> None:
    assert _pool is not None
    _pool.putconn(conn)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None

