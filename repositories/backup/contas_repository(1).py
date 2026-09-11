"""
Acesso a dados de Contas via SQL puro (psycopg2). Toda query filtra por
usuario_id — nunca retorna dado de outro usuário.
"""


def criar_conta(cur, usuario_id, nome, banco, tipo):
    cur.execute(
        """
        INSERT INTO contas (usuario_id, nome, banco, tipo)
        VALUES (%s, %s, %s, %s)
        RETURNING id, usuario_id, nome, banco, tipo, criado_em
        """,
        (usuario_id, nome, banco, tipo),
    )
    return cur.fetchone()


def buscar_conta(cur, conta_id, usuario_id):
    cur.execute(
        "SELECT * FROM contas WHERE id = %s AND usuario_id = %s",
        (conta_id, usuario_id),
    )
    return cur.fetchone()


def listar_contas(cur, usuario_id):
    cur.execute(
        "SELECT * FROM contas WHERE usuario_id = %s ORDER BY nome",
        (usuario_id,),
    )
    return cur.fetchall()


def atualizar_conta(cur, conta_id, usuario_id, nome, banco, tipo):
    cur.execute(
        """
        UPDATE contas SET nome = %s, banco = %s, tipo = %s
        WHERE id = %s AND usuario_id = %s
        RETURNING id, usuario_id, nome, banco, tipo, criado_em
        """,
        (nome, banco, tipo, conta_id, usuario_id),
    )
    return cur.fetchone()


def excluir_conta(cur, conta_id, usuario_id):
    cur.execute(
        "DELETE FROM contas WHERE id = %s AND usuario_id = %s",
        (conta_id, usuario_id),
    )
    return cur.rowcount


def calcular_saldo_compensado(cur, conta_id, usuario_id):
    """SUM(valor) de lançamentos compensados da conta. Fonte única de verdade."""
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS saldo
        FROM lancamentos
        WHERE conta_id = %s AND usuario_id = %s AND status = 'compensado'
        """,
        (conta_id, usuario_id),
    )
    return cur.fetchone()["saldo"]


def calcular_saldo_projetado(cur, conta_id, usuario_id):
    """
    saldo_projetado = saldo_compensado + SUM(valor) de lançamentos pendentes
    (status='pendente' OR data_compensacao IS NULL OR data_compensacao > CURRENT_DATE).
    Calculado em uma única query para evitar inconsistência entre duas leituras.
    """
    cur.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN status = 'compensado' THEN valor ELSE 0 END), 0)
            +
            COALESCE(SUM(CASE
                WHEN status = 'pendente' OR data_compensacao IS NULL OR data_compensacao > CURRENT_DATE
                THEN valor ELSE 0 END), 0) AS saldo_projetado
        FROM lancamentos
        WHERE conta_id = %s AND usuario_id = %s
        """,
        (conta_id, usuario_id),
    )
    return cur.fetchone()["saldo_projetado"]


def listar_lancamentos_por_conta(cur, conta_id, usuario_id, data_inicio=None, data_fim=None, status=None):
    """Extrato com filtros opcionais por período e status."""
    sql = """
        SELECT l.*, cat.nome AS categoria_nome
        FROM lancamentos l
        LEFT JOIN categorias cat ON cat.id = l.categoria_id
        WHERE l.conta_id = %s AND l.usuario_id = %s
    """
    params = [conta_id, usuario_id]

    if data_inicio:
        sql += " AND l.data_lancamento >= %s"
        params.append(data_inicio)
    if data_fim:
        sql += " AND l.data_lancamento <= %s"
        params.append(data_fim)
    if status:
        sql += " AND l.status = %s"
        params.append(status)

    sql += " ORDER BY l.data_lancamento DESC, l.id DESC"
    cur.execute(sql, tuple(params))
    return cur.fetchall()
