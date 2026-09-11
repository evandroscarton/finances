"""Regras de negócio de contas e cálculo de saldo."""
from repositories import contas_repository as repo


class ErroValidacao(Exception):
    pass


TIPOS_VALIDOS = {"corrente", "poupanca", "carteira"}


def criar_conta(usuario_id, nome, banco, tipo):
    if not nome or tipo not in TIPOS_VALIDOS:
        raise ErroValidacao("Nome e tipo (corrente/poupanca/carteira) são obrigatórios.")
    return repo.criar_conta(usuario_id, nome, banco, tipo)


def listar_contas_com_saldo(usuario_id):
    """Retorna contas já enriquecidas com saldo_compensado e saldo_projetado."""
    contas = repo.listar_contas(usuario_id)
    resultado = []
    for conta in contas:
        saldo_compensado = repo.calcular_saldo_compensado(conta["id"], usuario_id)
        saldo_projetado = repo.calcular_saldo_projetado(conta["id"], usuario_id)
        resultado.append({**conta, "saldo_compensado": saldo_compensado, "saldo_projetado": saldo_projetado})
    return resultado


def obter_conta_com_saldo(conta_id, usuario_id):
    conta = repo.buscar_conta(conta_id, usuario_id)
    if not conta:
        return None
    saldo_compensado = repo.calcular_saldo_compensado(conta_id, usuario_id)
    pendentes = repo.calcular_soma_pendentes(conta_id, usuario_id)
    saldo_projetado = saldo_compensado + pendentes

    # Verificação de consistência aritmética: saldo_projetado deve ser
    # exatamente saldo_compensado + pendentes. Recalcula via repo para
    # detectar divergência entre as duas formas de cálculo.
    saldo_projetado_repo = repo.calcular_saldo_projetado(conta_id, usuario_id)
    if saldo_projetado != saldo_projetado_repo:
        raise AssertionError(
            f"Inconsistência de saldo detectada na conta {conta_id}: "
            f"{saldo_projetado} != {saldo_projetado_repo}"
        )

    return {**conta, "saldo_compensado": saldo_compensado, "saldo_projetado": saldo_projetado}


def excluir_conta(conta_id, usuario_id):
    excluida = repo.excluir_conta(conta_id, usuario_id)
    if not excluida:
        raise ErroValidacao("Conta não encontrada ou não pertence ao usuário.")
    return excluida
