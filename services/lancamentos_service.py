"""
Regras de negócio de Lançamentos.
- Um lançamento pertence a exatamente UMA conta OU UM cartão (nunca ambos).
- Valor é sempre gravado com sinal (positivo=entrada, negativo=saída).
- Lançamentos de cartão validam limite disponível antes de gravar.
- Se data_compensacao não for informada, assume a data_lancamento (regra de negócio).
- Pagamento de fatura: cria lançamento de saída na conta + marca lançamentos
  do cartão como compensados, em transação atômica. Pode ser restrito a um
  intervalo de data_compensacao (pagamento parcial de fatura).
- Saldo compensado/projetado é sempre derivado de SUM sobre status/
  data_compensacao — logo, qualquer caminho que altere status para
  'compensado' (edição manual ou ação rápida) reflete automaticamente no saldo.
"""
from decimal import Decimal, InvalidOperation
from datetime import date
from db.connection import get_cursor
from repositories import lancamentos_repository as repo
from services.cartoes_service import validar_limite_disponivel, ErroValidacao as ErroCartao
from services import permissoes_service


class ErroValidacao(Exception):
    pass


STATUS_VALIDOS = {"compensado", "pendente"}


def _to_decimal(valor):
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        raise ErroValidacao("Valor monetário inválido.")


def _validar_e_calcular_valor(valor, tipo_valor):
    """Aplica o sinal correto: entrada=positivo, saída=negativo. Nunca zero."""
    valor = _to_decimal(valor)
    if valor == 0:
        raise ErroValidacao("Valor do lançamento não pode ser zero.")
    valor = abs(valor)
    if tipo_valor == "saida":
        valor = -valor
    elif tipo_valor != "entrada":
        raise ErroValidacao("Tipo de valor inválido. Use 'entrada' ou 'saida'.")
    return valor


def _resolver_data_compensacao(data_lancamento, data_compensacao):
    """
    Se data_compensacao não for informada, usa data_lancamento.
    Regra de negócio: todo lançamento precisa de uma data de compensação
    para que o cálculo de saldo compensado/projetado funcione corretamente;
    na ausência de informação explícita, assume-se que compensa na própria
    data do lançamento.
    """
    return data_compensacao or data_lancamento


def criar_lancamento(usuario_id, conta_id, cartao_id, categoria_id, descricao,
                      valor, tipo_valor, data_lancamento, data_compensacao, status):
    if not descricao:
        raise ErroValidacao("Descrição é obrigatória.")
    if bool(conta_id) == bool(cartao_id):
        raise ErroValidacao("Lançamento deve pertencer a exatamente uma conta OU um cartão.")
    if status not in STATUS_VALIDOS:
        raise ErroValidacao(f"Status inválido. Use um de: {', '.join(STATUS_VALIDOS)}.")
    if not data_lancamento:
        raise ErroValidacao("Data do lançamento é obrigatória.")

    data_compensacao = _resolver_data_compensacao(data_lancamento, data_compensacao)
    valor_final = _validar_e_calcular_valor(valor, tipo_valor)

    with get_cursor(commit=True) as cur:
        if conta_id:
            cur.execute("SELECT id FROM contas WHERE id = %s AND usuario_id = %s", (conta_id, usuario_id))
            if not cur.fetchone():
                raise ErroValidacao("Conta não encontrada ou não pertence ao usuário.")
        if cartao_id:
            cur.execute("SELECT id FROM cartoes_credito WHERE id = %s AND usuario_id = %s", (cartao_id, usuario_id))
            if not cur.fetchone():
                raise ErroValidacao("Cartão não encontrado ou não pertence ao usuário.")
            if valor_final < 0:
                try:
                    validar_limite_disponivel(cartao_id, usuario_id, valor_final)
                except ErroCartao as e:
                    raise ErroValidacao(str(e))
        if categoria_id:
            cur.execute("SELECT id FROM categorias WHERE id = %s AND usuario_id = %s", (categoria_id, usuario_id))
            if not cur.fetchone():
                raise ErroValidacao("Categoria não encontrada ou não pertence ao usuário.")

        return repo.criar_lancamento(
            cur, usuario_id, conta_id, cartao_id, categoria_id, descricao,
            valor_final, data_lancamento, data_compensacao, status,
        )


def buscar_lancamento(lancamento_id, usuario_id):
    with get_cursor() as cur:
        return repo.buscar_lancamento(cur, lancamento_id, usuario_id)


def atualizar_lancamento(lancamento_id, usuario_id, conta_id, cartao_id, categoria_id,
                          descricao, valor, tipo_valor, data_lancamento, data_compensacao, status):
    if not descricao:
        raise ErroValidacao("Descrição é obrigatória.")
    if bool(conta_id) == bool(cartao_id):
        raise ErroValidacao("Lançamento deve pertencer a exatamente uma conta OU um cartão.")
    if status not in STATUS_VALIDOS:
        raise ErroValidacao(f"Status inválido. Use um de: {', '.join(STATUS_VALIDOS)}.")

    data_compensacao = _resolver_data_compensacao(data_lancamento, data_compensacao)
    valor_final = _validar_e_calcular_valor(valor, tipo_valor)

    with get_cursor(commit=True) as cur:
        existente = repo.buscar_lancamento(cur, lancamento_id, usuario_id)
        if not existente:
            raise ErroValidacao("Lançamento não encontrado ou não pertence ao usuário.")
        if existente["transferencia_id"]:
            raise ErroValidacao("Lançamentos de transferência não podem ser editados diretamente.")

        return repo.atualizar_lancamento(
            cur, lancamento_id, usuario_id, conta_id, cartao_id, categoria_id,
            descricao, valor_final, data_lancamento, data_compensacao, status,
        )


def compensar_lancamento(lancamento_id, usuario_id):
    """
    Ação rápida da tela de listagem: marca um lançamento PENDENTE como
    COMPENSADO, preservando conta/cartão/categoria/valor/data_lancamento
    originais. Regra de data_compensacao:
    - Se já havia uma data_compensacao definida (futura), mantém-na —
      é a data efetiva em que o lançamento passa a valer no saldo.
    - Se não havia (era NULL), assume hoje, seguindo a mesma regra de
      _resolver_data_compensacao usada na criação/edição manual.
    Usa o mesmo repo.atualizar_lancamento da edição manual, garantindo que
    o efeito sobre saldo compensado/projetado seja idêntico (fonte única
    de verdade: SUM sobre status/data_compensacao).
    """
    with get_cursor(commit=True) as cur:
        existente = repo.buscar_lancamento(cur, lancamento_id, usuario_id)
        if not existente:
            raise ErroValidacao("Lançamento não encontrado ou não pertence ao usuário.")
        if existente["transferencia_id"]:
            raise ErroValidacao("Lançamentos de transferência não podem ser compensados diretamente aqui.")
        if existente["status"] == "compensado":
            raise ErroValidacao("Lançamento já está compensado.")

        nova_data_compensacao = existente["data_compensacao"] or date.today()

        return repo.atualizar_lancamento(
            cur, lancamento_id, usuario_id,
            existente["conta_id"], existente["cartao_id"], existente["categoria_id"],
            existente["descricao"], existente["valor"], existente["data_lancamento"],
            nova_data_compensacao, "compensado",
        )


def excluir_lancamento(lancamento_id, usuario_id):
    with get_cursor(commit=True) as cur:
        existente = repo.buscar_lancamento(cur, lancamento_id, usuario_id)
        if not existente:
            raise ErroValidacao("Lançamento não encontrado ou não pertence ao usuário.")
        if existente["transferencia_id"]:
            raise ErroValidacao("Exclua a transferência inteira, não um lançamento isolado.")

        return repo.excluir_lancamento(cur, lancamento_id, usuario_id)


def listar_com_filtros(usuario_id, filtros):
    """
    Aplica a regra de permissão (contas/cartões visíveis) antes de consultar
    o repository — telas de Lançamentos nunca exibem dado fora da
    parametrização do usuário.
    """
    contas_ids = permissoes_service.obter_contas_visiveis_ids(usuario_id)
    cartoes_ids = permissoes_service.obter_cartoes_visiveis_ids(usuario_id)
    with get_cursor() as cur:
        return repo.listar_com_filtros(cur, usuario_id, filtros, contas_ids, cartoes_ids)


def pagar_fatura_cartao(usuario_id, cartao_id, conta_pagamento_id, valor, data_pagamento,
                         data_inicio=None, data_fim=None):
    """
    Paga a fatura do cartão:
    1. Cria lançamento de SAÍDA na conta de pagamento (afeta saldo da conta).
    2. Marca como 'compensado' (com data_compensacao = data_pagamento) APENAS
       os lançamentos pendentes do cartão cuja data_compensacao esteja dentro
       do intervalo [data_inicio, data_fim] informado. Se ambos forem None,
       mantém o comportamento de compensar todos os pendentes.
    Tudo em UMA transação atômica — rollback se qualquer etapa falhar.
    Lançamentos de cartão NÃO afetam saldo de conta diretamente; só o
    pagamento da fatura (este lançamento) afeta.
    """
    valor = _to_decimal(valor)
    if valor <= 0:
        raise ErroValidacao("Valor do pagamento deve ser positivo.")
    if not data_pagamento:
        raise ErroValidacao("Data do pagamento é obrigatória.")

    with get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id FROM contas WHERE id = %s AND usuario_id = %s",
            (conta_pagamento_id, usuario_id),
        )
        if not cur.fetchone():
            raise ErroValidacao("Conta de pagamento não encontrada ou não pertence ao usuário.")

        cur.execute(
            "SELECT nome FROM cartoes_credito WHERE id = %s AND usuario_id = %s",
            (cartao_id, usuario_id),
        )
        cartao = cur.fetchone()
        if not cartao:
            raise ErroValidacao("Cartão não encontrado ou não pertence ao usuário.")

        repo.criar_lancamento(
            cur, usuario_id, conta_pagamento_id, None, None,
            f"Pagamento fatura {cartao['nome']}", -valor,
            data_pagamento, data_pagamento, "compensado",
        )

        sql = """
            UPDATE lancamentos
            SET status = 'compensado', data_compensacao = %s
            WHERE cartao_id = %s AND usuario_id = %s AND status = 'pendente'
        """
        params = [data_pagamento, cartao_id, usuario_id]

        if data_inicio:
            sql += " AND data_compensacao >= %s"
            params.append(data_inicio)
        if data_fim:
            sql += " AND data_compensacao <= %s"
            params.append(data_fim)

        cur.execute(sql, tuple(params))
        return True
