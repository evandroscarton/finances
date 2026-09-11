"""
Regras de autenticação: registro, login, hash de senha (werkzeug).
Usuario implementa a interface do Flask-Login (UserMixin).
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from db.connection import get_cursor
from repositories import usuarios_repository as repo


class ErroValidacao(Exception):
    pass


class Usuario(UserMixin):
    """Wrapper de usuário compatível com Flask-Login (id como string)."""
    def __init__(self, row):
        self.id = row["id"]
        self.nome = row["nome"]
        self.email = row["email"]

    def get_id(self):
        return str(self.id)


def registrar_usuario(nome, email, senha):
    if not nome or not email or not senha:
        raise ErroValidacao("Nome, email e senha são obrigatórios.")
    if len(senha) < 6:
        raise ErroValidacao("Senha deve ter no mínimo 6 caracteres.")

    with get_cursor(commit=True) as cur:
        if repo.buscar_por_email(cur, email):
            raise ErroValidacao("Email já cadastrado.")

        senha_hash = generate_password_hash(senha)
        row = repo.criar_usuario(cur, nome, email, senha_hash)
        return Usuario(row)


def autenticar(email, senha):
    with get_cursor() as cur:
        row = repo.buscar_por_email(cur, email)
        if not row:
            return None
        if not check_password_hash(row["senha_hash"], senha):
            return None
        return Usuario(row)


def carregar_usuario(usuario_id):
    """Usado pelo user_loader do Flask-Login."""
    with get_cursor() as cur:
        row = repo.buscar_por_id(cur, int(usuario_id))
        return Usuario(row) if row else None
