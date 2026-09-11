"""
Rotas de Categorias: CRUD simples de categorias de receita/despesa.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import categorias_service
from services.categorias_service import ErroValidacao

categorias_bp = Blueprint("categorias", __name__, url_prefix="/categorias")


@categorias_bp.route("/")
@login_required
def listar():
    categorias = categorias_service.listar_categorias(current_user.id)
    return render_template("categorias/list.html", categorias=categorias)


@categorias_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    if request.method == "GET":
        return render_template("categorias/form.html", categoria=None)

    nome = request.form.get("nome", "").strip()
    tipo = request.form.get("tipo", "").strip()
    cor = request.form.get("cor", "").strip() or None

    try:
        categorias_service.criar_categoria(current_user.id, nome, tipo, cor)
        flash("Categoria criada com sucesso!", "sucesso")
        return redirect(url_for("categorias.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("categorias.nova"))


@categorias_bp.route("/<int:categoria_id>/editar", methods=["GET", "POST"])
@login_required
def editar(categoria_id):
    categoria = categorias_service.buscar_categoria(categoria_id, current_user.id)
    if not categoria:
        flash("Categoria não encontrada.", "erro")
        return redirect(url_for("categorias.listar"))

    if request.method == "GET":
        return render_template("categorias/form.html", categoria=categoria)

    nome = request.form.get("nome", "").strip()
    tipo = request.form.get("tipo", "").strip()
    cor = request.form.get("cor", "").strip() or None

    try:
        categorias_service.atualizar_categoria(categoria_id, current_user.id, nome, tipo, cor)
        flash("Categoria atualizada com sucesso!", "sucesso")
        return redirect(url_for("categorias.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("categorias.editar", categoria_id=categoria_id))


@categorias_bp.route("/<int:categoria_id>/excluir", methods=["POST"])
@login_required
def excluir(categoria_id):
    try:
        categorias_service.excluir_categoria(categoria_id, current_user.id)
        flash("Categoria excluída com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("categorias.listar"))
