"""
Rotas de Contas: CRUD via telas Jinja2.
Regra: toda query é escopada por usuario_id (via contas_service).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import contas_service
from services.contas_service import ErroValidacao

contas_bp = Blueprint("contas", __name__, url_prefix="/contas")


@contas_bp.route("/")
@login_required
def listar():
    # aplicar_permissao=False: tela de gestão das PRÓPRIAS contas — o usuário
    # deve ver e administrar 100% do que é dele, independente da
    # parametrização de permissões (que só afeta telas de consulta/relatório).
    contas = contas_service.listar_contas_com_saldos(current_user.id, aplicar_permissao=False)
    return render_template("contas/list.html", contas=contas)


@contas_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    if request.method == "GET":
        return render_template("contas/form.html", conta=None)

    nome = request.form.get("nome", "").strip()
    banco = request.form.get("banco", "").strip()
    tipo = request.form.get("tipo", "").strip()

    try:
        contas_service.criar_conta(current_user.id, nome, banco, tipo)
        flash("Conta criada com sucesso!", "sucesso")
        return redirect(url_for("contas.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("contas.nova"))


@contas_bp.route("/<int:conta_id>/editar", methods=["GET", "POST"])
@login_required
def editar(conta_id):
    conta = contas_service.buscar_conta(conta_id, current_user.id)
    if not conta:
        flash("Conta não encontrada.", "erro")
        return redirect(url_for("contas.listar"))

    if request.method == "GET":
        return render_template("contas/form.html", conta=conta)

    nome = request.form.get("nome", "").strip()
    banco = request.form.get("banco", "").strip()
    tipo = request.form.get("tipo", "").strip()

    try:
        contas_service.atualizar_conta(conta_id, current_user.id, nome, banco, tipo)
        flash("Conta atualizada com sucesso!", "sucesso")
        return redirect(url_for("contas.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("contas.editar", conta_id=conta_id))


@contas_bp.route("/<int:conta_id>/excluir", methods=["POST"])
@login_required
def excluir(conta_id):
    try:
        contas_service.excluir_conta(conta_id, current_user.id)
        flash("Conta excluída com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("contas.listar"))


@contas_bp.route("/<int:conta_id>/extrato")
@login_required
def extrato(conta_id):
    conta = contas_service.buscar_conta(conta_id, current_user.id)
    if not conta:
        flash("Conta não encontrada.", "erro")
        return redirect(url_for("contas.listar"))

    # Filtros opcionais via query string: ?data_inicio=&data_fim=&status=
    data_inicio = request.args.get("data_inicio") or None
    data_fim = request.args.get("data_fim") or None
    status = request.args.get("status") or None

    lancamentos = contas_service.listar_extrato(
        conta_id, current_user.id, data_inicio, data_fim, status
    )
    saldo_compensado = contas_service.calcular_saldo_compensado(conta_id, current_user.id)
    saldo_projetado = contas_service.calcular_saldo_projetado(conta_id, current_user.id)

    return render_template(
        "contas/extrato.html",
        conta=conta,
        lancamentos=lancamentos,
        saldo_compensado=saldo_compensado,
        saldo_projetado=saldo_projetado,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status=status,
    )
