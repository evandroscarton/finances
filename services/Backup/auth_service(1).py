"""Regras de negócio de autenticação. Nunca expõe senha em texto puro."""
from werkzeug.security import generate_password_hash, check_password_hash
from repositories import usuarios_repository as repo


class ErroValidacao(Exception):
    pass


def registrar_usuario(nome, email, senha):
    if not nome or not email or not senha:
        raise ErroValidacao("Nome, email e senha são obrigatórios.")
    if len(senha) < 6:
        raise ErroValidacao("Senha deve ter ao menos 6 caracteres.")
    if repo.buscar_por_email(email):
        raise ErroValidacao("Email já cadastrado.")
    senha_hash = generate_password_hash(senha)
    return repo.criar_usuario(nome, email, senha_hash)


def autenticar(email, senha):
    usuario = repo.buscar_por_email(email)
    if not usuario or not check_password_hash(usuario["senha_hash"], senha):
        raise ErroValidacao("Email ou senha inválidos.")
    return usuario
