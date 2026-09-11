"""
Regras de negócio de Lançamentos Previstos.

Um "previsto" é um modelo reutilizável: ao clicar em "Lançar", ele gera um
lançamento REAL (status='pendente') na tabela `lancamentos`, montando a data
a partir de dia_mes + mes_ano. O registro previsto NUNCA é apagado ou marcado
ao lançar — o usuário pode trocar o mes_ano e lançar de novo em meses futuros.
"""
import calendar
from datetime import date

from db.connection import get_cursor
from repositories import lancamentos_previstos_repository as repo
from services import lancamentos_service


class ErroValidacao(Exception):
    pass


def _validar_e_normalizar(conta_id, cartao_id, categoria_id, descricao,
                           valor_str, tipo_valor, dia_mes_str, mes_ano_str):
    if not descricao:
        raise ErroValidacao("Descrição é obrigatória.")
    if not categoria_id:
        raise ErroValidacao("Categoria é obrigatória.")
    if bool(conta_id) == bool(cartao_id):
        raise ErroValidacao("Selecione exatamente uma origem: Conta ou Cartão.")

    try:
        valor = abs(float(valor_str))
        if valor <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise ErroValidacao("Valor inválido.")
    valor = valor if tipo_valor == "entrada" else -valor

    try:
        dia_mes = int(dia_mes_str)
        if not (1 <= dia_mes <= 31):
            raise ValueError
    except (TypeError, ValueError):
        raise ErroValidacao("Dia do mês inválido (use 1 a 31).")

    # mes_ano_str vem do input type="month" no formato "YYYY-MM"
    try:
        ano, mes = mes_ano_str.split("-")
        mes_ano = date(int(ano), int(mes), 1)
    except (TypeError, ValueError, AttributeError):
        raise ErroValidacao("Mês/Ano inválido.")

    return valor, dia_mes, mes_ano


def criar_previsto(usuario_id, conta_id, cartao_id, categoria_id, descricao,
                    valor_str, tipo_valor, dia_mes_str, mes_ano_str):
    valor, dia_mes, mes_ano = _validar_e_normalizar(
        conta_id, cartao_id, categoria_id, descricao, valor_str, tipo_valor,
        dia_mes_str, mes_ano_str,
    )
    with get_cursor() as cur:
        previsto = repo.criar_previsto(
            cur, usuario_id, conta_id, cartao_id, categoria_id, descricao,
            valor, dia_mes, mes_ano,
        )
    return previsto


def atualizar_previsto(previsto_id, usuario_id, conta_id, cartao_id, categoria_id,
                        descricao, valor_str, tipo_valor, dia_mes_str, mes_ano_str):
    valor, dia_mes, mes_ano = _validar_e_normalizar(
        conta_id, cartao_id, categoria_id, descricao, valor_str, tipo_valor,
        dia_mes_str, mes_ano_str,
    )
    with get_cursor() as cur:
        previsto = repo.atualizar_previsto(
            cur, previsto_id, usuario_id, conta_id, cartao_id, categoria_id,
            descricao, valor, dia_mes, mes_ano,
        )
    if not previsto:
        raise ErroValidacao("Lançamento previsto não encontrado.")
    return previsto


def buscar_previsto(previsto_id, usuario_id):
    with get_cursor() as cur:
        return repo.buscar_previsto(cur, previsto_id, usuario_id)


def listar_previstos(usuario_id, filtros):
    with get_cursor() as cur:
        return repo.listar_com_filtros(cur, usuario_id, filtros)


def excluir_previsto(previsto_id, usuario_id):
    with get_cursor() as cur:
        linhas = repo.excluir_previsto(cur, previsto_id, usuario_id)
    if linhas == 0:
        raise ErroValidacao("Lançamento previsto não encontrado.")


def _montar_data_real(dia_mes, mes_ano):
    """
    Monta a data real a partir de dia_mes + mes_ano, com clamp para o último
    dia válido do mês (ex.: dia_mes=31 em mês de 30 dias -> usa dia 30).
    """
    ultimo_dia_do_mes = calendar.monthrange(mes_ano.year, mes_ano.month)[1]
    dia_ajustado = min(dia_mes, ultimo_dia_do_mes)
    return date(mes_ano.year, mes_ano.month, dia_ajustado)


def lancar_previsto(previsto_id, usuario_id):
    """
    Cria um lançamento REAL (status='pendente') na tabela `lancamentos`, com
    data_lancamento = dia_mes + mes_ano do previsto. Não altera nem remove o
    registro previsto, permitindo reutilizá-lo em meses futuros.
    """
    previsto = buscar_previsto(previsto_id, usuario_id)
    if not previsto:
        raise ErroValidacao("Lançamento previsto não encontrado.")

    data_lancamento = _montar_data_real(previsto["dia_mes"], previsto["mes_ano"])
    valor = previsto["valor"]
    tipo_valor = "entrada" if valor > 0 else "saida"

    lancamento = lancamentos_service.criar_lancamento(
        usuario_id,
        previsto["conta_id"],
        previsto["cartao_id"],
        previsto["categoria_id"],
        previsto["descricao"],
        str(abs(valor)),
        tipo_valor,
        data_lancamento.strftime("%Y-%m-%d"),
        None,          # data_compensacao: nulo, ainda não compensado
        "pendente",    # status: previsão recém-lançada entra como pendente
    )
    return lancamento
