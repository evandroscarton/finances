"""
Acesso a dados de Lançamentos via SQL puro. Toda query filtra por
usuario_id — nunca vaza dado entre usuários.
"""


def criar_lancamento(cur, usuario_id, conta_id, cartao_id, categoria_id,
                      descricao, valor, data_lancamento, data_compensacao, status):
    cur.execute(
        """
        INSERT INTO lancamentos
            (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
             data_lancamento, data_compensacao, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, usuario_id, conta_id, cartao_id, categoria_id, descricao,
                  valor, data_lancamento, data_compensacao, status, transferencia_id
        """,
        (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
         data_lancamento, data_compensacao, status),
    )
    return cur.fetchone()


def buscar_lancamento(cur, lancamento_id, usuario_id):
    cur.execute(
        "SELECT * FROM lancamentos WHERE id = %s AND usuario_id = %s",
        (lancamento_id, usuario_id),
    )
    return cur.fetchone()


def atualizar_lancamento(cur, lancamento_id, usuario_id, conta_id, cartao_id, categoria_id,
                          descricao, valor, data_lancamento, data_compensacao, status):
    cur.execute(
        """
        UPDATE lancamentos
        SET conta_id = %s, cartao_id = %s, categoria_id = %s, descricao = %s,
            valor = %s, data_lancamento = %s, data_compensacao = %s, status = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id, usuario_id, conta_id, cartao_id, categoria_id, descricao,
                  valor, data_lancamento, data_compensacao, status, transferencia_id
        """,
        (conta_id, cartao_id, categoria_id, descricao, valor, data_lancamento,
         data_compensacao, status, lancamento_id, usuario_id),
    )
    return cur.fetchone()


def excluir_lancamento(cur, lancamento_id, usuario_id):
    cur.execute(
        "DELETE FROM lancamentos WHERE id = %s AND usuario_id = %s",
        (lancamento_id, usuario_id),
    )
    return cur.rowcount


def listar_com_filtros(cur, usuario_id, filtros, contas_visiveis_ids=None, cartoes_visiveis_ids=None):
    """
    Filtros suportados: conta_id, cartao_id, categoria_id, status,
    data_inicio, data_fim. Todos opcionais, montados dinamicamente
    com parâmetros (%s) — nunca concatenação de string.

    contas_visiveis_ids/cartoes_visiveis_ids: aplicados pela regra de
    permissoes_service (None = sem restrição, vê tudo; lista = restringe).
    """
    sql = """
        SELECT l.*, cat.nome AS categoria_nome, ct.nome AS conta_nome, cc.nome AS cartao_nome
        FROM lancamentos l
        LEFT JOIN categorias cat ON cat.id = l.categoria_id
        LEFT JOIN contas ct ON ct.id = l.conta_id
        LEFT JOIN cartoes_credito cc ON cc.id = l.cartao_id
        WHERE l.usuario_id = %s
    """
    params = [usuario_id]

    if contas_visiveis_ids is not None:
        sql += " AND (l.conta_id IS NULL OR l.conta_id = ANY(%s))"
        params.append(contas_visiveis_ids)
    if cartoes_visiveis_ids is not None:
        sql += " AND (l.cartao_id IS NULL OR l.cartao_id = ANY(%s))"
        params.append(cartoes_visiveis_ids)

    if filtros.get("conta_id"):
        sql += " AND l.conta_id = %s"
        params.append(filtros["conta_id"])
    if filtros.get("cartao_id"):
        sql += " AND l.cartao_id = %s"
        params.append(filtros["cartao_id"])
    if filtros.get("categoria_id"):
        sql += " AND l.categoria_id = %s"
        params.append(filtros["categoria_id"])
    if filtros.get("status"):
        sql += " AND l.status = %s"
        params.append(filtros["status"])
    if filtros.get("data_inicio"):
        sql += " AND l.data_lancamento >= %s"
        params.append(filtros["data_inicio"])
    if filtros.get("data_fim"):
        sql += " AND l.data_lancamento <= %s"
        params.append(filtros["data_fim"])

    sql += " ORDER BY l.data_lancamento DESC, l.id DESC"
    cur.execute(sql, tuple(params))
    return cur.fetchall()

def listar_lancamentos_por_conta_periodo(cursor, usuario_id, conta_id, data_inicio, data_fim):
    """
    Lista lançamentos de UMA conta específica dentro do período informado.
    Filtro obrigatório por usuario_id para impedir acesso cruzado entre usuários.
    Usado exclusivamente pela conciliação de extrato em PDF.
    O cursor é RealDictCursor (configurado em db/connection.py), então
    fetchall() já retorna lista de dicts diretamente.
    """
    cursor.execute(
        """
        SELECT id, valor, data_lancamento, descricao, status, data_compensacao
        FROM lancamentos
        WHERE conta_id = %s
          AND usuario_id = %s
          AND data_lancamento BETWEEN %s AND %s
        ORDER BY data_lancamento, id
        """,
        (conta_id, usuario_id, data_inicio, data_fim),
    )
    return cursor.fetchall()
