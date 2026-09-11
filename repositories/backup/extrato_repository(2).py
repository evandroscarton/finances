"""
Repository de Extrato.
Extrato = lançamentos COMPENSADOS ordenados por data, com saldo acumulado.
Lançamentos pendentes não entram no extrato (não representam saldo real,
apenas saldo projetado — que é tratado em outra tela).
"""


def obter_saldo_anterior(cur, usuario_id, conta_id, cartao_id, data_inicio):
    """
    Soma de todos os lançamentos compensados ANTERIORES à data_inicio
    (ponto de partida do saldo acumulado do extrato).
    Se data_inicio não for informada, retorna 0 (extrato começa do zero histórico).
    """
    if not data_inicio:
        return 0

    sql = """
        SELECT COALESCE(SUM(valor), 0) AS saldo_anterior
        FROM lancamentos
        WHERE usuario_id = %s
          AND status = 'compensado'
          AND data_compensacao < %s
    """
    params = [usuario_id, data_inicio]

    if conta_id:
        sql += " AND conta_id = %s"
        params.append(conta_id)

    if cartao_id:
        sql += " AND cartao_id = %s"
        params.append(cartao_id)

    cur.execute(sql, params)
    return cur.fetchone()["saldo_anterior"]


def listar_extrato(cur, usuario_id, conta_id, cartao_id, data_inicio, data_fim):
    """
    Lista lançamentos compensados ordenados por data_compensacao ASC (e id
    como critério de desempate para ordem estável dentro do mesmo dia).

    Para linhas que fazem parte de uma transferência (transferencia_id NOT NULL),
    faz um self-join em lancamentos (via transferencia_id, excluindo o próprio id)
    para trazer o nome da conta do OUTRO lado da transferência
    (conta_transferencia_nome). O service usa esse dado para montar o texto
    exibido na coluna "categoria" do relatório (ex.: "Transferência para: Poupança").
    """
    sql = """
        SELECT
            l.id, l.descricao, l.valor, l.data_lancamento, l.data_compensacao,
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
          AND l.status = 'compensado'
    """
    params = [usuario_id]

    if conta_id:
        sql += " AND l.conta_id = %s"
        params.append(conta_id)

    if cartao_id:
        sql += " AND l.cartao_id = %s"
        params.append(cartao_id)

    if data_inicio:
        sql += " AND l.data_compensacao >= %s"
        params.append(data_inicio)

    if data_fim:
        sql += " AND l.data_compensacao <= %s"
        params.append(data_fim)

    sql += " ORDER BY l.data_compensacao ASC, l.id ASC"

    cur.execute(sql, params)
    return cur.fetchall()
