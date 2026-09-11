"""
Regras de negócio de transferências entre contas.
CRÍTICO: toda transferência gera exatamente 2 lançamentos (saída na origem,
entrada no destino) na MESMA transação SQL. Se qualquer INSERT falhar,
faz ROLLBACK total — nunca deixa um lançamento órfão sem o par.
"""
from db.connection import get_cursor
from repositories import contas_repository as contas_repo
from repositories import lancamentos_repository as lancamentos_repo
from repositories import transferencias_repository as transferencias_repo


class ErroValidacao(Exception):
    pass


def criar_transferencia(usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao):
    if valor <= 0:
        raise ErroValidacao("Valor da transferência deve ser positivo.")
    if conta_origem_id == conta_destino_id:
        raise ErroValidacao("Conta de origem e destino devem ser diferentes.")

    origem = contas_repo.buscar_conta(conta_origem_id, usuario_id)
    destino = contas_repo.buscar_conta(conta_destino_id, usuario_id)
    if not origem or not destino:
        raise ErroValidacao("Conta de origem ou destino não encontrada, ou não pertence ao usuário.")

    # Transação atômica: cabeçalho da transferência + 2 lançamentos vinculados.
    # Usa get_cursor(commit=True) — em caso de exceção em qualquer ponto,
    # o context manager faz ROLLBACK automático (ver db/connection.py).
    with get_cursor(commit=True) as cur:
        transferencia_id = transferencias_repo.criar_transferencia_header(
            cur, usuario_id, conta_origem_id, conta_destino_id, valor, data, descricao
        )

        lanc_saida = lancamentos_repo.criar_lancamento(
            cur, usuario_id, conta_origem_id, None, None,
            descricao or "Transferência enviada", -valor, data, data,
            "compensado", transferencia_id,
        )

        lanc_entrada = lancamentos_repo.criar_lancamento(
            cur, usuario_id, conta_destino_id, None, None,
            descricao or "Transferência recebida", valor, data, data,
            "compensado", transferencia_id,
        )

        return {
            "transferencia_id": transferencia_id,
            "lancamento_saida": lanc_saida,
            "lancamento_entrada": lanc_entrada,
        }


def listar_transferencias(usuario_id):
    return transferencias_repo.listar_transferencias(usuario_id)
