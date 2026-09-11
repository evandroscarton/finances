"""
Camada de conexão com PostgreSQL via psycopg2, com pool de conexões.
Helper get_cursor() encapsula BEGIN/COMMIT/ROLLBACK automaticamente —
qualquer exceção dentro do bloco 'with' causa rollback e propaga o erro.
"""
import os
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

_pool = None


def init_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ["DATABASE_URL"],
        )
    return _pool


@contextmanager
def get_cursor(commit=False):
    """
    Fornece um cursor (RealDictCursor -> resultados como dict) dentro de
    uma transação. Se commit=True, faz COMMIT ao final; em qualquer
    exceção, faz ROLLBACK e repassa o erro (transação atômica garantida).
    """
    p = init_pool()
    conn = p.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        p.putconn(conn)
