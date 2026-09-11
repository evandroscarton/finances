"""
Acesso a dados de Categorias via SQL puro. Toda query filtra por usuario_id.
"""


def criar_categoria(cur, usuario_id, nome, tipo, cor):
    cur.execute(
        """
        INSERT INTO categorias (usuario_id, nome, tipo, cor)
        VALUES (%s, %s, %s, %s)
        RETURNING id, usuario_id, nome, tipo, cor
        """,
        (usuario_id, nome, tipo, cor),
    )
    return cur.fetchone()


def buscar_categoria(cur, categoria_id, usuario_id):
    cur.execute(
        "SELECT * FROM categorias WHERE id = %s AND usuario_id = %s",
        (categoria_id, usuario_id),
    )
    return cur.fetchone()


def listar_categorias(cur, usuario_id):
    cur.execute(
        "SELECT * FROM categorias WHERE usuario_id = %s ORDER BY tipo, nome",
        (usuario_id,),
    )
    return cur.fetchall()


def atualizar_categoria(cur, categoria_id, usuario_id, nome, tipo, cor):
    cur.execute(
        """
        UPDATE categorias SET nome = %s, tipo = %s, cor = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id, usuario_id, nome, tipo, cor
        """,
        (nome, tipo, cor, categoria_id, usuario_id),
    )
    return cur.fetchone()


def excluir_categoria(cur, categoria_id, usuario_id):
    cur.execute(
        "DELETE FROM categorias WHERE id = %s AND usuario_id = %s",
        (categoria_id, usuario_id),
    )
    return cur.rowcount
