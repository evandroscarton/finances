"""Repository de cartões de crédito."""
from db.connection import get_cursor


def criar_cartao(usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    with get_cursor(commit=True) as cur:
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


def listar_cartoes(usuario_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
            FROM cartoes_credito WHERE usuario_id = %s ORDER BY nome
            """,
            (usuario_id,),
        )
        return cur.fetchall()


def buscar_cartao(cartao_id, usuario_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
            FROM cartoes_credito WHERE id = %s AND usuario_id = %s
            """,
            (cartao_id, usuario_id),
        )
        return cur.fetchone()


def calcular_fatura_aberta(cartao_id, usuario_id):
    """Soma de todos os lançamentos de despesa (valor negativo) não pagos do cartão."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(SUM(valor), 0) AS total
            FROM lancamentos
            WHERE cartao_id = %s AND usuario_id = %s AND status = 'pendente'
            """,
            (cartao_id, usuario_id),
        )
        return cur.fetchone()["total"]
