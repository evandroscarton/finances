"""
Regras de negócio de lançamentos avulsos (não-transferência).
Lançamentos de cartão passam por validação de limite antes de serem criados.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from db.connection import get_cursor
from repositories import lancamentos_repository as repo
from repositories import contas_repository as contas_repo
from services import cartoes_service


class ErroValidacao(Exception):
    pass


def _parse_data(valor):
    """Converte string 'YYYY-MM-DD' vinda do JSON em objeto date. Aceita None."""
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ErroValidacao("Data inválida. Use o formato YYYY-MM-DD.")


def _to_decimal(valor):
    """
    Converte valor recebido do JSON (float/int/str) para Decimal.
    Colunas NUMERIC do Postgres retornam Decimal via psycopg2 — nunca
    misturamos Decimal com float em somas/comparações monetárias.
    """
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return valor
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        raise ErroValidacao("Valor monetário inválido.")


def _definir_status(data_compensacao):
    """Regra: status='compensado' apenas se data_compensacao preenchida e <= hoje."""
    if data_compensacao and data_compensacao <= date.today():
        return "compensado"
    return "pendente"


def criar_lancamento(usuario_id, conta_id, cartao_id, categoria_id, descricao,
                      valor, data_lancamento, data_compensacao):
    valor = _to_decimal(valor)
    if valor is None or valor == 0:
        raise ErroValidacao("Valor não pode ser zero.")
    if bool(conta_id) == bool(cartao_id):
        raise ErroValidacao("Lançamento deve pertencer a exatamente uma conta OU um cartão.")

    if conta_id:
        conta = contas_repo.buscar_conta(conta_id, usuario_id)
        if not conta:
            raise ErroValidacao("Conta não encontrada ou não pertence ao usuário.")

    if cartao_id and valor < 0:
        # Só valida limite para despesas (valor negativo)
        cartoes_service.validar_limite_disponivel(cartao_id, usuario_id, valor)

    data_lancamento = _parse_data(data_lancamento)
    data_compensacao = _parse_data(data_compensacao)
    if not data_lancamento:
        raise ErroValidacao("data_lancamento é obrigatória.")

    status = _definir_status(data_compensacao)

    with get_cursor(commit=True) as cur:
        return repo.criar_lancamento(
            cur, usuario_id, conta_id, cartao_id, categoria_id, descricao,
            valor, data_lancamento, data_compensacao, status,
        )


def pagar_fatura_cartao(usuario_id, cartao_id, conta_pagamento_id, valor, data_pagamento):
    """
    Pagamento de fatura: gera um único lançamento de saída na conta de
    pagamento. É o ÚNICO ponto em que despesa de cartão afeta saldo de conta.
    """
    from repositories import cartoes_repository as cartoes_repo

    valor = _to_decimal(valor)

    cartao = cartoes_repo.buscar_cartao(cartao_id, usuario_id)
    if not cartao:
        raise ErroValidacao("Cartão não encontrado.")
    conta = contas_repo.buscar_conta(conta_pagamento_id, usuario_id)
    if not conta:
        raise ErroValidacao("Conta de pagamento não encontrada ou não pertence ao usuário.")
    if valor is None or valor <= 0:
        raise ErroValidacao("Valor de pagamento deve ser positivo.")

    data_pagamento = _parse_data(data_pagamento)
    if not data_pagamento:
        raise ErroValidacao("data_pagamento é obrigatória.")

    with get_cursor(commit=True) as cur:
        lanc = repo.criar_lancamento(
            cur, usuario_id, conta_pagamento_id, None, None,
            f"Pagamento fatura cartão {cartao['nome']}", -valor,
            data_pagamento, data_pagamento, "compensado",
        )
        cur.execute(
            """
            UPDATE lancamentos
            SET status = 'compensado', data_compensacao = %s
            WHERE cartao_id = %s AND usuario_id = %s AND status = 'pendente'
            """,
            (data_pagamento, cartao_id, usuario_id),
        )
        return lanc


def excluir_lancamento(lancamento_id, usuario_id):
    lanc = repo.buscar_lancamento(lancamento_id, usuario_id)
    if not lanc:
        raise ErroValidacao("Lançamento não encontrado.")
    if lanc["transferencia_id"]:
        raise ErroValidacao("Lançamento de transferência não pode ser excluído isoladamente. Exclua a transferência.")
    return repo.excluir_lancamento(lancamento_id, usuario_id)
