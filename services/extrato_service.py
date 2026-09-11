"""
Regras de negócio do Extrato.
Calcula o saldo acumulado linha a linha, em Python, a partir do saldo
anterior ao período (nunca de coluna fixa) + soma incremental de cada
lançamento (compensado, e pendente se incluir_pendentes=True), na ordem
cronológica (data_referencia).
"""
from db.connection import get_cursor
from repositories import extrato_repository as repo
from services import permissoes_service


class ErroValidacao(Exception):
    pass


def gerar_extrato(usuario_id, conta_id, cartao_id, data_inicio, data_fim,
                   incluir_pendentes=False):
    """
    Filtro exige ao menos conta_id OU cartao_id — extrato sem nenhum dos
    dois misturaria contextos de saldo diferentes (conta bancária vs. fatura
    de cartão), o que não faz sentido para "saldo acumulado".

    incluir_pendentes (padrão False): quando True, além dos lançamentos
    compensados, também lista os pendentes/não compensados no período —
    e o saldo_inicial/saldo_final passam a considerá-los também, já que a
    soma incremental é feita sobre o conjunto de linhas efetivamente listado.
    Quando False (padrão), o comportamento é idêntico ao extrato original
    (somente compensados).

    contas_visiveis_ids/cartoes_visiveis_ids são obtidos da regra de
    permissoes_service e aplicados no repository — garante que o extrato
    nunca exiba conta/cartão fora da parametrização do usuário.
    """
    if not conta_id and not cartao_id:
        raise ErroValidacao("Selecione uma conta ou um cartão para gerar o extrato.")
    if conta_id and cartao_id:
        raise ErroValidacao("Selecione apenas uma conta OU um cartão, não ambos.")

    contas_ids = permissoes_service.obter_contas_visiveis_ids(usuario_id)
    cartoes_ids = permissoes_service.obter_cartoes_visiveis_ids(usuario_id)

    if conta_id and contas_ids is not None and conta_id not in contas_ids:
        raise ErroValidacao("Você não tem permissão para acessar esta conta.")
    if cartao_id and cartoes_ids is not None and cartao_id not in cartoes_ids:
        raise ErroValidacao("Você não tem permissão para acessar este cartão.")

    with get_cursor() as cur:
        saldo_acumulado = repo.obter_saldo_anterior(
            cur, usuario_id, conta_id, cartao_id, data_inicio, contas_ids, cartoes_ids,
            incluir_pendentes,
        )
        lancamentos = repo.listar_extrato(
            cur, usuario_id, conta_id, cartao_id, data_inicio, data_fim, contas_ids, cartoes_ids,
            incluir_pendentes,
        )

    linhas = []
    for l in lancamentos:
        saldo_acumulado += l["valor"]
        linhas.append({
            **l,
            "categoria_exibicao": _montar_categoria_exibicao(l),
            "saldo_apos": saldo_acumulado,
        })

    return {
        "linhas": linhas,
        "saldo_inicial": repo_saldo_inicial_seguro(data_inicio, saldo_acumulado, linhas),
        "saldo_final": saldo_acumulado,
    }


def _montar_categoria_exibicao(lancamento):
    """
    Define o texto exibido na coluna "categoria" do relatório.

    Transferências não têm categoria própria (categoria_id é NULL nesses
    lançamentos, por regra de negócio — ver instruções do agente). Em vez de
    exibir vazio, mostramos para onde/de onde foi a transferência, usando o
    nome da conta do outro lado (conta_transferencia_nome), obtido via
    self-join no repository.

    - valor negativo (saída da conta)  -> "Transferência para: <conta destino>"
    - valor positivo (entrada na conta) -> "Transferência de: <conta origem>"
    - lançamento normal (sem transferencia_id) -> mantém categoria_nome original
    """
    if lancamento.get("transferencia_id") is None:
        return lancamento.get("categoria_nome")

    conta_outro_lado = lancamento.get("conta_transferencia_nome") or "conta desconhecida"

    if lancamento["valor"] < 0:
        return f"Transferência para: {conta_outro_lado}"
    else:
        return f"Transferência de: {conta_outro_lado}"


def repo_saldo_inicial_seguro(data_inicio, saldo_final, linhas):
    """
    Saldo inicial exibido no topo do extrato = saldo_final menos a soma de
    todas as linhas do período, o que devolve exatamente o saldo anterior
    ao período (evita nova query, é aritmeticamente equivalente).

    Funciona igual esteja ou não incluindo pendentes, pois "linhas" já
    reflete exatamente o conjunto somado em saldo_final.
    """
    soma_periodo = sum(l["valor"] for l in linhas)
    return saldo_final - soma_periodo
