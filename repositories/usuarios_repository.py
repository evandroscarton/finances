"""
Repository de usuários. A criação de novos usuários (fora do primeiro
cadastro/registro público) é feita aqui via tela interna "Cadastrar Usuário",
usada para alimentar a base de e-mails que podem receber permissões.
"""


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
    cur.execute(
        "SELECT id, nome, email, senha_hash, criado_em FROM usuarios WHERE email = %s",
        (email,),
    )
    return cur.fetchone()


def buscar_por_id(cur, usuario_id):
    cur.execute(
        "SELECT id, nome, email, criado_em FROM usuarios WHERE id = %s",
        (usuario_id,),
    )
    return cur.fetchone()


def listar_todos(cur):
    """
    Lista todos os usuários cadastrados — usado no combo de e-mail da tela
    de Permissões (só e-mail já cadastrado pode ser parametrizado) e na
    própria tela de gestão de usuários.
    """
    cur.execute("SELECT id, nome, email, criado_em FROM usuarios ORDER BY nome")
    return cur.fetchall()
