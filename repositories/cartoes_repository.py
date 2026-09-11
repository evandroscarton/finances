"""
Acesso a dados de cartões de crédito. SQL puro, sempre parametrizado.
"""


def criar_cartao(cur, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    cur.execute(
        """
        INSERT INTO cartoes_credito
            (usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id),
    )
    return cur.fetchone()["id"]


def atualizar_cartao(cur, cartao_id, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    # WHERE usuario_id = %s garante, na própria query, que jamais se
    # atualize um cartão de outro usuário — defesa em profundidade além
    # da verificação já feita no service.
    cur.execute(
        """
        UPDATE cartoes_credito
        SET nome = %s,
            limite = %s,
            dia_fechamento = %s,
            dia_vencimento = %s,
            conta_pagamento_id = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id
        """,
        (nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id, cartao_id, usuario_id),
    )
    row = cur.fetchone()
    return row["id"] if row else None


def listar_cartoes(cur, usuario_id, cartoes_ids=None):
    if cartoes_ids is not None:
        cur.execute(
            """
            SELECT c.*, ct.nome AS conta_pagamento_nome
            FROM cartoes_credito c
            JOIN contas ct ON ct.id = c.conta_pagamento_id
            WHERE c.usuario_id = %s AND c.id = ANY(%s)
            ORDER BY c.nome
            """,
            (usuario_id, cartoes_ids),
        )
    else:
        cur.execute(
            """
            SELECT c.*, ct.nome AS conta_pagamento_nome
            FROM cartoes_credito c
            JOIN contas ct ON ct.id = c.conta_pagamento_id
            WHERE c.usuario_id = %s
            ORDER BY c.nome
            """,
            (usuario_id,),
        )
    return cur.fetchall()


def buscar_cartao(cur, cartao_id, usuario_id):
    cur.execute(
        """
        SELECT c.*, ct.nome AS conta_pagamento_nome
        FROM cartoes_credito c
        JOIN contas ct ON ct.id = c.conta_pagamento_id
        WHERE c.id = %s AND c.usuario_id = %s
        """,
        (cartao_id, usuario_id),
    )
    return cur.fetchone()
