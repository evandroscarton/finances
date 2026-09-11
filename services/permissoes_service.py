"""
Regras de negócio de permissões de acesso por conta/cartão.

REGRA CENTRAL (usada por todas as telas de listagem/relatório):
- Se o usuário NÃO tem nenhuma linha em permissoes_conta/permissoes_cartao,
  ele vê TODAS as suas contas/cartões (comportamento padrão, sem restrição).
- Se o usuário TEM ao menos uma linha parametrizada, ele só vê as
  contas/cartões explicitamente listadas — mesmo que tenha outras próprias.

Isso é resolvido em obter_contas_visiveis_ids()/obter_cartoes_visiveis_ids(),
que devem ser usados por TODA query de listagem/relatório sensível.
"""
from db.connection import get_cursor
from repositories import permissoes_repository as repo
from repositories import contas_repository, cartoes_repository


class ErroValidacao(Exception):
    pass


def obter_permissoes(usuario_id):
    with get_cursor() as cur:
        contas_ids = repo.listar_contas_permitidas_ids(cur, usuario_id)
        cartoes_ids = repo.listar_cartoes_permitidos_ids(cur, usuario_id)
    return contas_ids, cartoes_ids


def salvar_permissoes(usuario_id, contas_ids, cartoes_ids):
    """
    contas_ids/cartoes_ids: listas de int já validadas (podem ser vazias —
    isso é permitido e significa "voltar a ver tudo", conforme a regra
    central acima).
    """
    contas_ids = [int(c) for c in contas_ids if str(c).isdigit()]
    cartoes_ids = [int(c) for c in cartoes_ids if str(c).isdigit()]

    with get_cursor(commit=True) as cur:
        repo.substituir_permissoes(cur, usuario_id, contas_ids, cartoes_ids)


def obter_contas_visiveis_ids(usuario_id):
    """
    Retorna None se o usuário deve ver TODAS as contas (sem parametrização).
    Retorna lista de IDs (pode ser vazia) se houver restrição ativa.
    Usar sempre assim nos repositories de listagem:

        ids = obter_contas_visiveis_ids(usuario_id)
        if ids is not None:
            filtro += " AND conta_id = ANY(%s) "
    """
    with get_cursor() as cur:
        contas_ids = repo.listar_contas_permitidas_ids(cur, usuario_id)
    return contas_ids if contas_ids else None


def obter_cartoes_visiveis_ids(usuario_id):
    """Mesma regra de obter_contas_visiveis_ids(), aplicada a cartões."""
    with get_cursor() as cur:
        cartoes_ids = repo.listar_cartoes_permitidos_ids(cur, usuario_id)
    return cartoes_ids if cartoes_ids else None
