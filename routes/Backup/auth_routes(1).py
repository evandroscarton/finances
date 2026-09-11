"""Rotas de autenticação. Sem SQL aqui — apenas orquestra o service."""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from services import auth_service
from repositories import usuarios_repository as usuarios_repo

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


class UsuarioLogin(UserMixin):
    def __init__(self, dados):
        self.id = dados["id"]
        self.nome = dados["nome"]
        self.email = dados["email"]


def carregar_usuario(usuario_id):
    """Callback usado pelo Flask-Login (registrado em app/__init__.py)."""
    dados = usuarios_repo.buscar_por_id(usuario_id)
    return UsuarioLogin(dados) if dados else None


@auth_bp.route("/registrar", methods=["POST"])
def registrar():
    body = request.get_json(silent=True) or {}
    try:
        usuario = auth_service.registrar_usuario(
            body.get("nome"), body.get("email"), body.get("senha")
        )
        return jsonify(usuario), 201
    except auth_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    try:
        usuario = auth_service.autenticar(body.get("email"), body.get("senha"))
        login_user(UsuarioLogin(usuario))
        return jsonify({"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"]}), 200
    except auth_service.ErroValidacao as e:
        return jsonify({"erro": str(e)}), 401


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"mensagem": "Logout realizado."}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({"id": current_user.id, "nome": current_user.nome, "email": current_user.email}), 200
