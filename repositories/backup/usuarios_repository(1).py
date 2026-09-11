"""Acesso a dados de usuários. Toda query é parametrizada (%s)."""
from db.connection import get_cursor


def criar_usuario(nome, email, senha_hash):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO usuarios (nome, email, senha_hash)
            VALUES (%s, %s, %s)
            RETURNING id, nome, email, criado_em
            """,
            (nome, email, senha_hash),
        )
        return cur.fetchone()


def buscar_por_email(email):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, nome, email, senha_hash FROM usuarios WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def buscar_por_id(usuario_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, nome, email FROM usuarios WHERE id = %s",
            (usuario_id,),
        )
        return cur.fetchone()
