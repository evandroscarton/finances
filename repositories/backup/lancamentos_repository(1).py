"""Repository de lançamentos. Camada de acesso puro a dados, sem regra de negócio."""
from db.connection import get_cursor


def criar_lancamento(cur, usuario_id, conta_id, cartao_id, categoria_id,
                      descricao, valor, data_lancamento, data_compensacao,
                      status, transferencia_id=None):
    """
    Recebe um cursor já aberto (para permitir uso dentro de transações maiores,
    como transferências, sem abrir conexões concorrentes).
    """
    cur.execute(
        """
        INSERT INTO lancamentos
            (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
             data_lancamento, data_compensacao, status, transferencia_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, valor, status, data_lancamento, data_compensacao
        """,
        (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
         data_lancamento, data_compensacao, status, transferencia_id),
    )
    return cur.fetchone()


def listar_lancamentos_por_conta(usuario_id, conta_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, descricao, valor, data_lancamento, data_compensacao,
                   status, categoria_id, transferencia_id
            FROM lancamentos
            WHERE conta_id = %s AND usuario_id = %s
            ORDER BY data_lancamento DESC
            """,
            (conta_id, usuario_id),
        )
        return cur.fetchall()


def listar_lancamentos_por_cartao(usuario_id, cartao_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, descricao, valor, data_lancamento, data_compensacao, status, categoria_id
            FROM lancamentos
            WHERE cartao_id = %s AND usuario_id = %s
            ORDER BY data_lancamento DESC
            """,
            (cartao_id, usuario_id),
        )
        return cur.fetchall()


def buscar_lancamento(lancamento_id, usuario_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, conta_id, cartao_id, categoria_id, descricao, valor,
                   data_lancamento, data_compensacao, status, transferencia_id
            FROM lancamentos WHERE id = %s AND usuario_id = %s
            """,
            (lancamento_id, usuario_id),
        )
        return cur.fetchone()


def excluir_lancamento(lancamento_id, usuario_id):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM lancamentos WHERE id = %s AND usuario_id = %s RETURNING id",
            (lancamento_id, usuario_id),
        )
        return cur.fetchone()
