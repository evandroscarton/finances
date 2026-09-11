"""Repository de transferências. Apenas insere o registro-cabeçalho de transferência."""
from db.connection import get_cursor


def criar_transferencia_header(cur, usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao):
    """Insere o registro de transferência dentro de um cursor já aberto (mesma transação)."""
    cur.execute(
        """
        INSERT INTO transferencias (usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao),
    )
    return cur.fetchone()["id"]


def listar_transferencias(usuario_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, conta_origem_id, conta_destino_id, valor, data, descricao
            FROM transferencias WHERE usuario_id = %s ORDER BY data DESC
            """,
            (usuario_id,),
        )
        return cur.fetchall()
