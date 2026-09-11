"""
Rota de dashboard: exibe visão geral de saldos compensados e projetados
de todas as contas do usuário logado.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services import contas_service

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")


@dashboard_bp.route("/")
@login_required
def index():
    contas = contas_service.listar_contas_com_saldos(current_user.id)
    saldo_total_compensado = sum(c["saldo_compensado"] for c in contas)
    saldo_total_projetado = sum(c["saldo_projetado"] for c in contas)
    return render_template(
        "dashboard/index.html",
        contas=contas,
        saldo_total_compensado=saldo_total_compensado,
        saldo_total_projetado=saldo_total_projetado,
    )
