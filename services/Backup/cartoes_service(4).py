"""
Regras de negócio de cartões de crédito.
"""
from decimal import Decimal, InvalidOperation
from db.connection import get_cursor
from repositories import cartoes_repository as repo
from services import permissoes_service


class ErroValidacao(Exception):
    pass


def _to_decimal(valor):
    """
    Converte valor recebido (float/int/str vindo de formulário/JSON) para Decimal.
    Colunas NUMERIC do Postgres retornam Decimal via psycopg2 — nunca
    misturamos Decimal com float em operações aritméticas monetárias.
    """
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return valor
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        raise ErroValidacao("Valor monetário inválido.")


def _validar_dados_cartao(nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    """Validações comuns entre criação e edição de cartão."""
    if not nome or limite is None or limite <= 0:
        raise ErroValidacao("Nome e limite (> 0) são obrigatórios.")
    if not dia_fechamento or not dia_vencimento or not (1 <= dia_fechamento <= 31) or not (1 <= dia_vencimento <= 31):
        raise ErroValidacao("Dias de fechamento/vencimento devem estar entre 1 e 31.")
    if not conta_pagamento_id:
        raise ErroValidacao("Conta de pagamento é obrigatória.")


def criar_cartao(usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    limite = _to_decimal(limite)
    _validar_dados_cartao(nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id)

    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id FROM contas WHERE id = %s AND usuario_id = %s",
            (conta_pagamento_id, usuario_id),
        )
        if not cur.fetchone():
            raise ErroValidacao("Conta de pagamento não encontrada ou não pertence ao usuário.")

        return repo.criar_cartao(
            cur, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
        )


def atualizar_cartao(cartao_id, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    """
    Atualiza os dados cadastrais do cartão. Não altera limite retroativamente
    de lançamentos já existentes — apenas o teto (`limite`) usado em validações
    futuras de `validar_limite_disponivel`.
    """
    limite = _to_decimal(limite)
    _validar_dados_cartao(nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id)

    with get_cursor(commit=True) as cur:
        # Garante que o cartão pertence ao usuário antes de editar.
        cur.execute(
            "SELECT id FROM cartoes_credito WHERE id = %s AND usuario_id = %s",
            (cartao_id, usuario_id),
        )
        if not cur.fetchone():
            raise ErroValidacao("Cartão não encontrado ou não pertence ao usuário.")

        # Garante que a conta de pagamento pertence ao usuário.
        cur.execute(
            "SELECT id FROM contas WHERE id = %s AND usuario_id = %s",
            (conta_pagamento_id, usuario_id),
        )
        if not cur.fetchone():
            raise ErroValidacao("Conta de pagamento não encontrada ou não pertence ao usuário.")

        return repo.atualizar_cartao(
            cur, cartao_id, usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id
        )


def listar_cartoes(usuario_id, aplicar_permissao=True):
    """
    aplicar_permissao=True: usado pelas telas de Lançamentos/Previstos/Extrato/
    Relatórios, que devem respeitar a parametrização de permissoes_service.
    aplicar_permissao=False: usado em telas de gestão do próprio cartão
    (ex.: tela de Cartões, tela de Permissões) onde o usuário deve ver
    TODOS os seus cartões, independente de parametrização.
    """
    cartoes_ids = permissoes_service.obter_cartoes_visiveis_ids(usuario_id) if aplicar_permissao else None
    with get_cursor() as cur:
        return repo.listar_cartoes(cur, usuario_id, cartoes_ids)


def buscar_cartao(cartao_id, usuario_id):
    with get_cursor() as cur:
        return repo.buscar_cartao(cur, cartao_id, usuario_id)


def calcular_fatura_atual(cartao_id, usuario_id):
    """Soma dos lançamentos pendentes do cartão (fatura em aberto)."""
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


def listar_cartoes_com_fatura(usuario_id):
    """
    Lista todos os cartões (respeitando permissão) com suas faturas abertas
    e limites disponíveis calculados.
    """
    cartoes = listar_cartoes(usuario_id, aplicar_permissao=True)
    resultado = []
    for c in cartoes:
        fatura_aberta = calcular_fatura_atual(c["id"], usuario_id)
        # Fatura é representada como valor negativo (soma de despesas);
        # limite disponível = limite - abs(fatura_aberta)
        limite_disponivel = c["limite"] - abs(fatura_aberta)
        resultado.append({**c, "fatura_aberta": fatura_aberta, "limite_disponivel": limite_disponivel})
    return resultado


def listar_lancamentos_pendentes(cartao_id, usuario_id):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT l.*, cat.nome AS categoria_nome
            FROM lancamentos l
            LEFT JOIN categorias cat ON cat.id = l.categoria_id
            WHERE l.cartao_id = %s AND l.usuario_id = %s AND l.status = 'pendente'
            ORDER BY l.data_lancamento DESC
            """,
            (cartao_id, usuario_id),
        )
        return cur.fetchall()


def validar_limite_disponivel(cartao_id, usuario_id, valor_lancamento):
    """
    Verifica se o novo lançamento (despesa, valor negativo) não excede o
    limite disponível do cartão. Fatura atual + novo lançamento não pode
    ultrapassar o limite total.
    """
    valor_lancamento = _to_decimal(valor_lancamento)

    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM cartoes_credito WHERE id = %s AND usuario_id = %s",
            (cartao_id, usuario_id),
        )
        cartao = cur.fetchone()
        if not cartao:
            raise ErroValidacao("Cartão não encontrado ou não pertence ao usuário.")
        limite = cartao["limite"]

    fatura_atual = calcular_fatura_atual(cartao_id, usuario_id)
    total_usado = abs(fatura_atual) + abs(valor_lancamento)

    if total_usado > limite:
        disponivel = limite - abs(fatura_atual)
        raise ErroValidacao(
            f"Limite insuficiente. Disponível: R$ {disponivel:.2f}, "
            f"tentativa de despesa: R$ {abs(valor_lancamento):.2f}."
        )
    return cartao
