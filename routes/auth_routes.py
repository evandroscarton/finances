"""
Rotas de autenticação: registro, login, logout, edição de perfil e senha.
Renderiza templates Jinja2 (sessão via Flask-Login).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from services import auth_service
from services.auth_service import ErroValidacao

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "GET":
        return render_template("auth/registro.html")

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    try:
        usuario = auth_service.registrar_usuario(nome, email, senha)
        login_user(usuario)
        flash("Cadastro realizado com sucesso!", "sucesso")
        return redirect(url_for("dashboard.index"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("auth.registrar"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    usuario = auth_service.autenticar(email, senha)
    if not usuario:
        flash("Email ou senha inválidos.", "erro")
        return redirect(url_for("auth.login"))

    login_user(usuario)
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("auth.login"))


@auth_bp.route("/perfil", methods=["GET"])
@login_required
def perfil():
    """Tela de edição de perfil (dados cadastrais + troca de senha)."""
    return render_template("auth/perfil.html")


@auth_bp.route("/perfil", methods=["POST"])
@login_required
def atualizar_perfil():
    """Atualiza nome e email do usuário autenticado."""
    nome = request.form.get("nome", "")
    email = request.form.get("email", "")

    try:
        usuario_atualizado = auth_service.atualizar_perfil(current_user.id, nome, email)
        # Recarrega a sessão do Flask-Login com os dados novos (nome/email
        # exibidos no menu precisam refletir a alteração imediatamente).
        login_user(usuario_atualizado)
        flash("Dados atualizados com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")

    return redirect(url_for("auth.perfil"))


@auth_bp.route("/perfil/senha", methods=["POST"])
@login_required
def alterar_senha():
    """Altera a senha do usuário autenticado (exige senha atual correta)."""
    senha_atual = request.form.get("senha_atual", "")
    senha_nova = request.form.get("senha_nova", "")
    senha_confirmacao = request.form.get("senha_confirmacao", "")

    try:
        auth_service.alterar_senha(current_user.id, senha_atual, senha_nova, senha_confirmacao)
        flash("Senha alterada com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")

    return redirect(url_for("auth.perfil"))
