"""
Rotas de gestão de usuários (cadastro interno). Acesso restrito a usuários
autenticados — qualquer usuário logado pode cadastrar novos usuários, pois
não há hierarquia de admin definida neste sistema.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from services import usuarios_service
from services.usuarios_service import ErroValidacao

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@usuarios_bp.route("/", methods=["GET"])
@login_required
def listar():
    usuarios = usuarios_service.listar_usuarios()
    return render_template("usuarios/list.html", usuarios=usuarios)


@usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "GET":
        return render_template("usuarios/form.html")

    nome = request.form.get("nome", "")
    email = request.form.get("email", "")
    senha = request.form.get("senha", "")

    try:
        usuarios_service.cadastrar_usuario(nome, email, senha)
        flash("Usuário cadastrado com sucesso!", "sucesso")
        return redirect(url_for("usuarios.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return render_template("usuarios/form.html", nome=nome, email=email)
