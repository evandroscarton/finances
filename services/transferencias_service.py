"""
Regras de negócio de Transferências entre contas.
Toda transferência gera EXATAMENTE 2 lançamentos vinculados por
transferencia_id, dentro da MESMA transação SQL (BEGIN/COMMIT/ROLLBACK).
Nunca cria um lançamento sem o outro.
"""
from decimal import Decimal, InvalidOperation
from db.connection import get_cursor
from repositories import transferencias_repository as repo
from services import permissoes_service


class ErroValidacao(Exception):
    pass


def _to_decimal(valor):
    try:
        v = Decimal(str(valor))
    except InvalidOperation:
        raise ErroValidacao("Valor monetário inválido.")
    if v <= 0:
        raise ErroValidacao("Valor da transferência deve ser positivo.")
    return v


def criar_transferencia(usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao):
    if not conta_origem_id or not conta_destino_id:
        raise ErroValidacao("Conta de origem e destino são obrigatórias.")
    if conta_origem_id == conta_destino_id:
        raise ErroValidacao("Conta de origem e destino não podem ser a mesma.")
    if not data:
        raise ErroValidacao("Data da transferência é obrigatória.")

    valor = _to_decimal(valor)

    # get_cursor(commit=True) já encapsula BEGIN...COMMIT/ROLLBACK numa
    # única transação — se qualquer INSERT falhar, nada é persistido.
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM contas WHERE id = %s AND usuario_id = %s", (conta_origem_id, usuario_id))
        if not cur.fetchone():
            raise ErroValidacao("Conta de origem não encontrada ou não pertence ao usuário.")

        cur.execute("SELECT id FROM contas WHERE id = %s AND usuario_id = %s", (conta_destino_id, usuario_id))
        if not cur.fetchone():
            raise ErroValidacao("Conta de destino não encontrada ou não pertence ao usuário.")

        # 1. Cria registro de transferência (metadado)
        transferencia = repo.criar_transferencia(
            cur, usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao
        )

        # 2. Cria os 2 lançamentos vinculados pelo mesmo transferencia_id.
        #    Transferências não são categorizadas como receita/despesa
        #    (categoria_id=NULL) a menos que o usuário categorize depois.
        repo.criar_lancamento_transferencia(
            cur, usuario_id, conta_origem_id, -valor, data, descricao, transferencia["id"]
        )
        repo.criar_lancamento_transferencia(
            cur, usuario_id, conta_destino_id, valor, data, descricao, transferencia["id"]
        )

        return transferencia


def listar_transferencias(usuario_id):
    """
    Aplica a regra de permissão: só exibe transferências cujas DUAS pontas
    (origem e destino) estejam dentro das contas visíveis ao usuário.
    """
    contas_ids = permissoes_service.obter_contas_visiveis_ids(usuario_id)
    with get_cursor() as cur:
        return repo.listar_transferencias(cur, usuario_id, contas_ids)


def excluir_transferencia(transferencia_id, usuario_id):
    """
    Exclui a transferência e os 2 lançamentos vinculados na mesma transação
    (integridade: nunca deixa lançamento "órfão" de transferência).
    """
    with get_cursor(commit=True) as cur:
        transferencia = repo.buscar_transferencia(cur, transferencia_id, usuario_id)
        if not transferencia:
            raise ErroValidacao("Transferência não encontrada ou não pertence ao usuário.")

        repo.excluir_lancamentos_por_transferencia(cur, transferencia_id, usuario_id)
        repo.excluir_transferencia(cur, transferencia_id, usuario_id)
        return True
