"""
Regras de negócio de Categorias (receita/despesa, cor opcional).
"""
from db.connection import get_cursor
from repositories import categorias_repository as repo


class ErroValidacao(Exception):
    pass


TIPOS_VALIDOS = {"receita", "despesa"}


def criar_categoria(usuario_id, nome, tipo, cor=None):
    if not nome:
        raise ErroValidacao("Nome da categoria é obrigatório.")
    if tipo not in TIPOS_VALIDOS:
        raise ErroValidacao(f"Tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}.")

    with get_cursor(commit=True) as cur:
        return repo.criar_categoria(cur, usuario_id, nome, tipo, cor)


def buscar_categoria(categoria_id, usuario_id):
    with get_cursor() as cur:
        return repo.buscar_categoria(cur, categoria_id, usuario_id)


def listar_categorias(usuario_id):
    with get_cursor() as cur:
        return repo.listar_categorias(cur, usuario_id)


def atualizar_categoria(categoria_id, usuario_id, nome, tipo, cor=None):
    if not nome:
        raise ErroValidacao("Nome da categoria é obrigatório.")
    if tipo not in TIPOS_VALIDOS:
        raise ErroValidacao(f"Tipo inválido. Use um de: {', '.join(TIPOS_VALIDOS)}.")

    with get_cursor(commit=True) as cur:
        categoria = repo.buscar_categoria(cur, categoria_id, usuario_id)
        if not categoria:
            raise ErroValidacao("Categoria não encontrada ou não pertence ao usuário.")
        return repo.atualizar_categoria(cur, categoria_id, usuario_id, nome, tipo, cor)


def excluir_categoria(categoria_id, usuario_id):
    with get_cursor(commit=True) as cur:
        categoria = repo.buscar_categoria(cur, categoria_id, usuario_id)
        if not categoria:
            raise ErroValidacao("Categoria não encontrada ou não pertence ao usuário.")

        cur.execute(
            "SELECT COUNT(*) AS total FROM lancamentos WHERE categoria_id = %s AND usuario_id = %s",
            (categoria_id, usuario_id),
        )
        if cur.fetchone()["total"] > 0:
            raise ErroValidacao("Não é possível excluir categoria com lançamentos vinculados.")

        return repo.excluir_categoria(cur, categoria_id, usuario_id)
