"""
Regras de negócio de cartões de crédito.
"""
from decimal import Decimal, InvalidOperation
from db.connection import get_cursor
from repositories import cartoes_repository as repo


class ErroValidacao(Exception):
    pass


def criar_cartao(usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id):
    if not nome or limite is None or limite < 0:
        raise ErroValidacao("Nome e limite (>=0) são obrigatórios.")
    if not (1 <= dia_fechamento <= 31) or not (1 <= dia_vencimento <= 31):
        raise ErroValidacao("Dia de fechamento/vencimento deve estar entre 1 e 31.")
    if conta_pagamento_id:
        conta = contas_repo.buscar_conta(conta_pagamento_id, usuario_id)
        if not conta:
            raise ErroValidacao("Conta de pagamento não encontrada ou não pertence ao usuário.")
    return repo.criar_cartao(usuario_id, nome, limite, dia_fechamento, dia_vencimento, conta_pagamento_id)


def listar_cartoes_com_fatura(usuario_id):
    cartoes = repo.listar_cartoes(usuario_id)
    resultado = []
    for c in cartoes:
        fatura_aberta = repo.calcular_fatura_aberta(c["id"], usuario_id)
        # Fatura é representada como valor negativo (soma de despesas);
        # limite disponível = limite - abs(fatura_aberta)
        limite_disponivel = c["limite"] - abs(fatura_aberta)
        resultado.append({**c, "fatura_aberta": fatura_aberta, "limite_disponivel": limite_disponivel})
    return resultado


def validar_limite_disponivel(cartao_id, usuario_id, valor_despesa):
    """
    Valida se lançar uma despesa (valor_despesa deve ser negativo) não
    ultrapassa o limite disponível do cartão. Lança ErroValidacao se ultrapassar.
    """
    cartao = repo.buscar_cartao(cartao_id, usuario_id)
    if not cartao:
        raise ErroValidacao("Cartão não encontrado ou não pertence ao usuário.")
    fatura_aberta = repo.calcular_fatura_aberta(cartao_id, usuario_id)
    novo_total_usado = abs(fatura_aberta) + abs(valor_despesa)
    if novo_total_usado > cartao["limite"]:
        raise ErroValidacao(
            f"Limite insuficiente. Disponível: {cartao['limite'] - abs(fatura_aberta):.2f}"
        )
    return cartao

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
