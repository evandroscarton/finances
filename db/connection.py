"""
Camada de conexão com o PostgreSQL.
Usa pool de conexões (SimpleConnectionPool) para evitar overhead de
abrir/fechar conexão a cada request, e um helper de execução parametrizada
para prevenir SQL injection (nunca f-string em SQL).
"""
import os
from contextlib import contextmanager
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

_pool = None


def init_pool():
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")

        if database_url:
            # Produção (Render): usa a URL única fornecida pelo banco
            _pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=int(os.getenv("DB_POOL_MAX", "10")),
                dsn=database_url,
            )
        else:
            # Local: usa variáveis separadas do .env
            _pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=int(os.getenv("DB_POOL_MAX", "10")),
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "financeiro"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
            )
    return _pool


@contextmanager
def get_conn():
    """Fornece uma conexão do pool e garante devolução ao final."""
    p = init_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)


@contextmanager
def get_cursor(commit=False):
    """
    Fornece um cursor (RealDictCursor => resultados como dict).
    Se commit=True, faz COMMIT ao final; em caso de exceção, faz ROLLBACK.
    Usado para operações atômicas (ex.: transferências, pagamento de fatura).
    """
    with get_conn() as conn:
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
