"""
Repository de Extrato.
Extrato = lançamentos ordenados por data, com saldo acumulado.

Por padrão só lista lançamentos COMPENSADOS. Se incluir_pendentes=True,
também lista lançamentos pendentes (não compensados) — usados para uma
visão "estendida" do extrato, mas sem alterar a regra de saldo real vs.
projetado usada em outras telas.

data_referencia = COALESCE(data_compensacao, data_lancamento):
- para lançamentos compensados, data_compensacao nunca é nula.
- para lançamentos pendentes, data_compensacao pode ser NULL, então caímos
  para data_lancamento como referência de ordenação/filtro/exibição.
"""


def _condicao_status(sql, params, incluir_pendentes):
    if incluir_pendentes:
        sql += " AND l.status IN ('compensado', 'pendente')"
    else:
        sql += " AND l.status = 'compensado'"
    return sql, params


def obter_saldo_anterior(cur, usuario_id, conta_id, cartao_id, data_inicio,
                          contas_visiveis_ids=None, cartoes_visiveis_ids=None,
                          incluir_pendentes=False):
    """
    Soma de todos os lançamentos ANTERIORES à data_inicio (ponto de partida
    do saldo acumulado do extrato).

    Se incluir_pendentes=True, considera também lançamentos pendentes cuja
    data de referência (data_compensacao ou, na ausência, data_lancamento)
    seja anterior ao período — para manter saldo_inicial coerente com o que
    será exibido/somado nas linhas.

    Se data_inicio não for informada, retorna 0 (extrato começa do zero histórico).
    """
    if not data_inicio:
        return 0

    sql = """
        SELECT COALESCE(SUM(l.valor), 0) AS saldo_anterior
        FROM lancamentos l
        WHERE l.usuario_id = %s
          AND COALESCE(l.data_compensacao, l.data_lancamento) < %s
    """
    params = [usuario_id, data_inicio]

    sql, params = _condicao_status(sql, params, incluir_pendentes)
    sql = sql.replace("FROM lancamentos l\n        WHERE", "FROM lancamentos l\n        WHERE")

    if contas_visiveis_ids is not None:
        sql += " AND (l.conta_id IS NULL OR l.conta_id = ANY(%s))"
        params.append(contas_visiveis_ids)
    if cartoes_visiveis_ids is not None:
        sql += " AND (l.cartao_id IS NULL OR l.cartao_id = ANY(%s))"
        params.append(cartoes_visiveis_ids)

    if conta_id:
        sql += " AND l.conta_id = %s"
        params.append(conta_id)

    if cartao_id:
        sql += " AND l.cartao_id = %s"
        params.append(cartao_id)

    cur.execute(sql, params)
    return cur.fetchone()["saldo_anterior"]


def listar_extrato(cur, usuario_id, conta_id, cartao_id, data_inicio, data_fim,
                    contas_visiveis_ids=None, cartoes_visiveis_ids=None,
                    incluir_pendentes=False):
    """
    Lista lançamentos (compensados, e pendentes se incluir_pendentes=True)
    ordenados por data_referencia ASC (e id como critério de desempate para
    ordem estável dentro do mesmo dia).

    Traz l.status para o template poder diferenciar visualmente (fonte azul)
    as linhas pendentes das compensadas.

    Para linhas que fazem parte de uma transferência (transferencia_id NOT NULL),
    faz um self-join em lancamentos (via transferencia_id, excluindo o próprio id)
    para trazer o nome da conta do OUTRO lado da transferência
    (conta_transferencia_nome). O service usa esse dado para montar o texto
    exibido na coluna "categoria" do relatório (ex.: "Transferência para: Poupança").

    contas_visiveis_ids/cartoes_visiveis_ids: regra de permissoes_service
    (None = sem restrição; lista = restringe aos IDs permitidos).
    """
    sql = """
        SELECT
            l.id, l.descricao, l.valor, l.data_lancamento, l.data_compensacao,
            COALESCE(l.data_compensacao, l.data_lancamento) AS data_referencia,
            l.status,
            l.conta_id, l.cartao_id, l.categoria_id, l.transferencia_id,
            c.nome AS categoria_nome,
            ct.nome AS conta_nome,
            cc.nome AS cartao_nome,
            ct_outro.nome AS conta_transferencia_nome
        FROM lancamentos l
        LEFT JOIN categorias c ON c.id = l.categoria_id
        LEFT JOIN contas ct ON ct.id = l.conta_id
        LEFT JOIN cartoes_credito cc ON cc.id = l.cartao_id
        LEFT JOIN lancamentos l_outro
            ON l_outro.transferencia_id = l.transferencia_id
           AND l_outro.id <> l.id
        LEFT JOIN contas ct_outro ON ct_outro.id = l_outro.conta_id
        WHERE l.usuario_id = %s
    """
    params = [usuario_id]

    sql, params = _condicao_status(sql, params, incluir_pendentes)

    if contas_visiveis_ids is not None:
        sql += " AND (l.conta_id IS NULL OR l.conta_id = ANY(%s))"
        params.append(contas_visiveis_ids)
    if cartoes_visiveis_ids is not None:
        sql += " AND (l.cartao_id IS NULL OR l.cartao_id = ANY(%s))"
        params.append(cartoes_visiveis_ids)

    if conta_id:
        sql += " AND l.conta_id = %s"
        params.append(conta_id)

    if cartao_id:
        sql += " AND l.cartao_id = %s"
        params.append(cartao_id)

    if data_inicio:
        sql += " AND COALESCE(l.data_compensacao, l.data_lancamento) >= %s"
        params.append(data_inicio)

    if data_fim:
        sql += " AND COALESCE(l.data_compensacao, l.data_lancamento) <= %s"
        params.append(data_fim)

    sql += " ORDER BY COALESCE(l.data_compensacao, l.data_lancamento) ASC, l.id ASC"

    cur.execute(sql, params)
    return cur.fetchall()
