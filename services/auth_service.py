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


def atualizar_perfil(usuario_id, nome, email):
    """
    Atualiza nome e email do usuário autenticado.
    Nunca altera senha aqui — isso é responsabilidade de alterar_senha().
    """
    nome = (nome or "").strip()
    email = (email or "").strip().lower()

    if not nome or not email:
        raise ErroValidacao("Nome e email são obrigatórios.")
    if "@" not in email or "." not in email:
        raise ErroValidacao("Email inválido.")

    with get_cursor(commit=True) as cur:
        existente = repo.buscar_por_email_exceto_usuario(cur, email, usuario_id)
        if existente:
            raise ErroValidacao("Este email já está em uso por outro usuário.")

        row = repo.atualizar_dados(cur, usuario_id, nome, email)
        if not row:
            raise ErroValidacao("Usuário não encontrado.")
        return Usuario(row)


def alterar_senha(usuario_id, senha_atual, senha_nova, senha_confirmacao):
    """
    Troca a senha do usuário autenticado.
    Exige a senha atual correta antes de permitir a alteração (evita que
    alguém com sessão ativa aberta em um dispositivo compartilhado troque
    a senha sem saber a atual).
    """
    if not senha_atual or not senha_nova or not senha_confirmacao:
        raise ErroValidacao("Preencha todos os campos de senha.")
    if len(senha_nova) < 6:
        raise ErroValidacao("A nova senha deve ter no mínimo 6 caracteres.")
    if senha_nova != senha_confirmacao:
        raise ErroValidacao("A confirmação de senha não coincide.")

    with get_cursor(commit=True) as cur:
        row = repo.buscar_por_id(cur, usuario_id)
        if not row:
            raise ErroValidacao("Usuário não encontrado.")
        if not check_password_hash(row["senha_hash"], senha_atual):
            raise ErroValidacao("Senha atual incorreta.")

        novo_hash = generate_password_hash(senha_nova)
        repo.atualizar_senha(cur, usuario_id, novo_hash)
