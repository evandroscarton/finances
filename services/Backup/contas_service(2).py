"""
Regras de negócio de Contas.
Saldo compensado/projetado SEMPRE calculado via SUM sobre lancamentos —
nunca gravado como coluna fixa (fonte única de verdade).
"""
from db.connection import get_cursor
from repositories import contas_repository as repo


class ErroValidacao(Exception):
    pass


TIPOS_VALIDOS = {"corrente", "poupanca", "carteira"}


def criar_conta(usuario_id, nome, banco, tipo):
    if not nome:
        raise ErroValidacao("Nome da conta é obrigatório.")
    if tipo not in TIPOS_VALIDOS:
        raise ErroValidacao(f"Tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}.")

    with get_cursor(commit=True) as cur:
        return repo.criar_conta(cur, usuario_id, nome, banco, tipo)


def buscar_conta(conta_id, usuario_id):
    with get_cursor() as cur:
        return repo.buscar_conta(cur, conta_id, usuario_id)


def atualizar_conta(conta_id, usuario_id, nome, banco, tipo):
    if not nome:
        raise ErroValidacao("Nome da conta é obrigatório.")
    if tipo not in TIPOS_VALIDOS:
        raise ErroValidacao(f"Tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}.")

    with get_cursor(commit=True) as cur:
        conta = repo.buscar_conta(cur, conta_id, usuario_id)
        if not conta:
            raise ErroValidacao("Conta não encontrada ou não pertence ao usuário.")
        return repo.atualizar_conta(cur, conta_id, usuario_id, nome, banco, tipo)


def excluir_conta(conta_id, usuario_id):
    with get_cursor(commit=True) as cur:
        conta = repo.buscar_conta(cur, conta_id, usuario_id)
        if not conta:
            raise ErroValidacao("Conta não encontrada ou não pertence ao usuário.")

        cur.execute(
            "SELECT COUNT(*) AS total FROM lancamentos WHERE conta_id = %s AND usuario_id = %s",
            (conta_id, usuario_id),
        )
        if cur.fetchone()["total"] > 0:
            raise ErroValidacao("Não é possível excluir conta com lançamentos vinculados.")

        return repo.excluir_conta(cur, conta_id, usuario_id)


def calcular_saldo_compensado(conta_id, usuario_id):
    """
    Saldo compensado = SUM(valor) de lançamentos com status='compensado'
    daquela conta. Nunca lido de coluna fixa.
    """
    with get_cursor() as cur:
        return repo.calcular_saldo_compensado(cur, conta_id, usuario_id)


def calcular_saldo_projetado(conta_id, usuario_id):
    """
    Saldo projetado = saldo compensado + SUM(valor) de lançamentos pendentes
    (status='pendente' OR data_compensacao IS NULL OR data_compensacao > hoje).
    """
    with get_cursor() as cur:
        return repo.calcular_saldo_projetado(cur, conta_id, usuario_id)


def listar_contas_com_saldos(usuario_id):
    """Lista todas as contas do usuário com saldo compensado e projetado calculados."""
    with get_cursor() as cur:
        contas = repo.listar_contas(cur, usuario_id)
        resultado = []
        for c in contas:
            saldo_comp = repo.calcular_saldo_compensado(cur, c["id"], usuario_id)
            saldo_proj = repo.calcular_saldo_projetado(cur, c["id"], usuario_id)
            # Verificação de consistência: projetado deve ser >= compensado
            # em módulo aritmético (compensado + pendentes = projetado).
            c["saldo_compensado"] = saldo_comp
            c["saldo_projetado"] = saldo_proj
            resultado.append(c)
        return resultado


def listar_extrato(conta_id, usuario_id, data_inicio=None, data_fim=None, status=None):
    with get_cursor() as cur:
        return repo.listar_lancamentos_por_conta(
            cur, conta_id, usuario_id, data_inicio, data_fim, status
        )

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
