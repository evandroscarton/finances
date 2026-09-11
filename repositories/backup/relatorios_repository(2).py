"""
Repository de Relatórios.
Consultas agregadas — nunca alteram dados, apenas leitura.
Toda query é filtrada obrigatoriamente por usuario_id.
"""


def listar_totais_por_categoria(cur, usuario_id, filtros):
    """
    Agrupa lançamentos por categoria, somando os valores.
    Filtros aceitos (todos opcionais): conta_id, cartao_id, tipo, data_inicio, data_fim.
    - tipo: 'receita' ou 'despesa' (refere-se a categorias.tipo)
    - Lançamentos de transferência são EXCLUÍDOS do agrupamento por categoria,
      pois não representam receita/despesa real (regra de negócio do sistema).
    - Ordenação: receitas antes de despesas (CASE explícito, pois 'receita' > 'despesa'
      alfabeticamente e não podemos confiar em ordem de string), e dentro de cada
      tipo, valor total em ordem decrescente.
    """
    sql = """
        SELECT
            c.id AS categoria_id,
            c.nome AS categoria_nome,
            c.tipo AS categoria_tipo,
            c.cor AS categoria_cor,
            COUNT(l.id) AS quantidade,
            SUM(l.valor) AS total
        FROM lancamentos l
        JOIN categorias c ON c.id = l.categoria_id
        WHERE l.usuario_id = %s
          AND l.transferencia_id IS NULL
    """
    params = [usuario_id]

    if filtros.get("conta_id"):
        sql += " AND l.conta_id = %s"
        params.append(filtros["conta_id"])

    if filtros.get("cartao_id"):
        sql += " AND l.cartao_id = %s"
        params.append(filtros["cartao_id"])

    if filtros.get("tipo"):
        sql += " AND c.tipo = %s"
        params.append(filtros["tipo"])

    if filtros.get("data_inicio"):
        sql += " AND l.data_lancamento >= %s"
        params.append(filtros["data_inicio"])

    if filtros.get("data_fim"):
        sql += " AND l.data_lancamento <= %s"
        params.append(filtros["data_fim"])

    sql += """
        GROUP BY c.id, c.nome, c.tipo, c.cor
        ORDER BY
            CASE WHEN c.tipo = 'receita' THEN 0 ELSE 1 END,
            total DESC
    """

    cur.execute(sql, params)
    return cur.fetchall()


def somar_total_geral(cur, usuario_id, filtros):
    """
    Soma o total geral (receitas + despesas) dos lançamentos filtrados,
    usado para exibir o saldo do período no topo do relatório.
    Mesma lógica de filtros da função acima, sem agrupamento.
    """
    sql = """
        SELECT COALESCE(SUM(l.valor), 0) AS total_geral
        FROM lancamentos l
        JOIN categorias c ON c.id = l.categoria_id
        WHERE l.usuario_id = %s
          AND l.transferencia_id IS NULL
    """
    params = [usuario_id]

    if filtros.get("conta_id"):
        sql += " AND l.conta_id = %s"
        params.append(filtros["conta_id"])

    if filtros.get("cartao_id"):
        sql += " AND l.cartao_id = %s"
        params.append(filtros["cartao_id"])

    if filtros.get("tipo"):
        sql += " AND c.tipo = %s"
        params.append(filtros["tipo"])

    if filtros.get("data_inicio"):
        sql += " AND l.data_lancamento >= %s"
        params.append(filtros["data_inicio"])

    if filtros.get("data_fim"):
        sql += " AND l.data_lancamento <= %s"
        params.append(filtros["data_fim"])

    cur.execute(sql, params)
    return cur.fetchone()["total_geral"]
