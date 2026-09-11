"""
Regras de negócio do Extrato.
Calcula o saldo acumulado linha a linha, em Python, a partir do saldo
anterior ao período (nunca de coluna fixa) + soma incremental de cada
lançamento compensado, na ordem cronológica.
"""
from db.connection import get_cursor
from repositories import extrato_repository as repo


class ErroValidacao(Exception):
    pass


def gerar_extrato(usuario_id, conta_id, cartao_id, data_inicio, data_fim):
    """
    Filtro exige ao menos conta_id OU cartao_id — extrato sem nenhum dos
    dois misturaria contextos de saldo diferentes (conta bancária vs. fatura
    de cartão), o que não faz sentido para "saldo acumulado".
    """
    if not conta_id and not cartao_id:
        raise ErroValidacao("Selecione uma conta ou um cartão para gerar o extrato.")
    if conta_id and cartao_id:
        raise ErroValidacao("Selecione apenas uma conta OU um cartão, não ambos.")

    with get_cursor() as cur:
        saldo_acumulado = repo.obter_saldo_anterior(cur, usuario_id, conta_id, cartao_id, data_inicio)
        lancamentos = repo.listar_extrato(cur, usuario_id, conta_id, cartao_id, data_inicio, data_fim)

    linhas = []
    for l in lancamentos:
        saldo_acumulado += l["valor"]
        linhas.append({
            **l,
            "saldo_apos": saldo_acumulado,
        })

    return {
        "linhas": linhas,
        "saldo_inicial": repo_saldo_inicial_seguro(data_inicio, saldo_acumulado, linhas),
        "saldo_final": saldo_acumulado,
    }


def repo_saldo_inicial_seguro(data_inicio, saldo_final, linhas):
    """
    Saldo inicial exibido no topo do extrato = saldo_final menos a soma de
    todas as linhas do período, o que devolve exatamente o saldo anterior
    ao período (evita nova query, é aritmeticamente equivalente).
    """
    soma_periodo = sum(l["valor"] for l in linhas)
    return saldo_final - soma_periodo
