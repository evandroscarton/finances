"""Acesso a dados de Usuários via SQL puro."""


def criar_usuario(cur, nome, email, senha_hash):
    cur.execute(
        """
        INSERT INTO usuarios (nome, email, senha_hash)
        VALUES (%s, %s, %s)
        RETURNING id, nome, email, criado_em
        """,
        (nome, email, senha_hash),
    )
    return cur.fetchone()


def buscar_por_email(cur, email):
    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    return cur.fetchone()


def buscar_por_id(cur, usuario_id):
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    return cur.fetchone()
