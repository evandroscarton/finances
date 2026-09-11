"""
Regras de negócio de gestão de usuários. Cadastro interno (por um usuário já
logado) de novos usuários — não confundir com o fluxo de login/registro
público, que é tratado em auth_service.py.
"""
import re

from werkzeug.security import generate_password_hash

from db.connection import get_cursor
from repositories import usuarios_repository as repo

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ErroValidacao(Exception):
    pass


def cadastrar_usuario(nome, email, senha):
    if not nome or not nome.strip():
        raise ErroValidacao("Nome é obrigatório.")
    if not email or not _EMAIL_REGEX.match(email):
        raise ErroValidacao("E-mail inválido.")
    if not senha or len(senha) < 6:
        raise ErroValidacao("Senha deve ter no mínimo 6 caracteres.")

    email = email.strip().lower()
    senha_hash = generate_password_hash(senha)

    with get_cursor(commit=True) as cur:
        if repo.buscar_por_email(cur, email):
            raise ErroValidacao("Já existe um usuário cadastrado com este e-mail.")
        usuario = repo.criar_usuario(cur, nome.strip(), email, senha_hash)
    return usuario


def listar_usuarios():
    with get_cursor() as cur:
        return repo.listar_todos(cur)
