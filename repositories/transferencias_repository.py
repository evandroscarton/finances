"""
Acesso a dados de Transferências via SQL puro. Toda query filtra por
usuario_id.
"""


def criar_transferencia(cur, usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao):
    cur.execute(
        """
        INSERT INTO transferencias
            (usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao
        """,
        (usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao),
    )
    return cur.fetchone()


def criar_lancamento_transferencia(cur, usuario_id, conta_id, valor, data, descricao, transferencia_id):
    """Lançamento de transferência: sem categoria, status sempre 'compensado'."""
    cur.execute(
        """
        INSERT INTO lancamentos
            (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
             data_lancamento, data_compensacao, status, transferencia_id)
        VALUES (%s, %s, NULL, NULL, %s, %s, %s, %s, 'compensado', %s)
        RETURNING id
        """,
        (usuario_id, conta_id, descricao, valor, data, data, transferencia_id),
    )
    return cur.fetchone()


def buscar_transferencia(cur, transferencia_id, usuario_id):
    cur.execute(
        "SELECT * FROM transferencias WHERE id = %s AND usuario_id = %s",
        (transferencia_id, usuario_id),
    )
    return cur.fetchone()


def listar_transferencias(cur, usuario_id, contas_visiveis_ids=None):
    """
    Uma transferência só é exibida se AMBAS as pontas (origem e destino)
    estiverem visíveis para o usuário — caso contrário, o registro exporia
    o nome de uma conta que ele não tem permissão de ver.
    """
    sql = """
        SELECT t.*, co.nome AS conta_origem_nome, cd.nome AS conta_destino_nome
        FROM transferencias t
        JOIN contas co ON co.id = t.conta_origem_id
        JOIN contas cd ON cd.id = t.conta_destino_id
        WHERE t.usuario_id = %s
    """
    params = [usuario_id]

    if contas_visiveis_ids is not None:
        sql += " AND t.conta_origem_id = ANY(%s) AND t.conta_destino_id = ANY(%s)"
        params.append(contas_visiveis_ids)
        params.append(contas_visiveis_ids)

    sql += " ORDER BY t.data DESC, t.id DESC"
    cur.execute(sql, tuple(params))
    return cur.fetchall()



def excluir_lancamentos_por_transferencia(cur, transferencia_id, usuario_id):
    cur.execute(
        "DELETE FROM lancamentos WHERE transferencia_id = %s AND usuario_id = %s",
        (transferencia_id, usuario_id),
    )
    return cur.rowcount


def excluir_transferencia(cur, transferencia_id, usuario_id):
    cur.execute(
        "DELETE FROM transferencias WHERE id = %s AND usuario_id = %s",
        (transferencia_id, usuario_id),
    )
    return cur.rowcount
