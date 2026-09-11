"""
Acesso a dados de Lançamentos Previstos via SQL puro. Toda query filtra por
usuario_id — nunca vaza dado entre usuários.
"""


def criar_previsto(cur, usuario_id, conta_id, cartao_id, categoria_id,
                    descricao, valor, dia_mes, mes_ano):
    cur.execute(
        """
        INSERT INTO lancamentos_previstos
            (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
             dia_mes, mes_ano)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, usuario_id, conta_id, cartao_id, categoria_id, descricao,
                  valor, dia_mes, mes_ano, criado_em, ultimo_lancamento_em
        """,
        (usuario_id, conta_id, cartao_id, categoria_id, descricao, valor,
         dia_mes, mes_ano),
    )
    return cur.fetchone()

def buscar_previsto(cur, previsto_id, usuario_id):
    cur.execute(
        "SELECT * FROM lancamentos_previstos WHERE id = %s AND usuario_id = %s",
        (previsto_id, usuario_id),
    )
    return cur.fetchone()


def atualizar_previsto(cur, previsto_id, usuario_id, conta_id, cartao_id, categoria_id,
                        descricao, valor, dia_mes, mes_ano):
    cur.execute(
        """
        UPDATE lancamentos_previstos
        SET conta_id = %s, cartao_id = %s, categoria_id = %s, descricao = %s,
            valor = %s, dia_mes = %s, mes_ano = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id, usuario_id, conta_id, cartao_id, categoria_id, descricao,
                  valor, dia_mes, mes_ano, criado_em, ultimo_lancamento_em
        """,
        (conta_id, cartao_id, categoria_id, descricao, valor, dia_mes, mes_ano,
         previsto_id, usuario_id),
    )
    return cur.fetchone()

def excluir_previsto(cur, previsto_id, usuario_id):
    cur.execute(
        "DELETE FROM lancamentos_previstos WHERE id = %s AND usuario_id = %s",
        (previsto_id, usuario_id),
    )
    return cur.rowcount


def listar_com_filtros(cur, usuario_id, filtros, contas_visiveis_ids=None, cartoes_visiveis_ids=None):
    """
    Filtros suportados: conta_id, cartao_id, categoria_id — todos opcionais,
    montados dinamicamente com parâmetros (%s), nunca concatenação de string.

    contas_visiveis_ids/cartoes_visiveis_ids: regra de permissoes_service
    (None = sem restrição; lista = restringe aos IDs permitidos).
    """
    sql = """
        SELECT lp.*, cat.nome AS categoria_nome, ct.nome AS conta_nome, cc.nome AS cartao_nome
        FROM lancamentos_previstos lp
        LEFT JOIN categorias cat ON cat.id = lp.categoria_id
        LEFT JOIN contas ct ON ct.id = lp.conta_id
        LEFT JOIN cartoes_credito cc ON cc.id = lp.cartao_id
        WHERE lp.usuario_id = %s
    """
    params = [usuario_id]

    if contas_visiveis_ids is not None:
        sql += " AND (lp.conta_id IS NULL OR lp.conta_id = ANY(%s))"
        params.append(contas_visiveis_ids)
    if cartoes_visiveis_ids is not None:
        sql += " AND (lp.cartao_id IS NULL OR lp.cartao_id = ANY(%s))"
        params.append(cartoes_visiveis_ids)

    if filtros.get("conta_id"):
        sql += " AND lp.conta_id = %s"
        params.append(filtros["conta_id"])
    if filtros.get("cartao_id"):
        sql += " AND lp.cartao_id = %s"
        params.append(filtros["cartao_id"])
    if filtros.get("categoria_id"):
        sql += " AND lp.categoria_id = %s"
        params.append(filtros["categoria_id"])

    sql += " ORDER BY lp.mes_ano ASC, lp.dia_mes ASC, lp.id ASC"
    cur.execute(sql, tuple(params))
    return cur.fetchall()


def atualizar_ultimo_lancamento(cur, previsto_id, usuario_id, data_atual):
    cur.execute(
        """
        UPDATE lancamentos_previstos
        SET ultimo_lancamento_em = %s
        WHERE id = %s AND usuario_id = %s
        """,
        (data_atual, previsto_id, usuario_id),
    )

def atualizar_mes_ano_em_massa(cur, usuario_id, mes_ano):
    """
    Atualiza o mes_ano de TODOS os lançamentos previstos do usuário de uma vez
    (ex.: virou o mês, o usuário quer reaproveitar todos os modelos para o mês
    seguinte). Não afeta dia_mes, valor, categoria etc. — só a referência de
    mês/ano.
    """
    cur.execute(
        "UPDATE lancamentos_previstos SET mes_ano = %s WHERE usuario_id = %s",
        (mes_ano, usuario_id),
    )
    return cur.rowcount
