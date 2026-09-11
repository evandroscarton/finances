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


def buscar_por_email_exceto_usuario(cur, email, usuario_id):
    """
    Usado na edição de perfil: verifica se o email já pertence a OUTRO
    usuário (exclui o próprio usuário da checagem de duplicidade).
    """
    cur.execute(
        "SELECT * FROM usuarios WHERE email = %s AND id <> %s",
        (email, usuario_id),
    )
    return cur.fetchone()


def buscar_por_id(cur, usuario_id):
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    return cur.fetchone()


def atualizar_dados(cur, usuario_id, nome, email):
    """Atualiza nome e email do usuário. Nunca altera senha aqui."""
    cur.execute(
        """
        UPDATE usuarios
        SET nome = %s, email = %s
        WHERE id = %s
        RETURNING id, nome, email, criado_em
        """,
        (nome, email, usuario_id),
    )
    return cur.fetchone()


def atualizar_senha(cur, usuario_id, senha_hash):
    """Atualiza apenas o hash de senha do usuário."""
    cur.execute(
        "UPDATE usuarios SET senha_hash = %s WHERE id = %s",
        (senha_hash, usuario_id),
    )
