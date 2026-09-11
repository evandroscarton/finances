"""Regras de negócio de categorias."""
from repositories import categorias_repository as repo


class ErroValidacao(Exception):
    pass


TIPOS_VALIDOS = {"receita", "despesa"}


def criar_categoria(usuario_id, nome, tipo, cor=None):
    if not nome or tipo not in TIPOS_VALIDOS:
        raise ErroValidacao("Nome e tipo (receita/despesa) são obrigatórios.")
    return repo.criar_categoria(usuario_id, nome, tipo, cor)


def listar_categorias(usuario_id):
    return repo.listar_categorias(usuario_id)
