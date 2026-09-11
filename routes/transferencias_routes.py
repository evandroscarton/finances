"""
Rotas de Transferências entre contas. Cria dois lançamentos vinculados
(saída na origem, entrada no destino) em transação atômica via service.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import transferencias_service, contas_service
from services.transferencias_service import ErroValidacao

transferencias_bp = Blueprint("transferencias", __name__, url_prefix="/transferencias")


@transferencias_bp.route("/")
@login_required
def listar():
    transferencias = transferencias_service.listar_transferencias(current_user.id)
    return render_template("transferencias/list.html", transferencias=transferencias)


@transferencias_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    contas = contas_service.listar_contas_com_saldos(current_user.id)

    if request.method == "GET":
        return render_template("transferencias/form.html", contas=contas)

    conta_origem_id = request.form.get("conta_origem_id", type=int)
    conta_destino_id = request.form.get("conta_destino_id", type=int)
    valor = request.form.get("valor", "0")
    data = request.form.get("data", "")
    descricao = request.form.get("descricao", "").strip() or "Transferência entre contas"

    try:
        transferencias_service.criar_transferencia(
            current_user.id, conta_origem_id, conta_destino_id, valor, data, descricao
        )
        flash("Transferência realizada com sucesso!", "sucesso")
        return redirect(url_for("transferencias.listar"))
    except ErroValidacao as e:
        flash(str(e), "erro")
        return redirect(url_for("transferencias.nova"))


@transferencias_bp.route("/<int:transferencia_id>/excluir", methods=["POST"])
@login_required
def excluir(transferencia_id):
    try:
        transferencias_service.excluir_transferencia(transferencia_id, current_user.id)
        flash("Transferência excluída com sucesso!", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("transferencias.listar"))
