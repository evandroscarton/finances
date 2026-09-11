"""
Acesso a dados de Cartões de Crédito via SQL puro. Toda query filtra por
usuario_id.
"""


def criar_cartao(cur, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    cur.execute(
        """
        INSERT INTO cartoes_credito
            (usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
        """,
        (usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id),
    )
    return cur.fetchone()


def buscar_cartao(cur, cartao_id, usuario_id):
    cur.execute(
        "SELECT * FROM cartoes_credito WHERE id = %s AND usuario_id = %s",
        (cartao_id, usuario_id),
    )
    return cur.fetchone()


def listar_cartoes(cur, usuario_id, cartoes_visiveis_ids=None):
    """
    cartoes_visiveis_ids: None = sem restrição (vê todos os próprios cartões).
    Lista de IDs = restringe aos cartões permitidos.
    """
    sql = """
        SELECT c.*, ct.nome AS conta_pagamento_nome
        FROM cartoes_credito c
        JOIN contas ct ON ct.id = c.conta_pagamento_id
        WHERE c.usuario_id = %s
    """
    params = [usuario_id]

    if cartoes_visiveis_ids is not None:
        sql += " AND c.id = ANY(%s)"
        params.append(cartoes_visiveis_ids)

    sql += " ORDER BY c.nome"
    cur.execute(sql, tuple(params))
    return cur.fetchall()


def atualizar_cartao(cur, cartao_id, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    cur.execute(
        """
        UPDATE cartoes_credito
        SET nome = %s, limite = %s, dia_fechamento = %s, dia_vencimento = %s, conta_pagamento_id = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
        """,
        (nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id, cartao_id, usuario_id),
    )
    return cur.fetchone()


def excluir_cartao(cur, cartao_id, usuario_id):
    cur.execute(
        "DELETE FROM cartoes_credito WHERE id = %s AND usuario_id = %s",
        (cartao_id, usuario_id),
    )
    return cur.rowcount
