"""Repository de categorias."""
from db.connection import get_cursor


def criar_categoria(usuario_id, nome, tipo, cor):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO categorias (usuario_id, nome, tipo, cor)
            VALUES (%s, %s, %s, %s)
            RETURNING id, nome, tipo, cor
            """,
            (usuario_id, nome, tipo, cor),
        )
        return cur.fetchone()


def listar_categorias(usuario_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, nome, tipo, cor FROM categorias WHERE usuario_id = %s ORDER BY nome",
            (usuario_id,),
        )
        return cur.fetchall()


def buscar_categoria(categoria_id, usuario_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, nome, tipo, cor FROM categorias WHERE id = %s AND usuario_id = %s",
            (categoria_id, usuario_id),
        )
        return cur.fetchone()
